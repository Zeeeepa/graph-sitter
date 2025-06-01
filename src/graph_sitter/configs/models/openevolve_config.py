"""OpenEvolve configuration for continuous learning integration."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field

from graph_sitter.configs.models.base_config import BaseConfig


class OpenEvolveConfig(BaseConfig):
    """Configuration for OpenEvolve integration."""

    api_url: str = Field(
        default="https://api.openevolve.com",
        description="OpenEvolve API base URL"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="OpenEvolve API key for authentication"
    )
    
    timeout: int = Field(
        default=30000,
        description="Request timeout in milliseconds"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests"
    )
    
    evaluation_triggers: List[str] = Field(
        default_factory=lambda: [
            "task_failure",
            "pipeline_failure", 
            "performance_degradation"
        ],
        description="List of events that trigger evaluations"
    )
    
    batch_size: int = Field(
        default=10,
        description="Number of evaluations to process in a batch"
    )
    
    evaluation_queue_size: int = Field(
        default=100,
        description="Maximum size of the evaluation queue"
    )
    
    enable_auto_evaluation: bool = Field(
        default=True,
        description="Whether to automatically trigger evaluations"
    )
    
    min_evaluation_interval: int = Field(
        default=300,
        description="Minimum interval between evaluations in seconds"
    )

    def __init__(self, env_filepath: Path | None = None, **kwargs) -> None:
        super().__init__(prefix="OPENEVOLVE", env_filepath=env_filepath, **kwargs)

    @property
    def is_configured(self) -> bool:
        """Check if OpenEvolve is properly configured."""
        return self.api_key is not None and len(self.api_key.strip()) > 0

