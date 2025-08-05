"""
Basic usage example for OpenEvolve Integration with Graph-sitter

This example demonstrates how to use the OpenEvolve integration to evolve code
with continuous learning and comprehensive context tracking.
"""

import asyncio
import logging
from pathlib import Path

from graph_sitter.codebase import Codebase
from graph_sitter.extensions.openevolve import (
    OpenEvolveIntegration,
    OpenEvolveConfig
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_evolution_example():
    """
    Basic example of using OpenEvolve integration to evolve a Python file.
    """
    # Initialize codebase
    codebase_path = Path("./example_codebase")
    codebase = Codebase(codebase_path)
    
    # Create configuration
    config = OpenEvolveConfig()
    config.debug_mode = True
    config.evolution.max_iterations = 10
    config.learning.min_training_samples = 5
    
    # Initialize OpenEvolve integration
    integration = OpenEvolveIntegration(
        codebase=codebase,
        config=config,
        database_path="./evolution_example.db"
    )
    
    try:
        # Start an evolution session
        session_id = await integration.start_evolution_session(
            target_files=["src/calculator.py"],
            objectives={
                "improve_performance": 0.8,
                "reduce_complexity": 0.7,
                "maintain_functionality": 1.0
            },
            max_iterations=10
        )
        
        logger.info(f"Started evolution session: {session_id}")
        
        # Evolve the calculator file
        evolution_result = await integration.evolve_code(
            file_path="src/calculator.py",
            evolution_prompt="Optimize the calculation methods for better performance while maintaining readability",
            context={
                "focus_areas": ["performance", "readability"],
                "constraints": ["maintain_api_compatibility"]
            }
        )
        
        logger.info("Evolution completed successfully")
        logger.info(f"Evolution metrics: {evolution_result.get('evolution_metrics', {})}")
        
        # Get insights from the evolution
        insights = await integration.get_evolution_insights()
        logger.info(f"Learning insights: {insights.get('learning_insights', {})}")
        
        # Optimize the evolution strategy based on results
        optimization_result = await integration.optimize_evolution_strategy()
        logger.info(f"Strategy optimization: {optimization_result}")
        
        # End the session and get final report
        final_report = await integration.end_evolution_session()
        logger.info("Session completed successfully")
        
        return final_report
        
    except Exception as e:
        logger.error(f"Evolution failed: {e}")
        raise


async def continuous_learning_example():
    """
    Example demonstrating continuous learning across multiple evolution sessions.
    """
    # Initialize with optimized configuration for learning
    config = OpenEvolveConfig().get_optimized_config("accuracy")
    
    codebase = Codebase(Path("./example_codebase"))
    integration = OpenEvolveIntegration(codebase, config)
    
    # Run multiple evolution sessions to demonstrate learning
    files_to_evolve = [
        "src/calculator.py",
        "src/utils.py", 
        "src/data_processor.py"
    ]
    
    session_results = []
    
    for i, file_path in enumerate(files_to_evolve):
        logger.info(f"Starting evolution session {i+1} for {file_path}")
        
        # Start session
        session_id = await integration.start_evolution_session(
            target_files=[file_path],
            objectives={
                "code_quality": 0.8,
                "performance": 0.7,
                "maintainability": 0.9
            },
            max_iterations=15
        )
        
        # Evolve the file
        result = await integration.evolve_code(
            file_path=file_path,
            evolution_prompt=f"Improve code quality and performance for {file_path}",
            context={"session_number": i+1, "learning_enabled": True}
        )
        
        # Get insights to see how learning is progressing
        insights = await integration.get_evolution_insights()
        
        # End session
        final_report = await integration.end_evolution_session()
        session_results.append(final_report)
        
        logger.info(f"Session {i+1} completed. Learning confidence: {insights.get('learning_confidence', 0)}")
    
    # Analyze learning progression across sessions
    logger.info("Analyzing learning progression across sessions...")
    
    for i, result in enumerate(session_results):
        performance = result.get("performance", {})
        logger.info(f"Session {i+1} - Success rate: {performance.get('success_rate', 0):.2%}")
    
    return session_results


async def performance_monitoring_example():
    """
    Example demonstrating performance monitoring and analytics.
    """
    # Configure for performance monitoring
    config = OpenEvolveConfig()
    config.performance.enable_monitoring = True
    config.performance.generate_reports = True
    config.performance.bottleneck_detection_enabled = True
    
    codebase = Codebase(Path("./example_codebase"))
    integration = OpenEvolveIntegration(codebase, config)
    
    # Start session with performance monitoring
    session_id = await integration.start_evolution_session(
        target_files=["src/large_file.py"],
        objectives={"optimize_performance": 1.0},
        max_iterations=20
    )
    
    # Perform multiple evolution steps
    for i in range(5):
        await integration.evolve_code(
            file_path="src/large_file.py",
            evolution_prompt=f"Optimization step {i+1}: Focus on reducing execution time",
            context={"step_number": i+1}
        )
        
        # Get real-time performance analytics
        analytics = await integration.performance_monitor.get_session_analytics(session_id)
        
        logger.info(f"Step {i+1} - Avg execution time: {analytics.get('real_time_metrics', {}).get('avg_execution_time', 0):.2f}s")
        
        # Check for bottlenecks
        bottlenecks = analytics.get("performance_analysis", {}).get("bottlenecks", [])
        if bottlenecks:
            logger.warning(f"Bottlenecks detected: {[b['type'] for b in bottlenecks]}")
    
    # Generate comprehensive performance report
    performance_report = await integration.performance_monitor.generate_performance_report(
        session_id=session_id,
        include_recommendations=True
    )
    
    logger.info("Performance monitoring completed")
    logger.info(f"Recommendations: {len(performance_report.get('recommendations', []))}")
    
    await integration.end_evolution_session()
    return performance_report


async def pattern_recognition_example():
    """
    Example demonstrating pattern recognition and adaptive algorithms.
    """
    config = OpenEvolveConfig()
    config.learning.min_pattern_frequency = 2
    config.learning.pattern_confidence_threshold = 0.6
    
    codebase = Codebase(Path("./example_codebase"))
    integration = OpenEvolveIntegration(codebase, config)
    
    # Create patterns by repeating similar evolution tasks
    patterns_to_create = [
        {
            "file": "src/math_utils.py",
            "prompt": "Optimize mathematical calculations for speed",
            "context": {"focus": "performance", "domain": "math"}
        },
        {
            "file": "src/string_utils.py", 
            "prompt": "Optimize string processing for speed",
            "context": {"focus": "performance", "domain": "strings"}
        },
        {
            "file": "src/data_utils.py",
            "prompt": "Optimize data processing for speed", 
            "context": {"focus": "performance", "domain": "data"}
        }
    ]
    
    session_id = await integration.start_evolution_session(
        target_files=[p["file"] for p in patterns_to_create],
        objectives={"performance_optimization": 1.0},
        max_iterations=30
    )
    
    # Create patterns by repeating similar tasks
    for round_num in range(3):  # 3 rounds to establish patterns
        logger.info(f"Pattern creation round {round_num + 1}")
        
        for pattern in patterns_to_create:
            await integration.evolve_code(
                file_path=pattern["file"],
                evolution_prompt=pattern["prompt"],
                context={**pattern["context"], "round": round_num + 1}
            )
    
    # Get insights to see recognized patterns
    insights = await integration.get_evolution_insights()
    patterns = insights.get("context_patterns", {})
    
    logger.info(f"Recognized patterns: {len(patterns.get('step_patterns', []))}")
    logger.info(f"Pattern confidence: {patterns.get('analysis_timestamp', 0)}")
    
    # Test adaptive behavior with a new similar task
    logger.info("Testing adaptive behavior with new task...")
    
    adaptive_result = await integration.evolve_code(
        file_path="src/new_utils.py",
        evolution_prompt="Optimize computational algorithms for speed",
        context={"focus": "performance", "domain": "computation"}
    )
    
    # Check if learning system provided relevant suggestions
    applied_patterns = adaptive_result.get("applied_patterns", [])
    learning_insights = adaptive_result.get("learning_insights_used", [])
    
    logger.info(f"Applied patterns: {applied_patterns}")
    logger.info(f"Learning insights used: {learning_insights}")
    
    await integration.end_evolution_session()
    return insights


async def main():
    """
    Run all examples to demonstrate OpenEvolve integration capabilities.
    """
    logger.info("Starting OpenEvolve Integration Examples")
    
    try:
        # Basic usage example
        logger.info("\n=== Basic Evolution Example ===")
        basic_result = await basic_evolution_example()
        
        # Continuous learning example
        logger.info("\n=== Continuous Learning Example ===")
        learning_results = await continuous_learning_example()
        
        # Performance monitoring example
        logger.info("\n=== Performance Monitoring Example ===")
        performance_result = await performance_monitoring_example()
        
        # Pattern recognition example
        logger.info("\n=== Pattern Recognition Example ===")
        pattern_result = await pattern_recognition_example()
        
        logger.info("\n=== All Examples Completed Successfully ===")
        
        # Summary
        logger.info(f"Basic evolution success: {basic_result is not None}")
        logger.info(f"Learning sessions completed: {len(learning_results)}")
        logger.info(f"Performance monitoring active: {performance_result is not None}")
        logger.info(f"Patterns recognized: {pattern_result is not None}")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        raise


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())

