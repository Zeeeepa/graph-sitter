"""OpenEvolve API client for continuous learning integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import aiohttp
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from .models import EvaluationRequest, EvaluationResult, EvaluationStatus

logger = logging.getLogger(__name__)


class OpenEvolveAPIError(Exception):
    """Exception raised for OpenEvolve API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class OpenEvolveClient:
    """Client for interacting with the OpenEvolve API."""
    
    def __init__(self, config: OpenEvolveConfig):
        """Initialize the OpenEvolve client.
        
        Args:
            config: OpenEvolve configuration
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not config.is_configured:
            raise ValueError("OpenEvolve API key is required")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self.config.timeout / 1000)  # Convert to seconds
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "graph-sitter-openevolve/1.0.0"
            }
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the OpenEvolve API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data
            
        Raises:
            OpenEvolveAPIError: If the request fails
        """
        await self._ensure_session()
        
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with self._session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response_data = await response.json() if response.content_type == 'application/json' else {}
                
                if response.status >= 400:
                    error_message = response_data.get('error', f"HTTP {response.status}")
                    raise OpenEvolveAPIError(
                        message=error_message,
                        status_code=response.status,
                        response_data=response_data
                    )
                
                return response_data
                
        except aiohttp.ClientError as e:
            logger.error(f"OpenEvolve API request failed: {e}")
            raise OpenEvolveAPIError(f"Request failed: {e}")
        except asyncio.TimeoutError:
            logger.error("OpenEvolve API request timed out")
            raise OpenEvolveAPIError("Request timed out")
    
    async def submit_evaluation(self, evaluation_request: EvaluationRequest) -> str:
        """Submit an evaluation to OpenEvolve.
        
        Args:
            evaluation_request: Evaluation request data
            
        Returns:
            OpenEvolve evaluation ID
            
        Raises:
            OpenEvolveAPIError: If submission fails
        """
        logger.info(f"Submitting evaluation {evaluation_request.id} to OpenEvolve")
        
        data = {
            "id": str(evaluation_request.id),
            "trigger_event": evaluation_request.trigger_event,
            "context": evaluation_request.context,
            "metadata": evaluation_request.metadata,
            "priority": evaluation_request.priority,
            "timeout": evaluation_request.timeout
        }
        
        response = await self._make_request("POST", "/evaluations", data=data)
        evaluation_id = response.get("evaluation_id")
        
        if not evaluation_id:
            raise OpenEvolveAPIError("No evaluation ID returned from OpenEvolve")
        
        logger.info(f"Evaluation {evaluation_request.id} submitted with ID {evaluation_id}")
        return evaluation_id
    
    async def get_evaluation_result(self, evaluation_id: str) -> Dict[str, Any]:
        """Retrieve evaluation results from OpenEvolve.
        
        Args:
            evaluation_id: OpenEvolve evaluation ID
            
        Returns:
            Evaluation result data
            
        Raises:
            OpenEvolveAPIError: If retrieval fails
        """
        logger.debug(f"Retrieving evaluation result for {evaluation_id}")
        
        response = await self._make_request("GET", f"/evaluations/{evaluation_id}")
        return response
    
    async def get_evaluation_status(self, evaluation_id: str) -> EvaluationStatus:
        """Get the status of an evaluation.
        
        Args:
            evaluation_id: OpenEvolve evaluation ID
            
        Returns:
            Current evaluation status
        """
        response = await self._make_request("GET", f"/evaluations/{evaluation_id}/status")
        status_str = response.get("status", "unknown")
        
        try:
            return EvaluationStatus(status_str)
        except ValueError:
            logger.warning(f"Unknown evaluation status: {status_str}")
            return EvaluationStatus.FAILED
    
    async def cancel_evaluation(self, evaluation_id: str) -> bool:
        """Cancel a running evaluation.
        
        Args:
            evaluation_id: OpenEvolve evaluation ID
            
        Returns:
            True if cancellation was successful
        """
        logger.info(f"Cancelling evaluation {evaluation_id}")
        
        try:
            await self._make_request("DELETE", f"/evaluations/{evaluation_id}")
            return True
        except OpenEvolveAPIError as e:
            logger.error(f"Failed to cancel evaluation {evaluation_id}: {e}")
            return False
    
    async def list_evaluations(
        self, 
        status: Optional[EvaluationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List evaluations with optional filtering.
        
        Args:
            status: Filter by evaluation status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of evaluation data
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if status:
            params["status"] = status.value
        
        response = await self._make_request("GET", "/evaluations", params=params)
        return response.get("evaluations", [])
    
    async def get_system_improvements(self, evaluation_id: str) -> List[Dict[str, Any]]:
        """Get system improvement recommendations from an evaluation.
        
        Args:
            evaluation_id: OpenEvolve evaluation ID
            
        Returns:
            List of improvement recommendations
        """
        response = await self._make_request("GET", f"/evaluations/{evaluation_id}/improvements")
        return response.get("improvements", [])
    
    async def health_check(self) -> bool:
        """Check if the OpenEvolve API is healthy.
        
        Returns:
            True if the API is healthy
        """
        try:
            await self._make_request("GET", "/health")
            return True
        except OpenEvolveAPIError:
            return False

