"""
Codegen SDK Integration

Provides integration with the Codegen SDK for AI agent interactions,
enabling automated development tasks and intelligent code operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core.task import Task, TaskType, TaskStatus
from .base import IntegrationBase, IntegrationConfig, TaskHandler


logger = logging.getLogger(__name__)


class CodegenIntegration(IntegrationBase):
    """
    Integration with the Codegen SDK for AI-powered development tasks.
    
    Provides capabilities for:
    - Code generation and modification
    - PR creation and management
    - Issue tracking and resolution
    - Automated code reviews
    """
    
    def __init__(self, config: IntegrationConfig, org_id: str, token: str):
        """
        Initialize the Codegen integration.
        
        Args:
            config: Integration configuration
            org_id: Codegen organization ID
            token: Codegen API token
        """
        super().__init__(config)
        self.org_id = org_id
        self.token = token
        self._agent = None
        
    async def connect(self) -> bool:
        """Establish connection to Codegen SDK."""
        try:
            # Import Codegen SDK (assuming it's available)
            from codegen import Agent
            
            self._agent = Agent(org_id=self.org_id, token=self.token)
            
            # Test connection with a simple operation
            await self._test_connection()
            
            logger.info("Successfully connected to Codegen SDK")
            return True
            
        except ImportError:
            logger.error("Codegen SDK not available - please install the codegen package")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Codegen SDK: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Codegen SDK."""
        self._agent = None
        logger.info("Disconnected from Codegen SDK")
    
    async def health_check(self) -> bool:
        """Perform health check on Codegen connection."""
        if not self._agent:
            return False
        
        try:
            # Simple health check - could be expanded
            return True
        except Exception as e:
            logger.warning(f"Codegen health check failed: {e}")
            return False
    
    async def execute_task(self, task: Task) -> Any:
        """Execute a task using Codegen SDK."""
        if not self._agent:
            raise RuntimeError("Codegen agent not initialized")
        
        # Extract task configuration
        prompt = task.input_data.get("prompt", "")
        if not prompt:
            raise ValueError("Codegen tasks require a 'prompt' in input_data")
        
        # Additional configuration
        context = task.input_data.get("context", {})
        files = task.input_data.get("files", [])
        repo_url = task.input_data.get("repo_url", "")
        
        try:
            # Execute the task with Codegen
            codegen_task = self._agent.run(
                prompt=prompt,
                context=context,
                files=files,
                repo_url=repo_url
            )
            
            # Wait for completion with timeout
            timeout = task.timeout.total_seconds() if task.timeout else 3600
            result = await self._wait_for_completion(codegen_task, timeout)
            
            return result
            
        except Exception as e:
            logger.error(f"Codegen task execution failed: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test the Codegen connection."""
        # This would be a simple test operation
        # Implementation depends on Codegen SDK capabilities
        pass
    
    async def _wait_for_completion(self, codegen_task, timeout: float) -> Dict[str, Any]:
        """
        Wait for a Codegen task to complete.
        
        Args:
            codegen_task: The Codegen task object
            timeout: Maximum time to wait in seconds
            
        Returns:
            Task result data
        """
        start_time = datetime.utcnow()
        
        while True:
            # Check if timeout exceeded
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Codegen task timed out after {timeout} seconds")
            
            # Refresh task status
            codegen_task.refresh()
            
            if codegen_task.status == "completed":
                return {
                    "status": "completed",
                    "result": codegen_task.result,
                    "execution_time": elapsed,
                    "task_id": getattr(codegen_task, 'id', None),
                }
            elif codegen_task.status == "failed":
                error_info = getattr(codegen_task, 'error', 'Unknown error')
                raise RuntimeError(f"Codegen task failed: {error_info}")
            
            # Wait before next check
            await asyncio.sleep(5)


class CodegenTaskHandler(TaskHandler):
    """Task handler for Codegen-specific operations."""
    
    def __init__(self, integration: CodegenIntegration):
        """Initialize the Codegen task handler."""
        super().__init__(integration)
        self.supported_task_types = {
            TaskType.CODE_GENERATION,
            TaskType.CODE_REFACTORING,
            TaskType.CUSTOM,  # For custom Codegen operations
        }
    
    async def handle_task(self, task: Task) -> Any:
        """Handle execution of a Codegen task."""
        logger.info(f"Executing Codegen task {task.id}: {task.name}")
        
        # Validate required inputs
        if "prompt" not in task.input_data:
            raise ValueError("Codegen tasks require a 'prompt' in input_data")
        
        # Execute via integration
        result = await self.integration.execute_task(task)
        
        # Process and return result
        return self._process_result(task, result)
    
    def _process_result(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the result from Codegen execution."""
        processed_result = {
            "codegen_task_id": result.get("task_id"),
            "execution_time": result.get("execution_time"),
            "status": result.get("status"),
            "output": result.get("result"),
        }
        
        # Extract specific information based on task type
        if task.task_type == TaskType.CODE_GENERATION:
            processed_result["generated_code"] = self._extract_generated_code(result)
            processed_result["files_created"] = self._extract_created_files(result)
        
        elif task.task_type == TaskType.CODE_REFACTORING:
            processed_result["refactored_files"] = self._extract_refactored_files(result)
            processed_result["changes_summary"] = self._extract_changes_summary(result)
        
        return processed_result
    
    def _extract_generated_code(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract generated code from Codegen result."""
        # Implementation depends on Codegen result format
        output = result.get("result", {})
        
        if isinstance(output, dict) and "code" in output:
            return [{"content": output["code"], "language": output.get("language", "unknown")}]
        
        return []
    
    def _extract_created_files(self, result: Dict[str, Any]) -> List[str]:
        """Extract list of created files from Codegen result."""
        # Implementation depends on Codegen result format
        output = result.get("result", {})
        
        if isinstance(output, dict) and "files" in output:
            return output["files"]
        
        return []
    
    def _extract_refactored_files(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract refactored files information from Codegen result."""
        # Implementation depends on Codegen result format
        output = result.get("result", {})
        
        if isinstance(output, dict) and "changes" in output:
            return output["changes"]
        
        return []
    
    def _extract_changes_summary(self, result: Dict[str, Any]) -> str:
        """Extract summary of changes from Codegen result."""
        # Implementation depends on Codegen result format
        output = result.get("result", {})
        
        if isinstance(output, dict) and "summary" in output:
            return output["summary"]
        
        return "No summary available"
    
    def validate_task(self, task: Task) -> List[str]:
        """Validate Codegen-specific task configuration."""
        errors = super().validate_task(task)
        
        # Check for required prompt
        if "prompt" not in task.input_data:
            errors.append("Codegen tasks require a 'prompt' in input_data")
        
        # Validate prompt content
        prompt = task.input_data.get("prompt", "")
        if not prompt or not isinstance(prompt, str):
            errors.append("Prompt must be a non-empty string")
        
        # Check for optional but recommended fields
        if task.task_type == TaskType.CODE_GENERATION:
            if "context" not in task.input_data:
                logger.warning(f"Task {task.id}: Consider providing 'context' for better code generation")
        
        elif task.task_type == TaskType.CODE_REFACTORING:
            if "files" not in task.input_data:
                logger.warning(f"Task {task.id}: Consider specifying 'files' for targeted refactoring")
        
        return errors


class CodegenWorkflowIntegration:
    """
    Higher-level integration for Codegen workflows and complex operations.
    
    Provides pre-built workflows for common development tasks.
    """
    
    def __init__(self, codegen_integration: CodegenIntegration):
        """Initialize with a Codegen integration instance."""
        self.integration = codegen_integration
    
    async def create_feature_implementation_workflow(
        self,
        feature_description: str,
        repo_url: str,
        target_files: Optional[List[str]] = None,
        tests_required: bool = True
    ) -> Dict[str, Any]:
        """
        Create a workflow for implementing a new feature.
        
        Args:
            feature_description: Description of the feature to implement
            repo_url: Repository URL
            target_files: Specific files to modify (optional)
            tests_required: Whether to generate tests
            
        Returns:
            Workflow configuration
        """
        workflow_steps = []
        
        # Step 1: Analyze existing code
        analysis_task = {
            "name": "Analyze Existing Code",
            "type": "code_analysis",
            "prompt": f"Analyze the codebase to understand the structure for implementing: {feature_description}",
            "repo_url": repo_url,
            "files": target_files or [],
        }
        workflow_steps.append(analysis_task)
        
        # Step 2: Generate implementation
        implementation_task = {
            "name": "Implement Feature",
            "type": "code_generation",
            "prompt": f"Implement the following feature: {feature_description}",
            "repo_url": repo_url,
            "depends_on": ["analyze_existing_code"],
        }
        workflow_steps.append(implementation_task)
        
        # Step 3: Generate tests (if required)
        if tests_required:
            test_task = {
                "name": "Generate Tests",
                "type": "code_generation",
                "prompt": f"Generate comprehensive tests for the feature: {feature_description}",
                "repo_url": repo_url,
                "depends_on": ["implement_feature"],
            }
            workflow_steps.append(test_task)
        
        # Step 4: Create PR
        pr_task = {
            "name": "Create Pull Request",
            "type": "custom",
            "prompt": f"Create a pull request for the feature: {feature_description}",
            "repo_url": repo_url,
            "depends_on": ["generate_tests"] if tests_required else ["implement_feature"],
        }
        workflow_steps.append(pr_task)
        
        return {
            "name": f"Feature Implementation: {feature_description}",
            "description": f"Complete workflow for implementing {feature_description}",
            "steps": workflow_steps,
        }
    
    async def create_bug_fix_workflow(
        self,
        bug_description: str,
        repo_url: str,
        affected_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a workflow for fixing a bug.
        
        Args:
            bug_description: Description of the bug to fix
            repo_url: Repository URL
            affected_files: Files that might be affected
            
        Returns:
            Workflow configuration
        """
        workflow_steps = []
        
        # Step 1: Investigate bug
        investigation_task = {
            "name": "Investigate Bug",
            "type": "code_analysis",
            "prompt": f"Investigate and identify the root cause of: {bug_description}",
            "repo_url": repo_url,
            "files": affected_files or [],
        }
        workflow_steps.append(investigation_task)
        
        # Step 2: Fix bug
        fix_task = {
            "name": "Fix Bug",
            "type": "code_refactoring",
            "prompt": f"Fix the following bug: {bug_description}",
            "repo_url": repo_url,
            "depends_on": ["investigate_bug"],
        }
        workflow_steps.append(fix_task)
        
        # Step 3: Add regression tests
        test_task = {
            "name": "Add Regression Tests",
            "type": "code_generation",
            "prompt": f"Add regression tests to prevent the bug from recurring: {bug_description}",
            "repo_url": repo_url,
            "depends_on": ["fix_bug"],
        }
        workflow_steps.append(test_task)
        
        # Step 4: Create PR
        pr_task = {
            "name": "Create Bug Fix PR",
            "type": "custom",
            "prompt": f"Create a pull request for the bug fix: {bug_description}",
            "repo_url": repo_url,
            "depends_on": ["add_regression_tests"],
        }
        workflow_steps.append(pr_task)
        
        return {
            "name": f"Bug Fix: {bug_description}",
            "description": f"Complete workflow for fixing {bug_description}",
            "steps": workflow_steps,
        }

