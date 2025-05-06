# PR Static Analysis System

This module provides a GitHub integration for the PR static analysis system. It allows the system to fetch PR data, analyze it, and post results back to GitHub.

## Components

### 1. GitHub API Client (`github_api_client.py`)

The `GitHubAPIClient` class extends the basic `GithubClient` functionality with methods specifically designed for PR static analysis:

- Fetching PR data (files, commits, comments)
- Handling rate limits with exponential backoff
- Posting analysis results as comments

### 2. Webhook Handler (`webhook_handler.py`)

The `WebhookHandler` class processes GitHub webhook events, validates them, and routes them to the appropriate handlers:

- Validates webhook signatures using HMAC
- Routes events to registered handlers based on event type
- Provides a simple HTTP server for local development

### 3. PR Data Models

- `PRFile`: Represents a file in a GitHub pull request
- `PRCommit`: Represents a commit in a GitHub pull request
- `PRComment`: Represents a comment on a GitHub pull request
- `PRReviewComment`: Represents a review comment on a specific line

### 4. Comment Formatter (`comment_formatter.py`)

The `CommentFormatter` class formats static analysis results as GitHub comments:

- General PR comments with analysis summaries
- Inline comments for specific issues
- Summary comments with statistics
- Error comments for reporting problems

### 5. Authentication and Authorization (`github_auth.py`)

The `GitHubAuth` class provides authentication with GitHub using different methods:

- Personal access tokens
- OAuth tokens
- GitHub App authentication with JWT and installation tokens

The `GitHubPermissions` class checks if a user or token has the required permissions for certain operations.

### 6. PR Analyzer (`pr_analyzer.py`)

The `PRAnalyzer` class provides the main PR static analysis functionality:

- Fetches PR data from GitHub
- Analyzes the PR data to find issues
- Posts analysis results back to GitHub as comments

### 7. Webhook Server (`webhook_server.py`)

The `PRAnalysisWebhookServer` class provides an HTTP server for receiving GitHub webhook events and triggering PR static analysis.

## Usage

### Basic Usage

```python
from graph_sitter.git.auth.github_auth import GitHubAuth
from graph_sitter.git.clients.github_api_client import GitHubAPIClient
from graph_sitter.git.pr_analysis.pr_analyzer import PRAnalyzer

# Create GitHub client
github_auth = GitHubAuth.from_env()
github_client = GitHubAPIClient(token=github_auth.token)

# Create PR analyzer
analyzer = PRAnalyzer(github_client=github_client)

# Analyze a PR
results = analyzer.analyze_pr("owner/repo", 123)
```

### Running the Webhook Server

```python
from graph_sitter.git.pr_analysis.webhook_server import create_webhook_server_from_env

# Create webhook server from environment variables
server = create_webhook_server_from_env(port=8000)

# Start server
server.start()
```

### Environment Variables

The following environment variables are used:

- `GITHUB_TOKEN`: GitHub personal access token or OAuth token
- `GITHUB_APP_ID`: GitHub App ID
- `GITHUB_APP_PRIVATE_KEY`: GitHub App private key (base64 encoded)
- `GITHUB_APP_INSTALLATION_ID`: GitHub App installation ID
- `GITHUB_WEBHOOK_SECRET`: Secret for validating webhook signatures
- `PORT`: Port for the webhook server (default: 8000)

## GitHub App Setup

1. Create a GitHub App at https://github.com/settings/apps/new
2. Set the webhook URL to your server URL
3. Set the webhook secret
4. Grant the following permissions:
   - Repository contents: Read
   - Pull requests: Read & Write
   - Commit statuses: Read & Write
5. Subscribe to the following events:
   - Pull request
   - Pull request review
   - Pull request review comment
6. Install the app on your repositories
7. Set the environment variables with your app's credentials

## Local Development

For local development, you can use tools like ngrok to expose your local server to the internet:

```bash
# Start the webhook server
python -m graph_sitter.git.pr_analysis.webhook_server

# In another terminal, expose the server
ngrok http 8000
```

Then set the webhook URL in your GitHub App settings to the ngrok URL.

