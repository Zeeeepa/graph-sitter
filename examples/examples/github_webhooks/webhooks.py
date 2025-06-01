"""
Modern Modal deployment for GitHub webhook handling using the latest CodegenApp patterns.
This deployment uses the new modal base classes for better performance and reliability.
"""

import modal
from fastapi import Request
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
        "openai>=1.1.0",
        "slack_sdk",
    )
)

# Initialize the Modal app
app = modal.App(name="github-webhooks")


@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
    enable_memory_snapshot=True,
    container_idle_timeout=300,
    keep_warm=1,
)
class GitHubEventsApp(CodebaseEventsApp):
    """
    GitHub webhook event handler with codebase snapshotting.
    Automatically handles GitHub webhook events and maintains codebase context.
    """

    def setup_handlers(self, cg: CodegenApp):
        """Setup GitHub-specific event handlers."""
        # Register GitHub event handlers
        @cg.github.event("pull_request")
        async def handle_pull_request_event(data: dict, request: Request):
            """Handle GitHub Pull Request events."""
            action = data.get("action", "unknown")
            pr_number = data.get("pull_request", {}).get("number", "unknown")
            pr_title = data.get("pull_request", {}).get("title", "No title")
            
            print(f"GitHub PR Event: {action} - PR #{pr_number}: {pr_title}")
            
            # Add your custom GitHub PR handling logic here
            # Example: Auto-review PRs, run tests, update status checks, etc.
            return {"status": "processed", "event_type": "pull_request", "action": action}

        @cg.github.event("issues")
        async def handle_issues_event(data: dict, request: Request):
            """Handle GitHub Issues events."""
            action = data.get("action", "unknown")
            issue_number = data.get("issue", {}).get("number", "unknown")
            issue_title = data.get("issue", {}).get("title", "No title")
            
            print(f"GitHub Issue Event: {action} - Issue #{issue_number}: {issue_title}")
            
            # Add your custom GitHub issue handling logic here
            return {"status": "processed", "event_type": "issues", "action": action}

        @cg.github.event("push")
        async def handle_push_event(data: dict, request: Request):
            """Handle GitHub Push events."""
            ref = data.get("ref", "unknown")
            commits_count = len(data.get("commits", []))
            
            print(f"GitHub Push Event: {ref} - {commits_count} commits")
            
            # Add your custom GitHub push handling logic here
            # Example: Trigger CI/CD, update documentation, etc.
            return {"status": "processed", "event_type": "push", "ref": ref}

        @cg.github.event("pull_request_review")
        async def handle_pr_review_event(data: dict, request: Request):
            """Handle GitHub Pull Request Review events."""
            action = data.get("action", "unknown")
            pr_number = data.get("pull_request", {}).get("number", "unknown")
            review_state = data.get("review", {}).get("state", "unknown")
            
            print(f"GitHub PR Review Event: {action} - PR #{pr_number} - {review_state}")
            
            # Add your custom GitHub PR review handling logic here
            return {"status": "processed", "event_type": "pull_request_review", "action": action}


@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
class GitHubEventRouter(EventRouterMixin):
    """
    Router for GitHub webhook events.
    Handles incoming webhooks and routes them to the appropriate event handlers.
    """

    def get_event_handler_cls(self) -> modal.Cls:
        """Return the GitHub event handler class."""
        return GitHubEventsApp

    @modal.web_endpoint(method="POST", label="github-webhook")
    async def github_webhook(self, request):
        """
        Main GitHub webhook endpoint.
        Receives webhooks from GitHub and routes them to event handlers.
        
        Configure this URL in your GitHub webhook settings:
        https://your-modal-app.modal.run/github-webhook
        """
        # Extract org and repo from the webhook payload
        payload = await request.json()
        repository = payload.get("repository", {})
        full_name = repository.get("full_name", "")
        
        if not full_name:
            return {"error": "Repository information not found in payload"}
        
        org, repo = full_name.split("/", 1)
        
        return await self.handle_event(org, repo, "github", request)


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
    cg = CodegenApp(name="github-local", repo="your-org/your-repo")
    
    # Setup the same handlers as in GitHubEventsApp
    @cg.github.event("pull_request")
    async def handle_pull_request_event(data: dict, request: Request):
        print(f"Local GitHub PR Event: {data.get('action', 'unknown')}")
        return {"status": "processed", "event_type": "pull_request"}
    
    return cg.app


# Unified webhook endpoint for both GitHub and Linear
@app.function(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
@modal.web_endpoint(method="POST", label="unified-webhook")
async def unified_webhook_handler(request):
    """
    Unified webhook endpoint that can handle both GitHub and Linear events.
    Automatically detects the webhook source and routes accordingly.
    
    Configure this URL in both GitHub and Linear webhook settings:
    https://your-modal-app.modal.run/unified-webhook
    """
    headers = dict(request.headers)
    payload = await request.json()
    
    # Detect webhook source based on headers and payload
    if "x-github-event" in headers:
        # GitHub webhook
        repository = payload.get("repository", {})
        full_name = repository.get("full_name", "")
        if not full_name:
            return {"error": "Repository information not found in GitHub payload"}
        
        org, repo = full_name.split("/", 1)
        router = GitHubEventRouter()
        return await router.handle_event(org, repo, "github", request)
    
    elif "x-linear-signature" in headers or payload.get("type") == "Issue":
        # Linear webhook
        # You'll need to configure org/repo for Linear webhooks
        org = "your-org"  # Replace with your GitHub organization
        repo = "your-repo"  # Replace with your repository name
        
        router = LinearEventRouter()
        return await router.handle_event(org, repo, "linear", request)
    
    else:
        return {"error": "Unknown webhook source"}


if __name__ == "__main__":
    # For local development
    import uvicorn
    app_instance = create_local_app.local()
    uvicorn.run(app_instance, host="0.0.0.0", port=8000)

