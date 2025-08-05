"""
OpenEvolve Integration Configuration

Configuration settings for the OpenEvolve integration layer.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class OpenEvolveConfig:
    """Configuration for OpenEvolve integration."""
    
    # Agent configuration
    evaluator_timeout_seconds: int = 30
    database_persistence_path: str = "evaluation_database.json"
    selection_strategy: str = "tournament"
    
    # Evaluation settings
    effectiveness_threshold: float = 0.75
    performance_sample_size: int = 100
    correlation_analysis_window: int = 1000
    
    # Database settings
    database_url: Optional[str] = None
    schema_path: str = "src/codegen/integration/evaluations_schema.sql"
    
    # Analysis settings
    analysis_batch_size: int = 50
    real_time_monitoring: bool = True
    metric_aggregation_interval: int = 300  # seconds
    
    # OpenEvolve agent paths (for integration)
    openevolve_repo_path: Optional[str] = None
    autogenlib_repo_path: Optional[str] = None
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_detailed_logging: bool = True
    metrics_export_format: str = "json"
    
    # Performance optimization
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    max_concurrent_evaluations: int = 10
    
    # Integration-specific settings
    component_mapping: Dict[str, str] = field(default_factory=lambda: {
        "evaluator": "evaluator_agent.agent.EvaluatorAgent",
        "database": "database_agent.agent.InMemoryDatabaseAgent", 
        "controller": "selection_controller.agent.SelectionControllerAgent"
    })
    
    @classmethod
    def from_env(cls) -> "OpenEvolveConfig":
        """Create configuration from environment variables."""
        return cls(
            evaluator_timeout_seconds=int(os.getenv("OPENEVOLVE_EVALUATOR_TIMEOUT", "30")),
            database_persistence_path=os.getenv("OPENEVOLVE_DB_PATH", "evaluation_database.json"),
            selection_strategy=os.getenv("OPENEVOLVE_SELECTION_STRATEGY", "tournament"),
            effectiveness_threshold=float(os.getenv("OPENEVOLVE_EFFECTIVENESS_THRESHOLD", "0.75")),
            performance_sample_size=int(os.getenv("OPENEVOLVE_SAMPLE_SIZE", "100")),
            correlation_analysis_window=int(os.getenv("OPENEVOLVE_CORRELATION_WINDOW", "1000")),
            database_url=os.getenv("OPENEVOLVE_DATABASE_URL"),
            schema_path=os.getenv("OPENEVOLVE_SCHEMA_PATH", "src/codegen/integration/evaluations_schema.sql"),
            analysis_batch_size=int(os.getenv("OPENEVOLVE_BATCH_SIZE", "50")),
            real_time_monitoring=os.getenv("OPENEVOLVE_REAL_TIME", "true").lower() == "true",
            metric_aggregation_interval=int(os.getenv("OPENEVOLVE_METRIC_INTERVAL", "300")),
            openevolve_repo_path=os.getenv("OPENEVOLVE_REPO_PATH"),
            autogenlib_repo_path=os.getenv("AUTOGENLIB_REPO_PATH"),
            log_level=os.getenv("OPENEVOLVE_LOG_LEVEL", "INFO"),
            enable_detailed_logging=os.getenv("OPENEVOLVE_DETAILED_LOGGING", "true").lower() == "true",
            metrics_export_format=os.getenv("OPENEVOLVE_METRICS_FORMAT", "json"),
            enable_caching=os.getenv("OPENEVOLVE_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("OPENEVOLVE_CACHE_TTL", "3600")),
            max_concurrent_evaluations=int(os.getenv("OPENEVOLVE_MAX_CONCURRENT", "10"))
        )
    
    def validate(self) -> None:
        """Validate configuration settings."""
        if self.effectiveness_threshold < 0 or self.effectiveness_threshold > 1:
            raise ValueError("effectiveness_threshold must be between 0 and 1")
        
        if self.performance_sample_size <= 0:
            raise ValueError("performance_sample_size must be positive")
        
        if self.correlation_analysis_window <= 0:
            raise ValueError("correlation_analysis_window must be positive")
        
        if self.schema_path and not Path(self.schema_path).exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "evaluator_timeout_seconds": self.evaluator_timeout_seconds,
            "database_persistence_path": self.database_persistence_path,
            "selection_strategy": self.selection_strategy,
            "effectiveness_threshold": self.effectiveness_threshold,
            "performance_sample_size": self.performance_sample_size,
            "correlation_analysis_window": self.correlation_analysis_window,
            "database_url": self.database_url,
            "schema_path": self.schema_path,
            "analysis_batch_size": self.analysis_batch_size,
            "real_time_monitoring": self.real_time_monitoring,
            "metric_aggregation_interval": self.metric_aggregation_interval,
            "openevolve_repo_path": self.openevolve_repo_path,
            "autogenlib_repo_path": self.autogenlib_repo_path,
            "log_level": self.log_level,
            "enable_detailed_logging": self.enable_detailed_logging,
            "metrics_export_format": self.metrics_export_format,
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_concurrent_evaluations": self.max_concurrent_evaluations,
            "component_mapping": self.component_mapping
        }

