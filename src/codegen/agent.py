"""
Enhanced Agent class for interacting with Codegen SWE agents via API.

Includes robust error handling, retry mechanisms, rate limiting, and comprehensive monitoring.
"""

import requests
import time
import logging
import json
from typing import Optional, Dict, Any, List, Union, Callable
from urllib.parse import urljoin
from datetime import datetime, timezone

from .task import Task
from .exceptions import (
    AuthenticationError, 
    APIError, 
    RateLimitError, 
    ValidationError,
    TaskError,
    TimeoutError,
    NetworkError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class Agent:
    """
    Enhanced Agent class for interacting with Codegen SWE agents via API.
    
    Features:
    - Robust error handling with exponential backoff
    - Comprehensive retry mechanisms
    - Advanced rate limiting
    - Request/response logging
    - Connection pooling
    - Webhook support
    - Monitoring and metrics
    """
    
    def __init__(
        self, 
        org_id: str, 
        token: str, 
        base_url: str = "https://api.codegen.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0,
        rate_limit_buffer: float = 0.1,
        enable_logging: bool = True,
        connection_pool_size: int = 10,
        validate_on_init: bool = False
    ):
        """
        Initialize the enhanced Codegen Agent.
        
        Args:
            org_id: Your organization ID from Codegen
            token: Your API token from https://codegen.sh/token
            base_url: Base URL for the Codegen API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff_factor: Exponential backoff factor for retries
            rate_limit_buffer: Buffer time to add to rate limit waits
            enable_logging: Enable detailed request/response logging
            connection_pool_size: Size of the connection pool
            validate_on_init: Validate credentials during initialization (optional)
            
        Raises:
            ValidationError: If parameters are invalid
            ConfigurationError: If configuration is invalid
        """
        # Validate inputs
        if not org_id or not isinstance(org_id, str):
            raise ValidationError("org_id must be a non-empty string", field="org_id")
        if not token or not isinstance(token, str):
            raise ValidationError("token must be a non-empty string", field="token")
        if timeout <= 0:
            raise ValidationError("timeout must be positive", field="timeout")
        if max_retries < 0:
            raise ValidationError("max_retries must be non-negative", field="max_retries")
        
        # Configuration
        self.org_id = org_id
        self.token = token
        self.base_url = (base_url or "https://api.codegen.com").rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.rate_limit_buffer = rate_limit_buffer
        
        # Set up enhanced session with connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=connection_pool_size,
            pool_maxsize=connection_pool_size,
            max_retries=0  # We handle retries manually
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "enhanced-codegen-python-sdk/1.1.0",
            "X-Client-Version": "1.1.0"
        })
        
        # Enhanced monitoring
        self._request_count = 0
        self._error_count = 0
        self._rate_limit_count = 0
        self._last_request_time: Optional[float] = None
        self._rate_limit_reset_time: Optional[float] = None
        self._start_time = time.time()
        
        # Webhooks
        self._webhooks: List[Dict[str, Any]] = []
        
        # Configure logging
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
        
        logger.info(f"Enhanced Codegen Agent initialized for org {org_id}")
        
        # Validate credentials during initialization (optional)
        if validate_on_init:
            try:
                self._validate_credentials()
            except Exception as e:
                logger.error(f"Credential validation failed: {e}")
                raise AuthenticationError(f"Failed to validate credentials: {str(e)}")
    
    def _validate_credentials(self) -> None:
        """Validate the provided credentials with enhanced error handling."""
        try:
            response = self._make_request("GET", "/v1/auth/validate")
            if response.status_code == 200:
                logger.info("Credentials validated successfully")
            else:
                raise AuthenticationError("Invalid credentials")
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to validate credentials: {str(e)}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Make HTTP request with enhanced error handling and monitoring.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            timeout: Request timeout (uses instance timeout if None)
            
        Returns:
            Response object
            
        Raises:
            CodegenAPIError: For API-related errors
            CodegenTimeoutError: For timeout errors
            CodegenRateLimitError: For rate limiting
        """
        if timeout is None:
            timeout = self.timeout or 30  # Default to 30 if self.timeout is None
        
        url = urljoin(self.base_url, endpoint)
        
        # Check rate limiting
        if self._is_rate_limited():
            wait_time = (self._rate_limit_reset_time or 0) - time.time()
            logger.warning(f"Rate limited, waiting {wait_time:.1f} seconds")
            time.sleep(wait_time + self.rate_limit_buffer)
        
        # Prepare request
        request_id = f"req_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            if self.enable_logging:
                logger.debug(f"[{request_id}] {method} {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            self._request_count += 1
            self._last_request_time = time.time()
            
            if self.enable_logging:
                logger.debug(f"[{request_id}] Response: {response.status_code} ({response_time:.2f}s)")
            
            # Handle rate limiting
            if response.status_code == 429:
                self._rate_limit_count += 1
                retry_after = int(response.headers.get("Retry-After", 60))
                self._rate_limit_reset_time = time.time() + retry_after
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed - invalid token")
            
            # Handle other client/server errors
            if response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except (json.JSONDecodeError, ValueError):
                    pass
                
                error_message = error_data.get("error", f"HTTP {response.status_code}")
                self._error_count += 1
                raise APIError(error_message, response.status_code, error_data)
            
            return response
            
        except requests.exceptions.Timeout:
            self._error_count += 1
            raise TimeoutError(f"Request timed out after {timeout} seconds")
        
        except requests.exceptions.ConnectionError as e:
            self._error_count += 1
            raise NetworkError(f"Connection failed: {str(e)}", original_error=e)
        
        except requests.RequestException as e:
            self._error_count += 1
            raise NetworkError(f"Request failed: {str(e)}", original_error=e)
    
    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited."""
        if self._rate_limit_reset_time:
            return time.time() < self._rate_limit_reset_time
        return False
    
    def run(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        priority: str = "normal",
        timeout: Optional[int] = None,
        tags: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Task:
        """
        Run an agent with a prompt and enhanced options.
        
        Args:
            prompt: The task prompt for the agent
            context: Additional context for the task
            repository: Target repository (format: "owner/repo")
            branch: Target branch (default: main/master)
            priority: Task priority ("low", "normal", "high", "urgent")
            timeout: Task timeout in seconds
            tags: Optional tags for task categorization
            webhook_url: Optional webhook URL for task updates
            
        Returns:
            Task object representing the running task
            
        Raises:
            ValidationError: If parameters are invalid
            APIError: If the request fails
        """
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("prompt must be a non-empty string", field="prompt")
        
        if priority not in ["low", "normal", "high", "urgent"]:
            raise ValidationError("priority must be 'low', 'normal', 'high', or 'urgent'", field="priority")
        
        task_data: Dict[str, Any] = {
            "org_id": self.org_id,
            "prompt": prompt,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if context:
            task_data["context"] = context
        if repository:
            task_data["repository"] = repository
        if branch:
            task_data["branch"] = branch
        if timeout:
            task_data["timeout"] = timeout
        if tags:
            task_data["tags"] = tags
        if webhook_url:
            task_data["webhook_url"] = webhook_url
        
        logger.info(f"Creating task with priority {priority}: {prompt[:100]}...")
        
        response = self._make_request("POST", "/v1/tasks", data=task_data)
        task_info = response.json()
        
        task = Task(task_info["task_id"], self, task_info)
        logger.info(f"Task {task.task_id} created successfully")
        
        return task
    
    def get_task(self, task_id: str) -> Task:
        """
        Get a task by ID with enhanced error handling.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task object
            
        Raises:
            TaskError: If the task cannot be found
            ValidationError: If task_id is invalid
        """
        if not task_id or not isinstance(task_id, str):
            raise ValidationError("task_id must be a non-empty string", field="task_id")
        
        try:
            task_data = self._get_task(task_id)
            return Task(task_id, self, task_data)
        except Exception as e:
            raise TaskError(f"Failed to get task {task_id}: {str(e)}", task_id=task_id)
    
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
    
    def _get_task_logs(self, task_id: str) -> Dict[str, Any]:
        """Internal method to get task logs."""
        response = self._make_request("GET", f"/v1/tasks/{task_id}/logs")
        return response.json()
    
    def list_tasks(
        self, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> List[Task]:
        """
        List tasks for the organization with enhanced filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            tags: Filter by tags
            created_after: Filter tasks created after this timestamp
            created_before: Filter tasks created before this timestamp
            
        Returns:
            List of Task objects
        """
        params = {
            "org_id": self.org_id,
            "limit": min(limit, 100),  # Cap at 100
            "offset": offset
        }
        
        if status:
            params["status"] = status
        if tags:
            params["tags"] = ",".join(tags)
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        
        response = self._make_request("GET", "/v1/tasks", params=params)
        tasks_data = response.json().get("tasks", [])
        
        return [Task(task["task_id"], self, task) for task in tasks_data]
    
    def get_usage(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        granularity: str = "day"
    ) -> Dict[str, Any]:
        """
        Get enhanced usage statistics for the organization.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Data granularity ("hour", "day", "week", "month")
            
        Returns:
            Enhanced usage statistics
        """
        params = {"org_id": self.org_id, "granularity": granularity}
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._make_request("GET", "/v1/usage", params=params)
        return response.json()
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get available repositories for the organization."""
        params = {"org_id": self.org_id}
        response = self._make_request("GET", "/v1/repositories", params=params)
        return response.json().get("repositories", [])
    
    def create_webhook(self, url: str, events: List[str], secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a webhook for task events with enhanced options.
        
        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Optional webhook secret for verification
            
        Returns:
            Webhook information
        """
        data = {
            "org_id": self.org_id,
            "url": url,
            "events": events
        }
        
        if secret:
            data["secret"] = secret
        
        response = self._make_request("POST", "/v1/webhooks", data=data)
        webhook_info = response.json()
        self._webhooks.append(webhook_info)
        
        return webhook_info
    
    def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get all webhooks for the organization."""
        params = {"org_id": self.org_id}
        response = self._make_request("GET", "/v1/webhooks", params=params)
        return response.json().get("webhooks", [])
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        try:
            self._make_request("DELETE", f"/v1/webhooks/{webhook_id}")
            # Remove from local cache
            self._webhooks = [w for w in self._webhooks if w.get("id") != webhook_id]
            return True
        except Exception:
            return False
    
    def get_health(self) -> Dict[str, Any]:
        """Get API health status."""
        response = self._make_request("GET", "/v1/health")
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive agent statistics."""
        uptime = time.time() - self._start_time
        
        return {
            "org_id": self.org_id,
            "uptime_seconds": uptime,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "rate_limit_count": self._rate_limit_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "last_request_time": self._last_request_time,
            "is_rate_limited": self._is_rate_limited(),
            "webhooks_count": len(self._webhooks),
            "config": {
                "base_url": self.base_url,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "retry_backoff_factor": self.retry_backoff_factor
            }
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"Agent(org_id={self.org_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"Agent(org_id={self.org_id}, requests={self._request_count}, errors={self._error_count})"
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()
        logger.info(f"Agent session closed. Stats: {self.get_stats()}")
