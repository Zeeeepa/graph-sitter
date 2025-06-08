"""Codegen Extension for Contexten.

This extension provides comprehensive Codegen SDK integration including:
- Automated planning
- Task execution
- Code generation
- Quality analysis
- Progress tracking
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from codegen import Agent

from ...core.extension import ServiceExtension, ExtensionMetadata
from ...core.events.bus import Event

logger = logging.getLogger(__name__)

class CodegenExtension(ServiceExtension):
    """Codegen SDK integration extension."""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self.codegen_agent: Optional[Agent] = None
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._completed_tasks: Dict[str, Dict[str, Any]] = {}

    @property
    def metadata(self) -> ExtensionMetadata:
        return ExtensionMetadata(
            name="codegen",
            version="1.0.0",
            description="Codegen SDK integration for automated planning and execution",
            author="Contexten",
            dependencies=[],
            required=False,
            config_schema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Codegen organization ID"},
                    "token": {"type": "string", "description": "Codegen API token"},
                    "base_url": {"type": "string", "description": "Codegen API base URL"},
                },
                "required": ["org_id", "token"]
            },
            tags={"integration", "automation", "ai"}
        )

    async def initialize(self) -> None:
        """Initialize Codegen agent and services."""
        org_id = self.config.get('org_id')
        token = self.config.get('token')
        
        if not org_id or not token:
            raise ValueError("Codegen org_id and token are required")

        # Initialize Codegen agent
        self.codegen_agent = Agent(org_id=org_id, token=token)

        # Register event handlers
        self.register_event_handler("project.plan", self._handle_plan_request)
        self.register_event_handler("task.execute", self._handle_task_execution)
        self.register_event_handler("code.analyze", self._handle_code_analysis)

        logger.info("Codegen extension initialized")

    async def start(self) -> None:
        """Start Codegen extension services."""
        # Verify Codegen connection
        try:
            # Test connection with a simple task
            test_task = self.codegen_agent.run(prompt="Test connection")
            logger.info(f"Connected to Codegen, test task: {test_task.id}")
        except Exception as e:
            logger.error(f"Failed to connect to Codegen: {e}")
            raise

        # Start background tasks
        asyncio.create_task(self._monitor_tasks())

    async def stop(self) -> None:
        """Stop Codegen extension services."""
        # Cancel any active tasks
        for task_id in list(self._active_tasks.keys()):
            try:
                await self._cancel_task(task_id)
            except Exception as e:
                logger.error(f"Failed to cancel task {task_id}: {e}")

        logger.info("Codegen extension stopped")

    async def generate_plan(
        self,
        project_name: str,
        repository: str,
        requirements: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a project plan using Codegen.
        
        Args:
            project_name: Name of the project
            repository: Repository URL or name
            requirements: Project requirements
            context: Optional additional context
            
        Returns:
            Generated plan information
        """
        try:
            # Construct planning prompt
            prompt = self._build_planning_prompt(
                project_name, repository, requirements, context
            )

            # Execute planning task
            task = self.codegen_agent.run(prompt=prompt)
            
            # Store task
            self._active_tasks[task.id] = {
                "type": "planning",
                "project_name": project_name,
                "repository": repository,
                "requirements": requirements,
                "created_at": datetime.utcnow().isoformat(),
                "status": task.status,
            }

            # Monitor task completion
            asyncio.create_task(self._monitor_task(task.id, task))

            # Publish event
            await self.app.event_bus.publish(Event(
                type="codegen.plan.started",
                source="codegen",
                data={
                    "task_id": task.id,
                    "project_name": project_name,
                    "repository": repository,
                }
            ))

            return {
                "task_id": task.id,
                "status": task.status,
                "project_name": project_name,
                "repository": repository,
            }

        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            raise

    async def execute_task(
        self,
        task_description: str,
        repository: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task using Codegen.
        
        Args:
            task_description: Description of the task
            repository: Repository URL or name
            context: Optional additional context
            
        Returns:
            Task execution information
        """
        try:
            # Construct execution prompt
            prompt = self._build_execution_prompt(task_description, repository, context)

            # Execute task
            task = self.codegen_agent.run(prompt=prompt)
            
            # Store task
            self._active_tasks[task.id] = {
                "type": "execution",
                "description": task_description,
                "repository": repository,
                "created_at": datetime.utcnow().isoformat(),
                "status": task.status,
            }

            # Monitor task completion
            asyncio.create_task(self._monitor_task(task.id, task))

            # Publish event
            await self.app.event_bus.publish(Event(
                type="codegen.task.started",
                source="codegen",
                data={
                    "task_id": task.id,
                    "description": task_description,
                    "repository": repository,
                }
            ))

            return {
                "task_id": task.id,
                "status": task.status,
                "description": task_description,
                "repository": repository,
            }

        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            raise

    async def analyze_code(
        self,
        repository: str,
        branch: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze code using Codegen.
        
        Args:
            repository: Repository URL or name
            branch: Optional branch to analyze
            files: Optional specific files to analyze
            
        Returns:
            Code analysis results
        """
        try:
            # Construct analysis prompt
            prompt = self._build_analysis_prompt(repository, branch, files)

            # Execute analysis task
            task = self.codegen_agent.run(prompt=prompt)
            
            # Store task
            self._active_tasks[task.id] = {
                "type": "analysis",
                "repository": repository,
                "branch": branch,
                "files": files,
                "created_at": datetime.utcnow().isoformat(),
                "status": task.status,
            }

            # Monitor task completion
            asyncio.create_task(self._monitor_task(task.id, task))

            # Publish event
            await self.app.event_bus.publish(Event(
                type="codegen.analysis.started",
                source="codegen",
                data={
                    "task_id": task.id,
                    "repository": repository,
                    "branch": branch,
                }
            ))

            return {
                "task_id": task.id,
                "status": task.status,
                "repository": repository,
                "branch": branch,
            }

        except Exception as e:
            logger.error(f"Failed to analyze code: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information
        """
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        elif task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        else:
            raise ValueError(f"Task {task_id} not found")

    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks.
        
        Returns:
            List of active task information
        """
        return list(self._active_tasks.values())

    async def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """Get all completed tasks.
        
        Returns:
            List of completed task information
        """
        return list(self._completed_tasks.values())

    async def _cancel_task(self, task_id: str) -> None:
        """Cancel a task.
        
        Args:
            task_id: Task ID to cancel
        """
        if task_id in self._active_tasks:
            task_info = self._active_tasks.pop(task_id)
            task_info["status"] = "cancelled"
            task_info["completed_at"] = datetime.utcnow().isoformat()
            self._completed_tasks[task_id] = task_info

    def _build_planning_prompt(
        self,
        project_name: str,
        repository: str,
        requirements: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build planning prompt for Codegen.
        
        Args:
            project_name: Project name
            repository: Repository URL
            requirements: Requirements text
            context: Optional context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""
        Generate a detailed project plan for: {project_name}
        Repository: {repository}
        
        Requirements:
        {requirements}
        
        Please create a comprehensive plan that includes:
        1. Task breakdown with clear descriptions
        2. Dependencies between tasks
        3. Estimated effort for each task
        4. Implementation approach
        5. Quality gates and validation steps
        6. Risk assessment and mitigation
        
        Format the response as a structured plan with actionable tasks.
        """
        
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"
        
        return prompt.strip()

    def _build_execution_prompt(
        self,
        task_description: str,
        repository: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build execution prompt for Codegen.
        
        Args:
            task_description: Task description
            repository: Repository URL
            context: Optional context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""
        Execute the following task:
        {task_description}
        
        Repository: {repository}
        
        Please:
        1. Analyze the current codebase
        2. Implement the required changes
        3. Ensure code quality and best practices
        4. Add appropriate tests
        5. Create a pull request with clear description
        6. Validate the implementation
        """
        
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"
        
        return prompt.strip()

    def _build_analysis_prompt(
        self,
        repository: str,
        branch: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> str:
        """Build analysis prompt for Codegen.
        
        Args:
            repository: Repository URL
            branch: Optional branch
            files: Optional file list
            
        Returns:
            Formatted prompt
        """
        prompt = f"""
        Analyze the codebase in repository: {repository}
        """
        
        if branch:
            prompt += f"\nBranch: {branch}"
        
        if files:
            prompt += f"\nFocus on files: {', '.join(files)}"
        
        prompt += """
        
        Please provide:
        1. Code quality assessment
        2. Potential issues and bugs
        3. Security vulnerabilities
        4. Performance bottlenecks
        5. Technical debt analysis
        6. Improvement recommendations
        7. Test coverage analysis
        
        Format the response as a structured analysis report.
        """
        
        return prompt.strip()

    async def _monitor_task(self, task_id: str, task) -> None:
        """Monitor a specific task for completion.
        
        Args:
            task_id: Task ID
            task: Codegen task object
        """
        try:
            while task.status not in ["completed", "failed", "cancelled"]:
                await asyncio.sleep(10)  # Check every 10 seconds
                task.refresh()
                
                if task_id in self._active_tasks:
                    self._active_tasks[task_id]["status"] = task.status

            # Task completed
            if task_id in self._active_tasks:
                task_info = self._active_tasks.pop(task_id)
                task_info["status"] = task.status
                task_info["completed_at"] = datetime.utcnow().isoformat()
                
                if task.status == "completed":
                    task_info["result"] = task.result
                
                self._completed_tasks[task_id] = task_info

                # Publish completion event
                await self.app.event_bus.publish(Event(
                    type=f"codegen.task.{task.status}",
                    source="codegen",
                    data={
                        "task_id": task_id,
                        "status": task.status,
                        "type": task_info["type"],
                    }
                ))

        except Exception as e:
            logger.error(f"Error monitoring task {task_id}: {e}")

    async def _monitor_tasks(self) -> None:
        """Background task to monitor all active tasks."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Clean up old completed tasks (keep last 100)
                if len(self._completed_tasks) > 100:
                    # Remove oldest tasks
                    sorted_tasks = sorted(
                        self._completed_tasks.items(),
                        key=lambda x: x[1].get("completed_at", "")
                    )
                    for task_id, _ in sorted_tasks[:-100]:
                        del self._completed_tasks[task_id]

            except Exception as e:
                logger.error(f"Task monitoring failed: {e}")

    async def _handle_plan_request(self, event_data: Dict[str, Any]) -> None:
        """Handle plan generation requests."""
        await self.generate_plan(
            project_name=event_data["project_name"],
            repository=event_data["repository"],
            requirements=event_data["requirements"],
            context=event_data.get("context")
        )

    async def _handle_task_execution(self, event_data: Dict[str, Any]) -> None:
        """Handle task execution requests."""
        await self.execute_task(
            task_description=event_data["description"],
            repository=event_data["repository"],
            context=event_data.get("context")
        )

    async def _handle_code_analysis(self, event_data: Dict[str, Any]) -> None:
        """Handle code analysis requests."""
        await self.analyze_code(
            repository=event_data["repository"],
            branch=event_data.get("branch"),
            files=event_data.get("files")
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check Codegen extension health."""
        try:
            return {
                "status": "healthy",
                "active_tasks": len(self._active_tasks),
                "completed_tasks": len(self._completed_tasks),
                "timestamp": self.app.current_time.isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
                "timestamp": self.app.current_time.isoformat(),
            }

