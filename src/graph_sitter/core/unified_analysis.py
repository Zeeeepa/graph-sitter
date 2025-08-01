#!/usr/bin/env python3
"""
Unified Analysis Engine for Graph-sitter
========================================

This module consolidates the DeepCodebaseAnalyzer and basic codebase analysis
into a single, comprehensive analysis system that provides multiple levels
of analysis depth while eliminating duplication.
"""

import sys
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union, TYPE_CHECKING
from datetime import datetime
from collections import defaultdict, Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import types for analysis
from graph_sitter.core.class_definition import Class
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase


class AnalysisLevel:
    """Analysis depth levels."""
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    DEEP = "deep"


class UnifiedAnalysisEngine:
    """
    Unified analysis engine that consolidates all codebase analysis capabilities.
    
    Provides three levels of analysis:
    - BASIC: Simple counts and summaries (replaces basic codebase_analysis functions)
    - COMPREHENSIVE: Detailed metrics and insights
    - DEEP: Advanced metrics, complexity analysis, and architectural insights
    """
    
    def __init__(self, codebase: "Codebase"):
        self.codebase = codebase
        self.analysis_cache = {}
        self._last_analysis = {}
        
    def analyze(self, level: str = AnalysisLevel.COMPREHENSIVE) -> Dict[str, Any]:
        """
        Perform codebase analysis at the specified level.
        
        Args:
            level: Analysis level (basic, comprehensive, deep)
            
        Returns:
            Analysis results dictionary
        """
        try:
            if level == AnalysisLevel.BASIC:
                return self._analyze_basic()
            elif level == AnalysisLevel.COMPREHENSIVE:
                return self._analyze_comprehensive()
            elif level == AnalysisLevel.DEEP:
                return self._analyze_deep()
            else:
                raise ValueError(f"Unknown analysis level: {level}")
                
        except Exception as e:
            logger.error(f"Error in {level} analysis: {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _analyze_basic(self) -> Dict[str, Any]:
        """Basic analysis - simple counts and summaries."""
        try:
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            symbols = list(self.codebase.symbols)
            imports = list(self.codebase.imports)
            external_modules = list(self.codebase.external_modules)
            
            # Basic node summary
            node_summary = {
                "total_nodes": len(self.codebase.ctx.get_nodes()),
                "files": len(files),
                "imports": len(imports),
                "external_modules": len(external_modules),
                "symbols": len(symbols),
                "classes": len(classes),
                "functions": len(functions),
                "global_vars": len(list(self.codebase.global_vars)),
                "interfaces": len(list(self.codebase.interfaces))
            }
            
            # Basic edge summary
            edges = self.codebase.ctx.edges
            edge_summary = {
                "total_edges": len(edges),
                "symbol_usage": len([x for x in edges if x[2].type == EdgeType.SYMBOL_USAGE]),
                "import_symbol_resolution": len([x for x in edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION]),
                "exports": len([x for x in edges if x[2].type == EdgeType.EXPORT])
            }
            
            return {
                "analysis_level": AnalysisLevel.BASIC,
                "timestamp": datetime.now().isoformat(),
                "node_summary": node_summary,
                "edge_summary": edge_summary,
                "codebase_summary": self._generate_codebase_summary_text(node_summary, edge_summary)
            }
            
        except Exception as e:
            logger.error(f"Error in basic analysis: {e}")
            return {"error": str(e), "analysis_level": AnalysisLevel.BASIC}
    
    def _analyze_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive analysis - detailed metrics and insights."""
        try:
            logger.info("Starting comprehensive analysis...")
            
            # Get basic analysis first
            basic_results = self._analyze_basic()
            
            # Collect all components
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            symbols = list(self.codebase.symbols)
            imports = []
            
            # Collect all imports
            for file in files:
                imports.extend(file.imports)
            
            # Comprehensive metrics
            comprehensive_metrics = {
                "basic_counts": basic_results.get("node_summary", {}),
                "complexity_metrics": self._calculate_complexity_metrics(files, functions, classes),
                "dependency_metrics": self._calculate_dependency_metrics(files, imports),
                "code_quality_metrics": self._calculate_quality_metrics(files, functions, classes),
                "distribution_metrics": self._calculate_distribution_metrics(files, functions, classes)
            }
            
            return {
                "analysis_level": AnalysisLevel.COMPREHENSIVE,
                "timestamp": datetime.now().isoformat(),
                "basic_summary": basic_results,
                "comprehensive_metrics": comprehensive_metrics,
                "insights": self._generate_comprehensive_insights(comprehensive_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {"error": str(e), "analysis_level": AnalysisLevel.COMPREHENSIVE}
    
    def _analyze_deep(self) -> Dict[str, Any]:
        """Deep analysis - advanced metrics and architectural insights."""
        try:
            logger.info("Starting deep analysis...")
            
            # Get comprehensive analysis first
            comprehensive_results = self._analyze_comprehensive()
            
            # Collect all components
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            
            # Deep architectural metrics
            deep_metrics = {
                "architectural_metrics": self._calculate_architectural_metrics(files, classes, functions),
                "advanced_complexity": self._calculate_advanced_complexity(files, functions, classes),
                "coupling_analysis": self._calculate_coupling_analysis(files, classes, functions),
                "maintainability_index": self._calculate_maintainability_index(files, functions, classes),
                "technical_debt_indicators": self._calculate_technical_debt(files, functions, classes)
            }
            
            return {
                "analysis_level": AnalysisLevel.DEEP,
                "timestamp": datetime.now().isoformat(),
                "comprehensive_results": comprehensive_results,
                "deep_metrics": deep_metrics,
                "architectural_insights": self._generate_architectural_insights(deep_metrics),
                "recommendations": self._generate_recommendations(deep_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error in deep analysis: {e}")
            return {"error": str(e), "analysis_level": AnalysisLevel.DEEP}
    
    # Helper methods for analysis calculations
    
    def _generate_codebase_summary_text(self, node_summary: Dict, edge_summary: Dict) -> str:
        """Generate human-readable codebase summary text."""
        node_text = f"""Contains {node_summary['total_nodes']} nodes
- {node_summary['files']} files
- {node_summary['imports']} imports
- {node_summary['external_modules']} external_modules
- {node_summary['symbols']} symbols
\t- {node_summary['classes']} classes
\t- {node_summary['functions']} functions
\t- {node_summary['global_vars']} global_vars
\t- {node_summary['interfaces']} interfaces
"""
        
        edge_text = f"""Contains {edge_summary['total_edges']} edges
- {edge_summary['symbol_usage']} symbol -> used symbol
- {edge_summary['import_symbol_resolution']} import -> used symbol
- {edge_summary['exports']} export -> exported symbol
"""
        
        return f"{node_text}\n{edge_text}"
    
    def _calculate_complexity_metrics(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        try:
            # Function complexity analysis
            function_complexities = []
            for func in functions:
                # Estimate complexity based on dependencies and parameters
                complexity = len(func.dependencies) + len(func.parameters) + 1
                function_complexities.append(complexity)
            
            # Class complexity analysis
            class_complexities = []
            for cls in classes:
                # Estimate complexity based on methods and attributes
                complexity = len(cls.methods) + len(cls.attributes) + len(cls.decorators)
                class_complexities.append(complexity)
            
            # File complexity analysis
            file_complexities = []
            for file in files:
                # Estimate complexity based on symbols and imports
                complexity = len(file.symbols) + len(file.imports)
                file_complexities.append(complexity)
            
            return {
                "function_complexity": {
                    "average": sum(function_complexities) / len(function_complexities) if function_complexities else 0,
                    "max": max(function_complexities) if function_complexities else 0,
                    "min": min(function_complexities) if function_complexities else 0,
                    "distribution": self._get_distribution(function_complexities)
                },
                "class_complexity": {
                    "average": sum(class_complexities) / len(class_complexities) if class_complexities else 0,
                    "max": max(class_complexities) if class_complexities else 0,
                    "min": min(class_complexities) if class_complexities else 0,
                    "distribution": self._get_distribution(class_complexities)
                },
                "file_complexity": {
                    "average": sum(file_complexities) / len(file_complexities) if file_complexities else 0,
                    "max": max(file_complexities) if file_complexities else 0,
                    "min": min(file_complexities) if file_complexities else 0,
                    "distribution": self._get_distribution(file_complexities)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating complexity metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_dependency_metrics(self, files, imports) -> Dict[str, Any]:
        """Calculate dependency metrics."""
        try:
            # Import analysis
            import_sources = [imp.module_name for imp in imports if hasattr(imp, 'module_name')]
            import_counter = Counter(import_sources)
            
            # File dependency analysis
            file_dependencies = {}
            for file in files:
                file_deps = len(file.imports)
                file_dependencies[str(file.filepath)] = file_deps
            
            return {
                "total_imports": len(imports),
                "unique_modules": len(import_counter),
                "most_imported_modules": import_counter.most_common(10),
                "average_imports_per_file": sum(file_dependencies.values()) / len(file_dependencies) if file_dependencies else 0,
                "files_with_most_dependencies": sorted(file_dependencies.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"Error calculating dependency metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_quality_metrics(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        try:
            # Documentation analysis
            documented_functions = sum(1 for func in functions if hasattr(func, 'docstring') and func.docstring)
            documented_classes = sum(1 for cls in classes if hasattr(cls, 'docstring') and cls.docstring)
            
            # Naming analysis
            function_names = [func.name for func in functions]
            class_names = [cls.name for cls in classes]
            
            return {
                "documentation_coverage": {
                    "functions": documented_functions / len(functions) if functions else 0,
                    "classes": documented_classes / len(classes) if classes else 0,
                    "overall": (documented_functions + documented_classes) / (len(functions) + len(classes)) if (functions or classes) else 0
                },
                "naming_analysis": {
                    "average_function_name_length": sum(len(name) for name in function_names) / len(function_names) if function_names else 0,
                    "average_class_name_length": sum(len(name) for name in class_names) / len(class_names) if class_names else 0,
                    "naming_conventions": self._analyze_naming_conventions(function_names, class_names)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_distribution_metrics(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate distribution metrics."""
        try:
            # Functions per file
            functions_per_file = {}
            classes_per_file = {}
            
            for file in files:
                file_path = str(file.filepath)
                functions_per_file[file_path] = len(file.functions)
                classes_per_file[file_path] = len(file.classes)
            
            return {
                "functions_per_file": {
                    "average": sum(functions_per_file.values()) / len(functions_per_file) if functions_per_file else 0,
                    "max": max(functions_per_file.values()) if functions_per_file else 0,
                    "distribution": self._get_distribution(list(functions_per_file.values()))
                },
                "classes_per_file": {
                    "average": sum(classes_per_file.values()) / len(classes_per_file) if classes_per_file else 0,
                    "max": max(classes_per_file.values()) if classes_per_file else 0,
                    "distribution": self._get_distribution(list(classes_per_file.values()))
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating distribution metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_architectural_metrics(self, files, classes, functions) -> Dict[str, Any]:
        """Calculate architectural metrics."""
        try:
            # Layer analysis
            layers = self._identify_architectural_layers(files)
            
            # Module cohesion
            cohesion_metrics = self._calculate_module_cohesion(files, classes, functions)
            
            return {
                "architectural_layers": layers,
                "module_cohesion": cohesion_metrics,
                "coupling_metrics": self._calculate_basic_coupling(files, classes)
            }
            
        except Exception as e:
            logger.error(f"Error calculating architectural metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_advanced_complexity(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate advanced complexity metrics."""
        try:
            # Cyclomatic complexity estimation
            cyclomatic_complexity = []
            for func in functions:
                # Estimate based on control flow indicators
                complexity = 1  # Base complexity
                # Add complexity for each decision point (estimated)
                complexity += len(func.dependencies) // 2  # Rough estimate
                cyclomatic_complexity.append(complexity)
            
            return {
                "cyclomatic_complexity": {
                    "average": sum(cyclomatic_complexity) / len(cyclomatic_complexity) if cyclomatic_complexity else 0,
                    "max": max(cyclomatic_complexity) if cyclomatic_complexity else 0,
                    "distribution": self._get_distribution(cyclomatic_complexity)
                },
                "cognitive_complexity": self._estimate_cognitive_complexity(functions),
                "halstead_metrics": self._estimate_halstead_metrics(functions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating advanced complexity: {e}")
            return {"error": str(e)}
    
    def _calculate_coupling_analysis(self, files, classes, functions) -> Dict[str, Any]:
        """Calculate coupling analysis."""
        try:
            # Afferent and efferent coupling
            coupling_data = {}
            
            for file in files:
                file_path = str(file.filepath)
                afferent = len([f for f in files if file in f.imports])  # Who depends on this file
                efferent = len(file.imports)  # What this file depends on
                
                coupling_data[file_path] = {
                    "afferent_coupling": afferent,
                    "efferent_coupling": efferent,
                    "instability": efferent / (afferent + efferent) if (afferent + efferent) > 0 else 0
                }
            
            return {
                "file_coupling": coupling_data,
                "average_instability": sum(data["instability"] for data in coupling_data.values()) / len(coupling_data) if coupling_data else 0,
                "highly_coupled_files": sorted(coupling_data.items(), key=lambda x: x[1]["efferent_coupling"], reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"Error calculating coupling analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_maintainability_index(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate maintainability index."""
        try:
            # Simplified maintainability index calculation
            maintainability_scores = []
            
            for file in files:
                # Factors: complexity, size, documentation
                complexity_factor = len(file.symbols) / 10  # Normalize
                size_factor = len(getattr(file, 'source', '').split('\n')) / 100  # Normalize
                doc_factor = 1 if any(hasattr(sym, 'docstring') and sym.docstring for sym in file.symbols) else 0
                
                # Simple maintainability score (0-100)
                score = max(0, 100 - complexity_factor * 10 - size_factor * 5 + doc_factor * 10)
                maintainability_scores.append(score)
            
            return {
                "average_maintainability": sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0,
                "maintainability_distribution": self._get_distribution(maintainability_scores),
                "files_needing_attention": [f for f, score in zip(files, maintainability_scores) if score < 50]
            }
            
        except Exception as e:
            logger.error(f"Error calculating maintainability index: {e}")
            return {"error": str(e)}
    
    def _calculate_technical_debt(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate technical debt indicators."""
        try:
            debt_indicators = {
                "large_files": [f for f in files if len(getattr(f, 'source', '').split('\n')) > 500],
                "complex_functions": [f for f in functions if len(f.dependencies) > 10],
                "large_classes": [c for c in classes if len(c.methods) > 20],
                "undocumented_public_functions": [f for f in functions if not hasattr(f, 'docstring') or not f.docstring],
                "high_coupling_files": []  # Will be populated from coupling analysis
            }
            
            # Calculate debt score
            total_items = len(files) + len(functions) + len(classes)
            debt_items = sum(len(indicators) for indicators in debt_indicators.values())
            debt_ratio = debt_items / total_items if total_items > 0 else 0
            
            return {
                "debt_indicators": debt_indicators,
                "debt_ratio": debt_ratio,
                "debt_score": max(0, 100 - debt_ratio * 100),  # 0-100 scale
                "priority_areas": self._identify_priority_debt_areas(debt_indicators)
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical debt: {e}")
            return {"error": str(e)}
    
    # Utility methods
    
    def _get_distribution(self, values: List[float]) -> Dict[str, float]:
        """Get distribution statistics for a list of values."""
        if not values:
            return {"percentile_25": 0, "percentile_50": 0, "percentile_75": 0, "percentile_90": 0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "percentile_25": sorted_values[int(n * 0.25)] if n > 0 else 0,
            "percentile_50": sorted_values[int(n * 0.50)] if n > 0 else 0,
            "percentile_75": sorted_values[int(n * 0.75)] if n > 0 else 0,
            "percentile_90": sorted_values[int(n * 0.90)] if n > 0 else 0
        }
    
    def _analyze_naming_conventions(self, function_names: List[str], class_names: List[str]) -> Dict[str, Any]:
        """Analyze naming conventions."""
        snake_case_functions = sum(1 for name in function_names if '_' in name and name.islower())
        camel_case_classes = sum(1 for name in class_names if name[0].isupper() and '_' not in name)
        
        return {
            "snake_case_functions_ratio": snake_case_functions / len(function_names) if function_names else 0,
            "camel_case_classes_ratio": camel_case_classes / len(class_names) if class_names else 0,
            "consistency_score": (snake_case_functions + camel_case_classes) / (len(function_names) + len(class_names)) if (function_names or class_names) else 0
        }
    
    def _identify_architectural_layers(self, files) -> Dict[str, List[str]]:
        """Identify architectural layers based on file paths."""
        layers = {
            "presentation": [],
            "business": [],
            "data": [],
            "infrastructure": [],
            "other": []
        }
        
        for file in files:
            file_path = str(file.filepath).lower()
            
            if any(keyword in file_path for keyword in ['ui', 'view', 'template', 'component']):
                layers["presentation"].append(str(file.filepath))
            elif any(keyword in file_path for keyword in ['service', 'business', 'logic', 'core']):
                layers["business"].append(str(file.filepath))
            elif any(keyword in file_path for keyword in ['data', 'repository', 'dao', 'model']):
                layers["data"].append(str(file.filepath))
            elif any(keyword in file_path for keyword in ['config', 'util', 'helper', 'infrastructure']):
                layers["infrastructure"].append(str(file.filepath))
            else:
                layers["other"].append(str(file.filepath))
        
        return layers
    
    def _calculate_module_cohesion(self, files, classes, functions) -> Dict[str, Any]:
        """Calculate module cohesion metrics."""
        cohesion_scores = []
        
        for file in files:
            # Simple cohesion metric based on symbol relationships
            file_symbols = file.symbols
            if len(file_symbols) <= 1:
                cohesion_scores.append(1.0)  # Perfect cohesion for single symbol
            else:
                # Calculate relationships between symbols in the file
                relationships = 0
                total_possible = len(file_symbols) * (len(file_symbols) - 1)
                
                for symbol in file_symbols:
                    relationships += len([dep for dep in symbol.dependencies if dep in file_symbols])
                
                cohesion = relationships / total_possible if total_possible > 0 else 1.0
                cohesion_scores.append(cohesion)
        
        return {
            "average_cohesion": sum(cohesion_scores) / len(cohesion_scores) if cohesion_scores else 0,
            "cohesion_distribution": self._get_distribution(cohesion_scores)
        }
    
    def _calculate_basic_coupling(self, files, classes) -> Dict[str, Any]:
        """Calculate basic coupling metrics."""
        coupling_scores = []
        
        for file in files:
            external_dependencies = len(file.imports)
            internal_symbols = len(file.symbols)
            
            # Coupling ratio: external dependencies vs internal symbols
            coupling_ratio = external_dependencies / (internal_symbols + 1)  # +1 to avoid division by zero
            coupling_scores.append(coupling_ratio)
        
        return {
            "average_coupling": sum(coupling_scores) / len(coupling_scores) if coupling_scores else 0,
            "coupling_distribution": self._get_distribution(coupling_scores)
        }
    
    def _estimate_cognitive_complexity(self, functions) -> Dict[str, Any]:
        """Estimate cognitive complexity."""
        cognitive_scores = []
        
        for func in functions:
            # Simple estimation based on nesting and dependencies
            base_complexity = 1
            dependency_complexity = len(func.dependencies) * 0.5
            parameter_complexity = len(func.parameters) * 0.2
            
            cognitive_complexity = base_complexity + dependency_complexity + parameter_complexity
            cognitive_scores.append(cognitive_complexity)
        
        return {
            "average_cognitive_complexity": sum(cognitive_scores) / len(cognitive_scores) if cognitive_scores else 0,
            "max_cognitive_complexity": max(cognitive_scores) if cognitive_scores else 0,
            "distribution": self._get_distribution(cognitive_scores)
        }
    
    def _estimate_halstead_metrics(self, functions) -> Dict[str, Any]:
        """Estimate Halstead complexity metrics."""
        # Simplified Halstead metrics estimation
        total_operators = sum(len(func.dependencies) for func in functions)
        total_operands = sum(len(func.parameters) for func in functions)
        unique_operators = len(set(dep.name for func in functions for dep in func.dependencies if hasattr(dep, 'name')))
        unique_operands = len(set(param.name for func in functions for param in func.parameters if hasattr(param, 'name')))
        
        vocabulary = unique_operators + unique_operands
        length = total_operators + total_operands
        
        return {
            "vocabulary": vocabulary,
            "length": length,
            "estimated_difficulty": (unique_operators / 2) * (total_operands / unique_operands) if unique_operands > 0 else 0,
            "estimated_effort": length * vocabulary if vocabulary > 0 else 0
        }
    
    def _identify_priority_debt_areas(self, debt_indicators: Dict) -> List[str]:
        """Identify priority areas for technical debt reduction."""
        priorities = []
        
        if debt_indicators["large_files"]:
            priorities.append(f"Refactor {len(debt_indicators['large_files'])} large files")
        
        if debt_indicators["complex_functions"]:
            priorities.append(f"Simplify {len(debt_indicators['complex_functions'])} complex functions")
        
        if debt_indicators["large_classes"]:
            priorities.append(f"Break down {len(debt_indicators['large_classes'])} large classes")
        
        if debt_indicators["undocumented_public_functions"]:
            priorities.append(f"Document {len(debt_indicators['undocumented_public_functions'])} public functions")
        
        return priorities
    
    def _generate_comprehensive_insights(self, metrics: Dict) -> List[str]:
        """Generate insights from comprehensive metrics."""
        insights = []
        
        complexity = metrics.get("complexity_metrics", {})
        if complexity.get("function_complexity", {}).get("average", 0) > 5:
            insights.append("Functions have high average complexity - consider refactoring")
        
        quality = metrics.get("code_quality_metrics", {})
        doc_coverage = quality.get("documentation_coverage", {}).get("overall", 0)
        if doc_coverage < 0.5:
            insights.append(f"Low documentation coverage ({doc_coverage:.1%}) - add more docstrings")
        
        dependency = metrics.get("dependency_metrics", {})
        if dependency.get("average_imports_per_file", 0) > 10:
            insights.append("High average imports per file - consider dependency injection")
        
        return insights
    
    def _generate_architectural_insights(self, metrics: Dict) -> List[str]:
        """Generate architectural insights from deep metrics."""
        insights = []
        
        coupling = metrics.get("coupling_analysis", {})
        avg_instability = coupling.get("average_instability", 0)
        if avg_instability > 0.7:
            insights.append("High average instability - modules are tightly coupled")
        
        maintainability = metrics.get("maintainability_index", {})
        avg_maintainability = maintainability.get("average_maintainability", 0)
        if avg_maintainability < 60:
            insights.append("Low maintainability index - code needs refactoring")
        
        debt = metrics.get("technical_debt_indicators", {})
        debt_ratio = debt.get("debt_ratio", 0)
        if debt_ratio > 0.3:
            insights.append("High technical debt ratio - prioritize debt reduction")
        
        return insights
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        debt = metrics.get("technical_debt_indicators", {})
        priorities = debt.get("priority_areas", [])
        recommendations.extend(priorities)
        
        coupling = metrics.get("coupling_analysis", {})
        highly_coupled = coupling.get("highly_coupled_files", [])
        if highly_coupled:
            recommendations.append(f"Reduce coupling in: {', '.join([f[0] for f in highly_coupled[:3]])}")
        
        maintainability = metrics.get("maintainability_index", {})
        files_needing_attention = maintainability.get("files_needing_attention", [])
        if files_needing_attention:
            recommendations.append(f"Improve maintainability of {len(files_needing_attention)} files")
        
        return recommendations
    
    # Convenience methods for backward compatibility
    
    def get_codebase_summary(self) -> str:
        """Get basic codebase summary (backward compatibility)."""
        basic_analysis = self.analyze(AnalysisLevel.BASIC)
        return basic_analysis.get("codebase_summary", "Analysis failed")
    
    def get_file_summary(self, file: SourceFile) -> str:
        """Get file summary (backward compatibility)."""
        interfaces_count = len(getattr(file, 'interfaces', []))
        
        return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {interfaces_count} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
- File path: {getattr(file, 'filepath', 'Unknown')}
- Lines of code: {len(getattr(file, 'source', '').split('\n')) if hasattr(file, 'source') else 'Unknown'}
"""
    
    def get_class_summary(self, cls: Class) -> str:
        """Get class summary (backward compatibility)."""
        return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{self.get_symbol_summary(cls)}
"""
    
    def get_function_summary(self, func: Function) -> str:
        """Get function summary (backward compatibility)."""
        return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{self.get_symbol_summary(func)}
"""
    
    def get_symbol_summary(self, symbol: Symbol) -> str:
        """Get symbol summary (backward compatibility)."""
        usages = symbol.symbol_usages
        imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

        return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
"""
