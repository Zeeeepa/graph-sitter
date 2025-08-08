"""
Semantic Tools for Serena MCP Integration

This module provides high-level semantic tools that use the Serena MCP server
to perform code retrieval, editing, and analysis operations.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json

from graph_sitter.shared.logging.get_logger import get_logger
from .mcp_bridge import SerenaMCPBridge, MCPToolResult

logger = get_logger(__name__)


class SemanticTools:
    """High-level semantic tools using Serena MCP server."""
    
    def __init__(self, mcp_bridge: SerenaMCPBridge):
        self.mcp_bridge = mcp_bridge
    
    def semantic_search(self, query: str, file_pattern: Optional[str] = None, 
                       max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search across the codebase.
        
        Args:
            query: Search query (natural language or code pattern)
            file_pattern: Optional file pattern to limit search
            max_results: Maximum number of results to return
        
        Returns:
            List of search results with file paths, line numbers, and relevance scores
        """
        if not self.mcp_bridge.is_tool_available("semantic_search"):
            logger.warning("semantic_search tool not available")
            return []
        
        args = {
            "query": query,
            "max_results": max_results
        }
        
        if file_pattern:
            args["file_pattern"] = file_pattern
        
        result = self.mcp_bridge.call_tool("semantic_search", args)
        
        if result.success and result.content:
            return self._parse_search_results(result.content)
        else:
            logger.error(f"Semantic search failed: {result.error}")
            return []
    
    def find_symbol(self, symbol_name: str, symbol_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find symbol definitions and references.
        
        Args:
            symbol_name: Name of the symbol to find
            symbol_type: Optional type filter (function, class, variable, etc.)
        
        Returns:
            List of symbol locations with context
        """
        if not self.mcp_bridge.is_tool_available("find_symbol"):
            logger.warning("find_symbol tool not available")
            return []
        
        args = {"symbol_name": symbol_name}
        if symbol_type:
            args["symbol_type"] = symbol_type
        
        result = self.mcp_bridge.call_tool("find_symbol", args)
        
        if result.success and result.content:
            return self._parse_symbol_results(result.content)
        else:
            logger.error(f"Find symbol failed: {result.error}")
            return []
    
    def get_symbol_context(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get context information for a symbol at a specific position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Symbol context information or None
        """
        if not self.mcp_bridge.is_tool_available("get_symbol_context"):
            logger.warning("get_symbol_context tool not available")
            return None
        
        args = {
            "file_path": file_path,
            "line": line,
            "character": character
        }
        
        result = self.mcp_bridge.call_tool("get_symbol_context", args)
        
        if result.success and result.content:
            return result.content
        else:
            logger.error(f"Get symbol context failed: {result.error}")
            return None
    
    def edit_code(self, file_path: str, start_line: int, end_line: int, 
                  new_content: str, description: Optional[str] = None) -> bool:
        """
        Edit code in a file using semantic understanding.
        
        Args:
            file_path: Path to the file to edit
            start_line: Start line of the edit (0-based)
            end_line: End line of the edit (0-based)
            new_content: New content to insert
            description: Optional description of the change
        
        Returns:
            True if edit was successful, False otherwise
        """
        if not self.mcp_bridge.is_tool_available("edit_code"):
            logger.warning("edit_code tool not available")
            return False
        
        args = {
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "new_content": new_content
        }
        
        if description:
            args["description"] = description
        
        result = self.mcp_bridge.call_tool("edit_code", args)
        
        if result.success:
            logger.info(f"Successfully edited {file_path} lines {start_line}-{end_line}")
            return True
        else:
            logger.error(f"Code edit failed: {result.error}")
            return False
    
    def get_completions(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """
        Get code completions at a specific position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            List of completion items
        """
        if not self.mcp_bridge.is_tool_available("get_completions"):
            logger.warning("get_completions tool not available")
            return []
        
        args = {
            "file_path": file_path,
            "line": line,
            "character": character
        }
        
        result = self.mcp_bridge.call_tool("get_completions", args)
        
        if result.success and result.content:
            return self._parse_completion_results(result.content)
        else:
            logger.error(f"Get completions failed: {result.error}")
            return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get hover information for a symbol at a specific position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Hover information or None
        """
        if not self.mcp_bridge.is_tool_available("get_hover_info"):
            logger.warning("get_hover_info tool not available")
            return None
        
        args = {
            "file_path": file_path,
            "line": line,
            "character": character
        }
        
        result = self.mcp_bridge.call_tool("get_hover_info", args)
        
        if result.success and result.content:
            return result.content
        else:
            logger.error(f"Get hover info failed: {result.error}")
            return None
    
    def refactor_rename(self, file_path: str, line: int, character: int, 
                       new_name: str, preview: bool = False) -> Dict[str, Any]:
        """
        Rename a symbol across the codebase.
        
        Args:
            file_path: Path to the file containing the symbol
            line: Line number (0-based)
            character: Character position (0-based)
            new_name: New name for the symbol
            preview: Whether to return preview without applying changes
        
        Returns:
            Refactoring result with changes and conflicts
        """
        if not self.mcp_bridge.is_tool_available("refactor_rename"):
            logger.warning("refactor_rename tool not available")
            return {"success": False, "error": "Tool not available"}
        
        args = {
            "file_path": file_path,
            "line": line,
            "character": character,
            "new_name": new_name,
            "preview": preview
        }
        
        result = self.mcp_bridge.call_tool("refactor_rename", args)
        
        if result.success and result.content:
            return result.content
        else:
            return {"success": False, "error": result.error}
    
    def analyze_code_quality(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze code quality and get suggestions.
        
        Args:
            file_path: Optional specific file to analyze, or None for entire codebase
        
        Returns:
            Code quality analysis results
        """
        if not self.mcp_bridge.is_tool_available("analyze_code_quality"):
            logger.warning("analyze_code_quality tool not available")
            return {"success": False, "error": "Tool not available"}
        
        args = {}
        if file_path:
            args["file_path"] = file_path
        
        result = self.mcp_bridge.call_tool("analyze_code_quality", args)
        
        if result.success and result.content:
            return result.content
        else:
            return {"success": False, "error": result.error}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools."""
        return list(self.mcp_bridge.get_available_tools().keys())
    
    def _parse_search_results(self, content: Any) -> List[Dict[str, Any]]:
        """Parse search results from MCP response."""
        if isinstance(content, list):
            return content
        elif isinstance(content, dict) and "results" in content:
            return content["results"]
        else:
            logger.warning(f"Unexpected search results format: {type(content)}")
            return []
    
    def _parse_symbol_results(self, content: Any) -> List[Dict[str, Any]]:
        """Parse symbol results from MCP response."""
        if isinstance(content, list):
            return content
        elif isinstance(content, dict) and "symbols" in content:
            return content["symbols"]
        else:
            logger.warning(f"Unexpected symbol results format: {type(content)}")
            return []
    
    def _parse_completion_results(self, content: Any) -> List[Dict[str, Any]]:
        """Parse completion results from MCP response."""
        if isinstance(content, list):
            return content
        elif isinstance(content, dict) and "completions" in content:
            return content["completions"]
        else:
            logger.warning(f"Unexpected completion results format: {type(content)}")
            return []
