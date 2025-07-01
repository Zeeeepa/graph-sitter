"""
MCP Client integration for Strand Agents
"""

from typing import Dict, Any, Optional
from strands_agents.mcp import BaseMCPClient
from strands_agents.workflow import WorkflowContext

class MCPClient(BaseMCPClient):
    def __init__(
        self,
        server_url: str,
        context: Optional[WorkflowContext] = None,
        **kwargs
    ):
        """
        Initialize MCP client for model interactions.
        
        Args:
            server_url: URL of the MCP server
            context: Optional workflow context
            **kwargs: Additional configuration parameters
        """
        super().__init__(server_url=server_url, **kwargs)
        self.context = context or WorkflowContext()
        
    async def get_completion(
        self,
        prompt: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get completion from the model via MCP.
        
        Args:
            prompt: The prompt to send to the model
            params: Optional model parameters
            
        Returns:
            Dict containing model response
        """
        # Prepare request with context
        request = {
            "prompt": prompt,
            "parameters": params or {},
            "context": self.context.get_model_context()
        }
        
        # Get completion from model
        response = await self._send_request(
            method="POST",
            endpoint="/v1/completions",
            data=request
        )
        
        # Update context with model response
        self.context.update_model_interaction(response)
        
        return response
    
    async def get_embeddings(
        self,
        texts: List[str],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get embeddings for texts via MCP.
        
        Args:
            texts: List of texts to get embeddings for
            params: Optional model parameters
            
        Returns:
            Dict containing embeddings
        """
        request = {
            "texts": texts,
            "parameters": params or {}
        }
        
        return await self._send_request(
            method="POST",
            endpoint="/v1/embeddings",
            data=request
        )
    
    async def get_tool_response(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get tool execution response via MCP.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            params: Optional execution parameters
            
        Returns:
            Dict containing tool execution results
        """
        request = {
            "tool": tool_name,
            "input": tool_input,
            "parameters": params or {},
            "context": self.context.get_tool_context()
        }
        
        response = await self._send_request(
            method="POST",
            endpoint="/v1/tools/execute",
            data=request
        )
        
        # Update context with tool execution results
        self.context.update_tool_execution(response)
        
        return response

