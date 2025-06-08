"""
Tool Registry Implementation
"""

from typing import Dict, List, Any, Type, Optional
from .base import BaseTool

class ToolRegistry:
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        
    def register_tool_class(
        self,
        tool_class: Type[BaseTool],
        **kwargs
    ) -> None:
        """
        Register a tool class in the registry.
        
        Args:
            tool_class: Tool class to register
            **kwargs: Arguments to pass to tool constructor
        """
        tool = tool_class(**kwargs)
        self.register_tool(tool)
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
        
    def get_tools(self, names: Optional[List[str]] = None) -> List[BaseTool]:
        """
        Get multiple tools by name.
        
        Args:
            names: Optional list of tool names. If None, returns all tools.
            
        Returns:
            List of tool instances
        """
        if names is None:
            return list(self._tools.values())
        return [
            tool for name, tool in self._tools.items()
            if name in names
        ]
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools with their schemas.
        
        Returns:
            List of tool schemas
        """
        return [
            tool.get_schema()
            for tool in self._tools.values()
        ]
        
    def find_tool_for_action(self, action: str) -> Optional[BaseTool]:
        """
        Find tool that can handle an action.
        
        Args:
            action: Action to handle
            
        Returns:
            Tool instance or None if no tool can handle action
        """
        for tool in self._tools.values():
            if tool.can_handle(action):
                return tool
        return None

