#!/usr/bin/env python3
"""
Enhanced Codebase AI with Comprehensive and Reactive Code Analysis Demo

This example demonstrates the comprehensive and reactive code analysis capabilities
of the enhanced codebase AI system, including:

- Comprehensive static analysis with quality metrics
- Reactive change tracking and impact analysis
- Context-aware AI responses with rich metadata
- Quality insights and health scoring
- Advanced dependency and relationship analysis
"""

import asyncio
import logging
from pathlib import Path

from graph_sitter import Codebase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_comprehensive_analysis():
    """Demonstrate comprehensive code analysis capabilities."""
    print("🔍 Comprehensive Code Analysis Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Get a sample function for analysis
    functions = codebase.functions
    if not functions:
        print("⚠️  No functions found in codebase")
        return
    
    target_function = functions[0]
    print(f"📍 Analyzing function: {target_function.name}")
    
    # Demonstrate comprehensive AI analysis
    response = await codebase.ai(
        "Analyze this function for code quality, complexity, and potential improvements. "
        "Provide specific recommendations based on the comprehensive analysis.",
        target=target_function,
        include_context=True,
        enable_reactive_analysis=True,
        include_quality_metrics=True
    )
    
    print(f"\n🤖 AI Analysis Response:")
    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    print(f"Response Time: {response.response_time:.2f}s")
    print(f"Tokens Used: {response.tokens_used}")
    print(f"Context Size: {response.context_size}")
    
    # Display quality insights
    quality_insights = response.get_quality_insights()
    if quality_insights:
        print(f"\n📊 Quality Insights:")
        for metric, value in quality_insights.items():
            if isinstance(value, float):
                print(f"   {metric.title()}: {value:.2f}")
            else:
                print(f"   {metric.title()}: {value}")
    
    # Display analysis metrics
    if response.analysis_metrics:
        print(f"\n📈 Analysis Metrics:")
        metrics = response.analysis_metrics
        print(f"   Complexity Score: {metrics.complexity_score:.2f}")
        print(f"   Maintainability Score: {metrics.maintainability_score:.2f}")
        print(f"   Documentation Coverage: {metrics.documentation_coverage:.1%}")
        print(f"   Test Coverage Estimate: {metrics.test_coverage_estimate:.1%}")
        print(f"   Dead Code Count: {metrics.dead_code_count}")
        print(f"   Code Smells: {len(metrics.code_smells)}")
        print(f"   Technical Debt Indicators: {len(metrics.technical_debt_indicators)}")
    
    # Display reactive context
    if response.reactive_context:
        print(f"\n🔄 Reactive Analysis Context:")
        context = response.reactive_context
        print(f"   File Changes: {len(context.file_changes)}")
        print(f"   Quality Deltas: {len(context.quality_deltas)}")
        print(f"   Dependency Changes: {len(context.dependency_changes)}")
        print(f"   Test Impact: {len(context.test_impact)}")
    
    print(f"\n💬 AI Response:")
    print(response.content)
    
    return response


async def demonstrate_reactive_analysis():
    """Demonstrate reactive code analysis with change tracking."""
    print("\n🔄 Reactive Code Analysis Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Get a sample class for analysis
    classes = codebase.classes
    if not classes:
        print("⚠️  No classes found in codebase")
        return
    
    target_class = classes[0]
    print(f"📍 Analyzing class: {target_class.name}")
    
    # Demonstrate reactive analysis with change impact
    response = await codebase.ai(
        "Analyze the impact of potential changes to this class. "
        "What components would be affected if we refactor this class? "
        "What are the risks and migration requirements?",
        target=target_class,
        include_context=True,
        enable_reactive_analysis=True,
        include_quality_metrics=True
    )
    
    print(f"\n🎯 Change Impact Analysis:")
    print(f"Response Time: {response.response_time:.2f}s")
    
    # Display comprehensive context information
    if response.metadata:
        print(f"\n📋 Analysis Metadata:")
        for key, value in response.metadata.items():
            print(f"   {key}: {value}")
    
    print(f"\n💬 Impact Analysis Response:")
    print(response.content)
    
    return response


async def demonstrate_context_aware_generation():
    """Demonstrate context-aware code generation."""
    print("\n🛠️  Context-Aware Code Generation Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Demonstrate context-aware code generation
    response = await codebase.ai(
        "Generate a comprehensive test suite for the most complex function in this codebase. "
        "Use the quality metrics and complexity analysis to determine which function needs "
        "the most thorough testing. Include edge cases, error conditions, and performance tests.",
        include_context=True,
        enable_reactive_analysis=True,
        include_quality_metrics=True
    )
    
    print(f"\n🧪 Test Generation Analysis:")
    print(f"Provider: {response.provider}")
    print(f"Response Time: {response.response_time:.2f}s")
    
    # Show quality insights for the generated recommendation
    quality_insights = response.get_quality_insights()
    if quality_insights:
        print(f"\n📊 Codebase Quality Overview:")
        overall_health = quality_insights.get("overall_health", 0)
        print(f"   Overall Health Score: {overall_health:.2f}")
        
        if overall_health < 0.7:
            print("   ⚠️  Codebase health is below recommended threshold")
        elif overall_health > 0.8:
            print("   ✅ Codebase health is good")
        else:
            print("   📊 Codebase health is moderate")
    
    print(f"\n💬 Generated Test Suite:")
    print(response.content)
    
    return response


async def demonstrate_quality_monitoring():
    """Demonstrate quality monitoring and insights."""
    print("\n📊 Quality Monitoring Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Analyze overall codebase quality
    response = await codebase.ai(
        "Provide a comprehensive quality assessment of this codebase. "
        "Identify the top 3 areas that need improvement and provide specific "
        "actionable recommendations for each area. Include priority levels.",
        include_context=True,
        enable_reactive_analysis=True,
        include_quality_metrics=True
    )
    
    print(f"\n🎯 Quality Assessment:")
    print(f"Analysis completed in {response.response_time:.2f}s")
    
    # Display comprehensive quality metrics
    if response.analysis_metrics:
        metrics = response.analysis_metrics
        print(f"\n📈 Detailed Quality Metrics:")
        print(f"   📊 Complexity Score: {metrics.complexity_score:.2f}")
        print(f"   🔧 Maintainability: {metrics.maintainability_score:.2f}")
        print(f"   📚 Documentation: {metrics.documentation_coverage:.1%}")
        print(f"   🧪 Test Coverage: {metrics.test_coverage_estimate:.1%}")
        print(f"   💀 Dead Code Items: {metrics.dead_code_count}")
        print(f"   🔄 Circular Dependencies: {metrics.circular_dependencies}")
        
        if metrics.code_smells:
            print(f"   👃 Code Smells: {metrics.code_smells}")
        
        if metrics.technical_debt_indicators:
            print(f"   💳 Technical Debt: {metrics.technical_debt_indicators}")
    
    # Calculate and display health score
    quality_insights = response.get_quality_insights()
    if quality_insights:
        health_score = quality_insights.get("overall_health", 0)
        print(f"\n🏥 Overall Health Score: {health_score:.2f}")
        
        # Provide health recommendations
        if health_score < 0.5:
            print("   🚨 CRITICAL: Immediate attention required")
            print("   Recommendations:")
            print("   - Focus on reducing complexity")
            print("   - Improve documentation coverage")
            print("   - Add comprehensive tests")
        elif health_score < 0.7:
            print("   ⚠️  WARNING: Improvement needed")
            print("   Recommendations:")
            print("   - Address technical debt")
            print("   - Improve maintainability")
            print("   - Enhance test coverage")
        else:
            print("   ✅ GOOD: Codebase is in good health")
            print("   Recommendations:")
            print("   - Maintain current quality standards")
            print("   - Continue monitoring for regressions")
    
    print(f"\n💬 Quality Assessment Report:")
    print(response.content)
    
    return response


async def demonstrate_dependency_analysis():
    """Demonstrate comprehensive dependency analysis."""
    print("\n🔗 Dependency Analysis Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Analyze dependencies and relationships
    response = await codebase.ai(
        "Analyze the dependency structure of this codebase. "
        "Identify potential circular dependencies, tight coupling issues, "
        "and suggest architectural improvements to reduce complexity.",
        include_context=True,
        enable_reactive_analysis=True,
        include_quality_metrics=True
    )
    
    print(f"\n🔍 Dependency Analysis:")
    print(f"Analysis completed in {response.response_time:.2f}s")
    
    # Display reactive context for dependencies
    if response.reactive_context:
        context = response.reactive_context
        print(f"\n📊 Dependency Context:")
        print(f"   Dependency Changes: {len(context.dependency_changes)}")
        
        if context.dependency_changes:
            print("   Recent dependency changes detected:")
            for change in context.dependency_changes[:5]:  # Show first 5
                print(f"   - {change}")
    
    print(f"\n💬 Dependency Analysis Report:")
    print(response.content)
    
    return response


async def main():
    """Run all demonstrations."""
    print("🚀 Enhanced Codebase AI with Comprehensive and Reactive Analysis")
    print("=" * 80)
    print("This demonstration showcases the advanced capabilities of the enhanced")
    print("codebase AI system with comprehensive static analysis and reactive")
    print("change tracking for superior code understanding and recommendations.")
    print()
    
    try:
        # Run all demonstrations
        await demonstrate_comprehensive_analysis()
        await demonstrate_reactive_analysis()
        await demonstrate_context_aware_generation()
        await demonstrate_quality_monitoring()
        await demonstrate_dependency_analysis()
        
        print("\n" + "=" * 80)
        print("✅ All demonstrations completed successfully!")
        print()
        print("🎯 Key Features Demonstrated:")
        print("   ✅ Comprehensive static analysis with quality metrics")
        print("   ✅ Reactive change tracking and impact analysis")
        print("   ✅ Context-aware AI responses with rich metadata")
        print("   ✅ Quality insights and health scoring")
        print("   ✅ Advanced dependency and relationship analysis")
        print("   ✅ Performance metrics and response optimization")
        print()
        print("🔧 Enhanced Capabilities:")
        print("   📊 Real-time quality metric calculation")
        print("   🔄 Change impact analysis and tracking")
        print("   🎯 Context-aware code generation and analysis")
        print("   📈 Comprehensive health scoring and insights")
        print("   🔗 Advanced dependency and coupling analysis")
        print("   ⚡ Optimized performance with intelligent caching")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        print(f"\n❌ Error during demonstration: {e}")


if __name__ == "__main__":
    asyncio.run(main())

