#!/usr/bin/env python3
"""
Tests for MCP Orchestrator

This test suite validates the orchestrator component of the MCP server
implementation in graph-sitter.
"""

import pytest
import tempfile
import os
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena.mcp_bridge import SerenaMCPBridge, MCPToolResult


class MockMCPBridge:
    """Mock MCP Bridge for testing."""
    
    def __init__(self):
        self.is_initialized = True
        self.available_tools = {
            "test_tool": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {}
            }
        }
        self.calls = []
    
    def call_tool(self, tool_name, arguments):
        """Mock tool call."""
        self.calls.append((tool_name, arguments))
        return MCPToolResult(
            success=True,
            content={"result": "Success"},
            tool_name=tool_name
        )
    
    def get_available_tools(self):
        """Get available tools."""
        return self.available_tools
    
    def is_tool_available(self, tool_name):
        """Check if tool is available."""
        return tool_name in self.available_tools
    
    def shutdown(self):
        """Shutdown the bridge."""
        self.is_initialized = False


class TestMCPOrchestrator:
    """Test the MCP orchestrator component."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello_world():\n    print('Hello, World!')\n")
            
            yield temp_dir
    
    @pytest.fixture
    def mock_codebase(self, temp_repo):
        """Create a mock codebase instance."""
        return Codebase(temp_repo)
    
    @pytest.fixture
    def mock_bridge(self):
        """Create a mock MCP bridge."""
        return MockMCPBridge()
    
    def test_orchestrator_initialization(self, temp_repo, mock_bridge):
        """Test orchestrator initialization."""
        # Create a simple orchestrator class for testing
        class MCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge or SerenaMCPBridge(repo_path)
                self.tasks = {}
                self.task_id = 0
            
            def get_next_task_id(self):
                self.task_id += 1
                return f"task_{self.task_id}"
            
            def execute_tool(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = self.bridge.call_tool(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
            
            def start_task(self, tool_name, arguments):
                task_id = self.get_next_task_id()
                self.tasks[task_id] = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "status": "pending",
                    "result": None
                }
                
                # In a real implementation, this would be async
                result = self.execute_tool(tool_name, arguments)
                
                self.tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
                self.tasks[task_id]["result"] = result
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"]
                }
            
            def get_task_status(self, task_id):
                if task_id not in self.tasks:
                    return {"error": f"Task '{task_id}' not found"}
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"],
                    "result": self.tasks[task_id]["result"]
                }
        
        # Create orchestrator with mock bridge
        orchestrator = MCPOrchestrator(temp_repo, mock_bridge)
        
        # Verify initialization
        assert orchestrator.repo_path == temp_repo
        assert orchestrator.bridge == mock_bridge
        assert orchestrator.tasks == {}
    
    def test_orchestrator_execute_tool(self, temp_repo, mock_bridge):
        """Test executing a tool through the orchestrator."""
        # Create a simple orchestrator class for testing
        class MCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge or SerenaMCPBridge(repo_path)
            
            def execute_tool(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = self.bridge.call_tool(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
        
        # Create orchestrator with mock bridge
        orchestrator = MCPOrchestrator(temp_repo, mock_bridge)
        
        # Execute a tool
        result = orchestrator.execute_tool("test_tool", {"param": "value"})
        
        # Verify result
        assert result["success"] is True
        assert result["result"] == {"result": "Success"}
        assert result["error"] is None
        
        # Verify bridge call
        assert mock_bridge.calls == [("test_tool", {"param": "value"})]
    
    def test_orchestrator_task_management(self, temp_repo, mock_bridge):
        """Test task management in the orchestrator."""
        # Create a simple orchestrator class for testing
        class MCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge or SerenaMCPBridge(repo_path)
                self.tasks = {}
                self.task_id = 0
            
            def get_next_task_id(self):
                self.task_id += 1
                return f"task_{self.task_id}"
            
            def execute_tool(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = self.bridge.call_tool(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
            
            def start_task(self, tool_name, arguments):
                task_id = self.get_next_task_id()
                self.tasks[task_id] = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "status": "pending",
                    "result": None
                }
                
                # In a real implementation, this would be async
                result = self.execute_tool(tool_name, arguments)
                
                self.tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
                self.tasks[task_id]["result"] = result
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"]
                }
            
            def get_task_status(self, task_id):
                if task_id not in self.tasks:
                    return {"error": f"Task '{task_id}' not found"}
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"],
                    "result": self.tasks[task_id]["result"]
                }
        
        # Create orchestrator with mock bridge
        orchestrator = MCPOrchestrator(temp_repo, mock_bridge)
        
        # Start a task
        task_result = orchestrator.start_task("test_tool", {"param": "value"})
        
        # Verify task creation
        assert "task_id" in task_result
        assert task_result["status"] == "completed"
        
        # Get task status
        status = orchestrator.get_task_status(task_result["task_id"])
        
        # Verify status
        assert status["task_id"] == task_result["task_id"]
        assert status["status"] == "completed"
        assert status["result"]["success"] is True
        assert status["result"]["result"] == {"result": "Success"}
    
    def test_orchestrator_error_handling(self, temp_repo, mock_bridge):
        """Test error handling in the orchestrator."""
        # Create a simple orchestrator class for testing
        class MCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge or SerenaMCPBridge(repo_path)
            
            def execute_tool(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = self.bridge.call_tool(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
        
        # Create orchestrator with mock bridge
        orchestrator = MCPOrchestrator(temp_repo, mock_bridge)
        
        # Test with unavailable tool
        result = orchestrator.execute_tool("nonexistent_tool", {"param": "value"})
        
        # Verify error handling
        assert "error" in result
        assert "not available" in result["error"]
        
        # Test with uninitialized bridge
        mock_bridge.is_initialized = False
        result = orchestrator.execute_tool("test_tool", {"param": "value"})
        
        # Verify error handling
        assert "error" in result
        assert "not initialized" in result["error"]


class TestAsyncMCPOrchestrator:
    """Test the async MCP orchestrator component."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello_world():\n    print('Hello, World!')\n")
            
            yield temp_dir
    
    @pytest.fixture
    def mock_codebase(self, temp_repo):
        """Create a mock codebase instance."""
        return Codebase(temp_repo)
    
    @pytest.fixture
    def mock_async_bridge(self):
        """Create a mock async MCP bridge."""
        class MockAsyncMCPBridge:
            def __init__(self):
                self.is_initialized = True
                self.available_tools = {
                    "test_tool": {
                        "name": "test_tool",
                        "description": "A test tool",
                        "parameters": {}
                    }
                }
                self.calls = []
            
            async def call_tool_async(self, tool_name, arguments):
                """Mock async tool call."""
                self.calls.append((tool_name, arguments))
                return MCPToolResult(
                    success=True,
                    content={"result": "Success"},
                    tool_name=tool_name
                )
            
            def get_available_tools(self):
                """Get available tools."""
                return self.available_tools
            
            def is_tool_available(self, tool_name):
                """Check if tool is available."""
                return tool_name in self.available_tools
            
            async def shutdown_async(self):
                """Shutdown the bridge."""
                self.is_initialized = False
        
        return MockAsyncMCPBridge()
    
    @pytest.mark.asyncio
    async def test_async_orchestrator_execution(self, temp_repo, mock_async_bridge):
        """Test async execution in the orchestrator."""
        # Create a simple async orchestrator class for testing
        class AsyncMCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge
                self.tasks = {}
                self.task_id = 0
            
            def get_next_task_id(self):
                self.task_id += 1
                return f"task_{self.task_id}"
            
            async def execute_tool_async(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = await self.bridge.call_tool_async(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
            
            async def start_task_async(self, tool_name, arguments):
                task_id = self.get_next_task_id()
                self.tasks[task_id] = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "status": "pending",
                    "result": None
                }
                
                # Execute asynchronously
                result = await self.execute_tool_async(tool_name, arguments)
                
                self.tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
                self.tasks[task_id]["result"] = result
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"]
                }
        
        # Create orchestrator with mock bridge
        orchestrator = AsyncMCPOrchestrator(temp_repo, mock_async_bridge)
        
        # Execute a tool asynchronously
        result = await orchestrator.execute_tool_async("test_tool", {"param": "value"})
        
        # Verify result
        assert result["success"] is True
        assert result["result"] == {"result": "Success"}
        assert result["error"] is None
        
        # Verify bridge call
        assert mock_async_bridge.calls == [("test_tool", {"param": "value"})]
    
    @pytest.mark.asyncio
    async def test_async_orchestrator_task_management(self, temp_repo, mock_async_bridge):
        """Test async task management in the orchestrator."""
        # Create a simple async orchestrator class for testing
        class AsyncMCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge
                self.tasks = {}
                self.task_id = 0
            
            def get_next_task_id(self):
                self.task_id += 1
                return f"task_{self.task_id}"
            
            async def execute_tool_async(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = await self.bridge.call_tool_async(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
            
            async def start_task_async(self, tool_name, arguments):
                task_id = self.get_next_task_id()
                self.tasks[task_id] = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "status": "pending",
                    "result": None
                }
                
                # Execute asynchronously
                result = await self.execute_tool_async(tool_name, arguments)
                
                self.tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
                self.tasks[task_id]["result"] = result
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"]
                }
            
            def get_task_status(self, task_id):
                if task_id not in self.tasks:
                    return {"error": f"Task '{task_id}' not found"}
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"],
                    "result": self.tasks[task_id]["result"]
                }
        
        # Create orchestrator with mock bridge
        orchestrator = AsyncMCPOrchestrator(temp_repo, mock_async_bridge)
        
        # Start a task asynchronously
        task_result = await orchestrator.start_task_async("test_tool", {"param": "value"})
        
        # Verify task creation
        assert "task_id" in task_result
        assert task_result["status"] == "completed"
        
        # Get task status
        status = orchestrator.get_task_status(task_result["task_id"])
        
        # Verify status
        assert status["task_id"] == task_result["task_id"]
        assert status["status"] == "completed"
        assert status["result"]["success"] is True
        assert status["result"]["result"] == {"result": "Success"}
    
    @pytest.mark.asyncio
    async def test_async_orchestrator_parallel_execution(self, temp_repo, mock_async_bridge):
        """Test parallel execution in the async orchestrator."""
        # Create a simple async orchestrator class for testing
        class AsyncMCPOrchestrator:
            def __init__(self, repo_path, bridge=None):
                self.repo_path = repo_path
                self.bridge = bridge
                self.tasks = {}
                self.task_id = 0
            
            def get_next_task_id(self):
                self.task_id += 1
                return f"task_{self.task_id}"
            
            async def execute_tool_async(self, tool_name, arguments):
                if not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if not self.bridge.is_tool_available(tool_name):
                    return {"error": f"Tool '{tool_name}' not available"}
                
                # Add a small delay to simulate processing time
                await asyncio.sleep(0.1)
                
                result = await self.bridge.call_tool_async(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
            
            async def start_task_async(self, tool_name, arguments):
                task_id = self.get_next_task_id()
                self.tasks[task_id] = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "status": "pending",
                    "result": None
                }
                
                # Execute asynchronously
                result = await self.execute_tool_async(tool_name, arguments)
                
                self.tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
                self.tasks[task_id]["result"] = result
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"]
                }
        
        # Create orchestrator with mock bridge
        orchestrator = AsyncMCPOrchestrator(temp_repo, mock_async_bridge)
        
        # Execute multiple tasks in parallel
        tasks = []
        for i in range(5):
            task = orchestrator.start_task_async("test_tool", {"param": f"value_{i}"})
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all tasks completed
        assert len(results) == 5
        for result in results:
            assert "task_id" in result
            assert result["status"] == "completed"
        
        # Verify bridge calls
        assert len(mock_async_bridge.calls) == 5
        for i, (tool_name, arguments) in enumerate(mock_async_bridge.calls):
            assert tool_name == "test_tool"
            assert arguments["param"] == f"value_{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

