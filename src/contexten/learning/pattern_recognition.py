"""
Pattern Recognition System

This module implements pattern recognition capabilities for continuous
learning and system improvement based on historical data and performance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import numpy as np
from collections import defaultdict, Counter
import hashlib

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be recognized."""
    TASK_FAILURE = "task_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_USAGE = "resource_usage"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    ERROR_CORRELATION = "error_correlation"
    SUCCESS_PATTERN = "success_pattern"
    TIMING_PATTERN = "timing_pattern"


@dataclass
class Pattern:
    """Represents a recognized pattern."""
    id: str
    pattern_type: PatternType
    description: str
    confidence_score: float
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)
    related_patterns: Set[str] = field(default_factory=set)
    impact_score: float = 0.0
    actionable: bool = True


@dataclass
class DataPoint:
    """Represents a data point for pattern analysis."""
    timestamp: datetime
    event_type: str
    attributes: Dict[str, Any]
    outcome: str
    duration: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternRecognitionEngine:
    """
    Advanced pattern recognition engine for continuous learning.
    
    This engine analyzes historical data to identify patterns that can
    improve system performance, predict failures, and optimize workflows.
    """
    
    def __init__(self, min_confidence: float = 0.7, min_occurrences: int = 3):
        """
        Initialize the pattern recognition engine.
        
        Args:
            min_confidence: Minimum confidence score for pattern recognition
            min_occurrences: Minimum occurrences to consider a pattern valid
        """
        self.min_confidence = min_confidence
        self.min_occurrences = min_occurrences
        
        self.data_points: List[DataPoint] = []
        self.recognized_patterns: Dict[str, Pattern] = {}
        self.pattern_analyzers: Dict[PatternType, callable] = {}
        
        # Setup pattern analyzers
        self._setup_pattern_analyzers()
        
        logger.info("Pattern recognition engine initialized")
    
    def _setup_pattern_analyzers(self):
        """Setup pattern analyzer functions for different pattern types."""
        self.pattern_analyzers = {
            PatternType.TASK_FAILURE: self._analyze_task_failure_patterns,
            PatternType.PERFORMANCE_DEGRADATION: self._analyze_performance_patterns,
            PatternType.RESOURCE_USAGE: self._analyze_resource_patterns,
            PatternType.WORKFLOW_OPTIMIZATION: self._analyze_workflow_patterns,
            PatternType.ERROR_CORRELATION: self._analyze_error_patterns,
            PatternType.SUCCESS_PATTERN: self._analyze_success_patterns,
            PatternType.TIMING_PATTERN: self._analyze_timing_patterns
        }
    
    def add_data_point(self, data_point: DataPoint):
        """Add a new data point for analysis."""
        self.data_points.append(data_point)
        
        # Keep only recent data points (last 30 days by default)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.data_points = [
            dp for dp in self.data_points 
            if dp.timestamp >= cutoff_date
        ]
        
        logger.debug(f"Added data point: {data_point.event_type}")
    
    async def analyze_patterns(self) -> List[Pattern]:
        """
        Analyze all data points to identify patterns.
        
        Returns:
            List of newly recognized patterns
        """
        logger.info("Starting pattern analysis...")
        
        new_patterns = []
        
        # Run each pattern analyzer
        for pattern_type, analyzer in self.pattern_analyzers.items():
            try:
                patterns = await analyzer()
                for pattern in patterns:
                    if self._is_valid_pattern(pattern):
                        pattern_id = self._generate_pattern_id(pattern)
                        pattern.id = pattern_id
                        
                        if pattern_id not in self.recognized_patterns:
                            self.recognized_patterns[pattern_id] = pattern
                            new_patterns.append(pattern)
                            logger.info(f"New pattern recognized: {pattern.description}")
                        else:
                            # Update existing pattern
                            self._update_existing_pattern(pattern_id, pattern)
                            
            except Exception as e:
                logger.error(f"Error analyzing {pattern_type.value} patterns: {e}")
        
        # Analyze pattern relationships
        await self._analyze_pattern_relationships()
        
        logger.info(f"Pattern analysis complete. Found {len(new_patterns)} new patterns")
        return new_patterns
    
    async def _analyze_task_failure_patterns(self) -> List[Pattern]:
        """Analyze patterns in task failures."""
        patterns = []
        
        # Get failed tasks
        failed_tasks = [
            dp for dp in self.data_points 
            if dp.event_type == "task_execution" and dp.outcome == "failed"
        ]
        
        if len(failed_tasks) < self.min_occurrences:
            return patterns
        
        # Analyze failure reasons
        error_groups = defaultdict(list)
        for task in failed_tasks:
            error_type = self._categorize_error(task.error_message)
            error_groups[error_type].append(task)
        
        for error_type, tasks in error_groups.items():
            if len(tasks) >= self.min_occurrences:
                # Calculate confidence based on frequency and recency
                confidence = min(0.9, len(tasks) / len(failed_tasks) + 0.3)
                
                pattern = Pattern(
                    id="",  # Will be set later
                    pattern_type=PatternType.TASK_FAILURE,
                    description=f"Recurring task failures due to {error_type}",
                    confidence_score=confidence,
                    occurrences=len(tasks),
                    first_seen=min(t.timestamp for t in tasks),
                    last_seen=max(t.timestamp for t in tasks),
                    attributes={
                        "error_type": error_type,
                        "failure_rate": len(tasks) / len(failed_tasks),
                        "common_attributes": self._find_common_attributes(tasks)
                    },
                    impact_score=len(tasks) / len(self.data_points)
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _analyze_performance_patterns(self) -> List[Pattern]:
        """Analyze performance degradation patterns."""
        patterns = []
        
        # Get task execution data with durations
        execution_data = [
            dp for dp in self.data_points 
            if dp.event_type == "task_execution" and dp.duration is not None
        ]
        
        if len(execution_data) < self.min_occurrences * 2:
            return patterns
        
        # Group by task type or other attributes
        task_groups = defaultdict(list)
        for task in execution_data:
            task_type = task.attributes.get("task_type", "unknown")
            task_groups[task_type].append(task)
        
        for task_type, tasks in task_groups.items():
            if len(tasks) >= self.min_occurrences:
                durations = [t.duration for t in tasks]
                avg_duration = np.mean(durations)
                std_duration = np.std(durations)
                
                # Check for performance degradation trend
                recent_tasks = sorted(tasks, key=lambda t: t.timestamp)[-10:]
                recent_avg = np.mean([t.duration for t in recent_tasks])
                
                if recent_avg > avg_duration + std_duration:
                    confidence = min(0.9, (recent_avg - avg_duration) / avg_duration)
                    
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.PERFORMANCE_DEGRADATION,
                        description=f"Performance degradation in {task_type} tasks",
                        confidence_score=confidence,
                        occurrences=len(recent_tasks),
                        first_seen=recent_tasks[0].timestamp,
                        last_seen=recent_tasks[-1].timestamp,
                        attributes={
                            "task_type": task_type,
                            "avg_duration": avg_duration,
                            "recent_avg_duration": recent_avg,
                            "degradation_factor": recent_avg / avg_duration
                        },
                        impact_score=confidence * 0.8
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _analyze_resource_patterns(self) -> List[Pattern]:
        """Analyze resource usage patterns."""
        patterns = []
        
        # Get resource usage data
        resource_data = [
            dp for dp in self.data_points 
            if dp.event_type == "resource_usage"
        ]
        
        if len(resource_data) < self.min_occurrences:
            return patterns
        
        # Analyze memory usage patterns
        memory_usage = [
            dp.attributes.get("memory_mb", 0) 
            for dp in resource_data 
            if "memory_mb" in dp.attributes
        ]
        
        if memory_usage:
            avg_memory = np.mean(memory_usage)
            high_usage_threshold = avg_memory * 1.5
            high_usage_count = sum(1 for m in memory_usage if m > high_usage_threshold)
            
            if high_usage_count >= self.min_occurrences:
                confidence = min(0.9, high_usage_count / len(memory_usage))
                
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.RESOURCE_USAGE,
                    description="High memory usage pattern detected",
                    confidence_score=confidence,
                    occurrences=high_usage_count,
                    first_seen=min(dp.timestamp for dp in resource_data),
                    last_seen=max(dp.timestamp for dp in resource_data),
                    attributes={
                        "resource_type": "memory",
                        "avg_usage_mb": avg_memory,
                        "threshold_mb": high_usage_threshold,
                        "high_usage_rate": high_usage_count / len(memory_usage)
                    },
                    impact_score=confidence * 0.6
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _analyze_workflow_patterns(self) -> List[Pattern]:
        """Analyze workflow optimization opportunities."""
        patterns = []
        
        # Get workflow execution data
        workflow_data = [
            dp for dp in self.data_points 
            if dp.event_type == "workflow_execution"
        ]
        
        if len(workflow_data) < self.min_occurrences:
            return patterns
        
        # Analyze workflow step dependencies and timing
        workflow_groups = defaultdict(list)
        for workflow in workflow_data:
            workflow_type = workflow.attributes.get("workflow_type", "unknown")
            workflow_groups[workflow_type].append(workflow)
        
        for workflow_type, workflows in workflow_groups.items():
            if len(workflows) >= self.min_occurrences:
                # Analyze step execution patterns
                step_durations = defaultdict(list)
                for workflow in workflows:
                    steps = workflow.attributes.get("steps", [])
                    for step in steps:
                        step_name = step.get("name")
                        step_duration = step.get("duration")
                        if step_name and step_duration:
                            step_durations[step_name].append(step_duration)
                
                # Find optimization opportunities
                for step_name, durations in step_durations.items():
                    if len(durations) >= self.min_occurrences:
                        avg_duration = np.mean(durations)
                        if avg_duration > 60:  # Steps taking more than 1 minute
                            confidence = min(0.8, avg_duration / 300)  # Scale by 5 minutes
                            
                            pattern = Pattern(
                                id="",
                                pattern_type=PatternType.WORKFLOW_OPTIMIZATION,
                                description=f"Optimization opportunity in {workflow_type} workflow step: {step_name}",
                                confidence_score=confidence,
                                occurrences=len(durations),
                                first_seen=min(w.timestamp for w in workflows),
                                last_seen=max(w.timestamp for w in workflows),
                                attributes={
                                    "workflow_type": workflow_type,
                                    "step_name": step_name,
                                    "avg_duration": avg_duration,
                                    "optimization_potential": "high" if avg_duration > 180 else "medium"
                                },
                                impact_score=confidence * 0.7
                            )
                            patterns.append(pattern)
        
        return patterns
    
    async def _analyze_error_patterns(self) -> List[Pattern]:
        """Analyze error correlation patterns."""
        patterns = []
        
        # Get error data
        error_data = [
            dp for dp in self.data_points 
            if dp.outcome == "failed" and dp.error_message
        ]
        
        if len(error_data) < self.min_occurrences:
            return patterns
        
        # Analyze error co-occurrence
        error_sequences = []
        for i in range(len(error_data) - 1):
            current_error = self._categorize_error(error_data[i].error_message)
            next_error = self._categorize_error(error_data[i + 1].error_message)
            
            # Check if errors occurred within a reasonable time window
            time_diff = (error_data[i + 1].timestamp - error_data[i].timestamp).total_seconds()
            if time_diff < 3600:  # Within 1 hour
                error_sequences.append((current_error, next_error))
        
        # Find common error sequences
        sequence_counts = Counter(error_sequences)
        for (error1, error2), count in sequence_counts.items():
            if count >= self.min_occurrences:
                confidence = min(0.9, count / len(error_sequences))
                
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.ERROR_CORRELATION,
                    description=f"Error correlation: {error1} often followed by {error2}",
                    confidence_score=confidence,
                    occurrences=count,
                    first_seen=min(dp.timestamp for dp in error_data),
                    last_seen=max(dp.timestamp for dp in error_data),
                    attributes={
                        "primary_error": error1,
                        "secondary_error": error2,
                        "correlation_strength": count / len(error_sequences)
                    },
                    impact_score=confidence * 0.8
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _analyze_success_patterns(self) -> List[Pattern]:
        """Analyze patterns that lead to success."""
        patterns = []
        
        # Get successful task data
        successful_tasks = [
            dp for dp in self.data_points 
            if dp.event_type == "task_execution" and dp.outcome == "completed"
        ]
        
        if len(successful_tasks) < self.min_occurrences:
            return patterns
        
        # Analyze attributes that correlate with success
        attribute_success_rates = defaultdict(lambda: {"total": 0, "success": 0})
        
        for task in self.data_points:
            if task.event_type == "task_execution":
                for attr_name, attr_value in task.attributes.items():
                    key = f"{attr_name}:{attr_value}"
                    attribute_success_rates[key]["total"] += 1
                    if task.outcome == "completed":
                        attribute_success_rates[key]["success"] += 1
        
        # Find attributes with high success rates
        for attr_key, stats in attribute_success_rates.items():
            if stats["total"] >= self.min_occurrences:
                success_rate = stats["success"] / stats["total"]
                if success_rate > 0.9:  # 90% success rate
                    confidence = min(0.9, success_rate)
                    
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.SUCCESS_PATTERN,
                        description=f"High success rate pattern: {attr_key}",
                        confidence_score=confidence,
                        occurrences=stats["success"],
                        first_seen=min(dp.timestamp for dp in successful_tasks),
                        last_seen=max(dp.timestamp for dp in successful_tasks),
                        attributes={
                            "attribute": attr_key,
                            "success_rate": success_rate,
                            "total_occurrences": stats["total"]
                        },
                        impact_score=confidence * 0.5
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _analyze_timing_patterns(self) -> List[Pattern]:
        """Analyze timing-based patterns."""
        patterns = []
        
        # Get timestamped data
        timestamped_data = [dp for dp in self.data_points if dp.timestamp]
        
        if len(timestamped_data) < self.min_occurrences:
            return patterns
        
        # Analyze patterns by hour of day
        hourly_performance = defaultdict(lambda: {"total": 0, "success": 0, "avg_duration": []})
        
        for dp in timestamped_data:
            hour = dp.timestamp.hour
            hourly_performance[hour]["total"] += 1
            if dp.outcome == "completed":
                hourly_performance[hour]["success"] += 1
            if dp.duration:
                hourly_performance[hour]["avg_duration"].append(dp.duration)
        
        # Find hours with significantly different performance
        overall_success_rate = sum(
            stats["success"] for stats in hourly_performance.values()
        ) / sum(
            stats["total"] for stats in hourly_performance.values()
        )
        
        for hour, stats in hourly_performance.items():
            if stats["total"] >= self.min_occurrences:
                hour_success_rate = stats["success"] / stats["total"]
                
                # Check for significant deviation
                if abs(hour_success_rate - overall_success_rate) > 0.2:
                    confidence = min(0.8, abs(hour_success_rate - overall_success_rate))
                    
                    pattern_type = "better" if hour_success_rate > overall_success_rate else "worse"
                    
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.TIMING_PATTERN,
                        description=f"Performance {pattern_type} during hour {hour}:00",
                        confidence_score=confidence,
                        occurrences=stats["total"],
                        first_seen=min(dp.timestamp for dp in timestamped_data),
                        last_seen=max(dp.timestamp for dp in timestamped_data),
                        attributes={
                            "hour": hour,
                            "success_rate": hour_success_rate,
                            "overall_success_rate": overall_success_rate,
                            "performance_type": pattern_type
                        },
                        impact_score=confidence * 0.4
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _categorize_error(self, error_message: Optional[str]) -> str:
        """Categorize error messages into types."""
        if not error_message:
            return "unknown"
        
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "memory" in error_lower or "oom" in error_lower:
            return "memory"
        elif "network" in error_lower or "connection" in error_lower:
            return "network"
        elif "permission" in error_lower or "auth" in error_lower:
            return "permission"
        elif "not found" in error_lower or "404" in error_lower:
            return "not_found"
        elif "rate limit" in error_lower:
            return "rate_limit"
        else:
            return "other"
    
    def _find_common_attributes(self, data_points: List[DataPoint]) -> Dict[str, Any]:
        """Find common attributes across data points."""
        if not data_points:
            return {}
        
        # Count attribute values
        attribute_counts = defaultdict(lambda: defaultdict(int))
        for dp in data_points:
            for attr_name, attr_value in dp.attributes.items():
                attribute_counts[attr_name][str(attr_value)] += 1
        
        # Find most common values
        common_attributes = {}
        for attr_name, value_counts in attribute_counts.items():
            most_common_value = max(value_counts.items(), key=lambda x: x[1])
            if most_common_value[1] >= len(data_points) * 0.5:  # At least 50% occurrence
                common_attributes[attr_name] = most_common_value[0]
        
        return common_attributes
    
    def _is_valid_pattern(self, pattern: Pattern) -> bool:
        """Check if a pattern meets validity criteria."""
        return (
            pattern.confidence_score >= self.min_confidence and
            pattern.occurrences >= self.min_occurrences
        )
    
    def _generate_pattern_id(self, pattern: Pattern) -> str:
        """Generate a unique ID for a pattern."""
        pattern_str = f"{pattern.pattern_type.value}:{pattern.description}:{pattern.attributes}"
        return hashlib.md5(pattern_str.encode()).hexdigest()[:12]
    
    def _update_existing_pattern(self, pattern_id: str, new_pattern: Pattern):
        """Update an existing pattern with new data."""
        existing = self.recognized_patterns[pattern_id]
        existing.occurrences = max(existing.occurrences, new_pattern.occurrences)
        existing.last_seen = max(existing.last_seen, new_pattern.last_seen)
        existing.confidence_score = max(existing.confidence_score, new_pattern.confidence_score)
        existing.attributes.update(new_pattern.attributes)
    
    async def _analyze_pattern_relationships(self):
        """Analyze relationships between patterns."""
        patterns = list(self.recognized_patterns.values())
        
        for i, pattern1 in enumerate(patterns):
            for pattern2 in patterns[i+1:]:
                # Check for temporal correlation
                time_overlap = (
                    pattern1.last_seen >= pattern2.first_seen and
                    pattern2.last_seen >= pattern1.first_seen
                )
                
                if time_overlap:
                    # Check for attribute similarity
                    common_attrs = set(pattern1.attributes.keys()) & set(pattern2.attributes.keys())
                    if common_attrs:
                        pattern1.related_patterns.add(pattern2.id)
                        pattern2.related_patterns.add(pattern1.id)
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type."""
        return [
            pattern for pattern in self.recognized_patterns.values()
            if pattern.pattern_type == pattern_type
        ]
    
    def get_high_impact_patterns(self, min_impact: float = 0.5) -> List[Pattern]:
        """Get patterns with high impact scores."""
        return [
            pattern for pattern in self.recognized_patterns.values()
            if pattern.impact_score >= min_impact
        ]
    
    def get_actionable_patterns(self) -> List[Pattern]:
        """Get patterns that are actionable."""
        return [
            pattern for pattern in self.recognized_patterns.values()
            if pattern.actionable
        ]
    
    def export_patterns(self) -> Dict[str, Any]:
        """Export all recognized patterns."""
        return {
            "patterns": {
                pattern_id: {
                    "pattern_type": pattern.pattern_type.value,
                    "description": pattern.description,
                    "confidence_score": pattern.confidence_score,
                    "occurrences": pattern.occurrences,
                    "first_seen": pattern.first_seen.isoformat(),
                    "last_seen": pattern.last_seen.isoformat(),
                    "attributes": pattern.attributes,
                    "related_patterns": list(pattern.related_patterns),
                    "impact_score": pattern.impact_score,
                    "actionable": pattern.actionable
                }
                for pattern_id, pattern in self.recognized_patterns.items()
            },
            "summary": {
                "total_patterns": len(self.recognized_patterns),
                "by_type": {
                    pattern_type.value: len(self.get_patterns_by_type(pattern_type))
                    for pattern_type in PatternType
                },
                "high_impact_count": len(self.get_high_impact_patterns()),
                "actionable_count": len(self.get_actionable_patterns())
            }
        }


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the pattern recognition engine."""
        engine = PatternRecognitionEngine()
        
        # Add some sample data points
        for i in range(20):
            data_point = DataPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                event_type="task_execution",
                attributes={"task_type": "analysis", "priority": 5},
                outcome="completed" if i % 3 != 0 else "failed",
                duration=60 + i * 5,
                error_message="timeout error" if i % 3 == 0 else None
            )
            engine.add_data_point(data_point)
        
        # Analyze patterns
        patterns = await engine.analyze_patterns()
        
        print(f"Found {len(patterns)} patterns:")
        for pattern in patterns:
            print(f"- {pattern.description} (confidence: {pattern.confidence_score:.2f})")
        
        # Export patterns
        export_data = engine.export_patterns()
        print(f"\nPattern summary: {export_data['summary']}")
    
    asyncio.run(example_usage())

