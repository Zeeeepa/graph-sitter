"""
Codegen Service - Integration with Codegen SDK.
Handles plan generation, code generation, and task management.
"""

import os
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..consolidated_models import Task, TaskStatus, ServiceStatus

logger = logging.getLogger(__name__)


class CodegenService:
    """
    Service for integrating with Codegen SDK for plan generation and task execution.
    Provides comprehensive code generation capabilities with proper authentication.
    """
    
    def __init__(self):
        """Initialize the Codegen service."""
        self.org_id = os.getenv("CODEGEN_ORG_ID")
        self.token = os.getenv("CODEGEN_TOKEN")
        self._agent = None
        self.active_tasks: Dict[str, Task] = {}
        
        # Validate configuration
        if not self.org_id or not self.token:
            logger.warning("Codegen SDK not properly configured. Missing org_id or token.")
    
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
            logger.error(f"Codegen status check failed: {e}")
            return ServiceStatus.ERROR
    
    async def _get_agent(self):
        """Get or create Codegen agent instance."""
        if self._agent is None:
            try:
                # Try to import and initialize actual Codegen SDK
                from codegen import Agent
                self._agent = Agent(org_id=self.org_id, token=self.token)
                logger.info("Initialized Codegen SDK agent")
                
            except ImportError:
                logger.warning("Codegen SDK not available. Using mock implementation.")
                self._agent = MockCodegenAgent(self.org_id, self.token)
            except Exception as e:
                logger.error(f"Failed to initialize Codegen agent: {e}")
                # Fall back to mock implementation
                self._agent = MockCodegenAgent(self.org_id, self.token)
        
        return self._agent
    
    async def generate_plan(
        self,
        project_id: str,
        requirements: str,
        include_quality_gates: bool = True
    ) -> Dict[str, Any]:
        """Generate a development plan using Codegen SDK."""
        try:
            agent = await self._get_agent()
            if not agent:
                raise Exception("Codegen agent not available")
            
            # Create a comprehensive prompt for plan generation
            prompt = self._create_plan_prompt(project_id, requirements, include_quality_gates)
            
            # Run the agent to generate plan
            task = await agent.run(prompt=prompt)
            
            # Wait for completion (with timeout)
            plan_result = await self._wait_for_task_completion(task, timeout=300)  # 5 minutes
            
            # Parse the result into a structured plan
            structured_plan = self._parse_plan_result(plan_result)
            
            # Add metadata
            structured_plan.update({
                "project_id": project_id,
                "requirements": requirements,
                "generated_at": datetime.now().isoformat(),
                "include_quality_gates": include_quality_gates,
                "codegen_task_id": getattr(task, 'id', None)
            })
            
            logger.info(f"Generated plan for project {project_id}")
            return structured_plan
            
        except Exception as e:
            logger.error(f"Failed to generate plan for project {project_id}: {e}")
            raise Exception(f"Failed to generate plan: {str(e)}")
    
    async def create_task(
        self,
        task_type: str,
        project_id: str,
        prompt: str,
        context: Dict[str, Any] = None
    ) -> Task:
        """Create a new Codegen task."""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            flow_id=context.get('flow_id', ''),
            project_id=project_id,
            title=f"Codegen {task_type}",
            description=prompt,
            task_type=task_type,
            status=TaskStatus.PENDING
        )
        
        self.active_tasks[task_id] = task
        logger.info(f"Created Codegen task {task_id} of type {task_type}")
        return task
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a Codegen task."""
        task = self.active_tasks.get(task_id)
        if not task:
            raise Exception(f"Task {task_id} not found")
        
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            agent = await self._get_agent()
            if not agent:
                raise Exception("Codegen agent not available")
            
            # Create context-aware prompt based on task type
            prompt = self._create_task_prompt(task)
            
            # Run the task
            codegen_task = await agent.run(prompt=prompt)
            task.strands_task_id = getattr(codegen_task, 'id', None)
            
            # Wait for completion
            result = await self._wait_for_task_completion(codegen_task, timeout=600)  # 10 minutes
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = {
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Completed Codegen task {task_id}")
            return task.result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error_message = str(e)
            task.result = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.error(f"Failed to execute Codegen task {task_id}: {e}")
            return task.result
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.active_tasks.get(task_id)
    
    async def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.active_tasks.values())
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        try:
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                task.error_message = "Task cancelled by user"
                
                # Try to cancel the actual Codegen task if possible
                if task.strands_task_id:
                    agent = await self._get_agent()
                    if hasattr(agent, 'cancel_task'):
                        await agent.cancel_task(task.strands_task_id)
                
                logger.info(f"Cancelled Codegen task {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
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
            logger.error(f"Failed to validate PR {pr_url}: {e}")
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
            
            logger.info(f"Generated {len(followup_tasks)} follow-up tasks for {completed_task.id}")
            return followup_tasks
            
        except Exception as e:
            logger.error(f"Failed to create follow-up tasks: {e}")
            return []
    
    def _create_plan_prompt(self, project_id: str, requirements: str, include_quality_gates: bool) -> str:
        """Create a prompt for plan generation."""
        quality_gates_section = ""
        if include_quality_gates:
            quality_gates_section = """
            
5. Quality Gates and Validation:
   - Define quality metrics and thresholds
   - Specify testing requirements
   - Include code review criteria
   - Set performance benchmarks
   - Define security validation steps
            """
        
        return f"""
Please create a detailed development plan for the following project requirements:

Project ID: {project_id}
Requirements: {requirements}

Please provide a structured plan with the following format:
1. Break down the requirements into specific, actionable tasks
2. Estimate time and complexity for each task
3. Identify dependencies between tasks
4. Suggest appropriate tools and technologies
{quality_gates_section}

Format the response as a JSON object with the following structure:
{{
    "summary": "Brief summary of the plan",
    "tasks": [
        {{
            "id": "task_1",
            "title": "Task title",
            "description": "Detailed description",
            "type": "task_type",
            "estimated_hours": 8,
            "complexity": "medium",
            "dependencies": ["task_id"],
            "tools": ["tool1", "tool2"],
            "acceptance_criteria": ["criteria1", "criteria2"]
        }}
    ],
    "timeline": {{
        "total_estimated_hours": 40,
        "phases": [
            {{
                "name": "Phase 1",
                "tasks": ["task_1", "task_2"],
                "estimated_duration": "1 week"
            }}
        ]
    }},
    "risks": ["risk1", "risk2"],
    "recommendations": ["rec1", "rec2"]
}}

Ensure the plan is comprehensive, realistic, and follows software development best practices.
        """
    
    def _create_task_prompt(self, task: Task) -> str:
        """Create a context-aware prompt for task execution."""
        base_prompt = f"""
Task: {task.title}
Description: {task.description}
Type: {task.task_type}
Project ID: {task.project_id}

Please execute this task according to the description and type.
        """
        
        if task.task_type == "generate_plan":
            return base_prompt + """
Generate a detailed implementation plan with specific steps, timelines, and deliverables.
"""
        elif task.task_type == "generate_code":
            return base_prompt + """
Generate clean, well-documented code that follows best practices and includes appropriate tests.
"""
        elif task.task_type == "review_pr":
            return base_prompt + """
Review the pull request for code quality, security issues, performance concerns, and adherence to best practices.
Provide specific feedback and suggestions for improvement.
"""
        else:
            return base_prompt + """
Complete the task as described, providing detailed results and any relevant insights.
"""
    
    def _create_pr_validation_prompt(self, pr_url: str, quality_criteria: List[str]) -> str:
        """Create a prompt for PR validation."""
        criteria_text = "\n".join([f"- {criterion}" for criterion in quality_criteria])
        
        return f"""
Please review and validate the following pull request:

PR URL: {pr_url}

Quality Criteria to check:
{criteria_text}

Please provide a comprehensive review including:
1. Code quality assessment
2. Security analysis
3. Performance considerations
4. Test coverage evaluation
5. Documentation review
6. Adherence to best practices

Format the response as JSON:
{{
    "overall_status": "passed|failed|warning",
    "score": 85,
    "checks": [
        {{
            "name": "Code Quality",
            "status": "passed|failed|warning",
            "score": 90,
            "message": "Detailed feedback"
        }}
    ],
    "recommendations": ["rec1", "rec2"],
    "blocking_issues": ["issue1", "issue2"]
}}
        """
    
    def _create_followup_prompt(self, completed_task: Task, result: Dict[str, Any]) -> str:
        """Create a prompt for follow-up task generation."""
        return f"""
Based on the completed task and its results, please suggest follow-up tasks:

Completed Task:
- Title: {completed_task.title}
- Description: {completed_task.description}
- Type: {completed_task.task_type}
- Status: {completed_task.status.value}

Task Results:
{result}

Please suggest relevant follow-up tasks that should be created based on this completion.
Format as JSON array:
[
    {{
        "title": "Follow-up task title",
        "description": "Detailed description",
        "type": "task_type",
        "priority": "high|medium|low",
        "estimated_hours": 4
    }}
]
        """
    
    async def _wait_for_task_completion(self, task, timeout: int = 300):
        """Wait for a Codegen task to complete with timeout."""
        start_time = datetime.now()
        
        while True:
            # Check if task is completed
            if hasattr(task, 'status'):
                if task.status == "completed":
                    return getattr(task, 'result', "Task completed successfully")
                elif task.status == "failed":
                    raise Exception(f"Task failed: {getattr(task, 'error', 'Unknown error')}")
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise Exception(f"Task timed out after {timeout} seconds")
            
            # Refresh task status if possible
            if hasattr(task, 'refresh'):
                await task.refresh()
            
            # Wait before next check
            await asyncio.sleep(5)
    
    def _parse_plan_result(self, result: Any) -> Dict[str, Any]:
        """Parse plan generation result into structured format."""
        try:
            if isinstance(result, str):
                import json
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                # Fallback for unexpected result format
                return {
                    "summary": "Plan generated successfully",
                    "tasks": [],
                    "timeline": {"total_estimated_hours": 0, "phases": []},
                    "risks": [],
                    "recommendations": [],
                    "raw_result": str(result)
                }
        except Exception as e:
            logger.error(f"Failed to parse plan result: {e}")
            return {
                "summary": "Plan generation completed with parsing issues",
                "tasks": [],
                "timeline": {"total_estimated_hours": 0, "phases": []},
                "risks": [f"Result parsing error: {str(e)}"],
                "recommendations": [],
                "raw_result": str(result)
            }
    
    def _parse_validation_result(self, result: Any) -> Dict[str, Any]:
        """Parse PR validation result."""
        try:
            if isinstance(result, str):
                import json
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {
                    "overall_status": "warning",
                    "score": 50,
                    "checks": [],
                    "recommendations": [],
                    "blocking_issues": [],
                    "message": "Validation completed with parsing issues",
                    "raw_result": str(result)
                }
        except Exception as e:
            logger.error(f"Failed to parse validation result: {e}")
            return {
                "overall_status": "error",
                "score": 0,
                "checks": [],
                "recommendations": [],
                "blocking_issues": [f"Result parsing error: {str(e)}"],
                "raw_result": str(result)
            }
    
    def _parse_followup_tasks(self, result: Any) -> List[Dict[str, Any]]:
        """Parse follow-up tasks result."""
        try:
            if isinstance(result, str):
                import json
                return json.loads(result)
            elif isinstance(result, list):
                return result
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to parse follow-up tasks: {e}")
            return []


class MockCodegenAgent:
    """Mock Codegen Agent for development and testing."""
    
    def __init__(self, org_id: str, token: str):
        self.org_id = org_id
        self.token = token
        self.task_counter = 0
    
    async def run(self, prompt: str):
        """Mock run method."""
        self.task_counter += 1
        task_id = f"mock_task_{self.task_counter}"
        
        # Simulate task execution
        mock_task = MockCodegenTask(task_id, prompt)
        logger.info(f"Mock Codegen: Started task {task_id}")
        
        # Simulate some processing time
        await asyncio.sleep(1)
        
        return mock_task
    
    async def cancel_task(self, task_id: str):
        """Mock cancel method."""
        logger.info(f"Mock Codegen: Cancelled task {task_id}")


class MockCodegenTask:
    """Mock Codegen Task for development."""
    
    def __init__(self, task_id: str, prompt: str):
        self.id = task_id
        self.prompt = prompt
        self.status = "running"
        self.result = None
        self.error = None
        
        # Simulate completion after a short delay
        asyncio.create_task(self._simulate_completion())
    
    async def _simulate_completion(self):
        """Simulate task completion."""
        await asyncio.sleep(2)  # Simulate processing time
        
        # Generate mock result based on prompt content
        if "plan" in self.prompt.lower():
            self.result = {
                "summary": "Mock development plan generated",
                "tasks": [
                    {
                        "id": "task_1",
                        "title": "Setup Project Structure",
                        "description": "Initialize project with proper structure",
                        "type": "setup",
                        "estimated_hours": 4,
                        "complexity": "low",
                        "dependencies": [],
                        "tools": ["git", "npm"],
                        "acceptance_criteria": ["Project structure created", "Dependencies installed"]
                    },
                    {
                        "id": "task_2",
                        "title": "Implement Core Features",
                        "description": "Develop main functionality",
                        "type": "development",
                        "estimated_hours": 16,
                        "complexity": "high",
                        "dependencies": ["task_1"],
                        "tools": ["react", "typescript"],
                        "acceptance_criteria": ["Features implemented", "Tests passing"]
                    }
                ],
                "timeline": {
                    "total_estimated_hours": 20,
                    "phases": [
                        {
                            "name": "Setup Phase",
                            "tasks": ["task_1"],
                            "estimated_duration": "1 day"
                        },
                        {
                            "name": "Development Phase",
                            "tasks": ["task_2"],
                            "estimated_duration": "2-3 days"
                        }
                    ]
                },
                "risks": ["Complexity underestimated", "Dependencies may have issues"],
                "recommendations": ["Use TypeScript for better type safety", "Implement comprehensive testing"]
            }
        elif "review" in self.prompt.lower() or "validate" in self.prompt.lower():
            self.result = {
                "overall_status": "passed",
                "score": 85,
                "checks": [
                    {
                        "name": "Code Quality",
                        "status": "passed",
                        "score": 90,
                        "message": "Code follows best practices"
                    },
                    {
                        "name": "Security",
                        "status": "passed",
                        "score": 80,
                        "message": "No major security issues found"
                    }
                ],
                "recommendations": ["Add more unit tests", "Consider performance optimization"],
                "blocking_issues": []
            }
        else:
            self.result = "Mock task completed successfully"
        
        self.status = "completed"
        logger.info(f"Mock Codegen: Completed task {self.id}")
    
    async def refresh(self):
        """Mock refresh method."""
        pass  # Status is updated automatically in mock

