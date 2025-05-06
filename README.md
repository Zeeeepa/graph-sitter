# PR Static Analysis System

A system for analyzing GitHub pull requests and providing feedback.

## Overview

This system integrates with GitHub to analyze pull requests and provide feedback through comments and status checks. It consists of several components:

- **RepoOperator**: Manages Git repository operations
- **GitHubClient**: Interacts with the GitHub API
- **PR Models**: Represents GitHub pull request data
- **Webhook Handler**: Processes GitHub webhook events

## Installation

```bash
pip install -e .
```

## Usage

### Setting up the webhook server

```python
from fastapi import FastAPI, Request
from pr_static_analysis.webhook import WebhookHandler

app = FastAPI()
webhook_handler = WebhookHandler(secret="your-webhook-secret")

@app.post("/webhook/github")
async def github_webhook(request: Request):
    return await webhook_handler.handle_webhook(request)
```

### Analyzing a pull request

```python
from pr_static_analysis.git import RepoOperator, GitHubClient, PullRequestContext

# Initialize clients
github_client = GitHubClient(access_token="your-github-token")
repo_operator = RepoOperator(repo_path="/path/to/repo", access_token="your-github-token")

# Get PR data
pr = github_client.get_pr("owner/repo", 123)
pr_context = PullRequestContext.from_github_pr(pr._rawData)

# Get changed files
changed_files = github_client.get_pr_files("owner/repo", 123)

# Analyze files
# ...

# Post results
github_client.create_pr_comment("owner/repo", 123, "Analysis results...")
```

## Components

### RepoOperator

The `RepoOperator` class provides methods for interacting with Git repositories:

- `clone_repo(repo_url)`: Clone a repository
- `checkout_branch(branch_name)`: Checkout a branch
- `checkout_commit(commit_sha)`: Checkout a specific commit
- `get_file_content(file_path, ref)`: Get content of a file at a specific ref
- `get_changed_files(base_ref, head_ref)`: Get files changed between two refs
- `get_diff(file_path, base_ref, head_ref)`: Get diff for a specific file

### GitHubClient

The `GitHubClient` class provides methods for interacting with the GitHub API:

- `get_pr(repo, pr_number)`: Get a specific PR
- `get_pr_files(repo, pr_number)`: Get files changed in a PR
- `get_pr_commits(repo, pr_number)`: Get commits in a PR
- `get_pr_reviews(repo, pr_number)`: Get reviews for a PR
- `create_pr_comment(repo, pr_number, body)`: Create a general comment on a PR
- `create_pr_review_comment(repo, pr_number, body, commit_sha, path, line)`: Create an inline comment on a PR
- `create_status(repo, commit_sha, state, description, context)`: Create a status for a commit

### WebhookHandler

The `WebhookHandler` class processes GitHub webhook events:

- `register_handler(event_type, handler)`: Register a handler for a specific event type
- `handle_webhook(request)`: Handle a webhook request
- `route_event(event_type, action, payload)`: Route an event to the appropriate handlers
- `handle_pr_event(payload)`: Handle a pull request event
- `handle_push_event(payload)`: Handle a push event
- `handle_review_event(payload)`: Handle a pull request review event

## License

MIT

