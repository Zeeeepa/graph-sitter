"""Main FastAPI application for the dashboard."""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from ..services import GitHubService, LinearService, WebhookService, RequirementsService, ChatService
from ..utils.config import DashboardConfig
from ..utils.logger import get_logger, configure_dashboard_logging
from .routes import projects, requirements, webhooks, chat, settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Linear & GitHub Dashboard")
    
    # Initialize services
    config = app.state.config
    
    try:
        if config.github_token:
            app.state.github_service = GitHubService(config.github_token)
            logger.info("GitHub service initialized")
        else:
            logger.warning("GitHub service not initialized - no token provided")
            
        if config.linear_token:
            app.state.linear_service = LinearService(config.linear_token)
            logger.info("Linear service initialized")
        else:
            logger.warning("Linear service not initialized - no token provided")
            
        app.state.webhook_service = WebhookService()
        logger.info("Webhook service initialized")
        
        if config.github_token:
            app.state.requirements_service = RequirementsService(config.github_token)
            logger.info("Requirements service initialized")
        else:
            logger.warning("Requirements service not initialized - no GitHub token")
            
        if config.anthropic_api_key:
            app.state.chat_service = ChatService(config.anthropic_api_key)
            logger.info("Chat service initialized")
        else:
            logger.warning("Chat service not initialized - no Anthropic API key")
            
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        
    yield
    
    # Shutdown
    logger.info("Shutting down Linear & GitHub Dashboard")


def create_dashboard_app(config: DashboardConfig = None) -> FastAPI:
    """Create and configure the dashboard FastAPI application.
    
    Args:
        config: Dashboard configuration (uses environment if not provided)
        
    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = DashboardConfig.from_env()
        
    # Configure logging
    configure_dashboard_logging("DEBUG" if config.debug else "INFO")
    
    # Create FastAPI app
    app = FastAPI(
        title="Linear & GitHub Dashboard",
        description="Comprehensive dashboard for GitHub projects with Linear integration",
        version="1.0.0",
        lifespan=lifespan,
        debug=config.debug,
    )
    
    # Store config in app state
    app.state.config = config
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(requirements.router, prefix="/api/requirements", tags=["requirements"])
    app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "services": {
                "github": hasattr(app.state, "github_service"),
                "linear": hasattr(app.state, "linear_service"),
                "webhook": hasattr(app.state, "webhook_service"),
                "requirements": hasattr(app.state, "requirements_service"),
                "chat": hasattr(app.state, "chat_service"),
            }
        }
    
    # Configuration endpoint
    @app.get("/api/config")
    async def get_config():
        """Get dashboard configuration (without sensitive data)."""
        validation = config.validate_required_keys()
        missing_keys = config.get_missing_keys()
        
        return {
            "features": {
                "requirements_management": config.enable_requirements_management and validation["github_token"],
                "webhook_integration": config.enable_webhook_integration,
                "chat_interface": config.enable_chat_interface and validation["anthropic_api_key"],
                "code_analysis": config.enable_code_analysis,
            },
            "github": {
                "configured": validation["github_token"],
                "organization": config.github_organization,
                "include_forks": config.github_include_forks,
                "include_archived": config.github_include_archived,
            },
            "linear": {
                "configured": validation["linear_token"],
                "team_id": config.linear_team_id,
            },
            "ui": {
                "projects_per_page": config.projects_per_page,
                "max_pinned_projects": config.max_pinned_projects,
            },
            "missing_keys": missing_keys,
        }
    
    # Root endpoint - serve dashboard UI
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_ui():
        """Serve the dashboard UI."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Linear & GitHub Dashboard</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                .header h1 {
                    color: #333;
                    margin-bottom: 10px;
                }
                .header p {
                    color: #666;
                    font-size: 18px;
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }
                .feature {
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    background: #fafafa;
                }
                .feature h3 {
                    margin-top: 0;
                    color: #333;
                }
                .feature ul {
                    margin: 0;
                    padding-left: 20px;
                }
                .feature li {
                    margin-bottom: 5px;
                    color: #666;
                }
                .api-links {
                    text-align: center;
                    margin-top: 30px;
                }
                .api-links a {
                    display: inline-block;
                    margin: 0 10px;
                    padding: 10px 20px;
                    background: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    transition: background-color 0.2s;
                }
                .api-links a:hover {
                    background: #0056b3;
                }
                .status {
                    background: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                .status.warning {
                    background: #fff3cd;
                    border-color: #ffc107;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Linear & GitHub Dashboard</h1>
                    <p>Comprehensive project management with AI-powered insights</p>
                </div>
                
                <div class="status" id="status">
                    ✅ Dashboard is running successfully!
                </div>
                
                <div class="features">
                    <div class="feature">
                        <h3>📊 Project Management</h3>
                        <ul>
                            <li>Display 150+ GitHub projects</li>
                            <li>Tab-based interface with pin/unpin</li>
                            <li>Real-time PR/Branch status</li>
                            <li>Quick diff view on hover</li>
                        </ul>
                    </div>
                    
                    <div class="feature">
                        <h3>📋 Requirements Management</h3>
                        <ul>
                            <li>Requirements dialog for each project</li>
                            <li>Save as REQUIREMENTS.md</li>
                            <li>Version control integration</li>
                            <li>Requirements tracking</li>
                        </ul>
                    </div>
                    
                    <div class="feature">
                        <h3>🔗 Webhook Integration</h3>
                        <ul>
                            <li>PR/Branch/Comment events</li>
                            <li>Real-time notifications</li>
                            <li>Event history tracking</li>
                            <li>GitHub extension integration</li>
                        </ul>
                    </div>
                    
                    <div class="feature">
                        <h3>💬 AI Chat Interface</h3>
                        <ul>
                            <li>Anthropic Claude integration</li>
                            <li>Codebase analysis</li>
                            <li>Prompt generation</li>
                            <li>Codegen API integration</li>
                        </ul>
                    </div>
                </div>
                
                <div class="api-links">
                    <a href="/docs" target="_blank">📚 API Documentation</a>
                    <a href="/health" target="_blank">🏥 Health Check</a>
                    <a href="/api/config" target="_blank">⚙️ Configuration</a>
                </div>
            </div>
            
            <script>
                // Check configuration and update status
                fetch('/api/config')
                    .then(response => response.json())
                    .then(config => {
                        const statusEl = document.getElementById('status');
                        if (config.missing_keys && config.missing_keys.length > 0) {
                            statusEl.className = 'status warning';
                            statusEl.innerHTML = `⚠️ Missing API keys: ${config.missing_keys.join(', ')}. Some features may be limited.`;
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching config:', error);
                    });
            </script>
        </body>
        </html>
        """
    
    return app


# For running with uvicorn
app = create_dashboard_app()

