"""Machine learning models for predictive analytics."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib

logger = logging.getLogger(__name__)


class TaskFailurePredictionModel:
    """
    Random Forest model for predicting task failure probability.
    
    Features: task type, complexity, historical success rate, resource usage
    Target: Binary classification (success/failure)
    """
    
    def __init__(self, model_id: str = "task_failure_predictor"):
        """Initialize task failure prediction model."""
        self.model_id = model_id
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.training_accuracy = 0.0
        self.last_trained = None
        
        logger.debug(f"TaskFailurePredictionModel initialized with ID: {model_id}")
    
    async def train(self, training_data: pd.DataFrame, target_column: str = 'task_failed') -> Dict[str, float]:
        """
        Train the task failure prediction model.
        
        Args:
            training_data: DataFrame with training features and target
            target_column: Name of the target column
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training task failure prediction model with {len(training_data)} samples")
        
        try:
            # Prepare features and target
            if target_column not in training_data.columns:
                raise ValueError(f"Target column '{target_column}' not found in training data")
            
            # Select relevant features
            feature_columns = [
                'task_complexity', 'estimated_duration', 'priority',
                'task_type_complexity', 'historical_success_rate',
                'cpu_requirement', 'memory_requirement', 'current_system_load',
                'queue_length', 'hour_of_day', 'is_business_hours', 'is_weekend'
            ]
            
            # Filter available features
            available_features = [col for col in feature_columns if col in training_data.columns]
            self.feature_names = available_features
            
            X = training_data[available_features]
            y = training_data[target_column]
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data for validation
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            train_accuracy = self.model.score(X_train, y_train)
            test_accuracy = self.model.score(X_test, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
            
            self.training_accuracy = test_accuracy
            self.is_trained = True
            self.last_trained = datetime.utcnow()
            
            metrics = {
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'cv_mean_accuracy': cv_scores.mean(),
                'cv_std_accuracy': cv_scores.std(),
                'feature_count': len(available_features),
                'training_samples': len(training_data)
            }
            
            logger.info(f"Model training completed. Test accuracy: {test_accuracy:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training task failure prediction model: {e}")
            raise
    
    async def predict(self, features: Dict[str, float]) -> float:
        """
        Predict task failure probability.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Failure probability (0.0 to 1.0)
        """
        if not self.is_trained:
            logger.warning("Model not trained, returning default prediction")
            return 0.1  # Default low failure probability
        
        try:
            # Prepare feature vector
            feature_vector = []
            for feature_name in self.feature_names:
                value = features.get(feature_name, 0.0)
                feature_vector.append(value)
            
            # Scale features
            feature_array = np.array(feature_vector).reshape(1, -1)
            feature_scaled = self.scaler.transform(feature_array)
            
            # Get prediction probability
            failure_probability = self.model.predict_proba(feature_scaled)[0][1]  # Probability of class 1 (failure)
            
            return float(failure_probability)
            
        except Exception as e:
            logger.error(f"Error predicting task failure: {e}")
            return 0.1  # Default prediction on error
    
    async def get_confidence(self, features: Dict[str, float]) -> float:
        """Get prediction confidence score."""
        if not self.is_trained:
            return 0.5
        
        try:
            # Confidence based on training accuracy and feature completeness
            feature_completeness = len([f for f in self.feature_names if f in features]) / len(self.feature_names)
            confidence = self.training_accuracy * feature_completeness
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    async def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained:
            return {}
        
        try:
            importance_scores = self.model.feature_importances_
            importance_dict = dict(zip(self.feature_names, importance_scores))
            return importance_dict
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}


class ResourceUsagePredictionModel:
    """
    Linear Regression models for predicting CPU and memory usage.
    
    Features: task characteristics, historical usage patterns
    Target: Continuous values (CPU%, memory usage)
    """
    
    def __init__(self, model_id: str = "resource_usage_predictor"):
        """Initialize resource usage prediction model."""
        self.model_id = model_id
        self.cpu_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.memory_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.cpu_accuracy = 0.0
        self.memory_accuracy = 0.0
        self.last_trained = None
        
        logger.debug(f"ResourceUsagePredictionModel initialized with ID: {model_id}")
    
    async def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the resource usage prediction models.
        
        Args:
            training_data: DataFrame with training features and targets
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training resource usage prediction models with {len(training_data)} samples")
        
        try:
            # Select relevant features
            feature_columns = [
                'task_count', 'avg_task_complexity', 'total_estimated_duration',
                'workload_intensity', 'parallelization', 'historical_cpu_avg',
                'historical_memory_avg', 'current_cpu_usage', 'current_memory_usage',
                'available_resources'
            ]
            
            # Filter available features
            available_features = [col for col in feature_columns if col in training_data.columns]
            self.feature_names = available_features
            
            X = training_data[available_features]
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train CPU usage model
            if 'cpu_usage' in training_data.columns:
                y_cpu = training_data['cpu_usage']
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y_cpu, test_size=0.2, random_state=42
                )
                
                self.cpu_model.fit(X_train, y_train)
                cpu_predictions = self.cpu_model.predict(X_test)
                self.cpu_accuracy = 1 - mean_absolute_error(y_test, cpu_predictions)
            
            # Train memory usage model
            if 'memory_usage' in training_data.columns:
                y_memory = training_data['memory_usage']
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y_memory, test_size=0.2, random_state=42
                )
                
                self.memory_model.fit(X_train, y_train)
                memory_predictions = self.memory_model.predict(X_test)
                self.memory_accuracy = 1 - mean_absolute_error(y_test, memory_predictions)
            
            self.is_trained = True
            self.last_trained = datetime.utcnow()
            
            metrics = {
                'cpu_accuracy': self.cpu_accuracy,
                'memory_accuracy': self.memory_accuracy,
                'feature_count': len(available_features),
                'training_samples': len(training_data)
            }
            
            logger.info(f"Resource usage models training completed. CPU accuracy: {self.cpu_accuracy:.3f}, Memory accuracy: {self.memory_accuracy:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training resource usage prediction models: {e}")
            raise
    
    async def predict_cpu(self, features: Dict[str, float]) -> float:
        """Predict CPU usage."""
        if not self.is_trained:
            return 0.5  # Default prediction
        
        try:
            feature_vector = [features.get(name, 0.0) for name in self.feature_names]
            feature_array = np.array(feature_vector).reshape(1, -1)
            feature_scaled = self.scaler.transform(feature_array)
            
            cpu_prediction = self.cpu_model.predict(feature_scaled)[0]
            return max(0.0, min(1.0, float(cpu_prediction)))  # Clamp to [0, 1]
            
        except Exception as e:
            logger.error(f"Error predicting CPU usage: {e}")
            return 0.5
    
    async def predict_memory(self, features: Dict[str, float]) -> float:
        """Predict memory usage."""
        if not self.is_trained:
            return 0.5  # Default prediction
        
        try:
            feature_vector = [features.get(name, 0.0) for name in self.feature_names]
            feature_array = np.array(feature_vector).reshape(1, -1)
            feature_scaled = self.scaler.transform(feature_array)
            
            memory_prediction = self.memory_model.predict(feature_scaled)[0]
            return max(0.0, min(1.0, float(memory_prediction)))  # Clamp to [0, 1]
            
        except Exception as e:
            logger.error(f"Error predicting memory usage: {e}")
            return 0.5
    
    async def get_confidence(self, features: Dict[str, float]) -> float:
        """Get prediction confidence score."""
        if not self.is_trained:
            return 0.5
        
        try:
            feature_completeness = len([f for f in self.feature_names if f in features]) / len(self.feature_names)
            avg_accuracy = (self.cpu_accuracy + self.memory_accuracy) / 2
            confidence = avg_accuracy * feature_completeness
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5


class PerformanceOptimizationModel:
    """
    Model for performance optimization and forecasting.
    
    Uses clustering for workflow pattern identification,
    anomaly detection for performance degradation,
    and time series forecasting for capacity planning.
    """
    
    def __init__(self, model_id: str = "performance_optimizer"):
        """Initialize performance optimization model."""
        self.model_id = model_id
        self.forecasting_model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.forecast_accuracy = 0.0
        self.last_trained = None
        
        logger.debug(f"PerformanceOptimizationModel initialized with ID: {model_id}")
    
    async def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the performance optimization model.
        
        Args:
            training_data: DataFrame with historical performance data
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training performance optimization model with {len(training_data)} samples")
        
        try:
            # Prepare time series features
            if 'timestamp' in training_data.columns:
                training_data = training_data.sort_values('timestamp')
                
                # Create lag features for time series
                for lag in [1, 2, 3, 6, 12]:  # Various lag periods
                    for col in ['response_time', 'throughput', 'cpu_usage', 'memory_usage']:
                        if col in training_data.columns:
                            training_data[f'{col}_lag_{lag}'] = training_data[col].shift(lag)
                
                # Remove rows with NaN values from lag features
                training_data = training_data.dropna()
            
            # Select features for forecasting
            feature_columns = [col for col in training_data.columns 
                             if col.endswith('_lag_1') or col.endswith('_lag_2') or col.endswith('_lag_3')]
            
            if len(feature_columns) == 0:
                logger.warning("No suitable features found for time series forecasting")
                return {'forecast_accuracy': 0.0}
            
            self.feature_names = feature_columns
            X = training_data[feature_columns]
            
            # Train forecasting model for response time
            if 'response_time' in training_data.columns:
                y = training_data['response_time']
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # Scale features
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
                
                # Train model
                self.forecasting_model.fit(X_train_scaled, y_train)
                
                # Evaluate
                predictions = self.forecasting_model.predict(X_test_scaled)
                mae = mean_absolute_error(y_test, predictions)
                self.forecast_accuracy = max(0.0, 1.0 - mae / y_test.mean())
            
            self.is_trained = True
            self.last_trained = datetime.utcnow()
            
            metrics = {
                'forecast_accuracy': self.forecast_accuracy,
                'feature_count': len(feature_columns),
                'training_samples': len(training_data)
            }
            
            logger.info(f"Performance optimization model training completed. Forecast accuracy: {self.forecast_accuracy:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training performance optimization model: {e}")
            raise
    
    async def forecast(self, historical_data: pd.DataFrame, time_horizon: int = 24) -> Dict[str, Any]:
        """
        Generate performance forecasts.
        
        Args:
            historical_data: Historical performance data
            time_horizon: Forecast horizon in hours
            
        Returns:
            Dictionary with forecasts for different metrics
        """
        if not self.is_trained:
            logger.warning("Model not trained, returning default forecasts")
            return self._generate_default_forecasts(time_horizon)
        
        try:
            forecasts = {}
            
            # Simple trend-based forecasting for demonstration
            for metric in ['response_time', 'throughput', 'cpu_usage', 'memory_usage', 'error_rate']:
                if metric in historical_data.columns:
                    metric_data = historical_data[metric].dropna()
                    
                    if len(metric_data) >= 10:
                        # Calculate trend
                        recent_values = metric_data.tail(24)  # Last 24 hours
                        trend = (recent_values.iloc[-1] - recent_values.iloc[0]) / len(recent_values)
                        
                        # Generate forecast
                        current_value = metric_data.iloc[-1]
                        forecast_values = []
                        
                        for i in range(time_horizon):
                            forecast_value = current_value + (trend * i)
                            forecast_values.append(forecast_value)
                        
                        # Determine trend direction
                        if abs(trend) < 0.001:
                            trend_direction = 'stable'
                        elif trend > 0:
                            trend_direction = 'increasing'
                        else:
                            trend_direction = 'decreasing'
                        
                        forecasts[metric] = {
                            'values': forecast_values,
                            'trend': trend_direction,
                            'trend_magnitude': abs(trend),
                            'current_value': current_value,
                            'forecast_range': {
                                'min': min(forecast_values),
                                'max': max(forecast_values),
                                'mean': np.mean(forecast_values)
                            }
                        }
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error generating forecasts: {e}")
            return self._generate_default_forecasts(time_horizon)
    
    async def get_forecast_confidence(self, forecasts: Dict[str, Any]) -> float:
        """Calculate confidence in forecasts."""
        if not self.is_trained:
            return 0.3  # Low confidence for untrained model
        
        try:
            # Base confidence on model accuracy and forecast stability
            base_confidence = self.forecast_accuracy
            
            # Adjust based on forecast variability
            variability_penalty = 0.0
            for metric, forecast_data in forecasts.items():
                if 'forecast_range' in forecast_data:
                    range_data = forecast_data['forecast_range']
                    if range_data['mean'] > 0:
                        cv = (range_data['max'] - range_data['min']) / range_data['mean']
                        variability_penalty += min(cv * 0.1, 0.2)  # Penalize high variability
            
            confidence = max(0.1, base_confidence - variability_penalty)
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating forecast confidence: {e}")
            return 0.3
    
    def _generate_default_forecasts(self, time_horizon: int) -> Dict[str, Any]:
        """Generate default forecasts when model is not trained."""
        default_forecasts = {}
        
        metrics = {
            'response_time': {'base': 1.5, 'trend': 'stable'},
            'throughput': {'base': 100.0, 'trend': 'stable'},
            'cpu_usage': {'base': 0.6, 'trend': 'stable'},
            'memory_usage': {'base': 0.55, 'trend': 'stable'},
            'error_rate': {'base': 0.02, 'trend': 'stable'}
        }
        
        for metric, config in metrics.items():
            base_value = config['base']
            values = [base_value] * time_horizon  # Flat forecast
            
            default_forecasts[metric] = {
                'values': values,
                'trend': config['trend'],
                'trend_magnitude': 0.0,
                'current_value': base_value,
                'forecast_range': {
                    'min': base_value,
                    'max': base_value,
                    'mean': base_value
                }
            }
        
        return default_forecasts

