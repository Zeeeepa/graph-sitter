"""
Intelligent PR Reviewer - AI-powered code review with Codegen SDK integration.

This module provides comprehensive automated PR review capabilities that can:
- Analyze code changes with deep contextual understanding
- Identify potential bugs, security issues, and performance problems
- Suggest improvements and optimizations
- Generate intelligent test cases for new code
- Provide architectural guidance and best practices
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Graph-Sitter imports
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

# Codegen SDK imports
from codegen import Agent

# GitHub integration
from ..github.events.pull_request import PullRequestEvent
from ..github.types.events.pull_request import PullRequestOpenedEvent, PullRequestSynchronizeEvent

logger = get_logger(__name__)

class ReviewSeverity(Enum):
    """Severity levels for review comments."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ReviewCategory(Enum):
    """Categories of review feedback."""
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    STYLE = "style"

@dataclass
class ReviewComment:
    """A single review comment."""
    file_path: str
    line_number: int
    category: ReviewCategory
    severity: ReviewSeverity
    message: str
    suggestion: Optional[str] = None
    confidence_score: float = 0.0
    auto_fixable: bool = False

@dataclass
class PRAnalysis:
    """Comprehensive PR analysis result."""
    pr_number: int
    title: str
    description: str
    files_changed: List[str]
    lines_added: int
    lines_deleted: int
    complexity_score: float
    risk_score: float
    test_coverage_impact: float
    review_comments: List[ReviewComment] = field(default_factory=list)
    suggested_tests: List[str] = field(default_factory=list)
    architectural_concerns: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    performance_concerns: List[str] = field(default_factory=list)

@dataclass
class ReviewSummary:
    """Summary of the PR review."""
    overall_score: float  # 0-10 scale
    recommendation: str  # "approve", "request_changes", "comment"
    key_concerns: List[str]
    positive_aspects: List[str]
    estimated_review_time: int  # minutes
    priority_issues: List[ReviewComment]

class IntelligentPRReviewer:
    """
    AI-powered PR reviewer with deep contextual understanding.
    
    Uses Codegen SDK to provide intelligent, comprehensive code reviews
    that go beyond simple static analysis to understand intent and context.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize Codegen SDK agent
        self.codegen_agent = Agent(
            org_id=self.config.get('codegen_org_id'),
            token=self.config.get('codegen_token'),
            base_url=self.config.get('codegen_base_url', 'https://api.codegen.com')
        )
        
        # Review configuration
        self.auto_approve_threshold = self.config.get('auto_approve_threshold', 8.5)
        self.auto_request_changes_threshold = self.config.get('auto_request_changes_threshold', 6.0)
        self.max_review_comments = self.config.get('max_review_comments', 20)
        self.enable_auto_fixes = self.config.get('enable_auto_fixes', True)
        self.enable_test_generation = self.config.get('enable_test_generation', True)
        
        # Initialize codebase for context
        self.codebase = None
        if 'codebase_path' in self.config:
            self.codebase = Codebase(self.config['codebase_path'])
    
    async def review_pr(self, pr_event: PullRequestEvent) -> PRAnalysis:
        """
        Perform comprehensive AI-powered review of a pull request.
        
        Args:
            pr_event: Pull request event containing PR details
            
        Returns:
            Comprehensive analysis and review of the PR
        """
        logger.info(f"Starting intelligent review of PR #{pr_event.number}")
        
        try:
            # Extract PR details
            pr_number = pr_event.number
            pr_title = pr_event.pull_request.title
            pr_description = pr_event.pull_request.body or ""
            
            # Get changed files and diff
            changed_files = await self._get_changed_files(pr_number)
            pr_diff = await self._get_pr_diff(pr_number)
            
            # Calculate basic metrics
            lines_added, lines_deleted = self._calculate_line_changes(pr_diff)
            complexity_score = await self._calculate_complexity_score(changed_files, pr_diff)
            
            # Perform comprehensive analysis
            review_comments = await self._analyze_code_changes(changed_files, pr_diff)
            architectural_concerns = await self._analyze_architecture(changed_files, pr_diff)
            security_issues = await self._analyze_security(changed_files, pr_diff)
            performance_concerns = await self._analyze_performance(changed_files, pr_diff)
            
            # Generate test suggestions
            suggested_tests = []
            if self.enable_test_generation:
                suggested_tests = await self._generate_test_suggestions(changed_files, pr_diff)
            
            # Calculate risk and coverage impact
            risk_score = self._calculate_risk_score(
                complexity_score, len(security_issues), len(review_comments)
            )
            test_coverage_impact = await self._estimate_coverage_impact(changed_files)
            
            # Create comprehensive analysis
            analysis = PRAnalysis(
                pr_number=pr_number,
                title=pr_title,
                description=pr_description,
                files_changed=changed_files,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                complexity_score=complexity_score,
                risk_score=risk_score,
                test_coverage_impact=test_coverage_impact,
                review_comments=review_comments,
                suggested_tests=suggested_tests,
                architectural_concerns=architectural_concerns,
                security_issues=security_issues,
                performance_concerns=performance_concerns
            )
            
            logger.info(f"PR review complete: {len(review_comments)} comments, risk_score={risk_score:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error reviewing PR #{pr_event.number}: {e}", exc_info=True)
            raise
    
    async def generate_review_summary(self, analysis: PRAnalysis) -> ReviewSummary:
        """Generate a comprehensive review summary with recommendation."""
        logger.info(f"Generating review summary for PR #{analysis.pr_number}")
        
        try:
            # Calculate overall score
            overall_score = await self._calculate_overall_score(analysis)
            
            # Determine recommendation
            if overall_score >= self.auto_approve_threshold:
                recommendation = "approve"
            elif overall_score <= self.auto_request_changes_threshold:
                recommendation = "request_changes"
            else:
                recommendation = "comment"
            
            # Extract key concerns and positive aspects
            key_concerns = self._extract_key_concerns(analysis)
            positive_aspects = self._extract_positive_aspects(analysis)
            
            # Identify priority issues
            priority_issues = [
                comment for comment in analysis.review_comments
                if comment.severity in [ReviewSeverity.ERROR, ReviewSeverity.CRITICAL]
            ]
            
            # Estimate review time
            estimated_time = self._estimate_review_time(analysis)
            
            summary = ReviewSummary(
                overall_score=overall_score,
                recommendation=recommendation,
                key_concerns=key_concerns,
                positive_aspects=positive_aspects,
                estimated_review_time=estimated_time,
                priority_issues=priority_issues
            )
            
            logger.info(f"Review summary generated: score={overall_score:.1f}, recommendation={recommendation}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating review summary: {e}", exc_info=True)
            raise
    
    async def post_review_comments(self, analysis: PRAnalysis, summary: ReviewSummary) -> bool:
        """Post intelligent review comments to the PR."""
        logger.info(f"Posting review comments for PR #{analysis.pr_number}")
        
        try:
            # Generate main review comment
            main_comment = await self._generate_main_review_comment(analysis, summary)
            
            # Post main review
            await self._post_pr_review(analysis.pr_number, main_comment, summary.recommendation)
            
            # Post individual line comments for high-priority issues
            for comment in summary.priority_issues[:self.max_review_comments]:
                await self._post_line_comment(
                    analysis.pr_number,
                    comment.file_path,
                    comment.line_number,
                    comment.message,
                    comment.suggestion
                )
            
            # Apply auto-fixes if enabled and safe
            if self.enable_auto_fixes:
                await self._apply_auto_fixes(analysis)
            
            logger.info(f"Review comments posted successfully for PR #{analysis.pr_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting review comments: {e}", exc_info=True)
            return False
    
    async def _get_changed_files(self, pr_number: int) -> List[str]:
        """Get list of files changed in the PR."""
        try:
            prompt = f"""
            Get the list of files changed in PR #{pr_number}.
            Return only the file paths, one per line.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(2)
                task.refresh()
            
            # Parse file paths from result
            files = [line.strip() for line in task.result.split('\n') if line.strip()]
            return files
            
        except Exception as e:
            logger.error(f"Error getting changed files: {e}")
            return []
    
    async def _get_pr_diff(self, pr_number: int) -> str:
        """Get the full diff for the PR."""
        try:
            prompt = f"""
            Get the complete diff for PR #{pr_number}.
            Include all file changes with context lines.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            return task.result
            
        except Exception as e:
            logger.error(f"Error getting PR diff: {e}")
            return ""
    
    def _calculate_line_changes(self, diff: str) -> tuple[int, int]:
        """Calculate lines added and deleted from diff."""
        lines_added = diff.count('\n+') - diff.count('\n+++')
        lines_deleted = diff.count('\n-') - diff.count('\n---')
        return max(0, lines_added), max(0, lines_deleted)
    
    async def _calculate_complexity_score(self, files: List[str], diff: str) -> float:
        """Calculate complexity score for the changes."""
        try:
            prompt = f"""
            Analyze the complexity of changes in these files: {', '.join(files)}
            
            Consider:
            - Cyclomatic complexity of new/modified functions
            - Number of new dependencies
            - Depth of nested structures
            - Number of conditional statements
            
            Return a complexity score from 1-10 (10 being most complex).
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(2)
                task.refresh()
            
            # Extract numeric score
            result = task.result.lower()
            for word in result.split():
                try:
                    score = float(word)
                    if 1 <= score <= 10:
                        return score
                except ValueError:
                    continue
            
            return 5.0  # Default medium complexity
            
        except Exception as e:
            logger.error(f"Error calculating complexity: {e}")
            return 5.0
    
    async def _analyze_code_changes(self, files: List[str], diff: str) -> List[ReviewComment]:
        """Analyze code changes and generate review comments."""
        logger.info("Analyzing code changes for review comments")
        
        try:
            prompt = f"""
            Perform a comprehensive code review of the following changes:
            
            Files changed: {', '.join(files)}
            
            Diff:
            {diff[:5000]}  # Limit diff size for prompt
            
            Analyze for:
            1. Potential bugs and logic errors
            2. Code quality and maintainability issues
            3. Performance concerns
            4. Security vulnerabilities
            5. Style and convention violations
            6. Missing error handling
            7. Unclear or missing documentation
            
            For each issue found, provide:
            - File path and line number
            - Category (bug, security, performance, maintainability, testing, documentation, architecture, style)
            - Severity (info, warning, error, critical)
            - Clear description of the issue
            - Suggested fix or improvement
            - Confidence score (0.0-1.0)
            
            Format as JSON array of objects.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            # Parse review comments from result
            comments = self._parse_review_comments(task.result)
            
            logger.info(f"Generated {len(comments)} review comments")
            return comments
            
        except Exception as e:
            logger.error(f"Error analyzing code changes: {e}")
            return []
    
    async def _analyze_architecture(self, files: List[str], diff: str) -> List[str]:
        """Analyze architectural concerns in the changes."""
        try:
            prompt = f"""
            Analyze the architectural impact of changes in: {', '.join(files)}
            
            Look for:
            - Violations of SOLID principles
            - Tight coupling between components
            - Missing abstractions
            - Inappropriate dependencies
            - Circular dependencies
            - Violation of existing patterns
            
            Return a list of architectural concerns, if any.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            # Parse concerns from result
            concerns = [line.strip() for line in task.result.split('\n') if line.strip() and not line.startswith('#')]
            return concerns[:5]  # Limit to top 5 concerns
            
        except Exception as e:
            logger.error(f"Error analyzing architecture: {e}")
            return []
    
    async def _analyze_security(self, files: List[str], diff: str) -> List[str]:
        """Analyze security issues in the changes."""
        try:
            prompt = f"""
            Perform security analysis of changes in: {', '.join(files)}
            
            Look for:
            - SQL injection vulnerabilities
            - XSS vulnerabilities
            - Authentication/authorization issues
            - Input validation problems
            - Sensitive data exposure
            - Insecure cryptographic practices
            - Path traversal vulnerabilities
            
            Return a list of security issues found.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            # Parse security issues
            issues = [line.strip() for line in task.result.split('\n') if line.strip() and not line.startswith('#')]
            return issues[:5]  # Limit to top 5 issues
            
        except Exception as e:
            logger.error(f"Error analyzing security: {e}")
            return []
    
    async def _analyze_performance(self, files: List[str], diff: str) -> List[str]:
        """Analyze performance concerns in the changes."""
        try:
            prompt = f"""
            Analyze performance impact of changes in: {', '.join(files)}
            
            Look for:
            - Inefficient algorithms (O(n²) where O(n) possible)
            - Unnecessary database queries
            - Memory leaks
            - Blocking operations in async code
            - Large object creation in loops
            - Missing caching opportunities
            - Inefficient data structures
            
            Return a list of performance concerns.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            # Parse performance concerns
            concerns = [line.strip() for line in task.result.split('\n') if line.strip() and not line.startswith('#')]
            return concerns[:5]  # Limit to top 5 concerns
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return []
    
    async def _generate_test_suggestions(self, files: List[str], diff: str) -> List[str]:
        """Generate intelligent test suggestions for the changes."""
        try:
            prompt = f"""
            Analyze the code changes and suggest comprehensive test cases:
            
            Files: {', '.join(files)}
            
            Generate test suggestions for:
            - New functions and methods
            - Modified business logic
            - Edge cases and error conditions
            - Integration points
            - Performance critical paths
            
            Return specific, actionable test case descriptions.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            # Parse test suggestions
            suggestions = [line.strip() for line in task.result.split('\n') if line.strip() and not line.startswith('#')]
            return suggestions[:10]  # Limit to top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error generating test suggestions: {e}")
            return []
    
    def _calculate_risk_score(self, complexity: float, security_issues: int, review_comments: int) -> float:
        """Calculate overall risk score for the PR."""
        # Normalize factors to 0-1 scale
        complexity_factor = min(complexity / 10.0, 1.0)
        security_factor = min(security_issues / 5.0, 1.0)
        quality_factor = min(review_comments / 20.0, 1.0)
        
        # Weighted risk calculation
        risk_score = (
            complexity_factor * 0.3 +
            security_factor * 0.4 +
            quality_factor * 0.3
        ) * 10.0
        
        return min(risk_score, 10.0)
    
    async def _estimate_coverage_impact(self, files: List[str]) -> float:
        """Estimate the impact on test coverage."""
        if not self.codebase:
            return 0.0
        
        try:
            # Simple heuristic: check if test files are included
            test_files = [f for f in files if 'test' in f.lower() or f.endswith('_test.py')]
            source_files = [f for f in files if f.endswith('.py') and 'test' not in f.lower()]
            
            if not source_files:
                return 0.0
            
            # Estimate coverage impact
            if test_files:
                return min(len(test_files) / len(source_files), 1.0)
            else:
                return -0.1  # Negative impact if no tests added
                
        except Exception as e:
            logger.error(f"Error estimating coverage impact: {e}")
            return 0.0
    
    async def _calculate_overall_score(self, analysis: PRAnalysis) -> float:
        """Calculate overall score for the PR (0-10 scale)."""
        base_score = 7.0  # Start with good score
        
        # Deduct for issues
        critical_issues = len([c for c in analysis.review_comments if c.severity == ReviewSeverity.CRITICAL])
        error_issues = len([c for c in analysis.review_comments if c.severity == ReviewSeverity.ERROR])
        warning_issues = len([c for c in analysis.review_comments if c.severity == ReviewSeverity.WARNING])
        
        score_deductions = (
            critical_issues * 2.0 +
            error_issues * 1.0 +
            warning_issues * 0.5 +
            len(analysis.security_issues) * 1.5 +
            analysis.risk_score * 0.3
        )
        
        # Add for positive aspects
        score_additions = (
            len(analysis.suggested_tests) * 0.1 +
            max(0, analysis.test_coverage_impact) * 2.0
        )
        
        final_score = base_score - score_deductions + score_additions
        return max(0.0, min(10.0, final_score))
    
    def _extract_key_concerns(self, analysis: PRAnalysis) -> List[str]:
        """Extract key concerns from the analysis."""
        concerns = []
        
        # High-severity issues
        critical_comments = [c for c in analysis.review_comments if c.severity == ReviewSeverity.CRITICAL]
        if critical_comments:
            concerns.append(f"{len(critical_comments)} critical issues found")
        
        # Security issues
        if analysis.security_issues:
            concerns.append(f"{len(analysis.security_issues)} security concerns")
        
        # High complexity
        if analysis.complexity_score > 7:
            concerns.append("High complexity changes")
        
        # Missing tests
        if analysis.test_coverage_impact < 0:
            concerns.append("No tests added for new code")
        
        return concerns[:5]
    
    def _extract_positive_aspects(self, analysis: PRAnalysis) -> List[str]:
        """Extract positive aspects from the analysis."""
        positives = []
        
        # Good test coverage
        if analysis.test_coverage_impact > 0.5:
            positives.append("Good test coverage")
        
        # Low complexity
        if analysis.complexity_score < 4:
            positives.append("Low complexity changes")
        
        # No security issues
        if not analysis.security_issues:
            positives.append("No security concerns identified")
        
        # Few issues overall
        if len(analysis.review_comments) < 5:
            positives.append("Clean code with minimal issues")
        
        return positives[:5]
    
    def _estimate_review_time(self, analysis: PRAnalysis) -> int:
        """Estimate human review time in minutes."""
        base_time = 10  # Base 10 minutes
        
        # Add time based on changes
        time_additions = (
            len(analysis.files_changed) * 2 +
            (analysis.lines_added + analysis.lines_deleted) // 50 +
            len(analysis.review_comments) * 2 +
            analysis.complexity_score * 2
        )
        
        return min(base_time + time_additions, 120)  # Cap at 2 hours
    
    def _parse_review_comments(self, result: str) -> List[ReviewComment]:
        """Parse review comments from AI result."""
        comments = []
        
        try:
            # Try to parse as JSON first
            import json
            data = json.loads(result)
            
            for item in data:
                if isinstance(item, dict):
                    comment = ReviewComment(
                        file_path=item.get('file_path', ''),
                        line_number=item.get('line_number', 0),
                        category=ReviewCategory(item.get('category', 'style')),
                        severity=ReviewSeverity(item.get('severity', 'info')),
                        message=item.get('message', ''),
                        suggestion=item.get('suggestion'),
                        confidence_score=item.get('confidence_score', 0.5),
                        auto_fixable=item.get('auto_fixable', False)
                    )
                    comments.append(comment)
                    
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback to text parsing
            logger.warning("Failed to parse JSON, using text parsing")
            comments = self._parse_comments_from_text(result)
        
        return comments[:self.max_review_comments]
    
    def _parse_comments_from_text(self, text: str) -> List[ReviewComment]:
        """Parse comments from plain text result."""
        comments = []
        lines = text.split('\n')
        
        current_comment = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for file paths
            if line.endswith('.py') or line.endswith('.js') or line.endswith('.ts'):
                if current_comment:
                    comments.append(current_comment)
                
                current_comment = ReviewComment(
                    file_path=line,
                    line_number=1,
                    category=ReviewCategory.STYLE,
                    severity=ReviewSeverity.INFO,
                    message="",
                    confidence_score=0.5
                )
            elif current_comment and line:
                current_comment.message += f" {line}"
        
        if current_comment:
            comments.append(current_comment)
        
        return comments
    
    async def _generate_main_review_comment(self, analysis: PRAnalysis, summary: ReviewSummary) -> str:
        """Generate the main review comment."""
        comment_parts = [
            f"## 🤖 Intelligent PR Review",
            f"",
            f"**Overall Score:** {summary.overall_score:.1f}/10",
            f"**Recommendation:** {summary.recommendation.replace('_', ' ').title()}",
            f"**Estimated Review Time:** {summary.estimated_review_time} minutes",
            f""
        ]
        
        if summary.key_concerns:
            comment_parts.extend([
                f"### ⚠️ Key Concerns",
                ""
            ])
            for concern in summary.key_concerns:
                comment_parts.append(f"- {concern}")
            comment_parts.append("")
        
        if summary.positive_aspects:
            comment_parts.extend([
                f"### ✅ Positive Aspects",
                ""
            ])
            for positive in summary.positive_aspects:
                comment_parts.append(f"- {positive}")
            comment_parts.append("")
        
        if analysis.suggested_tests:
            comment_parts.extend([
                f"### 🧪 Suggested Tests",
                ""
            ])
            for test in analysis.suggested_tests[:5]:
                comment_parts.append(f"- {test}")
            comment_parts.append("")
        
        # Add metrics
        comment_parts.extend([
            f"### 📊 Metrics",
            f"- **Files Changed:** {len(analysis.files_changed)}",
            f"- **Lines Added:** {analysis.lines_added}",
            f"- **Lines Deleted:** {analysis.lines_deleted}",
            f"- **Complexity Score:** {analysis.complexity_score:.1f}/10",
            f"- **Risk Score:** {analysis.risk_score:.1f}/10",
            f"- **Review Comments:** {len(analysis.review_comments)}",
            f""
        ])
        
        comment_parts.append("---")
        comment_parts.append("*Generated by Graph-Sitter Autonomous CI/CD*")
        
        return "\n".join(comment_parts)
    
    async def _post_pr_review(self, pr_number: int, comment: str, recommendation: str):
        """Post the main PR review."""
        try:
            prompt = f"""
            Post a PR review for PR #{pr_number} with the following details:
            
            Review Type: {recommendation}
            Comment: {comment}
            
            Use the GitHub API to submit this review.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(2)
                task.refresh()
            
            logger.info(f"Posted main review for PR #{pr_number}")
            
        except Exception as e:
            logger.error(f"Error posting PR review: {e}")
    
    async def _post_line_comment(self, pr_number: int, file_path: str, line_number: int, message: str, suggestion: Optional[str]):
        """Post a line-specific comment."""
        try:
            full_message = message
            if suggestion:
                full_message += f"\n\n**Suggested fix:**\n```\n{suggestion}\n```"
            
            prompt = f"""
            Post a line comment on PR #{pr_number}:
            - File: {file_path}
            - Line: {line_number}
            - Comment: {full_message}
            
            Use the GitHub API to post this review comment.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(2)
                task.refresh()
            
            logger.debug(f"Posted line comment for {file_path}:{line_number}")
            
        except Exception as e:
            logger.error(f"Error posting line comment: {e}")
    
    async def _apply_auto_fixes(self, analysis: PRAnalysis):
        """Apply automatic fixes for simple issues."""
        if not self.enable_auto_fixes:
            return
        
        auto_fixable_comments = [c for c in analysis.review_comments if c.auto_fixable and c.suggestion]
        
        if not auto_fixable_comments:
            return
        
        try:
            fixes_to_apply = []
            for comment in auto_fixable_comments[:5]:  # Limit to 5 auto-fixes
                fixes_to_apply.append({
                    'file': comment.file_path,
                    'line': comment.line_number,
                    'fix': comment.suggestion,
                    'description': comment.message
                })
            
            prompt = f"""
            Apply the following automatic fixes to PR #{analysis.pr_number}:
            
            {json.dumps(fixes_to_apply, indent=2)}
            
            Create a commit with these fixes and push to the PR branch.
            Use the commit message: "🤖 Auto-fix: Apply automated code improvements"
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            logger.info(f"Applied {len(fixes_to_apply)} auto-fixes to PR #{analysis.pr_number}")
            
        except Exception as e:
            logger.error(f"Error applying auto-fixes: {e}")

