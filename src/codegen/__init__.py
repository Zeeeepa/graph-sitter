"""
Codegen SDK - Python SDK to interact with Codegen SWE agents via API.

The Codegen SDK enables developers to programmatically interact with Codegen SWE agents via API.
Codegen agents can research code, create PRs, modify Linear tickets, and more.

Example usage:
    from codegen import Agent

    # Initialize the Agent with your organization ID and API token
    agent = Agent(org_id="...", token="...")

    # Run an agent with a prompt
    task = agent.run(prompt="Leave a review on PR #123")

    # Check the initial status
    print(task.status)

    # Refresh the task to get updated status (tasks can take time)
    task.refresh()

    if task.status == "completed":
        print(task.result)  # Result often contains code, summaries, or links
"""

from .agent import Agent
from .task import Task
from .exceptions import CodegenError, AuthenticationError, TaskError

__version__ = "1.0.0"
__all__ = ["Agent", "Task", "CodegenError", "AuthenticationError", "TaskError"]

