"""Example usage of the autogenlib module."""

import asyncio
import os
from pathlib import Path

from src.codegen.autogenlib import AutogenClient, AutogenConfig, OrchestratorInterface, SimpleInterface


def basic_usage_example():
    """Basic usage example with SimpleInterface."""
    print("=== Basic Usage Example ===")
    
    # Create configuration
    config = AutogenConfig(
        org_id=os.getenv("CODEGEN_ORG_ID", "your_org_id"),
        token=os.getenv("CODEGEN_TOKEN", "your_token"),
        enable_context_enhancement=True,
        cache_enabled=True,
    )
    
    # Create simple interface
    interface = SimpleInterface(config)
    
    # Run a simple task
    response = interface.run_task(
        prompt="Create a simple Python function that calculates the factorial of a number",
        codebase_path="./src",  # Optional: provide codebase for context
    )
    
    print(f"Task ID: {response.task_id}")
    print(f"Status: {response.status}")
    print(f"Result: {response.result}")
    
    # Get usage statistics
    stats = interface.get_usage_stats()
    print(f"Usage Stats: {stats}")
    
    # Health check
    health = interface.health_check()
    print(f"Health: {health}")


async def async_usage_example():
    """Async usage example with OrchestratorInterface."""
    print("\n=== Async Usage Example ===")
    
    # Create configuration
    config = AutogenConfig(
        org_id=os.getenv("CODEGEN_ORG_ID", "your_org_id"),
        token=os.getenv("CODEGEN_TOKEN", "your_token"),
        enable_async_processing=True,
        max_concurrent_tasks=3,
        enable_context_enhancement=True,
    )
    
    # Create orchestrator interface
    interface = OrchestratorInterface(config)
    
    try:
        # Submit multiple tasks
        tasks = []
        prompts = [
            "Create a Python class for managing user authentication",
            "Write unit tests for a REST API endpoint",
            "Implement a caching layer for database queries",
        ]
        
        for prompt in prompts:
            response = await interface.submit_task(
                prompt=prompt,
                codebase_path="./src",
                enhance_context=True,
            )
            tasks.append(response.task_id)
            print(f"Submitted task {response.task_id}: {prompt[:50]}...")
        
        # Monitor task progress
        print("\nMonitoring task progress...")
        completed_tasks = 0
        
        while completed_tasks < len(tasks):
            for task_id in tasks:
                status_response = await interface.get_task_status(task_id)
                if status_response and status_response.status.value in ["completed", "failed"]:
                    if task_id not in [t for t in tasks if t.endswith("_done")]:
                        print(f"Task {task_id} {status_response.status.value}")
                        if status_response.result:
                            print(f"Result: {status_response.result[:100]}...")
                        completed_tasks += 1
                        tasks[tasks.index(task_id)] = task_id + "_done"
            
            await asyncio.sleep(2)
        
        # Get final statistics
        stats = await interface.get_usage_stats()
        print(f"\nFinal Usage Stats: {stats}")
        
        # List all tasks
        all_tasks = await interface.list_tasks()
        print(f"\nTotal tasks processed: {len(all_tasks)}")
        
    finally:
        # Cleanup
        await interface.shutdown()


def context_enhancement_example():
    """Example showing context enhancement capabilities."""
    print("\n=== Context Enhancement Example ===")
    
    # Create configuration with context enhancement enabled
    config = AutogenConfig(
        org_id=os.getenv("CODEGEN_ORG_ID", "your_org_id"),
        token=os.getenv("CODEGEN_TOKEN", "your_token"),
        enable_context_enhancement=True,
        include_file_summaries=True,
        include_class_summaries=True,
        include_function_summaries=True,
        max_context_length=8000,
    )
    
    # Create client
    client = AutogenClient(config)
    
    # Find a Python project directory
    current_dir = Path(".")
    python_files = list(current_dir.rglob("*.py"))
    
    if python_files:
        project_root = python_files[0].parent
        print(f"Using project root: {project_root}")
        
        # Run task with context enhancement
        from src.codegen.autogenlib.models import TaskRequest
        
        request = TaskRequest(
            prompt="Analyze this codebase and suggest improvements for code organization and structure",
            codebase_path=str(project_root),
            enhance_context=True,
        )
        
        response = client.run_task(request)
        
        print(f"Task ID: {response.task_id}")
        print(f"Status: {response.status}")
        print(f"Result: {response.result}")
    else:
        print("No Python files found for context enhancement example")


def error_handling_example():
    """Example showing error handling."""
    print("\n=== Error Handling Example ===")
    
    # Create configuration with invalid credentials
    config = AutogenConfig(
        org_id="invalid_org",
        token="invalid_token",
        max_retries=2,
        retry_delay=1.0,
    )
    
    try:
        client = AutogenClient(config)
        
        # This should fail due to invalid credentials
        from src.codegen.autogenlib.models import TaskRequest
        
        request = TaskRequest(prompt="This will fail")
        response = client.run_task(request)
        
        print(f"Unexpected success: {response}")
        
    except Exception as e:
        print(f"Expected error occurred: {e}")
        print("Error handling is working correctly")


def main():
    """Run all examples."""
    print("Autogenlib Usage Examples")
    print("=" * 50)
    
    # Check if credentials are available
    if not os.getenv("CODEGEN_ORG_ID") or not os.getenv("CODEGEN_TOKEN"):
        print("Warning: CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables not set")
        print("Some examples may fail. Set these variables to test with real Codegen API.")
        print()
    
    # Run examples
    try:
        basic_usage_example()
    except Exception as e:
        print(f"Basic usage example failed: {e}")
    
    try:
        asyncio.run(async_usage_example())
    except Exception as e:
        print(f"Async usage example failed: {e}")
    
    try:
        context_enhancement_example()
    except Exception as e:
        print(f"Context enhancement example failed: {e}")
    
    try:
        error_handling_example()
    except Exception as e:
        print(f"Error handling example failed: {e}")


if __name__ == "__main__":
    main()

