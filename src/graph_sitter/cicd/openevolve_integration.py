"""
OpenEvolve Integration for Graph-Sitter CI/CD

Provides continuous learning and system evolution through:
- Evaluation submission and tracking
- Pattern analysis and learning
- System improvement recommendations
- Performance optimization
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class EvaluationStatus(Enum):
    """OpenEvolve evaluation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class EvaluationType(Enum):
    """Types of evaluations"""
    CODE_ANALYSIS = "code_analysis"
    TASK_OPTIMIZATION = "task_optimization"
    ERROR_RESOLUTION = "error_resolution"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    SYSTEM_HEALTH = "system_health"


@dataclass
class Evaluation:
    """OpenEvolve evaluation definition and tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    evaluation_id: str = ""  # OpenEvolve evaluation ID
    
    # Evaluation definition
    target_type: str = ""  # task, pipeline, system, codebase
    target_id: str = ""
    evaluation_type: EvaluationType = EvaluationType.CODE_ANALYSIS
    
    # Configuration
    configuration: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    status: EvaluationStatus = EvaluationStatus.PENDING
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Results
    effectiveness_score: Optional[float] = None  # 0-100 score
    improvement_metrics: Dict[str, Any] = field(default_factory=dict)
    generated_solutions: List[Dict[str, Any]] = field(default_factory=list)
    selected_solution: Dict[str, Any] = field(default_factory=dict)
    
    # Context and learning
    context_data: Dict[str, Any] = field(default_factory=dict)
    learning_insights: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def start_evaluation(self) -> None:
        """Mark evaluation as started"""
        self.status = EvaluationStatus.IN_PROGRESS
        self.submitted_at = datetime.now(timezone.utc)
    
    def complete_evaluation(self, results: Dict[str, Any]) -> None:
        """Mark evaluation as completed with results"""
        self.status = EvaluationStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        
        if self.submitted_at:
            self.duration_ms = int((self.completed_at - self.submitted_at).total_seconds() * 1000)
        
        # Extract results
        self.effectiveness_score = results.get("effectiveness_score")
        self.improvement_metrics = results.get("improvement_metrics", {})
        self.generated_solutions = results.get("generated_solutions", [])
        self.selected_solution = results.get("selected_solution", {})
        self.learning_insights = results.get("learning_insights", {})
    
    def fail_evaluation(self, error_message: str, error_details: Dict[str, Any] = None) -> None:
        """Mark evaluation as failed"""
        self.status = EvaluationStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message
        self.error_details = error_details or {}


@dataclass
class LearningPattern:
    """Learned pattern from system analysis"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    
    # Pattern identification
    pattern_type: str = ""  # successful_implementation, error_resolution, optimization_strategy
    pattern_name: str = ""
    pattern_description: str = ""
    
    # Pattern data
    pattern_signature: Dict[str, Any] = field(default_factory=dict)
    pattern_context: Dict[str, Any] = field(default_factory=dict)
    success_indicators: Dict[str, Any] = field(default_factory=dict)
    
    # Effectiveness metrics
    usage_count: int = 0
    success_rate: float = 0.0
    effectiveness_score: Optional[float] = None
    confidence_level: float = 0.0
    
    # Pattern evolution
    version: int = 1
    parent_pattern_id: Optional[str] = None
    evolution_notes: str = ""
    
    # Application scope
    applicable_contexts: List[Dict[str, Any]] = field(default_factory=list)
    exclusion_criteria: List[Dict[str, Any]] = field(default_factory=list)
    
    # Lifecycle
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_applied_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None
    is_active: bool = True
    is_validated: bool = False
    validation_notes: str = ""
    
    def apply_pattern(self, success: bool) -> None:
        """Record pattern application and update metrics"""
        self.usage_count += 1
        self.last_applied_at = datetime.now(timezone.utc)
        
        # Update success rate
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            current_successes = self.success_rate * (self.usage_count - 1)
            if success:
                current_successes += 1
            self.success_rate = current_successes / self.usage_count


class OpenEvolveClient:
    """
    OpenEvolve integration client for continuous learning and system evolution
    """
    
    def __init__(self, organization_id: str, api_url: str = "", api_key: str = "", database_connection=None):
        self.organization_id = organization_id
        self.api_url = api_url or "https://api.openevolve.com"
        self.api_key = api_key
        self.db = database_connection
        
        # Configuration
        self.timeout_ms = 30000
        self.max_retries = 3
        self.evaluation_triggers = [
            "task_failure",
            "pipeline_failure", 
            "performance_degradation",
            "error_pattern_detected"
        ]
        
        # In-memory storage (would be replaced with database in production)
        self.evaluations: Dict[str, Evaluation] = {}
        self.learning_patterns: Dict[str, LearningPattern] = {}
        
        # Performance tracking
        self.metrics = {
            "total_evaluations": 0,
            "successful_evaluations": 0,
            "failed_evaluations": 0,
            "avg_evaluation_time_ms": 0.0,
            "total_improvements_identified": 0,
            "patterns_discovered": 0
        }
    
    async def submit_evaluation(self, evaluation: Evaluation) -> str:
        """Submit an evaluation to OpenEvolve"""
        evaluation.organization_id = self.organization_id
        self.evaluations[evaluation.id] = evaluation
        
        # Start evaluation
        evaluation.start_evaluation()
        logger.info(f"Submitting evaluation {evaluation.id} to OpenEvolve")
        
        try:
            # Submit to OpenEvolve API (mock implementation)
            openevolve_id = await self._submit_to_openevolve_api(evaluation)
            evaluation.evaluation_id = openevolve_id
            
            # Store in database
            if self.db:
                await self._store_evaluation_in_db(evaluation)
            
            self.metrics["total_evaluations"] += 1
            logger.info(f"Evaluation {evaluation.id} submitted with OpenEvolve ID: {openevolve_id}")
            
        except Exception as e:
            evaluation.fail_evaluation(str(e))
            self.metrics["failed_evaluations"] += 1
            logger.error(f"Failed to submit evaluation {evaluation.id}: {e}")
            raise
        
        return evaluation.id
    
    async def get_evaluation_result(self, evaluation_id: str) -> Optional[Evaluation]:
        """Get evaluation results from OpenEvolve"""
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            return None
        
        if evaluation.status == EvaluationStatus.COMPLETED:
            return evaluation
        
        try:
            # Check status with OpenEvolve API (mock implementation)
            results = await self._get_results_from_openevolve_api(evaluation.evaluation_id)
            
            if results:
                evaluation.complete_evaluation(results)
                self.metrics["successful_evaluations"] += 1
                
                # Update average evaluation time
                if evaluation.duration_ms:
                    total_evals = self.metrics["successful_evaluations"]
                    current_avg = self.metrics["avg_evaluation_time_ms"]
                    self.metrics["avg_evaluation_time_ms"] = (
                        (current_avg * (total_evals - 1) + evaluation.duration_ms) / total_evals
                    )
                
                # Process learning insights
                await self._process_learning_insights(evaluation)
                
                logger.info(f"Evaluation {evaluation_id} completed with score: {evaluation.effectiveness_score}")
            
        except Exception as e:
            evaluation.fail_evaluation(str(e))
            self.metrics["failed_evaluations"] += 1
            logger.error(f"Failed to get evaluation results for {evaluation_id}: {e}")
        
        return evaluation
    
    async def trigger_evaluation(self, trigger_event: str, context: Dict[str, Any]) -> Optional[str]:
        """Trigger an evaluation based on system events"""
        if trigger_event not in self.evaluation_triggers:
            logger.debug(f"Trigger event '{trigger_event}' not configured for evaluation")
            return None
        
        # Determine evaluation type based on trigger
        evaluation_type = self._get_evaluation_type_for_trigger(trigger_event)
        
        # Create evaluation
        evaluation = Evaluation(
            target_type=context.get("target_type", "system"),
            target_id=context.get("target_id", ""),
            evaluation_type=evaluation_type,
            context_data=context,
            configuration=self._get_evaluation_config(evaluation_type)
        )
        
        # Submit evaluation
        return await self.submit_evaluation(evaluation)
    
    async def discover_patterns(self, data_source: str, time_range_days: int = 30) -> List[LearningPattern]:
        """Discover patterns from system data"""
        logger.info(f"Discovering patterns from {data_source} over {time_range_days} days")
        
        # Mock pattern discovery (in real implementation, would analyze actual data)
        discovered_patterns = []
        
        # Example patterns that might be discovered
        pattern_templates = [
            {
                "pattern_type": "successful_implementation",
                "pattern_name": "High Success Rate Task Pattern",
                "pattern_description": "Tasks with specific characteristics show high success rates",
                "pattern_signature": {
                    "task_type": "feature",
                    "estimated_hours": {"min": 2, "max": 8},
                    "dependencies_count": {"max": 3}
                },
                "success_indicators": {"success_rate": 0.95, "avg_completion_time": 4.2}
            },
            {
                "pattern_type": "error_resolution",
                "pattern_name": "Common Error Recovery Pattern",
                "pattern_description": "Effective recovery strategy for deployment failures",
                "pattern_signature": {
                    "error_type": "deployment_failure",
                    "recovery_action": "rollback_and_retry"
                },
                "success_indicators": {"recovery_success_rate": 0.87, "avg_recovery_time": 120}
            }
        ]
        
        for template in pattern_templates:
            pattern = LearningPattern(
                organization_id=self.organization_id,
                **template
            )
            pattern.confidence_level = 0.8  # Mock confidence
            discovered_patterns.append(pattern)
            self.learning_patterns[pattern.id] = pattern
        
        self.metrics["patterns_discovered"] += len(discovered_patterns)
        logger.info(f"Discovered {len(discovered_patterns)} new patterns")
        
        return discovered_patterns
    
    async def apply_pattern(self, pattern_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a learned pattern to a specific context"""
        pattern = self.learning_patterns.get(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        
        if not pattern.is_active:
            raise ValueError(f"Pattern {pattern_id} is not active")
        
        logger.info(f"Applying pattern {pattern.pattern_name} to context")
        
        # Check if pattern is applicable to context
        if not self._is_pattern_applicable(pattern, context):
            return {
                "applied": False,
                "reason": "Pattern not applicable to current context",
                "pattern_id": pattern_id
            }
        
        # Apply pattern (mock implementation)
        await asyncio.sleep(0.1)  # Simulate pattern application
        
        # Record application
        success = True  # Mock success
        pattern.apply_pattern(success)
        
        return {
            "applied": True,
            "success": success,
            "pattern_id": pattern_id,
            "pattern_name": pattern.pattern_name,
            "application_result": {
                "improvements": ["Reduced execution time by 15%", "Improved success rate"],
                "metrics": {"time_saved": 0.15, "success_rate_improvement": 0.05}
            }
        }
    
    async def get_system_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Get system improvement recommendations based on evaluations and patterns"""
        recommendations = []
        
        # Analyze recent evaluations
        recent_evaluations = [
            e for e in self.evaluations.values()
            if e.status == EvaluationStatus.COMPLETED and e.effectiveness_score is not None
        ]
        
        if recent_evaluations:
            avg_effectiveness = sum(e.effectiveness_score for e in recent_evaluations) / len(recent_evaluations)
            
            if avg_effectiveness < 70:  # Below 70% effectiveness
                recommendations.append({
                    "type": "system_optimization",
                    "priority": "high",
                    "title": "System Performance Below Target",
                    "description": f"Average effectiveness score is {avg_effectiveness:.1f}%, below target of 70%",
                    "suggested_actions": [
                        "Review and optimize task configurations",
                        "Analyze failed evaluations for common patterns",
                        "Consider updating system parameters"
                    ],
                    "expected_impact": "15-25% improvement in system effectiveness"
                })
        
        # Analyze patterns for optimization opportunities
        high_success_patterns = [
            p for p in self.learning_patterns.values()
            if p.success_rate > 0.9 and p.usage_count > 5
        ]
        
        if high_success_patterns:
            recommendations.append({
                "type": "pattern_adoption",
                "priority": "medium",
                "title": "High-Success Patterns Available",
                "description": f"Found {len(high_success_patterns)} patterns with >90% success rate",
                "suggested_actions": [
                    "Apply high-success patterns to similar contexts",
                    "Create templates based on successful patterns",
                    "Train team on effective patterns"
                ],
                "expected_impact": "10-20% improvement in task success rates"
            })
        
        # Check for underutilized capabilities
        if self.metrics["total_evaluations"] < 10:
            recommendations.append({
                "type": "capability_utilization",
                "priority": "low",
                "title": "Increase Evaluation Usage",
                "description": "System evaluation capabilities are underutilized",
                "suggested_actions": [
                    "Configure more evaluation triggers",
                    "Enable automatic evaluation for critical processes",
                    "Set up regular system health evaluations"
                ],
                "expected_impact": "Better system visibility and optimization opportunities"
            })
        
        return recommendations
    
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get comprehensive learning and improvement metrics"""
        active_patterns = [p for p in self.learning_patterns.values() if p.is_active]
        validated_patterns = [p for p in active_patterns if p.is_validated]
        
        # Calculate pattern effectiveness
        pattern_effectiveness = 0.0
        if active_patterns:
            total_effectiveness = sum(p.effectiveness_score or 0 for p in active_patterns)
            pattern_effectiveness = total_effectiveness / len(active_patterns)
        
        return {
            "evaluation_metrics": self.metrics.copy(),
            "pattern_metrics": {
                "total_patterns": len(self.learning_patterns),
                "active_patterns": len(active_patterns),
                "validated_patterns": len(validated_patterns),
                "avg_pattern_effectiveness": pattern_effectiveness,
                "avg_pattern_success_rate": sum(p.success_rate for p in active_patterns) / len(active_patterns) if active_patterns else 0
            },
            "improvement_metrics": {
                "total_improvements_identified": self.metrics["total_improvements_identified"],
                "avg_evaluation_effectiveness": self.metrics.get("avg_effectiveness_score", 0),
                "system_learning_rate": len(active_patterns) / max(1, self.metrics["total_evaluations"])
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_evaluation_type_for_trigger(self, trigger_event: str) -> EvaluationType:
        """Map trigger events to evaluation types"""
        mapping = {
            "task_failure": EvaluationType.TASK_OPTIMIZATION,
            "pipeline_failure": EvaluationType.WORKFLOW_OPTIMIZATION,
            "performance_degradation": EvaluationType.PERFORMANCE_IMPROVEMENT,
            "error_pattern_detected": EvaluationType.ERROR_RESOLUTION
        }
        return mapping.get(trigger_event, EvaluationType.SYSTEM_HEALTH)
    
    def _get_evaluation_config(self, evaluation_type: EvaluationType) -> Dict[str, Any]:
        """Get configuration for evaluation type"""
        configs = {
            EvaluationType.CODE_ANALYSIS: {
                "analysis_depth": "comprehensive",
                "include_security": True,
                "include_performance": True
            },
            EvaluationType.TASK_OPTIMIZATION: {
                "optimization_targets": ["execution_time", "success_rate", "resource_usage"],
                "include_dependencies": True
            },
            EvaluationType.ERROR_RESOLUTION: {
                "include_root_cause": True,
                "suggest_prevention": True,
                "analyze_patterns": True
            }
        }
        return configs.get(evaluation_type, {})
    
    def _is_pattern_applicable(self, pattern: LearningPattern, context: Dict[str, Any]) -> bool:
        """Check if a pattern is applicable to the given context"""
        # Simple applicability check (can be made more sophisticated)
        if not pattern.applicable_contexts:
            return True
        
        for applicable_context in pattern.applicable_contexts:
            if all(context.get(key) == value for key, value in applicable_context.items()):
                return True
        
        return False
    
    async def _submit_to_openevolve_api(self, evaluation: Evaluation) -> str:
        """Submit evaluation to OpenEvolve API (mock implementation)"""
        # Mock API call
        await asyncio.sleep(0.2)
        return f"oe_{uuid.uuid4().hex[:8]}"
    
    async def _get_results_from_openevolve_api(self, openevolve_id: str) -> Optional[Dict[str, Any]]:
        """Get results from OpenEvolve API (mock implementation)"""
        # Mock API call
        await asyncio.sleep(0.1)
        
        # Mock results
        return {
            "effectiveness_score": 75.5,
            "improvement_metrics": {
                "performance_improvement": 0.15,
                "error_reduction": 0.25,
                "efficiency_gain": 0.10
            },
            "generated_solutions": [
                {
                    "solution_id": "sol_001",
                    "description": "Optimize task scheduling algorithm",
                    "impact_score": 0.8,
                    "implementation_effort": "medium"
                }
            ],
            "selected_solution": {
                "solution_id": "sol_001",
                "confidence": 0.85
            },
            "learning_insights": {
                "patterns_identified": 2,
                "optimization_opportunities": 3,
                "risk_factors": 1
            }
        }
    
    async def _process_learning_insights(self, evaluation: Evaluation) -> None:
        """Process learning insights from evaluation results"""
        insights = evaluation.learning_insights
        
        # Extract patterns from insights
        patterns_identified = insights.get("patterns_identified", 0)
        if patterns_identified > 0:
            # Create learning patterns based on insights (simplified)
            for i in range(patterns_identified):
                pattern = LearningPattern(
                    organization_id=self.organization_id,
                    pattern_type="evaluation_insight",
                    pattern_name=f"Pattern from evaluation {evaluation.id}",
                    pattern_description="Pattern discovered through OpenEvolve evaluation",
                    pattern_signature={"evaluation_id": evaluation.id},
                    effectiveness_score=evaluation.effectiveness_score,
                    confidence_level=0.7
                )
                self.learning_patterns[pattern.id] = pattern
        
        # Update improvement metrics
        improvements = insights.get("optimization_opportunities", 0)
        self.metrics["total_improvements_identified"] += improvements
    
    async def _store_evaluation_in_db(self, evaluation: Evaluation) -> None:
        """Store evaluation in database"""
        # Implementation would depend on database connection
        pass


class EvaluationEngine:
    """
    High-level evaluation engine that orchestrates OpenEvolve evaluations
    """
    
    def __init__(self, openevolve_client: OpenEvolveClient):
        self.client = openevolve_client
        self.evaluation_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
    
    async def start(self) -> None:
        """Start the evaluation engine"""
        self.running = True
        asyncio.create_task(self._process_evaluation_queue())
        logger.info("Evaluation engine started")
    
    async def stop(self) -> None:
        """Stop the evaluation engine"""
        self.running = False
        logger.info("Evaluation engine stopped")
    
    async def queue_evaluation(self, evaluation: Evaluation) -> None:
        """Queue an evaluation for processing"""
        await self.evaluation_queue.put(evaluation)
    
    async def _process_evaluation_queue(self) -> None:
        """Process queued evaluations"""
        while self.running:
            try:
                # Wait for evaluation with timeout
                evaluation = await asyncio.wait_for(
                    self.evaluation_queue.get(),
                    timeout=1.0
                )
                
                # Submit evaluation
                await self.client.submit_evaluation(evaluation)
                
                # Mark task as done
                self.evaluation_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing evaluation: {e}")


# Utility functions
def create_evaluation_from_dict(data: Dict[str, Any]) -> Evaluation:
    """Create an Evaluation object from dictionary data"""
    evaluation = Evaluation()
    for key, value in data.items():
        if key == "evaluation_type" and isinstance(value, str):
            evaluation.evaluation_type = EvaluationType(value)
        elif key == "status" and isinstance(value, str):
            evaluation.status = EvaluationStatus(value)
        elif hasattr(evaluation, key):
            setattr(evaluation, key, value)
    return evaluation

