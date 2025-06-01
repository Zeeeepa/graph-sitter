"""
Autonomous Failure Analyzer for Dashboard Integration

This module provides intelligent CI/CD failure analysis and auto-recovery
capabilities integrated with the dashboard monitoring system.
"""

import asyncio
import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from codegen import Agent

logger = logging.getLogger(__name__)


@dataclass
class FailurePattern:
    """Represents a known failure pattern"""
    id: str
    name: str
    description: str
    patterns: List[str]
    auto_fix: bool
    fix_strategy: str
    confidence_threshold: float
    category: str  # build, test, deploy, dependency, etc.


@dataclass
class FailureAnalysis:
    """Analysis result for a CI/CD failure"""
    id: str
    workflow_run_id: str
    failure_type: str
    root_cause: str
    suggested_fix: str
    confidence_score: float
    auto_fixable: bool
    affected_files: List[str]
    error_patterns: List[str]
    fix_applied: bool
    analysis_timestamp: datetime
    estimated_fix_time: Optional[int]  # minutes


@dataclass
class AutoFixResult:
    """Result of an automatic fix attempt"""
    fix_id: str
    failure_analysis_id: str
    fix_strategy: str
    success: bool
    changes_made: List[str]
    pr_created: Optional[str]
    rollback_available: bool
    execution_time: int  # seconds
    error_message: Optional[str]
    created_at: datetime


@dataclass
class FailureStatistics:
    """Statistics about failures and fixes"""
    total_failures: int
    auto_fixed_failures: int
    manual_fixes_required: int
    fix_success_rate: float
    common_failure_types: Dict[str, int]
    avg_fix_time: float
    time_period: str


class AutonomousFailureAnalyzer:
    """AI-powered failure analysis and auto-recovery system"""
    
    def __init__(self, codegen_org_id: str, codegen_token: str):
        self.codegen_agent = Agent(
            org_id=codegen_org_id,
            token=codegen_token
        )
        
        # Configuration from environment
        self.analysis_enabled = os.getenv("FAILURE_ANALYSIS_ENABLED", "true").lower() == "true"
        self.auto_recovery_enabled = os.getenv("FAILURE_AUTO_RECOVERY_ENABLED", "false").lower() == "true"
        self.pattern_learning = os.getenv("FAILURE_PATTERN_LEARNING", "true").lower() == "true"
        self.auto_fix_enabled = os.getenv("AUTO_FIX_ENABLED", "false").lower() == "true"
        self.auto_fix_dry_run = os.getenv("AUTO_FIX_DRY_RUN", "true").lower() == "true"
        self.auto_fix_require_approval = os.getenv("AUTO_FIX_REQUIRE_APPROVAL", "true").lower() == "true"
        self.auto_fix_confidence_threshold = float(os.getenv("AUTO_FIX_CONFIDENCE_THRESHOLD", "0.7"))
        self.max_auto_fixes_per_day = int(os.getenv("MAX_AUTO_FIXES_PER_DAY", "5"))
        
        # Internal state
        self.known_patterns = self._load_known_patterns()
        self.failure_history: List[FailureAnalysis] = []
        self.fix_history: List[AutoFixResult] = []
        self.daily_fix_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Callbacks for dashboard integration
        self.failure_callbacks: List[callable] = []
        self.fix_callbacks: List[callable] = []
        self.pattern_callbacks: List[callable] = []
    
    def _load_known_patterns(self) -> List[FailurePattern]:
        """Load known failure patterns"""
        return [
            FailurePattern(
                id="cython_compilation",
                name="Cython Compilation Error",
                description="Cython module compilation failures",
                patterns=[
                    r"error: Microsoft Visual C\+\+",
                    r"fatal error C1083",
                    r"cython.*error",
                    r"building.*failed",
                    r"compilation terminated"
                ],
                auto_fix=True,
                fix_strategy="rebuild_cython_modules",
                confidence_threshold=0.8,
                category="build"
            ),
            FailurePattern(
                id="dependency_conflict",
                name="Dependency Conflict",
                description="Package dependency conflicts",
                patterns=[
                    r"VersionConflict",
                    r"ResolutionImpossible",
                    r"pip.*conflict",
                    r"incompatible.*version",
                    r"dependency.*conflict"
                ],
                auto_fix=True,
                fix_strategy="resolve_dependencies",
                confidence_threshold=0.7,
                category="dependency"
            ),
            FailurePattern(
                id="test_timeout",
                name="Test Timeout",
                description="Test execution timeouts",
                patterns=[
                    r"timeout",
                    r"SIGTERM",
                    r"killed.*timeout",
                    r"test.*timed out",
                    r"execution.*timeout"
                ],
                auto_fix=True,
                fix_strategy="optimize_test_performance",
                confidence_threshold=0.6,
                category="test"
            ),
            FailurePattern(
                id="import_error",
                name="Import Error",
                description="Module import failures",
                patterns=[
                    r"ImportError",
                    r"ModuleNotFoundError",
                    r"No module named",
                    r"cannot import",
                    r"import.*failed"
                ],
                auto_fix=True,
                fix_strategy="fix_imports",
                confidence_threshold=0.8,
                category="build"
            ),
            FailurePattern(
                id="memory_error",
                name="Memory Error",
                description="Out of memory errors",
                patterns=[
                    r"MemoryError",
                    r"out of memory",
                    r"OOM",
                    r"memory.*exhausted",
                    r"allocation.*failed"
                ],
                auto_fix=False,
                fix_strategy="increase_memory_limits",
                confidence_threshold=0.9,
                category="resource"
            ),
            FailurePattern(
                id="flaky_test",
                name="Flaky Test",
                description="Intermittent test failures",
                patterns=[
                    r"AssertionError.*random",
                    r"intermittent.*failure",
                    r"race.*condition",
                    r"timing.*issue",
                    r"flaky.*test"
                ],
                auto_fix=False,
                fix_strategy="quarantine_and_analyze",
                confidence_threshold=0.5,
                category="test"
            ),
            FailurePattern(
                id="network_error",
                name="Network Error",
                description="Network connectivity issues",
                patterns=[
                    r"ConnectionError",
                    r"TimeoutError",
                    r"network.*unreachable",
                    r"connection.*refused",
                    r"DNS.*resolution.*failed"
                ],
                auto_fix=True,
                fix_strategy="retry_with_backoff",
                confidence_threshold=0.6,
                category="network"
            )
        ]
    
    async def analyze_failure(self, workflow_run_id: str, failure_logs: str, context: Dict[str, Any] = None) -> FailureAnalysis:
        """Analyze a workflow failure using AI and pattern matching"""
        
        if not self.analysis_enabled:
            logger.info("Failure analysis is disabled")
            return self._get_empty_analysis(workflow_run_id)
        
        logger.info(f"🔍 Analyzing failure for workflow run {workflow_run_id}")
        
        try:
            # Pattern matching analysis
            matched_patterns = self._match_failure_patterns(failure_logs)
            
            # AI-powered analysis
            ai_analysis = await self._ai_analyze_failure(workflow_run_id, failure_logs, context, matched_patterns)
            
            # Combine results
            analysis = self._combine_analysis_results(workflow_run_id, matched_patterns, ai_analysis, failure_logs)
            
            # Store analysis
            self.failure_history.append(analysis)
            
            # Learn from failure if enabled
            if self.pattern_learning:
                await self._learn_from_failure(analysis, failure_logs)
            
            # Notify callbacks
            await self._notify_failure_callbacks(analysis)
            
            logger.info(f"✅ Failure analysis complete: {analysis.failure_type} (confidence: {analysis.confidence_score:.2f})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failure analysis failed: {e}")
            return self._get_empty_analysis(workflow_run_id)
    
    def _match_failure_patterns(self, failure_logs: str) -> List[Tuple[FailurePattern, List[str]]]:
        """Match failure logs against known patterns"""
        
        matched_patterns = []
        
        for pattern in self.known_patterns:
            matches = []
            for regex_pattern in pattern.patterns:
                found_matches = re.findall(regex_pattern, failure_logs, re.IGNORECASE | re.MULTILINE)
                if found_matches:
                    matches.extend(found_matches)
            
            if matches:
                matched_patterns.append((pattern, matches))
        
        # Sort by confidence and number of matches
        matched_patterns.sort(key=lambda x: (x[0].confidence_threshold, len(x[1])), reverse=True)
        
        return matched_patterns
    
    async def _ai_analyze_failure(self, workflow_run_id: str, failure_logs: str, context: Dict[str, Any], matched_patterns: List) -> Dict[str, Any]:
        """Use AI to analyze the failure"""
        
        # Prepare context information
        context_info = context or {}
        pattern_info = [
            {
                "name": pattern.name,
                "category": pattern.category,
                "matches": matches[:3]  # Limit matches for prompt
            }
            for pattern, matches in matched_patterns[:5]  # Top 5 patterns
        ]
        
        analysis_prompt = f"""
Analyze this CI/CD workflow failure and provide intelligent diagnosis:

WORKFLOW RUN ID: {workflow_run_id}

FAILURE LOGS:
{failure_logs[:5000]}  # Limit log size for prompt

CONTEXT:
{json.dumps(context_info, indent=2)}

MATCHED PATTERNS:
{json.dumps(pattern_info, indent=2)}

Please provide:
1. Root cause analysis
2. Failure type classification
3. Suggested fix strategy
4. Confidence score (0.0-1.0)
5. Whether this is auto-fixable
6. Affected files (if identifiable)
7. Estimated fix time in minutes

Respond in JSON format:
{{
    "root_cause": "detailed explanation",
    "failure_type": "build|test|deploy|dependency|network|resource|other",
    "suggested_fix": "specific fix recommendation",
    "confidence_score": 0.0-1.0,
    "auto_fixable": true|false,
    "affected_files": ["file1.py", "file2.py"],
    "estimated_fix_time": 30,
    "fix_strategy": "specific strategy name",
    "additional_context": "any additional insights"
}}
"""
        
        try:
            task = self.codegen_agent.run(prompt=analysis_prompt)
            
            # Wait for analysis with timeout
            timeout_count = 0
            while task.status not in ['completed', 'failed'] and timeout_count < 30:
                await asyncio.sleep(2)
                task.refresh()
                timeout_count += 1
            
            if task.status == 'completed':
                # Parse AI response
                try:
                    json_match = re.search(r'\{.*\}', task.result, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            logger.warning(f"AI analysis failed or timed out: {task.status}")
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
        
        # Return default analysis
        return {
            "root_cause": "Unable to determine root cause",
            "failure_type": "other",
            "suggested_fix": "Manual investigation required",
            "confidence_score": 0.1,
            "auto_fixable": False,
            "affected_files": [],
            "estimated_fix_time": 60,
            "fix_strategy": "manual_investigation"
        }
    
    def _combine_analysis_results(self, workflow_run_id: str, matched_patterns: List, ai_analysis: Dict, failure_logs: str) -> FailureAnalysis:
        """Combine pattern matching and AI analysis results"""
        
        # Use best matched pattern if available
        if matched_patterns:
            best_pattern, best_matches = matched_patterns[0]
            failure_type = best_pattern.category
            confidence_boost = 0.2  # Boost confidence for pattern matches
        else:
            failure_type = ai_analysis.get("failure_type", "other")
            confidence_boost = 0.0
        
        # Extract error patterns from logs
        error_patterns = []
        for pattern, matches in matched_patterns[:3]:
            error_patterns.extend(matches[:2])  # Top 2 matches per pattern
        
        # Determine auto-fixability
        auto_fixable = False
        if matched_patterns:
            best_pattern = matched_patterns[0][0]
            auto_fixable = (
                best_pattern.auto_fix and
                ai_analysis.get("auto_fixable", False) and
                ai_analysis.get("confidence_score", 0.0) >= best_pattern.confidence_threshold
            )
        
        return FailureAnalysis(
            id=f"analysis_{workflow_run_id}_{int(datetime.now().timestamp())}",
            workflow_run_id=workflow_run_id,
            failure_type=failure_type,
            root_cause=ai_analysis.get("root_cause", "Unknown failure"),
            suggested_fix=ai_analysis.get("suggested_fix", "Manual investigation required"),
            confidence_score=min(1.0, ai_analysis.get("confidence_score", 0.1) + confidence_boost),
            auto_fixable=auto_fixable,
            affected_files=ai_analysis.get("affected_files", []),
            error_patterns=error_patterns,
            fix_applied=False,
            analysis_timestamp=datetime.now(),
            estimated_fix_time=ai_analysis.get("estimated_fix_time", 60)
        )
    
    async def _learn_from_failure(self, analysis: FailureAnalysis, failure_logs: str):
        """Learn from failure to improve future analysis"""
        
        # This would implement machine learning to improve pattern recognition
        # For now, we'll just log the learning opportunity
        logger.info(f"Learning opportunity: {analysis.failure_type} - {analysis.root_cause}")
    
    async def attempt_auto_fix(self, analysis: FailureAnalysis) -> Optional[AutoFixResult]:
        """Attempt to automatically fix the failure"""
        
        if not self.auto_fix_enabled:
            logger.info("Auto-fix is disabled")
            return None
        
        if not analysis.auto_fixable:
            logger.info(f"Failure {analysis.id} is not auto-fixable")
            return None
        
        if analysis.confidence_score < self.auto_fix_confidence_threshold:
            logger.info(f"Confidence score {analysis.confidence_score} below threshold {self.auto_fix_confidence_threshold}")
            return None
        
        # Check daily limit
        self._check_daily_limit()
        if self.daily_fix_count >= self.max_auto_fixes_per_day:
            logger.warning(f"Daily auto-fix limit reached: {self.daily_fix_count}/{self.max_auto_fixes_per_day}")
            return None
        
        logger.info(f"🔧 Attempting auto-fix for failure {analysis.id}")
        
        try:
            # Determine fix strategy
            fix_strategy = self._determine_fix_strategy(analysis)
            
            # Apply fix
            fix_result = await self._apply_fix(analysis, fix_strategy)
            
            # Update counters
            if fix_result.success:
                self.daily_fix_count += 1
            
            # Store fix result
            self.fix_history.append(fix_result)
            
            # Mark analysis as fixed
            analysis.fix_applied = fix_result.success
            
            # Notify callbacks
            await self._notify_fix_callbacks(fix_result)
            
            logger.info(f"{'✅' if fix_result.success else '❌'} Auto-fix {'completed' if fix_result.success else 'failed'}: {fix_result.fix_id}")
            
            return fix_result
            
        except Exception as e:
            logger.error(f"❌ Auto-fix failed: {e}")
            return AutoFixResult(
                fix_id=f"fix_{analysis.id}_{int(datetime.now().timestamp())}",
                failure_analysis_id=analysis.id,
                fix_strategy="error",
                success=False,
                changes_made=[],
                pr_created=None,
                rollback_available=False,
                execution_time=0,
                error_message=str(e),
                created_at=datetime.now()
            )
    
    def _determine_fix_strategy(self, analysis: FailureAnalysis) -> str:
        """Determine the appropriate fix strategy"""
        
        # Map failure types to fix strategies
        strategy_map = {
            "build": "rebuild_and_fix_compilation",
            "test": "optimize_and_retry_tests",
            "dependency": "resolve_dependency_conflicts",
            "network": "retry_with_exponential_backoff",
            "resource": "increase_resource_limits"
        }
        
        return strategy_map.get(analysis.failure_type, "generic_fix_attempt")
    
    async def _apply_fix(self, analysis: FailureAnalysis, fix_strategy: str) -> AutoFixResult:
        """Apply the fix using Codegen AI"""
        
        fix_id = f"fix_{analysis.id}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        # Build fix prompt
        fix_prompt = f"""
Apply an automatic fix for this CI/CD failure:

FAILURE ANALYSIS:
- ID: {analysis.id}
- Type: {analysis.failure_type}
- Root Cause: {analysis.root_cause}
- Confidence: {analysis.confidence_score}
- Affected Files: {analysis.affected_files}
- Error Patterns: {analysis.error_patterns}

FIX STRATEGY: {fix_strategy}

SUGGESTED FIX: {analysis.suggested_fix}

Please:
1. Implement the suggested fix
2. Test the changes
3. Create a PR with the fix
4. Provide rollback instructions

{"DRY RUN MODE: Only analyze and suggest changes, do not apply them." if self.auto_fix_dry_run else ""}
{"APPROVAL REQUIRED: Create PR but do not merge automatically." if self.auto_fix_require_approval else ""}

Create PR with title: "🤖 Auto-fix: {analysis.failure_type} failure in workflow {analysis.workflow_run_id}"

Include in PR description:
- Root cause analysis
- Changes made
- Testing performed
- Rollback instructions
"""
        
        try:
            task = self.codegen_agent.run(prompt=fix_prompt)
            
            # Wait for completion with timeout
            timeout_count = 0
            while task.status not in ['completed', 'failed'] and timeout_count < 120:  # 4 minute timeout
                await asyncio.sleep(2)
                task.refresh()
                timeout_count += 1
            
            execution_time = int((datetime.now() - start_time).total_seconds())
            
            if task.status == 'completed':
                # Parse result for PR link and changes
                pr_link = self._extract_pr_link(task.result)
                changes_made = self._extract_changes_made(task.result)
                
                return AutoFixResult(
                    fix_id=fix_id,
                    failure_analysis_id=analysis.id,
                    fix_strategy=fix_strategy,
                    success=True,
                    changes_made=changes_made,
                    pr_created=pr_link,
                    rollback_available=True,
                    execution_time=execution_time,
                    error_message=None,
                    created_at=datetime.now()
                )
            else:
                return AutoFixResult(
                    fix_id=fix_id,
                    failure_analysis_id=analysis.id,
                    fix_strategy=fix_strategy,
                    success=False,
                    changes_made=[],
                    pr_created=None,
                    rollback_available=False,
                    execution_time=execution_time,
                    error_message=f"Fix task failed: {task.result}",
                    created_at=datetime.now()
                )
        
        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds())
            return AutoFixResult(
                fix_id=fix_id,
                failure_analysis_id=analysis.id,
                fix_strategy=fix_strategy,
                success=False,
                changes_made=[],
                pr_created=None,
                rollback_available=False,
                execution_time=execution_time,
                error_message=str(e),
                created_at=datetime.now()
            )
    
    def _extract_pr_link(self, result_text: str) -> Optional[str]:
        """Extract PR link from result text"""
        pr_patterns = [
            r'https://github\.com/[^/]+/[^/]+/pull/\d+',
            r'PR #(\d+)',
            r'pull request.*?(\d+)'
        ]
        
        for pattern in pr_patterns:
            match = re.search(pattern, result_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_changes_made(self, result_text: str) -> List[str]:
        """Extract list of changes made from result text"""
        changes = []
        
        # Look for common change indicators
        change_patterns = [
            r'- (Fixed|Updated|Modified|Added|Removed).*',
            r'\* (Fixed|Updated|Modified|Added|Removed).*',
            r'\d+\. (Fixed|Updated|Modified|Added|Removed).*'
        ]
        
        for pattern in change_patterns:
            matches = re.findall(pattern, result_text, re.IGNORECASE | re.MULTILINE)
            changes.extend(matches)
        
        return changes[:10]  # Limit to 10 changes
    
    def _check_daily_limit(self):
        """Check and reset daily fix counter if needed"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_fix_count = 0
            self.last_reset_date = current_date
    
    def _get_empty_analysis(self, workflow_run_id: str) -> FailureAnalysis:
        """Get empty failure analysis"""
        return FailureAnalysis(
            id=f"analysis_{workflow_run_id}_empty",
            workflow_run_id=workflow_run_id,
            failure_type="unknown",
            root_cause="Analysis not available",
            suggested_fix="Manual investigation required",
            confidence_score=0.0,
            auto_fixable=False,
            affected_files=[],
            error_patterns=[],
            fix_applied=False,
            analysis_timestamp=datetime.now(),
            estimated_fix_time=None
        )
    
    async def _notify_failure_callbacks(self, analysis: FailureAnalysis):
        """Notify registered callbacks about failure analysis"""
        for callback in self.failure_callbacks:
            try:
                await callback(analysis)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}")
    
    async def _notify_fix_callbacks(self, fix_result: AutoFixResult):
        """Notify registered callbacks about fix results"""
        for callback in self.fix_callbacks:
            try:
                await callback(fix_result)
            except Exception as e:
                logger.error(f"Error in fix callback: {e}")
    
    # Public API methods
    
    def add_failure_callback(self, callback: callable):
        """Add callback for failure analysis notifications"""
        self.failure_callbacks.append(callback)
    
    def add_fix_callback(self, callback: callable):
        """Add callback for fix result notifications"""
        self.fix_callbacks.append(callback)
    
    def add_pattern_callback(self, callback: callable):
        """Add callback for new pattern notifications"""
        self.pattern_callbacks.append(callback)
    
    def get_failure_statistics(self, days: int = 30) -> FailureStatistics:
        """Get failure and fix statistics"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_failures = [f for f in self.failure_history if f.analysis_timestamp >= cutoff_date]
        recent_fixes = [f for f in self.fix_history if f.created_at >= cutoff_date]
        
        total_failures = len(recent_failures)
        auto_fixed = len([f for f in recent_fixes if f.success])
        manual_required = total_failures - auto_fixed
        
        # Calculate success rate
        fix_success_rate = (auto_fixed / total_failures) if total_failures > 0 else 0.0
        
        # Common failure types
        failure_types = {}
        for failure in recent_failures:
            failure_types[failure.failure_type] = failure_types.get(failure.failure_type, 0) + 1
        
        # Average fix time
        successful_fixes = [f for f in recent_fixes if f.success]
        avg_fix_time = sum(f.execution_time for f in successful_fixes) / len(successful_fixes) if successful_fixes else 0.0
        
        return FailureStatistics(
            total_failures=total_failures,
            auto_fixed_failures=auto_fixed,
            manual_fixes_required=manual_required,
            fix_success_rate=fix_success_rate,
            common_failure_types=failure_types,
            avg_fix_time=avg_fix_time,
            time_period=f"{days} days"
        )
    
    def get_recent_failures(self, limit: int = 10) -> List[FailureAnalysis]:
        """Get recent failure analyses"""
        return sorted(self.failure_history, key=lambda x: x.analysis_timestamp, reverse=True)[:limit]
    
    def get_recent_fixes(self, limit: int = 10) -> List[AutoFixResult]:
        """Get recent fix results"""
        return sorted(self.fix_history, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get failure analysis data for dashboard display"""
        
        stats = self.get_failure_statistics()
        recent_failures = self.get_recent_failures(5)
        recent_fixes = self.get_recent_fixes(5)
        
        return {
            "statistics": {
                "total_failures": stats.total_failures,
                "auto_fixed_failures": stats.auto_fixed_failures,
                "manual_fixes_required": stats.manual_fixes_required,
                "fix_success_rate": stats.fix_success_rate,
                "avg_fix_time": stats.avg_fix_time,
                "common_failure_types": stats.common_failure_types
            },
            "recent_failures": [
                {
                    "id": f.id,
                    "workflow_run_id": f.workflow_run_id,
                    "failure_type": f.failure_type,
                    "root_cause": f.root_cause,
                    "confidence_score": f.confidence_score,
                    "auto_fixable": f.auto_fixable,
                    "fix_applied": f.fix_applied,
                    "analysis_timestamp": f.analysis_timestamp.isoformat(),
                    "estimated_fix_time": f.estimated_fix_time
                }
                for f in recent_failures
            ],
            "recent_fixes": [
                {
                    "fix_id": f.fix_id,
                    "fix_strategy": f.fix_strategy,
                    "success": f.success,
                    "changes_made": f.changes_made,
                    "pr_created": f.pr_created,
                    "execution_time": f.execution_time,
                    "created_at": f.created_at.isoformat()
                }
                for f in recent_fixes
            ],
            "configuration": {
                "analysis_enabled": self.analysis_enabled,
                "auto_recovery_enabled": self.auto_recovery_enabled,
                "auto_fix_enabled": self.auto_fix_enabled,
                "auto_fix_dry_run": self.auto_fix_dry_run,
                "confidence_threshold": self.auto_fix_confidence_threshold,
                "daily_fix_limit": self.max_auto_fixes_per_day,
                "daily_fixes_used": self.daily_fix_count
            }
        }

