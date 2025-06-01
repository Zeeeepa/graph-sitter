"""Model trainer for ML model training operations."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler, LabelEncoder

from ..config import MLModelConfig
from ..models import ModelPerformanceMetrics

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Model trainer for handling ML model training operations.
    
    This class provides:
    - Automated hyperparameter tuning
    - Cross-validation
    - Model evaluation
    - Training data preparation
    """
    
    def __init__(self, config: MLModelConfig):
        """
        Initialize model trainer.
        
        Args:
            config: ML model configuration
        """
        self.config = config
        self.scalers = {}
        self.encoders = {}
        
        logger.info("ModelTrainer initialized")
    
    async def prepare_training_data(
        self, 
        data: pd.DataFrame, 
        target_column: str,
        feature_columns: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for model training.
        
        Args:
            data: Training data DataFrame
            target_column: Name of the target column
            feature_columns: List of feature columns (if None, auto-select)
            
        Returns:
            Tuple of (features, target, feature_names)
        """
        logger.info(f"Preparing training data with {len(data)} samples")
        
        try:
            # Handle missing target column
            if target_column not in data.columns:
                raise ValueError(f"Target column '{target_column}' not found in data")
            
            # Auto-select feature columns if not provided
            if feature_columns is None:
                # Exclude target and non-feature columns
                exclude_columns = {
                    target_column, 'id', 'timestamp', 'created_at', 'updated_at'
                }
                feature_columns = [
                    col for col in data.columns 
                    if col not in exclude_columns and not col.endswith('_id')
                ]
            
            # Filter available feature columns
            available_features = [col for col in feature_columns if col in data.columns]
            
            if not available_features:
                raise ValueError("No valid feature columns found")
            
            logger.info(f"Using {len(available_features)} features: {available_features}")
            
            # Prepare features
            X = data[available_features].copy()
            y = data[target_column].copy()
            
            # Handle missing values
            X = self._handle_missing_values(X)
            
            # Encode categorical variables
            X_encoded = self._encode_categorical_features(X)
            
            # Scale numerical features
            X_scaled = self._scale_numerical_features(X_encoded)
            
            # Encode target if categorical
            y_encoded = self._encode_target(y, target_column)
            
            logger.info(f"Training data prepared: {X_scaled.shape[0]} samples, {X_scaled.shape[1]} features")
            
            return X_scaled, y_encoded, available_features
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            raise
    
    async def train_with_cross_validation(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Train model with cross-validation.
        
        Args:
            model: ML model to train
            X: Feature matrix
            y: Target vector
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dictionary with cross-validation results
        """
        cv_folds = cv_folds or self.config.cross_validation_folds
        
        logger.info(f"Training model with {cv_folds}-fold cross-validation")
        
        try:
            # Perform cross-validation
            cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='accuracy')
            
            # Train on full dataset
            model.fit(X, y)
            
            # Calculate training accuracy
            train_predictions = model.predict(X)
            train_accuracy = accuracy_score(y, train_predictions)
            
            results = {
                'cv_mean_accuracy': cv_scores.mean(),
                'cv_std_accuracy': cv_scores.std(),
                'cv_scores': cv_scores.tolist(),
                'train_accuracy': train_accuracy,
                'cv_folds': cv_folds
            }
            
            logger.info(f"Cross-validation completed: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in cross-validation training: {e}")
            raise
    
    async def train_with_validation_split(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        test_size: Optional[float] = None,
        random_state: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Train model with train/validation split.
        
        Args:
            model: ML model to train
            X: Feature matrix
            y: Target vector
            test_size: Size of test set
            random_state: Random state for reproducibility
            
        Returns:
            Dictionary with training and validation results
        """
        test_size = test_size or self.config.test_size
        random_state = random_state or self.config.random_state
        
        logger.info(f"Training model with {test_size:.1%} validation split")
        
        try:
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            train_predictions = model.predict(X_train)
            val_predictions = model.predict(X_val)
            
            # Calculate metrics
            train_accuracy = accuracy_score(y_train, train_predictions)
            val_accuracy = accuracy_score(y_val, val_predictions)
            
            # Calculate additional metrics for validation set
            val_precision = precision_score(y_val, val_predictions, average='weighted', zero_division=0)
            val_recall = recall_score(y_val, val_predictions, average='weighted', zero_division=0)
            val_f1 = f1_score(y_val, val_predictions, average='weighted', zero_division=0)
            
            results = {
                'train_accuracy': train_accuracy,
                'val_accuracy': val_accuracy,
                'val_precision': val_precision,
                'val_recall': val_recall,
                'val_f1_score': val_f1,
                'train_samples': len(X_train),
                'val_samples': len(X_val)
            }
            
            logger.info(f"Training completed: Train={train_accuracy:.3f}, Val={val_accuracy:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in validation split training: {e}")
            raise
    
    async def hyperparameter_tuning(
        self,
        model,
        param_grid: Dict[str, List[Any]],
        X: np.ndarray,
        y: np.ndarray,
        cv_folds: Optional[int] = None,
        scoring: str = 'accuracy'
    ) -> Tuple[Any, Dict[str, Any], Dict[str, float]]:
        """
        Perform hyperparameter tuning using grid search.
        
        Args:
            model: ML model to tune
            param_grid: Parameter grid for grid search
            X: Feature matrix
            y: Target vector
            cv_folds: Number of cross-validation folds
            scoring: Scoring metric for optimization
            
        Returns:
            Tuple of (best_model, best_params, tuning_results)
        """
        cv_folds = cv_folds or self.config.cross_validation_folds
        
        logger.info(f"Starting hyperparameter tuning with {len(param_grid)} parameters")
        
        try:
            # Perform grid search
            grid_search = GridSearchCV(
                model, 
                param_grid, 
                cv=cv_folds, 
                scoring=scoring,
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X, y)
            
            # Get results
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_score = grid_search.best_score_
            
            tuning_results = {
                'best_score': best_score,
                'best_params': best_params,
                'cv_results': {
                    'mean_test_scores': grid_search.cv_results_['mean_test_score'].tolist(),
                    'std_test_scores': grid_search.cv_results_['std_test_score'].tolist(),
                    'params': grid_search.cv_results_['params']
                }
            }
            
            logger.info(f"Hyperparameter tuning completed: Best score = {best_score:.3f}")
            logger.info(f"Best parameters: {best_params}")
            
            return best_model, best_params, tuning_results
            
        except Exception as e:
            logger.error(f"Error in hyperparameter tuning: {e}")
            raise
    
    def _handle_missing_values(self, X: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features."""
        try:
            # For numerical columns, fill with median
            numerical_cols = X.select_dtypes(include=[np.number]).columns
            for col in numerical_cols:
                if X[col].isnull().any():
                    median_value = X[col].median()
                    X[col] = X[col].fillna(median_value)
            
            # For categorical columns, fill with mode
            categorical_cols = X.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                if X[col].isnull().any():
                    mode_value = X[col].mode().iloc[0] if not X[col].mode().empty else 'unknown'
                    X[col] = X[col].fillna(mode_value)
            
            return X
            
        except Exception as e:
            logger.error(f"Error handling missing values: {e}")
            return X
    
    def _encode_categorical_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features."""
        try:
            X_encoded = X.copy()
            categorical_cols = X.select_dtypes(include=['object', 'category']).columns
            
            for col in categorical_cols:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    X_encoded[f'{col}_encoded'] = self.encoders[col].fit_transform(X[col].astype(str))
                else:
                    # Handle unseen categories
                    try:
                        X_encoded[f'{col}_encoded'] = self.encoders[col].transform(X[col].astype(str))
                    except ValueError:
                        # If unseen categories, refit encoder
                        self.encoders[col] = LabelEncoder()
                        X_encoded[f'{col}_encoded'] = self.encoders[col].fit_transform(X[col].astype(str))
                
                # Drop original categorical column
                X_encoded = X_encoded.drop(columns=[col])
            
            return X_encoded
            
        except Exception as e:
            logger.error(f"Error encoding categorical features: {e}")
            return X
    
    def _scale_numerical_features(self, X: pd.DataFrame) -> np.ndarray:
        """Scale numerical features."""
        try:
            numerical_cols = X.select_dtypes(include=[np.number]).columns
            
            if len(numerical_cols) == 0:
                return X.values
            
            if 'numerical' not in self.scalers:
                self.scalers['numerical'] = StandardScaler()
                X_scaled = self.scalers['numerical'].fit_transform(X[numerical_cols])
            else:
                X_scaled = self.scalers['numerical'].transform(X[numerical_cols])
            
            # Combine scaled numerical features with non-numerical features
            non_numerical_cols = X.select_dtypes(exclude=[np.number]).columns
            if len(non_numerical_cols) > 0:
                X_non_numerical = X[non_numerical_cols].values
                X_combined = np.hstack([X_scaled, X_non_numerical])
                return X_combined
            else:
                return X_scaled
            
        except Exception as e:
            logger.error(f"Error scaling numerical features: {e}")
            return X.values
    
    def _encode_target(self, y: pd.Series, target_column: str) -> np.ndarray:
        """Encode target variable if categorical."""
        try:
            if y.dtype in ['object', 'category']:
                if target_column not in self.encoders:
                    self.encoders[target_column] = LabelEncoder()
                    y_encoded = self.encoders[target_column].fit_transform(y.astype(str))
                else:
                    y_encoded = self.encoders[target_column].transform(y.astype(str))
                return y_encoded
            else:
                return y.values
            
        except Exception as e:
            logger.error(f"Error encoding target variable: {e}")
            return y.values
    
    def get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from trained model."""
        try:
            if hasattr(model, 'feature_importances_'):
                importance_scores = model.feature_importances_
                importance_dict = dict(zip(feature_names, importance_scores))
                
                # Sort by importance
                sorted_importance = dict(
                    sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
                )
                
                return sorted_importance
            else:
                logger.warning("Model does not have feature_importances_ attribute")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def create_performance_metrics(
        self, 
        model_id: str, 
        y_true: np.ndarray, 
        y_pred: np.ndarray
    ) -> ModelPerformanceMetrics:
        """Create performance metrics object."""
        try:
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error creating performance metrics: {e}")
            return ModelPerformanceMetrics(
                model_id=model_id,
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )

