"""Settings and configuration API routes."""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...utils.config import DashboardConfig
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class UpdateSettingsRequest(BaseModel):
    """Request model for updating settings."""
    github_token: Optional[str] = None
    linear_token: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    codegen_api_key: Optional[str] = None
    github_organization: Optional[str] = None
    linear_team_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    enable_requirements_management: Optional[bool] = None
    enable_webhook_integration: Optional[bool] = None
    enable_chat_interface: Optional[bool] = None
    enable_code_analysis: Optional[bool] = None
    projects_per_page: Optional[int] = None
    max_pinned_projects: Optional[int] = None


class SettingsResponse(BaseModel):
    """Response model for settings."""
    github: Dict[str, Any]
    linear: Dict[str, Any]
    anthropic: Dict[str, Any]
    codegen: Dict[str, Any]
    features: Dict[str, Any]
    ui: Dict[str, Any]
    webhook: Dict[str, Any]
    validation: Dict[str, Any]


def get_config(request: Request) -> DashboardConfig:
    """Dependency to get dashboard configuration."""
    return request.app.state.config


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    config: DashboardConfig = Depends(get_config),
):
    """Get current dashboard settings."""
    try:
        validation = config.validate_required_keys()
        
        return SettingsResponse(
            github={
                "configured": validation["github_token"],
                "organization": config.github_organization,
                "include_forks": config.github_include_forks,
                "include_archived": config.github_include_archived,
            },
            linear={
                "configured": validation["linear_token"],
                "team_id": config.linear_team_id,
            },
            anthropic={
                "configured": validation["anthropic_api_key"],
                "model": config.chat_model,
                "max_tokens": config.chat_max_tokens,
            },
            codegen={
                "configured": config.codegen_api_key is not None,
            },
            features={
                "requirements_management": config.enable_requirements_management,
                "webhook_integration": config.enable_webhook_integration,
                "chat_interface": config.enable_chat_interface,
                "code_analysis": config.enable_code_analysis,
            },
            ui={
                "projects_per_page": config.projects_per_page,
                "max_pinned_projects": config.max_pinned_projects,
            },
            webhook={
                "base_url": config.webhook_base_url,
                "secret_configured": config.webhook_secret is not None,
            },
            validation={
                "all_keys_present": all(validation.values()),
                "missing_keys": config.get_missing_keys(),
                "required_keys": validation,
            },
        )
        
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")


@router.put("/", response_model=SettingsResponse)
async def update_settings(
    request: Request,
    settings_update: UpdateSettingsRequest,
    config: DashboardConfig = Depends(get_config),
):
    """Update dashboard settings."""
    try:
        # Update configuration
        if settings_update.github_token is not None:
            config.github_token = settings_update.github_token
            
        if settings_update.linear_token is not None:
            config.linear_token = settings_update.linear_token
            
        if settings_update.anthropic_api_key is not None:
            config.anthropic_api_key = settings_update.anthropic_api_key
            
        if settings_update.codegen_api_key is not None:
            config.codegen_api_key = settings_update.codegen_api_key
            
        if settings_update.github_organization is not None:
            config.github_organization = settings_update.github_organization
            
        if settings_update.linear_team_id is not None:
            config.linear_team_id = settings_update.linear_team_id
            
        if settings_update.webhook_secret is not None:
            config.webhook_secret = settings_update.webhook_secret
            
        if settings_update.enable_requirements_management is not None:
            config.enable_requirements_management = settings_update.enable_requirements_management
            
        if settings_update.enable_webhook_integration is not None:
            config.enable_webhook_integration = settings_update.enable_webhook_integration
            
        if settings_update.enable_chat_interface is not None:
            config.enable_chat_interface = settings_update.enable_chat_interface
            
        if settings_update.enable_code_analysis is not None:
            config.enable_code_analysis = settings_update.enable_code_analysis
            
        if settings_update.projects_per_page is not None:
            config.projects_per_page = settings_update.projects_per_page
            
        if settings_update.max_pinned_projects is not None:
            config.max_pinned_projects = settings_update.max_pinned_projects
            
        # Reinitialize services with new configuration
        await _reinitialize_services(request, config)
        
        # Return updated settings
        return await get_settings(config)
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


@router.post("/validate")
async def validate_settings(
    config: DashboardConfig = Depends(get_config),
):
    """Validate current settings and API keys."""
    try:
        validation_results = {}
        
        # Validate GitHub token
        if config.github_token:
            try:
                from ...services.github_service import GitHubService
                github_service = GitHubService(config.github_token)
                # Try to make a simple API call
                user = github_service.github.get_user()
                validation_results["github"] = {
                    "valid": True,
                    "user": user.login,
                    "rate_limit": github_service.github.get_rate_limit().core.remaining,
                }
            except Exception as e:
                validation_results["github"] = {
                    "valid": False,
                    "error": str(e),
                }
        else:
            validation_results["github"] = {
                "valid": False,
                "error": "No GitHub token provided",
            }
            
        # Validate Linear token
        if config.linear_token:
            try:
                from ...services.linear_service import LinearService
                linear_service = LinearService(config.linear_token)
                # Try to fetch teams
                teams = await linear_service.get_teams()
                validation_results["linear"] = {
                    "valid": True,
                    "teams_count": len(teams),
                }
            except Exception as e:
                validation_results["linear"] = {
                    "valid": False,
                    "error": str(e),
                }
        else:
            validation_results["linear"] = {
                "valid": False,
                "error": "No Linear token provided",
            }
            
        # Validate Anthropic API key
        if config.anthropic_api_key:
            try:
                from ...services.chat_service import ChatService
                chat_service = ChatService(config.anthropic_api_key)
                # Create a test session to validate the key
                session = await chat_service.create_session()
                validation_results["anthropic"] = {
                    "valid": True,
                    "model": config.chat_model,
                }
                # Clean up test session
                await chat_service.clear_session(session.session_id)
            except Exception as e:
                validation_results["anthropic"] = {
                    "valid": False,
                    "error": str(e),
                }
        else:
            validation_results["anthropic"] = {
                "valid": False,
                "error": "No Anthropic API key provided",
            }
            
        return {
            "validation_results": validation_results,
            "overall_valid": all(
                result.get("valid", False) 
                for result in validation_results.values()
            ),
        }
        
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate settings")


@router.get("/api-keys/status")
async def get_api_keys_status(
    config: DashboardConfig = Depends(get_config),
):
    """Get status of all API keys without exposing the actual keys."""
    try:
        return {
            "github_token": {
                "configured": config.github_token is not None,
                "length": len(config.github_token) if config.github_token else 0,
                "masked": f"{'*' * (len(config.github_token) - 4)}{config.github_token[-4:]}" if config.github_token and len(config.github_token) > 4 else None,
            },
            "linear_token": {
                "configured": config.linear_token is not None,
                "length": len(config.linear_token) if config.linear_token else 0,
                "masked": f"{'*' * (len(config.linear_token) - 4)}{config.linear_token[-4:]}" if config.linear_token and len(config.linear_token) > 4 else None,
            },
            "anthropic_api_key": {
                "configured": config.anthropic_api_key is not None,
                "length": len(config.anthropic_api_key) if config.anthropic_api_key else 0,
                "masked": f"{'*' * (len(config.anthropic_api_key) - 4)}{config.anthropic_api_key[-4:]}" if config.anthropic_api_key and len(config.anthropic_api_key) > 4 else None,
            },
            "codegen_api_key": {
                "configured": config.codegen_api_key is not None,
                "length": len(config.codegen_api_key) if config.codegen_api_key else 0,
                "masked": f"{'*' * (len(config.codegen_api_key) - 4)}{config.codegen_api_key[-4:]}" if config.codegen_api_key and len(config.codegen_api_key) > 4 else None,
            },
        }
        
    except Exception as e:
        logger.error(f"Error fetching API keys status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch API keys status")


@router.post("/reset")
async def reset_settings(
    request: Request,
    config: DashboardConfig = Depends(get_config),
):
    """Reset settings to default values."""
    try:
        # Create new default configuration
        default_config = DashboardConfig()
        
        # Update current config with defaults (keeping environment variables)
        env_config = DashboardConfig.from_env()
        
        # Update app state
        request.app.state.config = env_config
        
        # Reinitialize services
        await _reinitialize_services(request, env_config)
        
        logger.info("Settings reset to defaults")
        return {"message": "Settings reset to defaults successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset settings")


@router.get("/export")
async def export_settings(
    config: DashboardConfig = Depends(get_config),
):
    """Export current settings (without sensitive data)."""
    try:
        export_data = {
            "github": {
                "organization": config.github_organization,
                "include_forks": config.github_include_forks,
                "include_archived": config.github_include_archived,
            },
            "linear": {
                "team_id": config.linear_team_id,
            },
            "features": {
                "requirements_management": config.enable_requirements_management,
                "webhook_integration": config.enable_webhook_integration,
                "chat_interface": config.enable_chat_interface,
                "code_analysis": config.enable_code_analysis,
            },
            "ui": {
                "projects_per_page": config.projects_per_page,
                "max_pinned_projects": config.max_pinned_projects,
            },
            "chat": {
                "model": config.chat_model,
                "max_tokens": config.chat_max_tokens,
            },
            "cache": {
                "ttl_default": config.cache_ttl_default,
                "ttl_projects": config.cache_ttl_projects,
                "ttl_requirements": config.cache_ttl_requirements,
            },
        }
        
        return {
            "settings": export_data,
            "exported_at": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "version": "1.0.0",
        }
        
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to export settings")


async def _reinitialize_services(request: Request, config: DashboardConfig):
    """Reinitialize services with new configuration."""
    try:
        # Reinitialize GitHub service
        if config.github_token:
            from ...services.github_service import GitHubService
            request.app.state.github_service = GitHubService(config.github_token)
            logger.info("Reinitialized GitHub service")
            
        # Reinitialize Linear service
        if config.linear_token:
            from ...services.linear_service import LinearService
            request.app.state.linear_service = LinearService(config.linear_token)
            logger.info("Reinitialized Linear service")
            
        # Reinitialize Requirements service
        if config.github_token:
            from ...services.requirements_service import RequirementsService
            request.app.state.requirements_service = RequirementsService(config.github_token)
            logger.info("Reinitialized Requirements service")
            
        # Reinitialize Chat service
        if config.anthropic_api_key:
            from ...services.chat_service import ChatService
            request.app.state.chat_service = ChatService(config.anthropic_api_key)
            logger.info("Reinitialized Chat service")
            
    except Exception as e:
        logger.error(f"Error reinitializing services: {e}")
        raise

