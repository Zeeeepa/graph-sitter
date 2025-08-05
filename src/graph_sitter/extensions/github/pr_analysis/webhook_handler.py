"""
Webhook handler for GitHub PR events.
"""
import hmac
import json
from hashlib import sha256
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GitHubWebhookHandler:
    """Handler for GitHub webhooks."""

    def __init__(self, pr_analyzer, webhook_secret: Optional[str] = None):
        """Initialize the webhook handler.

        Args:
            pr_analyzer: PR analyzer instance
            webhook_secret: Secret for validating webhook payloads
        """
        self.pr_analyzer = pr_analyzer
        self.webhook_secret = webhook_secret
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        """Set up the webhook routes."""
        self.app.post("/webhook")(self.handle_webhook)

    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle a GitHub webhook event.

        Args:
            request: FastAPI request object

        Returns:
            Response dict
        """
        # Get headers and payload
        event_type = request.headers.get("X-GitHub-Event")
        delivery_id = request.headers.get("X-GitHub-Delivery")
        signature = request.headers.get("X-Hub-Signature-256")

        # Log webhook event
        logger.info(f"Received GitHub webhook: {event_type} ({delivery_id})")

        # Get payload
        payload_bytes = await request.body()
        
        # Validate webhook signature if secret is provided
        if self.webhook_secret and not self._validate_signature(payload_bytes, signature):
            logger.warning(f"Invalid webhook signature for {delivery_id}")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Handle pull request events
        if event_type == "pull_request":
            return await self.handle_pull_request(payload)
        
        # Ignore other events
        return {"status": "ignored", "event_type": event_type}

    async def handle_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a pull request event.

        Args:
            payload: Webhook payload

        Returns:
            Response dict
        """
        action = payload.get("action")
        pr_number = payload.get("number")
        repository = payload.get("repository", {}).get("full_name")

        logger.info(f"Handling PR {pr_number} in {repository} ({action})")

        # Only analyze PRs that are opened, synchronized, or reopened
        if action in ["opened", "synchronize", "reopened"]:
            # Analyze the PR
            try:
                results = await self.pr_analyzer.analyze_pr(pr_number, repository)
                
                # Post results to GitHub
                await self.post_results(results, pr_number, repository)
                
                return {
                    "status": "success",
                    "message": f"Analyzed PR {pr_number} in {repository}",
                    "results_count": len(results)
                }
            except Exception as e:
                logger.error(f"Error analyzing PR {pr_number} in {repository}: {e}")
                return {
                    "status": "error",
                    "message": f"Error analyzing PR: {str(e)}"
                }
        
        return {
            "status": "ignored",
            "message": f"Ignored PR {pr_number} in {repository} ({action})"
        }

    async def post_results(
        self, results: list, pr_number: int, repository: str
    ) -> None:
        """Post analysis results to GitHub.

        Args:
            results: Analysis results
            pr_number: PR number
            repository: Repository full name
        """
        if not results:
            logger.info(f"No issues found in PR {pr_number} in {repository}")
            return

        # Format results as a comment
        comment = self.pr_analyzer.format_results(results, pr_number, repository)
        
        # Post comment to GitHub
        success = await self.pr_analyzer.post_comment(pr_number, repository, comment)
        
        if success:
            logger.info(f"Posted analysis results to PR {pr_number} in {repository}")
        else:
            logger.error(f"Failed to post analysis results to PR {pr_number} in {repository}")

    def _validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate the webhook signature.

        Args:
            payload: Webhook payload bytes
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret or not signature:
            return False

        # Remove 'sha256=' prefix
        if signature.startswith("sha256="):
            signature = signature[7:]

        # Calculate expected signature
        expected = hmac.new(
            self.webhook_secret.encode(), payload, sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(expected, signature)

