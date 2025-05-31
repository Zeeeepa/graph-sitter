"""
Configuration module for OpenEvolve Integration

This module provides configuration classes and settings for the OpenEvolve integration
with Graph-sitter, including learning parameters, database settings, and performance tuning.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class LearningConfig:
    """Configuration for continuous learning system."""
    
    # Pattern recognition settings
    min_pattern_frequency: int = 3
    pattern_confidence_threshold: float = 0.7
    max_patterns_to_track: int = 100
    
    # Adaptive algorithm settings
    learning_rate: float = 0.1
    adaptation_window: int = 50
    min_training_samples: int = 10
    
    # Model training settings
    retrain_interval_hours: int = 1
    max_training_samples: int = 1000
    model_validation_split: float = 0.2
    
    # Feature extraction settings
    feature_dimensions: List[str] = field(default_factory=lambda: [
        "complexity", "diversity", "performance", "maintainability"
    ])
    
    # Success criteria
    success_threshold: float = 0.6
    improvement_threshold: float = 0.1


@dataclass
class DatabaseConfig:
    """Configuration for database storage and management."""
    
    # Database connection settings
    database_path: str = "openevolve_integration.db"
    connection_pool_size: int = 5
    connection_timeout: int = 30
    
    # Data retention settings
    max_session_age_days: int = 30
    max_step_history: int = 10000
    cleanup_interval_hours: int = 24
    
    # Performance settings
    batch_size: int = 100
    enable_wal_mode: bool = True
    cache_size_mb: int = 100
    
    # Backup settings
    enable_backup: bool = True
    backup_interval_hours: int = 6
    max_backup_files: int = 10


@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring and optimization."""
    
    # Monitoring settings
    enable_monitoring: bool = True
    metric_collection_interval: float = 1.0
    metric_window_size: int = 100
    
    # Threshold settings
    execution_time_threshold: float = 30.0
    memory_threshold_mb: float = 1000.0
    cpu_threshold_percent: float = 80.0
    error_rate_threshold: float = 0.1
    
    # Analysis settings
    trend_analysis_window: int = 20
    bottleneck_detection_enabled: bool = True
    auto_optimization_enabled: bool = False
    
    # Reporting settings
    generate_reports: bool = True
    report_interval_minutes: int = 15
    include_recommendations: bool = True


@dataclass
class EvolutionConfig:
    """Configuration for evolution process parameters."""
    
    # Evolution settings
    max_iterations: int = 100
    population_size: int = 50
    elite_ratio: float = 0.2
    mutation_rate: float = 0.1
    
    # Code generation settings
    max_code_length: int = 10000
    enable_diff_mode: bool = True
    enable_full_rewrite: bool = False
    
    # Evaluation settings
    evaluation_timeout: float = 60.0
    parallel_evaluation: bool = True
    max_parallel_workers: int = 4
    
    # Selection settings
    selection_strategy: str = "tournament"
    tournament_size: int = 3
    diversity_weight: float = 0.3


@dataclass
class IntegrationConfig:
    """Configuration for Graph-sitter integration."""
    
    # Integration settings
    enable_graph_analysis: bool = True
    enable_symbol_tracking: bool = True
    enable_dependency_analysis: bool = True
    
    # Context capture settings
    capture_ast_context: bool = True
    capture_semantic_context: bool = True
    max_context_depth: int = 5
    
    # File processing settings
    supported_languages: List[str] = field(default_factory=lambda: [
        "python", "javascript", "typescript", "java", "cpp", "rust"
    ])
    max_file_size_mb: float = 10.0
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "*.pyc", "*.pyo", "*.pyd", "__pycache__", "node_modules", ".git"
    ])


@dataclass
class OpenEvolveConfig:
    """Main configuration class for OpenEvolve integration."""
    
    # Sub-configurations
    learning: LearningConfig = field(default_factory=LearningConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    # General settings
    debug_mode: bool = False
    log_level: str = "INFO"
    enable_telemetry: bool = True
    
    # Paths and directories
    work_directory: str = "./openevolve_work"
    log_directory: str = "./logs"
    cache_directory: str = "./cache"
    
    @property
    def database_path(self) -> str:
        """Get the full database path."""
        if os.path.isabs(self.database.database_path):
            return self.database.database_path
        return os.path.join(self.work_directory, self.database.database_path)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        for key, value in updates.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), (LearningConfig, DatabaseConfig, 
                                                 PerformanceConfig, EvolutionConfig, 
                                                 IntegrationConfig)):
                    # Update sub-configuration
                    sub_config = getattr(self, key)
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if hasattr(sub_config, sub_key):
                                setattr(sub_config, sub_key, sub_value)
                else:
                    setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "learning": self.learning.__dict__,
            "database": self.database.__dict__,
            "performance": self.performance.__dict__,
            "evolution": self.evolution.__dict__,
            "integration": self.integration.__dict__,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "enable_telemetry": self.enable_telemetry,
            "work_directory": self.work_directory,
            "log_directory": self.log_directory,
            "cache_directory": self.cache_directory
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OpenEvolveConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        # Update sub-configurations
        if "learning" in config_dict:
            for key, value in config_dict["learning"].items():
                if hasattr(config.learning, key):
                    setattr(config.learning, key, value)
        
        if "database" in config_dict:
            for key, value in config_dict["database"].items():
                if hasattr(config.database, key):
                    setattr(config.database, key, value)
        
        if "performance" in config_dict:
            for key, value in config_dict["performance"].items():
                if hasattr(config.performance, key):
                    setattr(config.performance, key, value)
        
        if "evolution" in config_dict:
            for key, value in config_dict["evolution"].items():
                if hasattr(config.evolution, key):
                    setattr(config.evolution, key, value)
        
        if "integration" in config_dict:
            for key, value in config_dict["integration"].items():
                if hasattr(config.integration, key):
                    setattr(config.integration, key, value)
        
        # Update main configuration
        for key, value in config_dict.items():
            if key not in ["learning", "database", "performance", "evolution", "integration"]:
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return config
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            file_path: Path to save the configuration file
        """
        config_dict = self.to_dict()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'OpenEvolveConfig':
        """
        Load configuration from YAML file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Loaded configuration
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        return cls.from_dict(config_dict)
    
    def validate(self) -> List[str]:
        """
        Validate configuration settings.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate learning configuration
        if self.learning.min_pattern_frequency < 1:
            errors.append("learning.min_pattern_frequency must be >= 1")
        
        if not 0 <= self.learning.pattern_confidence_threshold <= 1:
            errors.append("learning.pattern_confidence_threshold must be between 0 and 1")
        
        if self.learning.learning_rate <= 0:
            errors.append("learning.learning_rate must be > 0")
        
        # Validate database configuration
        if self.database.connection_pool_size < 1:
            errors.append("database.connection_pool_size must be >= 1")
        
        if self.database.max_session_age_days < 1:
            errors.append("database.max_session_age_days must be >= 1")
        
        # Validate performance configuration
        if self.performance.execution_time_threshold <= 0:
            errors.append("performance.execution_time_threshold must be > 0")
        
        if not 0 <= self.performance.error_rate_threshold <= 1:
            errors.append("performance.error_rate_threshold must be between 0 and 1")
        
        # Validate evolution configuration
        if self.evolution.max_iterations < 1:
            errors.append("evolution.max_iterations must be >= 1")
        
        if self.evolution.population_size < 2:
            errors.append("evolution.population_size must be >= 2")
        
        if not 0 <= self.evolution.elite_ratio <= 1:
            errors.append("evolution.elite_ratio must be between 0 and 1")
        
        # Validate integration configuration
        if self.integration.max_file_size_mb <= 0:
            errors.append("integration.max_file_size_mb must be > 0")
        
        if self.integration.max_context_depth < 1:
            errors.append("integration.max_context_depth must be >= 1")
        
        # Validate paths
        try:
            Path(self.work_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create work_directory: {e}")
        
        try:
            Path(self.log_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create log_directory: {e}")
        
        return errors
    
    def get_optimized_config(self, optimization_target: str = "performance") -> 'OpenEvolveConfig':
        """
        Get an optimized configuration for a specific target.
        
        Args:
            optimization_target: Target to optimize for ("performance", "accuracy", "memory")
            
        Returns:
            Optimized configuration
        """
        config = OpenEvolveConfig.from_dict(self.to_dict())
        
        if optimization_target == "performance":
            # Optimize for speed
            config.performance.metric_collection_interval = 2.0
            config.performance.metric_window_size = 50
            config.evolution.parallel_evaluation = True
            config.evolution.max_parallel_workers = 8
            config.database.batch_size = 200
            config.learning.retrain_interval_hours = 2
            
        elif optimization_target == "accuracy":
            # Optimize for learning accuracy
            config.learning.min_training_samples = 50
            config.learning.max_training_samples = 5000
            config.learning.model_validation_split = 0.3
            config.performance.trend_analysis_window = 50
            config.evolution.population_size = 100
            config.evolution.max_iterations = 200
            
        elif optimization_target == "memory":
            # Optimize for memory usage
            config.performance.metric_window_size = 25
            config.database.cache_size_mb = 50
            config.database.max_step_history = 5000
            config.learning.max_training_samples = 500
            config.evolution.population_size = 25
            config.integration.max_context_depth = 3
        
        return config


def load_config(config_path: Optional[str] = None) -> OpenEvolveConfig:
    """
    Load configuration from file or environment variables.
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        Loaded configuration
    """
    # Start with default configuration
    config = OpenEvolveConfig()
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        try:
            config = OpenEvolveConfig.load_from_file(config_path)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            print("Using default configuration")
    
    # Override with environment variables
    env_overrides = {}
    
    # Database settings
    if os.getenv("OPENEVOLVE_DB_PATH"):
        env_overrides.setdefault("database", {})["database_path"] = os.getenv("OPENEVOLVE_DB_PATH")
    
    # Performance settings
    if os.getenv("OPENEVOLVE_MONITORING"):
        env_overrides.setdefault("performance", {})["enable_monitoring"] = (
            os.getenv("OPENEVOLVE_MONITORING").lower() == "true"
        )
    
    # Learning settings
    if os.getenv("OPENEVOLVE_LEARNING_RATE"):
        try:
            env_overrides.setdefault("learning", {})["learning_rate"] = float(
                os.getenv("OPENEVOLVE_LEARNING_RATE")
            )
        except ValueError:
            pass
    
    # General settings
    if os.getenv("OPENEVOLVE_DEBUG"):
        env_overrides["debug_mode"] = os.getenv("OPENEVOLVE_DEBUG").lower() == "true"
    
    if os.getenv("OPENEVOLVE_LOG_LEVEL"):
        env_overrides["log_level"] = os.getenv("OPENEVOLVE_LOG_LEVEL").upper()
    
    if os.getenv("OPENEVOLVE_WORK_DIR"):
        env_overrides["work_directory"] = os.getenv("OPENEVOLVE_WORK_DIR")
    
    # Apply environment overrides
    if env_overrides:
        config.update(env_overrides)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        print("Some features may not work correctly")
    
    return config


def create_default_config_file(file_path: str) -> None:
    """
    Create a default configuration file.
    
    Args:
        file_path: Path where to create the configuration file
    """
    config = OpenEvolveConfig()
    config.save_to_file(file_path)
    print(f"Default configuration saved to {file_path}")


if __name__ == "__main__":
    # CLI for configuration management
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-default":
            output_path = sys.argv[2] if len(sys.argv) > 2 else "openevolve_config.yaml"
            create_default_config_file(output_path)
        elif sys.argv[1] == "validate":
            config_path = sys.argv[2] if len(sys.argv) > 2 else "openevolve_config.yaml"
            try:
                config = OpenEvolveConfig.load_from_file(config_path)
                errors = config.validate()
                if errors:
                    print("Validation errors:")
                    for error in errors:
                        print(f"  - {error}")
                    sys.exit(1)
                else:
                    print("Configuration is valid")
            except Exception as e:
                print(f"Error loading configuration: {e}")
                sys.exit(1)
        else:
            print("Usage: python config.py [create-default|validate] [config_file]")
    else:
        print("Usage: python config.py [create-default|validate] [config_file]")

