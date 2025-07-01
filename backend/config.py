"""
Configuration settings for the AI-Powered CI/CD Automation Platform
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/cicd_platform")
    
    # API Keys and Tokens
    CODEGEN_TOKEN: str = os.getenv("CODEGEN_TOKEN", "")
    CODEGEN_ORG_ID: int = int(os.getenv("CODEGEN_ORG_ID", "1"))
    CODEGEN_BASE_URL: str = os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com")
    
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    
    MODAL_TOKEN: str = os.getenv("MODAL_TOKEN", "")
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # WebSocket Settings
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Prompt Enhancement Settings
    PROMPT_ENHANCEMENT_ENABLED: bool = True
    MAX_PROMPT_LENGTH: int = 4000
    CONTEXT_WINDOW_SIZE: int = 2000
    
    # Workflow Settings
    MAX_CONCURRENT_WORKFLOWS: int = 10
    WORKFLOW_TIMEOUT_MINUTES: int = 60
    RETRY_ATTEMPTS: int = 3
    
    # Code Analysis Settings
    GRAPH_SITTER_LANGUAGES: list = ["python", "javascript", "typescript", "go", "rust"]
    ANALYSIS_CACHE_TTL_HOURS: int = 24
    
    # Deployment Settings
    MODAL_ENVIRONMENT: str = os.getenv("MODAL_ENVIRONMENT", "staging")
    DEPLOYMENT_TIMEOUT_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Validation
def validate_settings():
    """Validate required settings"""
    required_settings = [
        ("CODEGEN_TOKEN", settings.CODEGEN_TOKEN),
        ("DATABASE_URL", settings.DATABASE_URL),
    ]
    
    missing = [name for name, value in required_settings if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True


# Prompt enhancement templates
PROMPT_TEMPLATES = {
    "code_analysis": """
    You are an expert software engineer analyzing code for quality, security, and maintainability.
    
    Context: {context}
    Repository: {repo_name}
    Branch: {branch}
    
    Task: {original_prompt}
    
    Please:
    1. Analyze the codebase structure and patterns
    2. Identify potential issues (dead code, unused parameters, security vulnerabilities)
    3. Suggest improvements following best practices
    4. Provide specific, actionable recommendations
    
    Focus on: {focus_areas}
    """,
    
    "pr_creation": """
    You are creating a pull request for the following changes.
    
    Context: {context}
    Repository: {repo_name}
    Base Branch: {base_branch}
    
    Requirements: {original_prompt}
    
    Please:
    1. Create clean, well-documented code changes
    2. Follow the existing code style and patterns
    3. Include appropriate tests
    4. Write a clear PR description explaining the changes
    5. Ensure all changes are backwards compatible
    
    Code Quality Standards: {quality_standards}
    """,
    
    "deployment_validation": """
    You are validating a deployment for production readiness.
    
    Context: {context}
    Environment: {environment}
    Deployment Target: {deployment_target}
    
    Task: {original_prompt}
    
    Please:
    1. Verify all dependencies are properly configured
    2. Check environment variables and secrets
    3. Validate database migrations and schema changes
    4. Ensure proper error handling and logging
    5. Confirm monitoring and alerting setup
    
    Validation Checklist: {validation_checklist}
    """,
    
    "workflow_orchestration": """
    You are orchestrating a complex development workflow.
    
    Context: {context}
    Project: {project_name}
    Current Step: {current_step}
    
    Objective: {original_prompt}
    
    Please:
    1. Execute the current workflow step efficiently
    2. Handle any errors gracefully with appropriate fallbacks
    3. Provide clear status updates and progress information
    4. Coordinate with other workflow components
    5. Ensure proper state management and persistence
    
    Workflow State: {workflow_state}
    """
}

