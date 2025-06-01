"""
Self-Healing Orchestrator

Main orchestrator that coordinates all self-healing components.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .models.config import SelfHealingConfig
from .models.events import ErrorEvent, DiagnosisResult, RecoveryAction
from .models.enums import ErrorSeverity, RecoveryStatus
from .error_detection.service import ErrorDetectionService
from .diagnosis.engine import DiagnosisEngine
from .recovery.system import RecoverySystem
from .monitoring.health_monitor import HealthMonitor


class SelfHealingOrchestrator:
    """
    Main orchestrator for the self-healing architecture.
    
    Coordinates error detection, diagnosis, recovery, and monitoring
    to provide comprehensive automated error recovery capabilities.
    """
    
    def __init__(self, config: SelfHealingConfig):
        """
        Initialize the self-healing orchestrator.
        
        Args:
            config: Configuration for self-healing system
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # Initialize components
        self.error_detection = ErrorDetectionService(config.error_detection)
        self.diagnosis_engine = DiagnosisEngine()
        self.recovery_system = RecoverySystem(config.recovery)
        self.health_monitor = HealthMonitor()
        
        # Event tracking
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            "total_errors_detected": 0,
            "total_errors_resolved": 0,
            "total_recoveries_attempted": 0,
            "total_recoveries_successful": 0,
            "total_escalations": 0,
        }
        
        # Setup event handlers
        self._setup_event_handlers()
    
    async def start(self) -> None:
        """Start the self-healing system."""
        if not self.config.enabled:
            self.logger.info("Self-healing system is disabled in configuration")
            return
        
        if self.is_running:
            self.logger.warning("Self-healing system is already running")
            return
        
        self.logger.info("Starting self-healing orchestrator")
        self.is_running = True
        
        try:
            # Start all components
            await self.error_detection.start()
            await self.health_monitor.start()
            
            self.logger.info("Self-healing system started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting self-healing system: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the self-healing system."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping self-healing orchestrator")
        self.is_running = False
        
        try:
            # Stop all components
            await self.error_detection.stop()
            await self.health_monitor.stop()
            
            self.logger.info("Self-healing system stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping self-healing system: {e}")
    
    async def handle_error_event(self, error_event: ErrorEvent) -> Optional[str]:
        """
        Handle a detected error event through the complete self-healing workflow.
        
        Args:
            error_event: The error event to handle
            
        Returns:
            Incident ID if handling was initiated, None otherwise
        """
        try:
            incident_id = error_event.id
            self.stats["total_errors_detected"] += 1
            
            self.logger.info(f"Handling error event {incident_id}: {error_event.error_type.value}")
            
            # Create incident record
            incident = {
                "id": incident_id,
                "error_event": error_event,
                "started_at": datetime.utcnow(),
                "status": "analyzing",
                "diagnosis": None,
                "recovery_actions": [],
                "resolved": False,
            }
            self.active_incidents[incident_id] = incident
            
            # Record error for monitoring
            self.health_monitor.record_error_event(error_event)
            
            # Step 1: Classify and analyze the error
            classified_error = await self.error_detection.classify_error(error_event)
            incident["error_event"] = classified_error
            
            # Step 2: Perform diagnosis
            incident["status"] = "diagnosing"
            diagnosis = await self.diagnosis_engine.analyze_error(incident_id, classified_error)
            incident["diagnosis"] = diagnosis
            
            # Step 3: Determine if we should attempt recovery
            should_recover = self._should_attempt_recovery(classified_error, diagnosis)
            
            if should_recover:
                # Step 4: Create and execute recovery actions
                incident["status"] = "recovering"
                await self._execute_recovery_workflow(incident)
            else:
                # Step 5: Escalate if recovery is not appropriate
                incident["status"] = "escalating"
                await self._escalate_incident(incident)
            
            return incident_id
            
        except Exception as e:
            self.logger.error(f"Error handling error event {error_event.id}: {e}")
            return None
    
    async def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an active incident.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Incident status information
        """
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return None
        
        return {
            "id": incident_id,
            "status": incident["status"],
            "error_type": incident["error_event"].error_type.value,
            "severity": incident["error_event"].severity.value,
            "started_at": incident["started_at"].isoformat(),
            "diagnosis_confidence": incident["diagnosis"].confidence.value if incident["diagnosis"] else None,
            "recovery_actions_count": len(incident["recovery_actions"]),
            "resolved": incident["resolved"],
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "enabled": self.config.enabled,
            "running": self.is_running,
            "active_incidents": len(self.active_incidents),
            "statistics": self.stats.copy(),
            "health_status": self.health_monitor.get_system_status(),
            "recovery_stats": self.recovery_system.get_recovery_statistics(),
        }
    
    def get_effectiveness_report(self) -> Dict[str, Any]:
        """Get effectiveness report from health monitor."""
        return self.health_monitor.effectiveness_tracker.get_overall_effectiveness_report()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers between components."""
        # Error detection handlers
        self.error_detection.add_error_handler(self._on_error_detected)
        self.error_detection.add_health_handler(self._on_health_metric)
        
        # Recovery system handlers
        self.recovery_system.add_recovery_handler(self._on_recovery_update)
        
        # Health monitor handlers
        self.health_monitor.add_status_handler(self._on_health_status_change)
    
    def _on_error_detected(self, error_event: ErrorEvent) -> None:
        """Handle error detection events."""
        try:
            # Create async task to handle the error
            asyncio.create_task(self.handle_error_event(error_event))
        except Exception as e:
            self.logger.error(f"Error in error detection handler: {e}")
    
    def _on_health_metric(self, health_metric) -> None:
        """Handle health metric updates."""
        try:
            # Add metric data to diagnosis engine for context
            self.diagnosis_engine.add_metric_data(health_metric.metric_name, [health_metric])
        except Exception as e:
            self.logger.error(f"Error in health metric handler: {e}")
    
    def _on_recovery_update(self, recovery_action: RecoveryAction) -> None:
        """Handle recovery action updates."""
        try:
            # Track recovery effectiveness
            if recovery_action.status in [RecoveryStatus.COMPLETED, RecoveryStatus.FAILED]:
                asyncio.create_task(
                    self.health_monitor.track_recovery_effectiveness(
                        recovery_action.id, recovery_action
                    )
                )
        except Exception as e:
            self.logger.error(f"Error in recovery update handler: {e}")
    
    def _on_health_status_change(self, new_status) -> None:
        """Handle overall health status changes."""
        try:
            self.logger.info(f"System health status changed to: {new_status.value}")
        except Exception as e:
            self.logger.error(f"Error in health status change handler: {e}")
    
    def _should_attempt_recovery(self, error_event: ErrorEvent, 
                               diagnosis: DiagnosisResult) -> bool:
        """Determine if we should attempt automated recovery."""
        try:
            # Don't attempt recovery for low confidence diagnosis
            if diagnosis.confidence.value in ["low"]:
                return False
            
            # Always attempt recovery for critical errors with high confidence
            if (error_event.severity == ErrorSeverity.CRITICAL and 
                diagnosis.confidence.value in ["high", "very_high"]):
                return True
            
            # Attempt recovery for high severity with medium+ confidence
            if (error_event.severity == ErrorSeverity.HIGH and 
                diagnosis.confidence.value in ["medium", "high", "very_high"]):
                return True
            
            # Attempt recovery for medium severity with high confidence
            if (error_event.severity == ErrorSeverity.MEDIUM and 
                diagnosis.confidence.value in ["high", "very_high"]):
                return True
            
            # Don't attempt recovery for low severity errors
            if error_event.severity == ErrorSeverity.LOW:
                return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error determining recovery attempt: {e}")
            return False
    
    async def _execute_recovery_workflow(self, incident: Dict[str, Any]) -> None:
        """Execute the recovery workflow for an incident."""
        try:
            error_event = incident["error_event"]
            diagnosis = incident["diagnosis"]
            
            # Create recovery actions
            recovery_actions = await self.recovery_system.create_recovery_actions(
                error_event, diagnosis
            )
            
            if not recovery_actions:
                self.logger.warning(f"No recovery actions created for incident {incident['id']}")
                await self._escalate_incident(incident)
                return
            
            incident["recovery_actions"] = recovery_actions
            self.stats["total_recoveries_attempted"] += len(recovery_actions)
            
            # Execute recovery actions
            successful_actions = 0
            for action in recovery_actions:
                try:
                    result_action = await self.recovery_system.execute_recovery_action(action)
                    
                    if result_action.status == RecoveryStatus.COMPLETED:
                        successful_actions += 1
                        self.stats["total_recoveries_successful"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Error executing recovery action {action.id}: {e}")
            
            # Check if recovery was successful
            if successful_actions > 0:
                incident["status"] = "resolved"
                incident["resolved"] = True
                self.stats["total_errors_resolved"] += 1
                
                # Record resolution time
                resolution_time = (datetime.utcnow() - incident["started_at"]).total_seconds()
                self.health_monitor.record_error_resolution(error_event, resolution_time)
                
                self.logger.info(f"Incident {incident['id']} resolved with {successful_actions} successful actions")
            else:
                # Recovery failed, escalate
                await self._escalate_incident(incident)
            
        except Exception as e:
            self.logger.error(f"Error in recovery workflow for incident {incident['id']}: {e}")
            await self._escalate_incident(incident)
    
    async def _escalate_incident(self, incident: Dict[str, Any]) -> None:
        """Escalate an incident to human intervention."""
        try:
            error_event = incident["error_event"]
            diagnosis = incident.get("diagnosis")
            failed_actions = [
                action for action in incident.get("recovery_actions", [])
                if action.status == RecoveryStatus.FAILED
            ]
            
            success = await self.recovery_system.escalate_to_human(
                error_event, diagnosis, failed_actions
            )
            
            if success:
                incident["status"] = "escalated"
                self.stats["total_escalations"] += 1
                self.logger.info(f"Incident {incident['id']} escalated to human intervention")
            else:
                incident["status"] = "escalation_failed"
                self.logger.error(f"Failed to escalate incident {incident['id']}")
            
        except Exception as e:
            self.logger.error(f"Error escalating incident {incident['id']}: {e}")
            incident["status"] = "escalation_failed"

