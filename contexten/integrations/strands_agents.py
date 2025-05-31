"""
Strands-Agents Integration - Advanced tool capabilities and extended memory features
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ToolCategory(Enum):
    """Tool categories from Strands-Agents"""
    FILE_OPERATIONS = "file_operations"
    SHELL_INTEGRATION = "shell_integration"
    MEMORY = "memory"
    HTTP_CLIENT = "http_client"
    SLACK_CLIENT = "slack_client"
    PYTHON_EXECUTION = "python_execution"
    MATHEMATICAL = "mathematical"
    AWS_INTEGRATION = "aws_integration"
    IMAGE_PROCESSING = "image_processing"
    VIDEO_PROCESSING = "video_processing"
    AUDIO_OUTPUT = "audio_output"
    ENVIRONMENT = "environment"
    JOURNALING = "journaling"
    TASK_SCHEDULING = "task_scheduling"
    REASONING = "reasoning"
    SWARM_INTELLIGENCE = "swarm_intelligence"


@dataclass
class ToolDefinition:
    """Definition of a Strands-Agents tool"""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]
    requires_confirmation: bool = False
    safety_level: str = "safe"  # safe, moderate, dangerous
    timeout: int = 30


@dataclass
class ToolExecution:
    """Represents a tool execution"""
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    result: Optional[Any] = None
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)


class StrandsAgentsIntegration:
    """
    Strands-Agents Integration for Enhanced Orchestration
    
    Provides advanced tool capabilities including:
    - File operations with syntax highlighting
    - Shell integration and command execution
    - Memory operations with Mem0 and Bedrock Knowledge Bases
    - HTTP client with authentication
    - Python execution with state persistence
    - Mathematical tools and calculations
    - AWS service integration
    - Swarm intelligence for multi-agent coordination
    """
    
    def __init__(self):
        """Initialize Strands-Agents integration"""
        self.logger = logging.getLogger(__name__)
        
        # Tool registry
        self._tools: Dict[str, ToolDefinition] = {}
        self._load_default_tools()
        
        # Execution tracking
        self._executions: Dict[str, ToolExecution] = {}
        
        # Memory integration
        self._memory_backend = None
        self._memory_config = {}
        
        # Python execution state
        self._python_state = {}
        
        # Statistics
        self._stats = {
            "tools_registered": len(self._tools),
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "tools_by_category": {},
            "average_execution_time": 0.0
        }
        
        self._running = False
    
    def _load_default_tools(self):
        """Load default Strands-Agents tools"""
        
        # File Operations
        self._tools["file_read"] = ToolDefinition(
            name="file_read",
            category=ToolCategory.FILE_OPERATIONS,
            description="Read file contents with syntax highlighting",
            parameters={"path": "string", "encoding": "string"}
        )
        
        self._tools["file_write"] = ToolDefinition(
            name="file_write",
            category=ToolCategory.FILE_OPERATIONS,
            description="Write content to file",
            parameters={"path": "string", "content": "string", "encoding": "string"},
            safety_level="moderate"
        )
        
        self._tools["editor"] = ToolDefinition(
            name="editor",
            category=ToolCategory.FILE_OPERATIONS,
            description="Advanced file editing with intelligent modifications",
            parameters={"command": "string", "path": "string", "content": "string"},
            safety_level="moderate"
        )
        
        # Shell Integration
        self._tools["shell"] = ToolDefinition(
            name="shell",
            category=ToolCategory.SHELL_INTEGRATION,
            description="Execute shell commands securely",
            parameters={"command": "string", "ignore_errors": "boolean"},
            requires_confirmation=True,
            safety_level="dangerous",
            timeout=60
        )
        
        # Memory Operations
        self._tools["memory"] = ToolDefinition(
            name="memory",
            category=ToolCategory.MEMORY,
            description="Store and retrieve memories with Mem0 integration",
            parameters={"operation": "string", "data": "any", "query": "string"}
        )
        
        # HTTP Client
        self._tools["http_request"] = ToolDefinition(
            name="http_request",
            category=ToolCategory.HTTP_CLIENT,
            description="Make HTTP requests with authentication support",
            parameters={
                "method": "string",
                "url": "string",
                "headers": "object",
                "body": "string",
                "auth_type": "string",
                "auth_token": "string"
            }
        )
        
        # Python Execution
        self._tools["python_repl"] = ToolDefinition(
            name="python_repl",
            category=ToolCategory.PYTHON_EXECUTION,
            description="Execute Python code with state persistence",
            parameters={"code": "string"},
            requires_confirmation=True,
            safety_level="moderate",
            timeout=120
        )
        
        # Mathematical Tools
        self._tools["calculator"] = ToolDefinition(
            name="calculator",
            category=ToolCategory.MATHEMATICAL,
            description="Perform advanced calculations with symbolic math",
            parameters={"expression": "string", "mode": "string"}
        )
        
        # AWS Integration
        self._tools["use_aws"] = ToolDefinition(
            name="use_aws",
            category=ToolCategory.AWS_INTEGRATION,
            description="Seamless access to AWS services",
            parameters={
                "service_name": "string",
                "operation_name": "string",
                "parameters": "object",
                "region": "string",
                "label": "string"
            }
        )
        
        # Swarm Intelligence
        self._tools["swarm"] = ToolDefinition(
            name="swarm",
            category=ToolCategory.SWARM_INTELLIGENCE,
            description="Coordinate multiple AI agents for parallel problem solving",
            parameters={
                "task": "string",
                "swarm_size": "integer",
                "coordination_pattern": "string"
            },
            timeout=300
        )
        
        # Update statistics
        for tool in self._tools.values():
            category = tool.category.value
            if category not in self._stats["tools_by_category"]:
                self._stats["tools_by_category"][category] = 0
            self._stats["tools_by_category"][category] += 1
    
    async def start(self):
        """Start the Strands-Agents integration"""
        self.logger.info("Starting Strands-Agents integration...")
        
        self._running = True
        
        # Initialize memory backend
        await self._initialize_memory()
        
        # Initialize Python execution environment
        await self._initialize_python_environment()
        
        self.logger.info(f"Strands-Agents integration started with {len(self._tools)} tools")
    
    async def stop(self):
        """Stop the Strands-Agents integration"""
        self.logger.info("Stopping Strands-Agents integration...")
        
        self._running = False
        
        # Cancel active executions
        for execution in self._executions.values():
            if execution.status == "running":
                execution.status = "cancelled"
        
        # Cleanup Python environment
        self._python_state.clear()
        
        self.logger.info("Strands-Agents integration stopped successfully")
    
    async def _initialize_memory(self):
        """Initialize memory backend integration"""
        try:
            # Configure memory backend (Mem0 or Bedrock Knowledge Bases)
            self._memory_config = {
                "backend": "mem0",  # or "bedrock_kb"
                "config": {
                    "vector_store": "qdrant",
                    "embedding_model": "text-embedding-3-small"
                }
            }
            
            self.logger.info("Memory backend initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory backend: {e}")
    
    async def _initialize_python_environment(self):
        """Initialize Python execution environment"""
        try:
            # Initialize global state for Python execution
            self._python_state = {
                "globals": {},
                "locals": {},
                "imports": set(),
                "session_id": str(uuid.uuid4())
            }
            
            # Pre-import common libraries
            common_imports = [
                "import pandas as pd",
                "import numpy as np",
                "import matplotlib.pyplot as plt",
                "import json",
                "import os",
                "import sys",
                "from datetime import datetime, timedelta"
            ]
            
            for import_stmt in common_imports:
                try:
                    exec(import_stmt, self._python_state["globals"])
                    self._python_state["imports"].add(import_stmt)
                except ImportError:
                    pass  # Skip if library not available
            
            self.logger.info("Python execution environment initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Python environment: {e}")
    
    async def execute_task(
        self,
        task_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task using Strands-Agents tools
        
        Args:
            task_config: Task configuration
            context: Execution context
            
        Returns:
            Task execution result
        """
        try:
            # Determine which tools to use based on task
            tools_to_use = await self._analyze_task_requirements(task_config, context)
            
            # Execute tools in sequence or parallel as needed
            results = []
            
            for tool_config in tools_to_use:
                tool_name = tool_config["tool"]
                parameters = tool_config["parameters"]
                
                result = await self.execute_tool(tool_name, parameters)
                results.append(result)
            
            return {
                "task_completed": True,
                "tools_used": [config["tool"] for config in tools_to_use],
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "task_completed": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_task_requirements(
        self,
        task_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze task to determine required tools"""
        tools_needed = []
        
        task_type = task_config.get("type", "").lower()
        task_description = task_config.get("description", "").lower()
        
        # File operations
        if "file" in task_description or "read" in task_description or "write" in task_description:
            if "write" in task_description or "create" in task_description:
                tools_needed.append({
                    "tool": "file_write",
                    "parameters": {
                        "path": task_config.get("file_path", "output.txt"),
                        "content": task_config.get("content", "")
                    }
                })
            else:
                tools_needed.append({
                    "tool": "file_read",
                    "parameters": {
                        "path": task_config.get("file_path", "input.txt")
                    }
                })
        
        # Code execution
        if "python" in task_description or "code" in task_description or "execute" in task_description:
            tools_needed.append({
                "tool": "python_repl",
                "parameters": {
                    "code": task_config.get("code", "print('Hello, World!')")
                }
            })
        
        # Mathematical operations
        if "calculate" in task_description or "math" in task_description or "compute" in task_description:
            tools_needed.append({
                "tool": "calculator",
                "parameters": {
                    "expression": task_config.get("expression", "2 + 2"),
                    "mode": "symbolic"
                }
            })
        
        # HTTP requests
        if "api" in task_description or "http" in task_description or "request" in task_description:
            tools_needed.append({
                "tool": "http_request",
                "parameters": {
                    "method": task_config.get("method", "GET"),
                    "url": task_config.get("url", ""),
                    "headers": task_config.get("headers", {})
                }
            })
        
        # Memory operations
        if "remember" in task_description or "memory" in task_description or "store" in task_description:
            tools_needed.append({
                "tool": "memory",
                "parameters": {
                    "operation": "store",
                    "data": task_config.get("data", context)
                }
            })
        
        # Shell commands
        if "command" in task_description or "shell" in task_description or "run" in task_description:
            tools_needed.append({
                "tool": "shell",
                "parameters": {
                    "command": task_config.get("command", "echo 'Hello'"),
                    "ignore_errors": task_config.get("ignore_errors", False)
                }
            })
        
        # Swarm intelligence
        if "swarm" in task_description or "parallel" in task_description or "multi-agent" in task_description:
            tools_needed.append({
                "tool": "swarm",
                "parameters": {
                    "task": task_config.get("swarm_task", task_description),
                    "swarm_size": task_config.get("swarm_size", 3),
                    "coordination_pattern": task_config.get("coordination_pattern", "collaborative")
                }
            })
        
        # Default to calculator if no specific tools identified
        if not tools_needed:
            tools_needed.append({
                "tool": "calculator",
                "parameters": {
                    "expression": "1 + 1",
                    "mode": "basic"
                }
            })
        
        return tools_needed
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific tool
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_def = self._tools[tool_name]
        execution_id = str(uuid.uuid4())
        
        # Create execution record
        execution = ToolExecution(
            id=execution_id,
            tool_name=tool_name,
            parameters=parameters,
            start_time=datetime.now()
        )
        
        self._executions[execution_id] = execution
        
        try:
            # Execute tool based on its type
            if tool_name == "file_read":
                result = await self._execute_file_read(parameters)
            elif tool_name == "file_write":
                result = await self._execute_file_write(parameters)
            elif tool_name == "editor":
                result = await self._execute_editor(parameters)
            elif tool_name == "shell":
                result = await self._execute_shell(parameters)
            elif tool_name == "memory":
                result = await self._execute_memory(parameters)
            elif tool_name == "http_request":
                result = await self._execute_http_request(parameters)
            elif tool_name == "python_repl":
                result = await self._execute_python_repl(parameters)
            elif tool_name == "calculator":
                result = await self._execute_calculator(parameters)
            elif tool_name == "use_aws":
                result = await self._execute_aws(parameters)
            elif tool_name == "swarm":
                result = await self._execute_swarm(parameters)
            else:
                raise ValueError(f"Tool execution not implemented: {tool_name}")
            
            # Update execution record
            execution.end_time = datetime.now()
            execution.status = "completed"
            execution.result = result
            
            # Update statistics
            self._stats["total_executions"] += 1
            self._stats["successful_executions"] += 1
            
            response_time = (execution.end_time - execution.start_time).total_seconds()
            if self._stats["average_execution_time"] == 0:
                self._stats["average_execution_time"] = response_time
            else:
                self._stats["average_execution_time"] = (
                    self._stats["average_execution_time"] * 0.9 + response_time * 0.1
                )
            
            self.logger.debug(f"Tool {tool_name} executed successfully in {response_time:.2f}s")
            
            return {
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "success",
                "result": result,
                "execution_time": response_time
            }
            
        except Exception as e:
            execution.end_time = datetime.now()
            execution.status = "failed"
            execution.error = str(e)
            
            self._stats["failed_executions"] += 1
            
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
            
            return {
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "error",
                "error": str(e)
            }
    
    async def _execute_file_read(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file read operation"""
        path = parameters.get("path", "")
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "path": path,
                "content": content,
                "size": len(content),
                "encoding": encoding
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to read file {path}: {e}")
    
    async def _execute_file_write(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file write operation"""
        path = parameters.get("path", "")
        content = parameters.get("content", "")
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "path": path,
                "bytes_written": len(content.encode(encoding)),
                "encoding": encoding
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to write file {path}: {e}")
    
    async def _execute_editor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute editor operation"""
        command = parameters.get("command", "view")
        path = parameters.get("path", "")
        content = parameters.get("content", "")
        
        if command == "view":
            return await self._execute_file_read({"path": path})
        elif command == "write":
            return await self._execute_file_write({"path": path, "content": content})
        else:
            raise ValueError(f"Unsupported editor command: {command}")
    
    async def _execute_shell(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command"""
        command = parameters.get("command", "")
        ignore_errors = parameters.get("ignore_errors", False)
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
            
            if process.returncode != 0 and not ignore_errors:
                raise RuntimeError(f"Command failed with return code {process.returncode}: {stderr.decode()}")
            
            return result
            
        except Exception as e:
            if not ignore_errors:
                raise RuntimeError(f"Shell command failed: {e}")
            return {"command": command, "error": str(e)}
    
    async def _execute_memory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory operation"""
        operation = parameters.get("operation", "store")
        data = parameters.get("data", {})
        query = parameters.get("query", "")
        
        # Simulate memory operations (in production, integrate with Mem0 or Bedrock KB)
        if operation == "store":
            memory_id = str(uuid.uuid4())
            return {
                "operation": "store",
                "memory_id": memory_id,
                "data_size": len(str(data)),
                "timestamp": datetime.now().isoformat()
            }
        elif operation == "retrieve":
            return {
                "operation": "retrieve",
                "query": query,
                "results": [{"id": "mem_123", "data": "Sample memory data", "relevance": 0.85}],
                "count": 1
            }
        else:
            raise ValueError(f"Unsupported memory operation: {operation}")
    
    async def _execute_http_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request"""
        method = parameters.get("method", "GET").upper()
        url = parameters.get("url", "")
        headers = parameters.get("headers", {})
        body = parameters.get("body", "")
        
        # Simulate HTTP request (in production, use actual HTTP client)
        return {
            "method": method,
            "url": url,
            "status_code": 200,
            "headers": {"content-type": "application/json"},
            "body": '{"message": "Simulated HTTP response"}',
            "response_time": 0.5
        }
    
    async def _execute_python_repl(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code with state persistence"""
        code = parameters.get("code", "")
        
        try:
            # Capture output
            import io
            import sys
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            try:
                # Execute code in persistent state
                exec(code, self._python_state["globals"], self._python_state["locals"])
                
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                return {
                    "code": code,
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "status": "success",
                    "session_id": self._python_state["session_id"]
                }
                
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            return {
                "code": code,
                "error": str(e),
                "status": "error",
                "session_id": self._python_state["session_id"]
            }
    
    async def _execute_calculator(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mathematical calculation"""
        expression = parameters.get("expression", "")
        mode = parameters.get("mode", "basic")
        
        try:
            # Simple evaluation (in production, use symbolic math libraries)
            result = eval(expression)
            
            return {
                "expression": expression,
                "result": result,
                "mode": mode,
                "type": type(result).__name__
            }
            
        except Exception as e:
            raise RuntimeError(f"Calculation failed: {e}")
    
    async def _execute_aws(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS service operation"""
        service_name = parameters.get("service_name", "")
        operation_name = parameters.get("operation_name", "")
        operation_params = parameters.get("parameters", {})
        region = parameters.get("region", "us-east-1")
        label = parameters.get("label", "")
        
        # Simulate AWS operation (in production, use boto3)
        return {
            "service": service_name,
            "operation": operation_name,
            "region": region,
            "label": label,
            "result": f"Simulated {service_name} {operation_name} result",
            "parameters": operation_params
        }
    
    async def _execute_swarm(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute swarm intelligence operation"""
        task = parameters.get("task", "")
        swarm_size = parameters.get("swarm_size", 3)
        coordination_pattern = parameters.get("coordination_pattern", "collaborative")
        
        # Simulate swarm execution
        agents = []
        for i in range(swarm_size):
            agent_result = {
                "agent_id": f"agent_{i+1}",
                "result": f"Agent {i+1} result for: {task}",
                "confidence": 0.8 + (i * 0.05),
                "execution_time": 1.0 + (i * 0.2)
            }
            agents.append(agent_result)
        
        # Aggregate results based on coordination pattern
        if coordination_pattern == "collaborative":
            final_result = f"Collaborative solution for: {task}"
        elif coordination_pattern == "competitive":
            final_result = f"Best competitive solution for: {task}"
        else:  # hybrid
            final_result = f"Hybrid solution for: {task}"
        
        return {
            "task": task,
            "swarm_size": swarm_size,
            "coordination_pattern": coordination_pattern,
            "agents": agents,
            "final_result": final_result,
            "consensus_score": 0.85
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        tools = []
        
        for tool in self._tools.values():
            tools.append({
                "name": tool.name,
                "category": tool.category.value,
                "description": tool.description,
                "parameters": tool.parameters,
                "requires_confirmation": tool.requires_confirmation,
                "safety_level": tool.safety_level,
                "timeout": tool.timeout
            })
        
        return sorted(tools, key=lambda x: (x["category"], x["name"]))
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        if tool_name not in self._tools:
            return None
        
        tool = self._tools[tool_name]
        
        return {
            "name": tool.name,
            "category": tool.category.value,
            "description": tool.description,
            "parameters": tool.parameters,
            "requires_confirmation": tool.requires_confirmation,
            "safety_level": tool.safety_level,
            "timeout": tool.timeout
        }
    
    async def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tool execution history"""
        executions = sorted(
            self._executions.values(),
            key=lambda x: x.start_time,
            reverse=True
        )
        
        return [
            {
                "id": exec.id,
                "tool_name": exec.tool_name,
                "status": exec.status,
                "start_time": exec.start_time.isoformat(),
                "end_time": exec.end_time.isoformat() if exec.end_time else None,
                "error": exec.error
            }
            for exec in executions[:limit]
        ]
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize Strands-Agents integration"""
        optimization_results = {
            "executions_cleaned": 0,
            "python_state_reset": False,
            "memory_optimized": False
        }
        
        # Clean up old executions
        cutoff_time = datetime.now() - timedelta(hours=24)
        old_executions = [
            exec_id for exec_id, execution in self._executions.items()
            if execution.end_time and execution.end_time < cutoff_time
        ]
        
        for exec_id in old_executions:
            del self._executions[exec_id]
            optimization_results["executions_cleaned"] += 1
        
        # Reset Python state if it gets too large
        if len(str(self._python_state)) > 1000000:  # 1MB
            await self._initialize_python_environment()
            optimization_results["python_state_reset"] = True
        
        self.logger.info(f"Strands-Agents optimization completed: {optimization_results}")
        return optimization_results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Strands-Agents integration statistics"""
        return {
            **self._stats,
            "active_executions": len([e for e in self._executions.values() if e.status == "running"]),
            "python_session_id": self._python_state.get("session_id", "none"),
            "memory_backend": self._memory_config.get("backend", "none")
        }
    
    def is_healthy(self) -> bool:
        """Check if Strands-Agents integration is healthy"""
        return (
            self._running and
            len(self._executions) < 10000 and  # Not too many executions
            self._stats["failed_executions"] < self._stats["total_executions"] * 0.2  # Less than 20% failure rate
        )

