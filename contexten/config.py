"""
Configuration management for the Enhanced Orchestrator
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import logging


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "contexten"
    username: str = "contexten_user"
    password: str = ""
    ssl_mode: str = "prefer"


@dataclass
class MemoryConfig:
    """Memory management configuration"""
    backend: str = "persistent"
    retention_days: int = 30
    optimization_enabled: bool = True
    cache_size_limit: int = 1000
    db_path: str = "contexten_memory.db"


@dataclass
class EventConfig:
    """Event evaluation configuration"""
    monitoring_enabled: bool = True
    classification_threshold: float = 0.8
    real_time_processing: bool = True
    max_event_history: int = 10000


@dataclass
class CICDConfig:
    """CI/CD configuration"""
    enabled: bool = True
    auto_healing: bool = True
    continuous_optimization: bool = True
    config_path: str = "contexten_cicd_config.yaml"


@dataclass
class SDKPythonConfig:
    """SDK-Python integration configuration"""
    enabled: bool = True
    default_provider: str = "bedrock"
    default_model: str = "us.amazon.nova-pro-v1:0"
    default_temperature: float = 0.3
    max_agents: int = 100


@dataclass
class StrandsAgentsConfig:
    """Strands-Agents integration configuration"""
    enabled: bool = True
    memory_backend: str = "mem0"
    python_timeout: int = 120
    shell_confirmation_required: bool = True
    max_executions_history: int = 1000


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class SecurityConfig:
    """Security configuration"""
    api_key_required: bool = True
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    allowed_hosts: list = None
    encryption_key: Optional[str] = None


@dataclass
class ContextenConfig:
    """Main configuration for the Enhanced Orchestrator"""
    
    # Core settings
    environment: str = "development"
    debug: bool = False
    max_parallel_tasks: int = 10
    task_timeout_seconds: int = 300
    
    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    memory: MemoryConfig = MemoryConfig()
    events: EventConfig = EventConfig()
    cicd: CICDConfig = CICDConfig()
    sdk_python: SDKPythonConfig = SDKPythonConfig()
    strands_agents: StrandsAgentsConfig = StrandsAgentsConfig()
    logging: LoggingConfig = LoggingConfig()
    security: SecurityConfig = SecurityConfig()
    
    # Custom settings
    custom: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom is None:
            self.custom = {}
        if self.security.allowed_hosts is None:
            self.security.allowed_hosts = ["localhost", "127.0.0.1"]


class ConfigManager:
    """Configuration manager for the Enhanced Orchestrator"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        self.config_path = config_path or self._get_default_config_path()
        self.config: ContextenConfig = ContextenConfig()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Check environment variable first
        if "CONTEXTEN_CONFIG" in os.environ:
            return os.environ["CONTEXTEN_CONFIG"]
        
        # Check common locations
        possible_paths = [
            "contexten_config.yaml",
            "config/contexten.yaml",
            os.path.expanduser("~/.contexten/config.yaml"),
            "/etc/contexten/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Default to current directory
        return "contexten_config.yaml"
    
    def load_config(self) -> ContextenConfig:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                # Update configuration with loaded data
                self._update_config_from_dict(config_data)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.info(f"Configuration file {self.config_path} not found, using defaults")
            
            # Override with environment variables
            self._load_from_environment()
            
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.logger.info("Using default configuration")
            return self.config
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        
        # Update main settings
        if "environment" in config_data:
            self.config.environment = config_data["environment"]
        if "debug" in config_data:
            self.config.debug = config_data["debug"]
        if "max_parallel_tasks" in config_data:
            self.config.max_parallel_tasks = config_data["max_parallel_tasks"]
        if "task_timeout_seconds" in config_data:
            self.config.task_timeout_seconds = config_data["task_timeout_seconds"]
        
        # Update component configurations
        if "database" in config_data:
            self._update_dataclass_from_dict(self.config.database, config_data["database"])
        
        if "memory" in config_data:
            self._update_dataclass_from_dict(self.config.memory, config_data["memory"])
        
        if "events" in config_data:
            self._update_dataclass_from_dict(self.config.events, config_data["events"])
        
        if "cicd" in config_data:
            self._update_dataclass_from_dict(self.config.cicd, config_data["cicd"])
        
        if "sdk_python" in config_data:
            self._update_dataclass_from_dict(self.config.sdk_python, config_data["sdk_python"])
        
        if "strands_agents" in config_data:
            self._update_dataclass_from_dict(self.config.strands_agents, config_data["strands_agents"])
        
        if "logging" in config_data:
            self._update_dataclass_from_dict(self.config.logging, config_data["logging"])
        
        if "security" in config_data:
            self._update_dataclass_from_dict(self.config.security, config_data["security"])
        
        # Update custom settings
        if "custom" in config_data:
            self.config.custom.update(config_data["custom"])
    
    def _update_dataclass_from_dict(self, dataclass_instance, data: Dict[str, Any]):
        """Update dataclass instance from dictionary"""
        for key, value in data.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        
        # Main settings
        if "CONTEXTEN_ENVIRONMENT" in os.environ:
            self.config.environment = os.environ["CONTEXTEN_ENVIRONMENT"]
        
        if "CONTEXTEN_DEBUG" in os.environ:
            self.config.debug = os.environ["CONTEXTEN_DEBUG"].lower() in ("true", "1", "yes")
        
        if "CONTEXTEN_MAX_PARALLEL_TASKS" in os.environ:
            self.config.max_parallel_tasks = int(os.environ["CONTEXTEN_MAX_PARALLEL_TASKS"])
        
        # Database settings
        if "CONTEXTEN_DB_HOST" in os.environ:
            self.config.database.host = os.environ["CONTEXTEN_DB_HOST"]
        
        if "CONTEXTEN_DB_PORT" in os.environ:
            self.config.database.port = int(os.environ["CONTEXTEN_DB_PORT"])
        
        if "CONTEXTEN_DB_NAME" in os.environ:
            self.config.database.database = os.environ["CONTEXTEN_DB_NAME"]
        
        if "CONTEXTEN_DB_USER" in os.environ:
            self.config.database.username = os.environ["CONTEXTEN_DB_USER"]
        
        if "CONTEXTEN_DB_PASSWORD" in os.environ:
            self.config.database.password = os.environ["CONTEXTEN_DB_PASSWORD"]
        
        # Memory settings
        if "CONTEXTEN_MEMORY_BACKEND" in os.environ:
            self.config.memory.backend = os.environ["CONTEXTEN_MEMORY_BACKEND"]
        
        if "CONTEXTEN_MEMORY_RETENTION_DAYS" in os.environ:
            self.config.memory.retention_days = int(os.environ["CONTEXTEN_MEMORY_RETENTION_DAYS"])
        
        # SDK-Python settings
        if "CONTEXTEN_SDK_PYTHON_ENABLED" in os.environ:
            self.config.sdk_python.enabled = os.environ["CONTEXTEN_SDK_PYTHON_ENABLED"].lower() in ("true", "1", "yes")
        
        if "CONTEXTEN_SDK_PYTHON_DEFAULT_PROVIDER" in os.environ:
            self.config.sdk_python.default_provider = os.environ["CONTEXTEN_SDK_PYTHON_DEFAULT_PROVIDER"]
        
        # Strands-Agents settings
        if "CONTEXTEN_STRANDS_AGENTS_ENABLED" in os.environ:
            self.config.strands_agents.enabled = os.environ["CONTEXTEN_STRANDS_AGENTS_ENABLED"].lower() in ("true", "1", "yes")
        
        # Logging settings
        if "CONTEXTEN_LOG_LEVEL" in os.environ:
            self.config.logging.level = os.environ["CONTEXTEN_LOG_LEVEL"]
        
        if "CONTEXTEN_LOG_FILE" in os.environ:
            self.config.logging.file_path = os.environ["CONTEXTEN_LOG_FILE"]
        
        # Security settings
        if "CONTEXTEN_API_KEY_REQUIRED" in os.environ:
            self.config.security.api_key_required = os.environ["CONTEXTEN_API_KEY_REQUIRED"].lower() in ("true", "1", "yes")
        
        if "CONTEXTEN_ENCRYPTION_KEY" in os.environ:
            self.config.security.encryption_key = os.environ["CONTEXTEN_ENCRYPTION_KEY"]
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """Save configuration to file"""
        try:
            save_path = config_path or self.config_path
            
            # Convert configuration to dictionary
            config_dict = asdict(self.config)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save configuration
            with open(save_path, 'w') as f:
                if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_config(self) -> ContextenConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            self._update_config_from_dict(updates)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """Validate configuration"""
        errors = []
        
        # Validate basic settings
        if self.config.max_parallel_tasks <= 0:
            errors.append("max_parallel_tasks must be greater than 0")
        
        if self.config.task_timeout_seconds <= 0:
            errors.append("task_timeout_seconds must be greater than 0")
        
        # Validate database configuration
        if not self.config.database.host:
            errors.append("database.host is required")
        
        if self.config.database.port <= 0 or self.config.database.port > 65535:
            errors.append("database.port must be between 1 and 65535")
        
        # Validate memory configuration
        if self.config.memory.retention_days <= 0:
            errors.append("memory.retention_days must be greater than 0")
        
        if self.config.memory.cache_size_limit <= 0:
            errors.append("memory.cache_size_limit must be greater than 0")
        
        # Validate event configuration
        if not 0 <= self.config.events.classification_threshold <= 1:
            errors.append("events.classification_threshold must be between 0 and 1")
        
        if self.config.events.max_event_history <= 0:
            errors.append("events.max_event_history must be greater than 0")
        
        # Validate SDK-Python configuration
        if self.config.sdk_python.max_agents <= 0:
            errors.append("sdk_python.max_agents must be greater than 0")
        
        if not 0 <= self.config.sdk_python.default_temperature <= 2:
            errors.append("sdk_python.default_temperature must be between 0 and 2")
        
        # Validate security configuration
        if self.config.security.max_requests_per_minute <= 0:
            errors.append("security.max_requests_per_minute must be greater than 0")
        
        return len(errors) == 0, errors
    
    def create_sample_config(self, output_path: str = "contexten_config_sample.yaml") -> bool:
        """Create a sample configuration file"""
        try:
            sample_config = ContextenConfig()
            
            # Create sample with comments
            config_dict = asdict(sample_config)
            
            with open(output_path, 'w') as f:
                f.write("# Contexten Enhanced Orchestrator Configuration\n")
                f.write("# This is a sample configuration file with default values\n\n")
                
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Sample configuration created at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create sample configuration: {e}")
            return False


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    
    return _config_manager


def get_config() -> ContextenConfig:
    """Get current configuration"""
    return get_config_manager().get_config()

