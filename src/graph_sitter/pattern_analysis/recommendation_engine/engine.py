"""Recommendation engine for generating optimization recommendations."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from ..models import OptimizationRecommendation, RecommendationType, Pattern
from ..config import RecommendationConfig
from .optimizers import (
    ConfigurationOptimizer,
    WorkflowOptimizer,
    ResourceOptimizer,
    PerformanceOptimizer
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Recommendation engine for generating optimization recommendations.
    
    This engine analyzes patterns and system state to generate:
    - Configuration tuning recommendations
    - Workflow improvement suggestions
    - Resource optimization recommendations
    - Performance enhancement suggestions
    """
    
    def __init__(self, config: Optional[RecommendationConfig] = None):
        """
        Initialize recommendation engine.
        
        Args:
            config: Configuration for recommendation generation
        """
        self.config = config or RecommendationConfig()
        
        # Initialize optimizers
        self.configuration_optimizer = ConfigurationOptimizer()
        self.workflow_optimizer = WorkflowOptimizer()
        self.resource_optimizer = ResourceOptimizer()
        self.performance_optimizer = PerformanceOptimizer()
        
        # Recommendation cache
        self.recommendation_cache = {}
        self.cache_ttl = self.config.generation_interval
        
        logger.info("RecommendationEngine initialized")
    
    async def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Generate system optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        logger.info("Generating optimization recommendations")
        
        try:
            all_recommendations = []
            
            # Generate recommendations from different optimizers
            optimization_tasks = [
                self._generate_configuration_recommendations(),
                self._generate_workflow_recommendations(),
                self._generate_resource_recommendations(),
                self._generate_performance_recommendations(),
            ]
            
            results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
            
            # Combine results from all optimizers
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Optimization task {i} failed: {result}")
                    continue
                if result:
                    all_recommendations.extend(result)
            
            # Filter and prioritize recommendations
            filtered_recommendations = await self._filter_recommendations(all_recommendations)
            prioritized_recommendations = await self._prioritize_recommendations(filtered_recommendations)
            
            # Limit to max recommendations
            final_recommendations = prioritized_recommendations[:self.config.max_recommendations]
            
            logger.info(f"Generated {len(final_recommendations)} optimization recommendations")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return []
    
    async def suggest_workflow_improvements(self, workflow_id: str) -> List[OptimizationRecommendation]:
        """
        Suggest workflow optimization for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow to optimize
            
        Returns:
            List of workflow improvement recommendations
        """
        logger.info(f"Generating workflow improvements for workflow: {workflow_id}")
        
        try:
            # Get workflow-specific data
            workflow_data = await self._get_workflow_data(workflow_id)
            
            # Generate workflow-specific recommendations
            recommendations = await self.workflow_optimizer.optimize_workflow(workflow_data)
            
            # Filter by confidence threshold
            filtered_recommendations = [
                rec for rec in recommendations 
                if self._calculate_recommendation_confidence(rec) >= self.config.min_confidence
            ]
            
            logger.info(f"Generated {len(filtered_recommendations)} workflow improvement recommendations")
            return filtered_recommendations
            
        except Exception as e:
            logger.error(f"Error generating workflow improvements: {e}")
            return []
    
    async def recommend_configuration_changes(self) -> List[OptimizationRecommendation]:
        """
        Recommend configuration tuning changes.
        
        Returns:
            List of configuration recommendations
        """
        logger.info("Generating configuration change recommendations")
        
        try:
            # Get current system configuration
            current_config = await self._get_current_configuration()
            
            # Get system performance metrics
            performance_metrics = await self._get_performance_metrics()
            
            # Generate configuration recommendations
            recommendations = await self.configuration_optimizer.optimize_configuration(
                current_config, performance_metrics
            )
            
            # Filter by confidence and impact
            filtered_recommendations = [
                rec for rec in recommendations 
                if (self._calculate_recommendation_confidence(rec) >= self.config.min_confidence and
                    rec.priority_score >= 0.5)
            ]
            
            logger.info(f"Generated {len(filtered_recommendations)} configuration recommendations")
            return filtered_recommendations
            
        except Exception as e:
            logger.error(f"Error generating configuration recommendations: {e}")
            return []
    
    async def generate_pattern_based_recommendations(self, patterns: List[Pattern]) -> List[OptimizationRecommendation]:
        """
        Generate recommendations based on detected patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            List of pattern-based recommendations
        """
        logger.info(f"Generating recommendations based on {len(patterns)} patterns")
        
        try:
            recommendations = []
            
            for pattern in patterns:
                pattern_recommendations = await self._generate_pattern_recommendations(pattern)
                recommendations.extend(pattern_recommendations)
            
            # Remove duplicates and prioritize
            unique_recommendations = await self._deduplicate_recommendations(recommendations)
            prioritized_recommendations = await self._prioritize_recommendations(unique_recommendations)
            
            logger.info(f"Generated {len(prioritized_recommendations)} pattern-based recommendations")
            return prioritized_recommendations
            
        except Exception as e:
            logger.error(f"Error generating pattern-based recommendations: {e}")
            return []
    
    async def _generate_configuration_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate configuration optimization recommendations."""
        try:
            current_config = await self._get_current_configuration()
            performance_metrics = await self._get_performance_metrics()
            
            recommendations = await self.configuration_optimizer.optimize_configuration(
                current_config, performance_metrics
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating configuration recommendations: {e}")
            return []
    
    async def _generate_workflow_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate workflow optimization recommendations."""
        try:
            workflow_data = await self._get_all_workflows_data()
            recommendations = await self.workflow_optimizer.optimize_workflows(workflow_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating workflow recommendations: {e}")
            return []
    
    async def _generate_resource_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate resource optimization recommendations."""
        try:
            resource_data = await self._get_resource_usage_data()
            recommendations = await self.resource_optimizer.optimize_resources(resource_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating resource recommendations: {e}")
            return []
    
    async def _generate_performance_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate performance optimization recommendations."""
        try:
            performance_data = await self._get_performance_metrics()
            recommendations = await self.performance_optimizer.optimize_performance(performance_data)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating performance recommendations: {e}")
            return []
    
    async def _generate_pattern_recommendations(self, pattern: Pattern) -> List[OptimizationRecommendation]:
        """Generate recommendations based on a specific pattern."""
        recommendations = []
        
        try:
            pattern_type = pattern.pattern_type
            pattern_data = pattern.pattern_data
            
            if pattern_type.value == "task_performance":
                # Task performance pattern recommendations
                if pattern_data.get('pattern_name') == 'slow_tasks':
                    recommendation = OptimizationRecommendation(
                        id="",
                        recommendation_type=RecommendationType.PERFORMANCE_ENHANCEMENT,
                        target_component="task_execution",
                        recommendation_data={
                            'action': 'optimize_slow_tasks',
                            'description': 'Optimize slow task execution patterns',
                            'specific_actions': [
                                'Increase task timeout thresholds',
                                'Implement task parallelization',
                                'Add task complexity-based routing'
                            ],
                            'pattern_id': pattern.id
                        },
                        expected_impact={
                            'performance_improvement': 0.2,
                            'duration_reduction': 0.15,
                            'success_rate_improvement': 0.05
                        },
                        priority_score=pattern.significance_score * 0.8
                    )
                    recommendations.append(recommendation)
            
            elif pattern_type.value == "resource_usage":
                # Resource usage pattern recommendations
                if pattern_data.get('pattern_name') == 'high_cpu_usage':
                    recommendation = OptimizationRecommendation(
                        id="",
                        recommendation_type=RecommendationType.RESOURCE_OPTIMIZATION,
                        target_component="resource_management",
                        recommendation_data={
                            'action': 'optimize_cpu_usage',
                            'description': 'Optimize high CPU usage patterns',
                            'specific_actions': [
                                'Implement CPU throttling',
                                'Add load balancing',
                                'Optimize CPU-intensive algorithms'
                            ],
                            'pattern_id': pattern.id
                        },
                        expected_impact={
                            'cpu_reduction': 0.2,
                            'system_stability': 0.15,
                            'cost_savings': 0.1
                        },
                        priority_score=pattern.significance_score * 0.9
                    )
                    recommendations.append(recommendation)
            
            elif pattern_type.value == "error_frequency":
                # Error pattern recommendations
                recommendation = OptimizationRecommendation(
                    id="",
                    recommendation_type=RecommendationType.ERROR_PREVENTION,
                    target_component="error_handling",
                    recommendation_data={
                        'action': 'improve_error_handling',
                        'description': 'Improve error handling and prevention',
                        'specific_actions': [
                            'Add better input validation',
                            'Implement retry mechanisms',
                            'Add error monitoring and alerting'
                        ],
                        'pattern_id': pattern.id
                    },
                    expected_impact={
                        'error_reduction': 0.3,
                        'reliability_improvement': 0.25,
                        'user_experience': 0.2
                    },
                    priority_score=pattern.significance_score * 1.0  # High priority for errors
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating pattern recommendations: {e}")
            return []
    
    async def _filter_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Filter recommendations by confidence and relevance."""
        filtered = []
        
        for recommendation in recommendations:
            confidence = self._calculate_recommendation_confidence(recommendation)
            
            if confidence >= self.config.min_confidence:
                filtered.append(recommendation)
        
        return filtered
    
    async def _prioritize_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Prioritize recommendations by impact and feasibility."""
        # Sort by priority score (descending)
        prioritized = sorted(recommendations, key=lambda r: r.priority_score, reverse=True)
        return prioritized
    
    async def _deduplicate_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Remove duplicate recommendations."""
        seen_actions = set()
        unique_recommendations = []
        
        for recommendation in recommendations:
            action_key = (
                recommendation.recommendation_type.value,
                recommendation.target_component,
                recommendation.recommendation_data.get('action', '')
            )
            
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                unique_recommendations.append(recommendation)
        
        return unique_recommendations
    
    def _calculate_recommendation_confidence(self, recommendation: OptimizationRecommendation) -> float:
        """Calculate confidence score for a recommendation."""
        try:
            # Base confidence from priority score
            base_confidence = recommendation.priority_score
            
            # Adjust based on expected impact
            impact_values = list(recommendation.expected_impact.values())
            if impact_values:
                avg_impact = sum(impact_values) / len(impact_values)
                impact_confidence = min(avg_impact * 2, 1.0)  # Scale impact to confidence
            else:
                impact_confidence = 0.5
            
            # Combine confidence factors
            confidence = (base_confidence + impact_confidence) / 2
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating recommendation confidence: {e}")
            return 0.5
    
    async def _get_current_configuration(self) -> Dict[str, Any]:
        """Get current system configuration."""
        # Mock implementation - replace with actual configuration retrieval
        return {
            'task_timeout': 300,
            'max_concurrent_tasks': 10,
            'cpu_limit': 0.8,
            'memory_limit': 0.8,
            'retry_attempts': 3,
            'batch_size': 100
        }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        # Mock implementation - replace with actual metrics retrieval
        return {
            'avg_response_time': 1.5,
            'throughput': 150.0,
            'error_rate': 0.02,
            'cpu_usage': 0.65,
            'memory_usage': 0.72,
            'success_rate': 0.98
        }
    
    async def _get_workflow_data(self, workflow_id: str) -> Dict[str, Any]:
        """Get data for a specific workflow."""
        # Mock implementation - replace with actual workflow data retrieval
        return {
            'workflow_id': workflow_id,
            'avg_execution_time': 120.0,
            'step_count': 5,
            'success_rate': 0.95,
            'bottlenecks': ['step_3', 'step_5'],
            'resource_usage': {'cpu': 0.6, 'memory': 0.5}
        }
    
    async def _get_all_workflows_data(self) -> List[Dict[str, Any]]:
        """Get data for all workflows."""
        # Mock implementation - replace with actual workflows data retrieval
        return [
            await self._get_workflow_data('workflow_1'),
            await self._get_workflow_data('workflow_2'),
            await self._get_workflow_data('workflow_3')
        ]
    
    async def _get_resource_usage_data(self) -> Dict[str, Any]:
        """Get current resource usage data."""
        # Mock implementation - replace with actual resource data retrieval
        return {
            'cpu_usage': 0.65,
            'memory_usage': 0.72,
            'disk_usage': 0.45,
            'network_io': 0.3,
            'resource_efficiency': 0.75,
            'peak_usage_times': ['09:00', '14:00', '18:00']
        }

