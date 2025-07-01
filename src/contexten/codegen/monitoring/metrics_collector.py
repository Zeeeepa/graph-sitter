"""
Metrics collection and analysis for Codegen SDK integration.

This module provides comprehensive metrics collection to monitor
performance, usage patterns, and system health.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque


logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    request_id: str
    timestamp: float
    prompt_tokens: int
    context_tokens: int
    total_tokens: int
    response_time: float
    status: str
    error: Optional[str] = None
    context_enhanced: bool = False
    cache_hit: bool = False


@dataclass
class AggregatedMetrics:
    """Aggregated metrics over a time period."""
    period_start: float
    period_end: float
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    context_enhanced_requests: int = 0
    error_counts: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        return self.total_response_time / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return self.cache_hits / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def context_enhancement_rate(self) -> float:
        """Calculate context enhancement rate."""
        return self.context_enhanced_requests / self.total_requests if self.total_requests > 0 else 0.0


class MetricsCollector:
    """
    Comprehensive metrics collector for Codegen SDK integration.
    
    Collects and analyzes:
    - Request/response metrics
    - Performance metrics
    - Usage patterns
    - Error tracking
    - Cost metrics
    """
    
    def __init__(self,
                 enable_cost_tracking: bool = True,
                 export_interval: int = 60,
                 retention_days: int = 30):
        """
        Initialize metrics collector.
        
        Args:
            enable_cost_tracking: Whether to track cost metrics
            export_interval: How often to export metrics (seconds)
            retention_days: How long to retain detailed metrics
        """
        self.enable_cost_tracking = enable_cost_tracking
        self.export_interval = export_interval
        self.retention_days = retention_days
        
        # Raw metrics storage
        self._request_metrics: deque = deque(maxlen=10000)  # Last 10k requests
        self._hourly_aggregates: Dict[str, AggregatedMetrics] = {}
        self._daily_aggregates: Dict[str, AggregatedMetrics] = {}
        
        # Real-time metrics
        self._current_metrics = {
            "requests_per_minute": deque(maxlen=60),
            "response_times": deque(maxlen=1000),
            "error_rates": deque(maxlen=100),
            "token_usage": deque(maxlen=1000),
            "active_requests": 0
        }
        
        # Error tracking
        self._error_patterns: Dict[str, int] = defaultdict(int)
        self._recent_errors: deque = deque(maxlen=100)
        
        # Performance tracking
        self._performance_metrics = {
            "p50_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
            "requests_per_second": 0.0,
            "tokens_per_second": 0.0,
            "error_rate": 0.0
        }
        
        # Export task
        self._export_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the metrics collector."""
        if self._initialized:
            return
        
        # Start export task
        self._export_task = asyncio.create_task(self._export_loop())
        
        self._initialized = True
        logger.info("Metrics collector initialized")
    
    async def record_request(self, request: Any, response: Any) -> None:
        """
        Record metrics for a request/response pair.
        
        Args:
            request: Request object
            response: Response object
        """
        try:
            # Extract metrics from request/response
            metrics = RequestMetrics(
                request_id=getattr(request, 'request_id', 'unknown'),
                timestamp=time.time(),
                prompt_tokens=self._count_prompt_tokens(request),
                context_tokens=self._count_context_tokens(request),
                total_tokens=self._count_total_tokens(request, response),
                response_time=getattr(response, 'response_time', 0.0),
                status=getattr(response, 'status', 'unknown'),
                error=getattr(response, 'error', None),
                context_enhanced=getattr(response.metadata, 'context_enhanced', False) if hasattr(response, 'metadata') else False,
                cache_hit=getattr(response, 'cache_hit', False)
            )
            
            # Store raw metrics
            self._request_metrics.append(metrics)
            
            # Update real-time metrics
            await self._update_realtime_metrics(metrics)
            
            # Update aggregates
            await self._update_aggregates(metrics)
            
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    async def record_error(self, request_id: str, error: str) -> None:
        """
        Record an error for tracking.
        
        Args:
            request_id: Request ID that failed
            error: Error message
        """
        try:
            error_info = {
                "request_id": request_id,
                "error": error,
                "timestamp": time.time()
            }
            
            self._recent_errors.append(error_info)
            self._error_patterns[error] += 1
            
            logger.debug(f"Recorded error for request {request_id}: {error}")
            
        except Exception as e:
            logger.error(f"Failed to record error: {e}")
    
    async def record_completion(self, request_id: str, response: Any) -> None:
        """
        Record completion metrics for a request.
        
        Args:
            request_id: Request ID that completed
            response: Response object
        """
        try:
            # Update active request count
            self._current_metrics["active_requests"] = max(0, self._current_metrics["active_requests"] - 1)
            
            # Record completion time if available
            if hasattr(response, 'completed_at') and hasattr(response, 'created_at'):
                completion_time = (response.completed_at - response.created_at).total_seconds()
                self._current_metrics["response_times"].append(completion_time)
            
        except Exception as e:
            logger.error(f"Failed to record completion: {e}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics."""
        try:
            # Calculate current performance metrics
            response_times = list(self._current_metrics["response_times"])
            
            if response_times:
                sorted_times = sorted(response_times)
                n = len(sorted_times)
                
                self._performance_metrics["p50_response_time"] = sorted_times[int(n * 0.5)]
                self._performance_metrics["p95_response_time"] = sorted_times[int(n * 0.95)]
                self._performance_metrics["p99_response_time"] = sorted_times[int(n * 0.99)]
            
            # Calculate rates
            now = time.time()
            recent_requests = [
                m for m in self._request_metrics
                if now - m.timestamp < 60  # Last minute
            ]
            
            self._performance_metrics["requests_per_second"] = len(recent_requests) / 60.0
            
            if recent_requests:
                total_tokens = sum(m.total_tokens for m in recent_requests)
                self._performance_metrics["tokens_per_second"] = total_tokens / 60.0
                
                failed_requests = sum(1 for m in recent_requests if m.status == 'failed')
                self._performance_metrics["error_rate"] = failed_requests / len(recent_requests)
            
            return {
                "performance": self._performance_metrics.copy(),
                "active_requests": self._current_metrics["active_requests"],
                "total_requests": len(self._request_metrics),
                "recent_errors": len(self._recent_errors),
                "error_patterns": dict(self._error_patterns),
                "cache_stats": self._get_cache_stats(),
                "token_usage": self._get_token_usage_stats()
            }
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {}
    
    def get_aggregated_metrics(self, 
                             period: str = "hour",
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> List[AggregatedMetrics]:
        """
        Get aggregated metrics for a time period.
        
        Args:
            period: Aggregation period ("hour" or "day")
            start_time: Start time for metrics
            end_time: End time for metrics
            
        Returns:
            List of aggregated metrics
        """
        try:
            if period == "hour":
                aggregates = self._hourly_aggregates
            elif period == "day":
                aggregates = self._daily_aggregates
            else:
                raise ValueError(f"Invalid period: {period}")
            
            # Filter by time range if provided
            if start_time or end_time:
                filtered_aggregates = []
                for key, aggregate in aggregates.items():
                    aggregate_time = datetime.fromtimestamp(aggregate.period_start)
                    
                    if start_time and aggregate_time < start_time:
                        continue
                    if end_time and aggregate_time > end_time:
                        continue
                    
                    filtered_aggregates.append(aggregate)
                
                return sorted(filtered_aggregates, key=lambda x: x.period_start)
            
            return sorted(aggregates.values(), key=lambda x: x.period_start)
            
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            return []
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Get detailed error analysis."""
        try:
            total_errors = sum(self._error_patterns.values())
            
            # Top error patterns
            top_errors = sorted(
                self._error_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Recent error timeline
            now = time.time()
            recent_errors = [
                e for e in self._recent_errors
                if now - e["timestamp"] < 3600  # Last hour
            ]
            
            # Error rate over time
            error_timeline = defaultdict(int)
            for error in recent_errors:
                hour_key = int(error["timestamp"] // 3600)
                error_timeline[hour_key] += 1
            
            return {
                "total_errors": total_errors,
                "unique_error_types": len(self._error_patterns),
                "top_errors": top_errors,
                "recent_errors_count": len(recent_errors),
                "error_timeline": dict(error_timeline)
            }
            
        except Exception as e:
            logger.error(f"Failed to get error analysis: {e}")
            return {}
    
    async def shutdown(self) -> None:
        """Shutdown the metrics collector."""
        logger.info("Shutting down metrics collector")
        
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
        
        # Final export
        await self._export_metrics()
        
        logger.info("Metrics collector shutdown complete")
    
    # Private methods
    
    async def _update_realtime_metrics(self, metrics: RequestMetrics) -> None:
        """Update real-time metrics."""
        # Update active requests
        self._current_metrics["active_requests"] += 1
        
        # Update response times
        self._current_metrics["response_times"].append(metrics.response_time)
        
        # Update token usage
        self._current_metrics["token_usage"].append(metrics.total_tokens)
        
        # Update requests per minute
        minute_key = int(metrics.timestamp // 60)
        self._current_metrics["requests_per_minute"].append(minute_key)
    
    async def _update_aggregates(self, metrics: RequestMetrics) -> None:
        """Update aggregated metrics."""
        # Hourly aggregates
        hour_key = datetime.fromtimestamp(metrics.timestamp).strftime("%Y-%m-%d-%H")
        if hour_key not in self._hourly_aggregates:
            hour_start = int(metrics.timestamp // 3600) * 3600
            self._hourly_aggregates[hour_key] = AggregatedMetrics(
                period_start=hour_start,
                period_end=hour_start + 3600
            )
        
        hourly = self._hourly_aggregates[hour_key]
        self._update_aggregate(hourly, metrics)
        
        # Daily aggregates
        day_key = datetime.fromtimestamp(metrics.timestamp).strftime("%Y-%m-%d")
        if day_key not in self._daily_aggregates:
            day_start = int(metrics.timestamp // 86400) * 86400
            self._daily_aggregates[day_key] = AggregatedMetrics(
                period_start=day_start,
                period_end=day_start + 86400
            )
        
        daily = self._daily_aggregates[day_key]
        self._update_aggregate(daily, metrics)
    
    def _update_aggregate(self, aggregate: AggregatedMetrics, metrics: RequestMetrics) -> None:
        """Update a single aggregate with new metrics."""
        aggregate.total_requests += 1
        aggregate.total_tokens += metrics.total_tokens
        aggregate.total_response_time += metrics.response_time
        
        if metrics.status == "completed":
            aggregate.successful_requests += 1
        elif metrics.status == "failed":
            aggregate.failed_requests += 1
        
        if metrics.cache_hit:
            aggregate.cache_hits += 1
        
        if metrics.context_enhanced:
            aggregate.context_enhanced_requests += 1
        
        if metrics.error:
            aggregate.error_counts[metrics.error] = aggregate.error_counts.get(metrics.error, 0) + 1
    
    def _count_prompt_tokens(self, request: Any) -> int:
        """Count tokens in the prompt."""
        try:
            if hasattr(request, 'prompt'):
                # Simple estimation - would use proper tokenizer in production
                return len(request.prompt.split()) * 1.3  # Rough estimate
            return 0
        except:
            return 0
    
    def _count_context_tokens(self, request: Any) -> int:
        """Count tokens in the context."""
        try:
            if hasattr(request, 'context') and request.context:
                # Simple estimation
                context_text = str(request.context)
                return len(context_text.split()) * 1.3
            return 0
        except:
            return 0
    
    def _count_total_tokens(self, request: Any, response: Any) -> int:
        """Count total tokens used."""
        try:
            prompt_tokens = self._count_prompt_tokens(request)
            context_tokens = self._count_context_tokens(request)
            
            # Add response tokens if available
            response_tokens = 0
            if hasattr(response, 'result') and response.result:
                response_tokens = len(str(response.result).split()) * 1.3
            
            return int(prompt_tokens + context_tokens + response_tokens)
        except:
            return 0
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache-related statistics."""
        recent_requests = list(self._request_metrics)[-1000:]  # Last 1000 requests
        
        if not recent_requests:
            return {"cache_hit_rate": 0.0, "cache_hits": 0, "total_requests": 0}
        
        cache_hits = sum(1 for m in recent_requests if m.cache_hit)
        
        return {
            "cache_hit_rate": cache_hits / len(recent_requests),
            "cache_hits": cache_hits,
            "total_requests": len(recent_requests)
        }
    
    def _get_token_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        recent_requests = list(self._request_metrics)[-1000:]  # Last 1000 requests
        
        if not recent_requests:
            return {}
        
        token_counts = [m.total_tokens for m in recent_requests]
        
        return {
            "total_tokens": sum(token_counts),
            "average_tokens": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "median_tokens": sorted(token_counts)[len(token_counts) // 2]
        }
    
    async def _export_loop(self) -> None:
        """Background export loop."""
        try:
            while True:
                await asyncio.sleep(self.export_interval)
                await self._export_metrics()
        except asyncio.CancelledError:
            logger.info("Metrics export loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Metrics export loop error: {e}")
    
    async def _export_metrics(self) -> None:
        """Export metrics to external systems."""
        try:
            # This would export to monitoring systems like Prometheus, DataDog, etc.
            # For now, just log summary
            current_metrics = self.get_current_metrics()
            
            logger.info(f"Metrics summary: "
                       f"RPS={current_metrics['performance']['requests_per_second']:.2f}, "
                       f"P95={current_metrics['performance']['p95_response_time']:.2f}s, "
                       f"Errors={current_metrics['performance']['error_rate']:.2%}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

