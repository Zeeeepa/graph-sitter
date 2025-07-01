"""Context Gatherer for rich context extraction from GraphSitter analysis."""

import logging
from typing import Any, Dict, List, Union

from graph_sitter.core.file import File
from graph_sitter.core.interfaces.editable import Editable

logger = logging.getLogger(__name__)


class ContextGatherer:
    """Rich context extraction from GraphSitter analysis."""
    
    def __init__(self, codebase):
        """Initialize with codebase reference."""
        self.codebase = codebase
    
    def gather_target_context(self, target: Editable) -> Dict[str, Any]:
        """Gather comprehensive context for a target editable object.
        
        Args:
            target: The target editable object to gather context for
            
        Returns:
            Dictionary containing rich context information
        """
        context = {
            "target_info": self._get_target_info(target),
            "static_analysis": self._get_static_analysis(target),
            "relationships": self._get_relationships(target),
            "codebase_summary": self._get_codebase_summary()
        }
        
        return context
    
    def _get_target_info(self, target: Editable) -> Dict[str, Any]:
        """Get basic information about the target."""
        info = {
            "type": target.__class__.__name__,
            "name": getattr(target, "name", "unknown"),
            "location": {
                "file": target.file.filepath if hasattr(target, "file") else "unknown",
                "line_start": getattr(target, "line_start", None),
                "line_end": getattr(target, "line_end", None)
            },
            "source_preview": self._get_source_preview(target)
        }
        
        # Add signature for functions/methods
        if hasattr(target, "signature"):
            info["signature"] = target.signature
        
        # Add class info for methods
        if hasattr(target, "parent_class") and target.parent_class:
            info["parent_class"] = target.parent_class.name
        
        return info
    
    def _get_static_analysis(self, target: Editable) -> Dict[str, Any]:
        """Get static analysis information."""
        analysis = {
            "call_sites": [],
            "dependencies": [],
            "usages": []
        }
        
        try:
            # Get call sites with context
            if hasattr(target, "call_sites"):
                for call_site in target.call_sites[:10]:  # Limit to first 10
                    call_context = {
                        "location": {
                            "file": call_site.file.filepath if hasattr(call_site, "file") else "unknown",
                            "line": getattr(call_site, "line_start", None)
                        },
                        "context": self._get_surrounding_context(call_site, lines=3)
                    }
                    analysis["call_sites"].append(call_context)
            
            # Get dependencies
            if hasattr(target, "dependencies"):
                for dep in target.dependencies[:10]:  # Limit to first 10
                    dep_info = {
                        "name": getattr(dep, "name", str(dep)),
                        "type": dep.__class__.__name__,
                        "location": {
                            "file": dep.file.filepath if hasattr(dep, "file") else "unknown"
                        }
                    }
                    analysis["dependencies"].append(dep_info)
            
            # Get usages
            if hasattr(target, "usages"):
                for usage in target.usages[:10]:  # Limit to first 10
                    usage_info = {
                        "location": {
                            "file": usage.file.filepath if hasattr(usage, "file") else "unknown",
                            "line": getattr(usage, "line_start", None)
                        },
                        "context": self._get_surrounding_context(usage, lines=2)
                    }
                    analysis["usages"].append(usage_info)
        
        except Exception as e:
            logger.warning(f"Error gathering static analysis: {e}")
        
        return analysis
    
    def _get_relationships(self, target: Editable) -> Dict[str, Any]:
        """Get relationship information."""
        relationships = {
            "parent_child": {},
            "siblings": []
        }
        
        try:
            # Parent/child relationships
            if hasattr(target, "parent") and target.parent:
                relationships["parent_child"]["parent"] = {
                    "name": getattr(target.parent, "name", "unknown"),
                    "type": target.parent.__class__.__name__
                }
            
            if hasattr(target, "children"):
                relationships["parent_child"]["children"] = [
                    {
                        "name": getattr(child, "name", "unknown"),
                        "type": child.__class__.__name__
                    }
                    for child in target.children[:5]  # Limit to first 5
                ]
            
            # Sibling methods/functions
            if hasattr(target, "parent_class") and target.parent_class:
                siblings = []
                if hasattr(target.parent_class, "methods"):
                    for method in target.parent_class.methods:
                        if method != target:
                            siblings.append({
                                "name": method.name,
                                "type": "method"
                            })
                relationships["siblings"] = siblings[:5]  # Limit to first 5
            elif hasattr(target, "file") and target.file:
                # For functions, get other functions in the same file
                siblings = []
                if hasattr(target.file, "functions"):
                    for func in target.file.functions:
                        if func != target:
                            siblings.append({
                                "name": func.name,
                                "type": "function"
                            })
                relationships["siblings"] = siblings[:5]  # Limit to first 5
        
        except Exception as e:
            logger.warning(f"Error gathering relationships: {e}")
        
        return relationships
    
    def _get_codebase_summary(self) -> Dict[str, Any]:
        """Get high-level codebase overview."""
        try:
            summary = {
                "total_files": len(self.codebase.files),
                "total_classes": len(self.codebase.classes),
                "total_functions": len(self.codebase.functions),
                "languages": list(set(
                    file.language for file in self.codebase.files 
                    if hasattr(file, "language") and file.language
                )),
                "main_directories": self._get_main_directories()
            }
            
            # Add project description if available
            if hasattr(self.codebase, "description"):
                summary["description"] = self.codebase.description
            
            return summary
        except Exception as e:
            logger.warning(f"Error gathering codebase summary: {e}")
            return {"error": str(e)}
    
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
            elif hasattr(target, "extended_source"):
                lines = target.extended_source.split("\n")
                if len(lines) <= max_lines:
                    return target.extended_source
                else:
                    preview_lines = lines[:max_lines]
                    return "\n".join(preview_lines) + f"\n... ({len(lines) - max_lines} more lines)"
            else:
                return "Source not available"
        except Exception:
            return "Error retrieving source"
    
    def _get_surrounding_context(self, target: Editable, lines: int = 3) -> str:
        """Get surrounding context for a target."""
        try:
            if not hasattr(target, "file") or not hasattr(target, "line_start"):
                return "Context not available"
            
            file_lines = target.file.source.split("\n")
            start_line = max(0, target.line_start - lines - 1)
            end_line = min(len(file_lines), target.line_start + lines)
            
            context_lines = file_lines[start_line:end_line]
            return "\n".join(context_lines)
        except Exception:
            return "Error retrieving context"
    
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

