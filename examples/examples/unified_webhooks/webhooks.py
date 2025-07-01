"""
Unified Modal deployment for both GitHub and Linear webhook handling.
This deployment demonstrates the latest CodegenApp patterns with automatic webhook detection.
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
app = modal.App(name="unified-webhooks")


@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
    enable_memory_snapshot=True,
    container_idle_timeout=300,
    keep_warm=1,
)
class UnifiedEventsApp(CodebaseEventsApp):
    """
    Unified webhook event handler supporting both GitHub and Linear events.
    Automatically handles webhook events and maintains codebase context.
    """

    def setup_handlers(self, cg: CodegenApp):
        """Setup both GitHub and Linear event handlers."""
        
        # GitHub Event Handlers
        @cg.github.event("pull_request")
        async def handle_pull_request_event(data: dict, request: Request):
            """Handle GitHub Pull Request events."""
            action = data.get("action", "unknown")
            pr_number = data.get("pull_request", {}).get("number", "unknown")
            pr_title = data.get("pull_request", {}).get("title", "No title")
            
            print(f"🔀 GitHub PR Event: {action} - PR #{pr_number}: {pr_title}")
            
            # Example: Auto-review PRs, run tests, update status checks
            if action == "opened":
                # Handle new PR creation
                print(f"New PR opened: #{pr_number}")
            elif action == "synchronize":
                # Handle PR updates
                print(f"PR updated: #{pr_number}")
            
            return {"status": "processed", "event_type": "pull_request", "action": action}

        @cg.github.event("issues")
        async def handle_github_issues_event(data: dict, request: Request):
            """Handle GitHub Issues events."""
            action = data.get("action", "unknown")
            issue_number = data.get("issue", {}).get("number", "unknown")
            issue_title = data.get("issue", {}).get("title", "No title")
            
            print(f"🐛 GitHub Issue Event: {action} - Issue #{issue_number}: {issue_title}")
            
            return {"status": "processed", "event_type": "github_issues", "action": action}

        @cg.github.event("push")
        async def handle_push_event(data: dict, request: Request):
            """Handle GitHub Push events."""
            ref = data.get("ref", "unknown")
            commits_count = len(data.get("commits", []))
            
            print(f"📤 GitHub Push Event: {ref} - {commits_count} commits")
            
            # Example: Trigger CI/CD, update documentation
            if ref == "refs/heads/main":
                print("Push to main branch detected")
            
            return {"status": "processed", "event_type": "push", "ref": ref}

        # Linear Event Handlers
        @cg.linear.event("Issue")
        async def handle_linear_issue_event(data: dict):
            """Handle Linear Issue events."""
            action = data.get("action", "unknown")
            issue_data = data.get("data", {})
            issue_title = issue_data.get("title", "No title")
            issue_id = issue_data.get("id", "unknown")
            
            print(f"📋 Linear Issue Event: {action} - {issue_id}: {issue_title}")
            
            # Example: Sync with GitHub issues, update project boards
            if action == "create":
                print(f"New Linear issue created: {issue_title}")
            elif action == "update":
                print(f"Linear issue updated: {issue_title}")
            
            return {"status": "processed", "event_type": "linear_issue", "action": action}

        @cg.linear.event("Comment")
        async def handle_linear_comment_event(data: dict):
            """Handle Linear Comment events."""
            action = data.get("action", "unknown")
            comment_data = data.get("data", {})
            
            print(f"💬 Linear Comment Event: {action}")
            
            return {"status": "processed", "event_type": "linear_comment", "action": action}

        @cg.linear.event("Project")
        async def handle_linear_project_event(data: dict):
            """Handle Linear Project events."""
            action = data.get("action", "unknown")
            project_data = data.get("data", {})
            project_name = project_data.get("name", "No name")
            
            print(f"📊 Linear Project Event: {action} - {project_name}")
            
            return {"status": "processed", "event_type": "linear_project", "action": action}


@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
class UnifiedEventRouter(EventRouterMixin):
    """
    Unified router for both GitHub and Linear webhook events.
    Automatically detects webhook source and routes appropriately.
    """

    def get_event_handler_cls(self) -> modal.Cls:
        """Return the unified event handler class."""
        return UnifiedEventsApp

    @modal.web_endpoint(method="POST", label="unified-webhook")
    async def unified_webhook(self, request):
        """
        Unified webhook endpoint that handles both GitHub and Linear events.
        Automatically detects the webhook source and routes accordingly.
        
        Configure this URL in both GitHub and Linear webhook settings:
        https://your-modal-app.modal.run/unified-webhook
        """
        headers = dict(request.headers)
        
        try:
            payload = await request.json()
        except Exception as e:
            return {"error": f"Invalid JSON payload: {str(e)}"}
        
        # Detect webhook source based on headers and payload
        if "x-github-event" in headers:
            # GitHub webhook
            repository = payload.get("repository", {})
            full_name = repository.get("full_name", "")
            
            if not full_name:
                return {"error": "Repository information not found in GitHub payload"}
            
            org, repo = full_name.split("/", 1)
            print(f"🔍 Detected GitHub webhook for {org}/{repo}")
            
            return await self.handle_event(org, repo, "github", request)
        
        elif "x-linear-signature" in headers or payload.get("type") in ["Issue", "Comment", "Project"]:
            # Linear webhook
            # Extract org/repo from environment variables or configure as needed
            import os
            org = os.environ.get("GITHUB_ORG", "your-org")
            repo = os.environ.get("GITHUB_REPO", "your-repo")
            
            print(f"🔍 Detected Linear webhook for {org}/{repo}")
            
            return await self.handle_event(org, repo, "linear", request)
        
        else:
            return {
                "error": "Unknown webhook source",
                "headers": list(headers.keys()),
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "non-dict payload"
            }

    @modal.web_endpoint(method="GET", label="health-check")
    async def health_check(self):
        """Health check endpoint."""
        return {"status": "healthy", "service": "unified-webhooks"}


# Separate endpoints for specific webhook types (optional)
@app.cls(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
class SpecificEventRouters(EventRouterMixin):
    """Specific routers for GitHub and Linear webhooks separately."""

    def get_event_handler_cls(self) -> modal.Cls:
        return UnifiedEventsApp

    @modal.web_endpoint(method="POST", label="github-only-webhook")
    async def github_only_webhook(self, request):
        """GitHub-only webhook endpoint."""
        payload = await request.json()
        repository = payload.get("repository", {})
        full_name = repository.get("full_name", "")
        
        if not full_name:
            return {"error": "Repository information not found in payload"}
        
        org, repo = full_name.split("/", 1)
        return await self.handle_event(org, repo, "github", request)

    @modal.web_endpoint(method="POST", label="linear-only-webhook")
    async def linear_only_webhook(self, request):
        """Linear-only webhook endpoint."""
        import os
        org = os.environ.get("GITHUB_ORG", "your-org")
        repo = os.environ.get("GITHUB_REPO", "your-repo")
        
        return await self.handle_event(org, repo, "linear", request)


# Local development function
@app.function(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
)
def create_local_app():
    """
    Create a local FastAPI app for development and testing.
    """
    import os
    repo_name = os.environ.get("GITHUB_REPO_FULL_NAME", "your-org/your-repo")
    
    cg = CodegenApp(name="unified-local", repo=repo_name)
    
    # Setup basic handlers for local testing
    @cg.github.event("pull_request")
    async def local_handle_pr(data: dict, request: Request):
        print(f"Local GitHub PR: {data.get('action', 'unknown')}")
        return {"status": "processed"}
    
    @cg.linear.event("Issue")
    async def local_handle_issue(data: dict):
        print(f"Local Linear Issue: {data.get('action', 'unknown')}")
        return {"status": "processed"}
    
    return cg.app


if __name__ == "__main__":
    # For local development
    import uvicorn
    app_instance = create_local_app.local()
    uvicorn.run(app_instance, host="0.0.0.0", port=8000)

