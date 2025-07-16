"""Predictive analytics service for forecasting and early warning systems."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..models import Prediction, MLModel, ModelType
from ..config import PatternAnalysisConfig
from .models import (
    TaskFailurePredictionModel,
    ResourceUsagePredictionModel,
    PerformanceOptimizationModel
)

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """
    Predictive analytics service for forecasting system behavior and generating early warnings.
    
    This service provides:
    - Task failure probability prediction
    - Resource usage forecasting
    - Performance optimization recommendations
    - Early warning system for potential issues
    """
    
    def __init__(self, config: Optional[PatternAnalysisConfig] = None):
        """
        Initialize predictive analytics service.
        
        Args:
            config: Configuration for pattern analysis
        """
        self.config = config or PatternAnalysisConfig()
        
        # Initialize prediction models
        self.task_failure_model = TaskFailurePredictionModel()
        self.resource_usage_model = ResourceUsagePredictionModel()
        self.performance_model = PerformanceOptimizationModel()
        
        # Model cache for performance
        self.model_cache = {}
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        logger.info("PredictiveAnalyticsService initialized")
    
    async def predict_task_failure(self, task_context: Dict[str, Any]) -> Prediction:
        """
        Predict probability of task failure based on context.
        
        Args:
            task_context: Dictionary containing task information
            
        Returns:
            Prediction object with failure probability
        """
        logger.debug(f"Predicting task failure for context: {task_context.get('task_type', 'unknown')}")
        
        try:
            # Extract features from task context
            features = await self._extract_task_features(task_context)
            
            # Get prediction from model
            failure_probability = await self.task_failure_model.predict(features)
            
            # Create prediction object
            prediction = Prediction(
                id="",
                model_id=self.task_failure_model.model_id,
                prediction_type="task_failure",
                input_data=task_context,
                prediction_result={
                    'failure_probability': failure_probability,
                    'success_probability': 1 - failure_probability,
                    'risk_level': self._get_risk_level(failure_probability),
                    'confidence': await self.task_failure_model.get_confidence(features)
                },
                confidence_score=await self.task_failure_model.get_confidence(features)
            )
            
            logger.debug(f"Task failure prediction: {failure_probability:.3f} probability")
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting task failure: {e}")
            raise
    
    async def predict_resource_usage(self, workload: Dict[str, Any]) -> Prediction:
        """
        Predict resource requirements for a given workload.
        
        Args:
            workload: Dictionary containing workload information
            
        Returns:
            Prediction object with resource usage forecast
        """
        logger.debug(f"Predicting resource usage for workload: {workload.get('workload_type', 'unknown')}")
        
        try:
            # Extract features from workload
            features = await self._extract_workload_features(workload)
            
            # Get predictions for different resources
            cpu_prediction = await self.resource_usage_model.predict_cpu(features)
            memory_prediction = await self.resource_usage_model.predict_memory(features)
            
            # Create prediction object
            prediction = Prediction(
                id="",
                model_id=self.resource_usage_model.model_id,
                prediction_type="resource_usage",
                input_data=workload,
                prediction_result={
                    'cpu_usage': cpu_prediction,
                    'memory_usage': memory_prediction,
                    'total_resource_score': (cpu_prediction + memory_prediction) / 2,
                    'resource_efficiency': await self._calculate_efficiency_score(cpu_prediction, memory_prediction),
                    'recommendations': await self._generate_resource_recommendations(cpu_prediction, memory_prediction)
                },
                confidence_score=await self.resource_usage_model.get_confidence(features)
            )
            
            logger.debug(f"Resource usage prediction: CPU={cpu_prediction:.3f}, Memory={memory_prediction:.3f}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting resource usage: {e}")
            raise
    
    async def generate_early_warnings(self) -> List[Dict[str, Any]]:
        """
        Generate early warning alerts for potential issues.
        
        Returns:
            List of early warning alerts
        """
        logger.info("Generating early warning alerts")
        
        try:
            warnings = []
            
            # Check for high failure probability trends
            failure_warnings = await self._check_failure_trends()
            warnings.extend(failure_warnings)
            
            # Check for resource exhaustion risks
            resource_warnings = await self._check_resource_risks()
            warnings.extend(resource_warnings)
            
            # Check for performance degradation
            performance_warnings = await self._check_performance_degradation()
            warnings.extend(performance_warnings)
            
            # Check for anomaly patterns
            anomaly_warnings = await self._check_anomaly_patterns()
            warnings.extend(anomaly_warnings)
            
            logger.info(f"Generated {len(warnings)} early warning alerts")
            return warnings
            
        except Exception as e:
            logger.error(f"Error generating early warnings: {e}")
            return []
    
    async def forecast_performance(self, time_horizon: int = 24) -> Dict[str, Any]:
        """
        Forecast system performance for the next time period.
        
        Args:
            time_horizon: Forecast horizon in hours
            
        Returns:
            Dictionary with performance forecasts
        """
        logger.info(f"Forecasting performance for next {time_horizon} hours")
        
        try:
            # Get historical performance data
            historical_data = await self._get_historical_performance_data()
            
            # Generate forecasts
            forecasts = await self.performance_model.forecast(historical_data, time_horizon)
            
            # Calculate forecast confidence
            confidence = await self.performance_model.get_forecast_confidence(forecasts)
            
            forecast_result = {
                'time_horizon_hours': time_horizon,
                'forecasts': forecasts,
                'confidence': confidence,
                'generated_at': datetime.utcnow().isoformat(),
                'key_insights': await self._extract_forecast_insights(forecasts)
            }
            
            logger.info("Performance forecast generated successfully")
            return forecast_result
            
        except Exception as e:
            logger.error(f"Error forecasting performance: {e}")
            return {}
    
    async def _extract_task_features(self, task_context: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from task context."""
        features = {}
        
        try:
            # Basic task features
            features['task_complexity'] = task_context.get('complexity_score', 0.5)
            features['estimated_duration'] = task_context.get('estimated_duration', 60.0)
            features['priority'] = task_context.get('priority', 0.5)
            
            # Task type encoding
            task_type = task_context.get('task_type', 'unknown')
            type_encoding = {
                'analysis': 0.3,
                'transformation': 0.6,
                'validation': 0.2,
                'optimization': 0.8,
                'generation': 0.9
            }
            features['task_type_complexity'] = type_encoding.get(task_type, 0.5)
            
            # Historical success rate for this task type
            features['historical_success_rate'] = task_context.get('historical_success_rate', 0.9)
            
            # Resource requirements
            features['cpu_requirement'] = task_context.get('cpu_requirement', 0.5)
            features['memory_requirement'] = task_context.get('memory_requirement', 0.5)
            
            # System context
            features['current_system_load'] = task_context.get('current_system_load', 0.5)
            features['queue_length'] = task_context.get('queue_length', 0.0)
            
            # Time-based features
            current_hour = datetime.utcnow().hour
            features['hour_of_day'] = current_hour / 24.0
            features['is_business_hours'] = 1.0 if 9 <= current_hour <= 17 else 0.0
            features['is_weekend'] = 1.0 if datetime.utcnow().weekday() >= 5 else 0.0
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting task features: {e}")
            return {'default_feature': 0.5}
    
    async def _extract_workload_features(self, workload: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from workload context."""
        features = {}
        
        try:
            # Workload characteristics
            features['task_count'] = workload.get('task_count', 1.0)
            features['avg_task_complexity'] = workload.get('avg_task_complexity', 0.5)
            features['total_estimated_duration'] = workload.get('total_estimated_duration', 300.0)
            
            # Workload type encoding
            workload_type = workload.get('workload_type', 'mixed')
            type_multipliers = {
                'cpu_intensive': 1.5,
                'memory_intensive': 1.2,
                'io_intensive': 0.8,
                'mixed': 1.0,
                'lightweight': 0.6
            }
            features['workload_intensity'] = type_multipliers.get(workload_type, 1.0)
            
            # Parallelization factor
            features['parallelization'] = workload.get('parallelization_factor', 1.0)
            
            # Historical resource usage patterns
            features['historical_cpu_avg'] = workload.get('historical_cpu_avg', 0.5)
            features['historical_memory_avg'] = workload.get('historical_memory_avg', 0.5)
            
            # Current system state
            features['current_cpu_usage'] = workload.get('current_cpu_usage', 0.5)
            features['current_memory_usage'] = workload.get('current_memory_usage', 0.5)
            features['available_resources'] = workload.get('available_resources', 0.8)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting workload features: {e}")
            return {'default_feature': 0.5}
    
    def _get_risk_level(self, failure_probability: float) -> str:
        """Determine risk level based on failure probability."""
        if failure_probability < 0.1:
            return 'low'
        elif failure_probability < 0.3:
            return 'medium'
        elif failure_probability < 0.6:
            return 'high'
        else:
            return 'critical'
    
    async def _calculate_efficiency_score(self, cpu_usage: float, memory_usage: float) -> float:
        """Calculate resource efficiency score."""
        try:
            # Efficiency is higher when resources are balanced and not over-utilized
            balance_score = 1.0 - abs(cpu_usage - memory_usage)
            utilization_score = 1.0 - max(cpu_usage, memory_usage)
            
            efficiency = (balance_score + utilization_score) / 2
            return max(0.0, min(1.0, efficiency))
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {e}")
            return 0.5
    
    async def _generate_resource_recommendations(self, cpu_usage: float, memory_usage: float) -> List[str]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        try:
            if cpu_usage > 0.8:
                recommendations.append("Consider CPU optimization or scaling")
            
            if memory_usage > 0.8:
                recommendations.append("Consider memory optimization or scaling")
            
            if abs(cpu_usage - memory_usage) > 0.3:
                recommendations.append("Resource usage is imbalanced - consider workload redistribution")
            
            if cpu_usage < 0.3 and memory_usage < 0.3:
                recommendations.append("Resources are under-utilized - consider consolidation")
            
            if not recommendations:
                recommendations.append("Resource usage is optimal")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating resource recommendations: {e}")
            return ["Unable to generate recommendations"]
    
    async def _check_failure_trends(self) -> List[Dict[str, Any]]:
        """Check for increasing failure probability trends."""
        warnings = []
        
        try:
            # Mock implementation - replace with actual trend analysis
            # This would analyze recent predictions and look for increasing failure rates
            
            # Simulate a warning condition
            current_failure_rate = 0.15  # 15% failure rate
            if current_failure_rate > 0.1:
                warnings.append({
                    'type': 'failure_trend',
                    'severity': 'medium',
                    'message': f'Task failure rate trending upward: {current_failure_rate:.1%}',
                    'details': {
                        'current_rate': current_failure_rate,
                        'threshold': 0.1,
                        'trend': 'increasing'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error checking failure trends: {e}")
            return []
    
    async def _check_resource_risks(self) -> List[Dict[str, Any]]:
        """Check for resource exhaustion risks."""
        warnings = []
        
        try:
            # Mock implementation - replace with actual resource monitoring
            current_cpu = 0.85  # 85% CPU usage
            current_memory = 0.78  # 78% memory usage
            
            if current_cpu > 0.8:
                warnings.append({
                    'type': 'resource_risk',
                    'severity': 'high',
                    'message': f'High CPU usage detected: {current_cpu:.1%}',
                    'details': {
                        'resource': 'cpu',
                        'current_usage': current_cpu,
                        'threshold': 0.8,
                        'risk_level': 'high'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            if current_memory > 0.8:
                warnings.append({
                    'type': 'resource_risk',
                    'severity': 'medium',
                    'message': f'High memory usage detected: {current_memory:.1%}',
                    'details': {
                        'resource': 'memory',
                        'current_usage': current_memory,
                        'threshold': 0.8,
                        'risk_level': 'medium'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error checking resource risks: {e}")
            return []
    
    async def _check_performance_degradation(self) -> List[Dict[str, Any]]:
        """Check for performance degradation patterns."""
        warnings = []
        
        try:
            # Mock implementation - replace with actual performance monitoring
            avg_response_time = 2.5  # seconds
            throughput_decline = 0.15  # 15% decline
            
            if avg_response_time > 2.0:
                warnings.append({
                    'type': 'performance_degradation',
                    'severity': 'medium',
                    'message': f'Response time degradation: {avg_response_time:.1f}s average',
                    'details': {
                        'metric': 'response_time',
                        'current_value': avg_response_time,
                        'threshold': 2.0,
                        'degradation': 'response_time'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            if throughput_decline > 0.1:
                warnings.append({
                    'type': 'performance_degradation',
                    'severity': 'medium',
                    'message': f'Throughput decline detected: {throughput_decline:.1%}',
                    'details': {
                        'metric': 'throughput',
                        'decline_rate': throughput_decline,
                        'threshold': 0.1,
                        'degradation': 'throughput'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error checking performance degradation: {e}")
            return []
    
    async def _check_anomaly_patterns(self) -> List[Dict[str, Any]]:
        """Check for anomalous behavior patterns."""
        warnings = []
        
        try:
            # Mock implementation - replace with actual anomaly detection
            anomaly_score = 0.75  # High anomaly score
            
            if anomaly_score > 0.7:
                warnings.append({
                    'type': 'anomaly_detection',
                    'severity': 'high',
                    'message': f'Anomalous behavior detected: score {anomaly_score:.2f}',
                    'details': {
                        'anomaly_score': anomaly_score,
                        'threshold': 0.7,
                        'pattern_type': 'behavioral_anomaly'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error checking anomaly patterns: {e}")
            return []
    
    async def _get_historical_performance_data(self) -> pd.DataFrame:
        """Get historical performance data for forecasting."""
        try:
            # Mock implementation - replace with actual data retrieval
            dates = pd.date_range(start=datetime.utcnow() - timedelta(days=30), 
                                 end=datetime.utcnow(), freq='H')
            
            # Generate synthetic performance data
            np.random.seed(42)
            data = {
                'timestamp': dates,
                'response_time': np.random.normal(1.5, 0.3, len(dates)),
                'throughput': np.random.normal(100, 15, len(dates)),
                'cpu_usage': np.random.normal(0.6, 0.15, len(dates)),
                'memory_usage': np.random.normal(0.55, 0.12, len(dates)),
                'error_rate': np.random.exponential(0.02, len(dates))
            }
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error getting historical performance data: {e}")
            return pd.DataFrame()
    
    async def _extract_forecast_insights(self, forecasts: Dict[str, Any]) -> List[str]:
        """Extract key insights from performance forecasts."""
        insights = []
        
        try:
            # Analyze forecast trends and generate insights
            if 'response_time' in forecasts:
                response_trend = forecasts['response_time'].get('trend', 'stable')
                if response_trend == 'increasing':
                    insights.append("Response times are expected to increase")
                elif response_trend == 'decreasing':
                    insights.append("Response times are expected to improve")
            
            if 'throughput' in forecasts:
                throughput_trend = forecasts['throughput'].get('trend', 'stable')
                if throughput_trend == 'decreasing':
                    insights.append("Throughput is expected to decline")
                elif throughput_trend == 'increasing':
                    insights.append("Throughput is expected to improve")
            
            if 'error_rate' in forecasts:
                error_trend = forecasts['error_rate'].get('trend', 'stable')
                if error_trend == 'increasing':
                    insights.append("Error rates are expected to increase")
            
            if not insights:
                insights.append("System performance is expected to remain stable")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting forecast insights: {e}")
            return ["Unable to generate insights"]

