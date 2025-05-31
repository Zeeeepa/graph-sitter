"""
Performance Analyzer

Comprehensive performance analysis tools for OpenEvolve integration components.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..database.overlay import DatabaseOverlay
from ..openevolve.config import OpenEvolveConfig


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: float
    component_type: str
    component_name: str
    effectiveness_score: float
    execution_time_ms: int
    memory_usage_mb: float
    success_rate: float
    error_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTrend:
    """Performance trend analysis over time."""
    component_name: str
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0.0 to 1.0
    slope: float  # Rate of change
    confidence: float  # 0.0 to 1.0
    data_points: int
    time_span_hours: float


@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks."""
    component_name: str
    bottleneck_type: str  # 'execution_time', 'memory', 'effectiveness', 'reliability'
    severity: str  # 'low', 'medium', 'high', 'critical'
    impact_score: float  # 0.0 to 1.0
    description: str
    recommendations: List[str]


class PerformanceAnalyzer:
    """
    Comprehensive performance analyzer for OpenEvolve integration components.
    
    Provides detailed analysis of component performance, trend detection,
    bottleneck identification, and optimization recommendations.
    """
    
    def __init__(self, database_overlay: DatabaseOverlay, config: OpenEvolveConfig):
        """Initialize the performance analyzer."""
        self.database_overlay = database_overlay
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds
        self.thresholds = {
            'effectiveness_min': 0.7,
            'execution_time_max_ms': 5000,
            'memory_usage_max_mb': 100.0,
            'success_rate_min': 0.95,
            'error_rate_max': 0.05
        }
        
        # Trend analysis parameters
        self.trend_window_hours = 24
        self.min_data_points = 5
    
    async def analyze_component_performance(
        self,
        session_id: str,
        component_type: Optional[str] = None,
        time_window_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance for components in a session.
        
        Args:
            session_id: Evaluation session ID
            component_type: Optional filter by component type
            time_window_hours: Optional time window for analysis
            
        Returns:
            Comprehensive performance analysis results
        """
        try:
            self.logger.info("Starting performance analysis for session: %s", session_id)
            
            # Get evaluation data
            evaluations = await self.database_overlay.get_component_evaluations(
                session_id=session_id,
                component_type=component_type
            )
            
            if not evaluations:
                return {'error': 'No evaluation data found', 'session_id': session_id}
            
            # Filter by time window if specified
            if time_window_hours:
                cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
                evaluations = [
                    eval_data for eval_data in evaluations
                    if datetime.fromisoformat(eval_data['evaluation_timestamp']) > cutoff_time
                ]
            
            # Convert to performance snapshots
            snapshots = self._convert_to_snapshots(evaluations)
            
            # Perform various analyses
            analysis_results = {
                'session_id': session_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'time_window_hours': time_window_hours,
                'total_evaluations': len(evaluations),
                'component_summary': await self._analyze_component_summary(snapshots),
                'performance_trends': await self._analyze_performance_trends(snapshots),
                'bottleneck_analysis': await self._analyze_bottlenecks(snapshots),
                'comparative_analysis': await self._analyze_component_comparison(snapshots),
                'optimization_opportunities': await self._identify_optimization_opportunities(snapshots),
                'performance_score': await self._calculate_overall_performance_score(snapshots)
            }
            
            # Store analysis results
            await self._store_analysis_results(session_id, analysis_results)
            
            self.logger.info("Performance analysis completed for session: %s", session_id)
            return analysis_results
            
        except Exception as e:
            self.logger.error("Performance analysis failed: %s", str(e))
            return {'error': str(e), 'session_id': session_id}
    
    def _convert_to_snapshots(self, evaluations: List[Dict[str, Any]]) -> List[PerformanceSnapshot]:
        """Convert evaluation data to performance snapshots."""
        snapshots = []
        
        for eval_data in evaluations:
            try:
                timestamp = datetime.fromisoformat(eval_data['evaluation_timestamp']).timestamp()
                
                snapshot = PerformanceSnapshot(
                    timestamp=timestamp,
                    component_type=eval_data['component_type'],
                    component_name=eval_data['component_name'],
                    effectiveness_score=eval_data['effectiveness_score'] or 0.0,
                    execution_time_ms=eval_data['execution_time_ms'] or 0,
                    memory_usage_mb=eval_data['memory_usage_mb'] or 0.0,
                    success_rate=eval_data['success_rate'] or 0.0,
                    error_count=eval_data['error_count'] or 0,
                    metadata=eval_data['metadata'] or {}
                )
                
                snapshots.append(snapshot)
                
            except Exception as e:
                self.logger.warning("Failed to convert evaluation to snapshot: %s", str(e))
                continue
        
        return snapshots
    
    async def _analyze_component_summary(self, snapshots: List[PerformanceSnapshot]) -> Dict[str, Any]:
        """Analyze overall component performance summary."""
        try:
            if not snapshots:
                return {'no_data': True}
            
            # Group by component
            component_groups = {}
            for snapshot in snapshots:
                key = f"{snapshot.component_type}:{snapshot.component_name}"
                if key not in component_groups:
                    component_groups[key] = []
                component_groups[key].append(snapshot)
            
            summary = {}
            
            for component_key, component_snapshots in component_groups.items():
                component_type, component_name = component_key.split(':', 1)
                
                # Calculate statistics
                effectiveness_scores = [s.effectiveness_score for s in component_snapshots]
                execution_times = [s.execution_time_ms for s in component_snapshots]
                memory_usage = [s.memory_usage_mb for s in component_snapshots if s.memory_usage_mb > 0]
                success_rates = [s.success_rate for s in component_snapshots]
                
                component_summary = {
                    'component_type': component_type,
                    'component_name': component_name,
                    'evaluation_count': len(component_snapshots),
                    'effectiveness': {
                        'average': statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0,
                        'min': min(effectiveness_scores) if effectiveness_scores else 0.0,
                        'max': max(effectiveness_scores) if effectiveness_scores else 0.0,
                        'variance': statistics.variance(effectiveness_scores) if len(effectiveness_scores) > 1 else 0.0
                    },
                    'performance': {
                        'avg_execution_time_ms': statistics.mean(execution_times) if execution_times else 0.0,
                        'min_execution_time_ms': min(execution_times) if execution_times else 0.0,
                        'max_execution_time_ms': max(execution_times) if execution_times else 0.0,
                        'avg_memory_usage_mb': statistics.mean(memory_usage) if memory_usage else 0.0
                    },
                    'reliability': {
                        'avg_success_rate': statistics.mean(success_rates) if success_rates else 0.0,
                        'total_errors': sum(s.error_count for s in component_snapshots)
                    }
                }
                
                summary[component_key] = component_summary
            
            return summary
            
        except Exception as e:
            self.logger.error("Component summary analysis failed: %s", str(e))
            return {'error': str(e)}
    
    async def _analyze_performance_trends(self, snapshots: List[PerformanceSnapshot]) -> List[PerformanceTrend]:
        """Analyze performance trends over time."""
        try:
            trends = []
            
            # Group by component
            component_groups = {}
            for snapshot in snapshots:
                key = f"{snapshot.component_type}:{snapshot.component_name}"
                if key not in component_groups:
                    component_groups[key] = []
                component_groups[key].append(snapshot)
            
            for component_key, component_snapshots in component_groups.items():
                if len(component_snapshots) < self.min_data_points:
                    continue
                
                # Sort by timestamp
                component_snapshots.sort(key=lambda x: x.timestamp)
                
                # Analyze effectiveness trend
                timestamps = [s.timestamp for s in component_snapshots]
                effectiveness_scores = [s.effectiveness_score for s in component_snapshots]
                
                trend = self._calculate_trend(timestamps, effectiveness_scores)
                
                if trend:
                    component_name = component_key.split(':', 1)[1]
                    trends.append(PerformanceTrend(
                        component_name=component_name,
                        trend_direction=trend['direction'],
                        trend_strength=trend['strength'],
                        slope=trend['slope'],
                        confidence=trend['confidence'],
                        data_points=len(component_snapshots),
                        time_span_hours=(timestamps[-1] - timestamps[0]) / 3600
                    ))
            
            return trends
            
        except Exception as e:
            self.logger.error("Performance trend analysis failed: %s", str(e))
            return []
    
    def _calculate_trend(self, timestamps: List[float], values: List[float]) -> Optional[Dict[str, Any]]:
        """Calculate trend statistics for a time series."""
        try:
            if len(timestamps) < 2 or len(values) < 2:
                return None
            
            # Normalize timestamps to hours from start
            start_time = timestamps[0]
            normalized_times = [(t - start_time) / 3600 for t in timestamps]
            
            # Calculate linear regression slope
            n = len(normalized_times)
            sum_x = sum(normalized_times)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(normalized_times, values))
            sum_x2 = sum(x * x for x in normalized_times)
            
            # Slope calculation
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                slope = 0.0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Determine trend direction and strength
            if abs(slope) < 0.01:
                direction = 'stable'
                strength = 0.0
            elif slope > 0:
                direction = 'improving'
                strength = min(1.0, abs(slope) * 10)  # Scale slope to 0-1
            else:
                direction = 'declining'
                strength = min(1.0, abs(slope) * 10)
            
            # Calculate confidence based on data consistency
            if len(values) > 1:
                variance = statistics.variance(values)
                confidence = max(0.1, min(0.95, 1.0 - variance))
            else:
                confidence = 0.5
            
            return {
                'direction': direction,
                'strength': strength,
                'slope': slope,
                'confidence': confidence
            }
            
        except Exception as e:
            self.logger.warning("Trend calculation failed: %s", str(e))
            return None
    
    async def _analyze_bottlenecks(self, snapshots: List[PerformanceSnapshot]) -> List[BottleneckAnalysis]:
        """Analyze performance bottlenecks."""
        try:
            bottlenecks = []
            
            # Group by component
            component_groups = {}
            for snapshot in snapshots:
                key = f"{snapshot.component_type}:{snapshot.component_name}"
                if key not in component_groups:
                    component_groups[key] = []
                component_groups[key].append(snapshot)
            
            for component_key, component_snapshots in component_groups.items():
                component_name = component_key.split(':', 1)[1]
                
                # Analyze different bottleneck types
                bottlenecks.extend(await self._check_execution_time_bottlenecks(component_name, component_snapshots))
                bottlenecks.extend(await self._check_memory_bottlenecks(component_name, component_snapshots))
                bottlenecks.extend(await self._check_effectiveness_bottlenecks(component_name, component_snapshots))
                bottlenecks.extend(await self._check_reliability_bottlenecks(component_name, component_snapshots))
            
            # Sort by severity and impact
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            bottlenecks.sort(key=lambda x: (severity_order.get(x.severity, 4), -x.impact_score))
            
            return bottlenecks
            
        except Exception as e:
            self.logger.error("Bottleneck analysis failed: %s", str(e))
            return []
    
    async def _check_execution_time_bottlenecks(
        self, 
        component_name: str, 
        snapshots: List[PerformanceSnapshot]
    ) -> List[BottleneckAnalysis]:
        """Check for execution time bottlenecks."""
        bottlenecks = []
        
        execution_times = [s.execution_time_ms for s in snapshots if s.execution_time_ms > 0]
        if not execution_times:
            return bottlenecks
        
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        # Check against thresholds
        if avg_time > self.thresholds['execution_time_max_ms']:
            severity = 'critical' if avg_time > self.thresholds['execution_time_max_ms'] * 2 else 'high'
            impact_score = min(1.0, avg_time / self.thresholds['execution_time_max_ms'])
            
            bottlenecks.append(BottleneckAnalysis(
                component_name=component_name,
                bottleneck_type='execution_time',
                severity=severity,
                impact_score=impact_score,
                description=f"Average execution time ({avg_time:.1f}ms) exceeds threshold ({self.thresholds['execution_time_max_ms']}ms)",
                recommendations=[
                    "Profile code to identify slow operations",
                    "Consider caching frequently computed results",
                    "Optimize algorithms and data structures",
                    "Implement asynchronous processing where possible"
                ]
            ))
        
        # Check for high variance (inconsistent performance)
        if len(execution_times) > 1:
            variance = statistics.variance(execution_times)
            if variance > (avg_time * 0.5) ** 2:  # High variance
                bottlenecks.append(BottleneckAnalysis(
                    component_name=component_name,
                    bottleneck_type='execution_time',
                    severity='medium',
                    impact_score=0.6,
                    description=f"Inconsistent execution times (variance: {variance:.1f})",
                    recommendations=[
                        "Investigate causes of performance variability",
                        "Implement performance monitoring",
                        "Consider load balancing or resource allocation improvements"
                    ]
                ))
        
        return bottlenecks
    
    async def _check_memory_bottlenecks(
        self, 
        component_name: str, 
        snapshots: List[PerformanceSnapshot]
    ) -> List[BottleneckAnalysis]:
        """Check for memory usage bottlenecks."""
        bottlenecks = []
        
        memory_usage = [s.memory_usage_mb for s in snapshots if s.memory_usage_mb > 0]
        if not memory_usage:
            return bottlenecks
        
        avg_memory = statistics.mean(memory_usage)
        max_memory = max(memory_usage)
        
        if avg_memory > self.thresholds['memory_usage_max_mb']:
            severity = 'critical' if avg_memory > self.thresholds['memory_usage_max_mb'] * 2 else 'high'
            impact_score = min(1.0, avg_memory / self.thresholds['memory_usage_max_mb'])
            
            bottlenecks.append(BottleneckAnalysis(
                component_name=component_name,
                bottleneck_type='memory',
                severity=severity,
                impact_score=impact_score,
                description=f"Average memory usage ({avg_memory:.1f}MB) exceeds threshold ({self.thresholds['memory_usage_max_mb']}MB)",
                recommendations=[
                    "Profile memory usage to identify leaks",
                    "Implement object pooling or reuse strategies",
                    "Optimize data structures for memory efficiency",
                    "Consider streaming or batch processing for large datasets"
                ]
            ))
        
        return bottlenecks
    
    async def _check_effectiveness_bottlenecks(
        self, 
        component_name: str, 
        snapshots: List[PerformanceSnapshot]
    ) -> List[BottleneckAnalysis]:
        """Check for effectiveness bottlenecks."""
        bottlenecks = []
        
        effectiveness_scores = [s.effectiveness_score for s in snapshots]
        if not effectiveness_scores:
            return bottlenecks
        
        avg_effectiveness = statistics.mean(effectiveness_scores)
        min_effectiveness = min(effectiveness_scores)
        
        if avg_effectiveness < self.thresholds['effectiveness_min']:
            severity = 'critical' if avg_effectiveness < 0.5 else 'high'
            impact_score = 1.0 - avg_effectiveness
            
            bottlenecks.append(BottleneckAnalysis(
                component_name=component_name,
                bottleneck_type='effectiveness',
                severity=severity,
                impact_score=impact_score,
                description=f"Average effectiveness ({avg_effectiveness:.3f}) below threshold ({self.thresholds['effectiveness_min']})",
                recommendations=[
                    "Review component implementation and algorithms",
                    "Validate evaluation criteria and metrics",
                    "Consider retraining or reconfiguration",
                    "Analyze input data quality and preprocessing"
                ]
            ))
        
        return bottlenecks
    
    async def _check_reliability_bottlenecks(
        self, 
        component_name: str, 
        snapshots: List[PerformanceSnapshot]
    ) -> List[BottleneckAnalysis]:
        """Check for reliability bottlenecks."""
        bottlenecks = []
        
        success_rates = [s.success_rate for s in snapshots]
        total_errors = sum(s.error_count for s in snapshots)
        
        if not success_rates:
            return bottlenecks
        
        avg_success_rate = statistics.mean(success_rates)
        
        if avg_success_rate < self.thresholds['success_rate_min']:
            severity = 'critical' if avg_success_rate < 0.8 else 'high'
            impact_score = 1.0 - avg_success_rate
            
            bottlenecks.append(BottleneckAnalysis(
                component_name=component_name,
                bottleneck_type='reliability',
                severity=severity,
                impact_score=impact_score,
                description=f"Average success rate ({avg_success_rate:.3f}) below threshold ({self.thresholds['success_rate_min']})",
                recommendations=[
                    "Implement better error handling and recovery",
                    "Add input validation and sanitization",
                    "Improve logging and monitoring",
                    "Consider circuit breaker patterns for external dependencies"
                ]
            ))
        
        if total_errors > len(snapshots) * 0.1:  # More than 10% error rate
            bottlenecks.append(BottleneckAnalysis(
                component_name=component_name,
                bottleneck_type='reliability',
                severity='medium',
                impact_score=0.7,
                description=f"High error count ({total_errors} errors in {len(snapshots)} evaluations)",
                recommendations=[
                    "Investigate root causes of errors",
                    "Implement better error prevention",
                    "Add comprehensive testing coverage"
                ]
            ))
        
        return bottlenecks
    
    async def _analyze_component_comparison(self, snapshots: List[PerformanceSnapshot]) -> Dict[str, Any]:
        """Compare performance across different components."""
        try:
            # Group by component type
            type_groups = {}
            for snapshot in snapshots:
                if snapshot.component_type not in type_groups:
                    type_groups[snapshot.component_type] = []
                type_groups[snapshot.component_type].append(snapshot)
            
            comparison = {}
            
            for component_type, type_snapshots in type_groups.items():
                # Group by component name within type
                component_groups = {}
                for snapshot in type_snapshots:
                    if snapshot.component_name not in component_groups:
                        component_groups[snapshot.component_name] = []
                    component_groups[snapshot.component_name].append(snapshot)
                
                # Calculate averages for each component
                component_averages = {}
                for component_name, component_snapshots in component_groups.items():
                    effectiveness_scores = [s.effectiveness_score for s in component_snapshots]
                    execution_times = [s.execution_time_ms for s in component_snapshots]
                    
                    component_averages[component_name] = {
                        'avg_effectiveness': statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0,
                        'avg_execution_time': statistics.mean(execution_times) if execution_times else 0.0,
                        'evaluation_count': len(component_snapshots)
                    }
                
                # Rank components
                if component_averages:
                    # Rank by effectiveness (higher is better)
                    effectiveness_ranking = sorted(
                        component_averages.items(),
                        key=lambda x: x[1]['avg_effectiveness'],
                        reverse=True
                    )
                    
                    # Rank by execution time (lower is better)
                    performance_ranking = sorted(
                        component_averages.items(),
                        key=lambda x: x[1]['avg_execution_time']
                    )
                    
                    comparison[component_type] = {
                        'component_count': len(component_averages),
                        'effectiveness_ranking': [(name, data['avg_effectiveness']) for name, data in effectiveness_ranking],
                        'performance_ranking': [(name, data['avg_execution_time']) for name, data in performance_ranking],
                        'component_details': component_averages
                    }
            
            return comparison
            
        except Exception as e:
            self.logger.error("Component comparison analysis failed: %s", str(e))
            return {'error': str(e)}
    
    async def _identify_optimization_opportunities(self, snapshots: List[PerformanceSnapshot]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities."""
        try:
            opportunities = []
            
            # Group by component
            component_groups = {}
            for snapshot in snapshots:
                key = f"{snapshot.component_type}:{snapshot.component_name}"
                if key not in component_groups:
                    component_groups[key] = []
                component_groups[key].append(snapshot)
            
            for component_key, component_snapshots in component_groups.items():
                component_name = component_key.split(':', 1)[1]
                
                # Analyze for optimization opportunities
                effectiveness_scores = [s.effectiveness_score for s in component_snapshots]
                execution_times = [s.execution_time_ms for s in component_snapshots]
                
                if effectiveness_scores and execution_times:
                    avg_effectiveness = statistics.mean(effectiveness_scores)
                    avg_execution_time = statistics.mean(execution_times)
                    
                    # Low effectiveness, high execution time
                    if avg_effectiveness < 0.7 and avg_execution_time > 1000:
                        opportunities.append({
                            'component_name': component_name,
                            'opportunity_type': 'algorithm_optimization',
                            'priority': 'high',
                            'description': 'Low effectiveness with high execution time suggests algorithmic improvements needed',
                            'potential_impact': 'high',
                            'recommendations': [
                                'Review and optimize core algorithms',
                                'Consider alternative approaches or libraries',
                                'Implement performance profiling'
                            ]
                        })
                    
                    # High variance in execution time
                    if len(execution_times) > 1:
                        variance = statistics.variance(execution_times)
                        if variance > (avg_execution_time * 0.3) ** 2:
                            opportunities.append({
                                'component_name': component_name,
                                'opportunity_type': 'consistency_improvement',
                                'priority': 'medium',
                                'description': 'High variance in execution time indicates inconsistent performance',
                                'potential_impact': 'medium',
                                'recommendations': [
                                    'Implement caching strategies',
                                    'Optimize resource allocation',
                                    'Add performance monitoring'
                                ]
                            })
                    
                    # Good effectiveness but slow execution
                    if avg_effectiveness > 0.8 and avg_execution_time > 2000:
                        opportunities.append({
                            'component_name': component_name,
                            'opportunity_type': 'performance_optimization',
                            'priority': 'medium',
                            'description': 'Good effectiveness but slow execution suggests optimization potential',
                            'potential_impact': 'medium',
                            'recommendations': [
                                'Profile code for performance bottlenecks',
                                'Implement parallel processing where possible',
                                'Optimize data access patterns'
                            ]
                        })
            
            # Sort by priority
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            opportunities.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            return opportunities
            
        except Exception as e:
            self.logger.error("Optimization opportunity identification failed: %s", str(e))
            return []
    
    async def _calculate_overall_performance_score(self, snapshots: List[PerformanceSnapshot]) -> float:
        """Calculate overall performance score for the session."""
        try:
            if not snapshots:
                return 0.0
            
            # Calculate weighted average of all metrics
            effectiveness_scores = [s.effectiveness_score for s in snapshots]
            execution_times = [s.execution_time_ms for s in snapshots]
            success_rates = [s.success_rate for s in snapshots]
            
            # Normalize execution times (lower is better)
            if execution_times:
                max_time = max(execution_times)
                normalized_times = [1.0 - (t / max_time) if max_time > 0 else 1.0 for t in execution_times]
            else:
                normalized_times = [1.0]
            
            # Calculate weighted score
            weights = {
                'effectiveness': 0.4,
                'performance': 0.3,
                'reliability': 0.3
            }
            
            avg_effectiveness = statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0
            avg_performance = statistics.mean(normalized_times) if normalized_times else 0.0
            avg_reliability = statistics.mean(success_rates) if success_rates else 0.0
            
            overall_score = (
                avg_effectiveness * weights['effectiveness'] +
                avg_performance * weights['performance'] +
                avg_reliability * weights['reliability']
            )
            
            return min(1.0, max(0.0, overall_score))
            
        except Exception as e:
            self.logger.error("Overall performance score calculation failed: %s", str(e))
            return 0.0
    
    async def _store_analysis_results(self, session_id: str, analysis_results: Dict[str, Any]) -> None:
        """Store performance analysis results in database."""
        try:
            # Store as performance analysis record
            await self.database_overlay.store_performance_analysis(
                session_id=session_id,
                component_type='session_analysis',
                analysis_type='comprehensive_performance',
                baseline_metrics={},
                current_metrics=analysis_results,
                improvement_percentage=0.0,  # Would need historical data to calculate
                optimization_suggestions=[
                    opp['description'] for opp in analysis_results.get('optimization_opportunities', [])
                ],
                priority_level=1,  # High priority for comprehensive analysis
                analyst_agent='PerformanceAnalyzer'
            )
            
        except Exception as e:
            self.logger.error("Failed to store analysis results: %s", str(e))

