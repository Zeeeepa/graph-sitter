"""Context Gatherer for rich context extraction from GraphSitter analysis."""

import logging
from typing import Any, Dict, List, Union, Optional
from dataclasses import dataclass, field

from graph_sitter.core.file import File
from graph_sitter.core.interfaces.editable import Editable

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveContext:
    """Comprehensive context for AI analysis."""
    target_info: Dict[str, Any] = field(default_factory=dict)
    static_analysis: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, Any] = field(default_factory=dict)
    codebase_summary: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    change_impact: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    test_context: Dict[str, Any] = field(default_factory=dict)


class ContextGatherer:
    """Rich context extraction from GraphSitter analysis with comprehensive and reactive capabilities."""
    
    def __init__(self, codebase):
        """Initialize with codebase reference."""
        self.codebase = codebase
    
    def gather_comprehensive_context(self, target: Editable) -> ComprehensiveContext:
        """Gather comprehensive context for a target editable object with reactive analysis.
        
        Args:
            target: The target editable object to gather context for
            
        Returns:
            ComprehensiveContext containing rich context information
        """
        context = ComprehensiveContext()
        
        try:
            # Gather all context components
            context.target_info = self._get_enhanced_target_info(target)
            context.static_analysis = self._get_comprehensive_static_analysis(target)
            context.relationships = self._get_detailed_relationships(target)
            context.codebase_summary = self._get_enhanced_codebase_summary()
            context.quality_metrics = self._get_quality_metrics(target)
            context.change_impact = self._get_change_impact_analysis(target)
            context.dependencies = self._get_dependency_analysis(target)
            context.test_context = self._get_test_context(target)
            
        except Exception as e:
            logger.warning(f"Error gathering comprehensive context: {e}")
        
        return context
    
    def gather_target_context(self, target: Editable) -> Dict[str, Any]:
        """Gather comprehensive context for a target editable object.
        
        Args:
            target: The target editable object to gather context for
            
        Returns:
            Dictionary containing rich context information
        """
        context = {
            "target_info": self._get_enhanced_target_info(target),
            "static_analysis": self._get_comprehensive_static_analysis(target),
            "relationships": self._get_detailed_relationships(target),
            "codebase_summary": self._get_enhanced_codebase_summary(),
            "quality_metrics": self._get_quality_metrics(target),
            "change_impact": self._get_change_impact_analysis(target)
        }
        
        return context
    
    def _get_enhanced_target_info(self, target: Editable) -> Dict[str, Any]:
        """Get enhanced information about the target with comprehensive analysis."""
        info = {
            "type": target.__class__.__name__,
            "name": getattr(target, "name", "unknown"),
            "location": {
                "file": target.file.filepath if hasattr(target, "file") else "unknown",
                "line_start": getattr(target, "line_start", None),
                "line_end": getattr(target, "line_end", None)
            },
            "source_preview": self._get_enhanced_source_preview(target),
            "complexity_metrics": self._calculate_target_complexity(target),
            "documentation_status": self._analyze_documentation_status(target),
            "code_patterns": self._identify_code_patterns(target)
        }
        
        # Add signature for functions/methods
        if hasattr(target, "signature"):
            info["signature"] = str(target.signature)
        
        # Add class-specific information
        if hasattr(target, "superclasses"):
            info["inheritance"] = {
                "superclasses": [cls.name for cls in target.superclasses],
                "subclasses": [cls.name for cls in getattr(target, "subclasses", [])]
            }
        
        # Add function-specific information
        if hasattr(target, "parameters"):
            info["parameters"] = [
                {
                    "name": param.name,
                    "type": getattr(param, "type_annotation", None),
                    "default": getattr(param, "default_value", None)
                }
                for param in target.parameters
            ]
        
        return info
    
    def _get_comprehensive_static_analysis(self, target: Editable) -> Dict[str, Any]:
        """Get comprehensive static analysis with call sites, dependencies, and usage patterns."""
        analysis = {
            "call_sites": self._get_enhanced_call_sites(target),
            "dependencies": self._get_enhanced_dependencies(target),
            "usages": self._get_enhanced_usages(target),
            "data_flow": self._analyze_data_flow(target),
            "control_flow": self._analyze_control_flow(target),
            "side_effects": self._analyze_side_effects(target)
        }
        
        return analysis
    
    def _get_detailed_relationships(self, target: Editable) -> Dict[str, Any]:
        """Get detailed relationships including parent/child and sibling relationships."""
        relationships = {
            "parent": self._get_parent_info(target),
            "children": self._get_children_info(target),
            "siblings": self._get_sibling_info(target),
            "collaborators": self._get_collaborator_info(target),
            "dependents": self._get_dependent_info(target)
        }
        
        return relationships
    
    def _get_enhanced_codebase_summary(self) -> Dict[str, Any]:
        """Get enhanced high-level project overview with quality metrics."""
        try:
            summary = {
                "project_structure": self._analyze_project_structure(),
                "technology_stack": self._identify_technology_stack(),
                "architecture_patterns": self._identify_architecture_patterns(),
                "quality_overview": self._get_codebase_quality_overview(),
                "recent_changes": self._get_recent_changes_summary(),
                "hotspots": self._identify_code_hotspots()
            }
            
            return summary
        except Exception as e:
            logger.warning(f"Error generating codebase summary: {e}")
            return {}
    
    def _get_quality_metrics(self, target: Editable) -> Dict[str, Any]:
        """Get quality metrics for the target."""
        return {
            "complexity": self._calculate_complexity_metrics(target),
            "maintainability": self._calculate_maintainability_metrics(target),
            "testability": self._calculate_testability_metrics(target),
            "documentation": self._calculate_documentation_metrics(target),
            "code_smells": self._detect_code_smells(target),
            "technical_debt": self._assess_technical_debt(target)
        }
    
    def _get_change_impact_analysis(self, target: Editable) -> Dict[str, Any]:
        """Get change impact analysis for reactive context."""
        return {
            "affected_components": self._identify_affected_components(target),
            "test_impact": self._analyze_test_impact(target),
            "performance_impact": self._analyze_performance_impact(target),
            "breaking_changes": self._identify_potential_breaking_changes(target),
            "migration_requirements": self._identify_migration_requirements(target)
        }
    
    def _get_dependency_analysis(self, target: Editable) -> Dict[str, Any]:
        """Get comprehensive dependency analysis."""
        return {
            "direct_dependencies": self._get_direct_dependencies(target),
            "transitive_dependencies": self._get_transitive_dependencies(target),
            "circular_dependencies": self._detect_circular_dependencies(target),
            "dependency_health": self._assess_dependency_health(target),
            "update_recommendations": self._get_dependency_update_recommendations(target)
        }
    
    def _get_test_context(self, target: Editable) -> Dict[str, Any]:
        """Get test context and coverage information."""
        return {
            "existing_tests": self._find_existing_tests(target),
            "test_coverage": self._estimate_test_coverage(target),
            "test_quality": self._assess_test_quality(target),
            "missing_tests": self._identify_missing_tests(target),
            "test_recommendations": self._generate_test_recommendations(target)
        }
    
    def _get_source_preview(self, target: Editable, max_lines: int = 10) -> str:
        """Get a preview of the source code."""
        try:
            if hasattr(target, "source"):
                lines = target.source.split("\n")
                if len(lines) <= max_lines:
                    return target.source
                else:
                    preview_lines = lines[:max_lines]
                    return "\n".join(preview_lines) + f"\n... ({len(lines) - max_lines} more lines)"
            return "Source not available"
        except Exception:
            return "Error retrieving source"
    
    def _get_enhanced_source_preview(self, target: Editable, max_lines: int = 15) -> str:
        """Get an enhanced preview of the source code with context."""
        try:
            if hasattr(target, "source"):
                lines = target.source.split("\n")
                if len(lines) <= max_lines:
                    return target.source
                else:
                    # Include more context for enhanced preview
                    preview_lines = lines[:max_lines]
                    return "\n".join(preview_lines) + f"\n... ({len(lines) - max_lines} more lines)"
            return "Source not available"
        except Exception:
            return "Error retrieving source"
    
    def _calculate_target_complexity(self, target: Editable) -> Dict[str, Any]:
        """Calculate complexity metrics for the target."""
        try:
            complexity = {
                "cyclomatic_complexity": 1,  # Base complexity
                "cognitive_complexity": 1,
                "nesting_depth": 0,
                "parameter_count": 0
            }
            
            if hasattr(target, "parameters"):
                complexity["parameter_count"] = len(target.parameters)
            
            # Estimate complexity based on source code patterns
            if hasattr(target, "source"):
                source = target.source
                # Count control flow statements
                control_keywords = ["if", "elif", "else", "for", "while", "try", "except", "finally", "with"]
                for keyword in control_keywords:
                    complexity["cyclomatic_complexity"] += source.count(f" {keyword} ")
                
                # Estimate nesting depth
                lines = source.split("\n")
                max_indent = 0
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        max_indent = max(max_indent, indent // 4)  # Assuming 4-space indentation
                complexity["nesting_depth"] = max_indent
            
            return complexity
        except Exception as e:
            logger.warning(f"Error calculating target complexity: {e}")
            return {"error": str(e)}
    
    def _analyze_documentation_status(self, target: Editable) -> Dict[str, Any]:
        """Analyze documentation status of the target."""
        try:
            status = {
                "has_docstring": False,
                "docstring_quality": "none",
                "missing_sections": [],
                "documentation_score": 0.0
            }
            
            if hasattr(target, "docstring") and target.docstring:
                status["has_docstring"] = True
                docstring = target.docstring.strip()
                
                # Basic quality assessment
                if len(docstring) > 100:
                    status["docstring_quality"] = "comprehensive"
                    status["documentation_score"] = 0.9
                elif len(docstring) > 30:
                    status["docstring_quality"] = "basic"
                    status["documentation_score"] = 0.6
                else:
                    status["docstring_quality"] = "minimal"
                    status["documentation_score"] = 0.3
                
                # Check for common sections
                if "Args:" not in docstring and "Parameters:" not in docstring:
                    status["missing_sections"].append("parameters")
                if "Returns:" not in docstring and "Return:" not in docstring:
                    status["missing_sections"].append("returns")
                if "Raises:" not in docstring and "Exceptions:" not in docstring:
                    status["missing_sections"].append("exceptions")
            
            return status
        except Exception as e:
            logger.warning(f"Error analyzing documentation status: {e}")
            return {"error": str(e)}
    
    def _identify_code_patterns(self, target: Editable) -> List[str]:
        """Identify code patterns in the target."""
        try:
            patterns = []
            
            if hasattr(target, "source"):
                source = target.source.lower()
                
                # Common patterns
                if "singleton" in source or "_instance" in source:
                    patterns.append("singleton")
                if "factory" in source or "create_" in source:
                    patterns.append("factory")
                if "observer" in source or "notify" in source:
                    patterns.append("observer")
                if "decorator" in source or "@" in source:
                    patterns.append("decorator")
                if "async" in source or "await" in source:
                    patterns.append("async")
                if "yield" in source:
                    patterns.append("generator")
                if "context" in source or "__enter__" in source:
                    patterns.append("context_manager")
            
            return patterns
        except Exception as e:
            logger.warning(f"Error identifying code patterns: {e}")
            return []
    
    def _get_enhanced_call_sites(self, target: Editable) -> List[Dict[str, Any]]:
        """Get enhanced call sites with context."""
        call_sites = []
        try:
            if hasattr(target, "call_sites"):
                for call_site in target.call_sites[:10]:  # Limit to first 10
                    call_context = {
                        "location": {
                            "file": call_site.file.filepath if hasattr(call_site, "file") else "unknown",
                            "line": getattr(call_site, "line_start", None)
                        },
                        "context": self._get_surrounding_context(call_site, lines=3),
                        "caller_info": self._get_caller_info(call_site)
                    }
                    call_sites.append(call_context)
        except Exception as e:
            logger.warning(f"Error getting enhanced call sites: {e}")
        
        return call_sites
    
    def _get_enhanced_dependencies(self, target: Editable) -> List[Dict[str, Any]]:
        """Get enhanced dependencies with analysis."""
        dependencies = []
        try:
            if hasattr(target, "dependencies"):
                for dep in target.dependencies[:10]:  # Limit to first 10
                    dep_info = {
                        "name": getattr(dep, "name", str(dep)),
                        "type": dep.__class__.__name__,
                        "location": {
                            "file": dep.file.filepath if hasattr(dep, "file") else "unknown"
                        },
                        "relationship_type": self._classify_dependency_relationship(target, dep),
                        "coupling_strength": self._assess_coupling_strength(target, dep)
                    }
                    dependencies.append(dep_info)
        except Exception as e:
            logger.warning(f"Error getting enhanced dependencies: {e}")
        
        return dependencies
    
    def _get_enhanced_usages(self, target: Editable) -> List[Dict[str, Any]]:
        """Get enhanced usages with context."""
        usages = []
        try:
            if hasattr(target, "usages"):
                for usage in target.usages[:10]:  # Limit to first 10
                    usage_info = {
                        "location": {
                            "file": usage.file.filepath if hasattr(usage, "file") else "unknown",
                            "line": getattr(usage, "line_start", None)
                        },
                        "context": self._get_surrounding_context(usage, lines=2),
                        "usage_pattern": self._classify_usage_pattern(usage)
                    }
                    usages.append(usage_info)
        except Exception as e:
            logger.warning(f"Error getting enhanced usages: {e}")
        
        return usages
    
    def _analyze_data_flow(self, target: Editable) -> Dict[str, Any]:
        """Analyze data flow patterns."""
        return {
            "input_sources": [],
            "output_destinations": [],
            "data_transformations": [],
            "side_effects": []
        }
    
    def _analyze_control_flow(self, target: Editable) -> Dict[str, Any]:
        """Analyze control flow patterns."""
        return {
            "branching_complexity": 0,
            "loop_patterns": [],
            "exception_handling": [],
            "early_returns": 0
        }
    
    def _analyze_side_effects(self, target: Editable) -> List[str]:
        """Analyze potential side effects."""
        side_effects = []
        try:
            if hasattr(target, "source"):
                source = target.source
                if "print(" in source or "logging." in source:
                    side_effects.append("logging/output")
                if "open(" in source or "file" in source:
                    side_effects.append("file_io")
                if "requests." in source or "urllib" in source:
                    side_effects.append("network_io")
                if "global " in source:
                    side_effects.append("global_state")
        except Exception as e:
            logger.warning(f"Error analyzing side effects: {e}")
        
        return side_effects
    
    # Placeholder implementations for comprehensive analysis methods
    def _get_parent_info(self, target: Editable) -> Dict[str, Any]:
        """Get parent information."""
        try:
            if hasattr(target, "parent") and target.parent:
                return {
                    "name": getattr(target.parent, "name", "unknown"),
                    "type": target.parent.__class__.__name__,
                    "location": getattr(target.parent, "file", {}).get("filepath", "unknown") if hasattr(target.parent, "file") else "unknown"
                }
        except Exception:
            pass
        return {}
    
    def _get_children_info(self, target: Editable) -> List[Dict[str, Any]]:
        """Get children information."""
        children = []
        try:
            if hasattr(target, "children"):
                for child in target.children[:5]:  # Limit to first 5
                    children.append({
                        "name": getattr(child, "name", "unknown"),
                        "type": child.__class__.__name__
                    })
        except Exception:
            pass
        return children
    
    def _get_sibling_info(self, target: Editable) -> List[Dict[str, Any]]:
        """Get sibling information."""
        siblings = []
        try:
            # For methods, get other methods in the same class
            if hasattr(target, "parent") and hasattr(target.parent, "methods"):
                for method in target.parent.methods:
                    if method != target:
                        siblings.append({
                            "name": method.name,
                            "type": "method"
                        })
            # For functions, get other functions in the same file
            elif hasattr(target, "file") and hasattr(target.file, "functions"):
                for func in target.file.functions:
                    if func != target:
                        siblings.append({
                            "name": func.name,
                            "type": "function"
                        })
        except Exception:
            pass
        return siblings[:5]  # Limit to first 5
    
    def _get_collaborator_info(self, target: Editable) -> List[Dict[str, Any]]:
        """Get collaborator information."""
        return []  # Placeholder
    
    def _get_dependent_info(self, target: Editable) -> List[Dict[str, Any]]:
        """Get dependent information."""
        return []  # Placeholder
    
    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure."""
        try:
            structure = {
                "total_files": len(self.codebase.files),
                "total_classes": len(self.codebase.classes),
                "total_functions": len(self.codebase.functions),
                "languages": list(set(
                    file.language for file in self.codebase.files 
                    if hasattr(file, "language") and file.language
                )),
                "main_directories": self._get_main_directories()
            }
            return structure
        except Exception as e:
            logger.warning(f"Error analyzing project structure: {e}")
            return {}
    
    def _get_main_directories(self) -> List[str]:
        """Get main directories in the codebase."""
        try:
            directories = set()
            for file in self.codebase.files[:100]:  # Sample first 100 files
                parts = file.filepath.split("/")
                if len(parts) > 1:
                    directories.add(parts[0])
            return sorted(list(directories))[:10]  # Return top 10
        except Exception:
            return []
    
    def _identify_technology_stack(self) -> List[str]:
        """Identify technology stack."""
        return []  # Placeholder
    
    def _identify_architecture_patterns(self) -> List[str]:
        """Identify architecture patterns."""
        return []  # Placeholder
    
    def _get_codebase_quality_overview(self) -> Dict[str, Any]:
        """Get codebase quality overview."""
        return {}  # Placeholder
    
    def _get_recent_changes_summary(self) -> Dict[str, Any]:
        """Get recent changes summary."""
        return {}  # Placeholder
    
    def _identify_code_hotspots(self) -> List[Dict[str, Any]]:
        """Identify code hotspots."""
        return []  # Placeholder
    
    def _calculate_complexity_metrics(self, target: Editable) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        return self._calculate_target_complexity(target)
    
    def _calculate_maintainability_metrics(self, target: Editable) -> Dict[str, Any]:
        """Calculate maintainability metrics."""
        return {}  # Placeholder
    
    def _calculate_testability_metrics(self, target: Editable) -> Dict[str, Any]:
        """Calculate testability metrics."""
        return {}  # Placeholder
    
    def _calculate_documentation_metrics(self, target: Editable) -> Dict[str, Any]:
        """Calculate documentation metrics."""
        return self._analyze_documentation_status(target)
    
    def _detect_code_smells(self, target: Editable) -> List[str]:
        """Detect code smells."""
        return []  # Placeholder
    
    def _assess_technical_debt(self, target: Editable) -> Dict[str, Any]:
        """Assess technical debt."""
        return {}  # Placeholder
    
    def _identify_affected_components(self, target: Editable) -> List[str]:
        """Identify affected components."""
        return []  # Placeholder
    
    def _analyze_test_impact(self, target: Editable) -> Dict[str, Any]:
        """Analyze test impact."""
        return {}  # Placeholder
    
    def _analyze_performance_impact(self, target: Editable) -> Dict[str, Any]:
        """Analyze performance impact."""
        return {}  # Placeholder
    
    def _identify_potential_breaking_changes(self, target: Editable) -> List[str]:
        """Identify potential breaking changes."""
        return []  # Placeholder
    
    def _identify_migration_requirements(self, target: Editable) -> List[str]:
        """Identify migration requirements."""
        return []  # Placeholder
    
    def _get_direct_dependencies(self, target: Editable) -> List[Dict[str, Any]]:
        """Get direct dependencies."""
        return self._get_enhanced_dependencies(target)
    
    def _get_transitive_dependencies(self, target: Editable) -> List[Dict[str, Any]]:
        """Get transitive dependencies."""
        return []  # Placeholder
    
    def _detect_circular_dependencies(self, target: Editable) -> List[str]:
        """Detect circular dependencies."""
        return []  # Placeholder
    
    def _assess_dependency_health(self, target: Editable) -> Dict[str, Any]:
        """Assess dependency health."""
        return {}  # Placeholder
    
    def _get_dependency_update_recommendations(self, target: Editable) -> List[str]:
        """Get dependency update recommendations."""
        return []  # Placeholder
    
    def _find_existing_tests(self, target: Editable) -> List[Dict[str, Any]]:
        """Find existing tests."""
        return []  # Placeholder
    
    def _estimate_test_coverage(self, target: Editable) -> float:
        """Estimate test coverage."""
        return 0.0  # Placeholder
    
    def _assess_test_quality(self, target: Editable) -> Dict[str, Any]:
        """Assess test quality."""
        return {}  # Placeholder
    
    def _identify_missing_tests(self, target: Editable) -> List[str]:
        """Identify missing tests."""
        return []  # Placeholder
    
    def _generate_test_recommendations(self, target: Editable) -> List[str]:
        """Generate test recommendations."""
        return []  # Placeholder
    
    def _get_caller_info(self, call_site) -> Dict[str, Any]:
        """Get caller information."""
        return {}  # Placeholder
    
    def _classify_dependency_relationship(self, target, dep) -> str:
        """Classify dependency relationship."""
        return "unknown"  # Placeholder
    
    def _assess_coupling_strength(self, target, dep) -> str:
        """Assess coupling strength."""
        return "medium"  # Placeholder
    
    def _classify_usage_pattern(self, usage) -> str:
        """Classify usage pattern."""
        return "unknown"  # Placeholder
    
    def _get_surrounding_context(self, target: Editable, lines: int = 3) -> str:
        """Get surrounding context for a target."""
        try:
            if hasattr(target, "file") and hasattr(target, "line_start"):
                file_lines = target.file.source.split("\n")
                start_line = max(0, target.line_start - lines - 1)
                end_line = min(len(file_lines), target.line_start + lines)
                context_lines = file_lines[start_line:end_line]
                return "\n".join(context_lines)
        except Exception:
            pass
        return "Context not available"
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format gathered context for use in AI prompts."""
        formatted_parts = []
        
        # Target information
        if "target_info" in context:
            target_info = context["target_info"]
            formatted_parts.append(f"=== TARGET INFORMATION ===")
            formatted_parts.append(f"Type: {target_info.get('type', 'unknown')}")
            formatted_parts.append(f"Name: {target_info.get('name', 'unknown')}")
            formatted_parts.append(f"Location: {target_info.get('location', {}).get('file', 'unknown')}")
            if target_info.get("signature"):
                formatted_parts.append(f"Signature: {target_info['signature']}")
            formatted_parts.append(f"Source Preview:\n{target_info.get('source_preview', 'Not available')}")
            formatted_parts.append("")
        
        # Static analysis
        if "static_analysis" in context:
            analysis = context["static_analysis"]
            if analysis.get("call_sites"):
                formatted_parts.append("=== CALL SITES ===")
                for i, call_site in enumerate(analysis["call_sites"][:3]):  # Show top 3
                    formatted_parts.append(f"Call Site {i+1}: {call_site.get('location', {}).get('file', 'unknown')}")
                    if call_site.get("context"):
                        formatted_parts.append(f"Context:\n{call_site['context']}")
                formatted_parts.append("")
            
            if analysis.get("dependencies"):
                formatted_parts.append("=== DEPENDENCIES ===")
                for dep in analysis["dependencies"][:5]:  # Show top 5
                    formatted_parts.append(f"- {dep.get('name', 'unknown')} ({dep.get('type', 'unknown')})")
                formatted_parts.append("")
        
        # Relationships
        if "relationships" in context:
            relationships = context["relationships"]
            if relationships.get("siblings"):
                formatted_parts.append("=== RELATED SYMBOLS ===")
                for sibling in relationships["siblings"][:3]:  # Show top 3
                    formatted_parts.append(f"- {sibling.get('name', 'unknown')} ({sibling.get('type', 'unknown')})")
                formatted_parts.append("")
        
        # Codebase summary
        if "codebase_summary" in context:
            summary = context["codebase_summary"]
            formatted_parts.append("=== CODEBASE OVERVIEW ===")
            formatted_parts.append(f"Files: {summary.get('total_files', 0)}")
            formatted_parts.append(f"Classes: {summary.get('total_classes', 0)}")
            formatted_parts.append(f"Functions: {summary.get('total_functions', 0)}")
            if summary.get("languages"):
                formatted_parts.append(f"Languages: {', '.join(summary['languages'])}")
            formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    def optimize_context_size(self, context: str, max_tokens: int = 8000) -> str:
        """Optimize context size by intelligent truncation."""
        # Simple token estimation (roughly 4 characters per token)
        estimated_tokens = len(context) // 4
        
        if estimated_tokens <= max_tokens:
            return context
        
        # Truncate by removing less important sections
        lines = context.split("\n")
        target_lines = int(len(lines) * (max_tokens / estimated_tokens))
        
        # Keep the most important sections (target info, first few call sites, etc.)
        truncated_lines = lines[:target_lines]
        truncated_context = "\n".join(truncated_lines)
        
        if len(truncated_context) < len(context):
            truncated_context += "\n\n[... context truncated for size optimization ...]"
        
        return truncated_context
