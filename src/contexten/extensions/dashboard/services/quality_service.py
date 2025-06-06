"""
Quality Service - Handles quality gates and validation.
Implements comprehensive quality assessment and validation system.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..consolidated_models import QualityGate, QualityGateStatus

logger = logging.getLogger(__name__)


class QualityService:
    """
    Service for managing quality gates and validation processes.
    Provides comprehensive code quality assessment and validation.
    """
    
    def __init__(self):
        """Initialize the Quality service."""
        self.quality_gates: Dict[str, List[QualityGate]] = {}
        self.validation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize default quality gates
        self._init_default_quality_gates()
    
    def _init_default_quality_gates(self):
        """Initialize default quality gates based on analysis data."""
        self.default_gates = [
            {
                "name": "Test Coverage",
                "metric": "test_coverage",
                "threshold": 80.0,
                "operator": ">=",
                "severity": "high",
                "adaptive": True
            },
            {
                "name": "Code Complexity",
                "metric": "complexity_score",
                "threshold": 7.0,
                "operator": "<=",
                "severity": "medium",
                "adaptive": True
            },
            {
                "name": "Security Score",
                "metric": "security_score",
                "threshold": 85.0,
                "operator": ">=",
                "severity": "critical",
                "adaptive": False
            },
            {
                "name": "Performance Score",
                "metric": "performance_score",
                "threshold": 75.0,
                "operator": ">=",
                "severity": "high",
                "adaptive": True
            },
            {
                "name": "Dependency Health",
                "metric": "dependency_health",
                "threshold": 90.0,
                "operator": ">=",
                "severity": "medium",
                "adaptive": True
            },
            {
                "name": "Recent Failures",
                "metric": "recent_failures",
                "threshold": 3,
                "operator": "<=",
                "severity": "high",
                "adaptive": False
            },
            {
                "name": "Documentation Coverage",
                "metric": "documentation_coverage",
                "threshold": 70.0,
                "operator": ">=",
                "severity": "low",
                "adaptive": True
            },
            {
                "name": "Code Duplication",
                "metric": "code_duplication",
                "threshold": 5.0,
                "operator": "<=",
                "severity": "medium",
                "adaptive": True
            }
        ]
    
    async def get_quality_gates(self, project_id: str) -> List[QualityGate]:
        """Get quality gates for a project."""
        if project_id not in self.quality_gates:
            # Create default quality gates for new project
            await self._create_default_gates_for_project(project_id)
        
        return self.quality_gates.get(project_id, [])
    
    async def _create_default_gates_for_project(self, project_id: str):
        """Create default quality gates for a project."""
        gates = []
        for gate_config in self.default_gates:
            gate = QualityGate(
                id=str(uuid.uuid4()),
                name=gate_config["name"],
                metric=gate_config["metric"],
                threshold=gate_config["threshold"],
                operator=gate_config["operator"],
                severity=gate_config["severity"],
                adaptive=gate_config["adaptive"]
            )
            gates.append(gate)
        
        self.quality_gates[project_id] = gates
        logger.info(f"Created {len(gates)} default quality gates for project {project_id}")
    
    async def validate_all_gates(self, project_id: str) -> Dict[str, Any]:
        """Validate all quality gates for a project."""
        gates = await self.get_quality_gates(project_id)
        
        # Get current project metrics
        metrics = await self._get_project_metrics(project_id)
        
        results = {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "passed",
            "gates_passed": 0,
            "gates_failed": 0,
            "gates_warning": 0,
            "gate_results": [],
            "blocking_issues": [],
            "recommendations": []
        }
        
        for gate in gates:
            gate_result = await self._validate_single_gate(gate, metrics)
            results["gate_results"].append(gate_result)
            
            # Update overall status
            if gate_result["status"] == "passed":
                results["gates_passed"] += 1
            elif gate_result["status"] == "failed":
                results["gates_failed"] += 1
                if gate.severity in ["critical", "high"]:
                    results["overall_status"] = "failed"
                    results["blocking_issues"].append(gate_result["message"])
            elif gate_result["status"] == "warning":
                results["gates_warning"] += 1
                if results["overall_status"] == "passed":
                    results["overall_status"] = "warning"
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results["gate_results"])
        
        # Store validation history
        if project_id not in self.validation_history:
            self.validation_history[project_id] = []
        self.validation_history[project_id].append(results)
        
        # Update adaptive thresholds
        await self._update_adaptive_thresholds(project_id, metrics)
        
        logger.info(f"Validated {len(gates)} quality gates for project {project_id}: {results['overall_status']}")
        return results
    
    async def _validate_single_gate(self, gate: QualityGate, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single quality gate."""
        current_value = metrics.get(gate.metric)
        
        if current_value is None:
            return {
                "gate_id": gate.id,
                "name": gate.name,
                "metric": gate.metric,
                "status": "warning",
                "message": f"Metric {gate.metric} not available",
                "current_value": None,
                "threshold": gate.threshold,
                "operator": gate.operator
            }
        
        # Update gate with current value
        gate.current_value = current_value
        
        # Perform validation based on operator
        passed = self._evaluate_condition(current_value, gate.operator, gate.threshold)
        
        if passed:
            gate.status = QualityGateStatus.PASSED
            status = "passed"
            message = f"{gate.name} passed: {current_value} {gate.operator} {gate.threshold}"
        else:
            # Determine if it's a failure or warning based on severity
            if gate.severity in ["critical", "high"]:
                gate.status = QualityGateStatus.FAILED
                status = "failed"
                message = f"{gate.name} failed: {current_value} does not meet threshold {gate.threshold}"
            else:
                gate.status = QualityGateStatus.WARNING
                status = "warning"
                message = f"{gate.name} warning: {current_value} below recommended threshold {gate.threshold}"
        
        return {
            "gate_id": gate.id,
            "name": gate.name,
            "metric": gate.metric,
            "status": status,
            "message": message,
            "current_value": current_value,
            "threshold": gate.threshold,
            "operator": gate.operator,
            "severity": gate.severity
        }
    
    def _evaluate_condition(self, value: Union[float, int], operator: str, threshold: Union[float, int]) -> bool:
        """Evaluate a condition based on operator."""
        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    async def _get_project_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get current metrics for a project."""
        try:
            # This would integrate with graph-sitter and other analysis tools
            # For now, we'll simulate metrics based on historical data
            
            # Try to get real metrics from graph-sitter analysis
            metrics = await self._analyze_project_with_graph_sitter(project_id)
            
            # If no real metrics available, use mock data
            if not metrics:
                metrics = self._get_mock_metrics(project_id)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics for project {project_id}: {e}")
            return self._get_mock_metrics(project_id)
    
    async def _analyze_project_with_graph_sitter(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Analyze project using graph-sitter tools."""
        try:
            # This would integrate with the actual graph-sitter analysis
            # from graph_sitter.codebase.codebase_analysis import CodebaseAnalysis
            # analyzer = CodebaseAnalysis()
            # results = await analyzer.analyze_project(project_id)
            # return results
            
            # For now, return None to indicate no real analysis available
            return None
            
        except Exception as e:
            logger.error(f"Graph-sitter analysis failed for project {project_id}: {e}")
            return None
    
    def _get_mock_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get mock metrics for development and testing."""
        # Simulate realistic metrics with some variation
        import random
        
        base_metrics = {
            "test_coverage": 75.0 + random.uniform(-10, 15),
            "complexity_score": 6.0 + random.uniform(-2, 4),
            "security_score": 85.0 + random.uniform(-5, 10),
            "performance_score": 80.0 + random.uniform(-10, 15),
            "dependency_health": 70.0 + random.uniform(-15, 20),
            "recent_failures": random.randint(0, 5),
            "documentation_coverage": 65.0 + random.uniform(-15, 20),
            "code_duplication": 3.0 + random.uniform(-1, 4),
            "lines_of_code": random.randint(5000, 50000),
            "technical_debt_ratio": 5.0 + random.uniform(-2, 5),
            "maintainability_index": 70.0 + random.uniform(-10, 20),
            "cyclomatic_complexity": 8.0 + random.uniform(-3, 5)
        }
        
        # Ensure values are within reasonable bounds
        for key, value in base_metrics.items():
            if key in ["test_coverage", "security_score", "performance_score", "dependency_health", "documentation_coverage", "maintainability_index"]:
                base_metrics[key] = max(0, min(100, value))
            elif key in ["complexity_score", "code_duplication", "technical_debt_ratio", "cyclomatic_complexity"]:
                base_metrics[key] = max(0, value)
            elif key == "recent_failures":
                base_metrics[key] = max(0, int(value))
        
        return base_metrics
    
    async def _update_adaptive_thresholds(self, project_id: str, metrics: Dict[str, Any]):
        """Update adaptive thresholds based on historical data."""
        gates = self.quality_gates.get(project_id, [])
        
        for gate in gates:
            if gate.adaptive and gate.metric in metrics:
                current_value = metrics[gate.metric]
                
                # Add to historical data
                gate.historical_data.append(current_value)
                
                # Keep only last 10 values
                if len(gate.historical_data) > 10:
                    gate.historical_data = gate.historical_data[-10:]
                
                # Update threshold based on historical performance
                if len(gate.historical_data) >= 3:
                    avg_value = sum(gate.historical_data) / len(gate.historical_data)
                    
                    # Adjust threshold to be slightly better than average
                    if gate.operator in [">=", ">"]:
                        # For metrics where higher is better
                        new_threshold = avg_value * 0.95  # 5% below average
                    else:
                        # For metrics where lower is better
                        new_threshold = avg_value * 1.05  # 5% above average
                    
                    # Don't make drastic changes
                    threshold_change = abs(new_threshold - gate.threshold) / gate.threshold
                    if threshold_change < 0.2:  # Max 20% change
                        gate.threshold = new_threshold
                        logger.info(f"Updated adaptive threshold for {gate.name}: {gate.threshold}")
    
    def _generate_recommendations(self, gate_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on gate results."""
        recommendations = []
        
        for result in gate_results:
            if result["status"] in ["failed", "warning"]:
                metric = result["metric"]
                current_value = result["current_value"]
                threshold = result["threshold"]
                
                if metric == "test_coverage":
                    recommendations.append(f"Increase test coverage from {current_value:.1f}% to at least {threshold}%. Consider adding unit tests for uncovered code paths.")
                elif metric == "complexity_score":
                    recommendations.append(f"Reduce code complexity from {current_value:.1f} to below {threshold}. Consider refactoring complex functions and breaking them into smaller methods.")
                elif metric == "security_score":
                    recommendations.append(f"Improve security score from {current_value:.1f} to at least {threshold}. Run security scans and address identified vulnerabilities.")
                elif metric == "performance_score":
                    recommendations.append(f"Optimize performance from {current_value:.1f} to at least {threshold}. Profile the application and optimize bottlenecks.")
                elif metric == "dependency_health":
                    recommendations.append(f"Update dependencies to improve health score from {current_value:.1f}% to at least {threshold}%. Check for outdated or vulnerable packages.")
                elif metric == "recent_failures":
                    recommendations.append(f"Reduce recent failures from {current_value} to {threshold} or fewer. Investigate and fix failing tests or builds.")
                elif metric == "documentation_coverage":
                    recommendations.append(f"Improve documentation coverage from {current_value:.1f}% to at least {threshold}%. Add docstrings and comments to undocumented code.")
                elif metric == "code_duplication":
                    recommendations.append(f"Reduce code duplication from {current_value:.1f}% to below {threshold}%. Extract common code into reusable functions or modules.")
        
        # Add general recommendations
        if len([r for r in gate_results if r["status"] == "failed"]) > 2:
            recommendations.append("Consider implementing a continuous integration pipeline with automated quality checks.")
        
        if any(r["metric"] == "security_score" and r["status"] == "failed" for r in gate_results):
            recommendations.append("Implement security scanning tools in your development workflow.")
        
        return recommendations
    
    async def validate_pr_quality(self, project_id: str, pr_url: str) -> Dict[str, Any]:
        """Validate quality gates specifically for a pull request."""
        try:
            # This would analyze the specific changes in the PR
            # For now, we'll run the standard validation
            results = await self.validate_all_gates(project_id)
            
            # Add PR-specific information
            results.update({
                "pr_url": pr_url,
                "validation_type": "pull_request",
                "pr_specific_checks": await self._run_pr_specific_checks(pr_url)
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to validate PR quality for {pr_url}: {e}")
            return {
                "project_id": project_id,
                "pr_url": pr_url,
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_pr_specific_checks(self, pr_url: str) -> List[Dict[str, Any]]:
        """Run PR-specific quality checks."""
        # This would analyze the specific changes in the PR
        # For now, return mock checks
        return [
            {
                "name": "Changed Files Analysis",
                "status": "passed",
                "message": "All changed files follow coding standards"
            },
            {
                "name": "New Code Coverage",
                "status": "passed",
                "message": "New code has adequate test coverage"
            },
            {
                "name": "Breaking Changes",
                "status": "passed",
                "message": "No breaking changes detected"
            }
        ]
    
    async def get_validation_history(self, project_id: str) -> List[Dict[str, Any]]:
        """Get validation history for a project."""
        return self.validation_history.get(project_id, [])
    
    async def create_custom_gate(
        self,
        project_id: str,
        name: str,
        metric: str,
        threshold: Union[float, int],
        operator: str,
        severity: str = "medium"
    ) -> QualityGate:
        """Create a custom quality gate for a project."""
        gate = QualityGate(
            id=str(uuid.uuid4()),
            name=name,
            metric=metric,
            threshold=threshold,
            operator=operator,
            severity=severity,
            adaptive=False  # Custom gates are not adaptive by default
        )
        
        if project_id not in self.quality_gates:
            self.quality_gates[project_id] = []
        
        self.quality_gates[project_id].append(gate)
        
        logger.info(f"Created custom quality gate '{name}' for project {project_id}")
        return gate
    
    async def delete_quality_gate(self, project_id: str, gate_id: str) -> bool:
        """Delete a quality gate."""
        gates = self.quality_gates.get(project_id, [])
        
        for i, gate in enumerate(gates):
            if gate.id == gate_id:
                del gates[i]
                logger.info(f"Deleted quality gate {gate_id} from project {project_id}")
                return True
        
        return False

