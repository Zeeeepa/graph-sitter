#!/usr/bin/env python3
"""
OpenEvolve Integration Example

This example demonstrates how to use the comprehensive analysis system
with OpenEvolve for autonomous code improvement and evolution.
"""

import asyncio
import json
from pathlib import Path

from graph_sitter import Codebase
from graph_sitter.analysis.open_evolve_integration import (
    AnalysisContextManager,
    EvolutionTaskGenerator,
    EvolutionaryPatternLearner,
    AutonomousImprovementOrchestrator,
    create_analysis_context,
    generate_improvement_tasks,
    run_autonomous_improvement,
    format_context_for_prompt
)
from graph_sitter.analysis.enhanced_analysis import EnhancedCodebaseAnalyzer


async def demonstrate_context_generation():
    """Demonstrate rich context generation for OpenEvolve."""
    print("🔍 Generating Analysis Context for OpenEvolve")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Create analysis context
    context = await create_analysis_context(codebase, "global")
    
    print(f"📊 Analysis Context Generated:")
    print(f"   Health Score: {context.health_score:.2f}")
    print(f"   Technical Debt: {context.technical_debt_score:.2f}")
    print(f"   Maintainability: {context.maintainability_score:.2f}")
    print(f"   Documentation: {context.documentation_coverage:.1%}")
    print(f"   Test Coverage: {context.test_coverage:.1%}")
    
    print(f"\n🔍 Code Structure Insights:")
    print(f"   High Complexity Functions: {len(context.high_complexity_functions)}")
    print(f"   Low Cohesion Classes: {len(context.low_cohesion_classes)}")
    print(f"   Dead Code Items: {len(context.dead_code_items)}")
    print(f"   Circular Dependencies: {len(context.circular_dependencies)}")
    
    print(f"\n💡 Improvement Opportunities:")
    print(f"   Refactoring Candidates: {len(context.refactoring_candidates)}")
    print(f"   Unused Imports: {len(context.unused_imports)}")
    
    return context


async def demonstrate_task_generation():
    """Demonstrate evolutionary task generation."""
    print("\n🎯 Generating Evolutionary Tasks")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Generate improvement tasks
    tasks = await generate_improvement_tasks(codebase, max_tasks=5)
    
    print(f"📋 Generated {len(tasks)} improvement tasks:")
    
    for i, task in enumerate(tasks, 1):
        print(f"\n   Task {i}: {task.task_id}")
        print(f"   Description: {task.description}")
        print(f"   Target: {task.target_type} '{task.target_identifier}'")
        print(f"   Goal: {task.improvement_goal}")
        print(f"   Priority: {task.priority:.2f}")
        print(f"   Estimated Impact: {task.estimated_impact:.2f}")
        print(f"   Constraints: {', '.join(task.constraints[:2])}...")
        print(f"   Success Criteria: {len(task.success_criteria)} criteria")
    
    return tasks


async def demonstrate_context_formatting():
    """Demonstrate context formatting for OpenEvolve prompts."""
    print("\n📝 Context Formatting for OpenEvolve Prompts")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Create analysis context
    context = await create_analysis_context(codebase)
    
    # Format for prompt
    formatted_context = format_context_for_prompt(context)
    
    print("🤖 Formatted Context for OpenEvolve:")
    print(formatted_context)
    
    return formatted_context


async def demonstrate_autonomous_improvement():
    """Demonstrate autonomous improvement orchestration."""
    print("\n🚀 Autonomous Improvement Orchestration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Run autonomous improvement cycle
    print("🔄 Running autonomous improvement cycle...")
    results = await run_autonomous_improvement(codebase, max_iterations=3)
    
    print(f"\n📈 Autonomous Improvement Results:")
    print(f"   Iterations Completed: {results['iterations']}")
    print(f"   Tasks Completed: {results['tasks_completed']}")
    print(f"   Quality Improvements: {len(results['quality_improvements'])}")
    print(f"   Final Health Score: {results['final_health_score']:.2f}")
    
    if results['quality_improvements']:
        avg_improvement = sum(results['quality_improvements']) / len(results['quality_improvements'])
        print(f"   Average Quality Improvement: {avg_improvement:.3f}")
    
    print(f"\n🧠 Learning Insights:")
    insights = results['learning_insights']
    print(f"   Total Learning Sessions: {insights.get('total_learning_sessions', 0)}")
    print(f"   Success Rate: {insights.get('success_rate', 0):.1%}")
    
    pattern_effectiveness = insights.get('pattern_effectiveness', {})
    if pattern_effectiveness:
        print(f"   Pattern Effectiveness:")
        for pattern_type, effectiveness in pattern_effectiveness.items():
            print(f"     {pattern_type}: {effectiveness:.1%}")
    
    return results


async def demonstrate_advanced_integration():
    """Demonstrate advanced OpenEvolve integration features."""
    print("\n🔬 Advanced OpenEvolve Integration")
    print("=" * 60)
    
    # Initialize components
    codebase = Codebase(".")
    analyzer = EnhancedCodebaseAnalyzer(codebase, "advanced-demo")
    
    # Create context manager
    context_manager = AnalysisContextManager(analyzer)
    
    # Create task generator
    task_generator = EvolutionTaskGenerator(context_manager)
    
    # Create pattern learner
    pattern_learner = EvolutionaryPatternLearner(analyzer)
    
    # Create orchestrator
    orchestrator = AutonomousImprovementOrchestrator(codebase, analyzer)
    
    print("🏗️ Advanced Components Initialized:")
    print(f"   ✅ AnalysisContextManager")
    print(f"   ✅ EvolutionTaskGenerator") 
    print(f"   ✅ EvolutionaryPatternLearner")
    print(f"   ✅ AutonomousImprovementOrchestrator")
    
    # Generate context for specific task types
    print(f"\n🎯 Context Generation for Different Task Types:")
    
    task_types = ['global', 'function', 'class', 'module']
    for task_type in task_types:
        try:
            context = await context_manager.get_context_for_task(task_type)
            summary = context_manager.get_context_summary(context)
            print(f"\n   {task_type.title()} Context:")
            print(f"   Health: {context.health_score:.2f}, Debt: {context.technical_debt_score:.2f}")
            print(f"   Issues: {len(context.high_complexity_functions + context.low_cohesion_classes)}")
        except Exception as e:
            print(f"   {task_type.title()} Context: Error - {e}")
    
    # Demonstrate pattern learning
    print(f"\n🧠 Pattern Learning Capabilities:")
    insights = pattern_learner.get_learning_insights()
    print(f"   Learning Sessions: {insights['total_learning_sessions']}")
    print(f"   Success Rate: {insights['success_rate']:.1%}")
    print(f"   Pattern Database: {len(pattern_learner.pattern_database)} pattern types")
    
    return {
        'context_manager': context_manager,
        'task_generator': task_generator,
        'pattern_learner': pattern_learner,
        'orchestrator': orchestrator
    }


async def demonstrate_openevolve_prompt_enhancement():
    """Demonstrate how analysis context enhances OpenEvolve prompts."""
    print("\n🎨 OpenEvolve Prompt Enhancement")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Generate tasks
    tasks = await generate_improvement_tasks(codebase, max_tasks=2)
    
    if not tasks:
        print("   No tasks generated for demonstration")
        return
    
    # Demonstrate enhanced prompt generation
    for i, task in enumerate(tasks, 1):
        print(f"\n📝 Enhanced Prompt for Task {i}:")
        print(f"   Task: {task.description}")
        
        # Format context for prompt
        context_text = format_context_for_prompt(task.context)
        
        # Create enhanced prompt
        enhanced_prompt = f"""
        AUTONOMOUS CODE IMPROVEMENT TASK
        
        Objective: {task.improvement_goal}
        Target: {task.target_type} '{task.target_identifier}'
        Priority: {task.priority:.2f} (High: >0.8, Medium: 0.5-0.8, Low: <0.5)
        
        ANALYSIS CONTEXT:
        {context_text}
        
        CONSTRAINTS:
        {chr(10).join(f'- {constraint}' for constraint in task.constraints)}
        
        SUCCESS CRITERIA:
        {chr(10).join(f'- {criterion}' for criterion in task.success_criteria)}
        
        INSTRUCTIONS:
        Please generate improved code that addresses the objective while respecting
        the constraints and meeting the success criteria. Use the analysis context
        to understand the current codebase state and focus on the most impactful
        improvements.
        
        The generated code should:
        1. Solve the specific problem identified
        2. Improve the overall codebase health
        3. Follow best practices and patterns
        4. Be maintainable and well-documented
        """
        
        print(enhanced_prompt)
        print(f"\n   📊 Prompt Enhancement Benefits:")
        print(f"   ✅ Rich quality context (health score, technical debt)")
        print(f"   ✅ Specific improvement targets and priorities")
        print(f"   ✅ Clear constraints and success criteria")
        print(f"   ✅ Codebase-specific insights and patterns")
        print(f"   ✅ Measurable outcomes and validation")


async def main():
    """Main demonstration function."""
    print("🚀 OpenEvolve Integration Demonstration")
    print("=" * 80)
    print("This example shows how the comprehensive analysis system")
    print("integrates with OpenEvolve for autonomous code improvement.")
    print("=" * 80)
    
    try:
        # Demonstrate core capabilities
        context = await demonstrate_context_generation()
        tasks = await demonstrate_task_generation()
        formatted_context = await demonstrate_context_formatting()
        improvement_results = await demonstrate_autonomous_improvement()
        advanced_components = await demonstrate_advanced_integration()
        await demonstrate_openevolve_prompt_enhancement()
        
        # Summary
        print("\n🎉 Integration Demonstration Complete!")
        print("=" * 60)
        print("✅ Analysis Context Generation")
        print("✅ Evolutionary Task Generation")
        print("✅ Context Formatting for Prompts")
        print("✅ Autonomous Improvement Orchestration")
        print("✅ Advanced Component Integration")
        print("✅ Enhanced Prompt Generation")
        
        print(f"\n📊 Summary Statistics:")
        print(f"   Context Health Score: {context.health_score:.2f}")
        print(f"   Generated Tasks: {len(tasks)}")
        print(f"   Improvement Iterations: {improvement_results['iterations']}")
        print(f"   Final Health Score: {improvement_results['final_health_score']:.2f}")
        
        print(f"\n🚀 Ready for OpenEvolve Integration!")
        print(f"   The analysis system provides rich context for autonomous development")
        print(f"   Tasks are automatically generated based on code quality insights")
        print(f"   Pattern learning enables continuous improvement")
        print(f"   Orchestration manages the complete autonomous development cycle")
        
    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

