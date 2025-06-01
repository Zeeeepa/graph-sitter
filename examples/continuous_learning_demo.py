"""
Continuous Learning and Analytics System Demo

This example demonstrates how to use the continuous learning system
to analyze codebases, identify patterns, and generate recommendations.
"""

import asyncio
import time
from graph_sitter import Codebase
from src.continuous_learning import (
    PatternEngine, 
    KnowledgeGraph, 
    AnalyticsProcessor, 
    ContinuousLearningPipeline
)


async def demo_continuous_learning():
    """Demonstrate the continuous learning system."""
    print("🚀 Continuous Learning and Analytics System Demo")
    print("=" * 60)
    
    # Initialize the continuous learning pipeline
    print("\n1. Initializing Continuous Learning Pipeline...")
    pipeline = ContinuousLearningPipeline()
    await pipeline.start_pipeline()
    
    # Load a codebase for analysis
    print("\n2. Loading Codebase...")
    try:
        # Use the current repository as an example
        codebase = Codebase.from_repo("codegen-sh/graph-sitter", language="python")
        print(f"   ✅ Loaded codebase with {len(list(codebase.files))} files")
    except Exception as e:
        print(f"   ❌ Error loading codebase: {e}")
        return
    
    # Process the codebase through the learning pipeline
    print("\n3. Processing Codebase through Learning Pipeline...")
    start_time = time.time()
    
    try:
        result = await pipeline.process_codebase(codebase)
        processing_time = time.time() - start_time
        
        print(f"   ✅ Processing completed in {processing_time:.2f} seconds")
        
        # Display results
        print("\n4. Analysis Results:")
        print(f"   📊 Patterns Identified: {len(result['patterns'])}")
        print(f"   💡 Recommendations Generated: {len(result['recommendations'])}")
        
        # Show top patterns
        print("\n   🔍 Top Patterns Identified:")
        for i, pattern in enumerate(result['patterns'][:3], 1):
            print(f"      {i}. {pattern['description']} (confidence: {pattern['confidence']:.2f})")
        
        # Show top recommendations
        print("\n   💡 Top Recommendations:")
        for i, rec in enumerate(result['recommendations'][:3], 1):
            print(f"      {i}. {rec.get('title', 'Recommendation')} (confidence: {rec.get('confidence', 0):.2f})")
        
    except Exception as e:
        print(f"   ❌ Error processing codebase: {e}")
        return
    
    # Demonstrate feedback submission
    print("\n5. Demonstrating Feedback Submission...")
    if result['patterns']:
        pattern_id = result['patterns'][0]['pattern_id']
        
        # Submit positive feedback
        success = await pipeline.submit_feedback(
            pattern_id, 
            "positive", 
            {"comment": "This pattern identification was very helpful!"}
        )
        
        if success:
            print(f"   ✅ Submitted positive feedback for pattern: {pattern_id}")
        else:
            print(f"   ❌ Failed to submit feedback")
    
    # Demonstrate performance metrics submission
    print("\n6. Demonstrating Performance Metrics...")
    success = await pipeline.submit_performance_metrics(
        "pattern_recognition",
        {
            "baseline_duration": 2.0,
            "current_duration": 1.5,
            "accuracy": 0.85
        }
    )
    
    if success:
        print("   ✅ Submitted performance metrics")
    else:
        print("   ❌ Failed to submit performance metrics")
    
    # Show pipeline statistics
    print("\n7. Pipeline Statistics:")
    stats = pipeline.get_pipeline_statistics()
    
    print(f"   📈 Signals Processed: {stats['pipeline_stats']['signals_processed']}")
    print(f"   🔄 Patterns Updated: {stats['pipeline_stats']['patterns_updated']}")
    print(f"   💡 Recommendations Generated: {stats['pipeline_stats']['recommendations_generated']}")
    print(f"   ❌ Errors: {stats['pipeline_stats']['errors']}")
    
    # Show learning insights
    print("\n8. Learning Insights:")
    insights = pipeline.get_learning_insights(codebase)
    
    print(f"   🎯 Learning Effectiveness: {insights['learning_effectiveness']:.2%}")
    print(f"   📊 Average Pattern Confidence: {insights['pattern_confidence_avg']:.2f}")
    print(f"   🔍 High Confidence Patterns: {insights['high_confidence_patterns']}")
    
    # Stop the pipeline
    print("\n9. Stopping Pipeline...")
    await pipeline.stop_pipeline()
    print("   ✅ Pipeline stopped successfully")
    
    print("\n🎉 Demo completed successfully!")


async def demo_individual_components():
    """Demonstrate individual components of the system."""
    print("\n" + "=" * 60)
    print("🔧 Individual Components Demo")
    print("=" * 60)
    
    # Load codebase
    try:
        codebase = Codebase.from_repo("codegen-sh/graph-sitter", language="python")
    except Exception as e:
        print(f"❌ Error loading codebase: {e}")
        return
    
    # 1. Pattern Engine Demo
    print("\n1. Pattern Engine Demo:")
    pattern_engine = PatternEngine()
    patterns = pattern_engine.identify_patterns(codebase)
    
    print(f"   🔍 Identified {len(patterns)} patterns")
    for pattern in patterns[:2]:
        print(f"      - {pattern.description} (confidence: {pattern.confidence:.2f})")
    
    # Get recommendations from pattern engine
    recommendations = pattern_engine.get_pattern_recommendations(codebase)
    print(f"   💡 Generated {len(recommendations)} recommendations")
    
    # 2. Knowledge Graph Demo
    print("\n2. Knowledge Graph Demo:")
    knowledge_graph = KnowledgeGraph()
    
    # Add patterns to knowledge graph
    for pattern in patterns[:3]:
        node_id = knowledge_graph.add_pattern(pattern)
        print(f"   ➕ Added pattern to knowledge graph: {node_id[:8]}...")
    
    # Get graph statistics
    graph_stats = knowledge_graph.get_graph_statistics()
    print(f"   📊 Knowledge graph contains {graph_stats.get('code_pattern_count', 0)} patterns")
    
    # 3. Analytics Processor Demo
    print("\n3. Analytics Processor Demo:")
    analytics_processor = AnalyticsProcessor()
    
    # Process codebase analysis
    analysis_result = await analytics_processor.process_codebase_analysis(codebase)
    
    print(f"   📈 Analysis completed with quality score: {analysis_result.get('quality_score', 'N/A')}")
    
    # Get dashboard data
    dashboard_data = analytics_processor.get_analytics_dashboard_data()
    print(f"   📊 Dashboard data includes {len(dashboard_data.get('metrics_summary', {}))} metric summaries")
    
    print("\n✅ Individual components demo completed!")


def demo_enhanced_codebase_analysis():
    """Demonstrate enhanced codebase analysis integration."""
    print("\n" + "=" * 60)
    print("🔬 Enhanced Codebase Analysis Demo")
    print("=" * 60)
    
    # Import the enhanced analyzer
    from src.continuous_learning.analytics_processor import EnhancedCodebaseAnalyzer
    
    try:
        codebase = Codebase.from_repo("codegen-sh/graph-sitter", language="python")
    except Exception as e:
        print(f"❌ Error loading codebase: {e}")
        return
    
    # Create enhanced analyzer
    enhanced_analyzer = EnhancedCodebaseAnalyzer()
    
    print("\n1. Running Enhanced Analysis...")
    analysis_result = enhanced_analyzer.enhanced_analysis(codebase)
    
    # Display base summary
    print("\n2. Base Summary:")
    base_summary = analysis_result['base_summary']
    print(f"   📁 Files: {base_summary.count('files')}")
    print(f"   🔧 Functions: {base_summary.count('functions')}")
    print(f"   📦 Classes: {base_summary.count('classes')}")
    
    # Display current metrics
    print("\n3. Current Metrics:")
    metrics = analysis_result['current_metrics']
    for metric_name, value in metrics.items():
        print(f"   📊 {metric_name}: {value:.2f}")
    
    # Display quality score
    quality_score = analysis_result['quality_score']
    print(f"\n4. Quality Score: {quality_score:.1f}/100")
    
    # Display recommendations
    recommendations = analysis_result['recommendations']
    if recommendations:
        print("\n5. Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n5. No specific recommendations at this time.")
    
    print("\n✅ Enhanced analysis demo completed!")


async def main():
    """Main demo function."""
    print("🎯 Continuous Learning and Analytics System")
    print("   Research Implementation Demo")
    print("=" * 60)
    
    try:
        # Run main continuous learning demo
        await demo_continuous_learning()
        
        # Run individual components demo
        await demo_individual_components()
        
        # Run enhanced analysis demo
        demo_enhanced_codebase_analysis()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Demo session completed!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())

