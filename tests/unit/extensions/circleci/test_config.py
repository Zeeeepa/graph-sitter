"""
Unit tests for CircleCI configuration management
"""

import pytest
import os
from pathlib import Path
from datetime import timedelta
from pydantic import ValidationError

from src.contexten.extensions.circleci.config import (
    CircleCIIntegrationConfig, APIConfig, WebhookConfig, FailureAnalysisConfig,
    AutoFixConfig, WorkflowConfig, GitHubIntegrationConfig, CodegenIntegrationConfig
)


class TestAPIConfig:
    """Test API configuration"""
    
    def test_valid_config(self):
        """Test valid API configuration"""
        config = APIConfig(api_token="test-token")
        assert config.api_token.get_secret_value() == "test-token"
        assert config.api_base_url == "https://circleci.com/api"
        assert config.request_timeout == 30
    
    def test_invalid_url(self):
        """Test invalid API URL"""
        with pytest.raises(ValidationError):
            APIConfig(api_token="test-token", api_base_url="invalid-url")
    
    def test_timeout_validation(self):
        """Test timeout validation"""
        with pytest.raises(ValidationError):
            APIConfig(api_token="test-token", request_timeout=0)
        
        with pytest.raises(ValidationError):
            APIConfig(api_token="test-token", request_timeout=400)


class TestWebhookConfig:
    """Test webhook configuration"""
    
    def test_default_config(self):
        """Test default webhook configuration"""
        config = WebhookConfig()
        assert config.webhook_secret is None
        assert config.validate_signatures is True
        assert "workflow-completed" in config.webhook_event_types
        assert "job-completed" in config.webhook_event_types
    
    def test_with_secret(self):
        """Test webhook config with secret"""
        config = WebhookConfig(webhook_secret="test-secret")
        assert config.webhook_secret.get_secret_value() == "test-secret"
    
    def test_queue_size_validation(self):
        """Test queue size validation"""
        with pytest.raises(ValidationError):
            WebhookConfig(max_queue_size=0)
        
        with pytest.raises(ValidationError):
            WebhookConfig(max_queue_size=20000)


class TestFailureAnalysisConfig:
    """Test failure analysis configuration"""
    
    def test_default_config(self):
        """Test default failure analysis configuration"""
        config = FailureAnalysisConfig()
        assert config.enabled is True
        assert config.log_analysis_depth == "deep"
        assert config.pattern_matching_enabled is True
        assert config.cache_duration == timedelta(hours=24)
    
    def test_depth_validation(self):
        """Test analysis depth validation"""
        config = FailureAnalysisConfig(log_analysis_depth="shallow")
        assert config.log_analysis_depth == "shallow"
        
        with pytest.raises(ValidationError):
            FailureAnalysisConfig(log_analysis_depth="invalid")
    
    def test_confidence_threshold_validation(self):
        """Test confidence threshold validation"""
        with pytest.raises(ValidationError):
            FailureAnalysisConfig(confidence_threshold=-0.1)
        
        with pytest.raises(ValidationError):
            FailureAnalysisConfig(confidence_threshold=1.1)


class TestAutoFixConfig:
    """Test auto-fix configuration"""
    
    def test_default_config(self):
        """Test default auto-fix configuration"""
        config = AutoFixConfig()
        assert config.enabled is True
        assert config.fix_confidence_threshold == 0.7
        assert config.enable_code_fixes is True
        assert config.require_human_approval is False
    
    def test_confidence_validation(self):
        """Test confidence threshold validation"""
        with pytest.raises(ValidationError):
            AutoFixConfig(fix_confidence_threshold=1.5)
    
    def test_max_fixes_validation(self):
        """Test max fixes validation"""
        with pytest.raises(ValidationError):
            AutoFixConfig(max_fixes_per_failure=0)


class TestCircleCIIntegrationConfig:
    """Test main integration configuration"""
    
    def test_minimal_config(self):
        """Test minimal valid configuration"""
        api_config = APIConfig(api_token="test-token")
        config = CircleCIIntegrationConfig(api=api_config)
        
        assert config.api.api_token.get_secret_value() == "test-token"
        assert config.debug_mode is False
        assert config.monitor_all_projects is True
    
    def test_from_env_missing_token(self):
        """Test from_env with missing token"""
        # Clear environment
        if "CIRCLECI_API_TOKEN" in os.environ:
            del os.environ["CIRCLECI_API_TOKEN"]
        
        with pytest.raises(ValueError, match="CIRCLECI_API_TOKEN"):
            CircleCIIntegrationConfig.from_env()
    
    def test_from_env_with_token(self):
        """Test from_env with token"""
        os.environ["CIRCLECI_API_TOKEN"] = "test-token"
        
        try:
            config = CircleCIIntegrationConfig.from_env()
            assert config.api.api_token.get_secret_value() == "test-token"
        finally:
            del os.environ["CIRCLECI_API_TOKEN"]
    
    def test_validation_missing_token(self):
        """Test validation with missing API token"""
        api_config = APIConfig(api_token="")
        config = CircleCIIntegrationConfig(api=api_config)
        
        issues = config.validate_configuration()
        assert any("API token" in issue for issue in issues)
    
    def test_validation_github_enabled_no_token(self):
        """Test validation with GitHub enabled but no token"""
        api_config = APIConfig(api_token="test-token")
        github_config = GitHubIntegrationConfig(enabled=True, github_token=None)
        config = CircleCIIntegrationConfig(api=api_config, github=github_config)
        
        issues = config.validate_configuration()
        assert any("GitHub token" in issue for issue in issues)
    
    def test_validation_codegen_enabled_no_token(self):
        """Test validation with Codegen enabled but no token"""
        api_config = APIConfig(api_token="test-token")
        codegen_config = CodegenIntegrationConfig(enabled=True, codegen_api_token=None)
        config = CircleCIIntegrationConfig(api=api_config, codegen=codegen_config)
        
        issues = config.validate_configuration()
        assert any("Codegen API token" in issue for issue in issues)
    
    def test_validation_webhook_signature_no_secret(self):
        """Test validation with signature validation but no secret"""
        api_config = APIConfig(api_token="test-token")
        webhook_config = WebhookConfig(validate_signatures=True, webhook_secret=None)
        config = CircleCIIntegrationConfig(api=api_config, webhook=webhook_config)
        
        issues = config.validate_configuration()
        assert any("Webhook secret" in issue for issue in issues)
    
    def test_validation_autofix_without_analysis(self):
        """Test validation with auto-fix enabled but analysis disabled"""
        api_config = APIConfig(api_token="test-token")
        analysis_config = FailureAnalysisConfig(enabled=False)
        autofix_config = AutoFixConfig(enabled=True)
        config = CircleCIIntegrationConfig(
            api=api_config, 
            failure_analysis=analysis_config, 
            auto_fix=autofix_config
        )
        
        issues = config.validate_configuration()
        assert any("Failure analysis must be enabled" in issue for issue in issues)
    
    def test_is_production_ready(self):
        """Test production readiness check"""
        api_config = APIConfig(api_token="test-token")
        config = CircleCIIntegrationConfig(api=api_config, debug_mode=True)
        
        assert not config.is_production_ready
        
        config.debug_mode = False
        assert config.is_production_ready
    
    def test_summary(self):
        """Test configuration summary"""
        api_config = APIConfig(api_token="test-token")
        config = CircleCIIntegrationConfig(api=api_config)
        
        summary = config.summary
        assert summary["api_configured"] is True
        assert summary["github_enabled"] is True
        assert summary["auto_fix_enabled"] is True
        assert summary["debug_mode"] is False
    
    def test_get_effective_config(self):
        """Test effective configuration with masked secrets"""
        api_config = APIConfig(api_token="test-token")
        webhook_config = WebhookConfig(webhook_secret="test-secret")
        config = CircleCIIntegrationConfig(api=api_config, webhook=webhook_config)
        
        effective = config.get_effective_config()
        assert effective["api"]["api_token"] == "***MASKED***"
        assert effective["webhook"]["webhook_secret"] == "***MASKED***"


@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary config file"""
    config_file = tmp_path / "test_config.yaml"
    config_content = """
api:
  api_token: test-token
  api_base_url: https://circleci.com/api
webhook:
  webhook_secret: test-secret
  validate_signatures: true
github:
  enabled: true
  github_token: github-token
"""
    config_file.write_text(config_content)
    return config_file


class TestConfigFile:
    """Test configuration file operations"""
    
    def test_from_file_yaml(self, temp_config_file):
        """Test loading from YAML file"""
        config = CircleCIIntegrationConfig.from_file(temp_config_file)
        
        assert config.api.api_token.get_secret_value() == "test-token"
        assert config.webhook.webhook_secret.get_secret_value() == "test-secret"
        assert config.github.github_token.get_secret_value() == "github-token"
    
    def test_from_file_not_found(self):
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            CircleCIIntegrationConfig.from_file(Path("non-existent.yaml"))
    
    def test_save_to_file(self, tmp_path):
        """Test saving to file"""
        api_config = APIConfig(api_token="test-token")
        config = CircleCIIntegrationConfig(api=api_config)
        
        config_file = tmp_path / "saved_config.yaml"
        config.save_to_file(config_file, format="yaml")
        
        assert config_file.exists()
        
        # Load and verify
        loaded_config = CircleCIIntegrationConfig.from_file(config_file)
        assert loaded_config.api.api_base_url == config.api.api_base_url
    
    def test_save_to_file_json(self, tmp_path):
        """Test saving to JSON file"""
        api_config = APIConfig(api_token="test-token")
        config = CircleCIIntegrationConfig(api=api_config)
        
        config_file = tmp_path / "saved_config.json"
        config.save_to_file(config_file, format="json")
        
        assert config_file.exists()
    
    def test_save_unsupported_format(self, tmp_path):
        """Test saving with unsupported format"""
        api_config = APIConfig(api_token="test-token")
        config = CircleCIIntegrationConfig(api=api_config)
        
        config_file = tmp_path / "config.txt"
        with pytest.raises(ValueError, match="Unsupported format"):
            config.save_to_file(config_file, format="txt")

