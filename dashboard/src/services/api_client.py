"""
API Client for Backend Communication

Handles all HTTP communication with the FastAPI backend server.
Provides async methods for all analysis operations.
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from ..utils.exceptions import APIError, NetworkError, ValidationError


class APIClient:
    """Client for communicating with the codebase analysis API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
        return self._client
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with error handling."""
        try:
            client = await self._get_client()
            response = await client.request(method, endpoint, **kwargs)
            
            if response.status_code == 404:
                raise APIError(f"Endpoint not found: {endpoint}")
            elif response.status_code >= 400:
                error_detail = response.json().get("detail", f"HTTP {response.status_code}")
                raise APIError(f"API error: {error_detail}")
            
            return response.json()
            
        except httpx.ConnectError:
            raise NetworkError("Cannot connect to the analysis server. Please ensure the backend is running on port 8000.")
        except httpx.TimeoutException:
            raise NetworkError("Request timed out. The analysis server may be overloaded.")
        except httpx.HTTPError as e:
            raise NetworkError(f"Network error: {str(e)}")
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}")
    
    async def start_analysis(self, repo_url: str) -> Dict[str, Any]:
        """Start a new repository analysis."""
        if not repo_url.strip():
            raise ValidationError("Repository URL cannot be empty")
        
        payload = {"repo_url": repo_url.strip()}
        return await self._make_request("POST", "/api/analyze", json=payload)
    
    async def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """Get the status of an analysis."""
        if not analysis_id:
            raise ValidationError("Analysis ID cannot be empty")
        
        return await self._make_request("GET", f"/api/analysis/{analysis_id}/status")
    
    async def get_analysis_tree(self, analysis_id: str) -> Dict[str, Any]:
        """Get the tree structure for an analysis."""
        if not analysis_id:
            raise ValidationError("Analysis ID cannot be empty")
        
        return await self._make_request("GET", f"/api/analysis/{analysis_id}/tree")
    
    async def get_analysis_issues(self, analysis_id: str) -> Dict[str, Any]:
        """Get the issues for an analysis."""
        if not analysis_id:
            raise ValidationError("Analysis ID cannot be empty")
        
        return await self._make_request("GET", f"/api/analysis/{analysis_id}/issues")
    
    async def get_analysis_dead_code(self, analysis_id: str) -> Dict[str, Any]:
        """Get the dead code analysis for an analysis."""
        if not analysis_id:
            raise ValidationError("Analysis ID cannot be empty")
        
        return await self._make_request("GET", f"/api/analysis/{analysis_id}/dead_code")
    
    async def get_analysis_important_functions(self, analysis_id: str) -> Dict[str, Any]:
        """Get the important functions for an analysis."""
        if not analysis_id:
            raise ValidationError("Analysis ID cannot be empty")
        
        return await self._make_request("GET", f"/api/analysis/{analysis_id}/important_functions")
    
    async def get_analysis_stats(self, analysis_id: str) -> Dict[str, Any]:
        """Get the statistics for an analysis."""
        if not analysis_id:
            raise ValidationError("Analysis ID cannot be empty")
        
        return await self._make_request("GET", f"/api/analysis/{analysis_id}/stats")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the API server is healthy."""
        return await self._make_request("GET", "/api/health")
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

