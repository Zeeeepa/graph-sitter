"""
Configuration Management for Graph-Sitter System

Handles environment variables, configuration files, and system settings
with proper validation and defaults.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
import json
import yaml
from urllib.parse import urlparse


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 300
    ssl_mode: str = 'prefer'
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class CodegenConfig:
    """Codegen API configuration"""
    org_id: str
    token: str
    api_url: str = "https://api.codegen.com"
    timeout: int = 60
    max_retries: int = 3
    rate_limit: int = 100  # requests per minute


@dataclass
class ContextenConfig:
    """Contexten integration configuration"""
    enabled: bool = True
    api_url: str = "https://api.contexten.com"
    api_key: Optional[str] = None
    timeout: int = 30
    max_context_length: int = 8000


@dataclass
class AnalysisConfig:
    """Analysis engine configuration"""
    max_workers: int = 4
    max_file_size_mb: int = 10
    supported_languages: List[str] = field(default_factory=lambda: [
        'python', 'typescript', 'javascript', 'java', 'csharp',
        'cpp', 'c', 'rust', 'go', 'ruby', 'php', 'swift', 'kotlin'
    ])
    enable_complexity_analysis: bool = True
    enable_dead_code_detection: bool = True
    enable_dependency_analysis: bool = True
    enable_security_analysis: bool = False
    complexity_threshold: int = 20
    maintainability_threshold: float = 50.0


@dataclass
class CacheConfig:
    """Caching configuration"""
    enabled: bool = True
    cache_dir: str = "/tmp/graph_sitter_cache"
    max_cache_size_gb: int = 5
    cache_ttl_hours: int = 24
    redis_url: Optional[str] = None
    use_redis: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_console: bool = True


class Config:
    """
    Main configuration class that loads and validates all settings
    """
    
    def __init__(self, config_file: Optional[str] = None, env_prefix: str = "GRAPH_SITTER"):
        """
        Initialize configuration
        
        Args:
            config_file: Optional path to configuration file
            env_prefix: Prefix for environment variables
        """
        self.env_prefix = env_prefix
        self.logger = logging.getLogger(__name__)
        
        # Load configuration from multiple sources
        self._config_data = {}
        self._load_defaults()
        
        if config_file:
            self._load_config_file(config_file)
        
        self._load_environment_variables()
        self._validate_configuration()
        
        # Initialize configuration objects
        self.database = self._create_database_config()
        self.codegen = self._create_codegen_config()
        self.contexten = self._create_contexten_config()
        self.analysis = self._create_analysis_config()
        self.cache = self._create_cache_config()
        self.logging = self._create_logging_config()
        
        # Setup logging
        self._setup_logging()
    
    def _load_defaults(self):
        """Load default configuration values"""
        self._config_data = {
            'database': {
                'url': 'postgresql://localhost:5432/graph_sitter',
                'max_connections': 20,
                'connection_timeout': 30,
                'query_timeout': 300,
                'ssl_mode': 'prefer',
                'pool_size': 10,
                'max_overflow': 20
            },
            'codegen': {
                'org_id': '',
                'token': '',
                'api_url': 'https://api.codegen.com',
                'timeout': 60,
                'max_retries': 3,
                'rate_limit': 100
            },
            'contexten': {
                'enabled': True,
                'api_url': 'https://api.contexten.com',
                'api_key': None,
                'timeout': 30,
                'max_context_length': 8000
            },
            'analysis': {
                'max_workers': min(4, os.cpu_count() or 1),
                'max_file_size_mb': 10,
                'supported_languages': [
                    'python', 'typescript', 'javascript', 'java', 'csharp',
                    'cpp', 'c', 'rust', 'go', 'ruby', 'php', 'swift', 'kotlin'
                ],
                'enable_complexity_analysis': True,
                'enable_dead_code_detection': True,
                'enable_dependency_analysis': True,
                'enable_security_analysis': False,
                'complexity_threshold': 20,
                'maintainability_threshold': 50.0
            },
            'cache': {
                'enabled': True,
                'cache_dir': '/tmp/graph_sitter_cache',
                'max_cache_size_gb': 5,
                'cache_ttl_hours': 24,
                'redis_url': None,
                'use_redis': False
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': None,
                'max_file_size_mb': 100,
                'backup_count': 5,
                'enable_console': True
            }
        }
    
    def _load_config_file(self, config_file: str):
        """Load configuration from file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            self.logger.warning(f"Configuration file not found: {config_file}")
            return
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    self.logger.error(f"Unsupported configuration file format: {config_path.suffix}")
                    return
            
            # Merge file configuration with defaults
            self._deep_merge(self._config_data, file_config)
            self.logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration file {config_file}: {str(e)}")
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Database
            f'{self.env_prefix}_DATABASE_URL': ('database', 'url'),
            f'{self.env_prefix}_DATABASE_MAX_CONNECTIONS': ('database', 'max_connections', int),
            f'{self.env_prefix}_DATABASE_TIMEOUT': ('database', 'connection_timeout', int),
            
            # Codegen
            f'{self.env_prefix}_CODEGEN_ORG_ID': ('codegen', 'org_id'),
            f'{self.env_prefix}_CODEGEN_TOKEN': ('codegen', 'token'),
            f'{self.env_prefix}_CODEGEN_API_URL': ('codegen', 'api_url'),
            
            # Contexten
            f'{self.env_prefix}_CONTEXTEN_ENABLED': ('contexten', 'enabled', lambda x: x.lower() == 'true'),
            f'{self.env_prefix}_CONTEXTEN_API_KEY': ('contexten', 'api_key'),
            f'{self.env_prefix}_CONTEXTEN_API_URL': ('contexten', 'api_url'),
            
            # Analysis
            f'{self.env_prefix}_MAX_WORKERS': ('analysis', 'max_workers', int),
            f'{self.env_prefix}_MAX_FILE_SIZE_MB': ('analysis', 'max_file_size_mb', int),
            f'{self.env_prefix}_COMPLEXITY_THRESHOLD': ('analysis', 'complexity_threshold', int),
            
            # Cache
            f'{self.env_prefix}_CACHE_ENABLED': ('cache', 'enabled', lambda x: x.lower() == 'true'),
            f'{self.env_prefix}_CACHE_DIR': ('cache', 'cache_dir'),
            f'{self.env_prefix}_REDIS_URL': ('cache', 'redis_url'),
            
            # Logging
            f'{self.env_prefix}_LOG_LEVEL': ('logging', 'level'),
            f'{self.env_prefix}_LOG_FILE': ('logging', 'file_path'),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                section = config_path[0]
                key = config_path[1]
                converter = config_path[2] if len(config_path) > 2 else str
                
                try:
                    converted_value = converter(value)
                    self._config_data[section][key] = converted_value
                    self.logger.debug(f"Set {section}.{key} from environment variable {env_var}")
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error converting environment variable {env_var}: {str(e)}")
    
    def _validate_configuration(self):
        """Validate configuration values"""
        errors = []
        
        # Validate required Codegen settings
        if not self._config_data['codegen']['org_id']:
            errors.append("CODEGEN_ORG_ID is required")
        
        if not self._config_data['codegen']['token']:
            errors.append("CODEGEN_TOKEN is required")
        
        # Validate database URL
        db_url = self._config_data['database']['url']
        try:
            parsed = urlparse(db_url)
            if not parsed.scheme or not parsed.netloc:
                errors.append(f"Invalid database URL: {db_url}")
        except Exception:
            errors.append(f"Invalid database URL format: {db_url}")
        
        # Validate numeric values
        numeric_validations = [
            ('analysis', 'max_workers', 1, 32),
            ('analysis', 'max_file_size_mb', 1, 1000),
            ('analysis', 'complexity_threshold', 1, 100),
            ('database', 'max_connections', 1, 1000),
            ('cache', 'max_cache_size_gb', 1, 100),
        ]
        
        for section, key, min_val, max_val in numeric_validations:
            value = self._config_data[section][key]
            if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                errors.append(f"{section}.{key} must be between {min_val} and {max_val}")
        
        # Validate cache directory
        cache_dir = self._config_data['cache']['cache_dir']
        try:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create cache directory {cache_dir}: {str(e)}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
    
    def _create_database_config(self) -> DatabaseConfig:
        """Create database configuration object"""
        db_config = self._config_data['database']
        return DatabaseConfig(**db_config)
    
    def _create_codegen_config(self) -> CodegenConfig:
        """Create Codegen configuration object"""
        codegen_config = self._config_data['codegen']
        return CodegenConfig(**codegen_config)
    
    def _create_contexten_config(self) -> ContextenConfig:
        """Create Contexten configuration object"""
        contexten_config = self._config_data['contexten']
        return ContextenConfig(**contexten_config)
    
    def _create_analysis_config(self) -> AnalysisConfig:
        """Create analysis configuration object"""
        analysis_config = self._config_data['analysis']
        return AnalysisConfig(**analysis_config)
    
    def _create_cache_config(self) -> CacheConfig:
        """Create cache configuration object"""
        cache_config = self._config_data['cache']
        return CacheConfig(**cache_config)
    
    def _create_logging_config(self) -> LoggingConfig:
        """Create logging configuration object"""
        logging_config = self._config_data['logging']
        return LoggingConfig(**logging_config)
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        log_config = self.logging
        
        # Set logging level
        numeric_level = getattr(logging, log_config.level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)
        
        # Create formatter
        formatter = logging.Formatter(log_config.format)
        
        # Setup console handler
        if log_config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)
        
        # Setup file handler
        if log_config.file_path:
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_config.file_path,
                    maxBytes=log_config.max_file_size_mb * 1024 * 1024,
                    backupCount=log_config.backup_count
                )
                file_handler.setFormatter(formatter)
                logging.getLogger().addHandler(file_handler)
            except Exception as e:
                self.logger.error(f"Failed to setup file logging: {str(e)}")
    
    def _deep_merge(self, base_dict: Dict, update_dict: Dict):
        """Deep merge two dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)"""
        summary = {}
        
        for section_name in ['database', 'codegen', 'contexten', 'analysis', 'cache', 'logging']:
            section = getattr(self, section_name)
            section_dict = {}
            
            for key, value in section.__dict__.items():
                # Hide sensitive information
                if any(sensitive in key.lower() for sensitive in ['token', 'key', 'password', 'secret']):
                    section_dict[key] = '***' if value else None
                else:
                    section_dict[key] = value
            
            summary[section_name] = section_dict
        
        return summary
    
    @property
    def max_workers(self) -> int:
        """Convenience property for max workers"""
        return self.analysis.max_workers
    
    @property
    def database_url(self) -> str:
        """Convenience property for database URL"""
        return self.database.url
    
    def validate_codegen_credentials(self) -> bool:
        """Validate Codegen API credentials"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.codegen.token}',
                'X-Organization-ID': self.codegen.org_id
            }
            
            response = requests.get(
                f"{self.codegen.api_url}/health",
                headers=headers,
                timeout=self.codegen.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Failed to validate Codegen credentials: {str(e)}")
            return False


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Load configuration from file and environment
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Configured Config object
    """
    return Config(config_file)

