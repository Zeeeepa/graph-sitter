"""Main data pipeline for extracting and preprocessing historical data."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from ..config import DataPipelineConfig, TimeRange
from ..models import TaskMetrics, PipelineMetrics, FeatureVector
from .extractors import DatabaseExtractor, MetricsExtractor
from .preprocessors import DataPreprocessor, FeatureEngineer

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Data pipeline for extracting and preprocessing historical data from all 7 database modules.
    
    This class handles:
    - Data extraction from multiple database sources
    - Data cleaning and normalization
    - Feature engineering for ML models
    - Batch processing with configurable intervals
    """
    
    def __init__(self, config: DataPipelineConfig):
        """Initialize the data pipeline with configuration."""
        self.config = config
        self.database_extractor = DatabaseExtractor()
        self.metrics_extractor = MetricsExtractor()
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        
        logger.info(f"DataPipeline initialized with batch_size={config.batch_size}")
    
    async def extract_historical_data(self, time_range: TimeRange) -> pd.DataFrame:
        """
        Extract historical data from all 7 database modules.
        
        Args:
            time_range: Time range for data extraction
            
        Returns:
            DataFrame containing extracted historical data
        """
        logger.info(f"Extracting historical data from {time_range.start_timestamp} to {time_range.end_timestamp}")
        
        try:
            # Extract data from all database modules in parallel
            extraction_tasks = [
                self._extract_task_data(time_range),
                self._extract_pipeline_data(time_range),
                self._extract_resource_data(time_range),
                self._extract_error_data(time_range),
                self._extract_performance_data(time_range),
                self._extract_workflow_data(time_range),
                self._extract_analytics_data(time_range),
            ]
            
            results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            # Combine all extracted data
            combined_data = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to extract data from module {i}: {result}")
                    continue
                if result is not None and not result.empty:
                    combined_data.append(result)
            
            if not combined_data:
                logger.warning("No data extracted from any module")
                return pd.DataFrame()
            
            # Merge all dataframes
            historical_data = pd.concat(combined_data, ignore_index=True, sort=False)
            logger.info(f"Extracted {len(historical_data)} records")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error extracting historical data: {e}")
            raise
    
    async def preprocess_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean, normalize, and feature engineer the raw data.
        
        Args:
            raw_data: Raw data from extraction
            
        Returns:
            Preprocessed DataFrame ready for ML models
        """
        logger.info(f"Preprocessing {len(raw_data)} records")
        
        try:
            # Step 1: Data cleaning and validation
            cleaned_data = await self.preprocessor.clean_data(raw_data)
            logger.info(f"Data cleaning completed: {len(cleaned_data)} records remaining")
            
            # Step 2: Normalization and standardization
            normalized_data = await self.preprocessor.normalize_data(cleaned_data)
            logger.info("Data normalization completed")
            
            # Step 3: Feature engineering
            engineered_data = await self.feature_engineer.engineer_features(normalized_data)
            logger.info(f"Feature engineering completed: {engineered_data.shape[1]} features")
            
            return engineered_data
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {e}")
            raise
    
    async def process_batch(self, time_range: TimeRange) -> pd.DataFrame:
        """
        Process a batch of data for the given time range.
        
        Args:
            time_range: Time range for batch processing
            
        Returns:
            Processed DataFrame ready for analysis
        """
        logger.info(f"Processing batch for time range: {time_range.start_timestamp} - {time_range.end_timestamp}")
        
        # Extract raw data
        raw_data = await self.extract_historical_data(time_range)
        
        if raw_data.empty:
            logger.warning("No data to process in this batch")
            return pd.DataFrame()
        
        # Preprocess data
        processed_data = await self.preprocess_data(raw_data)
        
        logger.info(f"Batch processing completed: {len(processed_data)} processed records")
        return processed_data
    
    async def run_continuous_processing(self) -> None:
        """
        Run continuous data processing with configured intervals.
        """
        logger.info(f"Starting continuous processing with {self.config.processing_interval}s intervals")
        
        while True:
            try:
                # Calculate time range for current batch
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(seconds=self.config.processing_interval)
                
                time_range = TimeRange(
                    start_timestamp=start_time.timestamp(),
                    end_timestamp=end_time.timestamp()
                )
                
                # Process batch
                await self.process_batch(time_range)
                
                # Wait for next interval
                await asyncio.sleep(self.config.processing_interval)
                
            except Exception as e:
                logger.error(f"Error in continuous processing: {e}")
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def _extract_task_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract task performance data."""
        return await self.database_extractor.extract_task_data(time_range)
    
    async def _extract_pipeline_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract pipeline performance data."""
        return await self.database_extractor.extract_pipeline_data(time_range)
    
    async def _extract_resource_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract resource usage data."""
        return await self.database_extractor.extract_resource_data(time_range)
    
    async def _extract_error_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract error and failure data."""
        return await self.database_extractor.extract_error_data(time_range)
    
    async def _extract_performance_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract performance metrics data."""
        return await self.database_extractor.extract_performance_data(time_range)
    
    async def _extract_workflow_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract workflow execution data."""
        return await self.database_extractor.extract_workflow_data(time_range)
    
    async def _extract_analytics_data(self, time_range: TimeRange) -> pd.DataFrame:
        """Extract analytics and monitoring data."""
        return await self.database_extractor.extract_analytics_data(time_range)
    
    def get_feature_vectors(self, processed_data: pd.DataFrame) -> List[FeatureVector]:
        """
        Convert processed data to feature vectors for ML models.
        
        Args:
            processed_data: Preprocessed DataFrame
            
        Returns:
            List of FeatureVector objects
        """
        feature_vectors = []
        
        for _, row in processed_data.iterrows():
            features = row.to_dict()
            
            # Extract target variable if present
            target = features.pop('target', None)
            timestamp = features.pop('timestamp', datetime.utcnow())
            
            feature_vector = FeatureVector(
                features=features,
                target=target,
                timestamp=timestamp
            )
            feature_vectors.append(feature_vector)
        
        return feature_vectors

