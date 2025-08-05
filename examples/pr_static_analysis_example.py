#!/usr/bin/env python
"""
Example script for using the PR static analysis system.

This script demonstrates how to use the PR static analysis system
to analyze a pull request and post results to GitHub.
"""

import argparse
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph_sitter.git.auth.github_auth import GitHubAuth
from graph_sitter.git.clients.github_api_client import GitHubAPIClient
from graph_sitter.git.pr_analysis.pr_analyzer import PRAnalyzer
from graph_sitter.git.pr_analysis.webhook_server import create_webhook_server_from_env
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def analyze_pr(repo: str, pr_number: int, token: str) -> None:
    """
    Analyze a pull request and post results to GitHub.
    
    Args:
        repo: Repository full name (owner/repo)
        pr_number: Pull request number
        token: GitHub token
    """
    # Create GitHub client
    github_client = GitHubAPIClient(token=token)
    
    # Create PR analyzer
    analyzer = PRAnalyzer(github_client=github_client)
    
    # Analyze PR
    logger.info(f"Analyzing PR {repo}#{pr_number}")
    results = analyzer.analyze_pr(repo, pr_number)
    
    # Print results
    logger.info(f"Analysis results: {results}")


def start_webhook_server(port: int) -> None:
    """
    Start the webhook server.
    
    Args:
        port: Port to listen on
    """
    # Create webhook server
    server = create_webhook_server_from_env(port=port)
    
    # Start server
    logger.info(f"Starting webhook server on port {port}")
    server.start()


def main() -> None:
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description="PR static analysis example")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze PR command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a pull request")
    analyze_parser.add_argument("repo", help="Repository full name (owner/repo)")
    analyze_parser.add_argument("pr_number", type=int, help="Pull request number")
    analyze_parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    
    # Start webhook server command
    server_parser = subparsers.add_parser("server", help="Start webhook server")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        # Get token from args or environment
        token = args.token or os.environ.get("GITHUB_TOKEN")
        if not token:
            logger.error("GitHub token not provided")
            parser.print_help()
            sys.exit(1)
        
        analyze_pr(args.repo, args.pr_number, token)
    elif args.command == "server":
        start_webhook_server(args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

