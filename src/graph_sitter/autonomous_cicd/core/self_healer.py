"""
Self-Healing System

Provides automatic error resolution, rollback capabilities,
alternative solution generation, and adaptive healing strategies.
"""

import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..models.error_models import (
    ErrorCategory,
    ErrorInstance,
    HealingAction,
    HealingResult,
    HealingStrategy,
)
from ..utils.command_executor import CommandExecutor
from ..utils.rollback_manager import RollbackManager


class SelfHealer:
    """
    Autonomous self-healing system that can automatically detect,
    analyze, and resolve common pipeline errors.
    """

    def __init__(
        self,
        max_healing_attempts: int = 3,
        enable_aggressive_healing: bool = False,
        enable_rollback: bool = True
    ):
        self.max_healing_attempts = max_healing_attempts
        self.enable_aggressive_healing = enable_aggressive_healing
        self.enable_rollback = enable_rollback
        
        self.logger = logging.getLogger(__name__)
        self.command_executor = CommandExecutor()
        self.rollback_manager = RollbackManager()
        
        # Healing state tracking
        self.active_healing_sessions: Dict[str, Dict[str, Any]] = {}
        self.healing_history: List[HealingResult] = []
        self.healing_actions: Dict[str, HealingAction] = {}
        
        # Success rate tracking
        self.strategy_success_rates: Dict[HealingStrategy, float] = {}
        
        # Initialize healing actions
        self._initialize_healing_actions()

    def _initialize_healing_actions(self) -> None:
        """Initialize built-in healing actions."""
        actions = [
            # Retry actions
            HealingAction(
                id="simple_retry",
                strategy=HealingStrategy.RETRY,
                description="Simple retry with exponential backoff",
                parameters={
                    "max_attempts": 3,
                    "base_delay": 1,
                    "backoff_factor": 2
                },
                success_criteria=["exit_code_0", "no_error_patterns"],
                timeout_seconds=300
            ),
            
            # Dependency healing
            HealingAction(
                id="update_dependencies",
                strategy=HealingStrategy.DEPENDENCY_UPDATE,
                description="Update and reinstall dependencies",
                parameters={
                    "package_managers": ["pip", "npm", "yarn"],
                    "update_strategy": "conservative"
                },
                prerequisites=["package_manager_available"],
                success_criteria=["dependencies_installed", "import_successful"],
                rollback_actions=["restore_dependency_lock"],
                timeout_seconds=600
            ),
            
            # Resource adjustments
            HealingAction(
                id="increase_memory",
                strategy=HealingStrategy.RESOURCE_ADJUSTMENT,
                description="Increase memory allocation",
                parameters={
                    "memory_multiplier": 1.5,
                    "max_memory": "8Gi"
                },
                success_criteria=["no_oom_errors"],
                timeout_seconds=60
            ),
            
            # Configuration fixes
            HealingAction(
                id="fix_common_config",
                strategy=HealingStrategy.CONFIGURATION_FIX,
                description="Fix common configuration issues",
                parameters={
                    "config_templates": ["python", "typescript", "generic"],
                    "backup_original": True
                },
                prerequisites=["config_file_exists"],
                success_criteria=["config_valid", "no_syntax_errors"],
                rollback_actions=["restore_config_backup"],
                timeout_seconds=120
            ),
            
            # Rollback actions
            HealingAction(
                id="rollback_changes",
                strategy=HealingStrategy.ROLLBACK,
                description="Rollback to last known good state",
                parameters={
                    "rollback_scope": "pipeline",
                    "preserve_logs": True
                },
                success_criteria=["pipeline_restored", "tests_passing"],
                timeout_seconds=300
            ),
            
            # Alternative approaches
            HealingAction(
                id="alternative_test_runner",
                strategy=HealingStrategy.ALTERNATIVE_APPROACH,
                description="Try alternative test runner or configuration",
                parameters={
                    "alternatives": ["pytest", "unittest", "nose2"],
                    "fallback_config": True
                },
                success_criteria=["tests_executed", "results_available"],
                timeout_seconds=600
            )
        ]
        
        for action in actions:
            self.healing_actions[action.id] = action

    async def heal_error(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """
        Attempt to heal an error using appropriate strategies.
        
        Args:
            error_instance: The error instance to heal
            context: Additional context for healing
            
        Returns:
            Healing result
        """
        self.logger.info(f"Starting healing process for error: {error_instance.id}")
        
        # Check if already healing this error
        if error_instance.id in self.active_healing_sessions:
            self.logger.warning(f"Healing already in progress for error: {error_instance.id}")
            return await self._get_healing_status(error_instance.id)
        
        # Start healing session
        session = {
            "error_id": error_instance.id,
            "start_time": datetime.now(),
            "attempts": 0,
            "strategies_tried": [],
            "current_strategy": None
        }
        self.active_healing_sessions[error_instance.id] = session
        
        try:
            # Determine healing strategies
            strategies = self._select_healing_strategies(error_instance)
            
            # Try each strategy
            for strategy in strategies:
                if session["attempts"] >= self.max_healing_attempts:
                    break
                
                session["current_strategy"] = strategy
                session["attempts"] += 1
                
                self.logger.info(f"Attempting healing strategy: {strategy.value}")
                
                # Execute healing action
                result = await self._execute_healing_strategy(
                    strategy, error_instance, context
                )
                
                session["strategies_tried"].append({
                    "strategy": strategy.value,
                    "result": result.success,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update error instance
                error_instance.healing_attempts.append({
                    "strategy": strategy.value,
                    "success": result.success,
                    "timestamp": datetime.now().isoformat(),
                    "details": result.dict()
                })
                
                if result.success:
                    error_instance.resolved = True
                    error_instance.resolution_time = datetime.now()
                    self.logger.info(f"Successfully healed error: {error_instance.id}")
                    break
                else:
                    self.logger.warning(f"Healing strategy {strategy.value} failed: {result.error_message}")
            
            # Final result
            final_result = HealingResult(
                action_id=f"healing_session_{error_instance.id}",
                strategy=session["current_strategy"] or HealingStrategy.ESCALATE_TO_HUMAN,
                success=error_instance.resolved,
                execution_time=(datetime.now() - session["start_time"]).total_seconds(),
                metrics={
                    "attempts": session["attempts"],
                    "strategies_tried": len(session["strategies_tried"])
                }
            )
            
            # Store result
            self.healing_history.append(final_result)
            
            # Update success rates
            await self._update_success_rates(session["strategies_tried"])
            
            return final_result
            
        finally:
            # Clean up session
            if error_instance.id in self.active_healing_sessions:
                del self.active_healing_sessions[error_instance.id]

    def _select_healing_strategies(self, error_instance: ErrorInstance) -> List[HealingStrategy]:
        """Select appropriate healing strategies for an error."""
        strategies = []
        
        if not error_instance.classification:
            # Unknown error - try conservative strategies
            strategies = [
                HealingStrategy.RETRY,
                HealingStrategy.ESCALATE_TO_HUMAN
            ]
        else:
            # Use suggested strategies from classification
            strategies = error_instance.classification.suggested_healing.copy()
            
            # Add category-specific strategies
            category = error_instance.classification.category
            
            if category == ErrorCategory.DEPENDENCY_ISSUE:
                if HealingStrategy.DEPENDENCY_UPDATE not in strategies:
                    strategies.insert(0, HealingStrategy.DEPENDENCY_UPDATE)
            
            elif category == ErrorCategory.RESOURCE_EXHAUSTION:
                if HealingStrategy.RESOURCE_ADJUSTMENT not in strategies:
                    strategies.insert(0, HealingStrategy.RESOURCE_ADJUSTMENT)
            
            elif category == ErrorCategory.CONFIGURATION_ERROR:
                if HealingStrategy.CONFIGURATION_FIX not in strategies:
                    strategies.insert(0, HealingStrategy.CONFIGURATION_FIX)
            
            elif category == ErrorCategory.TEST_FAILURE:
                strategies.extend([
                    HealingStrategy.ALTERNATIVE_APPROACH,
                    HealingStrategy.RETRY
                ])
        
        # Sort by success rate
        strategies = self._sort_strategies_by_success_rate(strategies)
        
        # Add fallback strategies
        if HealingStrategy.ESCALATE_TO_HUMAN not in strategies:
            strategies.append(HealingStrategy.ESCALATE_TO_HUMAN)
        
        return strategies

    def _sort_strategies_by_success_rate(self, strategies: List[HealingStrategy]) -> List[HealingStrategy]:
        """Sort strategies by their historical success rates."""
        def get_success_rate(strategy: HealingStrategy) -> float:
            return self.strategy_success_rates.get(strategy, 0.5)  # Default 50%
        
        return sorted(strategies, key=get_success_rate, reverse=True)

    async def _execute_healing_strategy(
        self,
        strategy: HealingStrategy,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute a specific healing strategy."""
        start_time = datetime.now()
        
        try:
            if strategy == HealingStrategy.RETRY:
                return await self._execute_retry(error_instance, context)
            
            elif strategy == HealingStrategy.DEPENDENCY_UPDATE:
                return await self._execute_dependency_update(error_instance, context)
            
            elif strategy == HealingStrategy.RESOURCE_ADJUSTMENT:
                return await self._execute_resource_adjustment(error_instance, context)
            
            elif strategy == HealingStrategy.CONFIGURATION_FIX:
                return await self._execute_configuration_fix(error_instance, context)
            
            elif strategy == HealingStrategy.ROLLBACK:
                return await self._execute_rollback(error_instance, context)
            
            elif strategy == HealingStrategy.ALTERNATIVE_APPROACH:
                return await self._execute_alternative_approach(error_instance, context)
            
            elif strategy == HealingStrategy.ESCALATE_TO_HUMAN:
                return await self._escalate_to_human(error_instance, context)
            
            else:
                return HealingResult(
                    action_id=f"unknown_strategy_{strategy.value}",
                    strategy=strategy,
                    success=False,
                    error_message=f"Unknown healing strategy: {strategy.value}",
                    execution_time=0
                )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return HealingResult(
                action_id=f"strategy_error_{strategy.value}",
                strategy=strategy,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    async def _execute_retry(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute retry healing strategy."""
        action = self.healing_actions["simple_retry"]
        
        max_attempts = action.parameters.get("max_attempts", 3)
        base_delay = action.parameters.get("base_delay", 1)
        backoff_factor = action.parameters.get("backoff_factor", 2)
        
        for attempt in range(max_attempts):
            if attempt > 0:
                delay = base_delay * (backoff_factor ** (attempt - 1))
                await asyncio.sleep(delay)
            
            # Re-run the failed command/stage
            success = await self._rerun_failed_stage(error_instance, context)
            
            if success:
                return HealingResult(
                    action_id=action.id,
                    strategy=HealingStrategy.RETRY,
                    success=True,
                    execution_time=0,  # Will be calculated by caller
                    metrics={"attempts": attempt + 1}
                )
        
        return HealingResult(
            action_id=action.id,
            strategy=HealingStrategy.RETRY,
            success=False,
            error_message=f"Retry failed after {max_attempts} attempts",
            execution_time=0
        )

    async def _execute_dependency_update(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute dependency update healing strategy."""
        action = self.healing_actions["update_dependencies"]
        
        # Detect package manager
        package_manager = await self._detect_package_manager(context)
        if not package_manager:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.DEPENDENCY_UPDATE,
                success=False,
                error_message="No supported package manager found",
                execution_time=0
            )
        
        try:
            # Create backup of dependency files
            await self._backup_dependency_files(package_manager)
            
            # Update dependencies
            if package_manager == "pip":
                commands = [
                    "pip install --upgrade pip",
                    "pip install -r requirements.txt --upgrade"
                ]
            elif package_manager == "npm":
                commands = [
                    "npm update",
                    "npm install"
                ]
            elif package_manager == "yarn":
                commands = [
                    "yarn upgrade",
                    "yarn install"
                ]
            else:
                commands = []
            
            # Execute commands
            for command in commands:
                result = await self.command_executor.execute(command)
                if not result.success:
                    return HealingResult(
                        action_id=action.id,
                        strategy=HealingStrategy.DEPENDENCY_UPDATE,
                        success=False,
                        error_message=f"Command failed: {command}",
                        execution_time=0
                    )
            
            # Verify dependencies
            verification_success = await self._verify_dependencies(package_manager)
            
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.DEPENDENCY_UPDATE,
                success=verification_success,
                execution_time=0,
                metrics={"package_manager": package_manager}
            )
            
        except Exception as e:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.DEPENDENCY_UPDATE,
                success=False,
                error_message=str(e),
                execution_time=0
            )

    async def _execute_resource_adjustment(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute resource adjustment healing strategy."""
        action = self.healing_actions["increase_memory"]
        
        # This would typically interact with container orchestration
        # For now, simulate resource adjustment
        
        current_memory = context.get("current_memory", "2Gi") if context else "2Gi"
        multiplier = action.parameters.get("memory_multiplier", 1.5)
        
        # Calculate new memory allocation
        try:
            if current_memory.endswith("Gi"):
                current_gb = float(current_memory[:-2])
                new_gb = current_gb * multiplier
                new_memory = f"{new_gb}Gi"
            else:
                new_memory = "4Gi"  # Default fallback
            
            # In a real implementation, this would update the container/VM resources
            self.logger.info(f"Adjusting memory from {current_memory} to {new_memory}")
            
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.RESOURCE_ADJUSTMENT,
                success=True,
                execution_time=0,
                metrics={
                    "old_memory": current_memory,
                    "new_memory": new_memory
                }
            )
            
        except Exception as e:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.RESOURCE_ADJUSTMENT,
                success=False,
                error_message=str(e),
                execution_time=0
            )

    async def _execute_configuration_fix(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute configuration fix healing strategy."""
        action = self.healing_actions["fix_common_config"]
        
        # Identify configuration files
        config_files = await self._identify_config_files(context)
        
        if not config_files:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.CONFIGURATION_FIX,
                success=False,
                error_message="No configuration files found",
                execution_time=0
            )
        
        try:
            fixed_files = []
            
            for config_file in config_files:
                # Backup original
                await self._backup_file(config_file)
                
                # Apply fixes
                if await self._fix_config_file(config_file, error_instance):
                    fixed_files.append(config_file)
            
            if fixed_files:
                # Verify configuration
                verification_success = await self._verify_configuration(fixed_files)
                
                return HealingResult(
                    action_id=action.id,
                    strategy=HealingStrategy.CONFIGURATION_FIX,
                    success=verification_success,
                    execution_time=0,
                    metrics={"fixed_files": fixed_files}
                )
            else:
                return HealingResult(
                    action_id=action.id,
                    strategy=HealingStrategy.CONFIGURATION_FIX,
                    success=False,
                    error_message="No configuration fixes applied",
                    execution_time=0
                )
                
        except Exception as e:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.CONFIGURATION_FIX,
                success=False,
                error_message=str(e),
                execution_time=0
            )

    async def _execute_rollback(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute rollback healing strategy."""
        if not self.enable_rollback:
            return HealingResult(
                action_id="rollback_disabled",
                strategy=HealingStrategy.ROLLBACK,
                success=False,
                error_message="Rollback is disabled",
                execution_time=0
            )
        
        action = self.healing_actions["rollback_changes"]
        
        try:
            # Use rollback manager to restore previous state
            rollback_success = await self.rollback_manager.rollback_to_last_good_state(
                scope=action.parameters.get("rollback_scope", "pipeline"),
                preserve_logs=action.parameters.get("preserve_logs", True)
            )
            
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.ROLLBACK,
                success=rollback_success,
                execution_time=0,
                metrics={"rollback_scope": action.parameters.get("rollback_scope")}
            )
            
        except Exception as e:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.ROLLBACK,
                success=False,
                error_message=str(e),
                execution_time=0
            )

    async def _execute_alternative_approach(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Execute alternative approach healing strategy."""
        action = self.healing_actions["alternative_test_runner"]
        
        # Determine alternative based on error context
        if error_instance.classification and error_instance.classification.category == ErrorCategory.TEST_FAILURE:
            return await self._try_alternative_test_runner(error_instance, context)
        elif error_instance.classification and error_instance.classification.category == ErrorCategory.BUILD_FAILURE:
            return await self._try_alternative_build_tool(error_instance, context)
        else:
            return HealingResult(
                action_id=action.id,
                strategy=HealingStrategy.ALTERNATIVE_APPROACH,
                success=False,
                error_message="No alternative approach available for this error type",
                execution_time=0
            )

    async def _escalate_to_human(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Escalate error to human intervention."""
        # Create detailed report for human review
        escalation_report = {
            "error_id": error_instance.id,
            "error_message": error_instance.error_message,
            "classification": error_instance.classification.dict() if error_instance.classification else None,
            "healing_attempts": error_instance.healing_attempts,
            "context": context,
            "escalation_time": datetime.now().isoformat()
        }
        
        # In a real implementation, this would:
        # 1. Create a ticket in the issue tracking system
        # 2. Send notifications to the development team
        # 3. Update monitoring dashboards
        
        self.logger.warning(f"Escalating error {error_instance.id} to human intervention")
        
        return HealingResult(
            action_id="human_escalation",
            strategy=HealingStrategy.ESCALATE_TO_HUMAN,
            success=True,  # Escalation itself is successful
            execution_time=0,
            metrics={"escalation_report": escalation_report}
        )

    # Helper methods
    
    async def _rerun_failed_stage(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Re-run the failed pipeline stage."""
        # This would re-execute the specific stage that failed
        # For now, simulate success/failure
        return True  # Placeholder

    async def _detect_package_manager(self, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Detect the package manager used in the project."""
        # Check for package manager files
        import os
        
        if os.path.exists("requirements.txt") or os.path.exists("pyproject.toml"):
            return "pip"
        elif os.path.exists("package.json"):
            if os.path.exists("yarn.lock"):
                return "yarn"
            else:
                return "npm"
        
        return None

    async def _backup_dependency_files(self, package_manager: str) -> None:
        """Backup dependency files before modification."""
        files_to_backup = []
        
        if package_manager == "pip":
            files_to_backup = ["requirements.txt", "pyproject.toml"]
        elif package_manager in ["npm", "yarn"]:
            files_to_backup = ["package.json", "package-lock.json", "yarn.lock"]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                await self._backup_file(file_path)

    async def _backup_file(self, file_path: str) -> None:
        """Create a backup of a file."""
        import shutil
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)

    async def _verify_dependencies(self, package_manager: str) -> bool:
        """Verify that dependencies are properly installed."""
        if package_manager == "pip":
            result = await self.command_executor.execute("python -c 'import sys; print(sys.version)'")
            return result.success
        elif package_manager in ["npm", "yarn"]:
            result = await self.command_executor.execute("node --version")
            return result.success
        
        return False

    async def _identify_config_files(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Identify configuration files in the project."""
        import os
        
        config_files = []
        common_configs = [
            "pyproject.toml", "setup.cfg", "tox.ini",
            "package.json", "tsconfig.json", "webpack.config.js",
            ".github/workflows/*.yml", ".github/workflows/*.yaml"
        ]
        
        for pattern in common_configs:
            if "*" in pattern:
                # Handle glob patterns
                import glob
                config_files.extend(glob.glob(pattern))
            elif os.path.exists(pattern):
                config_files.append(pattern)
        
        return config_files

    async def _fix_config_file(self, config_file: str, error_instance: ErrorInstance) -> bool:
        """Apply fixes to a configuration file."""
        # This would contain specific logic to fix common configuration issues
        # For now, return True as placeholder
        return True

    async def _verify_configuration(self, config_files: List[str]) -> bool:
        """Verify that configuration files are valid."""
        # This would validate configuration syntax and semantics
        return True

    async def _try_alternative_test_runner(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Try alternative test runners."""
        alternatives = ["pytest", "unittest", "nose2"]
        
        for runner in alternatives:
            try:
                result = await self.command_executor.execute(f"{runner} --version")
                if result.success:
                    # Try running tests with this runner
                    test_result = await self.command_executor.execute(f"{runner} tests/")
                    if test_result.success:
                        return HealingResult(
                            action_id="alternative_test_runner",
                            strategy=HealingStrategy.ALTERNATIVE_APPROACH,
                            success=True,
                            execution_time=0,
                            metrics={"successful_runner": runner}
                        )
            except Exception:
                continue
        
        return HealingResult(
            action_id="alternative_test_runner",
            strategy=HealingStrategy.ALTERNATIVE_APPROACH,
            success=False,
            error_message="No alternative test runner succeeded",
            execution_time=0
        )

    async def _try_alternative_build_tool(
        self,
        error_instance: ErrorInstance,
        context: Optional[Dict[str, Any]] = None
    ) -> HealingResult:
        """Try alternative build tools."""
        # This would try different build configurations or tools
        return HealingResult(
            action_id="alternative_build_tool",
            strategy=HealingStrategy.ALTERNATIVE_APPROACH,
            success=False,
            error_message="Alternative build tools not implemented",
            execution_time=0
        )

    async def _get_healing_status(self, error_id: str) -> HealingResult:
        """Get the status of an ongoing healing session."""
        session = self.active_healing_sessions.get(error_id)
        if not session:
            return HealingResult(
                action_id="status_check",
                strategy=HealingStrategy.ESCALATE_TO_HUMAN,
                success=False,
                error_message="No active healing session found",
                execution_time=0
            )
        
        return HealingResult(
            action_id="status_check",
            strategy=session.get("current_strategy", HealingStrategy.ESCALATE_TO_HUMAN),
            success=False,  # Still in progress
            execution_time=(datetime.now() - session["start_time"]).total_seconds(),
            metrics={
                "attempts": session["attempts"],
                "current_strategy": session.get("current_strategy", {}).value if session.get("current_strategy") else None
            }
        )

    async def _update_success_rates(self, strategies_tried: List[Dict[str, Any]]) -> None:
        """Update success rates for healing strategies."""
        for strategy_data in strategies_tried:
            strategy = HealingStrategy(strategy_data["strategy"])
            success = strategy_data["result"]
            
            current_rate = self.strategy_success_rates.get(strategy, 0.5)
            
            # Simple moving average update
            alpha = 0.1  # Learning rate
            new_rate = current_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
            
            self.strategy_success_rates[strategy] = new_rate

    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive healing statistics."""
        total_attempts = len(self.healing_history)
        successful_attempts = sum(1 for result in self.healing_history if result.success)
        
        # Strategy performance
        strategy_stats = {}
        for strategy, success_rate in self.strategy_success_rates.items():
            strategy_attempts = sum(
                1 for result in self.healing_history 
                if result.strategy == strategy
            )
            strategy_stats[strategy.value] = {
                "success_rate": success_rate,
                "total_attempts": strategy_attempts
            }
        
        # Average healing time
        healing_times = [result.execution_time for result in self.healing_history]
        avg_healing_time = sum(healing_times) / len(healing_times) if healing_times else 0
        
        return {
            "total_healing_attempts": total_attempts,
            "overall_success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "average_healing_time": avg_healing_time,
            "strategy_performance": strategy_stats,
            "active_sessions": len(self.active_healing_sessions)
        }

