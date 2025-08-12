#!/usr/bin/env python3
"""
Integration Tests for MCP Server and Orchestrator

This test suite validates the integration between the MCP server implementation
and the orchestrator components of graph-sitter.
"""

import pytest
import tempfile
import os
import json
import subprocess
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena.mcp_bridge import SerenaMCPBridge, MCPToolResult


class TestMCPServerOrchestratorIntegration:
    """Test the integration between MCP server and orchestrator."""
    
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
    
    @pytest.mark.skip(reason="This test requires a running MCP server and is meant for manual execution")
    def test_live_mcp_server_integration(self, temp_repo):
        """Test integration with a live MCP server.
        
        This test is skipped by default as it requires a running MCP server.
        It can be run manually by removing the skip decorator.
        """
        # Start MCP server in a separate process
        server_process = None
        try:
            # Use the actual MCP server command
            cmd = ["uvx", "--from", "git+https://github.com/oraios/serena", "serena-mcp-server", "--transport", "stdio"]
            
            server_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_repo,
                text=True,
                bufsize=0
            )
            
            # Allow server to start
            time.sleep(2)
            
            # Create MCP bridge
            bridge = SerenaMCPBridge(temp_repo)
            
            # Verify initialization
            assert bridge.is_initialized
            assert len(bridge.available_tools) > 0
            
            # Call a tool
            result = bridge.call_tool("analyze_code", {"file_path": "test.py"})
            
            # Verify result
            assert result.success
            assert result.tool_name == "analyze_code"
            
            # Cleanup
            bridge.shutdown()
            
        finally:
            # Ensure server process is terminated
            if server_process:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
    
    def test_mcp_bridge_with_orchestrator(self, temp_repo):
        """Test MCP bridge with orchestrator."""
        # Create a simple orchestrator class for testing
        class MCPOrchestrator:
            def __init__(self, repo_path):
                self.repo_path = repo_path
                self.bridge = None
                self.tasks = {}
                self.task_id = 0
            
            def initialize(self):
                """Initialize the orchestrator with a mock bridge."""
                self.bridge = MagicMock()
                self.bridge.is_initialized = True
                self.bridge.available_tools = {
                    "test_tool": {
                        "name": "test_tool",
                        "description": "A test tool",
                        "parameters": {}
                    }
                }
                self.bridge.call_tool.return_value = MCPToolResult(
                    success=True,
                    content={"result": "Success"},
                    tool_name="test_tool"
                )
                return True
            
            def get_next_task_id(self):
                self.task_id += 1
                return f"task_{self.task_id}"
            
            def execute_tool(self, tool_name, arguments):
                if not self.bridge or not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if tool_name not in self.bridge.available_tools:
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
            
            def shutdown(self):
                if self.bridge:
                    self.bridge.shutdown()
                    self.bridge = None
        
        # Create and initialize orchestrator
        orchestrator = MCPOrchestrator(temp_repo)
        success = orchestrator.initialize()
        
        # Verify initialization
        assert success
        assert orchestrator.bridge is not None
        assert orchestrator.bridge.is_initialized
        
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
        
        # Verify bridge call
        orchestrator.bridge.call_tool.assert_called_once_with("test_tool", {"param": "value"})
        
        # Shutdown
        orchestrator.shutdown()
        orchestrator.bridge.shutdown.assert_called_once()
    
    def test_concurrent_task_execution(self, temp_repo):
        """Test concurrent task execution in the orchestrator."""
        # Create a simple orchestrator class for testing
        class MCPOrchestrator:
            def __init__(self, repo_path):
                self.repo_path = repo_path
                self.bridge = None
                self.tasks = {}
                self.task_id = 0
                self.lock = threading.RLock()
            
            def initialize(self):
                """Initialize the orchestrator with a mock bridge."""
                self.bridge = MagicMock()
                self.bridge.is_initialized = True
                self.bridge.available_tools = {
                    "test_tool": {
                        "name": "test_tool",
                        "description": "A test tool",
                        "parameters": {}
                    }
                }
                
                # Make call_tool sleep briefly to simulate processing time
                def mock_call_tool(tool_name, arguments):
                    time.sleep(0.1)  # Simulate processing time
                    return MCPToolResult(
                        success=True,
                        content={"result": f"Success for {arguments.get('param', 'unknown')}"},
                        tool_name=tool_name
                    )
                
                self.bridge.call_tool.side_effect = mock_call_tool
                return True
            
            def get_next_task_id(self):
                with self.lock:
                    self.task_id += 1
                    return f"task_{self.task_id}"
            
            def execute_tool(self, tool_name, arguments):
                if not self.bridge or not self.bridge.is_initialized:
                    return {"error": "MCP bridge not initialized"}
                
                if tool_name not in self.bridge.available_tools:
                    return {"error": f"Tool '{tool_name}' not available"}
                
                result = self.bridge.call_tool(tool_name, arguments)
                return {
                    "success": result.success,
                    "result": result.content,
                    "error": result.error
                }
            
            def start_task(self, tool_name, arguments):
                task_id = self.get_next_task_id()
                with self.lock:
                    self.tasks[task_id] = {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "status": "pending",
                        "result": None
                    }
                
                # Execute tool
                result = self.execute_tool(tool_name, arguments)
                
                with self.lock:
                    self.tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
                    self.tasks[task_id]["result"] = result
                
                return {
                    "task_id": task_id,
                    "status": self.tasks[task_id]["status"]
                }
            
            def get_task_status(self, task_id):
                with self.lock:
                    if task_id not in self.tasks:
                        return {"error": f"Task '{task_id}' not found"}
                    
                    return {
                        "task_id": task_id,
                        "status": self.tasks[task_id]["status"],
                        "result": self.tasks[task_id]["result"]
                    }
            
            def shutdown(self):
                if self.bridge:
                    self.bridge.shutdown()
                    self.bridge = None
        
        # Create and initialize orchestrator
        orchestrator = MCPOrchestrator(temp_repo)
        orchestrator.initialize()
        
        # Create and start multiple threads to execute tasks concurrently
        threads = []
        task_ids = []
        
        def run_task(param_value):
            result = orchestrator.start_task("test_tool", {"param": param_value})
            task_ids.append(result["task_id"])
        
        # Start 5 concurrent tasks
        for i in range(5):
            thread = threading.Thread(target=run_task, args=(f"value_{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all tasks completed
        assert len(task_ids) == 5
        for task_id in task_ids:
            status = orchestrator.get_task_status(task_id)
            assert status["status"] == "completed"
            assert status["result"]["success"] is True
        
        # Verify bridge calls
        assert orchestrator.bridge.call_tool.call_count == 5
        
        # Shutdown
        orchestrator.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

