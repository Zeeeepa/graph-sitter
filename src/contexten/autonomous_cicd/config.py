"""
Configuration for Autonomous CI/CD System
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class CICDConfig:
    """Configuration for autonomous CI/CD system"""
    
    # Codegen SDK Configuration
    codegen_org_id: str = field(default_factory=lambda: os.getenv("CODEGEN_ORG_ID", ""))
    codegen_token: str = field(default_factory=lambda: os.getenv("CODEGEN_TOKEN", ""))
    codegen_base_url: str = field(default_factory=lambda: os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com"))
    
    # Repository Configuration
    repo_path: str = field(default_factory=lambda: os.getcwd())
    target_branch: str = "develop"
    protected_branches: List[str] = field(default_factory=lambda: ["main", "master", "develop"])
    
    # CI/CD Pipeline Configuration
    enable_auto_testing: bool = True
    enable_auto_deployment: bool = False
    enable_code_analysis: bool = True
    enable_security_scanning: bool = True
    
    # Analysis Configuration
    analysis_timeout: int = 300  # 5 minutes
    max_concurrent_analyses: int = 3
    code_quality_threshold: float = 0.8
    test_coverage_threshold: float = 0.75
    
    # GitHub Integration
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    github_webhook_secret: str = field(default_factory=lambda: os.getenv("GITHUB_WEBHOOK_SECRET", ""))
    
    # Linear Integration
    linear_api_key: str = field(default_factory=lambda: os.getenv("LINEAR_API_KEY", ""))
    
    # Notification Configuration
    slack_webhook_url: str = field(default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL", ""))
    notification_channels: List[str] = field(default_factory=list)
    
    # Performance Configuration
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    parallel_execution: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.codegen_org_id or not self.codegen_token:
            raise ValueError("CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables are required")
        
        if not Path(self.repo_path).exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
    
    @classmethod
    def from_env(cls) -> "CICDConfig":
        """Create configuration from environment variables"""
        return cls()
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "codegen_org_id": self.codegen_org_id[:8] + "..." if self.codegen_org_id else "",
            "codegen_base_url": self.codegen_base_url,
            "repo_path": self.repo_path,
            "target_branch": self.target_branch,
            "enable_auto_testing": self.enable_auto_testing,
            "enable_auto_deployment": self.enable_auto_deployment,
            "enable_code_analysis": self.enable_code_analysis,
            "analysis_timeout": self.analysis_timeout,
            "max_concurrent_analyses": self.max_concurrent_analyses,
            "code_quality_threshold": self.code_quality_threshold,
            "test_coverage_threshold": self.test_coverage_threshold,
        }

