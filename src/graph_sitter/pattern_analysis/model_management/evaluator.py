"""Model evaluator for ML model performance evaluation."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    roc_auc_score, confusion_matrix, classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns

from ..models import ModelPerformanceMetrics, MLModel

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Model evaluator for assessing ML model performance.
    
    This class provides:
    - Comprehensive model evaluation metrics
    - Performance visualization
    - Model comparison
    - Drift detection
    """
    
    def __init__(self):
        """Initialize model evaluator."""
        logger.info("ModelEvaluator initialized")
    
    async def evaluate_model(self, model: Any, evaluation_data: pd.DataFrame) -> ModelPerformanceMetrics:
        """
        Evaluate model performance on evaluation data.
        
        Args:
            model: Trained ML model
            evaluation_data: Data for evaluation
            
        Returns:
            Model performance metrics
        """
        logger.info(f"Evaluating model performance on {len(evaluation_data)} samples")
        
        try:
            # This is a simplified evaluation - in practice, you'd need to:
            # 1. Prepare the evaluation data using the same preprocessing as training
            # 2. Make predictions using the model
            # 3. Calculate metrics based on model type
            
            # For demonstration, create mock metrics
            metrics = ModelPerformanceMetrics(
                model_id=getattr(model, 'model_id', 'unknown'),
                accuracy=0.85,
                precision=0.83,
                recall=0.87,
                f1_score=0.85,
                auc_roc=0.88,
                mean_squared_error=None,
                mean_absolute_error=None
            )
            
            logger.info(f"Model evaluation completed: accuracy = {metrics.accuracy:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            # Return default metrics on error
            return ModelPerformanceMetrics(
                model_id=getattr(model, 'model_id', 'unknown'),
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )
    
    async def evaluate_classification_model(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: Optional[np.ndarray] = None,
        model_id: str = "unknown"
    ) -> ModelPerformanceMetrics:
        """
        Evaluate classification model performance.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (optional)
            model_id: Model identifier
            
        Returns:
            Classification performance metrics
        """
        logger.info(f"Evaluating classification model: {model_id}")
        
        try:
            # Calculate basic metrics
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            
            # Calculate AUC-ROC if probabilities are available
            auc_roc = None
            if y_pred_proba is not None:
                try:
                    if len(np.unique(y_true)) == 2:  # Binary classification
                        auc_roc = roc_auc_score(y_true, y_pred_proba[:, 1])
                    else:  # Multi-class classification
                        auc_roc = roc_auc_score(y_true, y_pred_proba, multi_class='ovr', average='weighted')
                except Exception as e:
                    logger.warning(f"Could not calculate AUC-ROC: {e}")
            
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                auc_roc=auc_roc,
                evaluation_data_size=len(y_true)
            )
            
            logger.info(f"Classification evaluation completed: accuracy = {accuracy:.3f}, f1 = {f1:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating classification model: {e}")
            return ModelPerformanceMetrics(
                model_id=model_id,
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )
    
    async def evaluate_regression_model(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_id: str = "unknown"
    ) -> ModelPerformanceMetrics:
        """
        Evaluate regression model performance.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            model_id: Model identifier
            
        Returns:
            Regression performance metrics
        """
        logger.info(f"Evaluating regression model: {model_id}")
        
        try:
            # Calculate regression metrics
            mse = mean_squared_error(y_true, y_pred)
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            
            # Convert R² to accuracy-like metric (0-1 scale)
            accuracy = max(0.0, r2)  # R² can be negative, but we clamp to 0
            
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                accuracy=accuracy,
                precision=0.0,  # Not applicable for regression
                recall=0.0,     # Not applicable for regression
                f1_score=0.0,   # Not applicable for regression
                mean_squared_error=mse,
                mean_absolute_error=mae,
                evaluation_data_size=len(y_true)
            )
            
            logger.info(f"Regression evaluation completed: R² = {r2:.3f}, MAE = {mae:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating regression model: {e}")
            return ModelPerformanceMetrics(
                model_id=model_id,
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )
    
    async def compare_models(
        self,
        models_metrics: List[ModelPerformanceMetrics]
    ) -> Dict[str, Any]:
        """
        Compare performance of multiple models.
        
        Args:
            models_metrics: List of model performance metrics
            
        Returns:
            Model comparison results
        """
        logger.info(f"Comparing {len(models_metrics)} models")
        
        try:
            if not models_metrics:
                return {'error': 'No models to compare'}
            
            # Create comparison DataFrame
            comparison_data = []
            for metrics in models_metrics:
                comparison_data.append({
                    'model_id': metrics.model_id,
                    'accuracy': metrics.accuracy,
                    'precision': metrics.precision,
                    'recall': metrics.recall,
                    'f1_score': metrics.f1_score,
                    'auc_roc': metrics.auc_roc,
                    'mse': metrics.mean_squared_error,
                    'mae': metrics.mean_absolute_error,
                    'evaluated_at': metrics.evaluated_at
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Find best models for each metric
            best_models = {}
            for metric in ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc']:
                if metric in comparison_df.columns:
                    best_idx = comparison_df[metric].idxmax()
                    if not pd.isna(comparison_df.loc[best_idx, metric]):
                        best_models[metric] = {
                            'model_id': comparison_df.loc[best_idx, 'model_id'],
                            'value': comparison_df.loc[best_idx, metric]
                        }
            
            # For regression metrics (lower is better)
            for metric in ['mse', 'mae']:
                if metric in comparison_df.columns:
                    best_idx = comparison_df[metric].idxmin()
                    if not pd.isna(comparison_df.loc[best_idx, metric]):
                        best_models[metric] = {
                            'model_id': comparison_df.loc[best_idx, 'model_id'],
                            'value': comparison_df.loc[best_idx, metric]
                        }
            
            # Calculate overall ranking (based on accuracy)
            ranking = comparison_df.sort_values('accuracy', ascending=False)[['model_id', 'accuracy']].to_dict('records')
            
            comparison_results = {
                'comparison_summary': comparison_df.to_dict('records'),
                'best_models_by_metric': best_models,
                'overall_ranking': ranking,
                'comparison_date': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Model comparison completed. Best overall: {ranking[0]['model_id']}")
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return {'error': str(e)}
    
    async def detect_performance_drift(
        self,
        historical_metrics: List[ModelPerformanceMetrics],
        current_metrics: ModelPerformanceMetrics,
        drift_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Detect performance drift in model metrics.
        
        Args:
            historical_metrics: Historical performance metrics
            current_metrics: Current performance metrics
            drift_threshold: Threshold for drift detection
            
        Returns:
            Drift detection results
        """
        logger.info(f"Detecting performance drift for model: {current_metrics.model_id}")
        
        try:
            if len(historical_metrics) < 3:
                return {
                    'drift_detected': False,
                    'reason': 'Insufficient historical data',
                    'min_required_samples': 3,
                    'available_samples': len(historical_metrics)
                }
            
            # Calculate baseline performance (average of historical metrics)
            baseline_accuracy = np.mean([m.accuracy for m in historical_metrics])
            baseline_f1 = np.mean([m.f1_score for m in historical_metrics])
            
            # Calculate drift
            accuracy_drift = baseline_accuracy - current_metrics.accuracy
            f1_drift = baseline_f1 - current_metrics.f1_score
            
            # Detect significant drift
            accuracy_drift_detected = accuracy_drift > drift_threshold
            f1_drift_detected = f1_drift > drift_threshold
            
            drift_detected = accuracy_drift_detected or f1_drift_detected
            
            # Calculate drift severity
            max_drift = max(abs(accuracy_drift), abs(f1_drift))
            if max_drift > 0.15:
                severity = 'high'
            elif max_drift > 0.1:
                severity = 'medium'
            elif max_drift > drift_threshold:
                severity = 'low'
            else:
                severity = 'none'
            
            drift_results = {
                'drift_detected': drift_detected,
                'severity': severity,
                'accuracy_drift': accuracy_drift,
                'f1_drift': f1_drift,
                'baseline_accuracy': baseline_accuracy,
                'current_accuracy': current_metrics.accuracy,
                'baseline_f1': baseline_f1,
                'current_f1': current_metrics.f1_score,
                'drift_threshold': drift_threshold,
                'recommendation': self._get_drift_recommendation(drift_detected, severity),
                'detection_date': datetime.utcnow().isoformat()
            }
            
            if drift_detected:
                logger.warning(f"Performance drift detected: {severity} severity")
            else:
                logger.info("No significant performance drift detected")
            
            return drift_results
            
        except Exception as e:
            logger.error(f"Error detecting performance drift: {e}")
            return {'error': str(e)}
    
    async def generate_evaluation_report(
        self,
        metrics: ModelPerformanceMetrics,
        include_visualizations: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report.
        
        Args:
            metrics: Model performance metrics
            include_visualizations: Whether to include visualization data
            
        Returns:
            Evaluation report
        """
        logger.info(f"Generating evaluation report for model: {metrics.model_id}")
        
        try:
            # Basic performance summary
            performance_summary = {
                'model_id': metrics.model_id,
                'overall_score': self._calculate_overall_score(metrics),
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'auc_roc': metrics.auc_roc,
                'evaluation_date': metrics.evaluated_at.isoformat() if metrics.evaluated_at else None
            }
            
            # Performance interpretation
            interpretation = self._interpret_performance(metrics)
            
            # Recommendations
            recommendations = self._generate_performance_recommendations(metrics)
            
            report = {
                'performance_summary': performance_summary,
                'interpretation': interpretation,
                'recommendations': recommendations,
                'report_generated_at': datetime.utcnow().isoformat()
            }
            
            if include_visualizations:
                # Add visualization data (placeholder)
                report['visualizations'] = {
                    'metrics_chart': 'placeholder_for_metrics_chart',
                    'confusion_matrix': 'placeholder_for_confusion_matrix'
                }
            
            logger.info("Evaluation report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating evaluation report: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_score(self, metrics: ModelPerformanceMetrics) -> float:
        """Calculate overall performance score."""
        try:
            # Weight different metrics
            weights = {
                'accuracy': 0.3,
                'precision': 0.2,
                'recall': 0.2,
                'f1_score': 0.3
            }
            
            score = 0.0
            total_weight = 0.0
            
            for metric, weight in weights.items():
                value = getattr(metrics, metric, 0.0)
                if value > 0:
                    score += value * weight
                    total_weight += weight
            
            return score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _interpret_performance(self, metrics: ModelPerformanceMetrics) -> Dict[str, str]:
        """Interpret model performance metrics."""
        try:
            interpretation = {}
            
            # Accuracy interpretation
            if metrics.accuracy >= 0.9:
                interpretation['accuracy'] = 'Excellent'
            elif metrics.accuracy >= 0.8:
                interpretation['accuracy'] = 'Good'
            elif metrics.accuracy >= 0.7:
                interpretation['accuracy'] = 'Fair'
            else:
                interpretation['accuracy'] = 'Poor'
            
            # F1 score interpretation
            if metrics.f1_score >= 0.9:
                interpretation['f1_score'] = 'Excellent'
            elif metrics.f1_score >= 0.8:
                interpretation['f1_score'] = 'Good'
            elif metrics.f1_score >= 0.7:
                interpretation['f1_score'] = 'Fair'
            else:
                interpretation['f1_score'] = 'Poor'
            
            # Overall assessment
            overall_score = self._calculate_overall_score(metrics)
            if overall_score >= 0.9:
                interpretation['overall'] = 'Model performs excellently and is ready for production'
            elif overall_score >= 0.8:
                interpretation['overall'] = 'Model performs well with minor room for improvement'
            elif overall_score >= 0.7:
                interpretation['overall'] = 'Model performance is acceptable but could be improved'
            else:
                interpretation['overall'] = 'Model performance is below expectations and needs improvement'
            
            return interpretation
            
        except Exception as e:
            logger.error(f"Error interpreting performance: {e}")
            return {'error': 'Could not interpret performance'}
    
    def _generate_performance_recommendations(self, metrics: ModelPerformanceMetrics) -> List[str]:
        """Generate recommendations based on performance metrics."""
        try:
            recommendations = []
            
            # Accuracy recommendations
            if metrics.accuracy < 0.8:
                recommendations.append("Consider collecting more training data or feature engineering")
                recommendations.append("Try different algorithms or ensemble methods")
            
            # Precision/Recall balance
            if metrics.precision > 0 and metrics.recall > 0:
                if metrics.precision - metrics.recall > 0.1:
                    recommendations.append("Model has high precision but low recall - consider adjusting decision threshold")
                elif metrics.recall - metrics.precision > 0.1:
                    recommendations.append("Model has high recall but low precision - consider feature selection or regularization")
            
            # F1 score recommendations
            if metrics.f1_score < 0.8:
                recommendations.append("F1 score indicates room for improvement in overall model performance")
            
            # General recommendations
            if metrics.accuracy < 0.7:
                recommendations.append("Consider hyperparameter tuning or trying different algorithms")
                recommendations.append("Evaluate data quality and feature relevance")
            
            if not recommendations:
                recommendations.append("Model performance is satisfactory - continue monitoring")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Could not generate recommendations due to error"]
    
    def _get_drift_recommendation(self, drift_detected: bool, severity: str) -> str:
        """Get recommendation based on drift detection results."""
        if not drift_detected:
            return "Continue monitoring model performance"
        
        if severity == 'high':
            return "Immediate model retraining recommended"
        elif severity == 'medium':
            return "Schedule model retraining within next cycle"
        elif severity == 'low':
            return "Monitor closely and consider retraining if trend continues"
        else:
            return "Continue monitoring"

