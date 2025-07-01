"""
Unit tests for database configuration management.
"""

import os
import pytest
from unittest.mock import patch

from src.graph_sitter.database.config import (
    DatabaseConfig, get_database_config, set_database_config, 
    reset_database_config, get_test_config, get_development_config,
    get_production_config, configure_for_environment
)


class TestDatabaseConfig:
    """Test database configuration functionality."""
    
    def test_default_config_creation(self):
        """Test creating config with default values."""
        config = DatabaseConfig()
        
        assert config.pool_size == 20
        assert config.max_overflow == 30
        assert config.pool_timeout == 30
        assert config.echo is False
        assert config.enable_query_monitoring is True
        
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config should not raise
        config = DatabaseConfig(
            url="postgresql://user:pass@localhost:5432/test",
            pool_size=10,
            max_overflow=20
        )
        assert config.pool_size == 10
        
        # Invalid pool size should raise
        with pytest.raises(ValueError, match="Pool size must be positive"):
            DatabaseConfig(pool_size=0)
        
        # Invalid URL should raise
        with pytest.raises(ValueError, match="Invalid database URL"):
            DatabaseConfig(url="invalid-url")
    
    def test_connection_args(self):
        """Test connection arguments generation."""
        config = DatabaseConfig(
            pool_size=15,
            max_overflow=25,
            pool_timeout=45,
            echo=True
        )
        
        args = config.connection_args
        assert args['pool_size'] == 15
        assert args['max_overflow'] == 25
        assert args['pool_timeout'] == 45
        assert args['echo'] is True
        assert 'connect_args' in args
    
    def test_database_name_extraction(self):
        """Test database name extraction from URL."""
        config = DatabaseConfig(url="postgresql://user:pass@localhost:5432/mydb")
        assert config.database_name == "mydb"
        
        config = DatabaseConfig(url="postgresql://user:pass@localhost:5432/")
        assert config.database_name == "graph_sitter"
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_is_production(self):
        """Test production environment detection."""
        config = DatabaseConfig()
        assert config.is_production is True
    
    def test_monitoring_config(self):
        """Test monitoring configuration."""
        config = DatabaseConfig(
            enable_query_monitoring=True,
            slow_query_threshold_ms=500
        )
        
        monitoring = config.get_monitoring_config()
        assert monitoring['enable_query_monitoring'] is True
        assert monitoring['slow_query_threshold_ms'] == 500


class TestConfigurationManagement:
    """Test global configuration management."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        reset_database_config()
    
    def test_global_config_singleton(self):
        """Test global configuration singleton behavior."""
        config1 = get_database_config()
        config2 = get_database_config()
        
        assert config1 is config2
    
    def test_set_custom_config(self):
        """Test setting custom configuration."""
        custom_config = DatabaseConfig(pool_size=50)
        set_database_config(custom_config)
        
        retrieved_config = get_database_config()
        assert retrieved_config is custom_config
        assert retrieved_config.pool_size == 50
    
    def test_reset_config(self):
        """Test configuration reset."""
        custom_config = DatabaseConfig(pool_size=50)
        set_database_config(custom_config)
        
        reset_database_config()
        
        new_config = get_database_config()
        assert new_config is not custom_config
        assert new_config.pool_size == 20  # Default value


class TestEnvironmentConfigurations:
    """Test environment-specific configurations."""
    
    def test_test_config(self):
        """Test test environment configuration."""
        config = get_test_config()
        
        assert "test" in config.url
        assert config.pool_size == 5
        assert config.echo is True
        assert config.auto_migrate is True
    
    def test_development_config(self):
        """Test development environment configuration."""
        config = get_development_config()
        
        assert "dev" in config.url
        assert config.pool_size == 10
        assert config.echo is True
        assert config.enable_query_monitoring is True
    
    def test_production_config(self):
        """Test production environment configuration."""
        config = get_production_config()
        
        assert config.pool_size == 50
        assert config.max_overflow == 100
        assert config.echo is False
        assert config.slow_query_threshold_ms == 500
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'test'})
    def test_configure_for_test_environment(self):
        """Test configuring for test environment."""
        config = configure_for_environment()
        
        assert "test" in config.url
        assert config.pool_size == 5
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_configure_for_production_environment(self):
        """Test configuring for production environment."""
        config = configure_for_environment()
        
        assert config.pool_size == 50
        assert config.echo is False
    
    def test_configure_for_unknown_environment(self):
        """Test configuring for unknown environment defaults to development."""
        config = configure_for_environment('unknown')
        
        assert "dev" in config.url
        assert config.pool_size == 10


class TestConfigurationValidation:
    """Test configuration validation edge cases."""
    
    def test_invalid_timeout_values(self):
        """Test invalid timeout values."""
        with pytest.raises(ValueError, match="Query timeout must be positive"):
            DatabaseConfig(query_timeout=0)
        
        with pytest.raises(ValueError, match="Statement timeout must be positive"):
            DatabaseConfig(statement_timeout=-1)
    
    def test_invalid_pool_values(self):
        """Test invalid pool values."""
        with pytest.raises(ValueError, match="Max overflow cannot be negative"):
            DatabaseConfig(max_overflow=-1)
        
        with pytest.raises(ValueError, match="Pool recycle must be positive"):
            DatabaseConfig(pool_recycle=0)
    
    def test_url_validation_edge_cases(self):
        """Test URL validation edge cases."""
        # Missing hostname
        with pytest.raises(ValueError):
            DatabaseConfig(url="postgresql://user:pass@:5432/db")
        
        # Missing scheme
        with pytest.raises(ValueError):
            DatabaseConfig(url="user:pass@localhost:5432/db")
        
        # Valid URL should work
        config = DatabaseConfig(url="postgresql://user:pass@localhost:5432/db")
        assert config.database_name == "db"

