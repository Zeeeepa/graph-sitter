"""
Cost tracking and optimization for Codegen SDK integration.

This module provides cost tracking capabilities to monitor and optimize
API usage costs and resource consumption.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class CostMetrics:
    """Cost metrics for tracking API usage."""
    total_requests: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    period_start: datetime = None
    period_end: datetime = None


class CostTracker:
    """
    Cost tracking and optimization for Codegen SDK usage.
    
    Tracks and analyzes:
    - Token usage costs
    - Request volume costs
    - Cost optimization opportunities
    - Budget monitoring and alerts
    """
    
    def __init__(self, cost_per_token: float = 0.0001):
        """
        Initialize cost tracker.
        
        Args:
            cost_per_token: Estimated cost per token
        """
        self.cost_per_token = cost_per_token
        self.metrics = CostMetrics()
    
    async def track_request_cost(self, tokens_used: int) -> float:
        """
        Track cost for a request.
        
        Args:
            tokens_used: Number of tokens used
            
        Returns:
            Estimated cost for this request
        """
        cost = tokens_used * self.cost_per_token
        
        self.metrics.total_requests += 1
        self.metrics.total_tokens += tokens_used
        self.metrics.estimated_cost += cost
        
        return cost
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "total_requests": self.metrics.total_requests,
            "total_tokens": self.metrics.total_tokens,
            "estimated_cost": self.metrics.estimated_cost,
            "average_cost_per_request": (
                self.metrics.estimated_cost / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0.0
            ),
            "average_tokens_per_request": (
                self.metrics.total_tokens / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0.0
            )
        }

