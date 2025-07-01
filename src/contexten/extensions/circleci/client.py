"""
CircleCI API Client

Comprehensive client for CircleCI API v2 and v1.1 with:
- Authentication and rate limiting
- Retry logic and error handling
- Build, workflow, and job management
- Log and artifact retrieval
- Project and organization management
"""

import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from urllib.parse import urljoin
import json

from .types import (
    CircleCIBuild, CircleCIWorkflow, CircleCIJob, CircleCIProject,
    BuildStatus, LogEntry, TestResult, ComponentStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CircleCIAPIError(Exception):
    """CircleCI API error"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 300):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit permission"""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) >= self.requests_per_minute:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = 60 - (now - oldest_request)
                if wait_time > 0:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
            
            self.requests.append(now)


class CircleCIClient:
    """
    Comprehensive CircleCI API client supporting both v2 and v1.1 APIs
    """
    
    def __init__(
        self,
        api_token: str,
        api_base_url: str = "https://circleci.com/api",
        request_timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_requests_per_minute: int = 300
    ):
        self.api_token = api_token
        self.api_base_url = api_base_url.rstrip('/')
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit_requests_per_minute)
        
        # Statistics
        self.stats = ComponentStats()
        
        # Session will be created when needed
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            headers = {
                "Circle-Token": self.api_token,
                "Accept": "application/json",
                "User-Agent": "Contexten-CircleCI-Integration/1.0.0"
            }
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self._session
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        api_version: str = "v2",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Build URL
        if api_version == "v1.1":
            url = f"{self.api_base_url}/v1.1{endpoint}"
        else:
            url = f"{self.api_base_url}/v2{endpoint}"
        
        session = await self._get_session()
        
        try:
            start_time = time.time()
            
            # Make request
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None
            ) as response:
                
                # Update statistics
                self.stats.requests_total += 1
                self.stats.last_request_at = datetime.now()
                
                response_time = time.time() - start_time
                self.stats.average_response_time = (
                    (self.stats.average_response_time * (self.stats.requests_total - 1) + response_time) /
                    self.stats.requests_total
                )
                
                # Handle response
                if response.status == 200:
                    self.stats.requests_successful += 1
                    try:
                        return await response.json()
                    except json.JSONDecodeError:
                        # Some endpoints return plain text
                        text = await response.text()
                        return {"data": text}
                
                elif response.status == 429:  # Rate limited
                    self.stats.requests_failed += 1
                    if retry_count < self.max_retries:
                        wait_time = self.retry_delay * (2 ** retry_count)
                        logger.warning(f"Rate limited, retrying in {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(
                            method, endpoint, api_version, params, data, retry_count + 1
                        )
                    else:
                        raise CircleCIAPIError(
                            f"Rate limited after {self.max_retries} retries",
                            status_code=response.status
                        )
                
                elif 500 <= response.status < 600:  # Server error
                    self.stats.requests_failed += 1
                    if retry_count < self.max_retries:
                        wait_time = self.retry_delay * (2 ** retry_count)
                        logger.warning(f"Server error {response.status}, retrying in {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(
                            method, endpoint, api_version, params, data, retry_count + 1
                        )
                    else:
                        error_text = await response.text()
                        raise CircleCIAPIError(
                            f"Server error after {self.max_retries} retries: {error_text}",
                            status_code=response.status
                        )
                
                else:  # Client error
                    self.stats.requests_failed += 1
                    error_text = await response.text()
                    try:
                        error_data = json.loads(error_text)
                    except json.JSONDecodeError:
                        error_data = {"message": error_text}
                    
                    raise CircleCIAPIError(
                        f"API error: {error_data.get('message', error_text)}",
                        status_code=response.status,
                        response_data=error_data
                    )
        
        except aiohttp.ClientError as e:
            self.stats.requests_failed += 1
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Request failed: {e}, retrying in {wait_time} seconds")
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method, endpoint, api_version, params, data, retry_count + 1
                )
            else:
                raise CircleCIAPIError(f"Request failed after {self.max_retries} retries: {e}")
    
    # Project Management
    async def get_projects(self) -> List[CircleCIProject]:
        """Get all projects for the authenticated user"""
        try:
            response = await self._make_request("GET", "/projects")
            projects = []
            
            for item in response.get("items", []):
                project = CircleCIProject(
                    slug=item["slug"],
                    name=item["name"],
                    organization_name=item["organization_name"],
                    organization_slug=item["organization_slug"],
                    organization_id=item["organization_id"],
                    vcs_info=item.get("vcs_info", {})
                )
                projects.append(project)
            
            logger.info(f"Retrieved {len(projects)} projects")
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise
    
    async def get_project(self, project_slug: str) -> CircleCIProject:
        """Get specific project information"""
        try:
            response = await self._make_request("GET", f"/project/{project_slug}")
            
            return CircleCIProject(
                slug=response["slug"],
                name=response["name"],
                organization_name=response["organization_name"],
                organization_slug=response["organization_slug"],
                organization_id=response["organization_id"],
                vcs_info=response.get("vcs_info", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to get project {project_slug}: {e}")
            raise
    
    # Pipeline and Workflow Management
    async def get_project_pipelines(
        self,
        project_slug: str,
        branch: Optional[str] = None,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get pipelines for a project"""
        try:
            params = {}
            if branch:
                params["branch"] = branch
            if page_token:
                params["page-token"] = page_token
            
            response = await self._make_request(
                "GET", f"/project/{project_slug}/pipeline", params=params
            )
            
            logger.debug(f"Retrieved pipelines for {project_slug}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get pipelines for {project_slug}: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> CircleCIWorkflow:
        """Get workflow information"""
        try:
            response = await self._make_request("GET", f"/workflow/{workflow_id}")
            
            return CircleCIWorkflow(
                id=response["id"],
                name=response["name"],
                project_slug=response["project_slug"],
                status=BuildStatus(response["status"]),
                started_at=datetime.fromisoformat(response["started_at"].replace("Z", "+00:00")) if response.get("started_at") else None,
                stopped_at=datetime.fromisoformat(response["stopped_at"].replace("Z", "+00:00")) if response.get("stopped_at") else None,
                created_at=datetime.fromisoformat(response["created_at"].replace("Z", "+00:00")) if response.get("created_at") else None,
                pipeline_id=response["pipeline_id"],
                pipeline_number=response["pipeline_number"],
                tag=response.get("tag")
            )
            
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            raise
    
    async def get_workflow_jobs(self, workflow_id: str) -> List[CircleCIJob]:
        """Get jobs for a workflow"""
        try:
            response = await self._make_request("GET", f"/workflow/{workflow_id}/job")
            jobs = []
            
            for item in response.get("items", []):
                job = CircleCIJob(
                    id=item["id"],
                    name=item["name"],
                    project_slug=item["project_slug"],
                    status=BuildStatus(item["status"]),
                    started_at=datetime.fromisoformat(item["started_at"].replace("Z", "+00:00")) if item.get("started_at") else None,
                    stopped_at=datetime.fromisoformat(item["stopped_at"].replace("Z", "+00:00")) if item.get("stopped_at") else None,
                    duration=item.get("duration"),
                    credits_used=item.get("credits_used"),
                    exit_code=item.get("exit_code"),
                    parallel=item.get("parallel"),
                    parallelism=item.get("parallelism"),
                    web_url=item["web_url"],
                    executor=item.get("executor"),
                    contexts=item.get("contexts", [])
                )
                jobs.append(job)
            
            logger.debug(f"Retrieved {len(jobs)} jobs for workflow {workflow_id}")
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get jobs for workflow {workflow_id}: {e}")
            raise
    
    # Job Management
    async def get_job(self, job_id: str) -> CircleCIJob:
        """Get job information"""
        try:
            response = await self._make_request("GET", f"/job/{job_id}")
            
            return CircleCIJob(
                id=response["id"],
                name=response["name"],
                project_slug=response["project_slug"],
                status=BuildStatus(response["status"]),
                started_at=datetime.fromisoformat(response["started_at"].replace("Z", "+00:00")) if response.get("started_at") else None,
                stopped_at=datetime.fromisoformat(response["stopped_at"].replace("Z", "+00:00")) if response.get("stopped_at") else None,
                duration=response.get("duration"),
                credits_used=response.get("credits_used"),
                exit_code=response.get("exit_code"),
                parallel=response.get("parallel"),
                parallelism=response.get("parallelism"),
                web_url=response["web_url"],
                executor=response.get("executor"),
                contexts=response.get("contexts", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
    
    async def get_job_logs(self, job_id: str) -> List[LogEntry]:
        """Get logs for a job"""
        try:
            # Get log steps first
            response = await self._make_request("GET", f"/job/{job_id}/steps")
            
            logs = []
            for step in response.get("items", []):
                for action in step.get("actions", []):
                    if action.get("has_output"):
                        # Get log output for this action
                        log_response = await self._make_request(
                            "GET", f"/job/{job_id}/steps/{step['step_index']}/actions/{action['index']}/output"
                        )
                        
                        for log_item in log_response.get("items", []):
                            log_entry = LogEntry(
                                timestamp=datetime.fromisoformat(log_item["time"].replace("Z", "+00:00")) if log_item.get("time") else None,
                                message=log_item.get("message", ""),
                                source=f"{step.get('name', 'unknown')}/{action.get('name', 'unknown')}",
                                level="error" if action.get("exit_code", 0) != 0 else "info",
                                is_error=action.get("exit_code", 0) != 0
                            )
                            logs.append(log_entry)
            
            logger.debug(f"Retrieved {len(logs)} log entries for job {job_id}")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get logs for job {job_id}: {e}")
            raise
    
    async def get_job_artifacts(self, job_id: str) -> List[Dict[str, Any]]:
        """Get artifacts for a job"""
        try:
            response = await self._make_request("GET", f"/job/{job_id}/artifacts")
            
            artifacts = response.get("items", [])
            logger.debug(f"Retrieved {len(artifacts)} artifacts for job {job_id}")
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to get artifacts for job {job_id}: {e}")
            raise
    
    async def get_job_tests(self, job_id: str) -> List[TestResult]:
        """Get test results for a job"""
        try:
            response = await self._make_request("GET", f"/job/{job_id}/tests")
            
            tests = []
            for item in response.get("items", []):
                test = TestResult(
                    name=item["name"],
                    classname=item.get("classname"),
                    file=item.get("file"),
                    result=item["result"],
                    message=item.get("message"),
                    time=item.get("time"),
                    failure_message=item.get("failure_message"),
                    failure_type=item.get("failure_type"),
                    stack_trace=item.get("stack_trace")
                )
                tests.append(test)
            
            logger.debug(f"Retrieved {len(tests)} test results for job {job_id}")
            return tests
            
        except Exception as e:
            logger.error(f"Failed to get tests for job {job_id}: {e}")
            raise
    
    # Legacy v1.1 API Support
    async def get_build_v1(self, username: str, project: str, build_num: int) -> CircleCIBuild:
        """Get build information using v1.1 API"""
        try:
            response = await self._make_request(
                "GET", f"/project/{username}/{project}/{build_num}", api_version="v1.1"
            )
            
            return CircleCIBuild(
                build_num=response["build_num"],
                username=response["username"],
                reponame=response["reponame"],
                branch=response["branch"],
                vcs_revision=response["vcs_revision"],
                status=BuildStatus(response["status"]),
                start_time=datetime.fromisoformat(response["start_time"]) if response.get("start_time") else None,
                stop_time=datetime.fromisoformat(response["stop_time"]) if response.get("stop_time") else None,
                build_time_millis=response.get("build_time_millis"),
                subject=response.get("subject"),
                body=response.get("body"),
                why=response.get("why"),
                dont_build=response.get("dont_build"),
                queued_at=datetime.fromisoformat(response["queued_at"]) if response.get("queued_at") else None,
                lifecycle=response.get("lifecycle"),
                outcome=response.get("outcome"),
                build_url=response.get("build_url"),
                compare=response.get("compare"),
                author_name=response.get("author_name"),
                author_email=response.get("author_email"),
                committer_name=response.get("committer_name"),
                committer_email=response.get("committer_email")
            )
            
        except Exception as e:
            logger.error(f"Failed to get build {username}/{project}/{build_num}: {e}")
            raise
    
    async def get_recent_builds_v1(
        self,
        username: str,
        project: str,
        limit: int = 30,
        offset: int = 0,
        filter_status: Optional[str] = None
    ) -> List[CircleCIBuild]:
        """Get recent builds using v1.1 API"""
        try:
            params = {"limit": limit, "offset": offset}
            if filter_status:
                params["filter"] = filter_status
            
            response = await self._make_request(
                "GET", f"/project/{username}/{project}", api_version="v1.1", params=params
            )
            
            builds = []
            for item in response:
                build = CircleCIBuild(
                    build_num=item["build_num"],
                    username=item["username"],
                    reponame=item["reponame"],
                    branch=item["branch"],
                    vcs_revision=item["vcs_revision"],
                    status=BuildStatus(item["status"]),
                    start_time=datetime.fromisoformat(item["start_time"]) if item.get("start_time") else None,
                    stop_time=datetime.fromisoformat(item["stop_time"]) if item.get("stop_time") else None,
                    build_time_millis=item.get("build_time_millis"),
                    subject=item.get("subject"),
                    body=item.get("body"),
                    why=item.get("why"),
                    dont_build=item.get("dont_build"),
                    queued_at=datetime.fromisoformat(item["queued_at"]) if item.get("queued_at") else None,
                    lifecycle=item.get("lifecycle"),
                    outcome=item.get("outcome"),
                    build_url=item.get("build_url"),
                    compare=item.get("compare"),
                    author_name=item.get("author_name"),
                    author_email=item.get("author_email"),
                    committer_name=item.get("committer_name"),
                    committer_email=item.get("committer_email")
                )
                builds.append(build)
            
            logger.debug(f"Retrieved {len(builds)} recent builds for {username}/{project}")
            return builds
            
        except Exception as e:
            logger.error(f"Failed to get recent builds for {username}/{project}: {e}")
            raise
    
    # Utility Methods
    async def trigger_pipeline(
        self,
        project_slug: str,
        branch: str = "main",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trigger a new pipeline"""
        try:
            data = {
                "branch": branch
            }
            if parameters:
                data["parameters"] = parameters
            
            response = await self._make_request(
                "POST", f"/project/{project_slug}/pipeline", data=data
            )
            
            logger.info(f"Triggered pipeline for {project_slug} on branch {branch}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to trigger pipeline for {project_slug}: {e}")
            raise
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel a workflow"""
        try:
            response = await self._make_request("POST", f"/workflow/{workflow_id}/cancel")
            
            logger.info(f"Cancelled workflow {workflow_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            raise
    
    async def rerun_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Rerun a workflow"""
        try:
            response = await self._make_request("POST", f"/workflow/{workflow_id}/rerun")
            
            logger.info(f"Reran workflow {workflow_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to rerun workflow {workflow_id}: {e}")
            raise
    
    # Health and Status
    async def health_check(self) -> bool:
        """Check if the API is accessible"""
        try:
            await self._make_request("GET", "/me")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_stats(self) -> ComponentStats:
        """Get client statistics"""
        return self.stats

