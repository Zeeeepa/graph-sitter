"""Usage tracking and cost management for autogenlib."""

import logging
import time
from typing import Dict, Any

from .config import AutogenConfig
from .exceptions import UsageLimitError
from .models import UsageStats

logger = logging.getLogger(__name__)


class UsageTracker:
    """Tracks usage statistics and manages costs."""
    
    def __init__(self, config: AutogenConfig):
        """Initialize the usage tracker.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self._stats = UsageStats(
            last_reset=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def track_request(self) -> None:
        """Track a new request."""
        if not self.config.enable_usage_tracking:
            return
        
        self._stats.total_requests += 1
        
        # Check if we're approaching usage limits
        if self._stats.estimated_cost >= self.config.usage_alert_threshold:
            logger.warning(
                f"Usage approaching threshold: ${self._stats.estimated_cost:.2f} "
                f">= ${self.config.usage_alert_threshold:.2f}"
            )
            
            # Optionally raise an error if we exceed the threshold significantly
            if self._stats.estimated_cost >= self.config.usage_alert_threshold * 1.2:
                raise UsageLimitError(
                    f"Usage limit exceeded: ${self._stats.estimated_cost:.2f}",
                    current_usage=self._stats.estimated_cost,
                    limit=self.config.usage_alert_threshold
                )
    
    def track_success(self, tokens_used: int = 0, estimated_cost: float = 0.0) -> None:
        """Track a successful request.
        
        Args:
            tokens_used: Number of tokens used in the request.
            estimated_cost: Estimated cost of the request.
        """
        if not self.config.enable_usage_tracking:
            return
        
        self._stats.successful_requests += 1
        self._stats.total_tokens += tokens_used
        self._stats.estimated_cost += estimated_cost
        
        logger.debug(f"Tracked successful request: {tokens_used} tokens, ${estimated_cost:.4f}")
    
    def track_failure(self) -> None:
        """Track a failed request."""
        if not self.config.enable_usage_tracking:
            return
        
        self._stats.failed_requests += 1
        logger.debug("Tracked failed request")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current usage statistics.
        
        Returns:
            Dictionary containing usage statistics.
        """
        return {
            "total_requests": self._stats.total_requests,
            "successful_requests": self._stats.successful_requests,
            "failed_requests": self._stats.failed_requests,
            "success_rate": (
                self._stats.successful_requests / max(self._stats.total_requests, 1) * 100
            ),
            "total_tokens": self._stats.total_tokens,
            "estimated_cost": self._stats.estimated_cost,
            "last_reset": self._stats.last_reset,
            "usage_threshold": self.config.usage_alert_threshold,
            "threshold_utilization": (
                self._stats.estimated_cost / self.config.usage_alert_threshold * 100
                if self.config.usage_alert_threshold > 0 else 0
            ),
        }
    
    def reset(self) -> None:
        """Reset usage statistics."""
        self._stats = UsageStats(
            last_reset=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        logger.info("Usage statistics reset")
    
    def export_stats(self) -> UsageStats:
        """Export current statistics as a UsageStats model.
        
        Returns:
            UsageStats object with current statistics.
        """
        return self._stats.model_copy()
    
    def import_stats(self, stats: UsageStats) -> None:
        """Import statistics from a UsageStats model.
        
        Args:
            stats: UsageStats object to import.
        """
        self._stats = stats.model_copy()
        logger.info(f"Imported usage statistics from {stats.last_reset}")
    
    def estimate_cost(self, tokens: int, model: str = "gpt-4") -> float:
        """Estimate the cost for a given number of tokens.
        
        Args:
            tokens: Number of tokens.
            model: Model name for cost calculation.
            
        Returns:
            Estimated cost in USD.
        """
        # Simple cost estimation - in practice, this would use actual pricing
        cost_per_token = {
            "gpt-4": 0.00003,  # $0.03 per 1K tokens
            "gpt-3.5-turbo": 0.000002,  # $0.002 per 1K tokens
            "claude-3": 0.000015,  # $0.015 per 1K tokens
        }
        
        rate = cost_per_token.get(model.lower(), 0.00003)  # Default to GPT-4 pricing
        return tokens * rate

