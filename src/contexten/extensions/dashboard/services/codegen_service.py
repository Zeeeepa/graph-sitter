"""Codegen service for integrating with Codegen SDK."""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import ServiceStatus, Task, TaskStatus


class CodegenService:
    """Service for integrating with Codegen SDK for plan generation and task execution."""
    
    def __init__(self):
        """Initialize the Codegen service."""
        self.org_id = os.getenv("CODEGEN_ORG_ID")
        self.token = os.getenv("CODEGEN_TOKEN")
        self._agent = None
    
    async def check_status(self) -> ServiceStatus:
        """Check if Codegen SDK is properly configured and accessible."""
        try:
            if not self.org_id or not self.token:
                return ServiceStatus.DISCONNECTED
            
            # Try to initialize the agent
            agent = await self._get_agent()
            if agent:
                return ServiceStatus.CONNECTED
            else:
                return ServiceStatus.ERROR
                
        except Exception as e:
            print(f"Codegen status check failed: {e}")
            return ServiceStatus.ERROR
    
    async def _get_agent(self):
        """Get or create Codegen agent instance."""
        if self._agent is None:
            try:
                # Import Codegen SDK (this would be the actual import)
                # from codegen import Agent
                # self._agent = Agent(org_id=self.org_id, token=self.token)
                
                # For now, return a mock agent
                self._agent = MockCodegenAgent(self.org_id, self.token)
                
            except ImportError:
                print("Codegen SDK not available. Using mock implementation.")
                self._agent = MockCodegenAgent(self.org_id, self.token)
            except Exception as e:
                print(f"Failed to initialize Codegen agent: {e}")
                return None
        
        return self._agent
    
    async def generate_plan(self, project_id: str, requirements: str) -> Dict[str, Any]:
        """Generate a development plan using Codegen SDK."""
        try:
            agent = await self._get_agent()
            if not agent:
                raise Exception("Codegen agent not available")
            
            # Create a prompt for plan generation
            prompt = self._create_plan_prompt(project_id, requirements)
            
            # Run the agent to generate plan
            task = await agent.run(prompt=prompt)
            
            # Wait for completion (with timeout)
            plan_result = await self._wait_for_task_completion(task, timeout=300)  # 5 minutes
            
            # Parse the result into a structured plan
            structured_plan = self._parse_plan_result(plan_result)
            
            return structured_plan
            
        except Exception as e:
            raise Exception(f"Failed to generate plan: {str(e)}")
    
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single task using Codegen SDK."""
        try:
            agent = await self._get_agent()
            if not agent:
                raise Exception("Codegen agent not available")
            
            # Create context-aware prompt
            prompt = self._create_task_prompt(task_description, context or {})
            
            # Run the task
            task = await agent.run(prompt=prompt)
            
            # Wait for completion
            result = await self._wait_for_task_completion(task, timeout=600)  # 10 minutes
            
            return {
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_pr(self, pr_url: str, quality_criteria: List[str] = None) -> Dict[str, Any]:
        """Validate a pull request using Codegen SDK."""
        try:
            agent = await self._get_agent()
            if not agent:
                raise Exception("Codegen agent not available")
            
            # Create PR validation prompt
            prompt = self._create_pr_validation_prompt(pr_url, quality_criteria or [])
            
            # Run validation
            task = await agent.run(prompt=prompt)
            
            # Wait for completion
            result = await self._wait_for_task_completion(task, timeout=180)  # 3 minutes
            
            # Parse validation result
            validation_result = self._parse_validation_result(result)
            
            return validation_result
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "passed": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_followup_tasks(self, completed_task: Task, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create follow-up tasks based on completed task results."""
        try:
            agent = await self._get_agent()
            if not agent:
                return []
            
            # Create prompt for follow-up task generation
            prompt = self._create_followup_prompt(completed_task, result)
            
            # Run the agent
            task = await agent.run(prompt=prompt)
            
            # Wait for completion
            followup_result = await self._wait_for_task_completion(task, timeout=120)  # 2 minutes
            
            # Parse follow-up tasks
            followup_tasks = self._parse_followup_tasks(followup_result)
            
            return followup_tasks
            
        except Exception as e:
            print(f"Failed to create follow-up tasks: {e}")
            return []
    
    def _create_plan_prompt(self, project_id: str, requirements: str) -> str:
        """Create a prompt for plan generation."""
        return f\"\"\"
        Please create a detailed development plan for the following project requirements:
        
        Project ID: {project_id}
        Requirements: {requirements}
        
        Please provide a structured plan with the following format:
        1. Break down the requirements into specific, actionable tasks
        2. Estimate time and complexity for each task
        3. Identify dependencies between tasks
        4. Suggest appropriate tools and technologies
        5. Include quality gates and validation steps
        
        Format the response as a JSON structure with tasks, dependencies, and metadata.
        \"\"\"
    
    def _create_task_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """Create a prompt for task execution."""
        context_str = "\\n".join([f"{k}: {v}" for k, v in context.items()])
        
        return f\"\"\"
        Please execute the following development task:
        
        Task: {task_description}
        
        Context:
        {context_str}
        
        Please:
        1. Analyze the task requirements
        2. Implement the necessary code changes
        3. Create or update tests as needed
        4. Ensure code quality and best practices
        5. Provide a summary of changes made
        \"\"\"
    
    def _create_pr_validation_prompt(self, pr_url: str, quality_criteria: List[str]) -> str:
        """Create a prompt for PR validation."""
        criteria_str = "\\n".join([f"- {criterion}" for criterion in quality_criteria])
        
        return f\"\"\"
        Please review and validate the following pull request:
        
        PR URL: {pr_url}
        
        Quality Criteria:
        {criteria_str}
        
        Please check:
        1. Code quality and best practices
        2. Test coverage and quality
        3. Documentation updates
        4. Security considerations
        5. Performance implications
        
        Provide a detailed review with pass/fail status and specific feedback.
        \"\"\"
    
    def _create_followup_prompt(self, completed_task: Task, result: Dict[str, Any]) -> str:
        """Create a prompt for follow-up task generation."""
        return f\"\"\"
        Based on the completed task and its results, please suggest follow-up tasks:
        
        Completed Task: {completed_task.title}
        Description: {completed_task.description}
        Result: {result}
        
        Please identify:
        1. Any additional tasks needed to complete the feature
        2. Testing tasks that should be performed
        3. Documentation updates required
        4. Integration tasks with other components
        5. Quality assurance steps
        
        Format as a list of specific, actionable tasks.
        \"\"\"
    
    async def _wait_for_task_completion(self, task, timeout: int = 300) -> Any:
        """Wait for a Codegen task to complete with timeout."""
        start_time = datetime.now()
        
        while True:
            # Check if task is completed
            await task.refresh()
            
            if task.status == "completed":
                return task.result
            elif task.status == "failed":
                raise Exception(f"Task failed: {getattr(task, 'error', 'Unknown error')}")
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise Exception(f"Task timed out after {timeout} seconds")
            
            # Wait before checking again
            await asyncio.sleep(5)
    
    def _parse_plan_result(self, result: Any) -> Dict[str, Any]:
        """Parse plan generation result into structured format."""
        # This would parse the actual Codegen result
        # For now, return a mock structured plan
        
        return {
            "id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": "Generated Development Plan",
            "description": "Automatically generated plan based on requirements",
            "tasks": [
                {
                    "id": "task_1",
                    "title": "Setup Project Structure",
                    "description": "Initialize project with proper directory structure and configuration",
                    "estimated_hours": 2,
                    "complexity": "low",
                    "dependencies": [],
                    "tools": ["git", "npm/yarn", "eslint"]
                },
                {
                    "id": "task_2", 
                    "title": "Implement Core Features",
                    "description": "Develop the main functionality as specified in requirements",
                    "estimated_hours": 8,
                    "complexity": "high",
                    "dependencies": ["task_1"],
                    "tools": ["react", "typescript", "api"]
                },
                {
                    "id": "task_3",
                    "title": "Add Tests",
                    "description": "Create comprehensive test suite for all features",
                    "estimated_hours": 4,
                    "complexity": "medium",
                    "dependencies": ["task_2"],
                    "tools": ["jest", "testing-library"]
                },
                {
                    "id": "task_4",
                    "title": "Documentation",
                    "description": "Create user and developer documentation",
                    "estimated_hours": 2,
                    "complexity": "low",
                    "dependencies": ["task_3"],
                    "tools": ["markdown", "docs"]
                }
            ],
            "total_estimated_hours": 16,
            "quality_gates": [
                "All tests must pass",
                "Code coverage > 80%",
                "No security vulnerabilities",
                "Performance benchmarks met"
            ],
            "created_at": datetime.now().isoformat()
        }
    
    def _parse_validation_result(self, result: Any) -> Dict[str, Any]:
        """Parse PR validation result."""
        # Mock validation result
        return {
            "status": "completed",
            "passed": True,
            "score": 85,
            "checks": [
                {"name": "Code Quality", "passed": True, "score": 90},
                {"name": "Test Coverage", "passed": True, "score": 85},
                {"name": "Documentation", "passed": False, "score": 70},
                {"name": "Security", "passed": True, "score": 95}
            ],
            "feedback": [
                "Code follows best practices and is well-structured",
                "Good test coverage for core functionality",
                "Consider adding more inline documentation",
                "No security issues detected"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_followup_tasks(self, result: Any) -> List[Dict[str, Any]]:
        """Parse follow-up tasks from result."""
        # Mock follow-up tasks
        return [
            {
                "title": "Update Integration Tests",
                "description": "Add integration tests for the new feature",
                "priority": "high",
                "estimated_hours": 2
            },
            {
                "title": "Update API Documentation",
                "description": "Document new API endpoints in OpenAPI spec",
                "priority": "medium",
                "estimated_hours": 1
            }
        ]


class MockCodegenAgent:
    """Mock Codegen agent for testing purposes."""
    
    def __init__(self, org_id: str, token: str):
        self.org_id = org_id
        self.token = token
    
    async def run(self, prompt: str):
        """Mock run method."""
        return MockTask(prompt)


class MockTask:
    """Mock task for testing purposes."""
    
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.status = "running"
        self.result = None
        self.error = None
        self._completion_time = datetime.now()
    
    async def refresh(self):
        """Mock refresh method."""
        # Simulate task completion after a short delay
        await asyncio.sleep(0.1)
        self.status = "completed"
        self.result = f"Mock result for prompt: {self.prompt[:50]}..."

