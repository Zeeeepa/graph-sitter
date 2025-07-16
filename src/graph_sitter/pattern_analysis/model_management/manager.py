"""Model manager for ML model training and lifecycle management."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import joblib
import os
from pathlib import Path

from ..models import MLModel, ModelType, ModelPerformanceMetrics
from ..config import MLModelConfig
from ..predictive_analytics.models import (
    TaskFailurePredictionModel,
    ResourceUsagePredictionModel,
    PerformanceOptimizationModel
)
from .trainer import ModelTrainer
from .evaluator import ModelEvaluator

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Model manager for ML model training and lifecycle management.
    
    This manager handles:
    - Model training and retraining
    - Model evaluation and performance monitoring
    - Model deployment and versioning
    - Model persistence and loading
    """
    
    def __init__(self, config: Optional[MLModelConfig] = None, model_storage_path: str = "./models"):
        """
        Initialize model manager.
        
        Args:
            config: Configuration for ML models
            model_storage_path: Path to store model files
        """
        self.config = config or MLModelConfig()
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.trainer = ModelTrainer(self.config)
        self.evaluator = ModelEvaluator()
        
        # Model registry
        self.models = {}
        self.model_metadata = {}
        
        # Performance tracking
        self.performance_history = {}
        
        logger.info(f"ModelManager initialized with storage path: {model_storage_path}")
    
    async def train_models(self, training_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Train and update ML models.
        
        Args:
            training_data: DataFrame with training data
            
        Returns:
            Dictionary with training results for each model
        """
        logger.info(f"Training models with {len(training_data)} samples")
        
        try:
            training_results = {}
            
            # Check if we have enough data for training
            if len(training_data) < self.config.min_training_samples:
                logger.warning(f"Insufficient training data: {len(training_data)} < {self.config.min_training_samples}")
                return {}
            
            # Train task failure prediction model
            task_failure_results = await self._train_task_failure_model(training_data)
            training_results['task_failure'] = task_failure_results
            
            # Train resource usage prediction model
            resource_usage_results = await self._train_resource_usage_model(training_data)
            training_results['resource_usage'] = resource_usage_results
            
            # Train performance optimization model
            performance_results = await self._train_performance_model(training_data)
            training_results['performance'] = performance_results
            
            # Update training timestamp
            self._update_training_timestamp()
            
            logger.info("Model training completed successfully")
            return training_results
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            raise
    
    async def evaluate_model_performance(self, model_id: str) -> ModelPerformanceMetrics:
        """
        Evaluate model accuracy and performance.
        
        Args:
            model_id: ID of the model to evaluate
            
        Returns:
            Model performance metrics
        """
        logger.info(f"Evaluating performance for model: {model_id}")
        
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            
            # Get evaluation data
            evaluation_data = await self._get_evaluation_data(model_id)
            
            if evaluation_data.empty:
                logger.warning(f"No evaluation data available for model {model_id}")
                return self._create_default_metrics(model_id)
            
            # Evaluate model
            metrics = await self.evaluator.evaluate_model(model, evaluation_data)
            
            # Store performance history
            self._store_performance_metrics(model_id, metrics)
            
            logger.info(f"Model evaluation completed for {model_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model {model_id}: {e}")
            raise
    
    async def deploy_model(self, model: MLModel) -> bool:
        """
        Deploy trained model to production.
        
        Args:
            model: ML model to deploy
            
        Returns:
            True if deployment successful, False otherwise
        """
        logger.info(f"Deploying model: {model.model_name}")
        
        try:
            # Validate model before deployment
            if not await self._validate_model_for_deployment(model):
                logger.error(f"Model {model.model_name} failed validation")
                return False
            
            # Save model to storage
            model_path = await self._save_model(model)
            
            # Update model registry
            self.models[model.id] = model
            self.model_metadata[model.id] = {
                'model_path': str(model_path),
                'deployed_at': datetime.utcnow(),
                'version': model.version,
                'status': 'deployed'
            }
            
            # Update deployment timestamp
            model.deployed_at = datetime.utcnow()
            
            logger.info(f"Model {model.model_name} deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying model {model.model_name}: {e}")
            return False
    
    async def load_model(self, model_id: str) -> Optional[MLModel]:
        """
        Load a model from storage.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            Loaded ML model or None if not found
        """
        logger.info(f"Loading model: {model_id}")
        
        try:
            if model_id in self.models:
                return self.models[model_id]
            
            # Check if model exists in metadata
            if model_id not in self.model_metadata:
                logger.warning(f"Model {model_id} not found in metadata")
                return None
            
            metadata = self.model_metadata[model_id]
            model_path = Path(metadata['model_path'])
            
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return None
            
            # Load model from file
            model_data = joblib.load(model_path)
            
            # Reconstruct MLModel object
            model = MLModel(
                id=model_id,
                model_name=model_data['model_name'],
                model_type=ModelType(model_data['model_type']),
                version=model_data['version'],
                accuracy=model_data['accuracy'],
                training_data_size=model_data['training_data_size'],
                trained_at=model_data['trained_at'],
                deployed_at=metadata.get('deployed_at'),
                model_data=model_data['model_data'],
                hyperparameters=model_data.get('hyperparameters', {})
            )
            
            # Cache loaded model
            self.models[model_id] = model
            
            logger.info(f"Model {model_id} loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return None
    
    async def get_model_performance_history(self, model_id: str) -> List[ModelPerformanceMetrics]:
        """
        Get performance history for a model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            List of historical performance metrics
        """
        return self.performance_history.get(model_id, [])
    
    async def check_model_drift(self, model_id: str) -> Dict[str, Any]:
        """
        Check for model performance drift.
        
        Args:
            model_id: ID of the model to check
            
        Returns:
            Dictionary with drift analysis results
        """
        logger.info(f"Checking model drift for: {model_id}")
        
        try:
            performance_history = await self.get_model_performance_history(model_id)
            
            if len(performance_history) < 2:
                return {'drift_detected': False, 'reason': 'Insufficient history'}
            
            # Compare recent performance with baseline
            recent_metrics = performance_history[-5:]  # Last 5 evaluations
            baseline_metrics = performance_history[:5]  # First 5 evaluations
            
            recent_accuracy = sum(m.accuracy for m in recent_metrics) / len(recent_metrics)
            baseline_accuracy = sum(m.accuracy for m in baseline_metrics) / len(baseline_metrics)
            
            accuracy_drop = baseline_accuracy - recent_accuracy
            drift_threshold = 0.05  # 5% accuracy drop threshold
            
            drift_detected = accuracy_drop > drift_threshold
            
            drift_analysis = {
                'drift_detected': drift_detected,
                'accuracy_drop': accuracy_drop,
                'recent_accuracy': recent_accuracy,
                'baseline_accuracy': baseline_accuracy,
                'threshold': drift_threshold,
                'recommendation': 'Retrain model' if drift_detected else 'Continue monitoring'
            }
            
            if drift_detected:
                logger.warning(f"Model drift detected for {model_id}: {accuracy_drop:.3f} accuracy drop")
            
            return drift_analysis
            
        except Exception as e:
            logger.error(f"Error checking model drift for {model_id}: {e}")
            return {'drift_detected': False, 'error': str(e)}
    
    async def schedule_retraining(self) -> None:
        """Schedule automatic model retraining based on configuration."""
        logger.info("Starting scheduled model retraining")
        
        while True:
            try:
                # Wait for training interval
                await asyncio.sleep(self.config.training_interval)
                
                # Check if retraining is needed
                for model_id in self.models.keys():
                    drift_analysis = await self.check_model_drift(model_id)
                    
                    if drift_analysis.get('drift_detected', False):
                        logger.info(f"Retraining model {model_id} due to drift")
                        
                        # Get fresh training data
                        training_data = await self._get_training_data()
                        
                        if not training_data.empty:
                            await self.train_models(training_data)
                
                logger.info("Scheduled retraining check completed")
                
            except Exception as e:
                logger.error(f"Error in scheduled retraining: {e}")
                # Wait before retrying
                await asyncio.sleep(3600)  # 1 hour
    
    async def _train_task_failure_model(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train task failure prediction model."""
        try:
            model = TaskFailurePredictionModel()
            
            # Prepare training data for task failure prediction
            task_data = training_data[training_data['data_type'] == 'task_metrics'].copy()
            
            if len(task_data) < 10:
                logger.warning("Insufficient task data for training")
                return {}
            
            # Create target variable (task failure)
            task_data['task_failed'] = task_data.get('success', True) == False
            
            # Train model
            results = await model.train(task_data, 'task_failed')
            
            # Create MLModel object
            ml_model = MLModel(
                id=model.model_id,
                model_name="Task Failure Predictor",
                model_type=ModelType.CLASSIFICATION,
                version="1.0",
                accuracy=results.get('test_accuracy', 0.0),
                training_data_size=len(task_data),
                trained_at=datetime.utcnow(),
                model_data=joblib.dumps(model),
                hyperparameters={'n_estimators': 100, 'max_depth': 10}
            )
            
            # Deploy model
            await self.deploy_model(ml_model)
            
            return results
            
        except Exception as e:
            logger.error(f"Error training task failure model: {e}")
            return {}
    
    async def _train_resource_usage_model(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train resource usage prediction model."""
        try:
            model = ResourceUsagePredictionModel()
            
            # Prepare training data for resource usage prediction
            resource_data = training_data[training_data['data_type'] == 'resource_metrics'].copy()
            
            if len(resource_data) < 10:
                logger.warning("Insufficient resource data for training")
                return {}
            
            # Train model
            results = await model.train(resource_data)
            
            # Create MLModel object
            ml_model = MLModel(
                id=model.model_id,
                model_name="Resource Usage Predictor",
                model_type=ModelType.REGRESSION,
                version="1.0",
                accuracy=(results.get('cpu_accuracy', 0.0) + results.get('memory_accuracy', 0.0)) / 2,
                training_data_size=len(resource_data),
                trained_at=datetime.utcnow(),
                model_data=joblib.dumps(model),
                hyperparameters={'n_estimators': 50}
            )
            
            # Deploy model
            await self.deploy_model(ml_model)
            
            return results
            
        except Exception as e:
            logger.error(f"Error training resource usage model: {e}")
            return {}
    
    async def _train_performance_model(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train performance optimization model."""
        try:
            model = PerformanceOptimizationModel()
            
            # Prepare training data for performance optimization
            performance_data = training_data[training_data['data_type'] == 'performance_metrics'].copy()
            
            if len(performance_data) < 20:
                logger.warning("Insufficient performance data for training")
                return {}
            
            # Train model
            results = await model.train(performance_data)
            
            # Create MLModel object
            ml_model = MLModel(
                id=model.model_id,
                model_name="Performance Optimizer",
                model_type=ModelType.TIME_SERIES,
                version="1.0",
                accuracy=results.get('forecast_accuracy', 0.0),
                training_data_size=len(performance_data),
                trained_at=datetime.utcnow(),
                model_data=joblib.dumps(model),
                hyperparameters={}
            )
            
            # Deploy model
            await self.deploy_model(ml_model)
            
            return results
            
        except Exception as e:
            logger.error(f"Error training performance model: {e}")
            return {}
    
    async def _validate_model_for_deployment(self, model: MLModel) -> bool:
        """Validate model meets deployment criteria."""
        try:
            # Check accuracy threshold
            if model.accuracy < self.config.accuracy_threshold:
                logger.warning(f"Model accuracy {model.accuracy} below threshold {self.config.accuracy_threshold}")
                return False
            
            # Check if model data exists
            if model.model_data is None:
                logger.error("Model data is None")
                return False
            
            # Check training data size
            if model.training_data_size < self.config.min_training_samples:
                logger.warning(f"Training data size {model.training_data_size} below minimum {self.config.min_training_samples}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating model: {e}")
            return False
    
    async def _save_model(self, model: MLModel) -> Path:
        """Save model to storage."""
        model_filename = f"{model.id}_{model.version}.joblib"
        model_path = self.model_storage_path / model_filename
        
        model_data = {
            'model_name': model.model_name,
            'model_type': model.model_type.value,
            'version': model.version,
            'accuracy': model.accuracy,
            'training_data_size': model.training_data_size,
            'trained_at': model.trained_at,
            'model_data': model.model_data,
            'hyperparameters': model.hyperparameters
        }
        
        joblib.dump(model_data, model_path)
        logger.info(f"Model saved to: {model_path}")
        
        return model_path
    
    async def _get_evaluation_data(self, model_id: str) -> pd.DataFrame:
        """Get evaluation data for a model."""
        # Mock implementation - replace with actual data retrieval
        # This would typically get recent data that wasn't used for training
        return pd.DataFrame()
    
    async def _get_training_data(self) -> pd.DataFrame:
        """Get fresh training data."""
        # Mock implementation - replace with actual data retrieval
        return pd.DataFrame()
    
    def _create_default_metrics(self, model_id: str) -> ModelPerformanceMetrics:
        """Create default performance metrics."""
        return ModelPerformanceMetrics(
            model_id=model_id,
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0
        )
    
    def _store_performance_metrics(self, model_id: str, metrics: ModelPerformanceMetrics) -> None:
        """Store performance metrics in history."""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = []
        
        self.performance_history[model_id].append(metrics)
        
        # Keep only last 100 metrics
        if len(self.performance_history[model_id]) > 100:
            self.performance_history[model_id] = self.performance_history[model_id][-100:]
    
    def _update_training_timestamp(self) -> None:
        """Update last training timestamp."""
        self.last_training = datetime.utcnow()
        logger.info(f"Training timestamp updated: {self.last_training}")

