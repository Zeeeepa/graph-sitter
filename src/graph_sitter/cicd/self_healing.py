"""
Self-Healing System for Graph-Sitter CI/CD

Provides automated error detection, diagnosis, and recovery:
- Real-time system monitoring
- Automated error classification
- Root cause analysis
- Automated recovery procedures
- Learning from incidents
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Incident status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ErrorClassification(Enum):
    """Error classification types"""
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    RUNTIME_ERROR = "runtime_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    DEPENDENCY_ISSUE = "dependency_issue"
    CONFIGURATION_ERROR = "configuration_error"
    INTEGRATION_FAILURE = "integration_failure"
    DATA_INCONSISTENCY = "data_inconsistency"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """System health metric definition"""
    name: str = ""
    current_value: float = 0.0
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0
    unit: str = ""
    status: str = "normal"  # normal, warning, critical
    measured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_status(self) -> None:
        """Update status based on thresholds"""
        if self.current_value >= self.threshold_critical:
            self.status = "critical"
        elif self.current_value >= self.threshold_warning:
            self.status = "warning"
        else:
            self.status = "normal"


@dataclass
class Incident:
    """Self-healing incident tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    # Incident classification
    incident_type: str = ""
    error_classification: ErrorClassification = ErrorClassification.UNKNOWN
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    
    # Detection
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detection_method: str = ""  # threshold, pattern, anomaly, manual
    
    # Description
    title: str = ""
    description: str = ""
    error_message: str = ""
    stack_trace: str = ""
    
    # Context
    affected_components: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    
    # Resolution tracking
    status: IncidentStatus = IncidentStatus.DETECTED
    resolved_at: Optional[datetime] = None
    resolution_method: str = ""
    resolution_steps: List[str] = field(default_factory=list)
    manual_intervention_required: bool = False
    
    # Effectiveness
    effectiveness_score: Optional[float] = None  # 0-100
    time_to_detect_seconds: Optional[int] = None
    time_to_resolve_seconds: Optional[int] = None
    
    # Learning
    root_cause: str = ""
    prevention_measures: List[str] = field(default_factory=list)
    lessons_learned: str = ""
    
    def start_investigation(self) -> None:
        """Mark incident as under investigation"""
        self.status = IncidentStatus.INVESTIGATING
    
    def start_resolution(self, method: str) -> None:
        """Mark incident as being resolved"""
        self.status = IncidentStatus.RESOLVING
        self.resolution_method = method
    
    def resolve_incident(self, effectiveness_score: float = None) -> None:
        """Mark incident as resolved"""
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc)
        
        if self.resolved_at:
            self.time_to_resolve_seconds = int((self.resolved_at - self.detected_at).total_seconds())
        
        if effectiveness_score is not None:
            self.effectiveness_score = effectiveness_score
    
    def close_incident(self) -> None:
        """Close the incident"""
        self.status = IncidentStatus.CLOSED


@dataclass
class RecoveryProcedure:
    """Automated recovery procedure definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Applicability
    error_patterns: List[str] = field(default_factory=list)
    component_types: List[str] = field(default_factory=list)
    severity_levels: List[IncidentSeverity] = field(default_factory=list)
    
    # Procedure steps
    steps: List[Dict[str, Any]] = field(default_factory=list)
    timeout_seconds: int = 300
    max_retries: int = 3
    
    # Effectiveness tracking
    success_rate: float = 0.0
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    
    # Configuration
    is_active: bool = True
    requires_approval: bool = False
    
    def is_applicable(self, incident: Incident) -> bool:
        """Check if procedure is applicable to incident"""
        # Check error patterns
        if self.error_patterns:
            pattern_match = any(
                pattern in incident.error_message.lower() or pattern in incident.description.lower()
                for pattern in self.error_patterns
            )
            if not pattern_match:
                return False
        
        # Check component types
        if self.component_types:
            component_match = any(
                comp_type in incident.affected_components
                for comp_type in self.component_types
            )
            if not component_match:
                return False
        
        # Check severity levels
        if self.severity_levels and incident.severity not in self.severity_levels:
            return False
        
        return True
    
    def record_usage(self, success: bool) -> None:
        """Record procedure usage and update success rate"""
        self.usage_count += 1
        self.last_used_at = datetime.now(timezone.utc)
        
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            current_successes = self.success_rate * (self.usage_count - 1)
            if success:
                current_successes += 1
            self.success_rate = current_successes / self.usage_count


class SelfHealingSystem:
    """
    Comprehensive self-healing system with:
    - Real-time monitoring and alerting
    - Automated error detection and classification
    - Root cause analysis
    - Automated recovery procedures
    - Learning and improvement
    """
    
    def __init__(self, organization_id: str, database_connection=None):
        self.organization_id = organization_id
        self.db = database_connection
        
        # System state
        self.running = False
        self.health_metrics: Dict[str, HealthMetric] = {}
        self.incidents: Dict[str, Incident] = {}
        self.recovery_procedures: Dict[str, RecoveryProcedure] = {}
        
        # Configuration
        self.monitoring_interval = 30  # seconds
        self.alert_thresholds = {
            "cpu_usage": {"warning": 80, "critical": 95},
            "memory_usage": {"warning": 85, "critical": 95},
            "error_rate": {"warning": 5, "critical": 10},
            "response_time": {"warning": 2000, "critical": 5000}
        }
        
        # Event handlers
        self.error_detectors: List[Callable] = []
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # Performance tracking
        self.metrics = {
            "total_incidents": 0,
            "auto_resolved_incidents": 0,
            "manual_intervention_required": 0,
            "avg_detection_time_seconds": 0.0,
            "avg_resolution_time_seconds": 0.0,
            "system_availability": 99.9
        }
        
        # Initialize default recovery procedures
        self._initialize_default_procedures()
    
    async def start(self) -> None:
        """Start the self-healing system"""
        self.running = True
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_system_health())
        asyncio.create_task(self._process_incidents())
        
        logger.info("Self-healing system started")
    
    async def stop(self) -> None:
        """Stop the self-healing system"""
        self.running = False
        logger.info("Self-healing system stopped")
    
    async def detect_incident(self, 
                            incident_type: str,
                            error_message: str,
                            context: Dict[str, Any] = None,
                            severity: IncidentSeverity = IncidentSeverity.MEDIUM) -> str:
        """Detect and register a new incident"""
        
        # Create incident
        incident = Incident(
            organization_id=self.organization_id,
            incident_type=incident_type,
            severity=severity,
            error_message=error_message,
            title=f"{incident_type}: {error_message[:100]}",
            description=error_message,
            context_data=context or {},
            detection_method="api"
        )
        
        # Classify error
        incident.error_classification = self._classify_error(error_message, context or {})
        
        # Store incident
        self.incidents[incident.id] = incident
        self.metrics["total_incidents"] += 1
        
        logger.warning(f"Incident detected: {incident.id} - {incident.title}")
        
        # Trigger automated response
        asyncio.create_task(self._handle_incident(incident.id))
        
        # Store in database
        if self.db:
            await self._store_incident_in_db(incident)
        
        return incident.id
    
    async def resolve_incident_manually(self, incident_id: str, resolution_notes: str) -> bool:
        """Manually resolve an incident"""
        incident = self.incidents.get(incident_id)
        if not incident:
            return False
        
        incident.resolve_incident()
        incident.resolution_method = "manual"
        incident.resolution_steps.append(f"Manual resolution: {resolution_notes}")
        incident.manual_intervention_required = True
        
        self.metrics["manual_intervention_required"] += 1
        
        logger.info(f"Incident {incident_id} manually resolved")
        return True
    
    async def add_recovery_procedure(self, procedure: RecoveryProcedure) -> str:
        """Add a new recovery procedure"""
        self.recovery_procedures[procedure.id] = procedure
        logger.info(f"Added recovery procedure: {procedure.name}")
        return procedure.id
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        health_status = {}
        
        for name, metric in self.health_metrics.items():
            health_status[name] = {
                "value": metric.current_value,
                "status": metric.status,
                "unit": metric.unit,
                "measured_at": metric.measured_at.isoformat()
            }
        
        # Calculate overall health score
        critical_count = sum(1 for m in self.health_metrics.values() if m.status == "critical")
        warning_count = sum(1 for m in self.health_metrics.values() if m.status == "warning")
        total_metrics = len(self.health_metrics)
        
        if total_metrics > 0:
            health_score = max(0, 100 - (critical_count * 30) - (warning_count * 10))
        else:
            health_score = 100
        
        return {
            "overall_health_score": health_score,
            "metrics": health_status,
            "active_incidents": len([i for i in self.incidents.values() if i.status != IncidentStatus.CLOSED]),
            "system_status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "unhealthy",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_incident_metrics(self) -> Dict[str, Any]:
        """Get incident and recovery metrics"""
        recent_incidents = [
            i for i in self.incidents.values()
            if i.detected_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ]
        
        if not recent_incidents:
            return {"period_days": 30, "incident_count": 0}
        
        # Calculate metrics
        auto_resolved = len([i for i in recent_incidents if not i.manual_intervention_required and i.status == IncidentStatus.RESOLVED])
        avg_resolution_time = 0
        resolved_incidents = [i for i in recent_incidents if i.time_to_resolve_seconds is not None]
        
        if resolved_incidents:
            avg_resolution_time = sum(i.time_to_resolve_seconds for i in resolved_incidents) / len(resolved_incidents)
        
        # Group by severity
        severity_breakdown = {}
        for severity in IncidentSeverity:
            severity_breakdown[severity.value] = len([i for i in recent_incidents if i.severity == severity])
        
        return {
            "period_days": 30,
            "total_incidents": len(recent_incidents),
            "auto_resolved_incidents": auto_resolved,
            "manual_intervention_required": len(recent_incidents) - auto_resolved,
            "auto_resolution_rate": auto_resolved / len(recent_incidents) if recent_incidents else 0,
            "avg_resolution_time_seconds": avg_resolution_time,
            "severity_breakdown": severity_breakdown,
            "recovery_procedures": {
                "total": len(self.recovery_procedures),
                "active": len([p for p in self.recovery_procedures.values() if p.is_active]),
                "avg_success_rate": sum(p.success_rate for p in self.recovery_procedures.values()) / len(self.recovery_procedures) if self.recovery_procedures else 0
            }
        }
    
    async def _monitor_system_health(self) -> None:
        """Continuously monitor system health"""
        while self.running:
            try:
                # Update health metrics
                await self._update_health_metrics()
                
                # Check for threshold violations
                await self._check_health_thresholds()
                
                # Sleep until next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _update_health_metrics(self) -> None:
        """Update system health metrics"""
        # Mock health metrics (in real implementation, would collect actual metrics)
        import random
        
        metrics_data = {
            "cpu_usage": random.uniform(20, 90),
            "memory_usage": random.uniform(30, 85),
            "error_rate": random.uniform(0, 8),
            "response_time": random.uniform(100, 3000),
            "active_connections": random.randint(50, 200),
            "disk_usage": random.uniform(40, 80)
        }
        
        for name, value in metrics_data.items():
            if name not in self.health_metrics:
                thresholds = self.alert_thresholds.get(name, {"warning": 80, "critical": 95})
                self.health_metrics[name] = HealthMetric(
                    name=name,
                    threshold_warning=thresholds["warning"],
                    threshold_critical=thresholds["critical"],
                    unit="%" if name.endswith("_usage") or name == "error_rate" else "ms" if name == "response_time" else "count"
                )
            
            metric = self.health_metrics[name]
            metric.current_value = value
            metric.measured_at = datetime.now(timezone.utc)
            metric.update_status()
    
    async def _check_health_thresholds(self) -> None:
        """Check health metrics against thresholds and create incidents"""
        for metric in self.health_metrics.values():
            if metric.status == "critical":
                # Check if we already have an active incident for this metric
                active_incidents = [
                    i for i in self.incidents.values()
                    if i.incident_type == f"threshold_violation_{metric.name}"
                    and i.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
                ]
                
                if not active_incidents:
                    await self.detect_incident(
                        incident_type=f"threshold_violation_{metric.name}",
                        error_message=f"{metric.name} exceeded critical threshold: {metric.current_value}{metric.unit} > {metric.threshold_critical}{metric.unit}",
                        context={"metric": metric.name, "value": metric.current_value, "threshold": metric.threshold_critical},
                        severity=IncidentSeverity.CRITICAL
                    )
    
    async def _process_incidents(self) -> None:
        """Process and handle incidents"""
        while self.running:
            try:
                # Find incidents that need processing
                pending_incidents = [
                    i for i in self.incidents.values()
                    if i.status == IncidentStatus.DETECTED
                ]
                
                for incident in pending_incidents:
                    await self._handle_incident(incident.id)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error processing incidents: {e}")
                await asyncio.sleep(5)
    
    async def _handle_incident(self, incident_id: str) -> None:
        """Handle a specific incident"""
        incident = self.incidents.get(incident_id)
        if not incident:
            return
        
        logger.info(f"Handling incident {incident_id}")
        
        # Start investigation
        incident.start_investigation()
        
        # Perform root cause analysis
        root_cause = await self._analyze_root_cause(incident)
        incident.root_cause = root_cause
        
        # Find applicable recovery procedures
        applicable_procedures = [
            p for p in self.recovery_procedures.values()
            if p.is_active and p.is_applicable(incident)
        ]
        
        if applicable_procedures:
            # Sort by success rate
            applicable_procedures.sort(key=lambda p: p.success_rate, reverse=True)
            
            # Try recovery procedures
            for procedure in applicable_procedures:
                incident.start_resolution(f"automated_{procedure.name}")
                success = await self._execute_recovery_procedure(procedure, incident)
                
                if success:
                    incident.resolve_incident(effectiveness_score=85.0)
                    procedure.record_usage(True)
                    self.metrics["auto_resolved_incidents"] += 1
                    logger.info(f"Incident {incident_id} automatically resolved using {procedure.name}")
                    return
                else:
                    procedure.record_usage(False)
        
        # If no automated resolution worked, require manual intervention
        incident.manual_intervention_required = True
        incident.resolution_steps.append("Automated recovery failed, manual intervention required")
        
        logger.warning(f"Incident {incident_id} requires manual intervention")
    
    async def _analyze_root_cause(self, incident: Incident) -> str:
        """Perform root cause analysis"""
        # Simple root cause analysis (can be enhanced with ML)
        error_msg = incident.error_message.lower()
        
        if "timeout" in error_msg or "connection" in error_msg:
            return "Network connectivity or timeout issue"
        elif "memory" in error_msg or "out of memory" in error_msg:
            return "Memory exhaustion"
        elif "permission" in error_msg or "access denied" in error_msg:
            return "Permission or authentication issue"
        elif "disk" in error_msg or "space" in error_msg:
            return "Disk space issue"
        elif "database" in error_msg or "sql" in error_msg:
            return "Database connectivity or query issue"
        else:
            return "Unknown root cause - requires investigation"
    
    async def _execute_recovery_procedure(self, procedure: RecoveryProcedure, incident: Incident) -> bool:
        """Execute a recovery procedure"""
        logger.info(f"Executing recovery procedure: {procedure.name}")
        
        try:
            for step in procedure.steps:
                step_type = step.get("type", "command")
                
                if step_type == "restart_service":
                    await self._restart_service(step.get("service_name", ""))
                elif step_type == "clear_cache":
                    await self._clear_cache(step.get("cache_type", ""))
                elif step_type == "scale_resources":
                    await self._scale_resources(step.get("resource_type", ""), step.get("scale_factor", 1.5))
                elif step_type == "rollback_deployment":
                    await self._rollback_deployment(step.get("deployment_id", ""))
                elif step_type == "wait":
                    await asyncio.sleep(step.get("duration", 5))
                
                # Add step to incident resolution
                incident.resolution_steps.append(f"Executed: {step_type}")
            
            # Simulate success/failure (in real implementation, would check actual results)
            import random
            success = random.random() > 0.3  # 70% success rate
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing recovery procedure {procedure.name}: {e}")
            incident.resolution_steps.append(f"Error in {procedure.name}: {str(e)}")
            return False
    
    async def _restart_service(self, service_name: str) -> None:
        """Restart a service"""
        logger.info(f"Restarting service: {service_name}")
        await asyncio.sleep(0.1)  # Simulate restart
    
    async def _clear_cache(self, cache_type: str) -> None:
        """Clear cache"""
        logger.info(f"Clearing cache: {cache_type}")
        await asyncio.sleep(0.1)  # Simulate cache clear
    
    async def _scale_resources(self, resource_type: str, scale_factor: float) -> None:
        """Scale resources"""
        logger.info(f"Scaling {resource_type} by factor {scale_factor}")
        await asyncio.sleep(0.1)  # Simulate scaling
    
    async def _rollback_deployment(self, deployment_id: str) -> None:
        """Rollback deployment"""
        logger.info(f"Rolling back deployment: {deployment_id}")
        await asyncio.sleep(0.1)  # Simulate rollback
    
    def _classify_error(self, error_message: str, context: Dict[str, Any]) -> ErrorClassification:
        """Classify error based on message and context"""
        error_msg = error_message.lower()
        
        if "syntax" in error_msg or "parse" in error_msg:
            return ErrorClassification.SYNTAX_ERROR
        elif "timeout" in error_msg or "connection" in error_msg:
            return ErrorClassification.INTEGRATION_FAILURE
        elif "memory" in error_msg or "out of memory" in error_msg:
            return ErrorClassification.RESOURCE_EXHAUSTION
        elif "permission" in error_msg or "unauthorized" in error_msg:
            return ErrorClassification.SECURITY_VULNERABILITY
        elif "config" in error_msg or "setting" in error_msg:
            return ErrorClassification.CONFIGURATION_ERROR
        elif "performance" in error_msg or "slow" in error_msg:
            return ErrorClassification.PERFORMANCE_ISSUE
        else:
            return ErrorClassification.RUNTIME_ERROR
    
    def _initialize_default_procedures(self) -> None:
        """Initialize default recovery procedures"""
        # Service restart procedure
        restart_procedure = RecoveryProcedure(
            name="Service Restart",
            description="Restart failed services",
            error_patterns=["connection refused", "service unavailable", "timeout"],
            component_types=["service", "api", "worker"],
            severity_levels=[IncidentSeverity.MEDIUM, IncidentSeverity.HIGH],
            steps=[
                {"type": "restart_service", "service_name": "target_service"},
                {"type": "wait", "duration": 10},
                {"type": "health_check"}
            ]
        )
        self.recovery_procedures[restart_procedure.id] = restart_procedure
        
        # Cache clear procedure
        cache_procedure = RecoveryProcedure(
            name="Cache Clear",
            description="Clear system caches",
            error_patterns=["cache", "stale data", "inconsistent"],
            component_types=["cache", "database", "api"],
            severity_levels=[IncidentSeverity.LOW, IncidentSeverity.MEDIUM],
            steps=[
                {"type": "clear_cache", "cache_type": "application"},
                {"type": "clear_cache", "cache_type": "database"},
                {"type": "wait", "duration": 5}
            ]
        )
        self.recovery_procedures[cache_procedure.id] = cache_procedure
        
        # Resource scaling procedure
        scaling_procedure = RecoveryProcedure(
            name="Resource Scaling",
            description="Scale resources to handle load",
            error_patterns=["high load", "resource exhaustion", "memory", "cpu"],
            component_types=["compute", "memory", "storage"],
            severity_levels=[IncidentSeverity.HIGH, IncidentSeverity.CRITICAL],
            steps=[
                {"type": "scale_resources", "resource_type": "cpu", "scale_factor": 1.5},
                {"type": "scale_resources", "resource_type": "memory", "scale_factor": 1.3},
                {"type": "wait", "duration": 30}
            ]
        )
        self.recovery_procedures[scaling_procedure.id] = scaling_procedure
    
    async def _store_incident_in_db(self, incident: Incident) -> None:
        """Store incident in database"""
        # Implementation would depend on database connection
        pass


class IncidentManager:
    """
    High-level incident management interface
    """
    
    def __init__(self, self_healing_system: SelfHealingSystem):
        self.system = self_healing_system
    
    async def create_incident(self, title: str, description: str, severity: IncidentSeverity = IncidentSeverity.MEDIUM) -> str:
        """Create a new incident"""
        return await self.system.detect_incident(
            incident_type="manual",
            error_message=description,
            context={"title": title},
            severity=severity
        )
    
    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident details"""
        return self.system.incidents.get(incident_id)
    
    async def list_incidents(self, status: Optional[IncidentStatus] = None, severity: Optional[IncidentSeverity] = None) -> List[Incident]:
        """List incidents with optional filters"""
        incidents = list(self.system.incidents.values())
        
        if status:
            incidents = [i for i in incidents if i.status == status]
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        
        return incidents
    
    async def resolve_incident(self, incident_id: str, resolution_notes: str) -> bool:
        """Resolve an incident manually"""
        return await self.system.resolve_incident_manually(incident_id, resolution_notes)


# Utility functions
def create_incident_from_dict(data: Dict[str, Any]) -> Incident:
    """Create an Incident object from dictionary data"""
    incident = Incident()
    for key, value in data.items():
        if key == "severity" and isinstance(value, str):
            incident.severity = IncidentSeverity(value)
        elif key == "status" and isinstance(value, str):
            incident.status = IncidentStatus(value)
        elif key == "error_classification" and isinstance(value, str):
            incident.error_classification = ErrorClassification(value)
        elif hasattr(incident, key):
            setattr(incident, key, value)
    return incident

