#!/usr/bin/env python3
"""
Comprehensive demo of the Codegen SDK functionality.

This script demonstrates all the key features of the Codegen SDK including:
- Agent initialization and configuration
- Task creation and management
- Error handling
- Webhook setup
- Repository management
- Usage statistics

Run with: python demo.py
"""

import os
import time
import json
from typing import List, Dict, Any

from .agent import Agent
from .task import Task
from .config import Config
from .exceptions import CodegenError, TaskError, AuthenticationError
from .utils import format_duration, get_current_timestamp


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def demo_configuration():
    """Demonstrate configuration options."""
    print_section("Configuration Demo")
    
    # Method 1: Environment variables
    print("1. Configuration from environment variables:")
    config = Config()
    print(f"   Org ID: {config.org_id or 'Not set'}")
    print(f"   Token: {'Set' if config.token else 'Not set'}")
    print(f"   Base URL: {config.base_url}")
    print(f"   Valid: {config.is_valid()}")
    
    # Method 2: Direct initialization
    print("\n2. Direct agent initialization:")
    try:
        # This would normally use real credentials
        print("   agent = Agent(org_id='your-org', token='your-token')")
        print("   (Skipping actual initialization in demo)")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 3: Configuration file
    print("\n3. Configuration from file:")
    print("   config = Config.from_file('.env')")
    print("   agent = Agent(org_id=config.org_id, token=config.token)")


def demo_basic_usage(agent: Agent):
    """Demonstrate basic SDK usage."""
    print_section("Basic Usage Demo")
    
    try:
        print("Creating a simple task...")
        task = agent.run(prompt="Review the latest commit for potential issues")
        
        print(f"✓ Task created: {task.task_id}")
        print(f"  Status: {task.status}")
        print(f"  Prompt: {task.prompt}")
        print(f"  Created: {task.created_at}")
        
        # Simulate checking status
        print("\nChecking task status...")
        task.refresh()
        print(f"  Current status: {task.status}")
        
        if task.status == "completed":
            print(f"  Result: {task.result}")
        elif task.status == "failed":
            print(f"  Error: {task.error}")
        
        return task
        
    except CodegenError as e:
        print(f"✗ Error creating task: {e}")
        return None


def demo_advanced_usage(agent: Agent):
    """Demonstrate advanced SDK features."""
    print_section("Advanced Usage Demo")
    
    try:
        print("Creating a task with advanced options...")
        
        # Advanced task with context and repository
        task = agent.run(
            prompt="Implement user authentication with JWT tokens",
            context={
                "requirements": [
                    "Use bcrypt for password hashing",
                    "Implement refresh token mechanism",
                    "Add rate limiting for login attempts"
                ],
                "files_to_modify": [
                    "src/auth/authentication.py",
                    "src/models/user.py",
                    "tests/test_auth.py"
                ],
                "priority": "high",
                "estimated_time": "2-3 hours"
            },
            repository="myorg/myapp",
            branch="feature/auth-system",
            priority="high"
        )
        
        print(f"✓ Advanced task created: {task.task_id}")
        print(f"  Repository: myorg/myapp")
        print(f"  Branch: feature/auth-system")
        print(f"  Priority: high")
        print(f"  Context keys: {list(task.metadata.get('context', {}).keys())}")
        
        # Demonstrate waiting for completion
        print("\nWaiting for task completion (demo - would normally wait)...")
        print("  task.wait_for_completion(timeout=600, poll_interval=10)")
        print("  (Skipping actual wait in demo)")
        
        # Demonstrate getting artifacts
        print("\nGetting task artifacts...")
        try:
            artifacts = task.get_artifacts()
            print(f"  Found {len(artifacts)} artifacts")
            for i, artifact in enumerate(artifacts[:3]):  # Show first 3
                print(f"    {i+1}. {artifact.get('type', 'Unknown')}: {artifact.get('name', 'Unnamed')}")
        except Exception as e:
            print(f"  Could not retrieve artifacts: {e}")
        
        return task
        
    except CodegenError as e:
        print(f"✗ Error creating advanced task: {e}")
        return None


def demo_task_management(agent: Agent):
    """Demonstrate task management features."""
    print_section("Task Management Demo")
    
    try:
        # List existing tasks
        print("Listing recent tasks...")
        tasks = agent.list_tasks(limit=5)
        
        print(f"✓ Found {len(tasks)} recent tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task.task_id[:12]}... - {task.status} - {task.prompt[:50]}...")
        
        if tasks:
            # Demonstrate getting task details
            print(f"\nGetting details for task: {tasks[0].task_id}")
            detailed_task = agent.get_task(tasks[0].task_id)
            
            print(f"  Status: {detailed_task.status}")
            print(f"  Created: {detailed_task.created_at}")
            print(f"  Updated: {detailed_task.updated_at}")
            
            if detailed_task.progress:
                print(f"  Progress: {detailed_task.progress}")
            
            # Demonstrate task cancellation (if running)
            if detailed_task.status in ["pending", "running"]:
                print(f"\nCancelling running task: {detailed_task.task_id}")
                try:
                    detailed_task.cancel()
                    print("  ✓ Task cancelled successfully")
                except TaskError as e:
                    print(f"  ✗ Could not cancel task: {e}")
        
        # Demonstrate filtering tasks by status
        print("\nFiltering completed tasks...")
        completed_tasks = agent.list_tasks(status="completed", limit=3)
        print(f"✓ Found {len(completed_tasks)} completed tasks")
        
    except CodegenError as e:
        print(f"✗ Error managing tasks: {e}")


def demo_batch_processing(agent: Agent):
    """Demonstrate batch task processing."""
    print_section("Batch Processing Demo")
    
    # Define a set of tasks to run
    task_prompts = [
        "Review PR #123 for security vulnerabilities",
        "Update API documentation for v2.0 endpoints",
        "Fix linting errors in the main codebase",
        "Add unit tests for the user service module",
        "Optimize database queries in the analytics module"
    ]
    
    print(f"Creating {len(task_prompts)} tasks for batch processing...")
    
    created_tasks = []
    
    try:
        # Create all tasks
        for i, prompt in enumerate(task_prompts, 1):
            print(f"  {i}. Creating: {prompt[:40]}...")
            task = agent.run(prompt=prompt, priority="normal")
            created_tasks.append(task)
            print(f"     ✓ Created: {task.task_id}")
        
        print(f"\n✓ Successfully created {len(created_tasks)} tasks")
        
        # Monitor task progress (simulation)
        print("\nMonitoring task progress...")
        print("  (In a real scenario, you would poll task status until completion)")
        
        for i, task in enumerate(created_tasks, 1):
            # Simulate checking status
            task.refresh()
            print(f"  {i}. {task.task_id[:12]}... - Status: {task.status}")
        
        # Demonstrate batch status checking
        print("\nBatch status summary:")
        status_counts = {}
        for task in created_tasks:
            status = task.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            print(f"  {status}: {count} tasks")
        
    except CodegenError as e:
        print(f"✗ Error in batch processing: {e}")


def demo_repository_management(agent: Agent):
    """Demonstrate repository management features."""
    print_section("Repository Management Demo")
    
    try:
        # Get available repositories
        print("Fetching available repositories...")
        repositories = agent.get_repositories()
        
        print(f"✓ Found {len(repositories)} available repositories:")
        for i, repo in enumerate(repositories[:5], 1):  # Show first 5
            print(f"  {i}. {repo.get('name', 'Unknown')}")
            print(f"     Description: {repo.get('description', 'No description')[:60]}...")
            print(f"     Language: {repo.get('language', 'Unknown')}")
            print(f"     Updated: {repo.get('updated_at', 'Unknown')}")
            print()
        
        if len(repositories) > 5:
            print(f"  ... and {len(repositories) - 5} more repositories")
        
    except CodegenError as e:
        print(f"✗ Error fetching repositories: {e}")


def demo_usage_statistics(agent: Agent):
    """Demonstrate usage statistics."""
    print_section("Usage Statistics Demo")
    
    try:
        # Get overall usage
        print("Fetching usage statistics...")
        usage = agent.get_usage()
        
        print("✓ Usage statistics:")
        print(f"  Total tasks: {usage.get('total_tasks', 'Unknown')}")
        print(f"  Completed tasks: {usage.get('completed_tasks', 'Unknown')}")
        print(f"  Failed tasks: {usage.get('failed_tasks', 'Unknown')}")
        print(f"  Total execution time: {usage.get('total_execution_time', 'Unknown')}")
        print(f"  Average task duration: {usage.get('average_duration', 'Unknown')}")
        
        # Get usage for specific date range
        print("\nFetching usage for current month...")
        monthly_usage = agent.get_usage(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        print("✓ Monthly usage statistics:")
        print(f"  Monthly tasks: {monthly_usage.get('total_tasks', 'Unknown')}")
        print(f"  Success rate: {monthly_usage.get('success_rate', 'Unknown')}%")
        
    except CodegenError as e:
        print(f"✗ Error fetching usage statistics: {e}")


def demo_webhook_setup(agent: Agent):
    """Demonstrate webhook setup."""
    print_section("Webhook Setup Demo")
    
    try:
        print("Setting up webhook for task events...")
        
        # Create a webhook (this would normally use a real URL)
        webhook_url = "https://your-app.com/webhooks/codegen"
        events = ["task.started", "task.completed", "task.failed", "task.cancelled"]
        
        print(f"  Webhook URL: {webhook_url}")
        print(f"  Events: {', '.join(events)}")
        
        # In a real scenario, you would call:
        # webhook = agent.create_webhook(url=webhook_url, events=events)
        
        print("  (Skipping actual webhook creation in demo)")
        print("✓ Webhook would be created successfully")
        
        print("\nWebhook payload example:")
        example_payload = {
            "event": "task.completed",
            "timestamp": get_current_timestamp(),
            "data": {
                "task_id": "task-123",
                "status": "completed",
                "result": "Task completed successfully",
                "duration": 120.5,
                "artifacts": [
                    {"type": "pull_request", "url": "https://github.com/org/repo/pull/456"}
                ]
            }
        }
        
        print(json.dumps(example_payload, indent=2))
        
    except CodegenError as e:
        print(f"✗ Error setting up webhook: {e}")


def demo_error_handling():
    """Demonstrate error handling patterns."""
    print_section("Error Handling Demo")
    
    print("Demonstrating various error scenarios...")
    
    # Authentication error
    print("\n1. Authentication Error:")
    try:
        # This would fail with invalid credentials
        print("   Attempting to create agent with invalid credentials...")
        print("   agent = Agent(org_id='invalid', token='invalid')")
        print("   → Would raise AuthenticationError")
    except AuthenticationError as e:
        print(f"   ✓ Caught AuthenticationError: {e}")
    
    # Validation error
    print("\n2. Validation Error:")
    try:
        # This would fail validation
        print("   Attempting to run task with empty prompt...")
        print("   agent.run(prompt='')")
        print("   → Would raise ValidationError")
    except Exception as e:
        print(f"   ✓ Would catch ValidationError: {e}")
    
    # Task error
    print("\n3. Task Error:")
    print("   Attempting to wait for non-existent task...")
    print("   task.wait_for_completion(timeout=1)")
    print("   → Would raise TaskError if task fails or times out")
    
    # API error
    print("\n4. API Error:")
    print("   Making request to invalid endpoint...")
    print("   agent._make_request('GET', '/invalid')")
    print("   → Would raise APIError with status code and details")
    
    print("\n✓ Error handling patterns demonstrated")


def main():
    """Main demo function."""
    print("Codegen SDK Comprehensive Demo")
    print("==============================")
    print("This demo showcases all the key features of the Codegen SDK.")
    print("Note: Some operations are simulated to avoid making real API calls.")
    
    # Check configuration
    config = Config()
    
    if not config.is_valid():
        print("\n⚠️  Configuration Notice:")
        print("To run this demo with real API calls, set these environment variables:")
        print("  export CODEGEN_ORG_ID='your-org-id'")
        print("  export CODEGEN_TOKEN='your-api-token'")
        print("Get your API token from: https://codegen.sh/token")
        print("\nRunning demo in simulation mode...\n")
        
        # Run configuration demo
        demo_configuration()
        demo_error_handling()
        
        print_section("Demo Complete")
        print("This was a simulated demo. To see real functionality:")
        print("1. Set your CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables")
        print("2. Run the demo again")
        print("3. Or use the individual example functions in examples.py")
        return
    
    # Real demo with actual agent
    try:
        print(f"Initializing agent for organization: {config.org_id}")
        agent = Agent(
            org_id=config.org_id,
            token=config.token,
            base_url=config.base_url
        )
        print("✓ Agent initialized successfully")
        
        # Run all demos
        demo_configuration()
        demo_basic_usage(agent)
        demo_advanced_usage(agent)
        demo_task_management(agent)
        demo_batch_processing(agent)
        demo_repository_management(agent)
        demo_usage_statistics(agent)
        demo_webhook_setup(agent)
        demo_error_handling()
        
        print_section("Demo Complete")
        print("✓ All demos completed successfully!")
        print("Check the output above for detailed examples of SDK usage.")
        
    except CodegenError as e:
        print(f"✗ Demo failed: {e}")
        print("Please check your credentials and try again.")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    main()

