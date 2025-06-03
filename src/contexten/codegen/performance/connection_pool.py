"""
Connection pooling for HTTP requests to optimize performance.

This module provides connection pooling and management for HTTP requests
to the Codegen API, reducing connection overhead and improving throughput.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
from contextlib import asynccontextmanager


logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Statistics for connection pool monitoring."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    connection_errors: int = 0
    timeouts: int = 0


class ConnectionPool:
    """
    HTTP connection pool with advanced features.
    
    Features:
    - Connection reuse and pooling
    - Automatic connection health checking
    - Request timeout handling
    - Connection lifecycle management
    - Performance monitoring
    """
    
    def __init__(self,
                 max_connections: int = 20,
                 max_keepalive_connections: int = 10,
                 timeout: float = 30.0,
                 keepalive_expiry: float = 300.0,
                 max_retries: int = 3):
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum total connections
            max_keepalive_connections: Maximum keepalive connections
            timeout: Request timeout in seconds
            keepalive_expiry: Keepalive connection expiry in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.timeout = timeout
        self.keepalive_expiry = keepalive_expiry
        self.max_retries = max_retries
        
        # HTTP client with connection pooling
        self.limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=keepalive_expiry
        )
        
        self.timeout_config = httpx.Timeout(
            connect=10.0,
            read=timeout,
            write=timeout,
            pool=timeout
        )
        
        self._client: Optional[httpx.AsyncClient] = None
        self._stats = ConnectionStats()
        self._response_times: List[float] = []
        self._health_check_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._initialized:
            return
        
        self._client = httpx.AsyncClient(
            limits=self.limits,
            timeout=self.timeout_config,
            follow_redirects=True,
            verify=True
        )
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        self._initialized = True
        logger.info(f"Connection pool initialized with {self.max_connections} max connections")
    
    async def close(self) -> None:
        """Close the connection pool and cleanup resources."""
        logger.info("Closing connection pool")
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._initialized = False
        logger.info("Connection pool closed")
    
    @asynccontextmanager
    async def get_client(self):
        """
        Get HTTP client from the pool.
        
        Yields:
            httpx.AsyncClient: HTTP client for making requests
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._client:
            raise RuntimeError("Connection pool not initialized")
        
        try:
            yield self._client
        except Exception as e:
            self._stats.connection_errors += 1
            logger.error(f"Connection pool error: {e}")
            raise
    
    async def request(self,
                     method: str,
                     url: str,
                     headers: Optional[Dict[str, str]] = None,
                     data: Optional[Any] = None,
                     json: Optional[Any] = None,
                     params: Optional[Dict[str, Any]] = None,
                     timeout: Optional[float] = None) -> httpx.Response:
        """
        Make HTTP request using the connection pool.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Optional request headers
            data: Optional request data
            json: Optional JSON data
            params: Optional query parameters
            timeout: Optional request timeout override
            
        Returns:
            httpx.Response: HTTP response
            
        Raises:
            httpx.RequestError: If request fails after retries
            httpx.TimeoutException: If request times out
        """
        start_time = time.time()
        last_exception = None
        
        # Use custom timeout if provided
        request_timeout = timeout or self.timeout
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.get_client() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        json=json,
                        params=params,
                        timeout=request_timeout
                    )
                    
                    # Record successful request
                    response_time = time.time() - start_time
                    self._record_request(response_time, success=True)
                    
                    return response
            
            except httpx.TimeoutException as e:
                self._stats.timeouts += 1
                last_exception = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries + 1}): {url}")
                
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.RequestError as e:
                self._stats.connection_errors += 1
                last_exception = e
                logger.warning(f"Request error (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        response_time = time.time() - start_time
        self._record_request(response_time, success=False)
        
        if last_exception:
            raise last_exception
        else:
            raise httpx.RequestError(f"Request failed after {self.max_retries + 1} attempts")
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return await self.request("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return await self.request("DELETE", url, **kwargs)
    
    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Make PATCH request."""
        return await self.request("PATCH", url, **kwargs)
    
    def get_stats(self) -> ConnectionStats:
        """Get current connection pool statistics."""
        if self._client and hasattr(self._client, '_transport'):
            transport = self._client._transport
            if hasattr(transport, '_pool'):
                pool = transport._pool
                self._stats.active_connections = getattr(pool, '_connections_in_use', 0)
                self._stats.idle_connections = getattr(pool, '_connections_available', 0)
                self._stats.total_connections = self._stats.active_connections + self._stats.idle_connections
        
        # Calculate average response time
        if self._response_times:
            self._stats.average_response_time = sum(self._response_times) / len(self._response_times)
        
        return self._stats
    
    def is_healthy(self) -> bool:
        """Check if connection pool is healthy."""
        if not self._initialized or not self._client:
            return False
        
        stats = self.get_stats()
        
        # Check for excessive errors
        if stats.total_requests > 0:
            error_rate = (stats.connection_errors + stats.timeouts) / stats.total_requests
            if error_rate > 0.1:  # More than 10% error rate
                return False
        
        # Check for reasonable response times
        if stats.average_response_time > self.timeout * 0.8:  # Close to timeout
            return False
        
        return True
    
    async def health_check(self, url: str) -> bool:
        """
        Perform health check on a specific URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.get(url, timeout=5.0)
            return response.status_code < 500
        except Exception as e:
            logger.warning(f"Health check failed for {url}: {e}")
            return False
    
    def _record_request(self, response_time: float, success: bool) -> None:
        """Record request statistics."""
        self._stats.total_requests += 1
        
        if not success:
            self._stats.failed_connections += 1
        
        # Keep last 1000 response times for average calculation
        self._response_times.append(response_time)
        if len(self._response_times) > 1000:
            self._response_times.pop(0)
    
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        try:
            while True:
                await asyncio.sleep(60.0)  # Check every minute
                
                if not self.is_healthy():
                    logger.warning("Connection pool health check failed")
                    # Could implement recovery logic here
                
        except asyncio.CancelledError:
            logger.info("Connection pool health check cancelled")
            raise
        except Exception as e:
            logger.error(f"Health check loop error: {e}")


class PoolManager:
    """
    Manager for multiple connection pools.
    
    Allows managing separate pools for different services or endpoints
    with different configurations.
    """
    
    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
    
    def create_pool(self,
                   name: str,
                   max_connections: int = 20,
                   timeout: float = 30.0,
                   **kwargs) -> ConnectionPool:
        """
        Create a new connection pool.
        
        Args:
            name: Pool name/identifier
            max_connections: Maximum connections for this pool
            timeout: Request timeout for this pool
            **kwargs: Additional pool configuration
            
        Returns:
            ConnectionPool: Created pool
        """
        if name in self._pools:
            raise ValueError(f"Pool '{name}' already exists")
        
        pool = ConnectionPool(
            max_connections=max_connections,
            timeout=timeout,
            **kwargs
        )
        
        self._pools[name] = pool
        logger.info(f"Created connection pool '{name}'")
        
        return pool
    
    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get connection pool by name."""
        return self._pools.get(name)
    
    async def initialize_all(self) -> None:
        """Initialize all connection pools."""
        for name, pool in self._pools.items():
            try:
                await pool.initialize()
                logger.info(f"Initialized pool '{name}'")
            except Exception as e:
                logger.error(f"Failed to initialize pool '{name}': {e}")
    
    async def close_all(self) -> None:
        """Close all connection pools."""
        for name, pool in self._pools.items():
            try:
                await pool.close()
                logger.info(f"Closed pool '{name}'")
            except Exception as e:
                logger.error(f"Failed to close pool '{name}': {e}")
        
        self._pools.clear()
    
    def get_all_stats(self) -> Dict[str, ConnectionStats]:
        """Get statistics for all pools."""
        return {name: pool.get_stats() for name, pool in self._pools.items()}
    
    def is_all_healthy(self) -> bool:
        """Check if all pools are healthy."""
        return all(pool.is_healthy() for pool in self._pools.values())

