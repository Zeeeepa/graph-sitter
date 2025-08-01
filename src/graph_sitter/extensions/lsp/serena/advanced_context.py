#!/usr/bin/env python3
"""
Advanced Context Engine for Serena Integration

This module provides comprehensive context analysis and inclusion capabilities
for deep code understanding and intelligent error analysis.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from pathlib import Path

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

logger = logging.getLogger(__name__)


@dataclass
class ContextualError:
    """Enhanced error with comprehensive context."""
    error_id: str
    error_type: str
    severity: str
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    message: str = ""
    description: str = ""
    
    # Context layers
    immediate_context: Dict[str, Any] = field(default_factory=dict)
    function_context: Dict[str, Any] = field(default_factory=dict)
    class_context: Dict[str, Any] = field(default_factory=dict)
    file_context: Dict[str, Any] = field(default_factory=dict)
    module_context: Dict[str, Any] = field(default_factory=dict)
    project_context: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships
    related_symbols: List[str] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Suggestions
    fix_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    code_examples: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)


@dataclass
class ContextualInsight:
    """Contextual insight about code elements."""
    insight_type: str
    confidence: float
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)


class AdvancedContextEngine:
    """
    Advanced context engine that provides deep contextual understanding
    of code elements and their relationships.
    """
    
    def __init__(self, codebase: Codebase, knowledge_integration=None):
        self.codebase = codebase
        self.knowledge_integration = knowledge_integration
        self.context_cache = {}
        self.insight_cache = {}
    
    async def analyze_error_context(
        self,
        error_info: Dict[str, Any],
        include_deep_analysis: bool = True
    ) -> ContextualError:
        """Analyze comprehensive context for an error."""
        contextual_error = ContextualError(
            error_id=error_info.get("id", "unknown"),
            error_type=error_info.get("type", "unknown"),
            severity=error_info.get("severity", "medium"),
            file_path=error_info.get("file_path", ""),
            line_number=error_info.get("line_number"),
            function_name=error_info.get("function_name"),
            class_name=error_info.get("class_name"),
            message=error_info.get("message", ""),
            description=error_info.get("description", "")
        )
        
        # Build context layers
        await self._build_immediate_context(contextual_error)
        await self._build_function_context(contextual_error)
        await self._build_class_context(contextual_error)
        await self._build_file_context(contextual_error)
        await self._build_module_context(contextual_error)
        await self._build_project_context(contextual_error)
        
        # Analyze relationships and impact
        await self._analyze_relationships(contextual_error)
        await self._analyze_impact(contextual_error)
        
        # Generate suggestions
        await self._generate_fix_suggestions(contextual_error)
        
        if include_deep_analysis and self.knowledge_integration:
            await self._enhance_with_knowledge_integration(contextual_error)
        
        return contextual_error
    
    async def _build_immediate_context(self, error: ContextualError):
        """Build immediate context around the error location."""
        try:
            file_obj = self._get_file_object(error.file_path)
            if not file_obj:
                return
            
            # Get surrounding code lines
            lines = file_obj.source.splitlines()
            if error.line_number and 1 <= error.line_number <= len(lines):
                start_line = max(1, error.line_number - 5)
                end_line = min(len(lines), error.line_number + 5)
                
                error.immediate_context = {
                    "surrounding_code": {
                        "lines": lines[start_line-1:end_line],
                        "start_line": start_line,
                        "end_line": end_line,
                        "error_line": error.line_number
                    },
                    "line_analysis": {
                        "line_content": lines[error.line_number-1] if error.line_number <= len(lines) else "",
                        "indentation_level": len(lines[error.line_number-1]) - len(lines[error.line_number-1].lstrip()) if error.line_number <= len(lines) else 0,
                        "line_type": self._classify_line_type(lines[error.line_number-1] if error.line_number <= len(lines) else "")
                    }
                }
        except Exception as e:
            logger.error(f"Failed to build immediate context: {e}")
    
    async def _build_function_context(self, error: ContextualError):
        """Build function-level context."""
        try:
            if not error.function_name:
                return
            
            func_obj = self._find_function(error.file_path, error.function_name)
            if not func_obj:
                return
            
            error.function_context = {
                "function_info": {
                    "name": func_obj.name,
                    "parameters": [p.name for p in func_obj.parameters],
                    "parameter_count": len(func_obj.parameters),
                    "return_statements": len(func_obj.return_statements),
                    "complexity": self._calculate_complexity(func_obj)
                },
                "function_calls": [call.name for call in func_obj.function_calls[:10]],
                "dependencies": [dep.name for dep in func_obj.dependencies[:10]],
                "call_sites": len(func_obj.call_sites),
                "local_variables": self._extract_local_variables(func_obj),
                "control_flow": self._analyze_control_flow(func_obj)
            }
        except Exception as e:
            logger.error(f"Failed to build function context: {e}")
    
    async def _build_class_context(self, error: ContextualError):
        """Build class-level context."""
        try:
            if not error.class_name:
                return
            
            class_obj = self._find_class(error.file_path, error.class_name)
            if not class_obj:
                return
            
            error.class_context = {
                "class_info": {
                    "name": class_obj.name,
                    "methods": [m.name for m in class_obj.methods],
                    "method_count": len(class_obj.methods),
                    "attributes": [a.name for a in class_obj.attributes],
                    "attribute_count": len(class_obj.attributes),
                    "parent_classes": class_obj.parent_class_names,
                    "inheritance_depth": len(class_obj.parent_class_names)
                },
                "method_analysis": self._analyze_class_methods(class_obj),
                "attribute_analysis": self._analyze_class_attributes(class_obj),
                "design_patterns": self._detect_class_patterns(class_obj)
            }
        except Exception as e:
            logger.error(f"Failed to build class context: {e}")
    
    async def _build_file_context(self, error: ContextualError):
        """Build file-level context."""
        try:
            file_obj = self._get_file_object(error.file_path)
            if not file_obj:
                return
            
            error.file_context = {
                "file_info": {
                    "name": file_obj.name,
                    "path": file_obj.filepath,
                    "size": len(file_obj.source),
                    "line_count": len(file_obj.source.splitlines())
                },
                "symbols": {
                    "functions": len(file_obj.functions),
                    "classes": len(file_obj.classes),
                    "global_vars": len(file_obj.global_vars),
                    "imports": len(file_obj.imports)
                },
                "imports": [imp.name for imp in file_obj.imports[:20]],
                "complexity_metrics": self._calculate_file_complexity(file_obj),
                "code_quality": self._assess_file_quality(file_obj)
            }
        except Exception as e:
            logger.error(f"Failed to build file context: {e}")
    
    async def _build_module_context(self, error: ContextualError):
        """Build module-level context."""
        try:
            module_path = Path(error.file_path).parent
            related_files = self._get_module_files(str(module_path))
            
            error.module_context = {
                "module_info": {
                    "path": str(module_path),
                    "file_count": len(related_files),
                    "total_functions": sum(len(f.functions) for f in related_files),
                    "total_classes": sum(len(f.classes) for f in related_files)
                },
                "related_files": [f.filepath for f in related_files[:10]],
                "module_dependencies": self._analyze_module_dependencies(related_files),
                "architectural_role": self._determine_architectural_role(str(module_path))
            }
        except Exception as e:
            logger.error(f"Failed to build module context: {e}")
    
    async def _build_project_context(self, error: ContextualError):
        """Build project-level context."""
        try:
            error.project_context = {
                "project_info": {
                    "total_files": len(list(self.codebase.files)),
                    "total_functions": len(list(self.codebase.functions)),
                    "total_classes": len(list(self.codebase.classes)),
                    "languages": self._detect_languages()
                },
                "architectural_patterns": self._detect_project_patterns(),
                "technology_stack": self._analyze_technology_stack(),
                "project_health": self._assess_project_health()
            }
        except Exception as e:
            logger.error(f"Failed to build project context: {e}")
    
    async def _analyze_relationships(self, error: ContextualError):
        """Analyze relationships and dependencies."""
        try:
            # Find related symbols
            if error.function_name:
                func_obj = self._find_function(error.file_path, error.function_name)
                if func_obj:
                    error.related_symbols.extend([dep.name for dep in func_obj.dependencies[:5]])
                    error.dependency_chain = self._build_dependency_chain(func_obj)
        except Exception as e:
            logger.error(f"Failed to analyze relationships: {e}")
    
    async def _analyze_impact(self, error: ContextualError):
        """Analyze the impact of the error."""
        try:
            impact_scope = "local"
            affected_components = []
            
            if error.function_name:
                func_obj = self._find_function(error.file_path, error.function_name)
                if func_obj and len(func_obj.call_sites) > 5:
                    impact_scope = "module"
                    affected_components.extend([site.name for site in func_obj.call_sites[:10]])
            
            if error.class_name:
                class_obj = self._find_class(error.file_path, error.class_name)
                if class_obj and len(class_obj.methods) > 10:
                    impact_scope = "project"
            
            error.impact_analysis = {
                "scope": impact_scope,
                "affected_components": affected_components,
                "severity_assessment": self._assess_impact_severity(error),
                "change_risk": self._assess_change_risk(error)
            }
        except Exception as e:
            logger.error(f"Failed to analyze impact: {e}")
    
    async def _generate_fix_suggestions(self, error: ContextualError):
        """Generate intelligent fix suggestions."""
        try:
            suggestions = []
            
            # Type-specific suggestions
            if error.error_type == "complexity_issue":
                suggestions.extend(self._get_complexity_fix_suggestions(error))
            elif error.error_type == "security_vulnerability":
                suggestions.extend(self._get_security_fix_suggestions(error))
            elif error.error_type == "performance_issue":
                suggestions.extend(self._get_performance_fix_suggestions(error))
            
            # General suggestions based on context
            suggestions.extend(self._get_contextual_suggestions(error))
            
            error.fix_suggestions = suggestions[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Failed to generate fix suggestions: {e}")
    
    async def _enhance_with_knowledge_integration(self, error: ContextualError):
        """Enhance error context with knowledge integration insights."""
        try:
            if self.knowledge_integration:
                knowledge = await self.knowledge_integration.extract_comprehensive_knowledge(
                    file_path=error.file_path,
                    symbol_name=error.function_name or error.class_name,
                    line_number=error.line_number
                )
                
                # Add semantic insights
                if "semantic" in knowledge:
                    semantic_data = knowledge["semantic"]
                    error.best_practices.extend(
                        semantic_data.get("best_practices", [])[:5]
                    )
                
                # Add architectural insights
                if "architectural" in knowledge:
                    arch_data = knowledge["architectural"]
                    error.code_examples.extend(
                        arch_data.get("code_examples", [])[:3]
                    )
        except Exception as e:
            logger.error(f"Failed to enhance with knowledge integration: {e}")
    
    # Helper methods
    def _get_file_object(self, file_path: str) -> Optional[SourceFile]:
        """Get file object by path."""
        for file in self.codebase.files:
            if file.filepath == file_path or file.name == file_path:
                return file
        return None
    
    def _find_function(self, file_path: str, function_name: str) -> Optional[Function]:
        """Find function in file."""
        file_obj = self._get_file_object(file_path)
        if file_obj:
            for func in file_obj.functions:
                if func.name == function_name:
                    return func
        return None
    
    def _find_class(self, file_path: str, class_name: str) -> Optional[Class]:
        """Find class in file."""
        file_obj = self._get_file_object(file_path)
        if file_obj:
            for cls in file_obj.classes:
                if cls.name == class_name:
                    return cls
        return None
    
    def _classify_line_type(self, line: str) -> str:
        """Classify the type of code line."""
        line = line.strip()
        if not line:
            return "empty"
        elif line.startswith("#"):
            return "comment"
        elif any(keyword in line for keyword in ["def ", "class ", "import ", "from "]):
            return "declaration"
        elif any(keyword in line for keyword in ["if ", "for ", "while ", "try:"]):
            return "control_flow"
        elif "=" in line:
            return "assignment"
        else:
            return "statement"
    
    def _calculate_complexity(self, func: Function) -> int:
        """Calculate function complexity."""
        try:
            if hasattr(func, 'source'):
                source = func.source.lower()
                complexity = 1
                complexity += source.count('if ')
                complexity += source.count('for ')
                complexity += source.count('while ')
                complexity += source.count('except ')
                return complexity
            return 1
        except Exception:
            return 1
    
    def _extract_local_variables(self, func: Function) -> List[str]:
        """Extract local variables from function."""
        variables = []
        try:
            if hasattr(func, 'source'):
                # Simple regex-based extraction
                import re
                assignments = re.findall(r'(\w+)\s*=', func.source)
                variables = list(set(assignments))
        except Exception:
            pass
        return variables[:10]
    
    def _analyze_control_flow(self, func: Function) -> Dict[str, int]:
        """Analyze control flow structures."""
        control_flow = {"if_statements": 0, "loops": 0, "try_blocks": 0}
        try:
            if hasattr(func, 'source'):
                source = func.source.lower()
                control_flow["if_statements"] = source.count('if ')
                control_flow["loops"] = source.count('for ') + source.count('while ')
                control_flow["try_blocks"] = source.count('try:')
        except Exception:
            pass
        return control_flow
    
    def _analyze_class_methods(self, cls: Class) -> Dict[str, Any]:
        """Analyze class methods."""
        return {
            "public_methods": len([m for m in cls.methods if not m.name.startswith('_')]),
            "private_methods": len([m for m in cls.methods if m.name.startswith('_')]),
            "method_complexity": sum(self._calculate_complexity(m) for m in cls.methods),
            "average_complexity": sum(self._calculate_complexity(m) for m in cls.methods) / max(1, len(cls.methods))
        }
    
    def _analyze_class_attributes(self, cls: Class) -> Dict[str, Any]:
        """Analyze class attributes."""
        return {
            "public_attributes": len([a for a in cls.attributes if not a.name.startswith('_')]),
            "private_attributes": len([a for a in cls.attributes if a.name.startswith('_')]),
            "total_attributes": len(cls.attributes)
        }
    
    def _detect_class_patterns(self, cls: Class) -> List[str]:
        """Detect design patterns in class."""
        patterns = []
        if any('factory' in m.name.lower() for m in cls.methods):
            patterns.append("Factory Pattern")
        if any('observer' in m.name.lower() for m in cls.methods):
            patterns.append("Observer Pattern")
        if any('singleton' in cls.name.lower()):
            patterns.append("Singleton Pattern")
        return patterns
    
    def _calculate_file_complexity(self, file_obj: SourceFile) -> Dict[str, float]:
        """Calculate file complexity metrics."""
        total_complexity = sum(self._calculate_complexity(f) for f in file_obj.functions)
        return {
            "total_complexity": total_complexity,
            "average_complexity": total_complexity / max(1, len(file_obj.functions)),
            "max_complexity": max((self._calculate_complexity(f) for f in file_obj.functions), default=0)
        }
    
    def _assess_file_quality(self, file_obj: SourceFile) -> Dict[str, Any]:
        """Assess file code quality."""
        lines = file_obj.source.splitlines()
        return {
            "comment_ratio": len([l for l in lines if l.strip().startswith('#')]) / max(1, len(lines)),
            "function_density": len(file_obj.functions) / max(1, len(lines)),
            "class_density": len(file_obj.classes) / max(1, len(lines))
        }
    
    def _get_module_files(self, module_path: str) -> List[SourceFile]:
        """Get all files in a module."""
        return [f for f in self.codebase.files if str(Path(f.filepath).parent) == module_path]
    
    def _analyze_module_dependencies(self, files: List[SourceFile]) -> Dict[str, int]:
        """Analyze module dependencies."""
        internal_deps = 0
        external_deps = 0
        
        for file in files:
            for imp in file.imports:
                if any(imp.name in f.filepath for f in files):
                    internal_deps += 1
                else:
                    external_deps += 1
        
        return {"internal": internal_deps, "external": external_deps}
    
    def _determine_architectural_role(self, module_path: str) -> str:
        """Determine the architectural role of a module."""
        path_lower = module_path.lower()
        if 'controller' in path_lower:
            return "controller"
        elif 'service' in path_lower:
            return "service"
        elif 'model' in path_lower:
            return "model"
        elif 'view' in path_lower:
            return "view"
        elif 'util' in path_lower:
            return "utility"
        else:
            return "unknown"
    
    def _detect_languages(self) -> List[str]:
        """Detect programming languages in the project."""
        extensions = set()
        for file in self.codebase.files:
            ext = Path(file.filepath).suffix.lower()
            if ext:
                extensions.add(ext)
        return list(extensions)
    
    def _detect_project_patterns(self) -> List[str]:
        """Detect architectural patterns in the project."""
        patterns = []
        file_paths = [f.filepath.lower() for f in self.codebase.files]
        
        if any('controller' in path for path in file_paths):
            patterns.append("MVC Pattern")
        if any('service' in path for path in file_paths):
            patterns.append("Service Layer")
        if any('repository' in path for path in file_paths):
            patterns.append("Repository Pattern")
        
        return patterns
    
    def _analyze_technology_stack(self) -> Dict[str, List[str]]:
        """Analyze the technology stack."""
        frameworks = []
        libraries = []
        
        # Analyze imports to detect frameworks/libraries
        for file in self.codebase.files:
            for imp in file.imports:
                imp_name = imp.name.lower()
                if any(fw in imp_name for fw in ['django', 'flask', 'fastapi']):
                    frameworks.append(imp.name)
                elif any(lib in imp_name for lib in ['numpy', 'pandas', 'requests']):
                    libraries.append(imp.name)
        
        return {
            "frameworks": list(set(frameworks))[:10],
            "libraries": list(set(libraries))[:20]
        }
    
    def _assess_project_health(self) -> Dict[str, Any]:
        """Assess overall project health."""
        total_files = len(list(self.codebase.files))
        total_functions = len(list(self.codebase.functions))
        
        return {
            "size_category": "small" if total_files < 50 else "medium" if total_files < 200 else "large",
            "function_to_file_ratio": total_functions / max(1, total_files),
            "estimated_complexity": "low" if total_functions < 100 else "medium" if total_functions < 500 else "high"
        }
    
    def _build_dependency_chain(self, func: Function) -> List[str]:
        """Build dependency chain for a function."""
        chain = []
        try:
            for dep in func.dependencies[:5]:
                chain.append(dep.name)
        except Exception:
            pass
        return chain
    
    def _assess_impact_severity(self, error: ContextualError) -> str:
        """Assess the severity of error impact."""
        if error.severity == "critical":
            return "high"
        elif error.function_context and error.function_context.get("call_sites", 0) > 10:
            return "medium"
        else:
            return "low"
    
    def _assess_change_risk(self, error: ContextualError) -> str:
        """Assess the risk of making changes."""
        if error.class_context and error.class_context.get("class_info", {}).get("method_count", 0) > 20:
            return "high"
        elif error.function_context and error.function_context.get("function_info", {}).get("complexity", 0) > 15:
            return "medium"
        else:
            return "low"
    
    def _get_complexity_fix_suggestions(self, error: ContextualError) -> List[Dict[str, Any]]:
        """Get fix suggestions for complexity issues."""
        return [
            {
                "type": "refactor",
                "description": "Break down the function into smaller, more focused functions",
                "priority": "high",
                "effort": "medium"
            },
            {
                "type": "extract_method",
                "description": "Extract complex logic into separate methods",
                "priority": "medium",
                "effort": "low"
            }
        ]
    
    def _get_security_fix_suggestions(self, error: ContextualError) -> List[Dict[str, Any]]:
        """Get fix suggestions for security issues."""
        return [
            {
                "type": "security_fix",
                "description": "Add input validation and sanitization",
                "priority": "critical",
                "effort": "low"
            },
            {
                "type": "security_review",
                "description": "Conduct security review of the affected component",
                "priority": "high",
                "effort": "medium"
            }
        ]
    
    def _get_performance_fix_suggestions(self, error: ContextualError) -> List[Dict[str, Any]]:
        """Get fix suggestions for performance issues."""
        return [
            {
                "type": "optimization",
                "description": "Optimize algorithm or data structure usage",
                "priority": "medium",
                "effort": "medium"
            },
            {
                "type": "caching",
                "description": "Add caching to reduce computational overhead",
                "priority": "low",
                "effort": "low"
            }
        ]
    
    def _get_contextual_suggestions(self, error: ContextualError) -> List[Dict[str, Any]]:
        """Get contextual suggestions based on error context."""
        suggestions = []
        
        if error.function_context:
            complexity = error.function_context.get("function_info", {}).get("complexity", 0)
            if complexity > 10:
                suggestions.append({
                    "type": "complexity_reduction",
                    "description": f"Function complexity is {complexity}, consider simplifying",
                    "priority": "medium",
                    "effort": "medium"
                })
        
        return suggestions

