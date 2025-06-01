"""
Recovery procedure registry and management.
"""

import logging
from typing import Dict, Any, List, Optional

from ..models.enums import ErrorType, ErrorSeverity


class RecoveryProcedureRegistry:
    """Registry for recovery procedures and best practices."""
    
    def __init__(self):
        """Initialize the procedure registry."""
        self.logger = logging.getLogger(__name__)
        
        # Built-in recovery procedures
        self.procedures = {
            ErrorType.MEMORY_LEAK: {
                ErrorSeverity.CRITICAL: [
                    {
                        "name": "immediate_memory_recovery",
                        "description": "Immediate actions for critical memory issues",
                        "steps": [
                            {
                                "type": "restart_service",
                                "description": "Restart affected service immediately",
                                "parameters": {"priority": "high"},
                                "timeout": 60,
                            },
                            {
                                "type": "scale_resources",
                                "description": "Scale up memory resources",
                                "parameters": {"resource_type": "memory", "scale_factor": 2.0},
                                "timeout": 300,
                            },
                            {
                                "type": "enable_monitoring",
                                "description": "Enable memory profiling",
                                "parameters": {"monitoring_type": "memory_profiling"},
                                "timeout": 30,
                            },
                        ],
                        "success_rate": 0.85,
                        "estimated_duration": 600,  # seconds
                    }
                ],
                ErrorSeverity.HIGH: [
                    {
                        "name": "memory_leak_mitigation",
                        "description": "Standard memory leak mitigation",
                        "steps": [
                            {
                                "type": "enable_monitoring",
                                "description": "Enable detailed memory monitoring",
                                "parameters": {"monitoring_type": "memory_detailed"},
                                "timeout": 30,
                            },
                            {
                                "type": "increase_resources",
                                "description": "Increase memory allocation",
                                "parameters": {"resource_type": "memory", "increase_factor": 1.5},
                                "timeout": 120,
                            },
                            {
                                "type": "health_check",
                                "description": "Verify system stability",
                                "parameters": {"check_type": "memory_stability"},
                                "timeout": 60,
                            },
                        ],
                        "success_rate": 0.75,
                        "estimated_duration": 300,
                    }
                ],
            },
            ErrorType.CPU_SPIKE: {
                ErrorSeverity.CRITICAL: [
                    {
                        "name": "cpu_spike_emergency",
                        "description": "Emergency CPU spike response",
                        "steps": [
                            {
                                "type": "scale_resources",
                                "description": "Scale up CPU resources immediately",
                                "parameters": {"resource_type": "cpu", "scale_factor": 2.0},
                                "timeout": 180,
                            },
                            {
                                "type": "enable_monitoring",
                                "description": "Enable CPU profiling",
                                "parameters": {"monitoring_type": "cpu_profiling"},
                                "timeout": 30,
                            },
                            {
                                "type": "health_check",
                                "description": "Check for runaway processes",
                                "parameters": {"check_type": "process_analysis"},
                                "timeout": 60,
                            },
                        ],
                        "success_rate": 0.80,
                        "estimated_duration": 400,
                    }
                ],
                ErrorSeverity.HIGH: [
                    {
                        "name": "cpu_optimization",
                        "description": "CPU usage optimization",
                        "steps": [
                            {
                                "type": "enable_monitoring",
                                "description": "Enable CPU monitoring",
                                "parameters": {"monitoring_type": "cpu_detailed"},
                                "timeout": 30,
                            },
                            {
                                "type": "increase_resources",
                                "description": "Increase CPU allocation",
                                "parameters": {"resource_type": "cpu", "increase_factor": 1.3},
                                "timeout": 120,
                            },
                        ],
                        "success_rate": 0.70,
                        "estimated_duration": 200,
                    }
                ],
            },
            ErrorType.NETWORK_TIMEOUT: {
                ErrorSeverity.HIGH: [
                    {
                        "name": "network_timeout_recovery",
                        "description": "Network timeout mitigation",
                        "steps": [
                            {
                                "type": "adjust_timeout",
                                "description": "Increase network timeouts",
                                "parameters": {"timeout_type": "network", "multiplier": 2.0},
                                "timeout": 60,
                            },
                            {
                                "type": "health_check",
                                "description": "Check network connectivity",
                                "parameters": {"check_type": "network_connectivity"},
                                "timeout": 120,
                            },
                            {
                                "type": "enable_monitoring",
                                "description": "Enable network monitoring",
                                "parameters": {"monitoring_type": "network_latency"},
                                "timeout": 30,
                            },
                        ],
                        "success_rate": 0.65,
                        "estimated_duration": 300,
                    }
                ],
            },
            ErrorType.DATABASE_CONNECTION: {
                ErrorSeverity.CRITICAL: [
                    {
                        "name": "database_emergency_recovery",
                        "description": "Emergency database connection recovery",
                        "steps": [
                            {
                                "type": "restart_service",
                                "description": "Restart database connection pool",
                                "parameters": {"service_type": "database_pool"},
                                "timeout": 120,
                            },
                            {
                                "type": "scale_resources",
                                "description": "Scale database connections",
                                "parameters": {"resource_type": "database_connections", "scale_factor": 1.5},
                                "timeout": 180,
                            },
                            {
                                "type": "health_check",
                                "description": "Verify database connectivity",
                                "parameters": {"check_type": "database_health"},
                                "timeout": 60,
                            },
                        ],
                        "success_rate": 0.90,
                        "estimated_duration": 500,
                    }
                ],
                ErrorSeverity.HIGH: [
                    {
                        "name": "database_connection_recovery",
                        "description": "Standard database connection recovery",
                        "steps": [
                            {
                                "type": "increase_resources",
                                "description": "Increase connection pool size",
                                "parameters": {"resource_type": "database_connections", "increase_factor": 1.3},
                                "timeout": 120,
                            },
                            {
                                "type": "adjust_timeout",
                                "description": "Increase database timeouts",
                                "parameters": {"timeout_type": "database", "multiplier": 1.5},
                                "timeout": 60,
                            },
                        ],
                        "success_rate": 0.75,
                        "estimated_duration": 240,
                    }
                ],
            },
            ErrorType.DEPLOYMENT_FAILURE: {
                ErrorSeverity.CRITICAL: [
                    {
                        "name": "deployment_rollback",
                        "description": "Emergency deployment rollback",
                        "steps": [
                            {
                                "type": "rollback_deployment",
                                "description": "Rollback to previous stable version",
                                "parameters": {"rollback_type": "immediate"},
                                "timeout": 600,
                            },
                            {
                                "type": "health_check",
                                "description": "Verify rollback success",
                                "parameters": {"check_type": "deployment_health"},
                                "timeout": 120,
                            },
                        ],
                        "success_rate": 0.95,
                        "estimated_duration": 800,
                    }
                ],
            },
        }
    
    async def get_procedures(self, error_type: ErrorType, 
                           severity: ErrorSeverity) -> List[Dict[str, Any]]:
        """
        Get recovery procedures for a specific error type and severity.
        
        Args:
            error_type: Type of error
            severity: Severity level
            
        Returns:
            List of applicable recovery procedures
        """
        try:
            type_procedures = self.procedures.get(error_type, {})
            severity_procedures = type_procedures.get(severity, [])
            
            # If no procedures for exact severity, try lower severity levels
            if not severity_procedures:
                severity_order = [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH, ErrorSeverity.MEDIUM, ErrorSeverity.LOW]
                current_index = severity_order.index(severity) if severity in severity_order else 0
                
                for i in range(current_index + 1, len(severity_order)):
                    fallback_severity = severity_order[i]
                    severity_procedures = type_procedures.get(fallback_severity, [])
                    if severity_procedures:
                        self.logger.info(f"Using {fallback_severity.value} procedures for {severity.value} error")
                        break
            
            return severity_procedures
            
        except Exception as e:
            self.logger.error(f"Error getting procedures for {error_type.value}/{severity.value}: {e}")
            return []
    
    async def add_procedure(self, error_type: ErrorType, severity: ErrorSeverity,
                          procedure: Dict[str, Any]) -> bool:
        """
        Add a new recovery procedure.
        
        Args:
            error_type: Type of error this procedure handles
            severity: Severity level this procedure handles
            procedure: Procedure definition
            
        Returns:
            True if procedure was added successfully
        """
        try:
            if error_type not in self.procedures:
                self.procedures[error_type] = {}
            
            if severity not in self.procedures[error_type]:
                self.procedures[error_type][severity] = []
            
            # Validate procedure structure
            if not self._validate_procedure(procedure):
                return False
            
            self.procedures[error_type][severity].append(procedure)
            
            self.logger.info(f"Added procedure '{procedure.get('name')}' for {error_type.value}/{severity.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding procedure: {e}")
            return False
    
    async def update_procedure_success_rate(self, error_type: ErrorType, 
                                          severity: ErrorSeverity,
                                          procedure_name: str,
                                          success_rate: float) -> bool:
        """
        Update the success rate of a procedure based on execution results.
        
        Args:
            error_type: Type of error
            severity: Severity level
            procedure_name: Name of the procedure
            success_rate: New success rate (0.0 to 1.0)
            
        Returns:
            True if update was successful
        """
        try:
            type_procedures = self.procedures.get(error_type, {})
            severity_procedures = type_procedures.get(severity, [])
            
            for procedure in severity_procedures:
                if procedure.get("name") == procedure_name:
                    old_rate = procedure.get("success_rate", 0.0)
                    procedure["success_rate"] = success_rate
                    
                    self.logger.info(f"Updated success rate for '{procedure_name}': {old_rate:.2f} -> {success_rate:.2f}")
                    return True
            
            self.logger.warning(f"Procedure '{procedure_name}' not found for {error_type.value}/{severity.value}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating procedure success rate: {e}")
            return False
    
    def get_all_procedures(self) -> Dict[ErrorType, Dict[ErrorSeverity, List[Dict[str, Any]]]]:
        """Get all registered procedures."""
        return self.procedures.copy()
    
    def _validate_procedure(self, procedure: Dict[str, Any]) -> bool:
        """Validate procedure structure."""
        required_fields = ["name", "description", "steps"]
        
        for field in required_fields:
            if field not in procedure:
                self.logger.error(f"Procedure missing required field: {field}")
                return False
        
        # Validate steps
        steps = procedure.get("steps", [])
        if not isinstance(steps, list) or not steps:
            self.logger.error("Procedure must have at least one step")
            return False
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                self.logger.error(f"Step {i} must be a dictionary")
                return False
            
            if "type" not in step or "description" not in step:
                self.logger.error(f"Step {i} missing required fields (type, description)")
                return False
        
        return True

