"""
Outcome Correlation Analyzer

Analyzes correlations between expected outcomes and actual effectiveness scores.
"""

import asyncio
import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple
import json
import math

from ..database.overlay import DatabaseOverlay


class OutcomeCorrelationAnalyzer:
    """
    Analyzes correlations between expected outcomes and actual effectiveness.
    
    Provides statistical analysis of how well component effectiveness scores
    correlate with expected outcomes and business objectives.
    """
    
    def __init__(self, database_overlay: DatabaseOverlay):
        """Initialize the correlation analyzer."""
        self.database_overlay = database_overlay
        self.logger = logging.getLogger(__name__)
    
    async def analyze_correlations(
        self,
        session_id: str,
        component_type: str,
        effectiveness_scores: Dict[str, float],
        evaluation_data: List[Dict[str, Any]],
        expected_outcomes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze correlations between effectiveness scores and outcomes.
        
        Args:
            session_id: Evaluation session ID
            component_type: Type of component being analyzed
            effectiveness_scores: Dictionary of effectiveness scores by dimension
            evaluation_data: List of evaluation data points
            expected_outcomes: Expected outcomes for comparison
            
        Returns:
            Dictionary containing correlation analysis results
        """
        try:
            self.logger.info("Starting correlation analysis for %s", component_type)
            
            # Prepare data for analysis
            analysis_data = await self._prepare_analysis_data(
                effectiveness_scores, evaluation_data, expected_outcomes
            )
            
            # Perform statistical correlation analysis
            correlation_results = await self._calculate_correlations(analysis_data)
            
            # Analyze effectiveness impact
            effectiveness_impact = await self._analyze_effectiveness_impact(
                effectiveness_scores, analysis_data
            )
            
            # Generate correlation insights
            insights = await self._generate_correlation_insights(
                correlation_results, effectiveness_impact
            )
            
            # Compile final results
            final_results = {
                'correlation_score': correlation_results.get('overall_correlation', 0.0),
                'effectiveness_impact': effectiveness_impact,
                'statistical_measures': correlation_results,
                'insights': insights,
                'analysis_method': 'statistical_correlation',
                'confidence_level': correlation_results.get('confidence_level', 0.5),
                'expected_outcome': expected_outcomes or {},
                'actual_outcome': {
                    'effectiveness_scores': effectiveness_scores,
                    'evaluation_summary': self._summarize_evaluation_data(evaluation_data)
                }
            }
            
            self.logger.info("Correlation analysis completed: correlation=%.4f", 
                           final_results['correlation_score'])
            
            return final_results
            
        except Exception as e:
            self.logger.error("Correlation analysis failed: %s", str(e))
            return {
                'correlation_score': 0.0,
                'effectiveness_impact': 0.0,
                'error': str(e),
                'analysis_method': 'failed',
                'confidence_level': 0.0
            }
    
    async def _prepare_analysis_data(
        self,
        effectiveness_scores: Dict[str, float],
        evaluation_data: List[Dict[str, Any]],
        expected_outcomes: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare data for correlation analysis."""
        try:
            # Extract numerical values from evaluation data
            numerical_outcomes = []
            categorical_outcomes = []
            
            for data_point in evaluation_data:
                # Extract numerical metrics
                if 'score' in data_point:
                    numerical_outcomes.append(data_point['score'])
                elif 'result' in data_point and isinstance(data_point['result'], (int, float)):
                    numerical_outcomes.append(data_point['result'])
                elif 'success' in data_point:
                    numerical_outcomes.append(1.0 if data_point['success'] else 0.0)
                
                # Extract categorical outcomes
                if 'category' in data_point:
                    categorical_outcomes.append(data_point['category'])
                elif 'status' in data_point:
                    categorical_outcomes.append(data_point['status'])
            
            # Prepare expected vs actual comparison
            expected_metrics = {}
            actual_metrics = {}
            
            if expected_outcomes:
                # Extract expected numerical values
                for key, value in expected_outcomes.items():
                    if isinstance(value, (int, float)):
                        expected_metrics[key] = value
                    elif isinstance(value, dict) and 'target' in value:
                        expected_metrics[key] = value['target']
            
            # Map effectiveness scores to expected metrics
            for dimension, score in effectiveness_scores.items():
                actual_metrics[dimension] = score
                
                # If no expected outcome specified, use reasonable defaults
                if dimension not in expected_metrics:
                    expected_metrics[dimension] = 0.75  # Default expectation
            
            return {
                'effectiveness_scores': effectiveness_scores,
                'numerical_outcomes': numerical_outcomes,
                'categorical_outcomes': categorical_outcomes,
                'expected_metrics': expected_metrics,
                'actual_metrics': actual_metrics,
                'evaluation_count': len(evaluation_data)
            }
            
        except Exception as e:
            self.logger.error("Failed to prepare analysis data: %s", str(e))
            return {
                'effectiveness_scores': effectiveness_scores,
                'numerical_outcomes': [],
                'categorical_outcomes': [],
                'expected_metrics': {},
                'actual_metrics': {},
                'evaluation_count': 0
            }
    
    async def _calculate_correlations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical correlations."""
        try:
            results = {}
            
            # Calculate Pearson correlation between expected and actual metrics
            expected_values = list(analysis_data['expected_metrics'].values())
            actual_values = list(analysis_data['actual_metrics'].values())
            
            if len(expected_values) >= 2 and len(actual_values) >= 2:
                correlation = self._pearson_correlation(expected_values, actual_values)
                results['pearson_correlation'] = correlation
            else:
                results['pearson_correlation'] = 0.0
            
            # Calculate effectiveness consistency
            effectiveness_scores = list(analysis_data['effectiveness_scores'].values())
            if len(effectiveness_scores) > 1:
                effectiveness_variance = statistics.variance(effectiveness_scores)
                consistency_score = max(0.0, 1.0 - effectiveness_variance)
                results['effectiveness_consistency'] = consistency_score
            else:
                results['effectiveness_consistency'] = 1.0
            
            # Calculate outcome alignment
            numerical_outcomes = analysis_data['numerical_outcomes']
            if numerical_outcomes and effectiveness_scores:
                # Correlate numerical outcomes with average effectiveness
                avg_effectiveness = statistics.mean(effectiveness_scores)
                avg_outcome = statistics.mean(numerical_outcomes)
                
                # Simple alignment score based on both being above/below 0.5
                alignment_score = 1.0 if (avg_effectiveness > 0.5) == (avg_outcome > 0.5) else 0.0
                results['outcome_alignment'] = alignment_score
            else:
                results['outcome_alignment'] = 0.5
            
            # Calculate overall correlation score
            correlation_components = [
                results.get('pearson_correlation', 0.0),
                results.get('effectiveness_consistency', 0.0),
                results.get('outcome_alignment', 0.0)
            ]
            
            # Weighted average
            weights = [0.5, 0.3, 0.2]
            overall_correlation = sum(comp * weight for comp, weight in zip(correlation_components, weights))
            results['overall_correlation'] = overall_correlation
            
            # Calculate confidence level based on data quantity and consistency
            data_count = analysis_data['evaluation_count']
            confidence = min(0.95, 0.3 + (data_count / 50.0))  # Increase confidence with more data
            
            # Adjust confidence based on consistency
            if results['effectiveness_consistency'] < 0.5:
                confidence *= 0.7  # Reduce confidence for inconsistent results
            
            results['confidence_level'] = confidence
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to calculate correlations: %s", str(e))
            return {
                'overall_correlation': 0.0,
                'confidence_level': 0.1,
                'error': str(e)
            }
    
    def _pearson_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        try:
            if len(x_values) != len(y_values) or len(x_values) < 2:
                return 0.0
            
            n = len(x_values)
            
            # Calculate means
            mean_x = statistics.mean(x_values)
            mean_y = statistics.mean(y_values)
            
            # Calculate correlation coefficient
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
            
            sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
            sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
            
            denominator = math.sqrt(sum_sq_x * sum_sq_y)
            
            if denominator == 0:
                return 0.0
            
            correlation = numerator / denominator
            return max(-1.0, min(1.0, correlation))  # Clamp to [-1, 1]
            
        except Exception as e:
            self.logger.warning("Pearson correlation calculation failed: %s", str(e))
            return 0.0
    
    async def _analyze_effectiveness_impact(
        self,
        effectiveness_scores: Dict[str, float],
        analysis_data: Dict[str, Any]
    ) -> float:
        """Analyze the impact of effectiveness on outcomes."""
        try:
            # Calculate average effectiveness
            avg_effectiveness = statistics.mean(effectiveness_scores.values()) if effectiveness_scores else 0.0
            
            # Analyze impact based on numerical outcomes
            numerical_outcomes = analysis_data['numerical_outcomes']
            if numerical_outcomes:
                avg_outcome = statistics.mean(numerical_outcomes)
                
                # Impact is how much effectiveness correlates with positive outcomes
                if avg_effectiveness > 0.5 and avg_outcome > 0.5:
                    impact = min(1.0, avg_effectiveness * avg_outcome)
                elif avg_effectiveness <= 0.5 and avg_outcome <= 0.5:
                    impact = min(1.0, (1 - avg_effectiveness) * (1 - avg_outcome))
                else:
                    impact = abs(avg_effectiveness - avg_outcome)
            else:
                # If no numerical outcomes, base impact on effectiveness alone
                impact = avg_effectiveness
            
            return impact
            
        except Exception as e:
            self.logger.error("Failed to analyze effectiveness impact: %s", str(e))
            return 0.0
    
    async def _generate_correlation_insights(
        self,
        correlation_results: Dict[str, Any],
        effectiveness_impact: float
    ) -> List[str]:
        """Generate insights from correlation analysis."""
        try:
            insights = []
            
            overall_correlation = correlation_results.get('overall_correlation', 0.0)
            confidence_level = correlation_results.get('confidence_level', 0.0)
            
            # Correlation strength insights
            if overall_correlation > 0.8:
                insights.append("Strong positive correlation between effectiveness and outcomes.")
            elif overall_correlation > 0.6:
                insights.append("Moderate positive correlation between effectiveness and outcomes.")
            elif overall_correlation > 0.4:
                insights.append("Weak positive correlation between effectiveness and outcomes.")
            elif overall_correlation > -0.4:
                insights.append("Little to no correlation between effectiveness and outcomes.")
            else:
                insights.append("Negative correlation detected - effectiveness may not align with outcomes.")
            
            # Effectiveness impact insights
            if effectiveness_impact > 0.8:
                insights.append("High effectiveness impact - component performance strongly influences outcomes.")
            elif effectiveness_impact > 0.6:
                insights.append("Moderate effectiveness impact on outcomes.")
            elif effectiveness_impact > 0.4:
                insights.append("Low effectiveness impact - outcomes may be influenced by other factors.")
            else:
                insights.append("Minimal effectiveness impact detected.")
            
            # Confidence insights
            if confidence_level < 0.5:
                insights.append("Low confidence in correlation analysis - consider collecting more data.")
            elif confidence_level < 0.7:
                insights.append("Moderate confidence in correlation analysis.")
            else:
                insights.append("High confidence in correlation analysis results.")
            
            # Consistency insights
            consistency = correlation_results.get('effectiveness_consistency', 0.0)
            if consistency < 0.5:
                insights.append("Inconsistent effectiveness scores detected - component behavior may be unstable.")
            elif consistency > 0.8:
                insights.append("Highly consistent effectiveness scores indicate stable component behavior.")
            
            # Actionable recommendations
            if overall_correlation < 0.5:
                insights.append("Consider reviewing component evaluation criteria or expected outcomes.")
            
            if effectiveness_impact < 0.5:
                insights.append("Component effectiveness may not be the primary driver of outcomes.")
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to generate correlation insights: %s", str(e))
            return ["Error generating insights from correlation analysis."]
    
    def _summarize_evaluation_data(self, evaluation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize evaluation data for outcome comparison."""
        try:
            if not evaluation_data:
                return {'no_data': True}
            
            summary = {
                'total_evaluations': len(evaluation_data),
                'data_types': set(),
                'numerical_summary': {},
                'categorical_summary': {}
            }
            
            # Analyze data types and extract summaries
            numerical_values = []
            categorical_values = []
            success_count = 0
            
            for data_point in evaluation_data:
                # Track data types
                for key, value in data_point.items():
                    summary['data_types'].add(type(value).__name__)
                
                # Extract numerical values
                if 'score' in data_point and isinstance(data_point['score'], (int, float)):
                    numerical_values.append(data_point['score'])
                elif 'result' in data_point and isinstance(data_point['result'], (int, float)):
                    numerical_values.append(data_point['result'])
                
                # Track success/failure
                if 'success' in data_point:
                    if data_point['success']:
                        success_count += 1
                elif 'status' in data_point:
                    if data_point['status'] in ['success', 'passed', 'completed']:
                        success_count += 1
                
                # Extract categorical values
                if 'category' in data_point:
                    categorical_values.append(data_point['category'])
                elif 'status' in data_point:
                    categorical_values.append(data_point['status'])
            
            # Numerical summary
            if numerical_values:
                summary['numerical_summary'] = {
                    'count': len(numerical_values),
                    'average': statistics.mean(numerical_values),
                    'min': min(numerical_values),
                    'max': max(numerical_values),
                    'variance': statistics.variance(numerical_values) if len(numerical_values) > 1 else 0.0
                }
            
            # Categorical summary
            if categorical_values:
                from collections import Counter
                category_counts = Counter(categorical_values)
                summary['categorical_summary'] = {
                    'unique_categories': len(category_counts),
                    'most_common': category_counts.most_common(3),
                    'distribution': dict(category_counts)
                }
            
            # Success rate
            summary['success_rate'] = success_count / len(evaluation_data)
            summary['data_types'] = list(summary['data_types'])
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to summarize evaluation data: %s", str(e))
            return {'error': str(e)}

