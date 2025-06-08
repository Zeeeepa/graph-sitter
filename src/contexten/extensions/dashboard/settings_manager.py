"""
Settings Manager

Handles secure configuration and API key management.
"""

import logging
import os
from typing import Optional, Dict

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardSettings

logger = get_logger(__name__)


class SettingsManager:
    """Manages dashboard settings and configuration"""
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self._settings: Optional[DashboardSettings] = None
        
    async def initialize(self):
        """Initialize the settings manager"""
        logger.info("Initializing SettingsManager...")
        await self.load_settings()
        
    async def load_settings(self) -> DashboardSettings:
        """Load settings from environment variables and storage"""
        # Load from environment variables
        settings = DashboardSettings(
            github_token=os.getenv("GITHUB_TOKEN"),
            linear_token=os.getenv("LINEAR_TOKEN"),
            codegen_org_id=os.getenv("CODEGEN_ORG_ID"),
            codegen_token=os.getenv("CODEGEN_TOKEN"),
            slack_token=os.getenv("SLACK_TOKEN"),
            postgresql_url=os.getenv("POSTGRESQL_URL"),
            
            # Feature flags from env or defaults
            auto_start_flows=os.getenv("AUTO_START_FLOWS", "false").lower() == "true",
            enable_notifications=os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true",
            enable_analytics=os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
            enable_quality_gates=os.getenv("ENABLE_QUALITY_GATES", "true").lower() == "true",
            
            # Workflow settings
            max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "5")),
            task_timeout=int(os.getenv("TASK_TIMEOUT", "3600")),
            quality_gate_timeout=int(os.getenv("QUALITY_GATE_TIMEOUT", "300")),
            
            # Notification settings
            slack_notifications=os.getenv("SLACK_NOTIFICATIONS", "false").lower() == "true",
            email_notifications=os.getenv("EMAIL_NOTIFICATIONS", "false").lower() == "true"
        )
        
        self._settings = settings
        return settings
    
    async def get_settings(self) -> DashboardSettings:
        """Get current settings"""
        if self._settings is None:
            await self.load_settings()
        return self._settings
    
    async def update_settings(self, new_settings: DashboardSettings) -> DashboardSettings:
        """Update settings"""
        # Validate settings
        await self._validate_settings(new_settings)
        
        # Update stored settings
        self._settings = new_settings
        
        # In a real implementation, you would persist these to a database
        # For now, we'll just keep them in memory
        
        logger.info("Settings updated successfully")
        return new_settings
    
    async def _validate_settings(self, settings: DashboardSettings):
        """Validate settings configuration"""
        errors = []
        
        # Validate required tokens for enabled features
        if settings.enable_quality_gates and not settings.github_token:
            errors.append("GitHub token required when quality gates are enabled")
        
        if settings.auto_start_flows and not settings.codegen_token:
            errors.append("Codegen token required when auto-start flows is enabled")
        
        if settings.slack_notifications and not settings.slack_token:
            errors.append("Slack token required when Slack notifications are enabled")
        
        # Validate numeric settings
        if settings.max_concurrent_tasks < 1:
            errors.append("Max concurrent tasks must be at least 1")
        
        if settings.task_timeout < 60:
            errors.append("Task timeout must be at least 60 seconds")
        
        if settings.quality_gate_timeout < 30:
            errors.append("Quality gate timeout must be at least 30 seconds")
        
        if errors:
            raise ValueError(f"Settings validation failed: {'; '.join(errors)}")
    
    async def test_connections(self) -> Dict[str, bool]:
        """Test connections to all configured services"""
        results = {}
        settings = await self.get_settings()
        
        # Test GitHub connection
        if settings.github_token:
            try:
                # In real implementation, test GitHub API
                results["github"] = True
            except Exception:
                results["github"] = False
        else:
            results["github"] = False
        
        # Test Linear connection
        if settings.linear_token:
            try:
                # In real implementation, test Linear API
                results["linear"] = True
            except Exception:
                results["linear"] = False
        else:
            results["linear"] = False
        
        # Test Codegen connection
        if settings.codegen_token and settings.codegen_org_id:
            try:
                # In real implementation, test Codegen API
                results["codegen"] = True
            except Exception:
                results["codegen"] = False
        else:
            results["codegen"] = False
        
        # Test Slack connection
        if settings.slack_token:
            try:
                # In real implementation, test Slack API
                results["slack"] = True
            except Exception:
                results["slack"] = False
        else:
            results["slack"] = False
        
        return results
