"""Data preprocessing and feature engineering components."""

import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_classif, f_regression

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Data preprocessing component for cleaning and normalizing data.
    
    Handles:
    - Missing value imputation
    - Outlier detection and treatment
    - Data type conversions
    - Data validation
    """
    
    def __init__(self):
        """Initialize data preprocessor."""
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        logger.info("DataPreprocessor initialized")
    
    async def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate the input data.
        
        Args:
            data: Raw input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Cleaning data with {len(data)} records")
        
        try:
            cleaned_data = data.copy()
            
            # Remove completely empty rows
            cleaned_data = cleaned_data.dropna(how='all')
            
            # Handle missing timestamps
            if 'timestamp' in cleaned_data.columns:
                cleaned_data = cleaned_data.dropna(subset=['timestamp'])
                cleaned_data['timestamp'] = pd.to_datetime(cleaned_data['timestamp'])
            
            # Remove duplicate records
            initial_count = len(cleaned_data)
            cleaned_data = cleaned_data.drop_duplicates()
            duplicates_removed = initial_count - len(cleaned_data)
            
            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed} duplicate records")
            
            # Handle outliers
            cleaned_data = await self._handle_outliers(cleaned_data)
            
            # Validate data types
            cleaned_data = await self._validate_data_types(cleaned_data)
            
            logger.info(f"Data cleaning completed: {len(cleaned_data)} records remaining")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            raise
    
    async def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize and standardize numerical features.
        
        Args:
            data: Cleaned DataFrame
            
        Returns:
            Normalized DataFrame
        """
        logger.info("Normalizing data")
        
        try:
            normalized_data = data.copy()
            
            # Identify numerical columns
            numerical_cols = normalized_data.select_dtypes(include=[np.number]).columns
            categorical_cols = normalized_data.select_dtypes(include=['object', 'category']).columns
            
            # Handle missing values in numerical columns
            if len(numerical_cols) > 0:
                imputer = SimpleImputer(strategy='median')
                normalized_data[numerical_cols] = imputer.fit_transform(normalized_data[numerical_cols])
                self.imputers['numerical'] = imputer
            
            # Handle missing values in categorical columns
            if len(categorical_cols) > 0:
                imputer = SimpleImputer(strategy='most_frequent')
                normalized_data[categorical_cols] = imputer.fit_transform(normalized_data[categorical_cols])
                self.imputers['categorical'] = imputer
            
            # Encode categorical variables
            for col in categorical_cols:
                if col not in ['timestamp', 'module', 'data_type']:  # Skip certain columns
                    encoder = LabelEncoder()
                    normalized_data[f'{col}_encoded'] = encoder.fit_transform(normalized_data[col].astype(str))
                    self.encoders[col] = encoder
            
            # Scale numerical features
            scaler = StandardScaler()
            if len(numerical_cols) > 0:
                normalized_data[numerical_cols] = scaler.fit_transform(normalized_data[numerical_cols])
                self.scalers['standard'] = scaler
            
            logger.info("Data normalization completed")
            return normalized_data
            
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            raise
    
    async def _handle_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle outliers using IQR method."""
        logger.debug("Handling outliers")
        
        try:
            cleaned_data = data.copy()
            numerical_cols = cleaned_data.select_dtypes(include=[np.number]).columns
            
            for col in numerical_cols:
                if col in cleaned_data.columns:
                    Q1 = cleaned_data[col].quantile(0.25)
                    Q3 = cleaned_data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    # Define outlier bounds
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # Cap outliers instead of removing them
                    cleaned_data[col] = cleaned_data[col].clip(lower=lower_bound, upper=upper_bound)
            
            logger.debug("Outlier handling completed")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error handling outliers: {e}")
            return data
    
    async def _validate_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and convert data types."""
        logger.debug("Validating data types")
        
        try:
            validated_data = data.copy()
            
            # Convert boolean columns
            bool_cols = ['success', 'alert_triggered']
            for col in bool_cols:
                if col in validated_data.columns:
                    validated_data[col] = validated_data[col].astype(bool)
            
            # Convert timestamp columns
            timestamp_cols = ['timestamp', 'created_at', 'updated_at']
            for col in timestamp_cols:
                if col in validated_data.columns:
                    validated_data[col] = pd.to_datetime(validated_data[col])
            
            # Ensure numerical columns are numeric
            numerical_cols = ['duration', 'cpu_usage', 'memory_usage', 'success_rate', 'throughput']
            for col in numerical_cols:
                if col in validated_data.columns:
                    validated_data[col] = pd.to_numeric(validated_data[col], errors='coerce')
            
            logger.debug("Data type validation completed")
            return validated_data
            
        except Exception as e:
            logger.error(f"Error validating data types: {e}")
            return data


class FeatureEngineer:
    """
    Feature engineering component for creating ML-ready features.
    
    Handles:
    - Temporal feature extraction
    - Aggregation features
    - Interaction features
    - Domain-specific features
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_selectors = {}
        logger.info("FeatureEngineer initialized")
    
    async def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features for machine learning models.
        
        Args:
            data: Normalized DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Engineering features")
        
        try:
            engineered_data = data.copy()
            
            # Temporal features
            engineered_data = await self._create_temporal_features(engineered_data)
            
            # Aggregation features
            engineered_data = await self._create_aggregation_features(engineered_data)
            
            # Performance ratio features
            engineered_data = await self._create_performance_features(engineered_data)
            
            # Interaction features
            engineered_data = await self._create_interaction_features(engineered_data)
            
            # Domain-specific features
            engineered_data = await self._create_domain_features(engineered_data)
            
            logger.info(f"Feature engineering completed: {engineered_data.shape[1]} features")
            return engineered_data
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            raise
    
    async def _create_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features."""
        logger.debug("Creating temporal features")
        
        try:
            if 'timestamp' not in data.columns:
                return data
            
            # Ensure timestamp is datetime
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            # Extract temporal components
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['day_of_month'] = data['timestamp'].dt.day
            data['month'] = data['timestamp'].dt.month
            data['quarter'] = data['timestamp'].dt.quarter
            data['is_weekend'] = data['day_of_week'].isin([5, 6]).astype(int)
            data['is_business_hours'] = ((data['hour'] >= 9) & (data['hour'] <= 17)).astype(int)
            
            # Time since features (if we have a reference point)
            if len(data) > 1:
                data = data.sort_values('timestamp')
                data['time_since_last'] = data['timestamp'].diff().dt.total_seconds().fillna(0)
            
            logger.debug("Temporal features created")
            return data
            
        except Exception as e:
            logger.error(f"Error creating temporal features: {e}")
            return data
    
    async def _create_aggregation_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create aggregation-based features."""
        logger.debug("Creating aggregation features")
        
        try:
            # Rolling window features for numerical columns
            numerical_cols = data.select_dtypes(include=[np.number]).columns
            
            for col in numerical_cols:
                if col in data.columns and len(data) > 5:
                    # Rolling statistics
                    data[f'{col}_rolling_mean_5'] = data[col].rolling(window=5, min_periods=1).mean()
                    data[f'{col}_rolling_std_5'] = data[col].rolling(window=5, min_periods=1).std().fillna(0)
                    data[f'{col}_rolling_max_5'] = data[col].rolling(window=5, min_periods=1).max()
                    data[f'{col}_rolling_min_5'] = data[col].rolling(window=5, min_periods=1).min()
            
            # Group-based aggregations
            if 'module' in data.columns:
                module_stats = data.groupby('module').agg({
                    col: ['mean', 'std', 'count'] for col in numerical_cols if col in data.columns
                }).fillna(0)
                
                # Flatten column names
                module_stats.columns = ['_'.join(col).strip() for col in module_stats.columns]
                
                # Merge back to original data
                data = data.merge(module_stats, left_on='module', right_index=True, how='left', suffixes=('', '_module_agg'))
            
            logger.debug("Aggregation features created")
            return data
            
        except Exception as e:
            logger.error(f"Error creating aggregation features: {e}")
            return data
    
    async def _create_performance_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create performance-related features."""
        logger.debug("Creating performance features")
        
        try:
            # Efficiency ratios
            if 'duration' in data.columns and 'task_count' in data.columns:
                data['tasks_per_second'] = data['task_count'] / (data['duration'] + 1e-6)
            
            if 'cpu_usage' in data.columns and 'memory_usage' in data.columns:
                data['resource_efficiency'] = (data['cpu_usage'] + data['memory_usage']) / 2
                data['resource_imbalance'] = abs(data['cpu_usage'] - data['memory_usage'])
            
            if 'success_rate' in data.columns:
                data['failure_rate'] = 1 - data['success_rate']
                data['success_score'] = data['success_rate'] * 100
            
            # Performance categories
            if 'duration' in data.columns:
                data['duration_category'] = pd.cut(
                    data['duration'], 
                    bins=[0, 10, 60, 300, float('inf')], 
                    labels=['fast', 'medium', 'slow', 'very_slow']
                ).astype(str)
            
            logger.debug("Performance features created")
            return data
            
        except Exception as e:
            logger.error(f"Error creating performance features: {e}")
            return data
    
    async def _create_interaction_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between variables."""
        logger.debug("Creating interaction features")
        
        try:
            # CPU and memory interaction
            if 'cpu_usage' in data.columns and 'memory_usage' in data.columns:
                data['cpu_memory_product'] = data['cpu_usage'] * data['memory_usage']
                data['cpu_memory_ratio'] = data['cpu_usage'] / (data['memory_usage'] + 1e-6)
            
            # Duration and complexity interaction
            if 'duration' in data.columns and 'complexity_score' in data.columns:
                data['duration_complexity_ratio'] = data['duration'] / (data['complexity_score'] + 1e-6)
            
            # Success rate and throughput interaction
            if 'success_rate' in data.columns and 'throughput' in data.columns:
                data['effective_throughput'] = data['success_rate'] * data['throughput']
            
            logger.debug("Interaction features created")
            return data
            
        except Exception as e:
            logger.error(f"Error creating interaction features: {e}")
            return data
    
    async def _create_domain_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create domain-specific features for graph-sitter system."""
        logger.debug("Creating domain-specific features")
        
        try:
            # Task type complexity mapping
            if 'task_type' in data.columns:
                complexity_map = {
                    'analysis': 0.3,
                    'transformation': 0.6,
                    'validation': 0.2,
                    'optimization': 0.8,
                    'generation': 0.9
                }
                data['task_complexity_score'] = data['task_type'].map(complexity_map).fillna(0.5)
            
            # Error severity scoring
            if 'error_message' in data.columns:
                data['has_error'] = data['error_message'].notna().astype(int)
                data['error_length'] = data['error_message'].str.len().fillna(0)
            
            # Module priority scoring
            if 'module' in data.columns:
                priority_map = {
                    'task_execution': 0.9,
                    'pipeline_orchestration': 0.8,
                    'resource_management': 0.7,
                    'error_tracking': 0.6,
                    'performance_monitoring': 0.5,
                    'workflow_management': 0.4,
                    'analytics_reporting': 0.3
                }
                data['module_priority'] = data['module'].map(priority_map).fillna(0.5)
            
            # System load indicators
            if 'cpu_usage' in data.columns and 'memory_usage' in data.columns:
                data['system_stress'] = np.maximum(data['cpu_usage'], data['memory_usage'])
                data['is_high_load'] = (data['system_stress'] > 0.8).astype(int)
            
            logger.debug("Domain-specific features created")
            return data
            
        except Exception as e:
            logger.error(f"Error creating domain features: {e}")
            return data
    
    async def select_features(self, data: pd.DataFrame, target_col: str, k: int = 20) -> Tuple[pd.DataFrame, List[str]]:
        """
        Select the most important features using statistical tests.
        
        Args:
            data: DataFrame with engineered features
            target_col: Target column name
            k: Number of features to select
            
        Returns:
            Tuple of (selected features DataFrame, selected feature names)
        """
        logger.info(f"Selecting top {k} features")
        
        try:
            if target_col not in data.columns:
                logger.warning(f"Target column '{target_col}' not found")
                return data, list(data.columns)
            
            # Separate features and target
            X = data.drop(columns=[target_col])
            y = data[target_col]
            
            # Remove non-numeric columns for feature selection
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            X_numeric = X[numeric_cols]
            
            if len(X_numeric.columns) == 0:
                logger.warning("No numeric features found for selection")
                return data, list(data.columns)
            
            # Determine if target is continuous or categorical
            if y.dtype in ['object', 'category'] or y.nunique() < 10:
                score_func = f_classif
            else:
                score_func = f_regression
            
            # Select features
            selector = SelectKBest(score_func=score_func, k=min(k, len(X_numeric.columns)))
            X_selected = selector.fit_transform(X_numeric, y)
            
            # Get selected feature names
            selected_features = X_numeric.columns[selector.get_support()].tolist()
            selected_features.append(target_col)  # Include target
            
            # Store selector for future use
            self.feature_selectors[target_col] = selector
            
            logger.info(f"Selected {len(selected_features)-1} features")
            return data[selected_features], selected_features
            
        except Exception as e:
            logger.error(f"Error selecting features: {e}")
            return data, list(data.columns)

