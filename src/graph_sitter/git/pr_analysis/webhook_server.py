"""
Webhook server for PR static analysis.

This module provides a webhook server for receiving GitHub webhook events
and triggering PR static analysis.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Type

from graph_sitter.git.auth.github_auth import GitHubAuth
from graph_sitter.git.clients.github_api_client import GitHubAPIClient
from graph_sitter.git.pr_analysis.pr_analyzer import PRAnalyzer
from graph_sitter.git.webhook.webhook_handler import WebhookHandler
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRAnalysisWebhookHandler(WebhookHandler):
    """
    Webhook handler for PR static analysis.
    
    This class extends the base WebhookHandler to add PR static analysis
    functionality.
    """
    
    _pr_analyzer: PRAnalyzer
    
    def __init__(
        self,
        github_client: GitHubAPIClient,
        webhook_secret: str,
        pr_analyzer: PRAnalyzer
    ):
        """
        Initialize the PR analysis webhook handler.
        
        Args:
            github_client: GitHub API client
            webhook_secret: Secret for validating webhook signatures
            pr_analyzer: PR analyzer
        """
        super().__init__(github_client, webhook_secret)
        self._pr_analyzer = pr_analyzer
        
        # Register handlers for PR events
        self.register_handler("pull_request", self.handle_pull_request_event)
    
    def handle_pull_request_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull request event.
        
        Args:
            data: Event data
            
        Returns:
            Response data
        """
        # Get basic event info
        base_response = super().handle_pull_request_event(data)
        
        # Skip if event was ignored
        if base_response.get("status") == "ignored":
            return base_response
        
        # Get PR info
        pr_number = base_response.get("pr_number")
        repo_name = base_response.get("repository")
        
        if not pr_number or not repo_name:
            logger.warning("Missing PR number or repository name")
            return {"status": "error", "message": "Missing PR number or repository name"}
        
        # Analyze PR
        try:
            analysis_results = self._pr_analyzer.analyze_pr(repo_name, pr_number)
            return {
                "status": "success",
                "message": f"Analyzed PR {repo_name}#{pr_number}",
                "analysis_results": analysis_results
            }
        except Exception as e:
            logger.error(f"Error analyzing PR {repo_name}#{pr_number}: {e}")
            return {"status": "error", "message": f"Error analyzing PR: {e}"}


class PRAnalysisWebhookServer:
    """
    Webhook server for PR static analysis.
    
    This class provides an HTTP server for receiving GitHub webhook events
    and triggering PR static analysis.
    """
    
    _webhook_handler: PRAnalysisWebhookHandler
    _port: int
    _server: Optional[HTTPServer] = None
    
    def __init__(self, webhook_handler: PRAnalysisWebhookHandler, port: int = 8000):
        """
        Initialize the webhook server.
        
        Args:
            webhook_handler: PR analysis webhook handler
            port: Port to listen on
        """
        self._webhook_handler = webhook_handler
        self._port = port
    
    def start(self) -> None:
        """
        Start the webhook server.
        
        This method starts an HTTP server that listens for GitHub webhook events
        and passes them to the webhook handler.
        """
        # Create request handler class
        webhook_handler = self._webhook_handler
        
        class RequestHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                # Read request body
                content_length = int(self.headers.get("Content-Length", 0))
                payload = self.rfile.read(content_length)
                
                # Process webhook
                response = webhook_handler.handle_webhook(dict(self.headers), payload)
                
                # Send response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
            
            def log_message(self, format, *args):
                # Override to use our logger
                logger.info(f"{self.address_string()} - {format % args}")
        
        # Create server
        self._server = HTTPServer(("", self._port), RequestHandler)
        
        logger.info(f"Starting webhook server on port {self._port}")
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Stopping webhook server")
            self.stop()
    
    def stop(self) -> None:
        """
        Stop the webhook server.
        """
        if self._server:
            self._server.server_close()
            self._server = None
            logger.info("Webhook server stopped")


def create_webhook_server_from_env(port: int = 8000) -> PRAnalysisWebhookServer:
    """
    Create a webhook server from environment variables.
    
    Args:
        port: Port to listen on
        
    Returns:
        Webhook server
    """
    # Get GitHub token and webhook secret from environment
    github_auth = GitHubAuth.from_env()
    token = github_auth.token
    webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    
    if not token:
        msg = "GitHub token not found in environment variables"
        raise ValueError(msg)
    
    if not webhook_secret:
        msg = "GitHub webhook secret not found in environment variables"
        raise ValueError(msg)
    
    # Create GitHub client
    github_client = GitHubAPIClient(token=token)
    
    # Create PR analyzer
    pr_analyzer = PRAnalyzer(github_client=github_client)
    
    # Create webhook handler
    webhook_handler = PRAnalysisWebhookHandler(
        github_client=github_client,
        webhook_secret=webhook_secret,
        pr_analyzer=pr_analyzer
    )
    
    # Create webhook server
    return PRAnalysisWebhookServer(webhook_handler=webhook_handler, port=port)


def main() -> None:
    """
    Main entry point for the webhook server.
    """
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Create webhook server
    server = create_webhook_server_from_env(port=port)
    
    # Start server
    server.start()


if __name__ == "__main__":
    main()

