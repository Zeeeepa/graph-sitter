"""
Adaptation Engine

This module implements the adaptation engine that uses pattern recognition
and performance data to automatically improve system behavior and configuration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import math

from .pattern_recognition import PatternRecognitionEngine, Pattern, PatternType
from .performance_tracker import PerformanceTracker, MetricType

logger = logging.getLogger(__name__)


class AdaptationType(Enum):
    """Types of adaptations the engine can make."""
    CONFIGURATION_CHANGE = "configuration_change"
    RESOURCE_SCALING = "resource_scaling"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    ERROR_PREVENTION = "error_prevention"
    PERFORMANCE_TUNING = "performance_tuning"
    SCHEDULING_ADJUSTMENT = "scheduling_adjustment"


@dataclass
class Adaptation:
    """Represents an adaptation made by the engine."""
    id: str
    adaptation_type: AdaptationType
    description: str
    trigger_pattern_id: Optional[str]
    configuration_changes: Dict[str, Any]
    expected_impact: str
    confidence_score: float
    applied_at: datetime
    effectiveness_score: Optional[float] = None
    measured_at: Optional[datetime] = None
    reverted: bool = False
    revert_reason: Optional[str] = None


@dataclass
class AdaptationRule:
    """Rule for making adaptations based on patterns."""
    id: str
    name: str
    pattern_types: List[PatternType]
    conditions: Dict[str, Any]
    adaptation_function: Callable
    min_confidence: float = 0.7
    cooldown_hours: int = 24
    enabled: bool = True


class AdaptationEngine:
    """
    Intelligent adaptation engine for continuous system improvement.
    
    This engine analyzes patterns and performance data to automatically
    make configuration changes, optimizations, and improvements to the system.
    """
    
    def __init__(self, 
                 pattern_engine: PatternRecognitionEngine,
                 performance_tracker: PerformanceTracker,
                 auto_adapt: bool = True):
        """
        Initialize the adaptation engine.
        
        Args:
            pattern_engine: Pattern recognition engine
            performance_tracker: Performance tracking system
            auto_adapt: Whether to automatically apply adaptations
        """
        self.pattern_engine = pattern_engine
        self.performance_tracker = performance_tracker
        self.auto_adapt = auto_adapt
        
        self.adaptations: List[Adaptation] = []
        self.adaptation_rules: Dict[str, AdaptationRule] = {}
        self.pending_adaptations: List[Adaptation] = []
        
        # Configuration state
        self.current_config: Dict[str, Any] = {}
        self.config_history: List[Dict[str, Any]] = []
        
        # Adaptation callbacks
        self.adaptation_callbacks: Dict[AdaptationType, List[Callable]] = {}
        
        # Setup default adaptation rules
        self._setup_default_rules()
        
        logger.info("Adaptation engine initialized")
    
    def _setup_default_rules(self):
        """Setup default adaptation rules."""
        # Task failure adaptation
        self.add_adaptation_rule(AdaptationRule(
            id="task_failure_timeout",
            name="Increase timeout for failing tasks",
            pattern_types=[PatternType.TASK_FAILURE],
            conditions={"error_type": "timeout"},
            adaptation_function=self._adapt_task_timeout,
            min_confidence=0.8
        ))
        
        # Performance degradation adaptation
        self.add_adaptation_rule(AdaptationRule(
            id="performance_scaling",
            name="Scale resources for performance issues",
            pattern_types=[PatternType.PERFORMANCE_DEGRADATION],
            conditions={"degradation_factor": 1.5},
            adaptation_function=self._adapt_resource_scaling,
            min_confidence=0.7
        ))
        
        # Resource usage adaptation
        self.add_adaptation_rule(AdaptationRule(
            id="resource_optimization",
            name="Optimize resource allocation",
            pattern_types=[PatternType.RESOURCE_USAGE],
            conditions={"high_usage_rate": 0.8},
            adaptation_function=self._adapt_resource_allocation,
            min_confidence=0.6
        ))
        
        # Workflow optimization adaptation
        self.add_adaptation_rule(AdaptationRule(
            id="workflow_parallelization",
            name="Parallelize slow workflow steps",
            pattern_types=[PatternType.WORKFLOW_OPTIMIZATION],
            conditions={"avg_duration": 180},  # 3 minutes
            adaptation_function=self._adapt_workflow_parallelization,
            min_confidence=0.7
        ))
        
        # Error correlation adaptation
        self.add_adaptation_rule(AdaptationRule(
            id="error_prevention",
            name="Prevent correlated errors",
            pattern_types=[PatternType.ERROR_CORRELATION],
            conditions={"correlation_strength": 0.7},
            adaptation_function=self._adapt_error_prevention,
            min_confidence=0.8
        ))
        
        # Timing pattern adaptation
        self.add_adaptation_rule(AdaptationRule(
            id="scheduling_optimization",
            name="Optimize task scheduling",
            pattern_types=[PatternType.TIMING_PATTERN],
            conditions={"performance_type": "worse"},
            adaptation_function=self._adapt_scheduling,
            min_confidence=0.6
        ))
    
    def add_adaptation_rule(self, rule: AdaptationRule):
        """Add an adaptation rule."""
        self.adaptation_rules[rule.id] = rule
        logger.info(f"Added adaptation rule: {rule.name}")
    
    def remove_adaptation_rule(self, rule_id: str) -> bool:
        """Remove an adaptation rule."""
        if rule_id in self.adaptation_rules:
            del self.adaptation_rules[rule_id]
            logger.info(f"Removed adaptation rule: {rule_id}")
            return True
        return False
    
    def add_adaptation_callback(self, adaptation_type: AdaptationType, callback: Callable):
        """Add a callback for when adaptations are applied."""
        if adaptation_type not in self.adaptation_callbacks:
            self.adaptation_callbacks[adaptation_type] = []
        self.adaptation_callbacks[adaptation_type].append(callback)
    
    async def analyze_and_adapt(self) -> List[Adaptation]:
        """
        Analyze patterns and create adaptations.
        
        Returns:
            List of adaptations that were created/applied
        """
        logger.info("Starting adaptation analysis...")
        
        # Get recognized patterns
        patterns = list(self.pattern_engine.recognized_patterns.values())
        
        adaptations_created = []
        
        # Process each pattern against adaptation rules
        for pattern in patterns:
            for rule in self.adaptation_rules.values():
                if not rule.enabled:
                    continue
                
                if pattern.pattern_type in rule.pattern_types:
                    if await self._should_apply_rule(pattern, rule):
                        adaptation = await self._create_adaptation(pattern, rule)
                        if adaptation:
                            adaptations_created.append(adaptation)
                            
                            if self.auto_adapt:
                                await self._apply_adaptation(adaptation)
                            else:
                                self.pending_adaptations.append(adaptation)
        
        logger.info(f"Created {len(adaptations_created)} adaptations")
        return adaptations_created
    
    async def _should_apply_rule(self, pattern: Pattern, rule: AdaptationRule) -> bool:
        """Check if a rule should be applied for a pattern."""
        # Check confidence threshold
        if pattern.confidence_score < rule.min_confidence:
            return False
        
        # Check cooldown period
        if await self._is_in_cooldown(rule):
            return False
        
        # Check rule conditions
        for condition_key, condition_value in rule.conditions.items():
            pattern_value = pattern.attributes.get(condition_key)
            
            if pattern_value is None:
                continue
            
            # Handle different condition types
            if isinstance(condition_value, (int, float)):
                if isinstance(pattern_value, (int, float)) and pattern_value < condition_value:
                    return False
            elif isinstance(condition_value, str):
                if pattern_value != condition_value:
                    return False
        
        return True
    
    async def _is_in_cooldown(self, rule: AdaptationRule) -> bool:
        """Check if a rule is in cooldown period."""
        cutoff_time = datetime.now() - timedelta(hours=rule.cooldown_hours)
        
        for adaptation in self.adaptations:
            if (adaptation.trigger_pattern_id and 
                adaptation.applied_at >= cutoff_time and
                any(rule.pattern_types)):
                return True
        
        return False
    
    async def _create_adaptation(self, pattern: Pattern, rule: AdaptationRule) -> Optional[Adaptation]:
        """Create an adaptation based on a pattern and rule."""
        try:
            # Call the adaptation function to get configuration changes
            config_changes = await rule.adaptation_function(pattern)
            
            if not config_changes:
                return None
            
            adaptation_id = f"{rule.id}_{pattern.id}_{int(datetime.now().timestamp())}"
            
            adaptation = Adaptation(
                id=adaptation_id,
                adaptation_type=self._get_adaptation_type_from_rule(rule),
                description=f"{rule.name} based on pattern: {pattern.description}",
                trigger_pattern_id=pattern.id,
                configuration_changes=config_changes,
                expected_impact=self._estimate_impact(pattern, config_changes),
                confidence_score=pattern.confidence_score,
                applied_at=datetime.now()
            )
            
            logger.info(f"Created adaptation: {adaptation.description}")
            return adaptation
            
        except Exception as e:
            logger.error(f"Error creating adaptation for rule {rule.id}: {e}")
            return None
    
    def _get_adaptation_type_from_rule(self, rule: AdaptationRule) -> AdaptationType:
        """Determine adaptation type from rule."""
        if "timeout" in rule.id or "scaling" in rule.id:
            return AdaptationType.CONFIGURATION_CHANGE
        elif "resource" in rule.id:
            return AdaptationType.RESOURCE_SCALING
        elif "workflow" in rule.id:
            return AdaptationType.WORKFLOW_OPTIMIZATION
        elif "error" in rule.id:
            return AdaptationType.ERROR_PREVENTION
        elif "scheduling" in rule.id:
            return AdaptationType.SCHEDULING_ADJUSTMENT
        else:
            return AdaptationType.PERFORMANCE_TUNING
    
    def _estimate_impact(self, pattern: Pattern, config_changes: Dict[str, Any]) -> str:
        """Estimate the expected impact of an adaptation."""
        impact_score = pattern.impact_score
        change_magnitude = len(config_changes)
        
        if impact_score > 0.7 and change_magnitude > 2:
            return "high"
        elif impact_score > 0.4 or change_magnitude > 1:
            return "medium"
        else:
            return "low"
    
    async def _apply_adaptation(self, adaptation: Adaptation):
        """Apply an adaptation to the system."""
        logger.info(f"Applying adaptation: {adaptation.description}")
        
        try:
            # Store current configuration
            self.config_history.append(self.current_config.copy())
            
            # Apply configuration changes
            for key, value in adaptation.configuration_changes.items():
                self.current_config[key] = value
            
            # Call adaptation callbacks
            callbacks = self.adaptation_callbacks.get(adaptation.adaptation_type, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(adaptation)
                    else:
                        callback(adaptation)
                except Exception as e:
                    logger.error(f"Error in adaptation callback: {e}")
            
            # Add to applied adaptations
            self.adaptations.append(adaptation)
            
            # Schedule effectiveness measurement
            asyncio.create_task(self._measure_effectiveness_later(adaptation))
            
            logger.info(f"Successfully applied adaptation: {adaptation.id}")
            
        except Exception as e:
            logger.error(f"Error applying adaptation {adaptation.id}: {e}")
            adaptation.reverted = True
            adaptation.revert_reason = str(e)
    
    async def _measure_effectiveness_later(self, adaptation: Adaptation, delay_hours: int = 2):
        """Measure adaptation effectiveness after a delay."""
        await asyncio.sleep(delay_hours * 3600)  # Wait for specified hours
        await self._measure_adaptation_effectiveness(adaptation)
    
    async def _measure_adaptation_effectiveness(self, adaptation: Adaptation):
        """Measure the effectiveness of an adaptation."""
        logger.info(f"Measuring effectiveness of adaptation: {adaptation.id}")
        
        try:
            # Get performance data before and after adaptation
            before_time = adaptation.applied_at - timedelta(hours=2)
            after_time = adaptation.applied_at + timedelta(hours=2)
            
            # This would integrate with actual performance measurement
            # For now, we'll simulate effectiveness measurement
            effectiveness_score = await self._calculate_effectiveness_score(adaptation, before_time, after_time)
            
            adaptation.effectiveness_score = effectiveness_score
            adaptation.measured_at = datetime.now()
            
            # If effectiveness is poor, consider reverting
            if effectiveness_score < 0.3:
                await self._consider_revert(adaptation)
            
            logger.info(f"Adaptation {adaptation.id} effectiveness: {effectiveness_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error measuring adaptation effectiveness: {e}")
    
    async def _calculate_effectiveness_score(self, 
                                           adaptation: Adaptation,
                                           before_time: datetime,
                                           after_time: datetime) -> float:
        """Calculate effectiveness score for an adaptation."""
        # This would use actual performance metrics
        # For now, we'll simulate based on adaptation type and confidence
        
        base_score = adaptation.confidence_score
        
        # Adjust based on adaptation type
        type_multipliers = {
            AdaptationType.CONFIGURATION_CHANGE: 0.8,
            AdaptationType.RESOURCE_SCALING: 0.9,
            AdaptationType.WORKFLOW_OPTIMIZATION: 0.7,
            AdaptationType.ERROR_PREVENTION: 0.85,
            AdaptationType.PERFORMANCE_TUNING: 0.75,
            AdaptationType.SCHEDULING_ADJUSTMENT: 0.6
        }
        
        multiplier = type_multipliers.get(adaptation.adaptation_type, 0.7)
        effectiveness = base_score * multiplier
        
        # Add some randomness to simulate real-world variability
        import random
        effectiveness += random.uniform(-0.2, 0.2)
        
        return max(0.0, min(1.0, effectiveness))
    
    async def _consider_revert(self, adaptation: Adaptation):
        """Consider reverting an adaptation if it's not effective."""
        if adaptation.effectiveness_score < 0.3:
            logger.warning(f"Reverting ineffective adaptation: {adaptation.id}")
            await self._revert_adaptation(adaptation)
    
    async def _revert_adaptation(self, adaptation: Adaptation):
        """Revert an adaptation."""
        try:
            # Restore previous configuration
            if self.config_history:
                previous_config = self.config_history.pop()
                self.current_config = previous_config
            
            adaptation.reverted = True
            adaptation.revert_reason = "Low effectiveness score"
            
            logger.info(f"Reverted adaptation: {adaptation.id}")
            
        except Exception as e:
            logger.error(f"Error reverting adaptation {adaptation.id}: {e}")
    
    # Adaptation functions for different rule types
    
    async def _adapt_task_timeout(self, pattern: Pattern) -> Dict[str, Any]:
        """Adapt task timeout based on failure patterns."""
        current_timeout = self.current_config.get("task_timeout", 300)
        
        # Increase timeout by 50% for timeout-related failures
        new_timeout = int(current_timeout * 1.5)
        
        return {
            "task_timeout": new_timeout,
            "retry_timeout": new_timeout // 2
        }
    
    async def _adapt_resource_scaling(self, pattern: Pattern) -> Dict[str, Any]:
        """Adapt resource scaling based on performance patterns."""
        current_max_tasks = self.current_config.get("max_concurrent_tasks", 10)
        degradation_factor = pattern.attributes.get("degradation_factor", 1.5)
        
        # Reduce concurrent tasks if performance is degrading
        if degradation_factor > 1.3:
            new_max_tasks = max(1, int(current_max_tasks * 0.8))
        else:
            new_max_tasks = min(20, int(current_max_tasks * 1.2))
        
        return {
            "max_concurrent_tasks": new_max_tasks,
            "resource_scaling_enabled": True
        }
    
    async def _adapt_resource_allocation(self, pattern: Pattern) -> Dict[str, Any]:
        """Adapt resource allocation based on usage patterns."""
        resource_type = pattern.attributes.get("resource_type", "memory")
        high_usage_rate = pattern.attributes.get("high_usage_rate", 0.8)
        
        if resource_type == "memory":
            return {
                "memory_limit_mb": int(self.current_config.get("memory_limit_mb", 1024) * 1.2),
                "memory_monitoring_enabled": True
            }
        elif resource_type == "cpu":
            return {
                "cpu_limit_percent": min(90, self.current_config.get("cpu_limit_percent", 80) + 10),
                "cpu_monitoring_enabled": True
            }
        
        return {}
    
    async def _adapt_workflow_parallelization(self, pattern: Pattern) -> Dict[str, Any]:
        """Adapt workflow parallelization based on optimization patterns."""
        workflow_type = pattern.attributes.get("workflow_type", "general")
        avg_duration = pattern.attributes.get("avg_duration", 180)
        
        # Enable parallelization for slow workflows
        parallel_steps = min(5, max(2, int(avg_duration / 60)))
        
        return {
            f"workflow_{workflow_type}_parallel_steps": parallel_steps,
            f"workflow_{workflow_type}_optimization_enabled": True
        }
    
    async def _adapt_error_prevention(self, pattern: Pattern) -> Dict[str, Any]:
        """Adapt error prevention based on correlation patterns."""
        primary_error = pattern.attributes.get("primary_error", "unknown")
        secondary_error = pattern.attributes.get("secondary_error", "unknown")
        
        return {
            f"error_prevention_{primary_error}_enabled": True,
            f"error_correlation_monitoring": True,
            "error_prevention_delay_seconds": 30
        }
    
    async def _adapt_scheduling(self, pattern: Pattern) -> Dict[str, Any]:
        """Adapt scheduling based on timing patterns."""
        hour = pattern.attributes.get("hour", 12)
        performance_type = pattern.attributes.get("performance_type", "worse")
        
        if performance_type == "worse":
            # Avoid scheduling during poor performance hours
            return {
                f"avoid_scheduling_hour_{hour}": True,
                "scheduling_optimization_enabled": True
            }
        else:
            # Prefer scheduling during good performance hours
            return {
                f"prefer_scheduling_hour_{hour}": True,
                "scheduling_optimization_enabled": True
            }
    
    def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get a summary of all adaptations."""
        total_adaptations = len(self.adaptations)
        effective_adaptations = len([a for a in self.adaptations if a.effectiveness_score and a.effectiveness_score > 0.6])
        reverted_adaptations = len([a for a in self.adaptations if a.reverted])
        
        return {
            "total_adaptations": total_adaptations,
            "effective_adaptations": effective_adaptations,
            "reverted_adaptations": reverted_adaptations,
            "effectiveness_rate": effective_adaptations / total_adaptations if total_adaptations > 0 else 0,
            "pending_adaptations": len(self.pending_adaptations),
            "active_rules": len([r for r in self.adaptation_rules.values() if r.enabled]),
            "current_config_size": len(self.current_config),
            "recent_adaptations": [
                {
                    "id": a.id,
                    "type": a.adaptation_type.value,
                    "description": a.description,
                    "effectiveness": a.effectiveness_score,
                    "applied_at": a.applied_at.isoformat()
                }
                for a in sorted(self.adaptations, key=lambda x: x.applied_at, reverse=True)[:5]
            ]
        }
    
    def get_pending_adaptations(self) -> List[Adaptation]:
        """Get all pending adaptations."""
        return self.pending_adaptations.copy()
    
    async def apply_pending_adaptation(self, adaptation_id: str) -> bool:
        """Apply a pending adaptation."""
        for i, adaptation in enumerate(self.pending_adaptations):
            if adaptation.id == adaptation_id:
                await self._apply_adaptation(adaptation)
                del self.pending_adaptations[i]
                return True
        return False
    
    def reject_pending_adaptation(self, adaptation_id: str) -> bool:
        """Reject a pending adaptation."""
        for i, adaptation in enumerate(self.pending_adaptations):
            if adaptation.id == adaptation_id:
                del self.pending_adaptations[i]
                logger.info(f"Rejected pending adaptation: {adaptation_id}")
                return True
        return False


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the adaptation engine."""
        from .pattern_recognition import PatternRecognitionEngine, DataPoint
        from .performance_tracker import PerformanceTracker
        
        # Initialize components
        pattern_engine = PatternRecognitionEngine()
        performance_tracker = PerformanceTracker()
        adaptation_engine = AdaptationEngine(pattern_engine, performance_tracker, auto_adapt=False)
        
        # Add some sample data
        for i in range(10):
            data_point = DataPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                event_type="task_execution",
                attributes={"task_type": "analysis"},
                outcome="failed" if i % 3 == 0 else "completed",
                duration=60 + i * 10,
                error_message="timeout error" if i % 3 == 0 else None
            )
            pattern_engine.add_data_point(data_point)
        
        # Analyze patterns
        patterns = await pattern_engine.analyze_patterns()
        print(f"Found {len(patterns)} patterns")
        
        # Create adaptations
        adaptations = await adaptation_engine.analyze_and_adapt()
        print(f"Created {len(adaptations)} adaptations")
        
        # Get summary
        summary = adaptation_engine.get_adaptation_summary()
        print(f"Adaptation summary: {json.dumps(summary, indent=2)}")
    
    asyncio.run(example_usage())

