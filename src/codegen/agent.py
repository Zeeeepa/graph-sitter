"""
Agent class for interacting with Codegen SWE agents via API.
"""

import requests
import time
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin

from .task import Task
from .exceptions import (
    AuthenticationError, 
    APIError, 
    RateLimitError, 
    ValidationError,
    TaskError
)


class Agent:
    """
    Main class for interacting with Codegen SWE agents via API.
    
    The Agent class provides methods to run tasks, manage authentication,
    and interact with the Codegen platform programmatically.
    """
    
    def __init__(
        self, 
        org_id: str, 
        token: str, 
        base_url: str = "https://api.codegen.com",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the Codegen Agent.
        
        Args:
            org_id: Your organization ID from Codegen
            token: Your API token from https://codegen.sh/token
            base_url: Base URL for the Codegen API (default: https://api.codegen.com)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
            
        Raises:
            AuthenticationError: If credentials are invalid
            ValidationError: If parameters are invalid
        """
        if not org_id or not isinstance(org_id, str):
            raise ValidationError("org_id must be a non-empty string")
        if not token or not isinstance(token, str):
            raise ValidationError("token must be a non-empty string")
        
        self.org_id = org_id
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set up session with authentication
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "codegen-python-sdk/1.0.0"
        })
        
        # Validate credentials on initialization
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """Validate the provided credentials."""
        try:
            response = self._make_request("GET", "/v1/auth/validate")
            if response.status_code != 200:
                raise AuthenticationError("Invalid credentials")
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to validate credentials: {str(e)}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        retry_count: int = 0
    ) -> requests.Response:
        """
        Make an HTTP request to the Codegen API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt
            
        Returns:
            Response object
            
        Raises:
            APIError: If the request fails
            RateLimitError: If rate limit is exceeded
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                if retry_count < self.max_retries:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                    return self._make_request(method, endpoint, data, params, retry_count + 1)
                else:
                    raise RateLimitError("Rate limit exceeded and max retries reached")
            
            # Handle other errors
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", f"HTTP {response.status_code}")
                raise APIError(error_message, response.status_code, error_data)
            
            return response
            
        except requests.RequestException as e:
            if retry_count < self.max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(method, endpoint, data, params, retry_count + 1)
            else:
                raise APIError(f"Request failed: {str(e)}")
    
    def run(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        priority: str = "normal",
        timeout: Optional[int] = None
    ) -> Task:
        """
        Run an agent with a prompt.
        
        Args:
            prompt: The task prompt for the agent
            context: Additional context for the task
            repository: Target repository (format: "owner/repo")
            branch: Target branch (default: main/master)
            priority: Task priority ("low", "normal", "high")
            timeout: Task timeout in seconds
            
        Returns:
            Task object representing the running task
            
        Raises:
            ValidationError: If parameters are invalid
            APIError: If the request fails
        """
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("prompt must be a non-empty string")
        
        if priority not in ["low", "normal", "high"]:
            raise ValidationError("priority must be 'low', 'normal', or 'high'")
        
        task_data = {
            "org_id": self.org_id,
            "prompt": prompt,
            "priority": priority
        }
        
        if context:
            task_data["context"] = context
        if repository:
            task_data["repository"] = repository
        if branch:
            task_data["branch"] = branch
        if timeout:
            task_data["timeout"] = timeout
        
        response = self._make_request("POST", "/v1/tasks", data=task_data)
        task_info = response.json()
        
        return Task(task_info["task_id"], self, task_info)
    
    def get_task(self, task_id: str) -> Task:
        """
        Get a task by ID.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task object
            
        Raises:
            TaskError: If the task cannot be found
        """
        try:
            task_data = self._get_task(task_id)
            return Task(task_id, self, task_data)
        except Exception as e:
            raise TaskError(f"Failed to get task {task_id}: {str(e)}")
    
    def _get_task(self, task_id: str) -> Dict[str, Any]:
        """Internal method to get task data."""
        response = self._make_request("GET", f"/v1/tasks/{task_id}")
        return response.json()
    
    def _cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Internal method to cancel a task."""
        response = self._make_request("POST", f"/v1/tasks/{task_id}/cancel")
        return response.json()
    
    def _get_task_artifacts(self, task_id: str) -> List[Dict[str, Any]]:
        """Internal method to get task artifacts."""
        response = self._make_request("GET", f"/v1/tasks/{task_id}/artifacts")
        return response.json().get("artifacts", [])
    
    def list_tasks(
        self, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Task]:
        """
        List tasks for the organization.
        
        Args:
            status: Filter by status ("pending", "running", "completed", "failed", "cancelled")
            limit: Maximum number of tasks to return (default: 50)
            offset: Number of tasks to skip (default: 0)
            
        Returns:
            List of Task objects
        """
        params = {
            "org_id": self.org_id,
            "limit": limit,
            "offset": offset
        }
        
        if status:
            params["status"] = status
        
        response = self._make_request("GET", "/v1/tasks", params=params)
        tasks_data = response.json().get("tasks", [])
        
        return [Task(task["task_id"], self, task) for task in tasks_data]
    
    def get_usage(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for the organization.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Usage statistics
        """
        params = {"org_id": self.org_id}
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._make_request("GET", "/v1/usage", params=params)
        return response.json()
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """
        Get available repositories for the organization.
        
        Returns:
            List of repository information
        """
        params = {"org_id": self.org_id}
        response = self._make_request("GET", "/v1/repositories", params=params)
        return response.json().get("repositories", [])
    
    def create_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Create a webhook for task events.
        
        Args:
            url: Webhook URL
            events: List of events to subscribe to
            
        Returns:
            Webhook information
        """
        data = {
            "org_id": self.org_id,
            "url": url,
            "events": events
        }
        
        response = self._make_request("POST", "/v1/webhooks", data=data)
        return response.json()
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"Agent(org_id={self.org_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"Agent(org_id={self.org_id}, base_url={self.base_url})"

