"""
Self-Healing Pipeline - Autonomous CI/CD pipeline that can diagnose and fix itself.

This module provides advanced self-healing capabilities for CI/CD pipelines:
- Real-time failure detection and classification
- Intelligent root cause analysis using Codegen SDK
- Automated fix generation and application
- Learning from past failures to prevent recurrence
- Predictive maintenance and optimization
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

# Graph-Sitter imports
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

# Codegen SDK imports
from codegen import Agent

logger = get_logger(__name__)

class HealingStatus(Enum):
    """Status of healing attempts."""
    NOT_STARTED = "not_started"
    ANALYZING = "analyzing"
    GENERATING_FIX = "generating_fix"
    APPLYING_FIX = "applying_fix"
    TESTING_FIX = "testing_fix"
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_HUMAN = "requires_human"

class FailureType(Enum):
    """Types of pipeline failures that can be healed."""
    TEST_FAILURE = "test_failure"
    BUILD_ERROR = "build_error"
    LINT_ERROR = "lint_error"
    DEPENDENCY_ERROR = "dependency_error"
    CONFIGURATION_ERROR = "configuration_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    TIMEOUT_ERROR = "timeout_error"
    FLAKY_TEST = "flaky_test"

class HealingStrategy(Enum):
    """Strategies for healing different types of failures."""
    CODE_FIX = "code_fix"
    DEPENDENCY_UPDATE = "dependency_update"
    CONFIG_ADJUSTMENT = "config_adjustment"
    TEST_STABILIZATION = "test_stabilization"
    INFRASTRUCTURE_REPAIR = "infrastructure_repair"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    ROLLBACK = "rollback"

@dataclass
class FailureContext:
    """Context information about a pipeline failure."""
    workflow_run_id: str
    job_name: str
    step_name: str
    failure_type: FailureType
    error_message: str
    error_logs: str
    affected_files: List[str]
    commit_sha: str
    branch_name: str
    timestamp: datetime
    previous_failures: List[str] = field(default_factory=list)

@dataclass
class HealingPlan:
    """Plan for healing a pipeline failure."""
    strategy: HealingStrategy
    description: str
    estimated_success_rate: float
    estimated_time_minutes: int
    required_changes: List[str]
    rollback_plan: str
    confidence_score: float
    automated: bool = True

@dataclass
class HealingResult:
    """Result of a healing attempt."""
    status: HealingStatus
    plan_executed: Optional[HealingPlan]
    changes_made: List[str]
    new_workflow_run_id: Optional[str]
    success: bool
    error_message: Optional[str]
    execution_time_minutes: float
    lessons_learned: List[str]

class SelfHealingPipeline:
    """
    Self-healing CI/CD pipeline that can automatically diagnose and fix failures.
    
    Uses Codegen SDK for intelligent analysis and fix generation, combined with
    Graph-Sitter for codebase understanding and manipulation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize Codegen SDK agent
        self.codegen_agent = Agent(
            org_id=self.config.get('codegen_org_id'),
            token=self.config.get('codegen_token'),
            base_url=self.config.get('codegen_base_url', 'https://api.codegen.com')
        )
        
        # Healing configuration
        self.max_healing_attempts = self.config.get('max_healing_attempts', 3)
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.7)
        self.enable_automated_fixes = self.config.get('enable_automated_fixes', True)
        self.enable_learning = self.config.get('enable_learning', True)
        self.max_fix_time_minutes = self.config.get('max_fix_time_minutes', 30)
        
        # State tracking
        self.healing_history: Dict[str, List[HealingResult]] = {}
        self.learned_patterns: Dict[str, Dict[str, Any]] = {}
        self.failure_patterns: Dict[str, int] = {}
        
        # Callbacks
        self.healing_callbacks: List[Callable] = []
        self.success_callbacks: List[Callable] = []
        self.failure_callbacks: List[Callable] = []
        
        # Initialize codebase for context
        self.codebase = None
        if 'codebase_path' in self.config:
            self.codebase = Codebase(self.config['codebase_path'])
    
    async def heal_failure(self, failure_context: FailureContext) -> HealingResult:
        """
        Attempt to heal a pipeline failure automatically.
        
        Args:
            failure_context: Context information about the failure
            
        Returns:
            Result of the healing attempt
        """
        logger.info(f"Starting self-healing for workflow {failure_context.workflow_run_id}")
        
        start_time = datetime.now()
        
        try:
            # Check if we've seen this failure pattern before
            similar_failures = await self._find_similar_failures(failure_context)
            
            # Generate healing plan
            healing_plan = await self._generate_healing_plan(failure_context, similar_failures)
            
            if not healing_plan:
                return HealingResult(
                    status=HealingStatus.FAILED,
                    plan_executed=None,
                    changes_made=[],
                    new_workflow_run_id=None,
                    success=False,
                    error_message="Could not generate healing plan",
                    execution_time_minutes=0,
                    lessons_learned=[]
                )
            
            # Check if plan meets confidence threshold
            if healing_plan.confidence_score < self.min_confidence_threshold:
                logger.warning(f"Healing plan confidence too low: {healing_plan.confidence_score}")
                return HealingResult(
                    status=HealingStatus.REQUIRES_HUMAN,
                    plan_executed=healing_plan,
                    changes_made=[],
                    new_workflow_run_id=None,
                    success=False,
                    error_message="Confidence threshold not met",
                    execution_time_minutes=0,
                    lessons_learned=["Low confidence healing plan generated"]
                )
            
            # Execute healing plan
            if self.enable_automated_fixes and healing_plan.automated:
                result = await self._execute_healing_plan(failure_context, healing_plan)
            else:
                result = HealingResult(
                    status=HealingStatus.REQUIRES_HUMAN,
                    plan_executed=healing_plan,
                    changes_made=[],
                    new_workflow_run_id=None,
                    success=False,
                    error_message="Automated fixes disabled",
                    execution_time_minutes=0,
                    lessons_learned=["Automated healing disabled"]
                )
            
            # Record execution time
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            result.execution_time_minutes = execution_time
            
            # Store healing result
            workflow_id = failure_context.workflow_run_id
            if workflow_id not in self.healing_history:
                self.healing_history[workflow_id] = []
            self.healing_history[workflow_id].append(result)
            
            # Learn from the result
            if self.enable_learning:
                await self._learn_from_healing_result(failure_context, result)
            
            # Call appropriate callbacks
            if result.success:
                for callback in self.success_callbacks:
                    await callback(failure_context, result)
            else:
                for callback in self.failure_callbacks:
                    await callback(failure_context, result)
            
            for callback in self.healing_callbacks:
                await callback(failure_context, result)
            
            logger.info(f"Healing completed: status={result.status.value}, success={result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Error during healing attempt: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            
            return HealingResult(
                status=HealingStatus.FAILED,
                plan_executed=None,
                changes_made=[],
                new_workflow_run_id=None,
                success=False,
                error_message=str(e),
                execution_time_minutes=execution_time,
                lessons_learned=[f"Healing failed with exception: {str(e)}"]
            )
    
    async def _find_similar_failures(self, failure_context: FailureContext) -> List[Dict[str, Any]]:
        """Find similar failures from history to inform healing strategy."""
        similar_failures = []
        
        # Look for failures with similar error messages
        for workflow_id, healing_results in self.healing_history.items():
            for result in healing_results:
                if result.plan_executed:
                    # Simple similarity check based on error message keywords
                    error_keywords = set(failure_context.error_message.lower().split())
                    if hasattr(result, 'original_error'):
                        result_keywords = set(result.original_error.lower().split())
                        similarity = len(error_keywords.intersection(result_keywords)) / len(error_keywords.union(result_keywords))
                        
                        if similarity > 0.3:  # 30% similarity threshold
                            similar_failures.append({
                                'workflow_id': workflow_id,
                                'result': result,
                                'similarity': similarity
                            })
        
        # Sort by similarity and success
        similar_failures.sort(key=lambda x: (x['result'].success, x['similarity']), reverse=True)
        return similar_failures[:5]  # Return top 5 similar failures
    
    async def _generate_healing_plan(
        self, 
        failure_context: FailureContext, 
        similar_failures: List[Dict[str, Any]]
    ) -> Optional[HealingPlan]:
        """Generate an intelligent healing plan using Codegen SDK."""
        logger.info("Generating healing plan")
        
        try:
            # Prepare context for AI analysis
            similar_context = ""
            if similar_failures:
                similar_context = "Similar failures and their solutions:\n"
                for failure in similar_failures:
                    result = failure['result']
                    similar_context += f"- Success: {result.success}, Changes: {', '.join(result.changes_made)}\n"
            
            prompt = f"""
            Analyze this CI/CD pipeline failure and generate a healing plan:
            
            Failure Details:
            - Type: {failure_context.failure_type.value}
            - Job: {failure_context.job_name}
            - Step: {failure_context.step_name}
            - Error: {failure_context.error_message}
            - Affected Files: {', '.join(failure_context.affected_files)}
            - Branch: {failure_context.branch_name}
            
            Error Logs:
            {failure_context.error_logs[:2000]}  # Limit log size
            
            {similar_context}
            
            Generate a healing plan with:
            1. Strategy (code_fix, dependency_update, config_adjustment, test_stabilization, infrastructure_repair, retry_with_backoff, rollback)
            2. Description of what needs to be done
            3. Estimated success rate (0.0-1.0)
            4. Estimated time in minutes
            5. Required changes (specific actions)
            6. Rollback plan
            7. Confidence score (0.0-1.0)
            8. Whether it can be automated (true/false)
            
            Focus on minimal, targeted fixes that address the root cause.
            Return as JSON format.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            # Parse healing plan from result
            plan = self._parse_healing_plan(task.result)
            
            if plan:
                logger.info(f"Generated healing plan: {plan.strategy.value} (confidence: {plan.confidence_score:.2f})")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating healing plan: {e}")
            return None
    
    async def _execute_healing_plan(
        self, 
        failure_context: FailureContext, 
        healing_plan: HealingPlan
    ) -> HealingResult:
        """Execute the healing plan."""
        logger.info(f"Executing healing plan: {healing_plan.strategy.value}")
        
        changes_made = []
        lessons_learned = []
        
        try:
            if healing_plan.strategy == HealingStrategy.CODE_FIX:
                changes_made = await self._apply_code_fixes(failure_context, healing_plan)
            
            elif healing_plan.strategy == HealingStrategy.DEPENDENCY_UPDATE:
                changes_made = await self._update_dependencies(failure_context, healing_plan)
            
            elif healing_plan.strategy == HealingStrategy.CONFIG_ADJUSTMENT:
                changes_made = await self._adjust_configuration(failure_context, healing_plan)
            
            elif healing_plan.strategy == HealingStrategy.TEST_STABILIZATION:
                changes_made = await self._stabilize_tests(failure_context, healing_plan)
            
            elif healing_plan.strategy == HealingStrategy.RETRY_WITH_BACKOFF:
                changes_made = await self._retry_with_backoff(failure_context, healing_plan)
            
            else:
                return HealingResult(
                    status=HealingStatus.FAILED,
                    plan_executed=healing_plan,
                    changes_made=[],
                    new_workflow_run_id=None,
                    success=False,
                    error_message=f"Strategy {healing_plan.strategy.value} not implemented",
                    execution_time_minutes=0,
                    lessons_learned=["Unsupported healing strategy"]
                )
            
            # If changes were made, trigger a new pipeline run
            new_workflow_run_id = None
            if changes_made:
                new_workflow_run_id = await self._trigger_new_pipeline_run(failure_context)
                lessons_learned.append(f"Applied {len(changes_made)} changes and triggered new run")
            
            # Wait for new run to complete (with timeout)
            if new_workflow_run_id:
                success = await self._wait_for_pipeline_completion(
                    new_workflow_run_id, 
                    timeout_minutes=healing_plan.estimated_time_minutes + 10
                )
            else:
                success = len(changes_made) > 0
            
            status = HealingStatus.SUCCESS if success else HealingStatus.FAILED
            
            return HealingResult(
                status=status,
                plan_executed=healing_plan,
                changes_made=changes_made,
                new_workflow_run_id=new_workflow_run_id,
                success=success,
                error_message=None,
                execution_time_minutes=0,  # Will be set by caller
                lessons_learned=lessons_learned
            )
            
        except Exception as e:
            logger.error(f"Error executing healing plan: {e}")
            return HealingResult(
                status=HealingStatus.FAILED,
                plan_executed=healing_plan,
                changes_made=changes_made,
                new_workflow_run_id=None,
                success=False,
                error_message=str(e),
                execution_time_minutes=0,
                lessons_learned=[f"Execution failed: {str(e)}"]
            )
    
    async def _apply_code_fixes(
        self, 
        failure_context: FailureContext, 
        healing_plan: HealingPlan
    ) -> List[str]:
        """Apply code fixes based on the healing plan."""
        logger.info("Applying code fixes")
        
        try:
            prompt = f"""
            Apply code fixes for the following failure:
            
            Error: {failure_context.error_message}
            Affected Files: {', '.join(failure_context.affected_files)}
            Required Changes: {', '.join(healing_plan.required_changes)}
            
            Make minimal, targeted fixes to resolve the issue.
            Create a commit with the changes and push to branch {failure_context.branch_name}.
            
            Return a list of specific changes made.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            # Parse changes from result
            changes = self._parse_changes_made(task.result)
            
            logger.info(f"Applied {len(changes)} code fixes")
            return changes
            
        except Exception as e:
            logger.error(f"Error applying code fixes: {e}")
            return []
    
    async def _update_dependencies(
        self, 
        failure_context: FailureContext, 
        healing_plan: HealingPlan
    ) -> List[str]:
        """Update dependencies to fix the failure."""
        logger.info("Updating dependencies")
        
        try:
            prompt = f"""
            Fix dependency issues for the following failure:
            
            Error: {failure_context.error_message}
            Required Changes: {', '.join(healing_plan.required_changes)}
            
            Update package dependencies, requirements files, or lock files as needed.
            Create a commit with the changes and push to branch {failure_context.branch_name}.
            
            Return a list of dependency changes made.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            changes = self._parse_changes_made(task.result)
            
            logger.info(f"Updated {len(changes)} dependencies")
            return changes
            
        except Exception as e:
            logger.error(f"Error updating dependencies: {e}")
            return []
    
    async def _adjust_configuration(
        self, 
        failure_context: FailureContext, 
        healing_plan: HealingPlan
    ) -> List[str]:
        """Adjust configuration files to fix the failure."""
        logger.info("Adjusting configuration")
        
        try:
            prompt = f"""
            Fix configuration issues for the following failure:
            
            Error: {failure_context.error_message}
            Job: {failure_context.job_name}
            Required Changes: {', '.join(healing_plan.required_changes)}
            
            Update CI/CD configuration files, environment variables, or settings as needed.
            Create a commit with the changes and push to branch {failure_context.branch_name}.
            
            Return a list of configuration changes made.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            changes = self._parse_changes_made(task.result)
            
            logger.info(f"Made {len(changes)} configuration adjustments")
            return changes
            
        except Exception as e:
            logger.error(f"Error adjusting configuration: {e}")
            return []
    
    async def _stabilize_tests(
        self, 
        failure_context: FailureContext, 
        healing_plan: HealingPlan
    ) -> List[str]:
        """Stabilize flaky or failing tests."""
        logger.info("Stabilizing tests")
        
        try:
            prompt = f"""
            Fix test failures for the following issue:
            
            Error: {failure_context.error_message}
            Affected Files: {', '.join(failure_context.affected_files)}
            Required Changes: {', '.join(healing_plan.required_changes)}
            
            Fix flaky tests, add missing assertions, or update test expectations.
            Create a commit with the changes and push to branch {failure_context.branch_name}.
            
            Return a list of test changes made.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            changes = self._parse_changes_made(task.result)
            
            logger.info(f"Stabilized {len(changes)} tests")
            return changes
            
        except Exception as e:
            logger.error(f"Error stabilizing tests: {e}")
            return []
    
    async def _retry_with_backoff(
        self, 
        failure_context: FailureContext, 
        healing_plan: HealingPlan
    ) -> List[str]:
        """Retry the pipeline with exponential backoff."""
        logger.info("Retrying with backoff")
        
        try:
            # Simply trigger a retry - no code changes needed
            await asyncio.sleep(60)  # Wait 1 minute before retry
            
            return ["Triggered pipeline retry with backoff"]
            
        except Exception as e:
            logger.error(f"Error retrying pipeline: {e}")
            return []
    
    async def _trigger_new_pipeline_run(self, failure_context: FailureContext) -> Optional[str]:
        """Trigger a new pipeline run after applying fixes."""
        try:
            prompt = f"""
            Trigger a new CI/CD pipeline run for branch {failure_context.branch_name}
            after applying healing fixes.
            
            Use the GitHub API to trigger the workflow.
            Return the new workflow run ID.
            """
            
            task = self.codegen_agent.run(prompt=prompt)
            
            while task.status != "completed":
                await asyncio.sleep(3)
                task.refresh()
            
            # Extract workflow run ID from result
            result = task.result
            for word in result.split():
                if word.isdigit() and len(word) > 8:  # Workflow run IDs are long numbers
                    return word
            
            return None
            
        except Exception as e:
            logger.error(f"Error triggering new pipeline run: {e}")
            return None
    
    async def _wait_for_pipeline_completion(self, workflow_run_id: str, timeout_minutes: int) -> bool:
        """Wait for pipeline completion and return success status."""
        logger.info(f"Waiting for pipeline {workflow_run_id} to complete")
        
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            try:
                prompt = f"""
                Check the status of GitHub workflow run {workflow_run_id}.
                Return 'success', 'failure', or 'running'.
                """
                
                task = self.codegen_agent.run(prompt=prompt)
                
                while task.status != "completed":
                    await asyncio.sleep(5)
                    task.refresh()
                
                status = task.result.lower().strip()
                
                if "success" in status:
                    logger.info(f"Pipeline {workflow_run_id} completed successfully")
                    return True
                elif "failure" in status or "failed" in status:
                    logger.warning(f"Pipeline {workflow_run_id} failed")
                    return False
                
                # Still running, wait and check again
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error checking pipeline status: {e}")
                await asyncio.sleep(30)
        
        logger.warning(f"Pipeline {workflow_run_id} timed out after {timeout_minutes} minutes")
        return False
    
    async def _learn_from_healing_result(self, failure_context: FailureContext, result: HealingResult):
        """Learn from healing results to improve future healing."""
        logger.info("Learning from healing result")
        
        try:
            # Record failure pattern
            pattern_key = f"{failure_context.failure_type.value}:{failure_context.job_name}"
            self.failure_patterns[pattern_key] = self.failure_patterns.get(pattern_key, 0) + 1
            
            # Store successful healing strategies
            if result.success and result.plan_executed:
                strategy_key = f"{failure_context.failure_type.value}:{result.plan_executed.strategy.value}"
                
                if strategy_key not in self.learned_patterns:
                    self.learned_patterns[strategy_key] = {
                        'success_count': 0,
                        'total_attempts': 0,
                        'average_time': 0,
                        'common_changes': []
                    }
                
                pattern = self.learned_patterns[strategy_key]
                pattern['total_attempts'] += 1
                
                if result.success:
                    pattern['success_count'] += 1
                    pattern['average_time'] = (
                        pattern['average_time'] + result.execution_time_minutes
                    ) / 2
                    pattern['common_changes'].extend(result.changes_made)
            
            logger.info(f"Updated learning patterns: {len(self.learned_patterns)} strategies learned")
            
        except Exception as e:
            logger.error(f"Error learning from result: {e}")
    
    def _parse_healing_plan(self, result: str) -> Optional[HealingPlan]:
        """Parse healing plan from AI result."""
        try:
            # Try to parse as JSON
            import json
            data = json.loads(result)
            
            return HealingPlan(
                strategy=HealingStrategy(data.get('strategy', 'code_fix')),
                description=data.get('description', ''),
                estimated_success_rate=data.get('estimated_success_rate', 0.5),
                estimated_time_minutes=data.get('estimated_time_minutes', 15),
                required_changes=data.get('required_changes', []),
                rollback_plan=data.get('rollback_plan', ''),
                confidence_score=data.get('confidence_score', 0.5),
                automated=data.get('automated', True)
            )
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback to text parsing
            logger.warning("Failed to parse JSON healing plan, using text parsing")
            return self._parse_plan_from_text(result)
    
    def _parse_plan_from_text(self, text: str) -> Optional[HealingPlan]:
        """Parse healing plan from plain text."""
        try:
            lines = text.split('\n')
            
            # Extract basic information
            strategy = HealingStrategy.CODE_FIX  # Default
            description = "Auto-generated healing plan"
            confidence_score = 0.5
            
            for line in lines:
                line = line.lower().strip()
                if 'strategy' in line:
                    if 'dependency' in line:
                        strategy = HealingStrategy.DEPENDENCY_UPDATE
                    elif 'config' in line:
                        strategy = HealingStrategy.CONFIG_ADJUSTMENT
                    elif 'test' in line:
                        strategy = HealingStrategy.TEST_STABILIZATION
                    elif 'retry' in line:
                        strategy = HealingStrategy.RETRY_WITH_BACKOFF
                
                if 'confidence' in line:
                    words = line.split()
                    for word in words:
                        try:
                            score = float(word)
                            if 0 <= score <= 1:
                                confidence_score = score
                                break
                        except ValueError:
                            continue
            
            return HealingPlan(
                strategy=strategy,
                description=description,
                estimated_success_rate=0.7,
                estimated_time_minutes=15,
                required_changes=["Apply automated fixes"],
                rollback_plan="Revert commit if needed",
                confidence_score=confidence_score,
                automated=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing plan from text: {e}")
            return None
    
    def _parse_changes_made(self, result: str) -> List[str]:
        """Parse changes made from AI result."""
        changes = []
        lines = result.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or 'changed' in line.lower()):
                changes.append(line.lstrip('-* '))
        
        return changes[:10]  # Limit to 10 changes
    
    async def get_healing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive healing statistics."""
        total_attempts = sum(len(results) for results in self.healing_history.values())
        successful_attempts = sum(
            1 for results in self.healing_history.values() 
            for result in results if result.success
        )
        
        success_rate = successful_attempts / total_attempts if total_attempts > 0 else 0
        
        # Strategy success rates
        strategy_stats = {}
        for results in self.healing_history.values():
            for result in results:
                if result.plan_executed:
                    strategy = result.plan_executed.strategy.value
                    if strategy not in strategy_stats:
                        strategy_stats[strategy] = {'attempts': 0, 'successes': 0}
                    
                    strategy_stats[strategy]['attempts'] += 1
                    if result.success:
                        strategy_stats[strategy]['successes'] += 1
        
        # Calculate strategy success rates
        for strategy, stats in strategy_stats.items():
            stats['success_rate'] = stats['successes'] / stats['attempts'] if stats['attempts'] > 0 else 0
        
        return {
            'total_healing_attempts': total_attempts,
            'successful_healings': successful_attempts,
            'overall_success_rate': success_rate,
            'strategy_statistics': strategy_stats,
            'learned_patterns': len(self.learned_patterns),
            'failure_patterns': dict(self.failure_patterns),
            'most_common_failure': max(self.failure_patterns.items(), key=lambda x: x[1])[0] if self.failure_patterns else None
        }
    
    def add_healing_callback(self, callback: Callable):
        """Add a callback for healing events."""
        self.healing_callbacks.append(callback)
    
    def add_success_callback(self, callback: Callable):
        """Add a callback for successful healing."""
        self.success_callbacks.append(callback)
    
    def add_failure_callback(self, callback: Callable):
        """Add a callback for failed healing."""
        self.failure_callbacks.append(callback)

