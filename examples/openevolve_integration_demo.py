#!/usr/bin/env python3
"""
OpenEvolve Integration & Evaluation System Demo

This demo script shows how to use the OpenEvolve integration system to evaluate
component effectiveness and generate performance analysis reports.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codegen.integration import (
    OpenEvolveIntegrator,
    DatabaseOverlay,
    EffectivenessEvaluator,
    PerformanceAnalyzer
)
from codegen.integration.openevolve.config import OpenEvolveConfig
from codegen.integration.analysis.optimization import OptimizationRecommender
from codegen.integration.analysis.reporting import AnalysisReporter


# Demo components to evaluate
class DemoEvaluatorComponent:
    """Demo evaluator component for testing."""
    
    def __init__(self):
        self.name = "DemoEvaluator"
    
    def evaluate(self, data):
        """Evaluate some data."""
        return sum(data) / len(data) if data else 0.0
    
    def assess(self, items):
        """Assess items."""
        return len([item for item in items if item > 0.5])


class DemoDatabaseComponent:
    """Demo database component for testing."""
    
    def __init__(self):
        self.name = "DemoDatabase"
        self.data = {}
    
    def save(self, key, value):
        """Save data."""
        self.data[key] = value
        return True
    
    def get(self, key):
        """Get data."""
        return self.data.get(key)
    
    def query(self, condition):
        """Query data."""
        return [v for k, v in self.data.items() if condition(v)]


class DemoControllerComponent:
    """Demo controller component for testing."""
    
    def __init__(self):
        self.name = "DemoController"
        self.state = "idle"
    
    def control(self, action):
        """Control action."""
        self.state = action
        return f"State changed to {action}"
    
    def manage(self, resources):
        """Manage resources."""
        return f"Managing {len(resources)} resources"


async def setup_logging():
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def demo_basic_integration():
    """Demonstrate basic OpenEvolve integration."""
    print("\n🧬 OpenEvolve Integration Demo - Basic Integration")
    print("=" * 60)
    
    # Create configuration
    config = OpenEvolveConfig(
        effectiveness_threshold=0.7,
        performance_sample_size=10,
        real_time_monitoring=True,
        enable_detailed_logging=True
    )
    
    # Initialize integrator
    async with OpenEvolveIntegrator(config) as integrator:
        print(f"✅ OpenEvolve integrator initialized")
        
        # Create demo components
        evaluator = DemoEvaluatorComponent()
        database = DemoDatabaseComponent()
        controller = DemoControllerComponent()
        
        print(f"✅ Demo components created")
        
        # Evaluate individual components
        print("\n📊 Evaluating Components:")
        
        # Evaluate evaluator component
        eval_result = await integrator.evaluate_component(
            component_type="evaluator",
            component_name="DemoEvaluator",
            component_instance=evaluator,
            evaluation_context={"test_data": [0.8, 0.9, 0.7, 0.85]}
        )
        
        print(f"  📈 Evaluator effectiveness: {eval_result.effectiveness_score:.3f}")
        print(f"     Execution time: {eval_result.execution_time_ms}ms")
        print(f"     Success: {eval_result.success}")
        
        # Evaluate database component
        db_result = await integrator.evaluate_component(
            component_type="database",
            component_name="DemoDatabase",
            component_instance=database,
            evaluation_context={"operations": ["save", "get", "query"]}
        )
        
        print(f"  💾 Database effectiveness: {db_result.effectiveness_score:.3f}")
        print(f"     Execution time: {db_result.execution_time_ms}ms")
        print(f"     Success: {db_result.success}")
        
        # Evaluate controller component
        ctrl_result = await integrator.evaluate_component(
            component_type="controller",
            component_name="DemoController",
            component_instance=controller,
            evaluation_context={"actions": ["start", "stop", "pause"]}
        )
        
        print(f"  🎮 Controller effectiveness: {ctrl_result.effectiveness_score:.3f}")
        print(f"     Execution time: {ctrl_result.execution_time_ms}ms")
        print(f"     Success: {ctrl_result.success}")
        
        # Get session summary
        summary = await integrator.get_session_summary()
        print(f"\n📋 Session Summary:")
        print(f"  Session ID: {summary.get('session_id', 'N/A')}")
        print(f"  Components evaluated: {len(summary.get('component_statistics', []))}")
        
        return integrator.current_session_id


async def demo_batch_evaluation():
    """Demonstrate batch evaluation of multiple components."""
    print("\n🔄 OpenEvolve Integration Demo - Batch Evaluation")
    print("=" * 60)
    
    config = OpenEvolveConfig(
        max_concurrent_evaluations=3,
        enable_caching=True
    )
    
    async with OpenEvolveIntegrator(config) as integrator:
        # Create multiple components
        components = {
            "evaluator": {
                "evaluator_1": DemoEvaluatorComponent(),
                "evaluator_2": DemoEvaluatorComponent()
            },
            "database": {
                "database_1": DemoDatabaseComponent(),
                "database_2": DemoDatabaseComponent()
            },
            "controller": {
                "controller_1": DemoControllerComponent()
            }
        }
        
        print(f"✅ Created {sum(len(comps) for comps in components.values())} components")
        
        # Evaluate all components concurrently
        print("\n🚀 Running batch evaluation...")
        results = await integrator.evaluate_all_components(
            components=components,
            evaluation_context={"batch_mode": True, "timestamp": "demo"}
        )
        
        print(f"✅ Evaluated {len(results)} components")
        
        # Display results
        print("\n📊 Batch Evaluation Results:")
        for component_name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"  {status} {component_name}: {result.effectiveness_score:.3f} ({result.execution_time_ms}ms)")
        
        return integrator.current_session_id


async def demo_performance_analysis(session_id: str):
    """Demonstrate performance analysis capabilities."""
    print("\n📈 OpenEvolve Integration Demo - Performance Analysis")
    print("=" * 60)
    
    config = OpenEvolveConfig()
    
    # Initialize database overlay
    async with DatabaseOverlay() as db_overlay:
        # Initialize performance analyzer
        analyzer = PerformanceAnalyzer(db_overlay, config)
        
        print(f"✅ Performance analyzer initialized")
        
        # Run comprehensive analysis
        print("\n🔍 Running performance analysis...")
        analysis_results = await analyzer.analyze_component_performance(
            session_id=session_id,
            time_window_hours=1.0  # Last hour
        )
        
        if 'error' in analysis_results:
            print(f"❌ Analysis failed: {analysis_results['error']}")
            return
        
        # Display analysis results
        print(f"✅ Analysis completed")
        print(f"\n📊 Performance Summary:")
        print(f"  Overall Performance Score: {analysis_results['performance_score']:.3f}")
        print(f"  Total Evaluations: {analysis_results['total_evaluations']}")
        
        # Show component summary
        component_summary = analysis_results.get('component_summary', {})
        print(f"\n🔧 Component Analysis:")
        for component_key, summary in component_summary.items():
            component_name = summary['component_name']
            avg_effectiveness = summary['effectiveness']['average']
            avg_time = summary['performance']['avg_execution_time_ms']
            print(f"  📦 {component_name}: {avg_effectiveness:.3f} effectiveness, {avg_time:.1f}ms avg time")
        
        # Show bottlenecks
        bottlenecks = analysis_results.get('bottleneck_analysis', [])
        if bottlenecks:
            print(f"\n⚠️  Identified Bottlenecks:")
            for bottleneck in bottlenecks[:3]:  # Show top 3
                severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(bottleneck.get('severity', 'low'), "⚪")
                print(f"  {severity_emoji} {bottleneck.get('component_name', 'Unknown')}: {bottleneck.get('description', 'No description')}")
        
        # Show optimization opportunities
        opportunities = analysis_results.get('optimization_opportunities', [])
        if opportunities:
            print(f"\n💡 Optimization Opportunities:")
            for opp in opportunities[:3]:  # Show top 3
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💫"}.get(opp.get('priority', 'low'), "💫")
                print(f"  {priority_emoji} {opp.get('component_name', 'Unknown')}: {opp.get('description', 'No description')}")
        
        return analysis_results


async def demo_optimization_recommendations(analysis_results: dict):
    """Demonstrate optimization recommendation generation."""
    print("\n💡 OpenEvolve Integration Demo - Optimization Recommendations")
    print("=" * 60)
    
    # Initialize optimization recommender
    recommender = OptimizationRecommender()
    
    print(f"✅ Optimization recommender initialized")
    
    # Convert analysis results to expected format
    bottlenecks = []
    for bottleneck_data in analysis_results.get('bottleneck_analysis', []):
        if isinstance(bottleneck_data, dict):
            bottlenecks.append(bottleneck_data)
    
    opportunities = analysis_results.get('optimization_opportunities', [])
    
    # Generate recommendations
    print(f"\n🎯 Generating optimization recommendations...")
    recommendations = await recommender.generate_recommendations(
        bottlenecks=bottlenecks,
        performance_data=analysis_results,
        optimization_opportunities=opportunities
    )
    
    print(f"✅ Generated {len(recommendations)} recommendations")
    
    # Display recommendations
    if recommendations:
        print(f"\n📋 Optimization Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
            priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(rec.priority, "⚪")
            effort_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(rec.effort_level, "⚪")
            
            print(f"\n  {i}. {rec.title}")
            print(f"     Priority: {priority_emoji} {rec.priority} | Effort: {effort_emoji} {rec.effort_level}")
            print(f"     Component: {rec.component_name}")
            print(f"     Impact: {rec.expected_impact}")
            print(f"     Steps: {len(rec.implementation_steps)} implementation steps")
    
    return recommendations


async def demo_comprehensive_reporting(session_id: str, analysis_results: dict, recommendations: list):
    """Demonstrate comprehensive reporting capabilities."""
    print("\n📄 OpenEvolve Integration Demo - Comprehensive Reporting")
    print("=" * 60)
    
    # Initialize reporter
    reporter = AnalysisReporter()
    
    print(f"✅ Analysis reporter initialized")
    
    # Generate comprehensive report
    print(f"\n📝 Generating comprehensive report...")
    
    # Generate JSON report
    json_report = await reporter.generate_comprehensive_report(
        session_id=session_id,
        analysis_results=analysis_results,
        recommendations=recommendations,
        format_type='json'
    )
    
    # Save JSON report
    json_file = f"openevolve_analysis_report_{session_id[:8]}.json"
    with open(json_file, 'w') as f:
        f.write(json_report)
    
    print(f"✅ JSON report saved: {json_file}")
    
    # Generate Markdown report
    markdown_report = await reporter.generate_comprehensive_report(
        session_id=session_id,
        analysis_results=analysis_results,
        recommendations=recommendations,
        format_type='markdown'
    )
    
    # Save Markdown report
    md_file = f"openevolve_analysis_report_{session_id[:8]}.md"
    with open(md_file, 'w') as f:
        f.write(markdown_report)
    
    print(f"✅ Markdown report saved: {md_file}")
    
    # Generate HTML report
    html_report = await reporter.generate_comprehensive_report(
        session_id=session_id,
        analysis_results=analysis_results,
        recommendations=recommendations,
        format_type='html'
    )
    
    # Save HTML report
    html_file = f"openevolve_analysis_report_{session_id[:8]}.html"
    with open(html_file, 'w') as f:
        f.write(html_report)
    
    print(f"✅ HTML report saved: {html_file}")
    
    print(f"\n📊 Report Summary:")
    print(f"  Session ID: {session_id}")
    print(f"  Generated files: {json_file}, {md_file}, {html_file}")
    print(f"  Total recommendations: {len(recommendations)}")


async def main():
    """Main demo function."""
    print("🧬 OpenEvolve Integration & Evaluation System Demo")
    print("=" * 60)
    print("This demo showcases the comprehensive OpenEvolve integration system")
    print("for evaluating component effectiveness and generating performance analysis.")
    print()
    
    await setup_logging()
    
    try:
        # Demo 1: Basic Integration
        session_id = await demo_basic_integration()
        
        # Demo 2: Batch Evaluation
        batch_session_id = await demo_batch_evaluation()
        
        # Use the batch session for analysis (more data)
        analysis_session_id = batch_session_id or session_id
        
        # Demo 3: Performance Analysis
        analysis_results = await demo_performance_analysis(analysis_session_id)
        
        if analysis_results and 'error' not in analysis_results:
            # Demo 4: Optimization Recommendations
            recommendations = await demo_optimization_recommendations(analysis_results)
            
            # Demo 5: Comprehensive Reporting
            await demo_comprehensive_reporting(analysis_session_id, analysis_results, recommendations)
        
        print("\n🎉 Demo completed successfully!")
        print("\nThe OpenEvolve Integration & Evaluation System provides:")
        print("  ✅ Component effectiveness evaluation")
        print("  ✅ Performance analysis and bottleneck detection")
        print("  ✅ Optimization recommendations")
        print("  ✅ Comprehensive reporting in multiple formats")
        print("  ✅ Real-time monitoring and correlation analysis")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

