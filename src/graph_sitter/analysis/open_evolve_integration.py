"""
OpenEvolve Integration for Autonomous Development

This module provides integration between the comprehensive analysis system
and the OpenEvolve autonomous algorithmic evolution framework, enabling
context-aware code generation and autonomous system improvement.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

from graph_sitter import Codebase
from .enhanced_analysis import EnhancedCodebaseAnalyzer, AnalysisReport
from .metrics import MetricsCalculator, FunctionMetrics, ClassMetrics
from .call_graph import CallGraphAnalyzer
from .dependency_analyzer import DependencyAnalyzer
from .dead_code import DeadCodeDetector

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Rich analysis context for OpenEvolve agents."""
    
    # Quality metrics
    health_score: float
    technical_debt_score: float
    maintainability_score: float
    complexity_score: float
    documentation_coverage: float
    test_coverage: float
    
    # Code structure insights
    call_graph_patterns: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    dead_code_items: List[Dict[str, Any]]
    circular_dependencies: List[Dict[str, Any]]
    
    # Improvement opportunities
    high_complexity_functions: List[Dict[str, Any]]
    low_cohesion_classes: List[Dict[str, Any]]
    unused_imports: List[Dict[str, Any]]
    refactoring_candidates: List[Dict[str, Any]]
    
    # Historical trends (if available)
    quality_trends: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None


@dataclass
class EvolutionTask:
    """Task definition for evolutionary improvement."""
    
    task_id: str
    description: str
    target_type: str  # 'function', 'class', 'module', 'system'
    target_identifier: str
    improvement_goal: str
    context: AnalysisContext
    priority: float
    estimated_impact: float
    constraints: List[str]
    success_criteria: List[str]


@dataclass
class EvolutionResult:
    """Result of evolutionary improvement."""
    
    task_id: str
    success: bool
    generated_code: Optional[str]
    quality_improvement: float
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    issues_resolved: List[str]
    new_issues: List[str]
    confidence_score: float
    explanation: str


class AnalysisContextManager:
    """Manages rich analysis context for OpenEvolve agents."""
    
    def __init__(self, analysis_system: EnhancedCodebaseAnalyzer):
        self.analysis_system = analysis_system
        self.context_cache: Dict[str, AnalysisContext] = {}
        self.pattern_database: Dict[str, Any] = {}
    
    async def get_context_for_task(self, task_type: str, target_identifier: str = None) -> AnalysisContext:
        """Get relevant analysis context for evolutionary task."""
        try:
            cache_key = f"{task_type}:{target_identifier or 'global'}"
            
            if cache_key in self.context_cache:
                return self.context_cache[cache_key]
            
            # Run comprehensive analysis
            logger.info(f"Generating analysis context for {task_type} task")
            
            # Get overall health metrics
            health_data = self.analysis_system.get_codebase_health_score()
            
            # Get call graph analysis
            call_graph_data = self.analysis_system.call_graph_analyzer.analyze_call_patterns()
            
            # Get dependency analysis
            dependency_data = self.analysis_system.dependency_analyzer.analyze_imports()
            
            # Get dead code analysis
            dead_code_items = self.analysis_system.dead_code_detector.find_dead_code()
            
            # Find circular dependencies
            circular_deps = self.analysis_system.dependency_analyzer.find_circular_dependencies()
            
            # Identify improvement opportunities
            improvement_opportunities = await self._identify_improvement_opportunities()
            
            context = AnalysisContext(
                health_score=health_data.get('overall_health_score', 0.0),
                technical_debt_score=health_data.get('component_scores', {}).get('technical_debt', 0.0),
                maintainability_score=health_data.get('component_scores', {}).get('maintainability', 0.0),
                complexity_score=health_data.get('component_scores', {}).get('complexity', 0.0),
                documentation_coverage=health_data.get('component_scores', {}).get('documentation', 0.0),
                test_coverage=health_data.get('component_scores', {}).get('test_coverage', 0.0),
                call_graph_patterns=call_graph_data,
                dependency_analysis=asdict(dependency_data),
                dead_code_items=[asdict(item) for item in dead_code_items],
                circular_dependencies=[asdict(dep) for dep in circular_deps],
                high_complexity_functions=improvement_opportunities['high_complexity_functions'],
                low_cohesion_classes=improvement_opportunities['low_cohesion_classes'],
                unused_imports=improvement_opportunities['unused_imports'],
                refactoring_candidates=improvement_opportunities['refactoring_candidates']
            )
            
            self.context_cache[cache_key] = context
            return context
            
        except Exception as e:
            logger.error(f"Error generating analysis context: {e}")
            # Return minimal context on error
            return AnalysisContext(
                health_score=0.0, technical_debt_score=1.0, maintainability_score=0.0,
                complexity_score=1.0, documentation_coverage=0.0, test_coverage=0.0,
                call_graph_patterns={}, dependency_analysis={}, dead_code_items=[],
                circular_dependencies=[], high_complexity_functions=[], low_cohesion_classes=[],
                unused_imports=[], refactoring_candidates=[]
            )
    
    async def _identify_improvement_opportunities(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identify specific improvement opportunities."""
        opportunities = {
            'high_complexity_functions': [],
            'low_cohesion_classes': [],
            'unused_imports': [],
            'refactoring_candidates': []
        }
        
        try:
            # Find high complexity functions
            for function in self.analysis_system.codebase.functions:
                try:
                    metrics = self.analysis_system.metrics_calculator.analyze_function_metrics(function)
                    if metrics.cyclomatic_complexity > 10:
                        opportunities['high_complexity_functions'].append({
                            'name': metrics.name,
                            'complexity': metrics.cyclomatic_complexity,
                            'maintainability': metrics.maintainability_index,
                            'filepath': metrics.filepath,
                            'recommendation': 'Consider breaking down into smaller functions'
                        })
                except Exception as e:
                    logger.warning(f"Error analyzing function {getattr(function, 'name', 'unknown')}: {e}")
            
            # Find low cohesion classes
            for class_def in self.analysis_system.codebase.classes:
                try:
                    metrics = self.analysis_system.metrics_calculator.analyze_class_metrics(class_def)
                    if metrics.cohesion_score < 0.3:
                        opportunities['low_cohesion_classes'].append({
                            'name': metrics.name,
                            'cohesion_score': metrics.cohesion_score,
                            'method_count': metrics.method_count,
                            'filepath': metrics.filepath,
                            'recommendation': 'Consider splitting class or improving method cohesion'
                        })
                except Exception as e:
                    logger.warning(f"Error analyzing class {getattr(class_def, 'name', 'unknown')}: {e}")
            
            # Find unused imports
            dead_code_items = self.analysis_system.dead_code_detector.find_dead_code()
            for item in dead_code_items:
                if item.type == 'import' and item.confidence > 0.8:
                    opportunities['unused_imports'].append({
                        'symbol': item.symbol.name if item.symbol.name else 'unknown',
                        'confidence': item.confidence,
                        'reason': item.reason,
                        'safe_to_remove': item.safe_to_remove
                    })
            
            # Identify refactoring candidates
            for function in self.analysis_system.codebase.functions:
                try:
                    metrics = self.analysis_system.metrics_calculator.analyze_function_metrics(function)
                    if (metrics.cyclomatic_complexity > 7 and 
                        metrics.maintainability_index < 50 and
                        metrics.lines_of_code > 50):
                        opportunities['refactoring_candidates'].append({
                            'name': metrics.name,
                            'complexity': metrics.cyclomatic_complexity,
                            'maintainability': metrics.maintainability_index,
                            'lines_of_code': metrics.lines_of_code,
                            'filepath': metrics.filepath,
                            'recommendation': 'Prime candidate for refactoring'
                        })
                except Exception as e:
                    logger.warning(f"Error evaluating refactoring candidate {getattr(function, 'name', 'unknown')}: {e}")
            
        except Exception as e:
            logger.error(f"Error identifying improvement opportunities: {e}")
        
        return opportunities
    
    def get_context_summary(self, context: AnalysisContext) -> str:
        """Generate human-readable context summary."""
        summary = f"""
        Code Quality Context:
        - Health Score: {context.health_score:.2f}/1.0
        - Technical Debt: {context.technical_debt_score:.2f}
        - Maintainability: {context.maintainability_score:.2f}
        - Documentation: {context.documentation_coverage:.1%}
        
        Code Structure:
        - High Complexity Functions: {len(context.high_complexity_functions)}
        - Low Cohesion Classes: {len(context.low_cohesion_classes)}
        - Dead Code Items: {len(context.dead_code_items)}
        - Circular Dependencies: {len(context.circular_dependencies)}
        
        Improvement Opportunities:
        - Refactoring Candidates: {len(context.refactoring_candidates)}
        - Unused Imports: {len(context.unused_imports)}
        """
        return summary.strip()


class EvolutionTaskGenerator:
    """Generates evolutionary tasks based on analysis insights."""
    
    def __init__(self, context_manager: AnalysisContextManager):
        self.context_manager = context_manager
        self.task_templates = self._load_task_templates()
    
    async def generate_improvement_tasks(self, max_tasks: int = 5) -> List[EvolutionTask]:
        """Generate prioritized improvement tasks."""
        tasks = []
        
        try:
            # Get global context
            context = await self.context_manager.get_context_for_task('global')
            
            # Generate tasks based on analysis insights
            task_id = 0
            
            # High complexity function tasks
            for func_data in context.high_complexity_functions[:2]:  # Top 2
                task_id += 1
                task = EvolutionTask(
                    task_id=f"complexity_reduction_{task_id}",
                    description=f"Reduce complexity of function '{func_data['name']}'",
                    target_type='function',
                    target_identifier=func_data['name'],
                    improvement_goal=f"Reduce cyclomatic complexity from {func_data['complexity']} to below 7",
                    context=context,
                    priority=0.9,
                    estimated_impact=0.8,
                    constraints=['Preserve existing functionality', 'Maintain API compatibility'],
                    success_criteria=[
                        'Cyclomatic complexity < 7',
                        'All existing tests pass',
                        'Maintainability index > 60'
                    ]
                )
                tasks.append(task)
            
            # Low cohesion class tasks
            for class_data in context.low_cohesion_classes[:2]:  # Top 2
                task_id += 1
                task = EvolutionTask(
                    task_id=f"cohesion_improvement_{task_id}",
                    description=f"Improve cohesion of class '{class_data['name']}'",
                    target_type='class',
                    target_identifier=class_data['name'],
                    improvement_goal=f"Increase cohesion score from {class_data['cohesion_score']:.2f} to above 0.6",
                    context=context,
                    priority=0.7,
                    estimated_impact=0.6,
                    constraints=['Preserve class interface', 'Maintain inheritance relationships'],
                    success_criteria=[
                        'Cohesion score > 0.6',
                        'No breaking changes to public API',
                        'All tests pass'
                    ]
                )
                tasks.append(task)
            
            # Dead code cleanup tasks
            if context.dead_code_items:
                task_id += 1
                safe_items = [item for item in context.dead_code_items if item.get('safe_to_remove', False)]
                if safe_items:
                    task = EvolutionTask(
                        task_id=f"dead_code_cleanup_{task_id}",
                        description="Remove safe dead code items",
                        target_type='system',
                        target_identifier='codebase',
                        improvement_goal=f"Remove {len(safe_items)} dead code items safely",
                        context=context,
                        priority=0.5,
                        estimated_impact=0.4,
                        constraints=['Only remove items with high confidence', 'Preserve entry points'],
                        success_criteria=[
                            'All tests pass after removal',
                            'No runtime errors',
                            'Reduced codebase size'
                        ]
                    )
                    tasks.append(task)
            
            # Sort by priority and return top tasks
            tasks.sort(key=lambda t: t.priority, reverse=True)
            return tasks[:max_tasks]
            
        except Exception as e:
            logger.error(f"Error generating improvement tasks: {e}")
            return []
    
    def _load_task_templates(self) -> Dict[str, Any]:
        """Load task templates for different improvement types."""
        return {
            'complexity_reduction': {
                'prompt_template': """
                Analyze the following function and reduce its cyclomatic complexity:
                
                Function: {function_name}
                Current Complexity: {current_complexity}
                Target Complexity: < 7
                
                Context:
                {context_summary}
                
                Please refactor this function to reduce complexity while maintaining functionality.
                """,
                'evaluation_criteria': ['complexity', 'maintainability', 'functionality']
            },
            'cohesion_improvement': {
                'prompt_template': """
                Improve the cohesion of the following class:
                
                Class: {class_name}
                Current Cohesion: {current_cohesion}
                Target Cohesion: > 0.6
                
                Context:
                {context_summary}
                
                Please refactor this class to improve method cohesion.
                """,
                'evaluation_criteria': ['cohesion', 'coupling', 'maintainability']
            }
        }


class EvolutionaryPatternLearner:
    """Learns from evolutionary outcomes to improve analysis and generation."""
    
    def __init__(self, analysis_system: EnhancedCodebaseAnalyzer):
        self.analysis_system = analysis_system
        self.pattern_database: Dict[str, Any] = {}
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        self.learning_history: List[Dict[str, Any]] = []
    
    async def learn_from_evolution_result(self, result: EvolutionResult):
        """Learn patterns from evolutionary result."""
        try:
            learning_entry = {
                'timestamp': asyncio.get_event_loop().time(),
                'task_id': result.task_id,
                'success': result.success,
                'quality_improvement': result.quality_improvement,
                'confidence_score': result.confidence_score,
                'metrics_delta': self._calculate_metrics_delta(result.metrics_before, result.metrics_after),
                'patterns': await self._extract_code_patterns(result.generated_code) if result.generated_code else []
            }
            
            self.learning_history.append(learning_entry)
            
            if result.success and result.quality_improvement > 0.1:
                self.success_patterns.append(learning_entry)
                await self._update_success_heuristics(learning_entry)
            elif not result.success or result.quality_improvement < -0.05:
                self.failure_patterns.append(learning_entry)
                await self._update_failure_heuristics(learning_entry)
            
            # Update analysis system with learned patterns
            await self._update_analysis_heuristics()
            
        except Exception as e:
            logger.error(f"Error learning from evolution result: {e}")
    
    async def _extract_code_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Extract patterns from generated code."""
        patterns = []
        
        try:
            # Simple pattern extraction (can be enhanced with AST analysis)
            lines = code.split('\n')
            
            # Function patterns
            function_lines = [line for line in lines if 'def ' in line]
            if function_lines:
                patterns.append({
                    'type': 'function_definition',
                    'count': len(function_lines),
                    'avg_length': sum(len(line) for line in function_lines) / len(function_lines)
                })
            
            # Import patterns
            import_lines = [line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')]
            if import_lines:
                patterns.append({
                    'type': 'import_usage',
                    'count': len(import_lines),
                    'types': list(set(line.split()[0] for line in import_lines))
                })
            
            # Comment patterns
            comment_lines = [line for line in lines if line.strip().startswith('#')]
            if comment_lines:
                patterns.append({
                    'type': 'documentation',
                    'comment_ratio': len(comment_lines) / len(lines),
                    'avg_comment_length': sum(len(line) for line in comment_lines) / len(comment_lines)
                })
            
        except Exception as e:
            logger.warning(f"Error extracting code patterns: {e}")
        
        return patterns
    
    def _calculate_metrics_delta(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, float]:
        """Calculate the change in metrics."""
        delta = {}
        
        for key in before:
            if key in after and isinstance(before[key], (int, float)) and isinstance(after[key], (int, float)):
                delta[key] = after[key] - before[key]
        
        return delta
    
    async def _update_success_heuristics(self, learning_entry: Dict[str, Any]):
        """Update heuristics based on successful patterns."""
        try:
            # Extract successful patterns
            patterns = learning_entry.get('patterns', [])
            
            for pattern in patterns:
                pattern_type = pattern.get('type')
                if pattern_type not in self.pattern_database:
                    self.pattern_database[pattern_type] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'success_examples': [],
                        'characteristics': {}
                    }
                
                self.pattern_database[pattern_type]['success_count'] += 1
                self.pattern_database[pattern_type]['success_examples'].append(pattern)
                
        except Exception as e:
            logger.warning(f"Error updating success heuristics: {e}")
    
    async def _update_failure_heuristics(self, learning_entry: Dict[str, Any]):
        """Update heuristics based on failure patterns."""
        try:
            # Extract failure patterns
            patterns = learning_entry.get('patterns', [])
            
            for pattern in patterns:
                pattern_type = pattern.get('type')
                if pattern_type not in self.pattern_database:
                    self.pattern_database[pattern_type] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'failure_examples': [],
                        'characteristics': {}
                    }
                
                self.pattern_database[pattern_type]['failure_count'] += 1
                if 'failure_examples' not in self.pattern_database[pattern_type]:
                    self.pattern_database[pattern_type]['failure_examples'] = []
                self.pattern_database[pattern_type]['failure_examples'].append(pattern)
                
        except Exception as e:
            logger.warning(f"Error updating failure heuristics: {e}")
    
    async def _update_analysis_heuristics(self):
        """Update analysis system with learned patterns."""
        try:
            # Update analysis system with learned insights
            insights = self.get_learning_insights()
            
            # This could update analysis weights, thresholds, or recommendations
            logger.info(f"Updated analysis heuristics with {len(insights)} insights")
            
        except Exception as e:
            logger.warning(f"Error updating analysis heuristics: {e}")
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning history."""
        insights = {
            'total_learning_sessions': len(self.learning_history),
            'success_rate': len(self.success_patterns) / max(1, len(self.learning_history)),
            'pattern_effectiveness': {},
            'improvement_trends': {}
        }
        
        # Analyze pattern effectiveness
        for pattern_type, data in self.pattern_database.items():
            total = data['success_count'] + data['failure_count']
            if total > 0:
                insights['pattern_effectiveness'][pattern_type] = data['success_count'] / total
        
        return insights


class AutonomousImprovementOrchestrator:
    """Orchestrates autonomous improvement cycles."""
    
    def __init__(self, codebase: Codebase, analysis_system: EnhancedCodebaseAnalyzer):
        self.codebase = codebase
        self.analysis_system = analysis_system
        self.context_manager = AnalysisContextManager(analysis_system)
        self.task_generator = EvolutionTaskGenerator(self.context_manager)
        self.pattern_learner = EvolutionaryPatternLearner(analysis_system)
        self.improvement_history: List[Dict[str, Any]] = []
    
    async def run_autonomous_improvement_cycle(self, max_iterations: int = 10) -> Dict[str, Any]:
        """Run autonomous improvement cycle."""
        cycle_results = {
            'iterations': 0,
            'tasks_completed': 0,
            'quality_improvements': [],
            'learning_insights': {},
            'final_health_score': 0.0
        }
        
        try:
            logger.info("Starting autonomous improvement cycle")
            
            for iteration in range(max_iterations):
                logger.info(f"Autonomous improvement iteration {iteration + 1}/{max_iterations}")
                
                # Generate improvement tasks
                tasks = await self.task_generator.generate_improvement_tasks(max_tasks=3)
                
                if not tasks:
                    logger.info("No improvement tasks generated, ending cycle")
                    break
                
                # Execute tasks (this would integrate with OpenEvolve)
                for task in tasks:
                    result = await self._simulate_task_execution(task)
                    
                    if result.success:
                        cycle_results['tasks_completed'] += 1
                        cycle_results['quality_improvements'].append(result.quality_improvement)
                        
                        # Learn from successful result
                        await self.pattern_learner.learn_from_evolution_result(result)
                
                cycle_results['iterations'] += 1
                
                # Check if we've reached satisfactory quality
                current_health = self.analysis_system.get_codebase_health_score()
                if current_health.get('overall_health_score', 0) > 0.9:
                    logger.info("High quality achieved, ending improvement cycle")
                    break
            
            # Get final insights
            cycle_results['learning_insights'] = self.pattern_learner.get_learning_insights()
            cycle_results['final_health_score'] = self.analysis_system.get_codebase_health_score().get('overall_health_score', 0)
            
            logger.info(f"Autonomous improvement cycle completed: {cycle_results['tasks_completed']} tasks completed")
            return cycle_results
            
        except Exception as e:
            logger.error(f"Error in autonomous improvement cycle: {e}")
            return cycle_results
    
    async def _simulate_task_execution(self, task: EvolutionTask) -> EvolutionResult:
        """Simulate task execution (would integrate with OpenEvolve)."""
        # This is a simulation - in real implementation, this would call OpenEvolve
        try:
            # Simulate some improvement
            quality_improvement = 0.1 if task.priority > 0.7 else 0.05
            
            result = EvolutionResult(
                task_id=task.task_id,
                success=True,
                generated_code=f"# Improved code for {task.target_identifier}\\npass",
                quality_improvement=quality_improvement,
                metrics_before={'complexity': 10, 'maintainability': 40},
                metrics_after={'complexity': 7, 'maintainability': 60},
                issues_resolved=[f"Reduced complexity in {task.target_identifier}"],
                new_issues=[],
                confidence_score=0.8,
                explanation=f"Successfully improved {task.target_type} {task.target_identifier}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error simulating task execution: {e}")
            return EvolutionResult(
                task_id=task.task_id,
                success=False,
                generated_code=None,
                quality_improvement=0.0,
                metrics_before={},
                metrics_after={},
                issues_resolved=[],
                new_issues=[str(e)],
                confidence_score=0.0,
                explanation=f"Failed to execute task: {e}"
            )


# Convenience functions for integration

async def create_analysis_context(codebase: Codebase, task_type: str = 'global') -> AnalysisContext:
    """Create analysis context for OpenEvolve integration."""
    analyzer = EnhancedCodebaseAnalyzer(codebase, "openevolve-integration")
    context_manager = AnalysisContextManager(analyzer)
    return await context_manager.get_context_for_task(task_type)


async def generate_improvement_tasks(codebase: Codebase, max_tasks: int = 5) -> List[EvolutionTask]:
    """Generate improvement tasks based on codebase analysis."""
    analyzer = EnhancedCodebaseAnalyzer(codebase, "task-generation")
    context_manager = AnalysisContextManager(analyzer)
    task_generator = EvolutionTaskGenerator(context_manager)
    return await task_generator.generate_improvement_tasks(max_tasks)


async def run_autonomous_improvement(codebase: Codebase, max_iterations: int = 5) -> Dict[str, Any]:
    """Run autonomous improvement cycle."""
    analyzer = EnhancedCodebaseAnalyzer(codebase, "autonomous-improvement")
    orchestrator = AutonomousImprovementOrchestrator(codebase, analyzer)
    return await orchestrator.run_autonomous_improvement_cycle(max_iterations)


def format_context_for_prompt(context: AnalysisContext) -> str:
    """Format analysis context for OpenEvolve prompt generation."""
    return f"""
    Code Quality Context:
    - Health Score: {context.health_score:.2f}/1.0 ({'Excellent' if context.health_score > 0.8 else 'Good' if context.health_score > 0.6 else 'Needs Improvement'})
    - Technical Debt: {context.technical_debt_score:.2f} ({'Low' if context.technical_debt_score < 0.3 else 'Medium' if context.technical_debt_score < 0.7 else 'High'})
    - Maintainability: {context.maintainability_score:.2f}/1.0
    - Documentation Coverage: {context.documentation_coverage:.1%}
    
    Key Issues to Address:
    - High Complexity Functions: {len(context.high_complexity_functions)} functions need simplification
    - Low Cohesion Classes: {len(context.low_cohesion_classes)} classes need restructuring
    - Dead Code: {len(context.dead_code_items)} unused items can be removed
    - Circular Dependencies: {len(context.circular_dependencies)} dependency cycles detected
    
    Improvement Priorities:
    1. Reduce complexity in critical functions
    2. Improve class cohesion and design
    3. Clean up unused code and imports
    4. Resolve architectural issues
    
    Success will be measured by improvements in health score, reduced technical debt, and better maintainability metrics.
    """

