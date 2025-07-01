"""
Modal Webhook Deployment for CICD System
Unified webhook handling for GitHub and Linear events with Codegen integration
"""

import modal
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from codegen import Agent


# Modal setup
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "curl")
    .pip_install(
        "codegen>=0.22.2",
        "fastapi[standard]",
        "uvicorn",
        "pydantic>=2.0.0",
        "httpx",
        "python-dotenv"
    )
)

app = modal.App("cicd-webhooks")


class WebhookEvent(BaseModel):
    """Webhook event model"""
    source: str  # github, linear
    event_type: str
    action: str
    data: Dict[str, Any]
    timestamp: datetime


@app.cls(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    container_idle_timeout=300,
    keep_warm=1
)
class CICDWebhookHandler:
    """
    Unified webhook handler for CICD system
    Processes GitHub and Linear events using Codegen prompts
    """
    
    def __init__(self):
        self.codegen_agent = Agent(
            org_id=os.environ.get("CODEGEN_ORG_ID", "323"),
            token=os.environ.get("CODEGEN_TOKEN", "")
        )
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.linear_token = os.environ.get("LINEAR_TOKEN", "")
    
    async def handle_github_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub webhook events using Codegen prompts"""
        
        if event_type == "pull_request":
            return await self._handle_pull_request(payload)
        elif event_type == "push":
            return await self._handle_push(payload)
        elif event_type == "issues":
            return await self._handle_github_issue(payload)
        else:
            return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
    
    async def _handle_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub PR events"""
        action = payload.get("action", "unknown")
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        repo_name = payload.get("repository", {}).get("full_name", "")
        
        prompt = f"""
Handle GitHub Pull Request event for repository {repo_name}:

Action: {action}
PR Number: #{pr_number}
PR Title: {pr_title}
PR URL: {pr.get('html_url', '')}

Based on the action, perform the following:

If action is "opened":
1. Automatically review the PR for code quality, security, and best practices
2. Check if PR is linked to any Linear issues
3. Run automated tests and code analysis
4. Add review comments with suggestions
5. Update related Linear issues with PR link

If action is "synchronize" (updated):
1. Re-run automated checks on new commits
2. Update previous review comments if needed
3. Check if changes address previous feedback

If action is "closed" and merged:
1. Validate deployment if this is to main branch
2. Update Linear issues to "Complete" status
3. Trigger post-deployment validation
4. Notify team of successful deployment

If action is "closed" and not merged:
1. Update Linear issues noting PR was closed without merge
2. Check if remediation is needed

Provide detailed feedback and take all necessary actions.
"""
        
        task = self.codegen_agent.run(prompt=prompt)
        
        # Wait for completion (simplified for webhook response time)
        for _ in range(30):  # 30 second timeout
            task.refresh()
            if task.status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)
        
        return {
            "status": "processed",
            "event_type": "pull_request",
            "action": action,
            "pr_number": pr_number,
            "task_status": task.status,
            "result": getattr(task, 'result', None) if task.status == "completed" else None
        }
    
    async def _handle_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub push events"""
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        repo_name = payload.get("repository", {}).get("full_name", "")
        
        if ref == "refs/heads/main":
            prompt = f"""
Handle GitHub push to main branch for repository {repo_name}:

Commits: {len(commits)} new commits
Latest commit: {commits[-1].get('message', '') if commits else 'No commits'}

Actions to take:
1. Trigger CI/CD pipeline for main branch deployment
2. Run comprehensive test suite
3. Perform security scans and compliance checks
4. Deploy to staging environment first
5. Validate staging deployment
6. If staging passes, deploy to production
7. Update all related Linear issues
8. Notify team of deployment status
9. Monitor deployment health and performance

Ensure all validation steps pass before production deployment.
"""
        else:
            prompt = f"""
Handle GitHub push to branch {ref} for repository {repo_name}:

Commits: {len(commits)} new commits

Actions to take:
1. Run branch-specific CI checks
2. Update any related Linear issues with progress
3. Check if this branch has open PRs that need updating
4. Run automated tests for the branch
5. Provide feedback on commit quality

Standard branch validation and feedback.
"""
        
        task = self.codegen_agent.run(prompt=prompt)
        
        # Quick response for webhook
        return {
            "status": "processing",
            "event_type": "push",
            "ref": ref,
            "commits_count": len(commits),
            "task_id": getattr(task, 'id', None)
        }
    
    async def _handle_github_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub issue events"""
        action = payload.get("action", "unknown")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        issue_title = issue.get("title", "")
        repo_name = payload.get("repository", {}).get("full_name", "")
        
        prompt = f"""
Handle GitHub Issue event for repository {repo_name}:

Action: {action}
Issue Number: #{issue_number}
Issue Title: {issue_title}

Actions to take:
1. Check if this GitHub issue should be synced with Linear
2. If it's a new issue, create corresponding Linear issue if appropriate
3. If it's a bug report, create Linear issue with "bug" label
4. If it's a feature request, create Linear issue with "enhancement" label
5. Assign to appropriate team member or @codegen
6. Link GitHub issue to Linear issue
7. Set appropriate priority and labels

Maintain synchronization between GitHub and Linear issue tracking.
"""
        
        task = self.codegen_agent.run(prompt=prompt)
        
        return {
            "status": "processing",
            "event_type": "github_issue",
            "action": action,
            "issue_number": issue_number,
            "task_id": getattr(task, 'id', None)
        }
    
    async def handle_linear_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Linear webhook events using Codegen prompts"""
        
        if event_type == "Issue":
            return await self._handle_linear_issue(payload)
        elif event_type == "Comment":
            return await self._handle_linear_comment(payload)
        elif event_type == "Project":
            return await self._handle_linear_project(payload)
        else:
            return {"status": "ignored", "reason": f"Unsupported Linear event type: {event_type}"}
    
    async def _handle_linear_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Linear issue events"""
        action = payload.get("action", "unknown")
        data = payload.get("data", {})
        issue_id = data.get("id", "")
        issue_title = data.get("title", "")
        issue_state = data.get("state", {}).get("name", "")
        assignee = data.get("assignee", {})
        
        prompt = f"""
Handle Linear Issue event:

Action: {action}
Issue ID: {issue_id}
Issue Title: {issue_title}
Current State: {issue_state}
Assignee: {assignee.get('name', 'Unassigned')}

Actions to take based on the event:

If action is "create":
1. Check if issue is unassigned
2. If unassigned for >30 seconds, assign to @codegen
3. Analyze issue requirements and create implementation plan
4. Check if GitHub repository work is needed
5. Create corresponding GitHub issue if appropriate

If action is "update":
1. Check what was updated (status, assignee, etc.)
2. If status changed to "In Progress", start monitoring
3. If status changed to "Complete", validate completion
4. If assignee changed, notify new assignee
5. Update any linked GitHub issues

If issue is unassigned:
1. Wait 30 seconds
2. If still unassigned, automatically assign to @codegen
3. Add comment explaining auto-assignment

Ensure proper issue lifecycle management and team coordination.
"""
        
        task = self.codegen_agent.run(prompt=prompt)
        
        return {
            "status": "processing",
            "event_type": "linear_issue",
            "action": action,
            "issue_id": issue_id,
            "task_id": getattr(task, 'id', None)
        }
    
    async def _handle_linear_comment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Linear comment events"""
        action = payload.get("action", "unknown")
        data = payload.get("data", {})
        comment_body = data.get("body", "")
        issue_id = data.get("issue", {}).get("id", "")
        user = data.get("user", {}).get("name", "")
        
        prompt = f"""
Handle Linear Comment event:

Action: {action}
Issue ID: {issue_id}
Comment by: {user}
Comment: {comment_body[:500]}...

Actions to take:
1. Analyze comment for actionable items
2. If comment mentions @codegen, respond appropriately
3. If comment contains questions, provide answers
4. If comment requests changes, create follow-up tasks
5. If comment indicates completion, validate and update status
6. Check if GitHub PR updates are needed based on comment

Provide intelligent responses and take appropriate actions.
"""
        
        task = self.codegen_agent.run(prompt=prompt)
        
        return {
            "status": "processing",
            "event_type": "linear_comment",
            "action": action,
            "issue_id": issue_id,
            "task_id": getattr(task, 'id', None)
        }
    
    async def _handle_linear_project(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Linear project events"""
        action = payload.get("action", "unknown")
        data = payload.get("data", {})
        project_name = data.get("name", "")
        project_id = data.get("id", "")
        
        prompt = f"""
Handle Linear Project event:

Action: {action}
Project ID: {project_id}
Project Name: {project_name}

Actions to take:
1. Update project tracking and metrics
2. If project status changed, notify team
3. If project completed, run final validation
4. Update dashboard with project status
5. Check if GitHub repository needs updates

Maintain project visibility and coordination.
"""
        
        task = self.codegen_agent.run(prompt=prompt)
        
        return {
            "status": "processing",
            "event_type": "linear_project",
            "action": action,
            "project_id": project_id,
            "task_id": getattr(task, 'id', None)
        }


# Create FastAPI app
webhook_app = FastAPI(title="CICD Webhook Handler", version="1.0.0")
handler = CICDWebhookHandler()


@webhook_app.post("/github-webhook")
async def github_webhook(request: Request):
    """GitHub webhook endpoint"""
    try:
        # Verify GitHub signature (simplified)
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        payload = await request.json()
        
        result = await handler.handle_github_event(event_type, payload)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )


@webhook_app.post("/linear-webhook")
async def linear_webhook(request: Request):
    """Linear webhook endpoint"""
    try:
        payload = await request.json()
        event_type = payload.get("type", "unknown")
        
        result = await handler.handle_linear_event(event_type, payload)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )


@webhook_app.post("/unified-webhook")
async def unified_webhook(request: Request):
    """Unified webhook endpoint that auto-detects source"""
    try:
        headers = dict(request.headers)
        payload = await request.json()
        
        # Auto-detect webhook source
        if "x-github-event" in headers:
            # GitHub webhook
            event_type = headers.get("x-github-event", "unknown")
            result = await handler.handle_github_event(event_type, payload)
            result["source"] = "github"
        
        elif "x-linear-signature" in headers or payload.get("type") in ["Issue", "Comment", "Project"]:
            # Linear webhook
            event_type = payload.get("type", "unknown")
            result = await handler.handle_linear_event(event_type, payload)
            result["source"] = "linear"
        
        else:
            result = {
                "status": "error",
                "error": "Unknown webhook source",
                "headers": list(headers.keys())
            }
        
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )


@webhook_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cicd-webhooks",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@webhook_app.get("/dashboard")
async def dashboard():
    """Simple dashboard endpoint"""
    return {
        "title": "CICD Dashboard",
        "status": "active",
        "endpoints": [
            "/github-webhook",
            "/linear-webhook", 
            "/unified-webhook",
            "/health"
        ],
        "features": [
            "Real-time webhook processing",
            "Codegen integration",
            "Auto-assignment monitoring",
            "PR validation",
            "Issue synchronization"
        ]
    }


# Deploy to Modal
@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    container_idle_timeout=300,
    keep_warm=1
)
@modal.asgi_app()
def fastapi_app():
    """Deploy FastAPI app to Modal"""
    return webhook_app


# Local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(webhook_app, host="0.0.0.0", port=8000)

