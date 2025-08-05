"""
Effectiveness Evaluation Engine

Core engine for evaluating component effectiveness using OpenEvolve agents
and tracking performance metrics.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..database.overlay import DatabaseOverlay
from ..openevolve.config import OpenEvolveConfig
from .metrics import EffectivenessMetrics, PerformanceMetrics
from .correlations import OutcomeCorrelationAnalyzer


@dataclass
class EvaluationContext:
    """Context for component evaluation."""
    session_id: str
    component_type: str
    component_name: str
    evaluation_parameters: Dict[str, Any]
    baseline_metrics: Optional[Dict[str, Any]] = None
    expected_outcomes: Optional[Dict[str, Any]] = None


@dataclass
class EffectivenessResult:
    """Result of effectiveness evaluation."""
    overall_effectiveness: float
    component_scores: Dict[str, float]
    performance_metrics: PerformanceMetrics
    correlation_analysis: Dict[str, Any]
    optimization_recommendations: List[str]
    confidence_level: float


class EffectivenessEvaluator:
    """
    Core effectiveness evaluation engine.
    
    Evaluates component effectiveness using OpenEvolve agents and provides
    comprehensive analysis of performance, outcomes, and optimization opportunities.
    """
    
    def __init__(self, database_overlay: DatabaseOverlay, config: OpenEvolveConfig):
        """Initialize the effectiveness evaluator."""
        self.database_overlay = database_overlay
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self.correlation_analyzer = OutcomeCorrelationAnalyzer(database_overlay)
        
        # Evaluation state
        self.evaluation_history: Dict[str, List[float]] = {}
        self.baseline_metrics: Dict[str, Dict[str, Any]] = {}
    
    async def evaluate_effectiveness(
        self,
        context: EvaluationContext,
        component_instance: Any,
        evaluation_data: List[Dict[str, Any]]
    ) -> EffectivenessResult:
        """
        Evaluate the effectiveness of a component.
        
        Args:
            context: Evaluation context with session and component info
            component_instance: The component instance to evaluate
            evaluation_data: Data for evaluation (test cases, scenarios, etc.)
            
        Returns:
            EffectivenessResult with comprehensive analysis
        """
        start_time = time.time()
        
        try:
            self.logger.info("Starting effectiveness evaluation for %s", context.component_name)
            
            # Step 1: Collect baseline metrics if not provided
            if context.baseline_metrics is None:
                context.baseline_metrics = await self._collect_baseline_metrics(
                    context, component_instance
                )
            
            # Step 2: Run component evaluations
            component_scores = await self._evaluate_component_performance(
                context, component_instance, evaluation_data
            )
            
            # Step 3: Analyze performance metrics
            performance_metrics = await self._analyze_performance_metrics(
                context, component_scores
            )
            
            # Step 4: Perform correlation analysis
            correlation_analysis = await self._perform_correlation_analysis(
                context, component_scores, evaluation_data
            )
            
            # Step 5: Generate optimization recommendations
            optimization_recommendations = await self._generate_optimization_recommendations(
                context, component_scores, performance_metrics, correlation_analysis
            )
            
            # Step 6: Calculate overall effectiveness
            overall_effectiveness = await self._calculate_overall_effectiveness(
                component_scores, performance_metrics, correlation_analysis
            )
            
            # Step 7: Calculate confidence level
            confidence_level = await self._calculate_confidence_level(
                component_scores, len(evaluation_data)
            )
            
            # Store results in database
            await self._store_evaluation_results(
                context, overall_effectiveness, component_scores, 
                performance_metrics, correlation_analysis
            )
            
            evaluation_time = time.time() - start_time
            self.logger.info(
                "Effectiveness evaluation completed for %s: %.4f (%.2fs)",
                context.component_name, overall_effectiveness, evaluation_time
            )
            
            return EffectivenessResult(
                overall_effectiveness=overall_effectiveness,
                component_scores=component_scores,
                performance_metrics=performance_metrics,
                correlation_analysis=correlation_analysis,
                optimization_recommendations=optimization_recommendations,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            self.logger.error("Effectiveness evaluation failed: %s", str(e))
            raise
    
    async def _collect_baseline_metrics(
        self, 
        context: EvaluationContext, 
        component_instance: Any
    ) -> Dict[str, Any]:
        """Collect baseline performance metrics for the component."""
        try:
            baseline_metrics = {}
            
            # Basic component metrics
            baseline_metrics['component_type'] = type(component_instance).__name__
            baseline_metrics['method_count'] = len([m for m in dir(component_instance) if not m.startswith('_')])
            baseline_metrics['has_documentation'] = hasattr(component_instance, '__doc__') and bool(component_instance.__doc__)
            
            # Performance baseline
            start_time = time.time()
            
            # Try to measure basic operations if possible
            if hasattr(component_instance, '__call__'):
                try:
                    # Measure call overhead
                    call_start = time.time()
                    # Don't actually call with real data, just measure overhead
                    call_time = time.time() - call_start
                    baseline_metrics['call_overhead_ms'] = call_time * 1000
                except:
                    baseline_metrics['call_overhead_ms'] = 0
            
            baseline_metrics['baseline_collection_time_ms'] = (time.time() - start_time) * 1000
            baseline_metrics['timestamp'] = time.time()
            
            # Store baseline in instance cache
            cache_key = f"{context.component_type}:{context.component_name}"
            self.baseline_metrics[cache_key] = baseline_metrics
            
            return baseline_metrics
            
        except Exception as e:
            self.logger.warning("Failed to collect baseline metrics: %s", str(e))
            return {'error': str(e), 'timestamp': time.time()}
    
    async def _evaluate_component_performance(
        self,
        context: EvaluationContext,
        component_instance: Any,
        evaluation_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate component performance across multiple dimensions."""
        try:
            scores = {}
            
            # Functionality score
            scores['functionality'] = await self._evaluate_functionality(
                component_instance, evaluation_data
            )
            
            # Reliability score
            scores['reliability'] = await self._evaluate_reliability(
                component_instance, evaluation_data
            )
            
            # Performance score
            scores['performance'] = await self._evaluate_performance(
                component_instance, evaluation_data
            )
            
            # Usability score
            scores['usability'] = await self._evaluate_usability(
                component_instance, evaluation_data
            )
            
            # Maintainability score
            scores['maintainability'] = await self._evaluate_maintainability(
                component_instance
            )
            
            # Update evaluation history
            cache_key = f"{context.component_type}:{context.component_name}"
            if cache_key not in self.evaluation_history:
                self.evaluation_history[cache_key] = []
            
            overall_score = statistics.mean(scores.values())
            self.evaluation_history[cache_key].append(overall_score)
            
            # Keep only recent history
            if len(self.evaluation_history[cache_key]) > self.config.correlation_analysis_window:
                self.evaluation_history[cache_key] = self.evaluation_history[cache_key][-self.config.correlation_analysis_window:]
            
            return scores
            
        except Exception as e:
            self.logger.error("Component performance evaluation failed: %s", str(e))
            return {'error': 0.0}
    
    async def _evaluate_functionality(
        self, 
        component_instance: Any, 
        evaluation_data: List[Dict[str, Any]]
    ) -> float:
        """Evaluate component functionality."""
        try:
            functionality_score = 0.5  # Base score
            
            # Check for expected methods based on component type
            expected_methods = {
                'evaluator': ['evaluate', 'assess', 'analyze', 'score'],
                'database': ['save', 'get', 'query', 'update', 'delete'],
                'controller': ['control', 'manage', 'execute', 'coordinate']
            }
            
            # Determine component type heuristically
            component_type = 'unknown'
            class_name = type(component_instance).__name__.lower()
            
            if 'evaluat' in class_name:
                component_type = 'evaluator'
            elif 'database' in class_name or 'db' in class_name:
                component_type = 'database'
            elif 'control' in class_name or 'manager' in class_name:
                component_type = 'controller'
            
            # Check for expected methods
            if component_type in expected_methods:
                methods = expected_methods[component_type]
                has_methods = sum(1 for method in methods if hasattr(component_instance, method))
                functionality_score += (has_methods / len(methods)) * 0.4
            
            # Check if component is callable
            if callable(component_instance):
                functionality_score += 0.1
            
            return min(1.0, functionality_score)
            
        except Exception as e:
            self.logger.warning("Functionality evaluation failed: %s", str(e))
            return 0.3
    
    async def _evaluate_reliability(
        self, 
        component_instance: Any, 
        evaluation_data: List[Dict[str, Any]]
    ) -> float:
        """Evaluate component reliability."""
        try:
            reliability_score = 0.5  # Base score
            
            # Check for error handling patterns
            error_handling_methods = ['validate', 'check', 'verify', 'handle_error']
            has_error_handling = any(hasattr(component_instance, method) for method in error_handling_methods)
            
            if has_error_handling:
                reliability_score += 0.3
            
            # Check for state management
            if hasattr(component_instance, '__dict__') and component_instance.__dict__:
                reliability_score += 0.1
            
            # Check for documentation
            if hasattr(component_instance, '__doc__') and component_instance.__doc__:
                reliability_score += 0.1
            
            return min(1.0, reliability_score)
            
        except Exception as e:
            self.logger.warning("Reliability evaluation failed: %s", str(e))
            return 0.3
    
    async def _evaluate_performance(
        self, 
        component_instance: Any, 
        evaluation_data: List[Dict[str, Any]]
    ) -> float:
        """Evaluate component performance characteristics."""
        try:
            performance_score = 0.5  # Base score
            
            # Measure instantiation time
            start_time = time.time()
            try:
                # Create a new instance to measure instantiation
                instance_type = type(component_instance)
                test_instance = instance_type()
                instantiation_time = time.time() - start_time
                
                # Score based on instantiation speed (faster is better)
                if instantiation_time < 0.001:  # < 1ms
                    performance_score += 0.3
                elif instantiation_time < 0.01:  # < 10ms
                    performance_score += 0.2
                elif instantiation_time < 0.1:  # < 100ms
                    performance_score += 0.1
                
            except:
                # If we can't instantiate, assume reasonable performance
                performance_score += 0.15
            
            # Check for optimization features
            optimization_methods = ['cache', 'optimize', 'index', 'batch']
            has_optimization = any(hasattr(component_instance, method) for method in optimization_methods)
            
            if has_optimization:
                performance_score += 0.2
            
            return min(1.0, performance_score)
            
        except Exception as e:
            self.logger.warning("Performance evaluation failed: %s", str(e))
            return 0.3
    
    async def _evaluate_usability(
        self, 
        component_instance: Any, 
        evaluation_data: List[Dict[str, Any]]
    ) -> float:
        """Evaluate component usability."""
        try:
            usability_score = 0.5  # Base score
            
            # Check for clear interface
            public_methods = [m for m in dir(component_instance) if not m.startswith('_')]
            
            # Score based on interface complexity (simpler is better for usability)
            if len(public_methods) <= 5:
                usability_score += 0.2
            elif len(public_methods) <= 10:
                usability_score += 0.1
            
            # Check for documentation
            if hasattr(component_instance, '__doc__') and component_instance.__doc__:
                usability_score += 0.2
            
            # Check for standard method names
            standard_methods = ['__str__', '__repr__', '__init__']
            has_standard = sum(1 for method in standard_methods if hasattr(component_instance, method))
            usability_score += (has_standard / len(standard_methods)) * 0.1
            
            return min(1.0, usability_score)
            
        except Exception as e:
            self.logger.warning("Usability evaluation failed: %s", str(e))
            return 0.3
    
    async def _evaluate_maintainability(self, component_instance: Any) -> float:
        """Evaluate component maintainability."""
        try:
            maintainability_score = 0.5  # Base score
            
            # Check for documentation
            if hasattr(component_instance, '__doc__') and component_instance.__doc__:
                maintainability_score += 0.2
            
            # Check for reasonable complexity
            method_count = len([m for m in dir(component_instance) if not m.startswith('_')])
            if method_count <= 10:  # Not too complex
                maintainability_score += 0.2
            elif method_count <= 20:
                maintainability_score += 0.1
            
            # Check for standard patterns
            if hasattr(component_instance, '__init__'):
                maintainability_score += 0.1
            
            return min(1.0, maintainability_score)
            
        except Exception as e:
            self.logger.warning("Maintainability evaluation failed: %s", str(e))
            return 0.3
    
    async def _analyze_performance_metrics(
        self, 
        context: EvaluationContext, 
        component_scores: Dict[str, float]
    ) -> PerformanceMetrics:
        """Analyze performance metrics from component scores."""
        try:
            # Calculate aggregate metrics
            avg_score = statistics.mean(component_scores.values()) if component_scores else 0.0
            score_variance = statistics.variance(component_scores.values()) if len(component_scores) > 1 else 0.0
            
            # Get historical data for trend analysis
            cache_key = f"{context.component_type}:{context.component_name}"
            historical_scores = self.evaluation_history.get(cache_key, [])
            
            # Calculate trend
            trend = 0.0
            if len(historical_scores) >= 2:
                recent_avg = statistics.mean(historical_scores[-3:]) if len(historical_scores) >= 3 else historical_scores[-1]
                older_avg = statistics.mean(historical_scores[:-3]) if len(historical_scores) > 3 else historical_scores[0]
                trend = recent_avg - older_avg
            
            return PerformanceMetrics(
                average_effectiveness=avg_score,
                score_variance=score_variance,
                trend_direction=trend,
                evaluation_count=len(historical_scores),
                consistency_score=max(0.0, 1.0 - score_variance),
                improvement_rate=max(0.0, trend)
            )
            
        except Exception as e:
            self.logger.error("Performance metrics analysis failed: %s", str(e))
            return PerformanceMetrics()
    
    async def _perform_correlation_analysis(
        self,
        context: EvaluationContext,
        component_scores: Dict[str, float],
        evaluation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform outcome vs effectiveness correlation analysis."""
        try:
            # Use the correlation analyzer
            correlation_results = await self.correlation_analyzer.analyze_correlations(
                session_id=context.session_id,
                component_type=context.component_type,
                effectiveness_scores=component_scores,
                evaluation_data=evaluation_data,
                expected_outcomes=context.expected_outcomes
            )
            
            return correlation_results
            
        except Exception as e:
            self.logger.error("Correlation analysis failed: %s", str(e))
            return {'error': str(e), 'correlation_score': 0.0}
    
    async def _generate_optimization_recommendations(
        self,
        context: EvaluationContext,
        component_scores: Dict[str, float],
        performance_metrics: PerformanceMetrics,
        correlation_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        try:
            recommendations = []
            
            # Performance-based recommendations
            if performance_metrics.average_effectiveness < self.config.effectiveness_threshold:
                recommendations.append(
                    f"Overall effectiveness ({performance_metrics.average_effectiveness:.3f}) "
                    f"is below threshold ({self.config.effectiveness_threshold}). "
                    "Consider reviewing component implementation."
                )
            
            # Score-specific recommendations
            for dimension, score in component_scores.items():
                if score < 0.6:
                    recommendations.append(
                        f"Low {dimension} score ({score:.3f}). "
                        f"Consider improving {dimension}-related features."
                    )
            
            # Variance-based recommendations
            if performance_metrics.score_variance > 0.1:
                recommendations.append(
                    f"High score variance ({performance_metrics.score_variance:.3f}) "
                    "indicates inconsistent performance. Consider stabilizing the component."
                )
            
            # Trend-based recommendations
            if performance_metrics.trend_direction < -0.05:
                recommendations.append(
                    "Negative performance trend detected. "
                    "Consider investigating recent changes or degradation causes."
                )
            
            # Correlation-based recommendations
            correlation_score = correlation_analysis.get('correlation_score', 0.0)
            if correlation_score < 0.5:
                recommendations.append(
                    f"Low outcome correlation ({correlation_score:.3f}). "
                    "Component effectiveness may not align with expected outcomes."
                )
            
            # Default recommendation if no issues found
            if not recommendations:
                recommendations.append(
                    "Component performance is within acceptable ranges. "
                    "Consider monitoring for continued stability."
                )
            
            return recommendations
            
        except Exception as e:
            self.logger.error("Failed to generate optimization recommendations: %s", str(e))
            return ["Error generating recommendations. Manual review recommended."]
    
    async def _calculate_overall_effectiveness(
        self,
        component_scores: Dict[str, float],
        performance_metrics: PerformanceMetrics,
        correlation_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall effectiveness score."""
        try:
            if not component_scores:
                return 0.0
            
            # Weighted average of component scores
            base_effectiveness = statistics.mean(component_scores.values())
            
            # Adjust based on consistency
            consistency_factor = performance_metrics.consistency_score
            
            # Adjust based on correlation
            correlation_factor = correlation_analysis.get('correlation_score', 0.5)
            
            # Calculate weighted effectiveness
            overall_effectiveness = (
                base_effectiveness * 0.6 +
                consistency_factor * 0.2 +
                correlation_factor * 0.2
            )
            
            return min(1.0, max(0.0, overall_effectiveness))
            
        except Exception as e:
            self.logger.error("Failed to calculate overall effectiveness: %s", str(e))
            return 0.0
    
    async def _calculate_confidence_level(
        self, 
        component_scores: Dict[str, float], 
        data_points: int
    ) -> float:
        """Calculate confidence level for the evaluation."""
        try:
            # Base confidence on number of data points and score consistency
            base_confidence = min(0.95, 0.5 + (data_points / 100.0))
            
            # Adjust based on score variance
            if len(component_scores) > 1:
                score_variance = statistics.variance(component_scores.values())
                variance_penalty = min(0.3, score_variance * 2)
                base_confidence -= variance_penalty
            
            return max(0.1, base_confidence)
            
        except Exception as e:
            self.logger.error("Failed to calculate confidence level: %s", str(e))
            return 0.5
    
    async def _store_evaluation_results(
        self,
        context: EvaluationContext,
        overall_effectiveness: float,
        component_scores: Dict[str, float],
        performance_metrics: PerformanceMetrics,
        correlation_analysis: Dict[str, Any]
    ) -> None:
        """Store evaluation results in database."""
        try:
            # Store component evaluation
            await self.database_overlay.store_component_evaluation(
                session_id=context.session_id,
                component_type=context.component_type,
                component_name=context.component_name,
                effectiveness_score=overall_effectiveness,
                performance_metrics={
                    'component_scores': component_scores,
                    'average_effectiveness': performance_metrics.average_effectiveness,
                    'score_variance': performance_metrics.score_variance,
                    'trend_direction': performance_metrics.trend_direction,
                    'consistency_score': performance_metrics.consistency_score
                },
                execution_time_ms=0,  # Will be set by caller
                success_rate=1.0 if overall_effectiveness > 0 else 0.0,
                error_count=0
            )
            
            # Store correlation analysis
            if correlation_analysis and 'expected_outcome' in correlation_analysis:
                await self.database_overlay.store_outcome_correlation(
                    session_id=context.session_id,
                    component_type=context.component_type,
                    expected_outcome=correlation_analysis.get('expected_outcome', {}),
                    actual_outcome=correlation_analysis.get('actual_outcome', {}),
                    correlation_score=correlation_analysis.get('correlation_score', 0.0),
                    effectiveness_impact=correlation_analysis.get('effectiveness_impact', 0.0),
                    analysis_method=correlation_analysis.get('analysis_method', 'statistical'),
                    confidence_level=correlation_analysis.get('confidence_level', 0.95)
                )
            
        except Exception as e:
            self.logger.error("Failed to store evaluation results: %s", str(e))

