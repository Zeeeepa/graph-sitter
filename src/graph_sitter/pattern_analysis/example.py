"""
Example usage of the Historical Pattern Analysis Engine.

This example demonstrates how to use the pattern analysis engine
to detect patterns, make predictions, and generate recommendations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .config import PatternAnalysisConfig, TimeRange
from .data_pipeline import DataPipeline
from .pattern_detection import PatternDetectionEngine
from .predictive_analytics import PredictiveAnalyticsService
from .recommendation_engine import RecommendationEngine
from .model_management import ModelManager
from .models import MLModel, ModelType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function demonstrating the pattern analysis engine."""
    logger.info("Starting Historical Pattern Analysis Engine Example")
    
    # Initialize configuration
    config = PatternAnalysisConfig()
    
    # Initialize components
    data_pipeline = DataPipeline(config.data_pipeline)
    pattern_engine = PatternDetectionEngine({}, config)
    predictive_service = PredictiveAnalyticsService(config)
    recommendation_engine = RecommendationEngine(config.recommendations)
    model_manager = ModelManager(config.ml_models)
    
    # Example 1: Data Pipeline Usage
    await example_data_pipeline(data_pipeline)
    
    # Example 2: Pattern Detection
    await example_pattern_detection(pattern_engine)
    
    # Example 3: Predictive Analytics
    await example_predictive_analytics(predictive_service)
    
    # Example 4: Recommendation Generation
    await example_recommendations(recommendation_engine)
    
    # Example 5: Model Management
    await example_model_management(model_manager)
    
    # Example 6: End-to-End Workflow
    await example_end_to_end_workflow(
        data_pipeline, pattern_engine, predictive_service, 
        recommendation_engine, model_manager
    )
    
    logger.info("Historical Pattern Analysis Engine Example Completed")


async def example_data_pipeline(data_pipeline: DataPipeline):
    """Example of using the data pipeline to extract and process data."""
    logger.info("=== Data Pipeline Example ===")
    
    # Define time range for data extraction
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)  # Last 24 hours
    
    time_range = TimeRange(
        start_timestamp=start_time.timestamp(),
        end_timestamp=end_time.timestamp()
    )
    
    # Extract historical data
    logger.info("Extracting historical data...")
    raw_data = await data_pipeline.extract_historical_data(time_range)
    logger.info(f"Extracted {len(raw_data)} records")
    
    if not raw_data.empty:
        # Preprocess the data
        logger.info("Preprocessing data...")
        processed_data = await data_pipeline.preprocess_data(raw_data)
        logger.info(f"Processed data shape: {processed_data.shape}")
        
        # Convert to feature vectors
        feature_vectors = data_pipeline.get_feature_vectors(processed_data)
        logger.info(f"Generated {len(feature_vectors)} feature vectors")
    
    logger.info("Data pipeline example completed\n")


async def example_pattern_detection(pattern_engine: PatternDetectionEngine):
    """Example of using the pattern detection engine."""
    logger.info("=== Pattern Detection Example ===")
    
    # Generate sample data for pattern detection
    sample_data = generate_sample_performance_data()
    
    # Detect patterns
    logger.info("Detecting patterns...")
    patterns = await pattern_engine.detect_patterns(sample_data)
    logger.info(f"Detected {len(patterns)} patterns")
    
    # Classify patterns
    if patterns:
        logger.info("Classifying patterns...")
        classified_patterns = await pattern_engine.classify_patterns(patterns)
        
        # Display top patterns
        for i, pattern in enumerate(classified_patterns[:3]):
            logger.info(f"Pattern {i+1}:")
            logger.info(f"  Type: {pattern.pattern_type.value}")
            logger.info(f"  Significance: {pattern.significance_score:.3f}")
            logger.info(f"  Impact: {pattern.impact_score:.3f}")
            logger.info(f"  Confidence: {pattern.confidence:.3f}")
            logger.info(f"  Description: {pattern.pattern_data.get('description', 'N/A')}")
    
    logger.info("Pattern detection example completed\n")


async def example_predictive_analytics(predictive_service: PredictiveAnalyticsService):
    """Example of using the predictive analytics service."""
    logger.info("=== Predictive Analytics Example ===")
    
    # Example 1: Task failure prediction
    task_context = {
        'task_type': 'analysis',
        'complexity_score': 0.7,
        'estimated_duration': 180.0,
        'historical_success_rate': 0.92,
        'cpu_requirement': 0.6,
        'memory_requirement': 0.5,
        'current_system_load': 0.65
    }
    
    logger.info("Predicting task failure probability...")
    failure_prediction = await predictive_service.predict_task_failure(task_context)
    logger.info(f"Failure probability: {failure_prediction.prediction_result['failure_probability']:.3f}")
    logger.info(f"Risk level: {failure_prediction.prediction_result['risk_level']}")
    
    # Example 2: Resource usage prediction
    workload = {
        'task_count': 5,
        'avg_task_complexity': 0.6,
        'workload_type': 'cpu_intensive',
        'parallelization_factor': 2.0,
        'current_cpu_usage': 0.4,
        'current_memory_usage': 0.3
    }
    
    logger.info("Predicting resource usage...")
    resource_prediction = await predictive_service.predict_resource_usage(workload)
    logger.info(f"Predicted CPU usage: {resource_prediction.prediction_result['cpu_usage']:.3f}")
    logger.info(f"Predicted memory usage: {resource_prediction.prediction_result['memory_usage']:.3f}")
    
    # Example 3: Early warning generation
    logger.info("Generating early warnings...")
    warnings = await predictive_service.generate_early_warnings()
    logger.info(f"Generated {len(warnings)} early warnings")
    
    for warning in warnings[:2]:  # Show first 2 warnings
        logger.info(f"  Warning: {warning['type']} - {warning['message']}")
    
    # Example 4: Performance forecasting
    logger.info("Generating performance forecast...")
    forecast = await predictive_service.forecast_performance(time_horizon=12)
    logger.info(f"Forecast confidence: {forecast.get('confidence', 0):.3f}")
    
    logger.info("Predictive analytics example completed\n")


async def example_recommendations(recommendation_engine: RecommendationEngine):
    """Example of using the recommendation engine."""
    logger.info("=== Recommendation Engine Example ===")
    
    # Generate optimization recommendations
    logger.info("Generating optimization recommendations...")
    recommendations = await recommendation_engine.generate_optimization_recommendations()
    logger.info(f"Generated {len(recommendations)} recommendations")
    
    # Display top recommendations
    for i, rec in enumerate(recommendations[:3]):
        logger.info(f"Recommendation {i+1}:")
        logger.info(f"  Type: {rec.recommendation_type.value}")
        logger.info(f"  Target: {rec.target_component}")
        logger.info(f"  Priority: {rec.priority_score:.3f}")
        logger.info(f"  Action: {rec.recommendation_data.get('action', 'N/A')}")
        logger.info(f"  Description: {rec.recommendation_data.get('description', 'N/A')}")
    
    # Generate workflow-specific recommendations
    logger.info("Generating workflow-specific recommendations...")
    workflow_recs = await recommendation_engine.suggest_workflow_improvements("workflow_123")
    logger.info(f"Generated {len(workflow_recs)} workflow recommendations")
    
    # Generate configuration recommendations
    logger.info("Generating configuration recommendations...")
    config_recs = await recommendation_engine.recommend_configuration_changes()
    logger.info(f"Generated {len(config_recs)} configuration recommendations")
    
    logger.info("Recommendation engine example completed\n")


async def example_model_management(model_manager: ModelManager):
    """Example of using the model manager."""
    logger.info("=== Model Management Example ===")
    
    # Generate sample training data
    training_data = generate_sample_training_data()
    
    # Train models
    logger.info("Training models...")
    training_results = await model_manager.train_models(training_data)
    logger.info(f"Training completed for {len(training_results)} models")
    
    for model_name, results in training_results.items():
        logger.info(f"  {model_name}: accuracy = {results.get('test_accuracy', 0):.3f}")
    
    # Evaluate model performance
    if model_manager.models:
        model_id = list(model_manager.models.keys())[0]
        logger.info(f"Evaluating model performance for: {model_id}")
        
        performance_metrics = await model_manager.evaluate_model_performance(model_id)
        logger.info(f"  Accuracy: {performance_metrics.accuracy:.3f}")
        logger.info(f"  F1 Score: {performance_metrics.f1_score:.3f}")
        
        # Check for model drift
        logger.info("Checking for model drift...")
        drift_analysis = await model_manager.check_model_drift(model_id)
        logger.info(f"  Drift detected: {drift_analysis.get('drift_detected', False)}")
        logger.info(f"  Recommendation: {drift_analysis.get('recommendation', 'N/A')}")
    
    logger.info("Model management example completed\n")


async def example_end_to_end_workflow(
    data_pipeline: DataPipeline,
    pattern_engine: PatternDetectionEngine,
    predictive_service: PredictiveAnalyticsService,
    recommendation_engine: RecommendationEngine,
    model_manager: ModelManager
):
    """Example of an end-to-end pattern analysis workflow."""
    logger.info("=== End-to-End Workflow Example ===")
    
    # Step 1: Extract and process data
    logger.info("Step 1: Data extraction and processing")
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=6)
    
    time_range = TimeRange(
        start_timestamp=start_time.timestamp(),
        end_timestamp=end_time.timestamp()
    )
    
    raw_data = await data_pipeline.extract_historical_data(time_range)
    if raw_data.empty:
        raw_data = generate_sample_performance_data()  # Use sample data
    
    processed_data = await data_pipeline.preprocess_data(raw_data)
    
    # Step 2: Detect patterns
    logger.info("Step 2: Pattern detection")
    patterns = await pattern_engine.detect_patterns(processed_data)
    classified_patterns = await pattern_engine.classify_patterns(patterns)
    
    # Step 3: Generate predictions
    logger.info("Step 3: Predictive analytics")
    warnings = await predictive_service.generate_early_warnings()
    
    # Step 4: Generate recommendations based on patterns
    logger.info("Step 4: Recommendation generation")
    pattern_recommendations = await recommendation_engine.generate_pattern_based_recommendations(classified_patterns)
    
    # Step 5: Train models if needed
    logger.info("Step 5: Model training (if needed)")
    if len(processed_data) >= 100:  # Minimum data for training
        training_results = await model_manager.train_models(processed_data)
        logger.info(f"Trained {len(training_results)} models")
    
    # Summary
    logger.info("=== Workflow Summary ===")
    logger.info(f"Processed {len(processed_data)} records")
    logger.info(f"Detected {len(classified_patterns)} patterns")
    logger.info(f"Generated {len(warnings)} early warnings")
    logger.info(f"Created {len(pattern_recommendations)} recommendations")
    
    logger.info("End-to-end workflow example completed\n")


def generate_sample_performance_data() -> pd.DataFrame:
    """Generate sample performance data for demonstration."""
    np.random.seed(42)
    
    # Generate timestamps for the last 24 hours
    end_time = datetime.utcnow()
    timestamps = [end_time - timedelta(hours=i) for i in range(24, 0, -1)]
    
    data = []
    for i, timestamp in enumerate(timestamps):
        # Simulate different types of data
        for module in ['task_execution', 'pipeline_orchestration', 'resource_management']:
            record = {
                'timestamp': timestamp,
                'module': module,
                'data_type': f'{module.split("_")[0]}_metrics',
                'duration': np.random.normal(120, 30),
                'cpu_usage': np.random.normal(0.6, 0.15),
                'memory_usage': np.random.normal(0.55, 0.12),
                'success_rate': np.random.normal(0.95, 0.05),
                'throughput': np.random.normal(100, 20),
                'error_rate': np.random.exponential(0.02),
                'task_count': np.random.poisson(10),
                'complexity_score': np.random.uniform(0.1, 1.0)
            }
            
            # Add some patterns and anomalies
            if i % 6 == 0:  # Every 6 hours, simulate high load
                record['cpu_usage'] *= 1.5
                record['memory_usage'] *= 1.3
                record['duration'] *= 1.4
            
            if i % 12 == 0:  # Every 12 hours, simulate some failures
                record['success_rate'] *= 0.8
                record['error_rate'] *= 3
            
            data.append(record)
    
    return pd.DataFrame(data)


def generate_sample_training_data() -> pd.DataFrame:
    """Generate sample training data for model training."""
    np.random.seed(42)
    
    data = []
    for i in range(500):  # Generate 500 training samples
        record = {
            'timestamp': datetime.utcnow() - timedelta(hours=i),
            'module': np.random.choice(['task_execution', 'pipeline_orchestration', 'resource_management']),
            'data_type': 'task_metrics',
            'duration': np.random.normal(120, 30),
            'cpu_usage': np.random.normal(0.6, 0.15),
            'memory_usage': np.random.normal(0.55, 0.12),
            'success': np.random.choice([True, False], p=[0.9, 0.1]),
            'task_type': np.random.choice(['analysis', 'transformation', 'validation']),
            'complexity_score': np.random.uniform(0.1, 1.0),
            'resource_efficiency': np.random.uniform(0.5, 1.0)
        }
        data.append(record)
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())

