"""
Rate limiting implementation for Codegen SDK requests.

This module provides intelligent rate limiting to respect API limits while
maximizing throughput and preventing rate limit violations.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from collections import deque


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float
    burst_limit: int
    window_size: float = 1.0  # seconds
    backoff_factor: float = 2.0
    max_backoff: float = 60.0  # seconds


class TokenBucket:
    """
    Token bucket implementation for rate limiting.
    
    Allows burst requests up to the bucket capacity while maintaining
    a steady rate of token replenishment.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Rate at which tokens are added (tokens per second)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens available
        """
        async with self._lock:
            now = time.time()
            
            # Add tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> float:
        """
        Calculate how long to wait for tokens to be available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time to wait in seconds
        """
        async with self._lock:
            now = time.time()
            
            # Add tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            
            if self.tokens >= tokens:
                return 0.0
            
            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate
            
            return wait_time
    
    def get_available_tokens(self) -> float:
        """Get the current number of available tokens."""
        now = time.time()
        elapsed = now - self.last_refill
        return min(self.capacity, self.tokens + elapsed * self.refill_rate)


class RateLimiter:
    """
    Advanced rate limiter with adaptive backoff and burst handling.
    
    Features:
    - Token bucket algorithm for smooth rate limiting
    - Adaptive backoff on rate limit violations
    - Request queuing with priority support
    - Metrics collection for monitoring
    """
    
    def __init__(self, 
                 requests_per_second: float = 5.0,
                 burst_limit: int = 10,
                 adaptive_backoff: bool = True):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            burst_limit: Maximum burst requests allowed
            adaptive_backoff: Whether to use adaptive backoff on violations
        """
        self.config = RateLimitConfig(
            requests_per_second=requests_per_second,
            burst_limit=burst_limit
        )
        
        self.token_bucket = TokenBucket(burst_limit, requests_per_second)
        self.adaptive_backoff = adaptive_backoff
        
        # Backoff state
        self.current_backoff = 0.0
        self.last_violation = 0.0
        self.violation_count = 0
        
        # Request queue for handling bursts
        self.request_queue = asyncio.Queue()
        self.queue_processor_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "average_wait_time": 0.0,
            "current_queue_size": 0,
            "violations": 0,
            "backoff_time": 0.0
        }
        
        self._request_times = deque(maxlen=1000)  # Track recent request times
        self._wait_times = deque(maxlen=1000)  # Track wait times
        
        # Start queue processor
        self._start_queue_processor()
    
    async def acquire(self, priority: int = 1) -> None:
        """
        Acquire permission to make a request.
        
        Args:
            priority: Request priority (1 = highest, 5 = lowest)
        """
        start_time = time.time()
        
        # Check if we can proceed immediately
        if await self.token_bucket.consume():
            self._record_request(start_time, 0.0)
            return
        
        # Need to wait - add to queue
        future = asyncio.Future()
        await self.request_queue.put((priority, start_time, future))
        self.metrics["current_queue_size"] = self.request_queue.qsize()
        
        # Wait for permission
        await future
        
        wait_time = time.time() - start_time
        self._record_request(start_time, wait_time)
    
    async def acquire_multiple(self, count: int, priority: int = 1) -> None:
        """
        Acquire permission for multiple requests.
        
        Args:
            count: Number of requests to acquire
            priority: Request priority
        """
        for _ in range(count):
            await self.acquire(priority)
    
    def record_violation(self) -> None:
        """Record a rate limit violation for adaptive backoff."""
        if not self.adaptive_backoff:
            return
        
        now = time.time()
        self.last_violation = now
        self.violation_count += 1
        self.metrics["violations"] += 1
        
        # Calculate adaptive backoff
        if self.current_backoff == 0:
            self.current_backoff = 1.0
        else:
            self.current_backoff = min(
                self.current_backoff * self.config.backoff_factor,
                self.config.max_backoff
            )
        
        self.metrics["backoff_time"] = self.current_backoff
        
        logger.warning(f"Rate limit violation detected. Backoff: {self.current_backoff}s")
    
    def reset_backoff(self) -> None:
        """Reset adaptive backoff after successful requests."""
        if self.current_backoff > 0:
            logger.info("Resetting rate limit backoff")
            self.current_backoff = 0.0
            self.metrics["backoff_time"] = 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current rate limiting metrics."""
        # Update dynamic metrics
        self.metrics["current_queue_size"] = self.request_queue.qsize()
        self.metrics["available_tokens"] = self.token_bucket.get_available_tokens()
        
        # Calculate average wait time
        if self._wait_times:
            self.metrics["average_wait_time"] = sum(self._wait_times) / len(self._wait_times)
        
        # Calculate current request rate
        now = time.time()
        recent_requests = [t for t in self._request_times if now - t < 60.0]  # Last minute
        self.metrics["current_request_rate"] = len(recent_requests) / 60.0
        
        return self.metrics.copy()
    
    def is_healthy(self) -> bool:
        """Check if rate limiter is operating normally."""
        return (
            self.queue_processor_task is not None and
            not self.queue_processor_task.done() and
            self.request_queue.qsize() < self.config.burst_limit * 2
        )
    
    async def shutdown(self) -> None:
        """Shutdown the rate limiter and cleanup resources."""
        logger.info("Shutting down rate limiter")
        
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Process remaining queue items
        while not self.request_queue.empty():
            try:
                _, _, future = await asyncio.wait_for(self.request_queue.get(), timeout=0.1)
                if not future.done():
                    future.set_exception(RuntimeError("Rate limiter shutting down"))
            except asyncio.TimeoutError:
                break
    
    def _start_queue_processor(self) -> None:
        """Start the background queue processor."""
        self.queue_processor_task = asyncio.create_task(self._process_queue())
    
    async def _process_queue(self) -> None:
        """Process the request queue in priority order."""
        try:
            while True:
                # Get next request from queue (blocks if empty)
                priority, start_time, future = await self.request_queue.get()
                
                if future.done():
                    continue
                
                try:
                    # Wait for tokens to be available
                    wait_time = await self.token_bucket.wait_for_tokens()
                    
                    # Apply adaptive backoff if needed
                    if self.current_backoff > 0:
                        wait_time = max(wait_time, self.current_backoff)
                    
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    
                    # Consume token and grant permission
                    if await self.token_bucket.consume():
                        future.set_result(None)
                        self.metrics["current_queue_size"] = self.request_queue.qsize()
                    else:
                        # This shouldn't happen, but handle gracefully
                        logger.warning("Failed to consume token after waiting")
                        await asyncio.sleep(0.1)  # Brief delay before retry
                        await self.request_queue.put((priority, start_time, future))
                
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                    logger.error(f"Error processing rate limit queue: {e}")
        
        except asyncio.CancelledError:
            logger.info("Rate limiter queue processor cancelled")
            raise
        except Exception as e:
            logger.error(f"Rate limiter queue processor error: {e}")
    
    def _record_request(self, start_time: float, wait_time: float) -> None:
        """Record request metrics."""
        now = time.time()
        
        self.metrics["total_requests"] += 1
        if wait_time > 0:
            self.metrics["rate_limited_requests"] += 1
        
        self._request_times.append(now)
        self._wait_times.append(wait_time)
        
        # Reset backoff on successful requests
        if self.current_backoff > 0 and wait_time < self.current_backoff:
            # Gradually reduce backoff
            self.current_backoff *= 0.9
            if self.current_backoff < 0.1:
                self.reset_backoff()


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts to API response patterns.
    
    Automatically adjusts rate limits based on:
    - Response times
    - Error rates
    - Server-provided rate limit headers
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_times = deque(maxlen=100)
        self.error_rates = deque(maxlen=100)
        self.last_adjustment = time.time()
        self.adjustment_interval = 60.0  # seconds
    
    def record_response(self, response_time: float, is_error: bool, 
                       rate_limit_headers: Optional[Dict[str, str]] = None) -> None:
        """
        Record API response for adaptive adjustment.
        
        Args:
            response_time: Response time in seconds
            is_error: Whether the response was an error
            rate_limit_headers: Rate limit headers from API response
        """
        self.response_times.append(response_time)
        self.error_rates.append(1.0 if is_error else 0.0)
        
        # Parse rate limit headers if provided
        if rate_limit_headers:
            self._parse_rate_limit_headers(rate_limit_headers)
        
        # Check if we should adjust rate limits
        now = time.time()
        if now - self.last_adjustment > self.adjustment_interval:
            self._adjust_rate_limits()
            self.last_adjustment = now
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> None:
        """Parse rate limit headers and adjust accordingly."""
        # Common rate limit header patterns
        remaining = headers.get("x-ratelimit-remaining") or headers.get("x-rate-limit-remaining")
        reset_time = headers.get("x-ratelimit-reset") or headers.get("x-rate-limit-reset")
        
        if remaining is not None:
            try:
                remaining_requests = int(remaining)
                if remaining_requests < 5:  # Low remaining requests
                    self.record_violation()
            except ValueError:
                pass
    
    def _adjust_rate_limits(self) -> None:
        """Adjust rate limits based on recent performance."""
        if not self.response_times or not self.error_rates:
            return
        
        avg_response_time = sum(self.response_times) / len(self.response_times)
        error_rate = sum(self.error_rates) / len(self.error_rates)
        
        # Adjust based on performance
        if error_rate > 0.1:  # High error rate
            # Reduce rate limit
            new_rate = self.config.requests_per_second * 0.8
            logger.info(f"Reducing rate limit due to high error rate: {new_rate}")
        elif avg_response_time > 5.0:  # Slow responses
            # Reduce rate limit
            new_rate = self.config.requests_per_second * 0.9
            logger.info(f"Reducing rate limit due to slow responses: {new_rate}")
        elif error_rate < 0.01 and avg_response_time < 1.0:  # Good performance
            # Gradually increase rate limit
            new_rate = min(
                self.config.requests_per_second * 1.1,
                self.config.requests_per_second * 2.0  # Don't exceed 2x original
            )
            logger.info(f"Increasing rate limit due to good performance: {new_rate}")
        else:
            return  # No adjustment needed
        
        # Update rate limit
        self.config.requests_per_second = new_rate
        self.token_bucket.refill_rate = new_rate

