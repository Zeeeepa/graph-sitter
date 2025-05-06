# GitHub Integration for PR Static Analysis

This module provides integration with GitHub for the PR static analysis system. It allows the system to retrieve PR data from GitHub, analyze it, and post results back to GitHub as comments.

## Components

### PRGitHubClient

The `PRGitHubClient` extends the base `GithubClient` to provide PR-specific functionality:

- Retrieving PR data
- Getting PR files and commits
- Posting comments on PRs
- Posting review comments on specific lines in PRs

### GitHubWebhookHandler

The `GitHubWebhookHandler` handles GitHub webhook events:

- Receiving and validating webhook payloads
- Extracting PR information from the payload
- Triggering PR analysis
- Posting analysis results back to GitHub

### GitHubCommentFormatter

The `GitHubCommentFormatter` formats analysis results as GitHub comments:

- Grouping results by severity
- Adding severity icons
- Formatting code snippets
- Adding suggestions for fixing issues

### PRAnalyzer

The `PRAnalyzer` orchestrates the PR analysis process:

- Retrieving PR data from GitHub
- Creating analysis contexts for the base and head branches
- Invoking the rule engine to apply rules
- Collecting and aggregating results
- Generating a final analysis report

## Usage

```python
from graph_sitter.extensions.github.pr_analysis import (
    PRGitHubClient,
    GitHubWebhookHandler,
    GitHubCommentFormatter,
    PRAnalyzer
)

# Create components
github_client = PRGitHubClient(token="your-github-token")
rule_engine = YourRuleEngine()  # Implement your own rule engine
comment_formatter = GitHubCommentFormatter()
pr_analyzer = PRAnalyzer(github_client, rule_engine, comment_formatter)

# Create webhook handler
webhook_handler = GitHubWebhookHandler(pr_analyzer, webhook_secret="your-webhook-secret")

# Set up FastAPI app
app = webhook_handler.app

# Run the app
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Webhook Setup

To set up a GitHub webhook:

1. Go to your repository settings
2. Click on "Webhooks"
3. Click "Add webhook"
4. Set the Payload URL to your webhook endpoint (e.g., `https://your-server.com/webhook`)
5. Set the Content type to `application/json`
6. Set a secret (optional but recommended)
7. Select the events you want to receive (at least "Pull requests")
8. Click "Add webhook"

## Environment Variables

- `GITHUB_TOKEN`: GitHub API token
- `WEBHOOK_SECRET`: Secret for validating webhook payloads

