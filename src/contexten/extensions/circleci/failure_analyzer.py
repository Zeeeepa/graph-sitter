"""
CircleCI Failure Analysis Engine

Intelligent failure analysis that:
- Parses build logs and identifies error patterns
- Classifies failure types and root causes
- Extracts relevant context and affected files
- Provides actionable fix suggestions
- Learns from patterns and successful fixes
"""

import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import hashlib

from .config import CircleCIIntegrationConfig
from .client import CircleCIClient
from .types import (
    FailureAnalysis, FailureType, FailurePattern, LogEntry, TestResult,
    CircleCIEvent, CircleCIJob, CircleCIWorkflow, AnalysisContext, AnalysisStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class ErrorPattern:
    """Error pattern definition"""
    name: str
    pattern: str
    failure_type: FailureType
    confidence: float
    description: str
    suggested_fixes: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)


@dataclass
class AnalysisCache:
    """Cache entry for analysis results"""
    analysis: FailureAnalysis
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class FailureAnalyzer:
    """
    Comprehensive failure analysis engine for CircleCI builds
    """
    
    def __init__(self, config: CircleCIIntegrationConfig, client: CircleCIClient):
        self.config = config
        self.client = client
        self.stats = AnalysisStats()
        
        # Analysis cache
        self.analysis_cache: Dict[str, AnalysisCache] = {}
        
        # Error patterns
        self.error_patterns = self._load_error_patterns()
        
        # Learning data
        self.successful_fixes: Dict[str, List[str]] = {}  # pattern -> fixes
        self.failure_signatures: Dict[str, FailureType] = {}  # signature -> type
    
    def _load_error_patterns(self) -> List[ErrorPattern]:
        """Load predefined error patterns"""
        patterns = [
            # Test failures
            ErrorPattern(
                name="jest_test_failure",
                pattern=r"FAIL\s+.*\.test\.(js|ts|jsx|tsx)",
                failure_type=FailureType.TEST_FAILURE,
                confidence=0.9,
                description="Jest test failure",
                suggested_fixes=[
                    "Review failing test assertions",
                    "Check test data and mocks",
                    "Verify component behavior changes"
                ],
                file_patterns=["*.test.js", "*.test.ts", "*.spec.js", "*.spec.ts"]
            ),
            
            ErrorPattern(
                name="pytest_failure",
                pattern=r"FAILED\s+.*\.py::",
                failure_type=FailureType.TEST_FAILURE,
                confidence=0.9,
                description="Python pytest failure",
                suggested_fixes=[
                    "Review test assertions and expected values",
                    "Check test fixtures and data",
                    "Verify function behavior changes"
                ],
                file_patterns=["test_*.py", "*_test.py"]
            ),
            
            # Compilation errors
            ErrorPattern(
                name="typescript_error",
                pattern=r"error TS\d+:",
                failure_type=FailureType.COMPILATION_ERROR,
                confidence=0.95,
                description="TypeScript compilation error",
                suggested_fixes=[
                    "Fix type annotations and interfaces",
                    "Resolve import/export issues",
                    "Update TypeScript configuration"
                ],
                file_patterns=["*.ts", "*.tsx", "tsconfig.json"]
            ),
            
            ErrorPattern(
                name="eslint_error",
                pattern=r"✖\s+\d+\s+problems?\s+\(\d+\s+errors?,\s+\d+\s+warnings?\)",
                failure_type=FailureType.COMPILATION_ERROR,
                confidence=0.8,
                description="ESLint errors",
                suggested_fixes=[
                    "Fix linting errors and warnings",
                    "Update ESLint configuration",
                    "Add eslint-disable comments if needed"
                ],
                file_patterns=[".eslintrc.*", "*.js", "*.ts", "*.jsx", "*.tsx"]
            ),
            
            # Dependency errors
            ErrorPattern(
                name="npm_install_error",
                pattern=r"npm ERR!",
                failure_type=FailureType.DEPENDENCY_ERROR,
                confidence=0.85,
                description="NPM installation error",
                suggested_fixes=[
                    "Update package.json dependencies",
                    "Clear npm cache and reinstall",
                    "Resolve version conflicts"
                ],
                file_patterns=["package.json", "package-lock.json", "yarn.lock"]
            ),
            
            ErrorPattern(
                name="pip_install_error",
                pattern=r"ERROR:\s+Could not install packages",
                failure_type=FailureType.DEPENDENCY_ERROR,
                confidence=0.85,
                description="Python pip installation error",
                suggested_fixes=[
                    "Update requirements.txt",
                    "Resolve dependency conflicts",
                    "Check Python version compatibility"
                ],
                file_patterns=["requirements.txt", "setup.py", "pyproject.toml"]
            ),
            
            # Infrastructure errors
            ErrorPattern(
                name="docker_build_error",
                pattern=r"The command '/bin/sh -c.*' returned a non-zero code",
                failure_type=FailureType.INFRASTRUCTURE_ERROR,
                confidence=0.8,
                description="Docker build failure",
                suggested_fixes=[
                    "Review Dockerfile commands",
                    "Check base image availability",
                    "Verify build context and files"
                ],
                file_patterns=["Dockerfile", "docker-compose.yml", ".dockerignore"]
            ),
            
            ErrorPattern(
                name="out_of_memory",
                pattern=r"(out of memory|OOM|killed|signal 9)",
                failure_type=FailureType.INFRASTRUCTURE_ERROR,
                confidence=0.9,
                description="Out of memory error",
                suggested_fixes=[
                    "Increase memory allocation in CircleCI config",
                    "Optimize memory usage in code",
                    "Use memory-efficient algorithms"
                ],
                file_patterns=[".circleci/config.yml"]
            ),
            
            # Timeout errors
            ErrorPattern(
                name="timeout_error",
                pattern=r"(timeout|timed out|exceeded.*time limit)",
                failure_type=FailureType.TIMEOUT_ERROR,
                confidence=0.8,
                description="Operation timeout",
                suggested_fixes=[
                    "Increase timeout values in configuration",
                    "Optimize slow operations",
                    "Parallelize long-running tasks"
                ],
                file_patterns=[".circleci/config.yml", "jest.config.js", "pytest.ini"]
            ),
            
            # Configuration errors
            ErrorPattern(
                name="circleci_config_error",
                pattern=r"CONFIG_ERROR",
                failure_type=FailureType.CONFIGURATION_ERROR,
                confidence=0.95,
                description="CircleCI configuration error",
                suggested_fixes=[
                    "Validate CircleCI configuration syntax",
                    "Check workflow and job definitions",
                    "Verify environment variables and contexts"
                ],
                file_patterns=[".circleci/config.yml"]
            ),
        ]
        
        logger.info(f"Loaded {len(patterns)} error patterns")
        return patterns
    
    async def analyze_failure(
        self,
        event: CircleCIEvent,
        context: Optional[AnalysisContext] = None
    ) -> FailureAnalysis:
        """Analyze a failure event"""
        
        if not event.is_failure_event:
            raise ValueError("Event is not a failure event")
        
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(event)
            if cache_key in self.analysis_cache:
                cached = self.analysis_cache[cache_key]
                if (datetime.now() - cached.created_at) < self.config.failure_analysis.cache_duration:
                    cached.access_count += 1
                    cached.last_accessed = datetime.now()
                    self.stats.analysis_cache_hits += 1
                    logger.debug(f"Using cached analysis for {event.id}")
                    return cached.analysis
            
            # Create analysis context if not provided
            if context is None:
                context = AnalysisContext(
                    build_id=event.workflow_id or event.job_id or event.id,
                    project_slug=event.project_slug,
                    failure_type=FailureType.UNKNOWN,
                    repository_url=f"https://github.com/{event.project_slug}",
                    branch=event.branch,
                    commit_sha=event.commit_sha
                )
            
            # Gather failure data
            logs = await self._collect_logs(event, context)
            tests = await self._collect_test_results(event, context)
            
            # Analyze patterns
            patterns = await self._analyze_patterns(logs, tests)
            
            # Determine root cause
            root_cause, failure_type, confidence = await self._determine_root_cause(patterns, logs, tests)
            
            # Extract affected files
            affected_files = await self._extract_affected_files(logs, tests, patterns)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(patterns, failure_type, affected_files)
            
            # Create analysis
            analysis = FailureAnalysis(
                build_id=context.build_id,
                project_slug=context.project_slug,
                analysis_timestamp=datetime.now(),
                failure_type=failure_type,
                root_cause=root_cause,
                confidence=confidence,
                error_messages=self._extract_error_messages(logs),
                failed_tests=tests,
                log_entries=logs[:100],  # Limit log entries
                patterns=patterns,
                affected_files=affected_files,
                suggested_fixes=suggestions,
                analysis_duration=(datetime.now() - start_time).total_seconds()
            )
            
            # Cache the analysis
            if self.config.failure_analysis.cache_analyses:
                self.analysis_cache[cache_key] = AnalysisCache(
                    analysis=analysis,
                    created_at=datetime.now()
                )
                self._cleanup_cache()
            
            # Update stats
            self.stats.failures_analyzed += 1
            if confidence >= 0.8:
                self.stats.high_confidence_analyses += 1
            self.stats.patterns_identified += len(patterns)
            
            # Learn from this analysis
            await self._learn_from_analysis(analysis)
            
            logger.info(f"Analysis completed for {event.id}: {failure_type.value} (confidence: {confidence:.2f})")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze failure {event.id}: {e}")
            raise
    
    async def _collect_logs(self, event: CircleCIEvent, context: AnalysisContext) -> List[LogEntry]:
        """Collect build logs"""
        logs = []
        
        try:
            if event.job_id:
                # Get logs for specific job
                job_logs = await self.client.get_job_logs(event.job_id)
                logs.extend(job_logs)
                
            elif event.workflow_id:
                # Get logs for all jobs in workflow
                jobs = await self.client.get_workflow_jobs(event.workflow_id)
                for job in jobs:
                    if job.is_failed:
                        job_logs = await self.client.get_job_logs(job.id)
                        logs.extend(job_logs)
            
            # Filter and limit logs
            error_logs = [log for log in logs if log.is_error or "error" in log.message.lower()]
            other_logs = [log for log in logs if not log.is_error and "error" not in log.message.lower()]
            
            # Prioritize error logs
            max_logs = self.config.failure_analysis.max_log_lines
            selected_logs = error_logs[:max_logs//2] + other_logs[:max_logs//2]
            
            logger.debug(f"Collected {len(selected_logs)} log entries")
            return selected_logs
            
        except Exception as e:
            logger.error(f"Failed to collect logs: {e}")
            return []
    
    async def _collect_test_results(self, event: CircleCIEvent, context: AnalysisContext) -> List[TestResult]:
        """Collect test results"""
        tests = []
        
        try:
            if event.job_id:
                # Get test results for specific job
                job_tests = await self.client.get_job_tests(event.job_id)
                tests.extend(job_tests)
                
            elif event.workflow_id:
                # Get test results for all jobs in workflow
                jobs = await self.client.get_workflow_jobs(event.workflow_id)
                for job in jobs:
                    if job.is_failed:
                        job_tests = await self.client.get_job_tests(job.id)
                        tests.extend(job_tests)
            
            # Filter failed tests
            failed_tests = [test for test in tests if test.result == "failed"]
            
            logger.debug(f"Collected {len(failed_tests)} failed tests")
            return failed_tests
            
        except Exception as e:
            logger.error(f"Failed to collect test results: {e}")
            return []
    
    async def _analyze_patterns(self, logs: List[LogEntry], tests: List[TestResult]) -> List[FailurePattern]:
        """Analyze logs and tests for failure patterns"""
        patterns = []
        
        # Combine all text for analysis
        all_text = []
        for log in logs:
            all_text.append(log.message)
        for test in tests:
            if test.failure_message:
                all_text.append(test.failure_message)
            if test.stack_trace:
                all_text.append(test.stack_trace)
        
        combined_text = "\n".join(all_text)
        
        # Match against known patterns
        for error_pattern in self.error_patterns:
            matches = re.findall(error_pattern.pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            if matches:
                pattern = FailurePattern(
                    pattern_type=error_pattern.failure_type,
                    confidence=error_pattern.confidence,
                    description=error_pattern.description,
                    error_message=matches[0] if isinstance(matches[0], str) else str(matches[0]),
                    suggested_fixes=error_pattern.suggested_fixes.copy(),
                    file_patterns=error_pattern.file_patterns.copy()
                )
                patterns.append(pattern)
        
        # Custom pattern analysis
        custom_patterns = await self._analyze_custom_patterns(combined_text, logs, tests)
        patterns.extend(custom_patterns)
        
        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        logger.debug(f"Identified {len(patterns)} failure patterns")
        return patterns
    
    async def _analyze_custom_patterns(
        self, 
        text: str, 
        logs: List[LogEntry], 
        tests: List[TestResult]
    ) -> List[FailurePattern]:
        """Analyze custom patterns not covered by predefined patterns"""
        patterns = []
        
        # Look for common error indicators
        error_indicators = [
            (r"ModuleNotFoundError: No module named '([^']+)'", FailureType.DEPENDENCY_ERROR, 0.9),
            (r"ImportError: cannot import name '([^']+)'", FailureType.DEPENDENCY_ERROR, 0.8),
            (r"SyntaxError: (.+)", FailureType.COMPILATION_ERROR, 0.95),
            (r"TypeError: (.+)", FailureType.COMPILATION_ERROR, 0.7),
            (r"ReferenceError: (.+)", FailureType.COMPILATION_ERROR, 0.8),
            (r"AssertionError: (.+)", FailureType.TEST_FAILURE, 0.9),
            (r"Permission denied", FailureType.INFRASTRUCTURE_ERROR, 0.8),
            (r"No space left on device", FailureType.INFRASTRUCTURE_ERROR, 0.95),
        ]
        
        for pattern_regex, failure_type, confidence in error_indicators:
            matches = re.findall(pattern_regex, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches[:3]:  # Limit to first 3 matches
                    pattern = FailurePattern(
                        pattern_type=failure_type,
                        confidence=confidence,
                        description=f"Custom pattern: {failure_type.value}",
                        error_message=match if isinstance(match, str) else str(match),
                        suggested_fixes=self._get_default_fixes(failure_type)
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _get_default_fixes(self, failure_type: FailureType) -> List[str]:
        """Get default fix suggestions for failure type"""
        fixes = {
            FailureType.TEST_FAILURE: [
                "Review and update failing tests",
                "Check test data and expectations",
                "Verify recent code changes"
            ],
            FailureType.COMPILATION_ERROR: [
                "Fix syntax and type errors",
                "Update imports and dependencies",
                "Check configuration files"
            ],
            FailureType.DEPENDENCY_ERROR: [
                "Update dependency versions",
                "Resolve version conflicts",
                "Check package availability"
            ],
            FailureType.INFRASTRUCTURE_ERROR: [
                "Check resource allocation",
                "Verify environment configuration",
                "Review infrastructure setup"
            ],
            FailureType.TIMEOUT_ERROR: [
                "Increase timeout values",
                "Optimize performance",
                "Parallelize operations"
            ],
            FailureType.CONFIGURATION_ERROR: [
                "Validate configuration syntax",
                "Check environment variables",
                "Review workflow definitions"
            ]
        }
        
        return fixes.get(failure_type, ["Review logs and fix identified issues"])
    
    async def _determine_root_cause(
        self, 
        patterns: List[FailurePattern], 
        logs: List[LogEntry], 
        tests: List[TestResult]
    ) -> Tuple[str, FailureType, float]:
        """Determine root cause and failure type"""
        
        if not patterns:
            return "Unknown failure - no patterns identified", FailureType.UNKNOWN, 0.1
        
        # Use highest confidence pattern
        primary_pattern = patterns[0]
        
        # Build root cause description
        root_cause = primary_pattern.description
        if primary_pattern.error_message:
            root_cause += f": {primary_pattern.error_message}"
        
        # Calculate overall confidence
        confidence = primary_pattern.confidence
        
        # Adjust confidence based on multiple patterns
        if len(patterns) > 1:
            # Multiple patterns increase confidence if they agree
            same_type_patterns = [p for p in patterns if p.pattern_type == primary_pattern.pattern_type]
            if len(same_type_patterns) > 1:
                confidence = min(confidence + 0.1, 1.0)
        
        # Adjust confidence based on error log quality
        error_logs = [log for log in logs if log.is_error]
        if len(error_logs) > 5:
            confidence = min(confidence + 0.05, 1.0)
        
        return root_cause, primary_pattern.pattern_type, confidence
    
    async def _extract_affected_files(
        self, 
        logs: List[LogEntry], 
        tests: List[TestResult], 
        patterns: List[FailurePattern]
    ) -> List[str]:
        """Extract files that might be affected by the failure"""
        affected_files = set()
        
        # Extract from test results
        for test in tests:
            if test.file:
                affected_files.add(test.file)
        
        # Extract from log messages
        file_patterns = [
            r"([a-zA-Z0-9_/.-]+\.(js|ts|jsx|tsx|py|java|cpp|c|h))",
            r"at ([a-zA-Z0-9_/.-]+\.(js|ts|jsx|tsx|py)):(\d+)",
            r"File \"([^\"]+)\"",
            r"in ([a-zA-Z0-9_/.-]+\.(js|ts|jsx|tsx|py|java))"
        ]
        
        for log in logs:
            for pattern in file_patterns:
                matches = re.findall(pattern, log.message)
                for match in matches:
                    if isinstance(match, tuple):
                        affected_files.add(match[0])
                    else:
                        affected_files.add(match)
        
        # Add files from pattern file patterns
        for pattern in patterns:
            affected_files.update(pattern.file_patterns)
        
        # Filter and clean file paths
        cleaned_files = []
        for file_path in affected_files:
            # Remove common prefixes and clean up
            cleaned = file_path.strip()
            if cleaned and not cleaned.startswith('.') and len(cleaned) > 2:
                cleaned_files.append(cleaned)
        
        return list(set(cleaned_files))[:20]  # Limit to 20 files
    
    async def _generate_suggestions(
        self, 
        patterns: List[FailurePattern], 
        failure_type: FailureType, 
        affected_files: List[str]
    ) -> List[str]:
        """Generate fix suggestions"""
        suggestions = set()
        
        # Add suggestions from patterns
        for pattern in patterns:
            suggestions.update(pattern.suggested_fixes)
        
        # Add type-specific suggestions
        type_suggestions = self._get_default_fixes(failure_type)
        suggestions.update(type_suggestions)
        
        # Add file-specific suggestions
        if affected_files:
            for file_path in affected_files[:5]:  # Limit to first 5 files
                if file_path.endswith('.test.js') or file_path.endswith('.test.ts'):
                    suggestions.add(f"Review test file: {file_path}")
                elif file_path.endswith('package.json'):
                    suggestions.add("Check package.json dependencies and scripts")
                elif file_path.endswith('.circleci/config.yml'):
                    suggestions.add("Validate CircleCI configuration")
        
        # Add learned suggestions
        if self.config.failure_analysis.pattern_learning_enabled:
            learned_suggestions = self._get_learned_suggestions(failure_type)
            suggestions.update(learned_suggestions)
        
        return list(suggestions)[:10]  # Limit to 10 suggestions
    
    def _get_learned_suggestions(self, failure_type: FailureType) -> List[str]:
        """Get suggestions learned from successful fixes"""
        pattern_key = failure_type.value
        return self.successful_fixes.get(pattern_key, [])
    
    def _extract_error_messages(self, logs: List[LogEntry]) -> List[str]:
        """Extract key error messages from logs"""
        error_messages = []
        
        for log in logs:
            if log.is_error or "error" in log.message.lower():
                # Clean up the message
                message = log.message.strip()
                if len(message) > 10 and len(message) < 500:  # Reasonable length
                    error_messages.append(message)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_messages = []
        for msg in error_messages:
            if msg not in seen:
                seen.add(msg)
                unique_messages.append(msg)
        
        return unique_messages[:10]  # Limit to 10 messages
    
    async def _learn_from_analysis(self, analysis: FailureAnalysis):
        """Learn from analysis for future improvements"""
        if not self.config.failure_analysis.pattern_learning_enabled:
            return
        
        # Create signature for this failure
        signature = self._create_failure_signature(analysis)
        self.failure_signatures[signature] = analysis.failure_type
        
        logger.debug(f"Learned failure signature: {signature} -> {analysis.failure_type.value}")
    
    def _create_failure_signature(self, analysis: FailureAnalysis) -> str:
        """Create a signature for failure pattern learning"""
        # Combine key elements
        elements = [
            analysis.failure_type.value,
            analysis.root_cause[:100],  # First 100 chars
            str(len(analysis.failed_tests)),
            str(len(analysis.error_messages))
        ]
        
        # Add pattern types
        for pattern in analysis.patterns:
            elements.append(pattern.pattern_type.value)
        
        # Create hash
        signature_text = "|".join(elements)
        return hashlib.md5(signature_text.encode()).hexdigest()[:16]
    
    def _get_cache_key(self, event: CircleCIEvent) -> str:
        """Generate cache key for event"""
        key_elements = [
            event.project_slug,
            event.commit_sha or "",
            event.workflow_id or event.job_id or event.id
        ]
        return hashlib.md5("|".join(key_elements).encode()).hexdigest()
    
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        if len(self.analysis_cache) <= self.config.failure_analysis.max_cache_size:
            return
        
        # Remove oldest entries
        sorted_entries = sorted(
            self.analysis_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Keep only the most recent entries
        keep_count = int(self.config.failure_analysis.max_cache_size * 0.8)
        for key, _ in sorted_entries[:-keep_count]:
            del self.analysis_cache[key]
        
        logger.debug(f"Cleaned cache, kept {keep_count} entries")
    
    # Public API methods
    def get_stats(self) -> AnalysisStats:
        """Get analysis statistics"""
        return self.stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            "cache_size": len(self.analysis_cache),
            "max_cache_size": self.config.failure_analysis.max_cache_size,
            "cache_hits": self.stats.analysis_cache_hits,
            "patterns_loaded": len(self.error_patterns)
        }
    
    async def analyze_build_failure(
        self, 
        project_slug: str, 
        build_number: int
    ) -> FailureAnalysis:
        """Analyze a specific build failure (convenience method)"""
        
        # Create a synthetic event for the build
        event = CircleCIEvent(
            id=f"build-{project_slug}-{build_number}",
            type=CircleCIEventType.WORKFLOW_COMPLETED,
            timestamp=datetime.now(),
            project_slug=project_slug,
            organization=project_slug.split('/')[0],
            build_number=build_number,
            status=BuildStatus.FAILED
        )
        
        return await self.analyze_failure(event)
    
    def learn_from_successful_fix(self, failure_type: FailureType, fix_description: str):
        """Learn from a successful fix"""
        if not self.config.failure_analysis.learn_from_successful_fixes:
            return
        
        pattern_key = failure_type.value
        if pattern_key not in self.successful_fixes:
            self.successful_fixes[pattern_key] = []
        
        if fix_description not in self.successful_fixes[pattern_key]:
            self.successful_fixes[pattern_key].append(fix_description)
            logger.info(f"Learned successful fix for {failure_type.value}: {fix_description}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "healthy": True,
            "patterns_loaded": len(self.error_patterns),
            "cache_size": len(self.analysis_cache),
            "stats": self.stats.dict()
        }

