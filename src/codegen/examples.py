"""
Example usage of the Codegen SDK.

This module contains practical examples of how to use the Codegen SDK
to interact with Codegen SWE agents programmatically.
"""

import os
import time
from typing import List, Dict, Any

from .agent import Agent
from .task import Task
from .config import Config
from .exceptions import CodegenError, TaskError


def basic_usage_example():
    """Basic example of using the Codegen SDK."""
    
    # Initialize the Agent with your organization ID and API token
    agent = Agent(org_id="your-org-id", token="your-api-token")
    
    # Run an agent with a prompt
    task = agent.run(prompt="Leave a review on PR #123")
    
    # Check the initial status
    print(f"Task status: {task.status}")
    
    # Refresh the task to get updated status (tasks can take time)
    task.refresh()
    
    if task.status == "completed":
        print(f"Task result: {task.result}")
    elif task.status == "failed":
        print(f"Task failed: {task.error}")


def advanced_usage_example():
    """Advanced example with context and repository specification."""
    
    # Load configuration from environment or file
    config = Config()
    
    if not config.is_valid():
        print("Please set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables")
        return
    
    agent = Agent(
        org_id=config.org_id,
        token=config.token,
        base_url=config.base_url
    )
    
    # Run a task with additional context
    task = agent.run(
        prompt="Fix the authentication bug in the login component",
        context={
            "issue_number": 456,
            "priority": "high",
            "affected_files": ["src/auth/login.py", "tests/test_auth.py"]
        },
        repository="myorg/myrepo",
        branch="develop",
        priority="high"
    )
    
    print(f"Created task: {task.task_id}")
    
    # Wait for completion with timeout
    try:
        task.wait_for_completion(timeout=600, poll_interval=10)
        print(f"Task completed successfully!")
        print(f"Result: {task.result}")
        
        # Get artifacts (e.g., created PRs, modified files)
        artifacts = task.get_artifacts()
        for artifact in artifacts:
            print(f"Artifact: {artifact}")
            
    except TaskError as e:
        print(f"Task failed or timed out: {e}")


def batch_tasks_example():
    """Example of running multiple tasks and managing them."""
    
    agent = Agent(org_id="your-org-id", token="your-api-token")
    
    # List of tasks to run
    prompts = [
        "Review PR #123 for security issues",
        "Update documentation for the new API endpoints",
        "Fix linting errors in the codebase",
        "Add unit tests for the user service"
    ]
    
    # Start all tasks
    tasks = []
    for prompt in prompts:
        task = agent.run(prompt=prompt, priority="normal")
        tasks.append(task)
        print(f"Started task: {task.task_id}")
    
    # Monitor all tasks
    completed_tasks = []
    failed_tasks = []
    
    while len(completed_tasks) + len(failed_tasks) < len(tasks):
        for task in tasks:
            if task in completed_tasks or task in failed_tasks:
                continue
                
            task.refresh()
            
            if task.status == "completed":
                completed_tasks.append(task)
                print(f"Task {task.task_id} completed: {task.result}")
            elif task.status == "failed":
                failed_tasks.append(task)
                print(f"Task {task.task_id} failed: {task.error}")
        
        time.sleep(5)  # Wait before checking again
    
    print(f"Completed: {len(completed_tasks)}, Failed: {len(failed_tasks)}")


def webhook_example():
    """Example of setting up webhooks for task events."""
    
    agent = Agent(org_id="your-org-id", token="your-api-token")
    
    # Create a webhook to receive task updates
    webhook = agent.create_webhook(
        url="https://your-app.com/webhooks/codegen",
        events=["task.completed", "task.failed", "task.started"]
    )
    
    print(f"Created webhook: {webhook}")
    
    # Now when tasks complete, your webhook will be called
    task = agent.run(prompt="Analyze code quality in the main branch")
    print(f"Task started: {task.task_id}")


def repository_management_example():
    """Example of managing repositories and getting usage stats."""
    
    agent = Agent(org_id="your-org-id", token="your-api-token")
    
    # Get available repositories
    repositories = agent.get_repositories()
    print("Available repositories:")
    for repo in repositories:
        print(f"  - {repo['name']}: {repo['description']}")
    
    # Get usage statistics
    usage = agent.get_usage(start_date="2024-01-01", end_date="2024-01-31")
    print(f"Usage stats: {usage}")
    
    # List recent tasks
    recent_tasks = agent.list_tasks(limit=10)
    print("Recent tasks:")
    for task in recent_tasks:
        print(f"  - {task.task_id}: {task.status} - {task.prompt[:50]}...")


def error_handling_example():
    """Example of proper error handling."""
    
    try:
        agent = Agent(org_id="invalid-org", token="invalid-token")
    except CodegenError as e:
        print(f"Authentication failed: {e}")
        return
    
    try:
        # This will fail due to invalid prompt
        task = agent.run(prompt="")
    except CodegenError as e:
        print(f"Validation error: {e}")
    
    try:
        # Run a valid task
        task = agent.run(prompt="Review the latest commit")
        
        # Wait for completion with error handling
        task.wait_for_completion(timeout=300)
        
    except TaskError as e:
        print(f"Task error: {e}")
        
        # Try to cancel if still running
        if task.status in ["pending", "running"]:
            try:
                task.cancel()
                print("Task cancelled successfully")
            except TaskError as cancel_error:
                print(f"Failed to cancel task: {cancel_error}")


def configuration_example():
    """Example of different configuration methods."""
    
    # Method 1: Direct initialization
    agent1 = Agent(org_id="org-123", token="token-456")
    
    # Method 2: From environment variables
    # Set CODEGEN_ORG_ID and CODEGEN_TOKEN
    config = Config()
    if config.is_valid():
        agent2 = Agent(org_id=config.org_id, token=config.token)
    
    # Method 3: From configuration file
    # Create a .env file with your credentials
    config_from_file = Config.from_file(".env")
    if config_from_file.is_valid():
        agent3 = Agent(
            org_id=config_from_file.org_id,
            token=config_from_file.token,
            base_url=config_from_file.base_url,
            timeout=config_from_file.timeout
        )


if __name__ == "__main__":
    """Run examples when script is executed directly."""
    
    print("Codegen SDK Examples")
    print("===================")
    
    # Check if credentials are available
    config = Config()
    if not config.is_valid():
        print("Please set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables to run examples")
        print("You can get your API token from: https://codegen.sh/token")
        exit(1)
    
    print("Running basic usage example...")
    try:
        basic_usage_example()
    except Exception as e:
        print(f"Basic example failed: {e}")
    
    print("\nRunning advanced usage example...")
    try:
        advanced_usage_example()
    except Exception as e:
        print(f"Advanced example failed: {e}")
    
    print("\nExamples completed!")

