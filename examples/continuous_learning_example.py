"""
Example usage of the Continuous Learning System & Pattern Recognition

This example demonstrates how to use the continuous learning engine
for pattern analysis, workflow optimization, and outcome prediction.
"""

import asyncio
from src.learning import ContinuousLearningEngine, LearningConfig

async def main():
    """Example usage of the continuous learning system."""
    
    # Initialize the learning engine
    config = LearningConfig(
        model_update_interval=3600,
        pattern_analysis_window=86400,
        prediction_confidence_threshold=0.8,
        optimization_target_metrics=['build_time', 'test_success_rate', 'code_quality_score'],
        enable_real_time_learning=True,
        max_concurrent_analyses=10
    )
    
    learning_engine = ContinuousLearningEngine(config)
    
    print("🔬 Continuous Learning System Example")
    print("=" * 50)
    
    # Example 1: Pattern Analysis
    print("\n1. Pattern Analysis Example")
    print("-" * 30)
    
    pattern_results = await learning_engine.analyze_patterns(
        data_type='code_quality',
        timeframe='24h'
    )
    
    print(f"Pattern Type: {pattern_results.get('pattern_type')}")
    print(f"Confidence Score: {pattern_results.get('confidence_score', 0):.2%}")
    print(f"Analysis Duration: {pattern_results.get('analysis_metadata', {}).get('analysis_duration_ms', 0):.0f}ms")
    print(f"Trends: {pattern_results.get('trends', {})}")
    print(f"Recommendations: {pattern_results.get('recommendations', [])}")
    
    # Example 2: Workflow Optimization
    print("\n2. Workflow Optimization Example")
    print("-" * 35)
    
    optimization_results = await learning_engine.optimize_workflow(
        workflow_id='build-pipeline-001',
        context={
            'team_size': 8,
            'project_complexity': 'high',
            'performance_target': 'speed'
        }
    )
    
    print(f"Workflow ID: {optimization_results.get('workflow_id')}")
    print(f"Confidence Score: {optimization_results.get('confidence_score', 0):.2%}")
    print(f"Optimizations Found: {len(optimization_results.get('optimizations', []))}")
    print(f"Expected Improvements: {optimization_results.get('expected_improvements', {})}")
    
    # Example 3: Outcome Prediction
    print("\n3. Outcome Prediction Example")
    print("-" * 32)
    
    prediction_results = await learning_engine.predict_outcomes(
        scenario={
            'prediction_type': 'build_success',
            'complexity': 'medium',
            'team_experience': 'high',
            'code_changes': 150,
            'test_coverage': 85
        }
    )
    
    print(f"Prediction Value: {prediction_results.get('prediction', {}).get('value', 0):.2%}")
    print(f"Confidence: {prediction_results.get('prediction', {}).get('confidence', 0):.2%}")
    print(f"Models Used: {prediction_results.get('prediction_metadata', {}).get('models_used', [])}")
    print(f"Feature Importance: {prediction_results.get('feature_importance', {})}")
    
    print("\n✅ Continuous Learning System Example Completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
