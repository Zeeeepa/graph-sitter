"""
Linear Workflow Automation

Comprehensive workflow automation system that:
- Creates tasks from Linear issues
- Integrates with Codegen SDK for task execution
- Provides real-time progress tracking
- Syncs status back to Linear
- Manages task lifecycle
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
import asyncio
import uuid

from .config import LinearIntegrationConfig
from .types import (
    LinearIssue, AssignmentEvent, WorkflowTask, TaskStatus, TaskProgress,
    ComponentStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class TaskTemplate:
    """Template for creating tasks from issues"""
    name: str
    description: str
    prompt_template: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    estimated_duration: int = 3600  # seconds
    priority: int = 0


@dataclass
class WorkflowStats:
    """Workflow automation statistics"""
    tasks_created: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_cancelled: int = 0
    progress_updates_sent: int = 0
    status_syncs_performed: int = 0
    last_task_created: Optional[datetime] = None
    last_progress_update: Optional[datetime] = None
    last_error: Optional[str] = None


class WorkflowAutomation:
    """Comprehensive workflow automation for Linear integration"""
    
    def __init__(self, config: LinearIntegrationConfig):
        self.config = config
        self.workflow_config = config.workflow
        
        # Task management
        self.active_tasks: Dict[str, WorkflowTask] = {}  # issue_id -> task
        self.task_templates: Dict[str, TaskTemplate] = {}
        
        # Codegen SDK integration
        self.codegen_agent = None
        self.linear_client = None
        
        # Progress tracking
        self.progress_callbacks: Dict[str, Callable[[str, TaskProgress], Awaitable[None]]] = {}
        
        # Statistics
        self.stats = ComponentStats()
        self.workflow_stats = WorkflowStats()
        self.start_time = datetime.now()
        
        # Background tasks
        self.progress_update_task: Optional[asyncio.Task] = None
        self.status_sync_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Initialize default task templates
        self._initialize_default_templates()
        
        logger.info("Workflow automation initialized")
    
    def set_linear_client(self, linear_client) -> None:
        """Set the Linear client for API operations"""
        self.linear_client = linear_client
        logger.info("Linear client set for workflow automation")
    
    def set_codegen_agent(self, codegen_agent) -> None:
        """Set the Codegen agent for task execution"""
        self.codegen_agent = codegen_agent
        logger.info("Codegen agent set for workflow automation")
    
    def _initialize_default_templates(self) -> None:
        """Initialize default task templates"""
        
        # Code generation template
        code_gen_template = TaskTemplate(
            name="code_generation",
            description="Generate code based on issue requirements",
            prompt_template="""
            Generate code for the following requirement:
            
            Title: {title}
            Description: {description}
            
            Requirements:
            {requirements}
            
            Please provide a complete implementation with:
            1. Well-documented code
            2. Error handling
            3. Unit tests
            4. Usage examples
            """,
            required_fields=["title", "description"],
            optional_fields=["requirements", "language", "framework"],
            estimated_duration=1800  # 30 minutes
        )
        
        # Bug fix template
        bug_fix_template = TaskTemplate(
            name="bug_fix",
            description="Fix bugs based on issue description",
            prompt_template="""
            Fix the following bug:
            
            Title: {title}
            Description: {description}
            
            Bug Details:
            {bug_details}
            
            Steps to Reproduce:
            {steps_to_reproduce}
            
            Expected Behavior:
            {expected_behavior}
            
            Please provide:
            1. Root cause analysis
            2. Fix implementation
            3. Test cases to prevent regression
            4. Documentation updates if needed
            """,
            required_fields=["title", "description"],
            optional_fields=["bug_details", "steps_to_reproduce", "expected_behavior"],
            estimated_duration=2400  # 40 minutes
        )
        
        # Feature implementation template
        feature_template = TaskTemplate(
            name="feature_implementation",
            description="Implement new features based on specifications",
            prompt_template="""
            Implement the following feature:
            
            Title: {title}
            Description: {description}
            
            Feature Specifications:
            {specifications}
            
            Acceptance Criteria:
            {acceptance_criteria}
            
            Please provide:
            1. Feature implementation
            2. Integration with existing code
            3. Comprehensive tests
            4. Documentation
            5. Migration scripts if needed
            """,
            required_fields=["title", "description"],
            optional_fields=["specifications", "acceptance_criteria", "dependencies"],
            estimated_duration=3600  # 60 minutes
        )
        
        # Code review template
        review_template = TaskTemplate(
            name="code_review",
            description="Perform code review based on issue context",
            prompt_template="""
            Perform a code review for:
            
            Title: {title}
            Description: {description}
            
            Code to Review:
            {code_content}
            
            Review Focus Areas:
            {focus_areas}
            
            Please provide:
            1. Code quality assessment
            2. Security analysis
            3. Performance considerations
            4. Best practices recommendations
            5. Suggested improvements
            """,
            required_fields=["title", "description", "code_content"],
            optional_fields=["focus_areas", "coding_standards"],
            estimated_duration=1200  # 20 minutes
        )
        
        self.task_templates = {
            "code_generation": code_gen_template,
            "bug_fix": bug_fix_template,
            "feature_implementation": feature_template,
            "code_review": review_template
        }
        
        logger.info(f"Initialized {len(self.task_templates)} default task templates")
    
    def _determine_task_type(self, issue: LinearIssue) -> str:
        """Determine the appropriate task type for an issue"""
        title = issue.title.lower()
        description = (issue.description or "").lower()
        content = f"{title} {description}"
        
        # Check labels first
        if issue.labels:
            label_names = [label.name.lower() for label in issue.labels]
            
            if any(label in ["bug", "fix", "error", "issue"] for label in label_names):
                return "bug_fix"
            elif any(label in ["feature", "enhancement", "new"] for label in label_names):
                return "feature_implementation"
            elif any(label in ["review", "audit", "check"] for label in label_names):
                return "code_review"
        
        # Check content keywords
        if any(keyword in content for keyword in ["bug", "fix", "error", "broken", "issue"]):
            return "bug_fix"
        elif any(keyword in content for keyword in ["feature", "implement", "add", "create", "new"]):
            return "feature_implementation"
        elif any(keyword in content for keyword in ["review", "audit", "check", "analyze"]):
            return "code_review"
        
        # Default to code generation
        return "code_generation"
    
    def _extract_task_parameters(self, issue: LinearIssue, task_type: str) -> Dict[str, Any]:
        """Extract parameters for task creation from issue"""
        template = self.task_templates.get(task_type)
        if not template:
            return {}
        
        parameters = {
            "title": issue.title,
            "description": issue.description or "",
            "issue_id": issue.id,
            "issue_url": issue.url or "",
            "priority": issue.priority or 0,
            "estimate": issue.estimate or 0
        }
        
        # Extract additional parameters from description
        description = issue.description or ""
        
        # Look for structured information in description
        if "requirements:" in description.lower():
            requirements_section = self._extract_section(description, "requirements")
            if requirements_section:
                parameters["requirements"] = requirements_section
        
        if "acceptance criteria:" in description.lower():
            criteria_section = self._extract_section(description, "acceptance criteria")
            if criteria_section:
                parameters["acceptance_criteria"] = criteria_section
        
        if "steps to reproduce:" in description.lower():
            steps_section = self._extract_section(description, "steps to reproduce")
            if steps_section:
                parameters["steps_to_reproduce"] = steps_section
        
        if "expected behavior:" in description.lower():
            expected_section = self._extract_section(description, "expected behavior")
            if expected_section:
                parameters["expected_behavior"] = expected_section
        
        return parameters
    
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a specific section from text"""
        import re
        
        pattern = rf"{re.escape(section_name)}:\s*(.*?)(?=\n\w+:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    async def handle_assignment(self, assignment_event: AssignmentEvent) -> bool:
        """Handle a bot assignment event"""
        try:
            if assignment_event.action != AssignmentEvent.ASSIGNED:
                logger.debug(f"Ignoring non-assignment event: {assignment_event.action}")
                return True
            
            issue_id = assignment_event.issue_id
            
            # Check if task already exists
            if issue_id in self.active_tasks:
                logger.info(f"Task already exists for issue {issue_id}")
                return True
            
            # Get issue details
            if not self.linear_client:
                logger.error("Linear client not set, cannot get issue details")
                return False
            
            issue = await self.linear_client.get_issue(issue_id)
            if not issue:
                logger.error(f"Could not get issue details for {issue_id}")
                return False
            
            # Create task from issue
            task = await self.create_task_from_issue(issue)
            if not task:
                logger.error(f"Failed to create task for issue {issue_id}")
                return False
            
            # Start task if auto-start is enabled
            if self.workflow_config.auto_start_tasks:
                success = await self.start_task(task.id)
                if not success:
                    logger.error(f"Failed to start task {task.id}")
                    return False
            
            logger.info(f"Successfully handled assignment for issue {issue_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling assignment: {e}")
            self.workflow_stats.last_error = str(e)
            return False
    
    async def create_task_from_issue(self, issue: LinearIssue) -> Optional[WorkflowTask]:
        """Create a workflow task from a Linear issue"""
        try:
            # Determine task type
            task_type = self._determine_task_type(issue)
            template = self.task_templates.get(task_type)
            
            if not template:
                logger.error(f"No template found for task type: {task_type}")
                return None
            
            # Extract parameters
            parameters = self._extract_task_parameters(issue, task_type)
            
            # Create task
            task_id = str(uuid.uuid4())
            
            progress = TaskProgress(
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                current_step="Task created",
                steps_completed=0,
                total_steps=5,  # Default steps: analyze, plan, implement, test, review
                started_at=None,
                completed_at=None,
                metadata={"task_type": task_type, "template": template.name}
            )
            
            task = WorkflowTask(
                id=task_id,
                issue_id=issue.id,
                title=issue.title,
                description=issue.description,
                status=TaskStatus.PENDING,
                progress=progress,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                assigned_to=self.config.bot.bot_user_id,
                metadata={
                    "task_type": task_type,
                    "template": template.name,
                    "parameters": parameters,
                    "estimated_duration": template.estimated_duration
                }
            )
            
            # Store task
            self.active_tasks[issue.id] = task
            
            # Update statistics
            self.workflow_stats.tasks_created += 1
            self.workflow_stats.last_task_created = datetime.now()
            
            # Send initial progress update
            if self.workflow_config.auto_update_status:
                await self._send_progress_update(task)
            
            logger.info(f"Created task {task_id} for issue {issue.id} (type: {task_type})")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from issue {issue.id}: {e}")
            self.workflow_stats.last_error = str(e)
            return None
    
    async def start_task(self, task_id: str) -> bool:
        """Start executing a task"""
        try:
            # Find task by ID
            task = None
            for t in self.active_tasks.values():
                if t.id == task_id:
                    task = t
                    break
            
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            if task.status != TaskStatus.PENDING:
                logger.warning(f"Task {task_id} is not in pending status: {task.status}")
                return False
            
            # Update task status
            task.status = TaskStatus.RUNNING
            task.progress.status = TaskStatus.RUNNING
            task.progress.started_at = datetime.now()
            task.progress.current_step = "Starting task execution"
            task.updated_at = datetime.now()
            
            # Send progress update
            await self._send_progress_update(task)
            
            # Execute task with Codegen SDK
            if self.codegen_agent:
                success = await self._execute_with_codegen(task)
            else:
                # Simulate task execution for now
                success = await self._simulate_task_execution(task)
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.progress.status = TaskStatus.COMPLETED
                task.progress.progress_percentage = 100.0
                task.progress.completed_at = datetime.now()
                task.progress.current_step = "Task completed successfully"
                self.workflow_stats.tasks_completed += 1
            else:
                task.status = TaskStatus.FAILED
                task.progress.status = TaskStatus.FAILED
                task.progress.error_message = "Task execution failed"
                task.progress.current_step = "Task failed"
                self.workflow_stats.tasks_failed += 1
            
            task.updated_at = datetime.now()
            
            # Send final progress update
            await self._send_progress_update(task)
            
            logger.info(f"Task {task_id} completed with status: {task.status}")
            return success
            
        except Exception as e:
            logger.error(f"Error starting task {task_id}: {e}")
            
            # Update task with error
            if task:
                task.status = TaskStatus.FAILED
                task.progress.status = TaskStatus.FAILED
                task.progress.error_message = str(e)
                task.updated_at = datetime.now()
                await self._send_progress_update(task)
            
            self.workflow_stats.last_error = str(e)
            return False
    
    async def _execute_with_codegen(self, task: WorkflowTask) -> bool:
        """Execute task using Codegen SDK"""
        try:
            if not self.codegen_agent:
                logger.error("Codegen agent not configured")
                return False
            
            # Get task template and parameters
            task_type = task.metadata.get("task_type")
            template = self.task_templates.get(task_type)
            parameters = task.metadata.get("parameters", {})
            
            if not template:
                logger.error(f"Template not found for task type: {task_type}")
                return False
            
            # Format prompt
            try:
                prompt = template.prompt_template.format(**parameters)
            except KeyError as e:
                logger.error(f"Missing parameter for prompt template: {e}")
                return False
            
            # Update progress
            task.progress.current_step = "Executing with Codegen SDK"
            task.progress.progress_percentage = 25.0
            await self._send_progress_update(task)
            
            # Execute with Codegen
            codegen_task = self.codegen_agent.run(prompt=prompt)
            
            # Monitor progress
            while codegen_task.status not in ["completed", "failed", "cancelled"]:
                await asyncio.sleep(5)
                codegen_task.refresh()
                
                # Update progress based on Codegen task status
                if codegen_task.status == "running":
                    task.progress.progress_percentage = min(75.0, task.progress.progress_percentage + 5.0)
                    task.progress.current_step = "Codegen task in progress"
                    await self._send_progress_update(task)
            
            # Check final status
            if codegen_task.status == "completed":
                task.progress.current_step = "Codegen task completed"
                task.progress.progress_percentage = 90.0
                task.metadata["codegen_result"] = codegen_task.result
                await self._send_progress_update(task)
                
                # Post results to Linear
                if self.linear_client and codegen_task.result:
                    await self._post_results_to_linear(task, codegen_task.result)
                
                return True
            else:
                task.progress.error_message = f"Codegen task failed: {codegen_task.status}"
                return False
            
        except Exception as e:
            logger.error(f"Error executing task with Codegen: {e}")
            task.progress.error_message = str(e)
            return False
    
    async def _simulate_task_execution(self, task: WorkflowTask) -> bool:
        """Simulate task execution for testing"""
        try:
            steps = [
                ("Analyzing requirements", 20.0),
                ("Planning implementation", 40.0),
                ("Implementing solution", 60.0),
                ("Running tests", 80.0),
                ("Finalizing results", 100.0)
            ]
            
            for step_name, progress in steps:
                task.progress.current_step = step_name
                task.progress.progress_percentage = progress
                task.progress.steps_completed += 1
                await self._send_progress_update(task)
                
                # Simulate work
                await asyncio.sleep(2)
            
            # Simulate posting results
            if self.linear_client:
                result_comment = f"""
                ✅ **Task Completed Successfully**
                
                **Task Type:** {task.metadata.get('task_type', 'Unknown')}
                **Duration:** {(datetime.now() - task.progress.started_at).total_seconds():.1f} seconds
                
                **Results:**
                - Analysis completed
                - Implementation provided
                - Tests included
                - Documentation updated
                
                This is a simulated result. In production, this would contain the actual Codegen output.
                """
                
                await self.linear_client.create_comment(task.issue_id, result_comment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error simulating task execution: {e}")
            return False
    
    async def _post_results_to_linear(self, task: WorkflowTask, result: str) -> None:
        """Post task results to Linear issue"""
        try:
            if not self.linear_client:
                return
            
            # Format result comment
            duration = (datetime.now() - task.progress.started_at).total_seconds()
            
            comment = f"""
            ✅ **Task Completed Successfully**
            
            **Task Type:** {task.metadata.get('task_type', 'Unknown')}
            **Duration:** {duration:.1f} seconds
            **Task ID:** {task.id}
            
            **Results:**
            {result}
            
            ---
            *Generated by Codegen Linear Integration*
            """
            
            await self.linear_client.create_comment(task.issue_id, comment)
            logger.info(f"Posted results to Linear issue {task.issue_id}")
            
        except Exception as e:
            logger.error(f"Error posting results to Linear: {e}")
    
    async def _send_progress_update(self, task: WorkflowTask) -> None:
        """Send progress update to Linear"""
        try:
            if not self.workflow_config.auto_update_status or not self.linear_client:
                return
            
            # Create progress comment
            progress_comment = f"""
            🔄 **Task Progress Update**
            
            **Status:** {task.progress.status.value.title()}
            **Progress:** {task.progress.progress_percentage:.1f}%
            **Current Step:** {task.progress.current_step}
            **Steps Completed:** {task.progress.steps_completed}/{task.progress.total_steps}
            
            {f"**Error:** {task.progress.error_message}" if task.progress.error_message else ""}
            
            ---
            *Task ID: {task.id}*
            """
            
            await self.linear_client.create_comment(task.issue_id, progress_comment)
            
            self.workflow_stats.progress_updates_sent += 1
            self.workflow_stats.last_progress_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")
    
    async def sync_progress(self, issue_id: str, progress_data: Dict[str, Any]) -> bool:
        """Sync external progress data with task"""
        try:
            task = self.active_tasks.get(issue_id)
            if not task:
                logger.warning(f"No active task found for issue {issue_id}")
                return False
            
            # Update task progress
            if "status" in progress_data:
                task.progress.status = TaskStatus(progress_data["status"])
                task.status = task.progress.status
            
            if "progress_percentage" in progress_data:
                task.progress.progress_percentage = progress_data["progress_percentage"]
            
            if "current_step" in progress_data:
                task.progress.current_step = progress_data["current_step"]
            
            if "error_message" in progress_data:
                task.progress.error_message = progress_data["error_message"]
            
            task.updated_at = datetime.now()
            
            # Send update to Linear
            await self._send_progress_update(task)
            
            self.workflow_stats.status_syncs_performed += 1
            return True
            
        except Exception as e:
            logger.error(f"Error syncing progress for issue {issue_id}: {e}")
            return False
    
    async def cancel_task(self, issue_id: str) -> bool:
        """Cancel an active task"""
        try:
            task = self.active_tasks.get(issue_id)
            if not task:
                logger.warning(f"No active task found for issue {issue_id}")
                return False
            
            task.status = TaskStatus.CANCELLED
            task.progress.status = TaskStatus.CANCELLED
            task.progress.current_step = "Task cancelled"
            task.updated_at = datetime.now()
            
            # Send cancellation update
            await self._send_progress_update(task)
            
            self.workflow_stats.tasks_cancelled += 1
            logger.info(f"Cancelled task for issue {issue_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task for issue {issue_id}: {e}")
            return False
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active tasks"""
        return {
            issue_id: {
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "progress": task.progress.progress_percentage,
                "current_step": task.progress.current_step,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "last_update": task.updated_at.isoformat()
            }
            for issue_id, task in self.active_tasks.items()
        }
    
    def get_stats(self) -> ComponentStats:
        """Get workflow automation statistics"""
        self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        self.stats.requests_made = self.workflow_stats.tasks_created
        self.stats.requests_successful = self.workflow_stats.tasks_completed
        self.stats.requests_failed = self.workflow_stats.tasks_failed
        self.stats.last_error = self.workflow_stats.last_error
        self.stats.last_request = self.workflow_stats.last_task_created
        
        return self.stats
    
    def get_workflow_stats(self) -> WorkflowStats:
        """Get detailed workflow statistics"""
        return self.workflow_stats
    
    async def start_background_tasks(self) -> None:
        """Start background monitoring tasks"""
        if self.is_running:
            logger.warning("Background tasks already running")
            return
        
        self.is_running = True
        
        # Start progress update task
        self.progress_update_task = asyncio.create_task(self._progress_update_loop())
        
        # Start status sync task
        self.status_sync_task = asyncio.create_task(self._status_sync_loop())
        
        logger.info("Started workflow automation background tasks")
    
    async def stop_background_tasks(self) -> None:
        """Stop background monitoring tasks"""
        if not self.is_running:
            logger.warning("Background tasks not running")
            return
        
        self.is_running = False
        
        # Cancel tasks
        if self.progress_update_task:
            self.progress_update_task.cancel()
            try:
                await self.progress_update_task
            except asyncio.CancelledError:
                pass
        
        if self.status_sync_task:
            self.status_sync_task.cancel()
            try:
                await self.status_sync_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped workflow automation background tasks")
    
    async def _progress_update_loop(self) -> None:
        """Background loop for sending progress updates"""
        while self.is_running:
            try:
                # Send progress updates for running tasks
                for task in self.active_tasks.values():
                    if task.status == TaskStatus.RUNNING:
                        await self._send_progress_update(task)
                
                await asyncio.sleep(self.workflow_config.progress_update_interval)
                
            except Exception as e:
                logger.error(f"Error in progress update loop: {e}")
                await asyncio.sleep(30)
    
    async def _status_sync_loop(self) -> None:
        """Background loop for syncing status with Linear"""
        while self.is_running:
            try:
                # Sync status for all active tasks
                for issue_id, task in self.active_tasks.items():
                    # Check if task has been updated recently
                    if (datetime.now() - task.updated_at).total_seconds() < self.workflow_config.status_sync_interval:
                        continue
                    
                    # Sync with Linear
                    # This would typically involve checking Linear for updates
                    # and updating local task status accordingly
                    pass
                
                await asyncio.sleep(self.workflow_config.status_sync_interval)
                
            except Exception as e:
                logger.error(f"Error in status sync loop: {e}")
                await asyncio.sleep(60)

