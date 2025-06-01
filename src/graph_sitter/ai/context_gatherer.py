"""
Context Gathering System for AI-Enhanced Codebase Operations

Leverages GraphSitter's static analysis to gather rich contextual information
for AI-powered code analysis, generation, and refactoring.
"""

import json
from typing import Any, Dict, List, Optional, Union

from graph_sitter.core.interfaces.editable import Editable
from graph_sitter.core.file import File
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.symbol import Symbol
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ContextGatherer:
    """Gathers and formats contextual information for AI operations"""
    
    def __init__(self, codebase):
        self.codebase = codebase
    
    def gather_context(
        self,
        target: Optional[Editable] = None,
        context: Optional[Union[str, Editable, List[Editable], Dict[str, Any]]] = None,
        include_call_sites: bool = True,
        include_dependencies: bool = True,
        include_usages: bool = True,
        include_related_symbols: bool = True,
        max_context_size: int = 8000
    ) -> Dict[str, Any]:
        """
        Gather comprehensive context for AI operations
        
        Args:
            target: Primary target for analysis (function, class, file, etc.)
            context: Additional context provided by user
            include_call_sites: Include where the target is called
            include_dependencies: Include what the target depends on
            include_usages: Include how the target is used
            include_related_symbols: Include related symbols (same class, module, etc.)
            max_context_size: Maximum size of context in characters
            
        Returns:
            Dict containing structured context information
        """
        
        gathered_context = {
            "target_info": {},
            "static_analysis": {},
            "relationships": {},
            "user_context": {},
            "codebase_summary": {}
        }
        
        # Gather target information
        if target:
            gathered_context["target_info"] = self._gather_target_info(target)
            gathered_context["static_analysis"] = self._gather_static_analysis(
                target, include_call_sites, include_dependencies, include_usages
            )
            gathered_context["relationships"] = self._gather_relationships(
                target, include_related_symbols
            )
        
        # Process user-provided context
        if context:
            gathered_context["user_context"] = self._process_user_context(context)
        
        # Add codebase summary
        gathered_context["codebase_summary"] = self._gather_codebase_summary()
        
        # Truncate if necessary
        if max_context_size > 0:
            gathered_context = self._truncate_context(gathered_context, max_context_size)
        
        return gathered_context
    
    def _gather_target_info(self, target: Editable) -> Dict[str, Any]:
        """Gather basic information about the target"""
        info = {
            "type": target.__class__.__name__,
            "name": getattr(target, "name", "unknown"),
            "qualified_name": getattr(target, "qualified_name", ""),
            "file_path": getattr(target, "file", {}).get("filepath", "") if hasattr(target, "file") else "",
            "start_line": getattr(target, "start_line", 0),
            "end_line": getattr(target, "end_line", 0),
            "source_preview": self._get_source_preview(target)
        }
        
        # Add type-specific information
        if isinstance(target, Function):
            info.update({
                "signature": getattr(target, "signature", ""),
                "parameters": [p.name for p in getattr(target, "parameters", [])],
                "return_type": getattr(target, "return_type", None),
                "is_async": getattr(target, "is_async", False),
                "is_static": getattr(target, "is_static", False),
                "docstring": getattr(target, "docstring", None)
            })
        elif isinstance(target, Class):
            info.update({
                "superclasses": [cls.name for cls in getattr(target, "superclasses", [])],
                "methods": [m.name for m in getattr(target, "methods", [])],
                "attributes": [attr.name for attr in getattr(target, "attributes", [])],
                "docstring": getattr(target, "docstring", None)
            })
        elif isinstance(target, File):
            info.update({
                "language": getattr(target, "language", ""),
                "extension": getattr(target, "extension", ""),
                "size": len(getattr(target, "source", "")),
                "line_count": len(getattr(target, "source", "").splitlines()),
                "functions_count": len(getattr(target, "functions", [])),
                "classes_count": len(getattr(target, "classes", []))
            })
        
        return info
    
    def _gather_static_analysis(
        self,
        target: Editable,
        include_call_sites: bool,
        include_dependencies: bool,
        include_usages: bool
    ) -> Dict[str, Any]:
        """Gather static analysis information"""
        analysis = {}
        
        if include_call_sites and hasattr(target, "call_sites"):
            try:
                call_sites = list(target.call_sites)
                analysis["call_sites"] = [
                    {
                        "file": getattr(cs, "file", {}).get("filepath", "") if hasattr(cs, "file") else "",
                        "line": getattr(cs, "line_number", 0),
                        "context": self._get_source_preview(cs, lines_before=2, lines_after=2)
                    }
                    for cs in call_sites[:10]  # Limit to first 10
                ]
                analysis["call_sites_count"] = len(call_sites)
            except Exception as e:
                logger.debug(f"Could not gather call sites: {e}")
                analysis["call_sites"] = []
        
        if include_dependencies and hasattr(target, "dependencies"):
            try:
                dependencies = list(target.dependencies)
                analysis["dependencies"] = [
                    {
                        "name": getattr(dep, "name", "unknown"),
                        "type": dep.__class__.__name__,
                        "file": getattr(dep, "file", {}).get("filepath", "") if hasattr(dep, "file") else ""
                    }
                    for dep in dependencies[:20]  # Limit to first 20
                ]
                analysis["dependencies_count"] = len(dependencies)
            except Exception as e:
                logger.debug(f"Could not gather dependencies: {e}")
                analysis["dependencies"] = []
        
        if include_usages and hasattr(target, "usages"):
            try:
                usages = list(target.usages)
                analysis["usages"] = [
                    {
                        "file": getattr(usage, "file", {}).get("filepath", "") if hasattr(usage, "file") else "",
                        "line": getattr(usage, "line_number", 0),
                        "context": self._get_source_preview(usage, lines_before=1, lines_after=1)
                    }
                    for usage in usages[:10]  # Limit to first 10
                ]
                analysis["usages_count"] = len(usages)
            except Exception as e:
                logger.debug(f"Could not gather usages: {e}")
                analysis["usages"] = []
        
        return analysis
    
    def _gather_relationships(self, target: Editable, include_related_symbols: bool) -> Dict[str, Any]:
        """Gather relationship information"""
        relationships = {}
        
        # Parent relationships
        if hasattr(target, "parent") and target.parent:
            relationships["parent"] = {
                "name": getattr(target.parent, "name", "unknown"),
                "type": target.parent.__class__.__name__,
                "file": getattr(target.parent, "file", {}).get("filepath", "") if hasattr(target.parent, "file") else ""
            }
        
        # Sibling relationships (for methods in a class, functions in a file, etc.)
        if include_related_symbols:
            if isinstance(target, Function) and hasattr(target, "parent") and target.parent:
                # Other methods in the same class
                if hasattr(target.parent, "methods"):
                    siblings = [m for m in target.parent.methods if m.name != target.name]
                    relationships["sibling_methods"] = [
                        {
                            "name": m.name,
                            "signature": getattr(m, "signature", ""),
                            "line": getattr(m, "start_line", 0)
                        }
                        for m in siblings[:10]
                    ]
            elif isinstance(target, Function) and hasattr(target, "file"):
                # Other functions in the same file
                if hasattr(target.file, "functions"):
                    siblings = [f for f in target.file.functions if f.name != target.name]
                    relationships["sibling_functions"] = [
                        {
                            "name": f.name,
                            "signature": getattr(f, "signature", ""),
                            "line": getattr(f, "start_line", 0)
                        }
                        for f in siblings[:10]
                    ]
        
        return relationships
    
    def _process_user_context(self, context: Union[str, Editable, List[Editable], Dict[str, Any]]) -> Dict[str, Any]:
        """Process user-provided context"""
        if isinstance(context, str):
            return {"text": context}
        elif isinstance(context, Editable):
            return {"editable": self._gather_target_info(context)}
        elif isinstance(context, list):
            return {
                "editables": [self._gather_target_info(item) for item in context if isinstance(item, Editable)]
            }
        elif isinstance(context, dict):
            processed = {}
            for key, value in context.items():
                if isinstance(value, str):
                    processed[key] = value
                elif isinstance(value, Editable):
                    processed[key] = self._gather_target_info(value)
                elif isinstance(value, list):
                    processed[key] = [
                        self._gather_target_info(item) if isinstance(item, Editable) else str(item)
                        for item in value
                    ]
                else:
                    processed[key] = str(value)
            return processed
        else:
            return {"raw": str(context)}
    
    def _gather_codebase_summary(self) -> Dict[str, Any]:
        """Gather high-level codebase summary"""
        try:
            return {
                "total_files": len(self.codebase.files),
                "total_functions": len(self.codebase.functions),
                "total_classes": len(self.codebase.classes),
                "languages": list(set(f.language for f in self.codebase.files if hasattr(f, "language"))),
                "main_directories": [
                    d.name for d in getattr(self.codebase, "directories", [])[:10]
                ] if hasattr(self.codebase, "directories") else []
            }
        except Exception as e:
            logger.debug(f"Could not gather codebase summary: {e}")
            return {}
    
    def _get_source_preview(self, target: Editable, lines_before: int = 3, lines_after: int = 3) -> str:
        """Get a preview of the source code around the target"""
        try:
            if hasattr(target, "source"):
                return target.source[:500]  # First 500 characters
            elif hasattr(target, "extended_source"):
                return target.extended_source[:500]
            else:
                return ""
        except Exception:
            return ""
    
    def _truncate_context(self, context: Dict[str, Any], max_size: int) -> Dict[str, Any]:
        """Truncate context to fit within size limits"""
        context_str = json.dumps(context, default=str)
        
        if len(context_str) <= max_size:
            return context
        
        # Progressively remove less important information
        truncated = context.copy()
        
        # Remove source previews first
        if "static_analysis" in truncated:
            for key in ["call_sites", "usages"]:
                if key in truncated["static_analysis"]:
                    for item in truncated["static_analysis"][key]:
                        if "context" in item:
                            item["context"] = item["context"][:100] + "..." if len(item["context"]) > 100 else item["context"]
        
        # Limit lists
        for section in truncated.values():
            if isinstance(section, dict):
                for key, value in section.items():
                    if isinstance(value, list) and len(value) > 5:
                        section[key] = value[:5] + [{"truncated": f"... and {len(value) - 5} more"}]
        
        return truncated
    
    def format_context_for_ai(self, context: Dict[str, Any]) -> str:
        """Format gathered context for AI consumption"""
        formatted_sections = []
        
        # Target information
        if context.get("target_info"):
            target_info = context["target_info"]
            section = f"=== TARGET: {target_info.get('name', 'Unknown')} ({target_info.get('type', 'Unknown')}) ===\n"
            
            if target_info.get("file_path"):
                section += f"File: {target_info['file_path']}\n"
            if target_info.get("start_line"):
                section += f"Lines: {target_info['start_line']}-{target_info.get('end_line', target_info['start_line'])}\n"
            if target_info.get("signature"):
                section += f"Signature: {target_info['signature']}\n"
            if target_info.get("docstring"):
                section += f"Documentation: {target_info['docstring']}\n"
            if target_info.get("source_preview"):
                section += f"Source Preview:\n{target_info['source_preview']}\n"
            
            formatted_sections.append(section)
        
        # Static analysis
        if context.get("static_analysis"):
            analysis = context["static_analysis"]
            section = "=== STATIC ANALYSIS ===\n"
            
            if analysis.get("call_sites"):
                section += f"Called from {analysis.get('call_sites_count', len(analysis['call_sites']))} locations:\n"
                for cs in analysis["call_sites"][:5]:
                    section += f"  - {cs.get('file', 'unknown')}:{cs.get('line', 0)}\n"
                    if cs.get("context"):
                        section += f"    {cs['context'][:100]}...\n"
            
            if analysis.get("dependencies"):
                section += f"Depends on {analysis.get('dependencies_count', len(analysis['dependencies']))} symbols:\n"
                for dep in analysis["dependencies"][:5]:
                    section += f"  - {dep.get('name', 'unknown')} ({dep.get('type', 'unknown')})\n"
            
            if analysis.get("usages"):
                section += f"Used in {analysis.get('usages_count', len(analysis['usages']))} locations:\n"
                for usage in analysis["usages"][:5]:
                    section += f"  - {usage.get('file', 'unknown')}:{usage.get('line', 0)}\n"
            
            formatted_sections.append(section)
        
        # Relationships
        if context.get("relationships"):
            relationships = context["relationships"]
            section = "=== RELATIONSHIPS ===\n"
            
            if relationships.get("parent"):
                parent = relationships["parent"]
                section += f"Parent: {parent.get('name', 'unknown')} ({parent.get('type', 'unknown')})\n"
            
            if relationships.get("sibling_methods"):
                section += "Sibling methods:\n"
                for method in relationships["sibling_methods"][:5]:
                    section += f"  - {method.get('name', 'unknown')}() at line {method.get('line', 0)}\n"
            
            if relationships.get("sibling_functions"):
                section += "Other functions in file:\n"
                for func in relationships["sibling_functions"][:5]:
                    section += f"  - {func.get('name', 'unknown')}() at line {func.get('line', 0)}\n"
            
            formatted_sections.append(section)
        
        # User context
        if context.get("user_context"):
            user_ctx = context["user_context"]
            section = "=== USER PROVIDED CONTEXT ===\n"
            section += json.dumps(user_ctx, indent=2, default=str)
            formatted_sections.append(section)
        
        # Codebase summary
        if context.get("codebase_summary"):
            summary = context["codebase_summary"]
            section = "=== CODEBASE OVERVIEW ===\n"
            section += f"Files: {summary.get('total_files', 0)}, "
            section += f"Functions: {summary.get('total_functions', 0)}, "
            section += f"Classes: {summary.get('total_classes', 0)}\n"
            if summary.get("languages"):
                section += f"Languages: {', '.join(summary['languages'])}\n"
            formatted_sections.append(section)
        
        return "\n\n".join(formatted_sections)

