"""
Effectiveness and Performance Metrics

Data structures and utilities for tracking effectiveness and performance metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import statistics
import time


@dataclass
class EffectivenessMetrics:
    """Metrics for component effectiveness evaluation."""
    overall_score: float = 0.0
    functionality_score: float = 0.0
    reliability_score: float = 0.0
    performance_score: float = 0.0
    usability_score: float = 0.0
    maintainability_score: float = 0.0
    
    # Aggregate metrics
    score_variance: float = 0.0
    score_range: float = 0.0
    weighted_average: float = 0.0
    
    # Weights for different dimensions
    weights: Dict[str, float] = field(default_factory=lambda: {
        'functionality': 0.3,
        'reliability': 0.25,
        'performance': 0.2,
        'usability': 0.15,
        'maintainability': 0.1
    })
    
    def calculate_weighted_average(self) -> float:
        """Calculate weighted average of all scores."""
        scores = {
            'functionality': self.functionality_score,
            'reliability': self.reliability_score,
            'performance': self.performance_score,
            'usability': self.usability_score,
            'maintainability': self.maintainability_score
        }
        
        weighted_sum = sum(scores[dim] * self.weights[dim] for dim in scores)
        total_weight = sum(self.weights.values())
        
        self.weighted_average = weighted_sum / total_weight if total_weight > 0 else 0.0
        return self.weighted_average
    
    def calculate_variance(self) -> float:
        """Calculate variance of all scores."""
        scores = [
            self.functionality_score,
            self.reliability_score,
            self.performance_score,
            self.usability_score,
            self.maintainability_score
        ]
        
        if len(scores) > 1:
            self.score_variance = statistics.variance(scores)
        else:
            self.score_variance = 0.0
        
        return self.score_variance
    
    def calculate_range(self) -> float:
        """Calculate range of all scores."""
        scores = [
            self.functionality_score,
            self.reliability_score,
            self.performance_score,
            self.usability_score,
            self.maintainability_score
        ]
        
        self.score_range = max(scores) - min(scores) if scores else 0.0
        return self.score_range
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        self.calculate_weighted_average()
        self.calculate_variance()
        self.calculate_range()
        
        return {
            'overall_score': self.overall_score,
            'weighted_average': self.weighted_average,
            'individual_scores': {
                'functionality': self.functionality_score,
                'reliability': self.reliability_score,
                'performance': self.performance_score,
                'usability': self.usability_score,
                'maintainability': self.maintainability_score
            },
            'statistical_measures': {
                'variance': self.score_variance,
                'range': self.score_range,
                'standard_deviation': self.score_variance ** 0.5
            },
            'weights': self.weights
        }


@dataclass
class PerformanceMetrics:
    """Metrics for component performance analysis."""
    average_effectiveness: float = 0.0
    score_variance: float = 0.0
    trend_direction: float = 0.0
    evaluation_count: int = 0
    consistency_score: float = 0.0
    improvement_rate: float = 0.0
    
    # Timing metrics
    average_execution_time_ms: float = 0.0
    min_execution_time_ms: float = 0.0
    max_execution_time_ms: float = 0.0
    execution_time_variance: float = 0.0
    
    # Resource metrics
    average_memory_usage_mb: float = 0.0
    peak_memory_usage_mb: float = 0.0
    memory_efficiency_score: float = 0.0
    
    # Reliability metrics
    success_rate: float = 0.0
    error_rate: float = 0.0
    failure_count: int = 0
    
    # Historical data
    historical_scores: List[float] = field(default_factory=list)
    historical_timestamps: List[float] = field(default_factory=list)
    
    def add_measurement(
        self, 
        effectiveness_score: float, 
        execution_time_ms: float = 0.0,
        memory_usage_mb: float = 0.0,
        success: bool = True
    ) -> None:
        """Add a new measurement to the metrics."""
        # Add to historical data
        self.historical_scores.append(effectiveness_score)
        self.historical_timestamps.append(time.time())
        
        # Update counts
        self.evaluation_count += 1
        if not success:
            self.failure_count += 1
        
        # Recalculate metrics
        self._recalculate_metrics()
    
    def _recalculate_metrics(self) -> None:
        """Recalculate all derived metrics."""
        if not self.historical_scores:
            return
        
        # Effectiveness metrics
        self.average_effectiveness = statistics.mean(self.historical_scores)
        if len(self.historical_scores) > 1:
            self.score_variance = statistics.variance(self.historical_scores)
        
        # Trend calculation
        if len(self.historical_scores) >= 2:
            recent_scores = self.historical_scores[-3:] if len(self.historical_scores) >= 3 else [self.historical_scores[-1]]
            older_scores = self.historical_scores[:-3] if len(self.historical_scores) > 3 else [self.historical_scores[0]]
            
            recent_avg = statistics.mean(recent_scores)
            older_avg = statistics.mean(older_scores)
            self.trend_direction = recent_avg - older_avg
        
        # Consistency score (inverse of variance)
        self.consistency_score = max(0.0, 1.0 - self.score_variance)
        
        # Improvement rate (positive trend)
        self.improvement_rate = max(0.0, self.trend_direction)
        
        # Reliability metrics
        self.success_rate = (self.evaluation_count - self.failure_count) / self.evaluation_count
        self.error_rate = self.failure_count / self.evaluation_count
    
    def get_trend_analysis(self, window_size: int = 5) -> Dict[str, Any]:
        """Get trend analysis over a specified window."""
        if len(self.historical_scores) < window_size:
            return {'insufficient_data': True}
        
        recent_window = self.historical_scores[-window_size:]
        older_window = self.historical_scores[-2*window_size:-window_size] if len(self.historical_scores) >= 2*window_size else self.historical_scores[:-window_size]
        
        recent_avg = statistics.mean(recent_window)
        older_avg = statistics.mean(older_window) if older_window else recent_avg
        
        trend_strength = abs(recent_avg - older_avg)
        trend_direction = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'recent_average': recent_avg,
            'older_average': older_avg,
            'window_size': window_size,
            'confidence': min(1.0, len(recent_window) / window_size)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            'effectiveness': {
                'average': self.average_effectiveness,
                'variance': self.score_variance,
                'consistency': self.consistency_score,
                'trend': self.trend_direction
            },
            'reliability': {
                'success_rate': self.success_rate,
                'error_rate': self.error_rate,
                'failure_count': self.failure_count,
                'total_evaluations': self.evaluation_count
            },
            'performance': {
                'average_execution_time_ms': self.average_execution_time_ms,
                'execution_time_variance': self.execution_time_variance,
                'memory_efficiency': self.memory_efficiency_score
            },
            'trends': self.get_trend_analysis(),
            'improvement_metrics': {
                'improvement_rate': self.improvement_rate,
                'trend_direction': self.trend_direction
            }
        }


@dataclass
class ComponentComparisonMetrics:
    """Metrics for comparing multiple components."""
    component_scores: Dict[str, EffectivenessMetrics] = field(default_factory=dict)
    relative_rankings: Dict[str, int] = field(default_factory=dict)
    performance_gaps: Dict[str, float] = field(default_factory=dict)
    
    def add_component(self, component_name: str, metrics: EffectivenessMetrics) -> None:
        """Add a component's metrics for comparison."""
        self.component_scores[component_name] = metrics
        self._recalculate_comparisons()
    
    def _recalculate_comparisons(self) -> None:
        """Recalculate relative rankings and performance gaps."""
        if not self.component_scores:
            return
        
        # Calculate overall scores for ranking
        component_overall_scores = {
            name: metrics.calculate_weighted_average()
            for name, metrics in self.component_scores.items()
        }
        
        # Create rankings (1 = best)
        sorted_components = sorted(
            component_overall_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for rank, (component_name, score) in enumerate(sorted_components, 1):
            self.relative_rankings[component_name] = rank
        
        # Calculate performance gaps (difference from best)
        if sorted_components:
            best_score = sorted_components[0][1]
            for component_name, score in component_overall_scores.items():
                self.performance_gaps[component_name] = best_score - score
    
    def get_comparison_summary(self) -> Dict[str, Any]:
        """Get comprehensive comparison summary."""
        if not self.component_scores:
            return {'no_components': True}
        
        # Find best and worst performers
        rankings = [(name, rank) for name, rank in self.relative_rankings.items()]
        rankings.sort(key=lambda x: x[1])
        
        best_performer = rankings[0][0] if rankings else None
        worst_performer = rankings[-1][0] if rankings else None
        
        # Calculate average metrics across all components
        all_scores = [metrics.calculate_weighted_average() for metrics in self.component_scores.values()]
        avg_score = statistics.mean(all_scores) if all_scores else 0.0
        score_variance = statistics.variance(all_scores) if len(all_scores) > 1 else 0.0
        
        return {
            'summary': {
                'total_components': len(self.component_scores),
                'average_score': avg_score,
                'score_variance': score_variance,
                'best_performer': best_performer,
                'worst_performer': worst_performer
            },
            'rankings': self.relative_rankings,
            'performance_gaps': self.performance_gaps,
            'component_details': {
                name: metrics.get_summary()
                for name, metrics in self.component_scores.items()
            }
        }

