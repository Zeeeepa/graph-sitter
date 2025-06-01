"""
Recovery System

Main system for executing automated recovery procedures and remediation actions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from ..models.config import RecoveryConfig
from ..models.events import RecoveryAction, ErrorEvent, DiagnosisResult
from ..models.enums import RecoveryStatus, ErrorSeverity
from .actions import RecoveryActionExecutor, RollbackManager, EscalationManager
from .procedures import RecoveryProcedureRegistry


class RecoverySystem:
    """
    System for automated recovery and remediation.
    
    Executes recovery procedures, manages rollbacks, and escalates
    complex issues to human intervention when needed.
    """
    
    def __init__(self, config: RecoveryConfig):
        """
        Initialize the recovery system.
        
        Args:
            config: Configuration for recovery system
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.action_executor = RecoveryActionExecutor(config)
        self.rollback_manager = RollbackManager(config)
        self.escalation_manager = EscalationManager(config)
        self.procedure_registry = RecoveryProcedureRegistry()
        
        # Active recovery actions
        self.active_actions: Dict[str, RecoveryAction] = {}
        
        # Recovery handlers
        self.recovery_handlers: List[Callable[[RecoveryAction], None]] = []
        
        # Statistics
        self.recovery_stats = {
            "total_attempts": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "escalated_issues": 0,
        }
    
    def add_recovery_handler(self, handler: Callable[[RecoveryAction], None]) -> None:
        """Add a handler for recovery action events."""
        self.recovery_handlers.append(handler)
    
    async def execute_recovery_action(self, action: RecoveryAction) -> RecoveryAction:
        """
        Execute a recovery action.
        
        Args:
            action: The recovery action to execute
            
        Returns:
            Updated recovery action with execution results
        """
        try:
            self.logger.info(f"Executing recovery action {action.id}: {action.action_type}")
            
            # Update statistics
            self.recovery_stats["total_attempts"] += 1
            
            # Add to active actions
            self.active_actions[action.id] = action
            
            # Update action status
            action.status = RecoveryStatus.IN_PROGRESS
            action.started_at = datetime.utcnow()
            
            # Notify handlers
            self._notify_handlers(action)
            
            # Execute the action
            result = await self.action_executor.execute(action)
            
            # Update action with results
            action.result = result
            action.completed_at = datetime.utcnow()
            
            if result.get("success", False):
                action.status = RecoveryStatus.COMPLETED
                self.recovery_stats["successful_recoveries"] += 1
                self.logger.info(f"Recovery action {action.id} completed successfully")
            else:
                action.status = RecoveryStatus.FAILED
                action.error_message = result.get("error", "Unknown error")
                self.recovery_stats["failed_recoveries"] += 1
                self.logger.error(f"Recovery action {action.id} failed: {action.error_message}")
                
                # Check if we should retry
                if action.retry_count < action.max_retries:
                    await self._schedule_retry(action)
                else:
                    # Max retries reached, consider escalation
                    await self._handle_failed_recovery(action)
            
            # Remove from active actions
            self.active_actions.pop(action.id, None)
            
            # Notify handlers of completion
            self._notify_handlers(action)
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error executing recovery action {action.id}: {e}")
            
            action.status = RecoveryStatus.FAILED
            action.error_message = str(e)
            action.completed_at = datetime.utcnow()
            
            # Remove from active actions
            self.active_actions.pop(action.id, None)
            
            # Notify handlers
            self._notify_handlers(action)
            
            return action
    
    async def rollback_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Rollback a failed deployment.
        
        Args:
            deployment_id: ID of the deployment to rollback
            
        Returns:
            Rollback operation result
        """
        try:
            self.logger.info(f"Initiating rollback for deployment {deployment_id}")
            
            if not self.config.rollback_enabled:
                return {
                    "success": False,
                    "error": "Rollback is disabled in configuration",
                }
            
            result = await self.rollback_manager.rollback_deployment(deployment_id)
            
            if result.get("success", False):
                self.logger.info(f"Deployment {deployment_id} rolled back successfully")
            else:
                self.logger.error(f"Rollback failed for deployment {deployment_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error rolling back deployment {deployment_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def escalate_to_human(self, issue: ErrorEvent, 
                              diagnosis: Optional[DiagnosisResult] = None,
                              failed_actions: Optional[List[RecoveryAction]] = None) -> bool:
        """
        Escalate complex issues to human intervention.
        
        Args:
            issue: The error event to escalate
            diagnosis: Optional diagnosis result
            failed_actions: Optional list of failed recovery actions
            
        Returns:
            True if escalation was successful
        """
        try:
            self.logger.info(f"Escalating issue {issue.id} to human intervention")
            
            # Update statistics
            self.recovery_stats["escalated_issues"] += 1
            
            # Prepare escalation data
            escalation_data = {
                "error_event": issue,
                "diagnosis": diagnosis,
                "failed_actions": failed_actions or [],
                "escalated_at": datetime.utcnow(),
                "severity": issue.severity,
            }
            
            # Execute escalation
            result = await self.escalation_manager.escalate(escalation_data)
            
            if result:
                self.logger.info(f"Issue {issue.id} escalated successfully")
            else:
                self.logger.error(f"Failed to escalate issue {issue.id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error escalating issue {issue.id}: {e}")
            return False
    
    async def create_recovery_actions(self, error_event: ErrorEvent,
                                    diagnosis: DiagnosisResult) -> List[RecoveryAction]:
        """
        Create recovery actions based on error event and diagnosis.
        
        Args:
            error_event: The error event to recover from
            diagnosis: Diagnosis result with recommendations
            
        Returns:
            List of recovery actions to execute
        """
        try:
            actions = []
            
            # Get recovery procedures for this error type
            procedures = await self.procedure_registry.get_procedures(
                error_event.error_type,
                error_event.severity
            )
            
            # Create actions from diagnosis recommendations
            for i, recommendation in enumerate(diagnosis.recommended_actions):
                action = RecoveryAction(
                    error_event_id=error_event.id,
                    diagnosis_id=diagnosis.id,
                    action_type=self._classify_action_type(recommendation),
                    description=recommendation,
                    parameters=self._extract_action_parameters(recommendation, error_event),
                    max_retries=self.config.max_retry_attempts,
                )
                actions.append(action)
            
            # Add procedure-based actions
            for procedure in procedures:
                for step in procedure.get("steps", []):
                    action = RecoveryAction(
                        error_event_id=error_event.id,
                        diagnosis_id=diagnosis.id,
                        action_type=step.get("type", "custom"),
                        description=step.get("description", ""),
                        parameters=step.get("parameters", {}),
                        max_retries=self.config.max_retry_attempts,
                    )
                    actions.append(action)
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error creating recovery actions: {e}")
            return []
    
    async def get_recovery_status(self, action_id: str) -> Optional[RecoveryAction]:
        """
        Get the status of a recovery action.
        
        Args:
            action_id: ID of the recovery action
            
        Returns:
            Recovery action if found, None otherwise
        """
        return self.active_actions.get(action_id)
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery system statistics."""
        total = self.recovery_stats["total_attempts"]
        success_rate = (self.recovery_stats["successful_recoveries"] / total * 100) if total > 0 else 0
        
        return {
            **self.recovery_stats,
            "success_rate": round(success_rate, 2),
            "active_actions": len(self.active_actions),
        }
    
    def _notify_handlers(self, action: RecoveryAction) -> None:
        """Notify recovery handlers of action updates."""
        for handler in self.recovery_handlers:
            try:
                handler(action)
            except Exception as e:
                self.logger.error(f"Error in recovery handler: {e}")
    
    async def _schedule_retry(self, action: RecoveryAction) -> None:
        """Schedule a retry for a failed action."""
        try:
            action.retry_count += 1
            action.status = RecoveryStatus.PENDING
            
            # Calculate retry delay (exponential backoff)
            delay = min(2 ** action.retry_count, 300)  # Max 5 minutes
            
            self.logger.info(f"Scheduling retry {action.retry_count} for action {action.id} in {delay} seconds")
            
            # Schedule retry
            asyncio.create_task(self._execute_retry(action, delay))
            
        except Exception as e:
            self.logger.error(f"Error scheduling retry for action {action.id}: {e}")
    
    async def _execute_retry(self, action: RecoveryAction, delay: float) -> None:
        """Execute a retry after delay."""
        try:
            await asyncio.sleep(delay)
            await self.execute_recovery_action(action)
            
        except Exception as e:
            self.logger.error(f"Error executing retry for action {action.id}: {e}")
    
    async def _handle_failed_recovery(self, action: RecoveryAction) -> None:
        """Handle a recovery action that has failed all retries."""
        try:
            self.logger.warning(f"Recovery action {action.id} failed after {action.retry_count} retries")
            
            # Check if we should escalate based on severity
            if action.error_message and "critical" in action.error_message.lower():
                # This is a placeholder - in a real implementation, you'd get the original error event
                self.logger.info(f"Considering escalation for critical failure in action {action.id}")
            
        except Exception as e:
            self.logger.error(f"Error handling failed recovery for action {action.id}: {e}")
    
    def _classify_action_type(self, recommendation: str) -> str:
        """Classify the type of action based on recommendation text."""
        recommendation_lower = recommendation.lower()
        
        if "restart" in recommendation_lower:
            return "restart_service"
        elif "scale" in recommendation_lower:
            return "scale_resources"
        elif "rollback" in recommendation_lower:
            return "rollback_deployment"
        elif "increase" in recommendation_lower and ("memory" in recommendation_lower or "cpu" in recommendation_lower):
            return "increase_resources"
        elif "timeout" in recommendation_lower:
            return "adjust_timeout"
        elif "monitor" in recommendation_lower:
            return "enable_monitoring"
        elif "check" in recommendation_lower:
            return "health_check"
        else:
            return "custom_action"
    
    def _extract_action_parameters(self, recommendation: str, error_event: ErrorEvent) -> Dict[str, Any]:
        """Extract parameters for action execution from recommendation and error context."""
        parameters = {}
        
        # Extract context from error event
        context = error_event.context or {}
        parameters.update(context)
        
        # Add error-specific parameters
        parameters["error_type"] = error_event.error_type.value
        parameters["severity"] = error_event.severity.value
        parameters["source_component"] = error_event.source_component
        
        # Extract specific parameters from recommendation text
        recommendation_lower = recommendation.lower()
        
        if "restart" in recommendation_lower and error_event.source_component:
            parameters["service_name"] = error_event.source_component
        
        if "scale" in recommendation_lower:
            if "cpu" in recommendation_lower:
                parameters["resource_type"] = "cpu"
                parameters["scale_factor"] = 1.5  # 50% increase
            elif "memory" in recommendation_lower:
                parameters["resource_type"] = "memory"
                parameters["scale_factor"] = 1.5  # 50% increase
        
        return parameters

