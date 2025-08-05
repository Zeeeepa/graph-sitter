"""
Command-line interface for the Codegen SDK.
"""

import argparse
import json
import sys
import time
from typing import Optional, Dict, Any

from .agent import Agent
from .config import Config
from .exceptions import CodegenError
from .utils import format_duration, get_current_timestamp


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="Codegen SDK Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a simple task
  codegen run "Review PR #123"
  
  # Run with specific repository and context
  codegen run "Fix authentication bug" --repo myorg/myrepo --branch develop
  
  # List recent tasks
  codegen list --status completed --limit 10
  
  # Get task details
  codegen get task-id-123
  
  # Check usage statistics
  codegen usage --start-date 2024-01-01
        """
    )
    
    # Global options
    parser.add_argument("--org-id", help="Organization ID (or set CODEGEN_ORG_ID)")
    parser.add_argument("--token", help="API token (or set CODEGEN_TOKEN)")
    parser.add_argument("--base-url", help="API base URL", default="https://api.codegen.com")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a new task")
    run_parser.add_argument("prompt", help="Task prompt")
    run_parser.add_argument("--repo", "--repository", help="Target repository (owner/repo)")
    run_parser.add_argument("--branch", help="Target branch")
    run_parser.add_argument("--priority", choices=["low", "normal", "high"], default="normal")
    run_parser.add_argument("--context", help="Additional context (JSON string)")
    run_parser.add_argument("--wait", action="store_true", help="Wait for task completion")
    run_parser.add_argument("--timeout", type=int, default=300, help="Wait timeout in seconds")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get task details")
    get_parser.add_argument("task_id", help="Task ID")
    get_parser.add_argument("--artifacts", action="store_true", help="Include artifacts")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of tasks")
    list_parser.add_argument("--offset", type=int, default=0, help="Number of tasks to skip")
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a task")
    cancel_parser.add_argument("task_id", help="Task ID")
    
    # Usage command
    usage_parser = subparsers.add_parser("usage", help="Get usage statistics")
    usage_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    usage_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    
    # Repositories command
    repos_parser = subparsers.add_parser("repos", help="List available repositories")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")
    
    return parser


def setup_agent(args: argparse.Namespace) -> Agent:
    """Set up the Agent instance from command-line arguments."""
    
    # Load configuration
    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config()
    
    # Override with command-line arguments
    org_id = args.org_id or config.org_id
    token = args.token or config.token
    base_url = args.base_url or config.base_url
    
    if not org_id or not token:
        print("Error: Organization ID and token are required")
        print("Set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables")
        print("Or use --org-id and --token command-line options")
        print("Get your API token from: https://codegen.sh/token")
        sys.exit(1)
    
    try:
        return Agent(org_id=org_id, token=token, base_url=base_url)
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def output_result(data: Any, json_format: bool = False) -> None:
    """Output result in the specified format."""
    
    if json_format:
        if hasattr(data, 'to_dict'):
            print(json.dumps(data.to_dict(), indent=2))
        elif isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(str(data), indent=2))
    else:
        print(data)


def cmd_run(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'run' command."""
    
    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in context argument")
            sys.exit(1)
    
    try:
        task = agent.run(
            prompt=args.prompt,
            context=context,
            repository=args.repo,
            branch=args.branch,
            priority=args.priority
        )
        
        if args.json:
            output_result(task, json_format=True)
        else:
            print(f"Task created: {task.task_id}")
            print(f"Status: {task.status}")
            print(f"Prompt: {task.prompt}")
        
        if args.wait:
            print(f"Waiting for completion (timeout: {args.timeout}s)...")
            start_time = time.time()
            
            try:
                task.wait_for_completion(timeout=args.timeout)
                duration = time.time() - start_time
                
                if args.json:
                    output_result(task, json_format=True)
                else:
                    print(f"Task completed in {format_duration(duration)}")
                    print(f"Result: {task.result}")
                    
            except Exception as e:
                print(f"Error waiting for completion: {e}")
                sys.exit(1)
                
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_get(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'get' command."""
    
    try:
        task = agent.get_task(args.task_id)
        
        if args.json:
            result = task.to_dict()
            if args.artifacts:
                result["artifacts"] = task.get_artifacts()
            output_result(result, json_format=True)
        else:
            print(f"Task ID: {task.task_id}")
            print(f"Status: {task.status}")
            print(f"Created: {task.created_at}")
            print(f"Updated: {task.updated_at}")
            print(f"Prompt: {task.prompt}")
            
            if task.result:
                print(f"Result: {task.result}")
            if task.error:
                print(f"Error: {task.error}")
            
            if args.artifacts:
                artifacts = task.get_artifacts()
                if artifacts:
                    print("Artifacts:")
                    for artifact in artifacts:
                        print(f"  - {artifact}")
                        
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_list(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'list' command."""
    
    try:
        tasks = agent.list_tasks(
            status=args.status,
            limit=args.limit,
            offset=args.offset
        )
        
        if args.json:
            output_result([task.to_dict() for task in tasks], json_format=True)
        else:
            if not tasks:
                print("No tasks found")
                return
            
            print(f"Found {len(tasks)} tasks:")
            print()
            
            for task in tasks:
                print(f"ID: {task.task_id}")
                print(f"Status: {task.status}")
                print(f"Created: {task.created_at}")
                print(f"Prompt: {task.prompt[:80]}{'...' if len(task.prompt) > 80 else ''}")
                print("-" * 50)
                
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_cancel(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'cancel' command."""
    
    try:
        task = agent.get_task(args.task_id)
        task.cancel()
        
        if args.json:
            output_result(task, json_format=True)
        else:
            print(f"Task {task.task_id} cancelled")
            
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_usage(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'usage' command."""
    
    try:
        usage = agent.get_usage(
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        output_result(usage, json_format=args.json)
        
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_repos(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'repos' command."""
    
    try:
        repositories = agent.get_repositories()
        
        if args.json:
            output_result(repositories, json_format=True)
        else:
            if not repositories:
                print("No repositories found")
                return
            
            print("Available repositories:")
            for repo in repositories:
                print(f"  - {repo.get('name', 'Unknown')}: {repo.get('description', 'No description')}")
                
    except CodegenError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_config(agent: Agent, args: argparse.Namespace) -> None:
    """Handle the 'config' command."""
    
    config = Config()
    
    if args.json:
        output_result(config.to_dict(), json_format=True)
    else:
        print("Current configuration:")
        print(f"  Organization ID: {config.org_id or 'Not set'}")
        print(f"  Token: {'Set' if config.token else 'Not set'}")
        print(f"  Base URL: {config.base_url}")
        print(f"  Timeout: {config.timeout}s")
        print(f"  Max Retries: {config.max_retries}")
        print(f"  Debug: {config.debug}")


def main() -> None:
    """Main CLI entry point."""
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Handle config command separately (doesn't need agent)
    if args.command == "config":
        cmd_config(None, args)
        return
    
    # Set up agent for other commands
    agent = setup_agent(args)
    
    # Dispatch to command handlers
    command_handlers = {
        "run": cmd_run,
        "get": cmd_get,
        "list": cmd_list,
        "cancel": cmd_cancel,
        "usage": cmd_usage,
        "repos": cmd_repos,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        handler(agent, args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

