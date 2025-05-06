import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request
from pr_static_analysis.git import RepoOperator, GitHubClient, PullRequestContext
from pr_static_analysis.webhook import WebhookHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PR Static Analysis")

# Initialize webhook handler
webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
webhook_handler = WebhookHandler(secret=webhook_secret)

# Initialize GitHub client
github_token = os.environ.get("GITHUB_TOKEN")
github_client = GitHubClient(access_token=github_token)

# Define a handler for pull request events
def analyze_pr(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a pull request.
    
    Args:
        payload: Pull request event payload
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    # Parse PR context from payload
    pr_context = PullRequestContext.from_payload(payload)
    
    # Get repository information
    repo_full_name = pr_context.base.repo_full_name
    pr_number = pr_context.number
    
    logger.info(f"Analyzing PR #{pr_number} in {repo_full_name}")
    
    # Clone repository
    repo_path = f"/tmp/repos/{repo_full_name.replace('/', '_')}"
    repo_operator = RepoOperator(repo_path=repo_path, access_token=github_token)
    
    # Clone repository if it doesn't exist
    if not os.path.exists(repo_path):
        repo_url = f"https://github.com/{repo_full_name}.git"
        repo_operator.clone_repo(repo_url)
    
    # Get changed files
    changed_files = github_client.get_pr_files(repo_full_name, pr_number)
    
    # Analyze each file
    analysis_results = {}
    for file in changed_files:
        file_path = file.filename
        
        # Skip deleted files
        if file.status == "removed":
            continue
        
        # Get file content
        file_content = repo_operator.get_file_content(file_path, pr_context.head.sha)
        
        # Perform analysis (placeholder)
        # In a real implementation, this would call into the analysis engine
        analysis_results[file_path] = {
            "status": "analyzed",
            "issues": []  # Placeholder for analysis results
        }
    
    # Post results as a comment
    comment_body = "## PR Static Analysis Results\n\n"
    comment_body += f"Analyzed {len(analysis_results)} files.\n\n"
    
    # Add analysis results to comment
    for file_path, result in analysis_results.items():
        comment_body += f"### {file_path}\n"
        comment_body += f"Status: {result['status']}\n"
        comment_body += f"Issues: {len(result['issues'])}\n\n"
    
    # Post comment
    github_client.create_pr_comment(repo_full_name, pr_number, comment_body)
    
    return {
        "pr_number": pr_number,
        "repo": repo_full_name,
        "files_analyzed": len(analysis_results),
        "status": "completed"
    }

# Register handler for pull request events
webhook_handler.register_handler("pull_request.opened", analyze_pr)
webhook_handler.register_handler("pull_request.synchronize", analyze_pr)

# Define webhook endpoint
@app.post("/webhook/github")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events.
    """
    return await webhook_handler.handle_webhook(request)

# Define health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

