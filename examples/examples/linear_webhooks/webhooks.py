"""
Modern Modal deployment for Linear webhook handling using the latest CodegenApp patterns.
This deployment uses the new modal base classes for better performance and reliability.
"""

import modal
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.modal.base import CodebaseEventsApp, EventRouterMixin

# Set up the base image with required dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "codegen>=0.22.2",
        "fastapi[standard]",
        "uvicorn",
        "pydantic>=2.0.0",
    )
)

# Initialize the Modal app
app = modal.App(name="linear-webhooks")


@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
    enable_memory_snapshot=True,
    container_idle_timeout=300,
    keep_warm=1,
)
class LinearEventsApp(CodebaseEventsApp):
    """
    Linear webhook event handler with codebase snapshotting.
    Automatically handles Linear webhook events and maintains codebase context.
    """

    def setup_handlers(self, cg: CodegenApp):
        """Setup Linear-specific event handlers."""
        # Register Linear event handlers
        @cg.linear.event("Issue")
        async def handle_issue_event(data: dict):
            """Handle Linear Issue events."""
            print(f"Linear Issue Event: {data.get('action', 'unknown')} - {data.get('data', {}).get('title', 'No title')}")
            
            # Add your custom Linear issue handling logic here
            # Example: Create GitHub issues, update project boards, etc.
            return {"status": "processed", "event_type": "issue"}

        @cg.linear.event("Comment")
        async def handle_comment_event(data: dict):
            """Handle Linear Comment events."""
            print(f"Linear Comment Event: {data.get('action', 'unknown')}")
            
            # Add your custom Linear comment handling logic here
            return {"status": "processed", "event_type": "comment"}

        @cg.linear.event("Project")
        async def handle_project_event(data: dict):
            """Handle Linear Project events."""
            print(f"Linear Project Event: {data.get('action', 'unknown')}")
            
            # Add your custom Linear project handling logic here
            return {"status": "processed", "event_type": "project"}


@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
class LinearEventRouter(EventRouterMixin):
    """
    Router for Linear webhook events.
    Handles incoming webhooks and routes them to the appropriate event handlers.
    """

    def get_event_handler_cls(self) -> modal.Cls:
        """Return the Linear event handler class."""
        return LinearEventsApp

    @modal.web_endpoint(method="POST", label="linear-webhook")
    async def linear_webhook(self, request):
        """
        Main Linear webhook endpoint.
        Receives webhooks from Linear and routes them to event handlers.
        
        Configure this URL in your Linear webhook settings:
        https://your-modal-app.modal.run/linear-webhook
        """
        # Extract org and repo from environment or request headers
        # You can customize this based on your setup
        org = "your-org"  # Replace with your GitHub organization
        repo = "your-repo"  # Replace with your repository name
        
        return await self.handle_event(org, repo, "linear", request)


# Optional: Direct FastAPI app for local development
@app.function(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
def create_local_app():
    """
    Create a local FastAPI app for development and testing.
    Use this for local development without Modal's event routing.
    """
    cg = CodegenApp(name="linear-local", repo="your-org/your-repo")
    
    # Setup the same handlers as in LinearEventsApp
    @cg.linear.event("Issue")
    async def handle_issue_event(data: dict):
        print(f"Local Linear Issue Event: {data.get('action', 'unknown')}")
        return {"status": "processed", "event_type": "issue"}
    
    return cg.app


if __name__ == "__main__":
    # For local development
    import uvicorn
    app_instance = create_local_app.local()
    uvicorn.run(app_instance, host="0.0.0.0", port=8000)

