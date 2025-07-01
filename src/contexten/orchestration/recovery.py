"""
Recovery Management System

This module provides automated recovery capabilities for the orchestration system,
including failure detection, recovery strategies, and self-healing mechanisms.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RESTART_WORKFLOW = "restart_workflow"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_EXECUTION = "fallback_execution"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    SYSTEM_RESTART = "system_restart"
    RESOURCE_CLEANUP = "resource_cleanup"
    CONFIGURATION_RESET = "configuration_reset"


class FailureType(Enum):
    """Types of failures that can be recovered from"""
    WORKFLOW_TIMEOUT = "workflow_timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    INTEGRATION_FAILURE = "integration_failure"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RecoveryAction:
    """A recovery action to be executed"""
    strategy: RecoveryStrategy
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1 = highest priority
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RecoveryPlan:
    """A complete recovery plan for a failure"""
    failure_id: str
    failure_type: FailureType
    failure_description: str
    actions: List[RecoveryAction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None


class RecoveryManager:
    """
    Automated recovery management system for orchestration failures
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.recovery_active = True
        
        # Recovery configuration
        self.max_concurrent_recoveries = 3
        self.recovery_timeout = 1800  # 30 minutes
        self.escalation_threshold = 3  # failures before escalation
        
        # Active recoveries
        self.active_recoveries: Dict[str, RecoveryPlan] = {}
        self.recovery_history: List[RecoveryPlan] = []
        
        # Failure tracking
        self.failure_counts: Dict[str, int] = {}
        self.last_failures: Dict[str, datetime] = {}
        
        # Recovery strategies mapping
        self.recovery_strategies = {
            FailureType.WORKFLOW_TIMEOUT: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    description="Retry workflow with exponential backoff",
                    parameters={"initial_delay": 60, "max_delay": 600}
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.RESOURCE_CLEANUP,
                    description="Clean up resources and retry",
                    priority=2
                )
            ],
            FailureType.RESOURCE_EXHAUSTION: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RESOURCE_CLEANUP,
                    description="Clean up unused resources",
                    priority=1
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.RESTART_WORKFLOW,
                    description="Restart workflow with resource limits",
                    priority=2,
                    parameters={"resource_limits": {"memory": "2GB", "cpu": "1"}}
                )
            ],
            FailureType.INTEGRATION_FAILURE: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    description="Retry integration with backoff",
                    parameters={"initial_delay": 30, "max_delay": 300}
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK_EXECUTION,
                    description="Use fallback integration method",
                    priority=2
                )
            ],
            FailureType.RATE_LIMIT_ERROR: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    description="Wait for rate limit reset and retry",
                    parameters={"initial_delay": 300, "max_delay": 3600}
                )
            ],
            FailureType.AUTHENTICATION_ERROR: [
                RecoveryAction(
                    strategy=RecoveryStrategy.CONFIGURATION_RESET,
                    description="Reset authentication configuration",
                    priority=1
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.ESCALATE_TO_HUMAN,
                    description="Escalate authentication issue to human",
                    priority=2
                )
            ]
        }
        
        # Recovery action handlers
        self.action_handlers: Dict[RecoveryStrategy, Callable] = {
            RecoveryStrategy.RESTART_WORKFLOW: self._restart_workflow,
            RecoveryStrategy.RETRY_WITH_BACKOFF: self._retry_with_backoff,
            RecoveryStrategy.FALLBACK_EXECUTION: self._fallback_execution,
            RecoveryStrategy.ESCALATE_TO_HUMAN: self._escalate_to_human,
            RecoveryStrategy.SYSTEM_RESTART: self._system_restart,
            RecoveryStrategy.RESOURCE_CLEANUP: self._resource_cleanup,
            RecoveryStrategy.CONFIGURATION_RESET: self._configuration_reset
        }
    
    async def initialize(self):
        """Initialize the recovery manager"""
        logger.info("Recovery manager initialized")
    
    async def handle_workflow_failure(self, execution):
        """Handle a workflow execution failure"""
        
        if not self.recovery_active:
            logger.info("Recovery disabled, skipping failure handling")
            return
        
        logger.warning(f"Handling workflow failure: {execution.execution_id}")
        
        # Classify the failure
        failure_type = self._classify_failure(execution)
        
        # Check if we should attempt recovery
        if not self._should_attempt_recovery(execution, failure_type):
            logger.info(f"Skipping recovery for {execution.execution_id} - threshold exceeded")
            return
        
        # Create recovery plan
        recovery_plan = self._create_recovery_plan(execution, failure_type)
        
        # Execute recovery
        await self._execute_recovery_plan(recovery_plan)
    
    def _classify_failure(self, execution) -> FailureType:
        """Classify the type of failure based on execution details"""
        
        error_message = execution.error_message or ""
        error_type = execution.error_type or ""
        
        # Check for specific error patterns
        if "timeout" in error_message.lower() or "TimeoutError" in error_type:
            return FailureType.WORKFLOW_TIMEOUT
        
        elif "memory" in error_message.lower() or "MemoryError" in error_type:
            return FailureType.RESOURCE_EXHAUSTION
        
        elif "rate limit" in error_message.lower() or "429" in error_message:
            return FailureType.RATE_LIMIT_ERROR
        
        elif "authentication" in error_message.lower() or "401" in error_message:
            return FailureType.AUTHENTICATION_ERROR
        
        elif "network" in error_message.lower() or "ConnectionError" in error_type:
            return FailureType.NETWORK_ERROR
        
        elif "config" in error_message.lower():
            return FailureType.CONFIGURATION_ERROR
        
        elif any(integration in error_message.lower() for integration in ["github", "linear", "codegen"]):
            return FailureType.INTEGRATION_FAILURE
        
        else:
            return FailureType.UNKNOWN_ERROR
    
    def _should_attempt_recovery(self, execution, failure_type: FailureType) -> bool:
        """Determine if recovery should be attempted"""
        
        workflow_id = execution.workflow_config.workflow_type.value
        
        # Check failure count for this workflow
        failure_count = self.failure_counts.get(workflow_id, 0)
        
        if failure_count >= self.escalation_threshold:
            logger.warning(f"Failure threshold exceeded for {workflow_id}: {failure_count}")
            return False
        
        # Check if too many concurrent recoveries
        if len(self.active_recoveries) >= self.max_concurrent_recoveries:
            logger.warning("Too many concurrent recoveries, skipping")
            return False
        
        # Check if recent failure (avoid recovery loops)
        last_failure = self.last_failures.get(workflow_id)
        if last_failure and (datetime.now() - last_failure).total_seconds() < 300:  # 5 minutes
            logger.warning(f"Recent failure for {workflow_id}, skipping recovery")
            return False
        
        return True
    
    def _create_recovery_plan(self, execution, failure_type: FailureType) -> RecoveryPlan:
        """Create a recovery plan for the failure"""
        
        failure_id = f"recovery_{execution.execution_id}_{int(datetime.now().timestamp())}"
        
        # Get recovery actions for this failure type
        actions = self.recovery_strategies.get(failure_type, [
            RecoveryAction(
                strategy=RecoveryStrategy.ESCALATE_TO_HUMAN,
                description="Unknown failure type - escalate to human"
            )
        ])
        
        # Sort actions by priority
        actions.sort(key=lambda x: x.priority)
        
        recovery_plan = RecoveryPlan(
            failure_id=failure_id,
            failure_type=failure_type,
            failure_description=f"Workflow {execution.execution_id} failed: {execution.error_message}",
            actions=actions.copy()  # Create a copy to avoid modifying the template
        )
        
        logger.info(f"Created recovery plan {failure_id} with {len(actions)} actions")
        
        return recovery_plan
    
    async def _execute_recovery_plan(self, recovery_plan: RecoveryPlan):
        """Execute a recovery plan"""
        
        self.active_recoveries[recovery_plan.failure_id] = recovery_plan
        recovery_plan.executed_at = datetime.now()
        
        logger.info(f"Executing recovery plan: {recovery_plan.failure_id}")
        
        try:
            # Execute actions in priority order
            for action in recovery_plan.actions:
                try:
                    logger.info(f"Executing recovery action: {action.strategy.value}")
                    
                    # Get action handler
                    handler = self.action_handlers.get(action.strategy)
                    if not handler:
                        logger.error(f"No handler for recovery strategy: {action.strategy}")
                        continue
                    
                    # Execute action with timeout
                    await asyncio.wait_for(
                        handler(action, recovery_plan),
                        timeout=action.timeout_seconds
                    )
                    
                    logger.info(f"Recovery action completed: {action.strategy.value}")
                    
                    # If action succeeded, we might not need to execute remaining actions
                    # This depends on the specific recovery strategy
                    if action.strategy in [RecoveryStrategy.RESTART_WORKFLOW, RecoveryStrategy.SYSTEM_RESTART]:
                        break
                    
                except asyncio.TimeoutError:
                    logger.error(f"Recovery action timed out: {action.strategy.value}")
                    action.retry_count += 1
                    
                    if action.retry_count < action.max_retries:
                        logger.info(f"Retrying recovery action: {action.strategy.value}")
                        # Add action back to the end of the list for retry
                        recovery_plan.actions.append(action)
                
                except Exception as e:
                    logger.error(f"Recovery action failed: {action.strategy.value} - {e}")
                    action.retry_count += 1
                    
                    if action.retry_count < action.max_retries:
                        recovery_plan.actions.append(action)
            
            # Mark recovery as successful if we got here
            recovery_plan.success = True
            recovery_plan.completed_at = datetime.now()
            
            logger.info(f"Recovery plan completed successfully: {recovery_plan.failure_id}")
            
        except Exception as e:
            recovery_plan.success = False
            recovery_plan.error_message = str(e)
            recovery_plan.completed_at = datetime.now()
            
            logger.error(f"Recovery plan failed: {recovery_plan.failure_id} - {e}")
        
        finally:
            # Move to history and clean up
            self.recovery_history.append(recovery_plan)
            if recovery_plan.failure_id in self.active_recoveries:
                del self.active_recoveries[recovery_plan.failure_id]
    
    async def _restart_workflow(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Restart a failed workflow"""
        
        logger.info("Executing workflow restart recovery")
        
        # Extract workflow information from recovery plan
        # This would need to be enhanced based on how workflow info is stored
        
        # For now, just log the action
        logger.info(f"Would restart workflow with parameters: {action.parameters}")
        
        # Simulate restart delay
        await asyncio.sleep(5)
    
    async def _retry_with_backoff(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Retry with exponential backoff"""
        
        initial_delay = action.parameters.get("initial_delay", 60)
        max_delay = action.parameters.get("max_delay", 600)
        
        # Calculate delay with exponential backoff
        delay = min(initial_delay * (2 ** action.retry_count), max_delay)
        
        logger.info(f"Retrying with backoff: {delay} seconds")
        
        await asyncio.sleep(delay)
        
        # The actual retry would happen in the workflow system
        logger.info("Backoff delay completed")
    
    async def _fallback_execution(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Execute fallback strategy"""
        
        logger.info("Executing fallback recovery strategy")
        
        # This would implement fallback logic specific to the failure type
        # For example, using a different API endpoint or execution method
        
        await asyncio.sleep(2)
        logger.info("Fallback execution completed")
    
    async def _escalate_to_human(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Escalate issue to human intervention"""
        
        logger.warning(f"Escalating to human: {recovery_plan.failure_description}")
        
        # This would send notifications to administrators
        # Could integrate with Slack, email, or ticketing systems
        
        escalation_message = {
            "type": "recovery_escalation",
            "failure_id": recovery_plan.failure_id,
            "failure_type": recovery_plan.failure_type.value,
            "description": recovery_plan.failure_description,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send escalation notification
        await self._send_escalation_notification(escalation_message)
    
    async def _system_restart(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Restart the orchestration system"""
        
        logger.warning("Executing system restart recovery")
        
        # This would restart the orchestration system
        # Should be used only for critical failures
        
        # For safety, just log the action for now
        logger.warning("System restart requested - manual intervention required")
    
    async def _resource_cleanup(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Clean up system resources"""
        
        logger.info("Executing resource cleanup recovery")
        
        # Clean up memory, temporary files, connections, etc.
        import gc
        gc.collect()
        
        # Cancel any stuck tasks
        for execution_id, execution in list(self.orchestrator.active_executions.items()):
            if execution.status.value in ["running", "pending"]:
                # Check if execution is stuck (running too long)
                if execution.started_at:
                    runtime = (datetime.now() - execution.started_at).total_seconds()
                    if runtime > execution.workflow_config.timeout_seconds:
                        logger.warning(f"Cancelling stuck execution: {execution_id}")
                        execution.status = "cancelled"
                        del self.orchestrator.active_executions[execution_id]
        
        logger.info("Resource cleanup completed")
    
    async def _configuration_reset(self, action: RecoveryAction, recovery_plan: RecoveryPlan):
        """Reset configuration to known good state"""
        
        logger.info("Executing configuration reset recovery")
        
        # This would reset configurations to default or last known good state
        # Implementation depends on configuration management system
        
        await asyncio.sleep(1)
        logger.info("Configuration reset completed")
    
    async def _send_escalation_notification(self, escalation_message: Dict[str, Any]):
        """Send escalation notification to administrators"""
        
        try:
            # This would integrate with notification systems
            logger.critical(f"ESCALATION: {json.dumps(escalation_message, indent=2)}")
            
            # Could send to Slack, email, etc.
            
        except Exception as e:
            logger.error(f"Failed to send escalation notification: {e}")
    
    async def trigger_recovery(self, health_status: Dict[str, Any]):
        """Trigger recovery based on health status"""
        
        if not self.recovery_active:
            return
        
        overall_health = health_status.get("overall_health", 100)
        
        if overall_health < 50:
            logger.warning("Critical system health - triggering emergency recovery")
            
            # Create emergency recovery plan
            recovery_plan = RecoveryPlan(
                failure_id=f"emergency_{int(datetime.now().timestamp())}",
                failure_type=FailureType.UNKNOWN_ERROR,
                failure_description=f"Critical system health: {overall_health}%",
                actions=[
                    RecoveryAction(
                        strategy=RecoveryStrategy.RESOURCE_CLEANUP,
                        description="Emergency resource cleanup"
                    ),
                    RecoveryAction(
                        strategy=RecoveryStrategy.SYSTEM_RESTART,
                        description="Emergency system restart",
                        priority=2
                    )
                ]
            )
            
            await self._execute_recovery_plan(recovery_plan)
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status"""
        
        return {
            "recovery_active": self.recovery_active,
            "active_recoveries": len(self.active_recoveries),
            "total_recoveries": len(self.recovery_history),
            "successful_recoveries": len([r for r in self.recovery_history if r.success]),
            "failed_recoveries": len([r for r in self.recovery_history if not r.success]),
            "failure_counts": self.failure_counts.copy(),
            "last_recovery": self.recovery_history[-1].created_at.isoformat() if self.recovery_history else None
        }
    
    def disable_recovery(self):
        """Disable automatic recovery"""
        self.recovery_active = False
        logger.warning("Automatic recovery disabled")
    
    def enable_recovery(self):
        """Enable automatic recovery"""
        self.recovery_active = True
        logger.info("Automatic recovery enabled")

