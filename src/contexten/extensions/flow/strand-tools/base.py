"""
Base Tool Implementation for Strand Tools
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from strands_agents.tools import Tool

class BaseTool(Tool, ABC):
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        **kwargs
    ):
        """
        Initialize base tool.
        
        Args:
            name: Tool name
            description: Tool description
            version: Tool version
            **kwargs: Additional tool configuration
        """
        super().__init__(
            name=name,
            description=description,
            version=version,
            **kwargs
        )
        
    @abstractmethod
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute tool action.
        
        Args:
            action: Action to execute
            parameters: Optional action parameters
            
        Returns:
            Dict containing execution results
        """
        pass
    
    @abstractmethod
    def can_handle(self, action: str) -> bool:
        """
        Check if tool can handle action.
        
        Args:
            action: Action to check
            
        Returns:
            True if tool can handle action, False otherwise
        """
        pass
    
    def validate_parameters(
        self,
        action: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and process action parameters.
        
        Args:
            action: Action being executed
            parameters: Parameters to validate
            
        Returns:
            Validated parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Default implementation - override in specific tools
        return parameters
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema including supported actions and parameters.
        
        Returns:
            Dict containing tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "actions": self.get_supported_actions(),
            "parameters": self.get_parameter_schema()
        }
    
    def get_supported_actions(self) -> Dict[str, str]:
        """
        Get mapping of supported actions to descriptions.
        
        Returns:
            Dict mapping action names to descriptions
        """
        # Default implementation - override in specific tools
        return {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get schema for tool parameters.
        
        Returns:
            Dict containing parameter schema
        """
        # Default implementation - override in specific tools
        return {}

