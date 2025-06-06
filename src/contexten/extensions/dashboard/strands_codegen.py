"""
Strands Codegen Integration
Proper Codegen SDK integration with org_id and token
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio
import os

try:
    from codegen import Agent
    CODEGEN_SDK_AVAILABLE = True
except ImportError:
    CODEGEN_SDK_AVAILABLE = False
    Agent = None

logger = logging.getLogger(__name__)


class StrandsCodegenManager:
    """
    Codegen SDK integration for Strands ecosystem
    """
    
    def __init__(self, org_id: str = None, token: str = None):
        self.org_id = org_id or os.getenv('CODEGEN_ORG_ID')
        self.token = token or os.getenv('CODEGEN_TOKEN')
        self.agent = None
        self.active_tasks: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
        
    async def initialize(self) -> bool:
        """Initialize Codegen SDK agent"""
        try:
            if not self.org_id or not self.token:
                logger.error("Codegen org_id and token are required")
                self._initialize_mock()
                return False
            
            if CODEGEN_SDK_AVAILABLE:
                self.agent = Agent(org_id=self.org_id, token=self.token)
                logger.info("Codegen SDK agent initialized successfully")
                return True
            else:
                logger.warning("Codegen SDK not available, using mock implementation")
                self._initialize_mock()
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Codegen SDK agent: {e}")
            self._initialize_mock()
            return False
    
    def _initialize_mock(self):
        """Initialize mock Codegen agent for development"""
        self.agent = MockCodegenAgent(self.org_id, self.token)
        logger.info("Mock Codegen agent initialized")
    
    async def create_code_generation_task(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Create a code generation task"""
        try:
            task_id = f"codegen_task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            task_config = {
                'id': task_id,
                'prompt': prompt,
                'context': context or {},
                'status': 'created',
                'created_at': datetime.now().isoformat(),
                'type': 'code_generation'
            }
            
            self.active_tasks[task_id] = task_config
            
            logger.info(f"Created code generation task: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create code generation task: {e}")
            raise
    
    async def create_plan_creation_task(self, requirements: str, context: Dict[str, Any] = None) -> str:
        """Create a plan creation task"""
        try:
            task_id = f"plan_task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            task_config = {
                'id': task_id,
                'requirements': requirements,
                'context': context or {},
                'status': 'created',
                'created_at': datetime.now().isoformat(),
                'type': 'plan_creation'
            }
            
            self.active_tasks[task_id] = task_config
            
            logger.info(f"Created plan creation task: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create plan creation task: {e}")
            raise
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a Codegen task"""
        try:
            if task_id not in self.active_tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.active_tasks[task_id]
            task['status'] = 'running'
            task['started_at'] = datetime.now().isoformat()
            
            if self.agent and hasattr(self.agent, 'run'):
                # Execute using real Codegen SDK
                if task['type'] == 'code_generation':
                    prompt = task['prompt']
                    context_str = self._format_context(task['context'])
                    full_prompt = f"{prompt}\n\nContext:\n{context_str}" if context_str else prompt
                    
                    codegen_task = self.agent.run(prompt=full_prompt)
                    
                    # Start monitoring the task
                    asyncio.create_task(self._monitor_codegen_task(task_id, codegen_task))
                    
                elif task['type'] == 'plan_creation':
                    requirements = task['requirements']
                    context_str = self._format_context(task['context'])
                    plan_prompt = f"Create a detailed implementation plan for: {requirements}\n\nContext:\n{context_str}" if context_str else f"Create a detailed implementation plan for: {requirements}"
                    
                    codegen_task = self.agent.run(prompt=plan_prompt)
                    
                    # Start monitoring the task
                    asyncio.create_task(self._monitor_codegen_task(task_id, codegen_task))
                
                return {
                    'task_id': task_id,
                    'status': 'running',
                    'message': 'Task execution started'
                }
            else:
                # Mock execution
                asyncio.create_task(self._execute_mock_task(task_id))
                
                return {
                    'task_id': task_id,
                    'status': 'running',
                    'message': 'Mock task execution started'
                }
                
        except Exception as e:
            logger.error(f"Failed to execute task {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['status'] = 'failed'
                self.active_tasks[task_id]['error'] = str(e)
            raise
    
    async def _monitor_codegen_task(self, task_id: str, codegen_task):
        """Monitor a Codegen SDK task"""
        try:
            task = self.active_tasks[task_id]
            
            # Poll for task completion
            while True:
                try:
                    # Refresh task status
                    codegen_task.refresh()
                    
                    if codegen_task.status == "completed":
                        task['status'] = 'completed'
                        task['completed_at'] = datetime.now().isoformat()
                        task['result'] = codegen_task.result
                        
                        # Move to history
                        self.task_history.append(task.copy())
                        
                        logger.info(f"Codegen task {task_id} completed successfully")
                        break
                        
                    elif codegen_task.status == "failed":
                        task['status'] = 'failed'
                        task['failed_at'] = datetime.now().isoformat()
                        task['error'] = getattr(codegen_task, 'error', 'Unknown error')
                        
                        logger.error(f"Codegen task {task_id} failed: {task.get('error')}")
                        break
                    
                    # Update progress if available
                    if hasattr(codegen_task, 'progress'):
                        task['progress'] = codegen_task.progress
                    
                    await asyncio.sleep(5)  # Poll every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error monitoring Codegen task {task_id}: {e}")
                    task['status'] = 'failed'
                    task['error'] = f"Monitoring error: {e}"
                    break
            
        except Exception as e:
            logger.error(f"Failed to monitor Codegen task {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['status'] = 'failed'
                self.active_tasks[task_id]['error'] = str(e)
    
    async def _execute_mock_task(self, task_id: str):
        """Execute a mock Codegen task"""
        try:
            task = self.active_tasks[task_id]
            
            # Simulate task execution time
            await asyncio.sleep(3)
            
            if task['type'] == 'code_generation':
                result = {
                    'code': f"# Generated code for: {task['prompt']}\n\ndef example_function():\n    return 'Hello from generated code!'",
                    'files_created': ['example.py'],
                    'summary': f"Generated code based on prompt: {task['prompt'][:100]}...",
                    'pr_url': 'https://github.com/example/repo/pull/123'
                }
            elif task['type'] == 'plan_creation':
                result = {
                    'plan': {
                        'title': f"Implementation Plan for: {task['requirements'][:50]}...",
                        'steps': [
                            {'step': 1, 'description': 'Analyze requirements', 'estimated_time': '2 hours'},
                            {'step': 2, 'description': 'Design architecture', 'estimated_time': '4 hours'},
                            {'step': 3, 'description': 'Implement core functionality', 'estimated_time': '8 hours'},
                            {'step': 4, 'description': 'Add tests', 'estimated_time': '3 hours'},
                            {'step': 5, 'description': 'Documentation', 'estimated_time': '2 hours'}
                        ],
                        'total_estimated_time': '19 hours',
                        'technologies': ['Python', 'FastAPI', 'React'],
                        'dependencies': ['fastapi', 'uvicorn', 'react']
                    },
                    'summary': f"Created implementation plan for: {task['requirements'][:100]}..."
                }
            else:
                result = {
                    'message': f"Mock task completed: {task['type']}",
                    'task_id': task_id
                }
            
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            task['result'] = result
            
            # Move to history
            self.task_history.append(task.copy())
            
            logger.info(f"Mock Codegen task {task_id} completed")
            
        except Exception as e:
            logger.error(f"Failed to execute mock task {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['status'] = 'failed'
                self.active_tasks[task_id]['error'] = str(e)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt"""
        if not context:
            return ""
        
        formatted = []
        for key, value in context.items():
            formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        try:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]
            
            # Check history
            for task in self.task_history:
                if task['id'] == task_id:
                    return task
            
            raise ValueError(f"Task {task_id} not found")
            
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            raise
    
    async def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active tasks"""
        try:
            return list(self.active_tasks.values())
        except Exception as e:
            logger.error(f"Failed to list active tasks: {e}")
            return []
    
    async def list_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List task history"""
        try:
            return self.task_history[-limit:] if limit else self.task_history
        except Exception as e:
            logger.error(f"Failed to list task history: {e}")
            return []
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        try:
            if task_id not in self.active_tasks:
                return False
            
            task = self.active_tasks[task_id]
            
            if task['status'] in ['completed', 'failed', 'cancelled']:
                return False
            
            task['status'] = 'cancelled'
            task['cancelled_at'] = datetime.now().isoformat()
            
            logger.info(f"Cancelled Codegen task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        try:
            return {
                'org_id': self.org_id,
                'agent_type': 'codegen_sdk' if CODEGEN_SDK_AVAILABLE else 'mock',
                'active_tasks': len(self.active_tasks),
                'total_tasks': len(self.task_history) + len(self.active_tasks),
                'sdk_available': CODEGEN_SDK_AVAILABLE
            }
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return {'error': str(e)}


class MockCodegenAgent:
    """Mock Codegen agent for development"""
    
    def __init__(self, org_id: str, token: str):
        self.org_id = org_id
        self.token = token
    
    def run(self, prompt: str):
        """Mock run method"""
        return MockCodegenTask(prompt)


class MockCodegenTask:
    """Mock Codegen task for development"""
    
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.status = "running"
        self.result = None
        self.progress = 0
    
    def refresh(self):
        """Mock refresh method"""
        # Simulate progress
        if self.status == "running":
            self.progress += 20
            if self.progress >= 100:
                self.status = "completed"
                self.result = f"Mock result for prompt: {self.prompt}"

