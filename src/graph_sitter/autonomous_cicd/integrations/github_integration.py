"""
GitHub Actions Integration

Provides workflow automation, custom action development,
event-driven triggers, and status reporting.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel

from ..models.pipeline_models import PipelineExecution, PipelineStatus


class WorkflowRun(BaseModel):
    """GitHub Actions workflow run information."""
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    created_at: datetime
    updated_at: datetime
    html_url: str
    jobs_url: str
    logs_url: str


class WorkflowJob(BaseModel):
    """GitHub Actions workflow job information."""
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    steps: List[Dict[str, Any]]


class GitHubActionsIntegration:
    """
    Integration with GitHub Actions for autonomous CI/CD pipeline management.
    """

    def __init__(
        self,
        github_token: str,
        repository: str,
        base_url: str = "https://api.github.com"
    ):
        self.github_token = github_token
        self.repository = repository  # Format: "owner/repo"
        self.base_url = base_url
        
        self.logger = logging.getLogger(__name__)
        
        # HTTP session for API calls
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutonomousCICD/1.0"
        })

    async def trigger_workflow(
        self,
        workflow_file: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a GitHub Actions workflow.
        
        Args:
            workflow_file: Workflow file name (e.g., "ci.yml")
            ref: Git reference (branch, tag, or SHA)
            inputs: Workflow inputs
            
        Returns:
            API response
        """
        url = f"{self.base_url}/repos/{self.repository}/actions/workflows/{workflow_file}/dispatches"
        
        payload = {
            "ref": ref,
            "inputs": inputs or {}
        }
        
        self.logger.info(f"Triggering workflow {workflow_file} on {ref}")
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Successfully triggered workflow {workflow_file}")
            return {"success": True, "status_code": response.status_code}
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to trigger workflow: {e}")
            return {"success": False, "error": str(e)}

    async def get_workflow_runs(
        self,
        workflow_file: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 30
    ) -> List[WorkflowRun]:
        """
        Get workflow runs for the repository.
        
        Args:
            workflow_file: Filter by specific workflow file
            status: Filter by status (queued, in_progress, completed)
            per_page: Number of results per page
            
        Returns:
            List of workflow runs
        """
        if workflow_file:
            url = f"{self.base_url}/repos/{self.repository}/actions/workflows/{workflow_file}/runs"
        else:
            url = f"{self.base_url}/repos/{self.repository}/actions/runs"
        
        params = {"per_page": per_page}
        if status:
            params["status"] = status
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            workflow_runs = []
            
            for run_data in data.get("workflow_runs", []):
                workflow_run = WorkflowRun(
                    id=run_data["id"],
                    name=run_data["name"],
                    status=run_data["status"],
                    conclusion=run_data.get("conclusion"),
                    created_at=datetime.fromisoformat(run_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(run_data["updated_at"].replace("Z", "+00:00")),
                    html_url=run_data["html_url"],
                    jobs_url=run_data["jobs_url"],
                    logs_url=run_data["logs_url"]
                )
                workflow_runs.append(workflow_run)
            
            return workflow_runs
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get workflow runs: {e}")
            return []

    async def get_workflow_run_details(self, run_id: int) -> Optional[WorkflowRun]:
        """
        Get details for a specific workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            Workflow run details or None if not found
        """
        url = f"{self.base_url}/repos/{self.repository}/actions/runs/{run_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            return WorkflowRun(
                id=data["id"],
                name=data["name"],
                status=data["status"],
                conclusion=data.get("conclusion"),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                html_url=data["html_url"],
                jobs_url=data["jobs_url"],
                logs_url=data["logs_url"]
            )
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get workflow run details: {e}")
            return None

    async def get_workflow_jobs(self, run_id: int) -> List[WorkflowJob]:
        """
        Get jobs for a workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            List of workflow jobs
        """
        url = f"{self.base_url}/repos/{self.repository}/actions/runs/{run_id}/jobs"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            for job_data in data.get("jobs", []):
                job = WorkflowJob(
                    id=job_data["id"],
                    name=job_data["name"],
                    status=job_data["status"],
                    conclusion=job_data.get("conclusion"),
                    started_at=datetime.fromisoformat(job_data["started_at"].replace("Z", "+00:00")) if job_data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(job_data["completed_at"].replace("Z", "+00:00")) if job_data.get("completed_at") else None,
                    steps=job_data.get("steps", [])
                )
                jobs.append(job)
            
            return jobs
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get workflow jobs: {e}")
            return []

    async def get_workflow_logs(self, run_id: int) -> Optional[str]:
        """
        Get logs for a workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            Workflow logs as string or None if not available
        """
        url = f"{self.base_url}/repos/{self.repository}/actions/runs/{run_id}/logs"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # GitHub returns logs as a zip file
            # In a real implementation, you would extract and parse the zip
            # For now, return the raw content
            return response.text
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get workflow logs: {e}")
            return None

    async def cancel_workflow_run(self, run_id: int) -> bool:
        """
        Cancel a workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{self.repository}/actions/runs/{run_id}/cancel"
        
        try:
            response = self.session.post(url)
            response.raise_for_status()
            
            self.logger.info(f"Successfully cancelled workflow run {run_id}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to cancel workflow run: {e}")
            return False

    async def create_workflow_file(
        self,
        workflow_name: str,
        workflow_content: str,
        branch: str = "main",
        commit_message: Optional[str] = None
    ) -> bool:
        """
        Create or update a workflow file in the repository.
        
        Args:
            workflow_name: Name of the workflow file
            workflow_content: YAML content of the workflow
            branch: Target branch
            commit_message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        file_path = f".github/workflows/{workflow_name}"
        commit_message = commit_message or f"Add/update workflow {workflow_name}"
        
        # First, try to get the existing file to get its SHA
        get_url = f"{self.base_url}/repos/{self.repository}/contents/{file_path}"
        
        try:
            get_response = self.session.get(get_url, params={"ref": branch})
            existing_sha = None
            
            if get_response.status_code == 200:
                existing_data = get_response.json()
                existing_sha = existing_data["sha"]
            
            # Create or update the file
            import base64
            encoded_content = base64.b64encode(workflow_content.encode()).decode()
            
            payload = {
                "message": commit_message,
                "content": encoded_content,
                "branch": branch
            }
            
            if existing_sha:
                payload["sha"] = existing_sha
            
            put_response = self.session.put(get_url, json=payload)
            put_response.raise_for_status()
            
            self.logger.info(f"Successfully created/updated workflow {workflow_name}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to create workflow file: {e}")
            return False

    async def monitor_pipeline_execution(
        self,
        pipeline_execution: PipelineExecution,
        polling_interval: int = 30
    ) -> Dict[str, Any]:
        """
        Monitor a pipeline execution through GitHub Actions.
        
        Args:
            pipeline_execution: Pipeline execution to monitor
            polling_interval: Polling interval in seconds
            
        Returns:
            Monitoring results
        """
        if not pipeline_execution.workflow_run_id:
            return {"error": "No workflow run ID associated with pipeline"}
        
        run_id = int(pipeline_execution.workflow_run_id)
        start_time = datetime.now()
        
        self.logger.info(f"Starting monitoring for workflow run {run_id}")
        
        while True:
            # Get current status
            workflow_run = await self.get_workflow_run_details(run_id)
            
            if not workflow_run:
                return {"error": f"Workflow run {run_id} not found"}
            
            # Update pipeline status
            if workflow_run.status == "completed":
                if workflow_run.conclusion == "success":
                    pipeline_execution.status = PipelineStatus.SUCCESS
                elif workflow_run.conclusion == "failure":
                    pipeline_execution.status = PipelineStatus.FAILED
                elif workflow_run.conclusion == "cancelled":
                    pipeline_execution.status = PipelineStatus.CANCELLED
                else:
                    pipeline_execution.status = PipelineStatus.FAILED
                
                # Get final results
                jobs = await self.get_workflow_jobs(run_id)
                logs = await self.get_workflow_logs(run_id)
                
                monitoring_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "status": "completed",
                    "conclusion": workflow_run.conclusion,
                    "monitoring_time": monitoring_time,
                    "jobs": [job.dict() for job in jobs],
                    "logs_available": logs is not None,
                    "workflow_url": workflow_run.html_url
                }
            
            elif workflow_run.status == "in_progress":
                pipeline_execution.status = PipelineStatus.RUNNING
            
            # Wait before next poll
            await asyncio.sleep(polling_interval)

    async def setup_webhook(
        self,
        webhook_url: str,
        events: List[str] = None
    ) -> bool:
        """
        Setup a webhook for repository events.
        
        Args:
            webhook_url: URL to receive webhook events
            events: List of events to subscribe to
            
        Returns:
            True if successful, False otherwise
        """
        if events is None:
            events = ["workflow_run", "workflow_job"]
        
        url = f"{self.base_url}/repos/{self.repository}/hooks"
        
        payload = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Successfully setup webhook for {webhook_url}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to setup webhook: {e}")
            return False

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook events from GitHub.
        
        Args:
            event_data: Webhook event data
            
        Returns:
            Processing results
        """
        event_type = event_data.get("action")
        
        if "workflow_run" in event_data:
            return await self._handle_workflow_run_event(event_data)
        elif "workflow_job" in event_data:
            return await self._handle_workflow_job_event(event_data)
        else:
            return {"status": "ignored", "reason": "Unsupported event type"}

    async def _handle_workflow_run_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow run events."""
        workflow_run = event_data["workflow_run"]
        action = event_data["action"]
        
        self.logger.info(f"Received workflow run event: {action} for run {workflow_run['id']}")
        
        # Process based on action
        if action == "completed":
            # Workflow completed - trigger any post-processing
            conclusion = workflow_run.get("conclusion")
            
            if conclusion == "failure":
                # Trigger self-healing if enabled
                return {
                    "status": "processed",
                    "action": "trigger_healing",
                    "run_id": workflow_run["id"],
                    "conclusion": conclusion
                }
            else:
                return {
                    "status": "processed",
                    "action": "workflow_completed",
                    "run_id": workflow_run["id"],
                    "conclusion": conclusion
                }
        
        return {"status": "processed", "action": action}

    async def _handle_workflow_job_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow job events."""
        workflow_job = event_data["workflow_job"]
        action = event_data["action"]
        
        self.logger.info(f"Received workflow job event: {action} for job {workflow_job['id']}")
        
        return {
            "status": "processed",
            "action": action,
            "job_id": workflow_job["id"],
            "job_name": workflow_job["name"]
        }

    def get_integration_status(self) -> Dict[str, Any]:
        """Get the current status of the GitHub integration."""
        try:
            # Test API connectivity
            url = f"{self.base_url}/repos/{self.repository}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                repo_data = response.json()
                return {
                    "status": "connected",
                    "repository": self.repository,
                    "default_branch": repo_data.get("default_branch"),
                    "private": repo_data.get("private"),
                    "actions_enabled": True  # Assume enabled if we can access the repo
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "repository": self.repository
                }
                
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "repository": self.repository
            }

