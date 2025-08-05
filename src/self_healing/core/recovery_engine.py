"""
Self-Healing Architecture - Recovery Engine Module
Automated recovery and remediation system for system errors.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import json

from .error_detection import ErrorEvent, ErrorCategory, ErrorSeverity


class RiskLevel(Enum):
    """Risk levels for recovery actions."""
    LOW = 1      # Safe actions with minimal impact
    MEDIUM = 2   # Moderate risk, may affect performance
    HIGH = 3     # High risk, may cause service disruption
    CRITICAL = 4 # Extreme risk, requires manual approval


class RecoveryStatus(Enum):
    """Status of recovery action execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


@dataclass
class RecoveryContext:
    """Context information for recovery action execution."""
    error_event: ErrorEvent
    system_state: Dict[str, Any]
    previous_attempts: List['RecoveryExecution']
    approval_required: bool = False
    approved_by: Optional[str] = None
    timeout_seconds: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_event": self.error_event.to_dict(),
            "system_state": self.system_state,
            "previous_attempts": [attempt.to_dict() for attempt in self.previous_attempts],
            "approval_required": self.approval_required,
            "approved_by": self.approved_by,
            "timeout_seconds": self.timeout_seconds
        }


@dataclass
class RecoveryResult:
    """Result of recovery action execution."""
    success: bool
    execution_time: float
    output_log: str
    error_message: Optional[str] = None
    rollback_executed: bool = False
    rollback_success: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def success_result(cls, execution_time: float, output_log: str, metadata: Dict[str, Any] = None):
        """Create a successful recovery result."""
        return cls(
            success=True,
            execution_time=execution_time,
            output_log=output_log,
            metadata=metadata or {}
        )
    
    @classmethod
    def failure_result(cls, execution_time: float, error_message: str, output_log: str = ""):
        """Create a failed recovery result."""
        return cls(
            success=False,
            execution_time=execution_time,
            output_log=output_log,
            error_message=error_message
        )
    
    @classmethod
    def manual_intervention_required(cls):
        """Create result indicating manual intervention is required."""
        return cls(
            success=False,
            execution_time=0.0,
            output_log="Manual intervention required",
            error_message="Automated recovery not available for this error type"
        )


@dataclass
class RecoveryExecution:
    """Record of a recovery action execution."""
    id: str
    recovery_action_name: str
    error_event_id: str
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[RecoveryResult] = None
    context: Optional[RecoveryContext] = None
    retry_attempt: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        data['status'] = self.status.value
        return data


class RecoveryAction(ABC):
    """Abstract base class for recovery actions."""
    
    def __init__(self, name: str, risk_level: RiskLevel, success_rate: float = 0.0):
        self.name = name
        self.risk_level = risk_level
        self.success_rate = success_rate
        self.prerequisites: List[str] = []
        self.applicable_categories: List[ErrorCategory] = []
        self.max_execution_time = 300  # 5 minutes default
        self.retry_count = 0
        self.enabled = True
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    async def execute(self, context: RecoveryContext) -> RecoveryResult:
        """Execute the recovery action."""
        pass
    
    @abstractmethod
    async def rollback(self, context: RecoveryContext) -> bool:
        """Rollback the recovery action if it failed."""
        pass
    
    @abstractmethod
    def can_handle(self, error_event: ErrorEvent) -> bool:
        """Check if this action can handle the given error."""
        pass
    
    def get_estimated_execution_time(self) -> int:
        """Get estimated execution time in seconds."""
        return self.max_execution_time
    
    def requires_approval(self) -> bool:
        """Check if this action requires manual approval."""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class RestartServiceAction(RecoveryAction):
    """Recovery action to restart a service."""
    
    def __init__(self):
        super().__init__("restart_service", RiskLevel.MEDIUM, 0.85)
        self.applicable_categories = [
            ErrorCategory.API,
            ErrorCategory.PERFORMANCE,
            ErrorCategory.RESOURCE
        ]
        self.max_execution_time = 120
    
    async def execute(self, context: RecoveryContext) -> RecoveryResult:
        """Execute service restart."""
        start_time = time.time()
        
        try:
            component = context.error_event.source_component
            self.logger.info(f"Restarting service: {component}")
            
            # Simulate service restart (replace with actual implementation)
            await asyncio.sleep(2)  # Simulate restart time
            
            # Check if service is healthy after restart
            health_check_result = await self._check_service_health(component)
            
            execution_time = time.time() - start_time
            
            if health_check_result:
                return RecoveryResult.success_result(
                    execution_time=execution_time,
                    output_log=f"Service {component} restarted successfully",
                    metadata={"component": component, "health_check": "passed"}
                )
            else:
                return RecoveryResult.failure_result(
                    execution_time=execution_time,
                    error_message=f"Service {component} failed health check after restart",
                    output_log=f"Restart completed but health check failed for {component}"
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return RecoveryResult.failure_result(
                execution_time=execution_time,
                error_message=str(e),
                output_log=f"Failed to restart service: {e}"
            )
    
    async def rollback(self, context: RecoveryContext) -> bool:
        """Rollback service restart (attempt to restore previous state)."""
        try:
            # In a real implementation, this might restore from backup or previous configuration
            self.logger.info("Rollback for service restart - checking service state")
            return True
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    def can_handle(self, error_event: ErrorEvent) -> bool:
        """Check if this action can handle the error."""
        return (error_event.category in self.applicable_categories and
                error_event.severity in [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM])
    
    async def _check_service_health(self, component: str) -> bool:
        """Check if service is healthy after restart."""
        # Simulate health check (replace with actual implementation)
        await asyncio.sleep(1)
        return True  # Assume success for demo


class ClearCacheAction(RecoveryAction):
    """Recovery action to clear application cache."""
    
    def __init__(self):
        super().__init__("clear_cache", RiskLevel.LOW, 0.95)
        self.applicable_categories = [
            ErrorCategory.PERFORMANCE,
            ErrorCategory.API,
            ErrorCategory.DATABASE
        ]
        self.max_execution_time = 30
    
    async def execute(self, context: RecoveryContext) -> RecoveryResult:
        """Execute cache clearing."""
        start_time = time.time()
        
        try:
            component = context.error_event.source_component
            self.logger.info(f"Clearing cache for component: {component}")
            
            # Simulate cache clearing (replace with actual implementation)
            await asyncio.sleep(0.5)
            
            execution_time = time.time() - start_time
            
            return RecoveryResult.success_result(
                execution_time=execution_time,
                output_log=f"Cache cleared successfully for {component}",
                metadata={"component": component, "cache_type": "application"}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return RecoveryResult.failure_result(
                execution_time=execution_time,
                error_message=str(e),
                output_log=f"Failed to clear cache: {e}"
            )
    
    async def rollback(self, context: RecoveryContext) -> bool:
        """Rollback cache clearing (warm up cache if needed)."""
        try:
            # In a real implementation, this might warm up critical cache entries
            self.logger.info("Cache clearing rollback - warming up critical cache entries")
            return True
        except Exception as e:
            self.logger.error(f"Cache rollback failed: {e}")
            return False
    
    def can_handle(self, error_event: ErrorEvent) -> bool:
        """Check if this action can handle the error."""
        return (error_event.category in self.applicable_categories and
                "cache" in error_event.message.lower())


class ScaleResourcesAction(RecoveryAction):
    """Recovery action to scale system resources."""
    
    def __init__(self):
        super().__init__("scale_resources", RiskLevel.LOW, 0.90)
        self.applicable_categories = [
            ErrorCategory.PERFORMANCE,
            ErrorCategory.RESOURCE
        ]
        self.max_execution_time = 180
    
    async def execute(self, context: RecoveryContext) -> RecoveryResult:
        """Execute resource scaling."""
        start_time = time.time()
        
        try:
            component = context.error_event.source_component
            self.logger.info(f"Scaling resources for component: {component}")
            
            # Determine scaling strategy based on error context
            scaling_strategy = self._determine_scaling_strategy(context)
            
            # Simulate resource scaling (replace with actual implementation)
            await asyncio.sleep(3)
            
            execution_time = time.time() - start_time
            
            return RecoveryResult.success_result(
                execution_time=execution_time,
                output_log=f"Resources scaled successfully for {component}",
                metadata={
                    "component": component,
                    "scaling_strategy": scaling_strategy,
                    "previous_resources": "2 CPU, 4GB RAM",
                    "new_resources": "4 CPU, 8GB RAM"
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return RecoveryResult.failure_result(
                execution_time=execution_time,
                error_message=str(e),
                output_log=f"Failed to scale resources: {e}"
            )
    
    async def rollback(self, context: RecoveryContext) -> bool:
        """Rollback resource scaling."""
        try:
            self.logger.info("Rolling back resource scaling to previous configuration")
            # Simulate rollback (replace with actual implementation)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"Resource scaling rollback failed: {e}")
            return False
    
    def can_handle(self, error_event: ErrorEvent) -> bool:
        """Check if this action can handle the error."""
        performance_keywords = ["cpu", "memory", "resource", "overload", "capacity"]
        return (error_event.category in self.applicable_categories and
                any(keyword in error_event.message.lower() for keyword in performance_keywords))
    
    def _determine_scaling_strategy(self, context: RecoveryContext) -> str:
        """Determine appropriate scaling strategy based on error context."""
        error_message = context.error_event.message.lower()
        
        if "cpu" in error_message:
            return "scale_cpu"
        elif "memory" in error_message:
            return "scale_memory"
        else:
            return "scale_both"


class RecoveryActionRegistry:
    """Registry for managing available recovery actions."""
    
    def __init__(self):
        self.actions: Dict[str, RecoveryAction] = {}
        self.logger = logging.getLogger(__name__)
        
        # Register default actions
        self._register_default_actions()
    
    def _register_default_actions(self):
        """Register default recovery actions."""
        default_actions = [
            RestartServiceAction(),
            ClearCacheAction(),
            ScaleResourcesAction()
        ]
        
        for action in default_actions:
            self.register_action(action)
    
    def register_action(self, action: RecoveryAction):
        """Register a recovery action."""
        self.actions[action.name] = action
        self.logger.info(f"Registered recovery action: {action.name}")
    
    def get_action(self, name: str) -> Optional[RecoveryAction]:
        """Get recovery action by name."""
        return self.actions.get(name)
    
    def get_applicable_actions(self, error_event: ErrorEvent) -> List[RecoveryAction]:
        """Get all actions that can handle the given error."""
        applicable_actions = []
        
        for action in self.actions.values():
            if action.enabled and action.can_handle(error_event):
                applicable_actions.append(action)
        
        # Sort by success rate (descending) and risk level (ascending)
        applicable_actions.sort(
            key=lambda a: (-a.success_rate, a.risk_level.value)
        )
        
        return applicable_actions
    
    def list_actions(self) -> List[str]:
        """List all registered action names."""
        return list(self.actions.keys())


class RiskAssessor:
    """Assess risk of recovery actions in current context."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def assess_risk(self, action: RecoveryAction, context: RecoveryContext) -> Dict[str, Any]:
        """Assess risk of executing recovery action in given context."""
        risk_factors = []
        risk_score = action.risk_level.value
        
        # Factor 1: Previous failed attempts
        failed_attempts = len([
            attempt for attempt in context.previous_attempts
            if attempt.result and not attempt.result.success
        ])
        
        if failed_attempts > 0:
            risk_factors.append(f"Previous failed attempts: {failed_attempts}")
            risk_score += failed_attempts * 0.5
        
        # Factor 2: Error severity
        if context.error_event.severity == ErrorSeverity.CRITICAL:
            risk_factors.append("Critical error severity")
            risk_score += 1.0
        
        # Factor 3: System load (simulated)
        system_load = context.system_state.get("cpu_usage", 0.5)
        if system_load > 0.8:
            risk_factors.append(f"High system load: {system_load:.1%}")
            risk_score += 0.5
        
        # Factor 4: Time of day (higher risk during business hours)
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            risk_factors.append("Business hours execution")
            risk_score += 0.3
        
        # Calculate final risk level
        if risk_score <= 2.0:
            final_risk = RiskLevel.LOW
        elif risk_score <= 3.5:
            final_risk = RiskLevel.MEDIUM
        elif risk_score <= 5.0:
            final_risk = RiskLevel.HIGH
        else:
            final_risk = RiskLevel.CRITICAL
        
        return {
            "risk_level": final_risk,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(final_risk),
            "requires_approval": final_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        }
    
    def _get_risk_recommendation(self, risk_level: RiskLevel) -> str:
        """Get recommendation based on risk level."""
        recommendations = {
            RiskLevel.LOW: "Safe to execute automatically",
            RiskLevel.MEDIUM: "Execute with monitoring",
            RiskLevel.HIGH: "Requires approval before execution",
            RiskLevel.CRITICAL: "Manual intervention recommended"
        }
        return recommendations.get(risk_level, "Unknown risk level")


class RecoveryOrchestrator:
    """Main orchestrator for recovery actions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.action_registry = RecoveryActionRegistry()
        self.risk_assessor = RiskAssessor(config.get("risk_assessment", {}))
        self.logger = logging.getLogger(__name__)
        self.active_executions: Dict[str, RecoveryExecution] = {}
        self.max_concurrent_recoveries = config.get("max_concurrent_recoveries", 3)
        self.recovery_callbacks: List[Callable] = []
    
    def add_recovery_callback(self, callback: Callable[[RecoveryExecution], None]):
        """Add callback to be called when recovery actions complete."""
        self.recovery_callbacks.append(callback)
    
    async def execute_recovery(self, error_event: ErrorEvent, system_state: Dict[str, Any]) -> RecoveryExecution:
        """Execute recovery for the given error event."""
        # Check if we're at max concurrent recoveries
        if len(self.active_executions) >= self.max_concurrent_recoveries:
            self.logger.warning("Max concurrent recoveries reached, queuing recovery")
            # In a real implementation, this would queue the recovery
            return self._create_failed_execution(error_event, "Max concurrent recoveries reached")
        
        # Get applicable recovery actions
        applicable_actions = self.action_registry.get_applicable_actions(error_event)
        
        if not applicable_actions:
            self.logger.warning(f"No applicable recovery actions for error: {error_event.message}")
            return self._create_failed_execution(error_event, "No applicable recovery actions")
        
        # Create recovery context
        previous_attempts = self._get_previous_attempts(error_event)
        context = RecoveryContext(
            error_event=error_event,
            system_state=system_state,
            previous_attempts=previous_attempts
        )
        
        # Select best action based on risk assessment
        selected_action = await self._select_best_action(applicable_actions, context)
        
        if not selected_action:
            self.logger.warning("No safe recovery action available")
            return self._create_failed_execution(error_event, "No safe recovery action available")
        
        # Execute the selected action
        execution = await self._execute_action(selected_action, context)
        
        # Trigger callbacks
        for callback in self.recovery_callbacks:
            try:
                await callback(execution)
            except Exception as e:
                self.logger.error(f"Recovery callback failed: {e}")
        
        return execution
    
    async def _select_best_action(self, actions: List[RecoveryAction], context: RecoveryContext) -> Optional[RecoveryAction]:
        """Select the best recovery action based on risk assessment."""
        for action in actions:
            risk_assessment = await self.risk_assessor.assess_risk(action, context)
            
            # Skip actions that require approval (for now)
            if risk_assessment["requires_approval"]:
                self.logger.info(f"Action {action.name} requires approval, skipping")
                continue
            
            # Skip high-risk actions unless explicitly allowed
            if (risk_assessment["risk_level"] == RiskLevel.HIGH and 
                not self.config.get("allow_high_risk_actions", False)):
                self.logger.info(f"Action {action.name} is high risk, skipping")
                continue
            
            return action
        
        return None
    
    async def _execute_action(self, action: RecoveryAction, context: RecoveryContext) -> RecoveryExecution:
        """Execute a recovery action and track the execution."""
        execution_id = f"recovery_{int(time.time() * 1000)}"
        
        execution = RecoveryExecution(
            id=execution_id,
            recovery_action_name=action.name,
            error_event_id=context.error_event.fingerprint,
            status=RecoveryStatus.PENDING,
            started_at=datetime.now(),
            context=context
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            self.logger.info(f"Executing recovery action: {action.name}")
            execution.status = RecoveryStatus.RUNNING
            
            # Execute with timeout
            result = await asyncio.wait_for(
                action.execute(context),
                timeout=action.max_execution_time
            )
            
            execution.result = result
            execution.completed_at = datetime.now()
            
            if result.success:
                execution.status = RecoveryStatus.COMPLETED
                self.logger.info(f"Recovery action {action.name} completed successfully")
            else:
                execution.status = RecoveryStatus.FAILED
                self.logger.warning(f"Recovery action {action.name} failed: {result.error_message}")
                
                # Attempt rollback if configured
                if self.config.get("auto_rollback_on_failure", True):
                    rollback_success = await action.rollback(context)
                    result.rollback_executed = True
                    result.rollback_success = rollback_success
                    
                    if rollback_success:
                        execution.status = RecoveryStatus.ROLLED_BACK
                        self.logger.info(f"Recovery action {action.name} rolled back successfully")
        
        except asyncio.TimeoutError:
            execution.status = RecoveryStatus.FAILED
            execution.result = RecoveryResult.failure_result(
                execution_time=action.max_execution_time,
                error_message="Recovery action timed out",
                output_log=f"Action {action.name} exceeded timeout of {action.max_execution_time}s"
            )
            execution.completed_at = datetime.now()
            self.logger.error(f"Recovery action {action.name} timed out")
        
        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.result = RecoveryResult.failure_result(
                execution_time=0.0,
                error_message=str(e),
                output_log=f"Unexpected error during recovery: {e}"
            )
            execution.completed_at = datetime.now()
            self.logger.error(f"Recovery action {action.name} failed with exception: {e}")
        
        finally:
            # Remove from active executions
            self.active_executions.pop(execution_id, None)
        
        return execution
    
    def _get_previous_attempts(self, error_event: ErrorEvent) -> List[RecoveryExecution]:
        """Get previous recovery attempts for this error."""
        # In a real implementation, this would query the database
        return []
    
    def _create_failed_execution(self, error_event: ErrorEvent, reason: str) -> RecoveryExecution:
        """Create a failed execution record."""
        return RecoveryExecution(
            id=f"failed_{int(time.time() * 1000)}",
            recovery_action_name="none",
            error_event_id=error_event.fingerprint,
            status=RecoveryStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result=RecoveryResult.failure_result(
                execution_time=0.0,
                error_message=reason,
                output_log=f"Recovery failed: {reason}"
            )
        )


# Example usage
async def example_usage():
    """Example of how to use the recovery system."""
    
    # Configuration
    config = {
        "max_concurrent_recoveries": 3,
        "allow_high_risk_actions": False,
        "auto_rollback_on_failure": True,
        "risk_assessment": {
            "business_hours_penalty": 0.3
        }
    }
    
    # Initialize recovery orchestrator
    recovery_orchestrator = RecoveryOrchestrator(config)
    
    # Add callback for recovery completion
    async def handle_recovery_completion(execution: RecoveryExecution):
        print(f"Recovery completed: {execution.recovery_action_name}")
        print(f"Status: {execution.status.value}")
        if execution.result:
            print(f"Success: {execution.result.success}")
            print(f"Execution time: {execution.result.execution_time:.2f}s")
    
    recovery_orchestrator.add_recovery_callback(handle_recovery_completion)
    
    # Example error event
    error_event = ErrorEvent(
        timestamp=datetime.now(),
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.PERFORMANCE,
        message="High CPU usage detected in user_service",
        source_component="user_service"
    )
    
    # System state
    system_state = {
        "cpu_usage": 0.85,
        "memory_usage": 0.70,
        "active_connections": 150
    }
    
    # Execute recovery
    execution = await recovery_orchestrator.execute_recovery(error_event, system_state)
    print(f"Recovery execution: {execution.to_dict()}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run example
    asyncio.run(example_usage())

