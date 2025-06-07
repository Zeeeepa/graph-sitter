"""
Example usage of the Codegen Agent API Overlay Extension

This example demonstrates how to use the overlay extension with the standard codegen API.
"""

import logging
import time

# Set up logging to see overlay operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("🚀 Codegen Agent API Overlay Extension Example")
    print("=" * 50)
    
    # Step 1: Apply the overlay
    print("\n1. Applying overlay to codegen package...")
    try:
        from contexten.extensions.codegen_agent_api import apply_codegen_overlay
        overlay = apply_codegen_overlay()
        print("✅ Overlay applied successfully!")
        
        # Get overlay status
        status = overlay.get_status()
        print(f"   📦 Package version: {status['package_info']['version']}")
        print(f"   📍 Package location: {status['package_info']['location']}")
        
    except Exception as e:
        print(f"❌ Failed to apply overlay: {e}")
        print("   Make sure you have installed codegen: pip install codegen")
        return
    
    # Step 2: Set up event handlers
    print("\n2. Setting up event handlers...")
    from contexten.extensions.codegen_agent_api import register_event_handler
    
    def on_agent_created(data):
        print(f"   🤖 Agent created for org: {data.get('org_id', 'unknown')}")
    
    def on_task_created(data):
        print(f"   📝 Task created: {data.get('task_id', 'unknown')}")
    
    def on_task_status_changed(data):
        task_id = data.get('task_id', 'unknown')
        old_status = data.get('old_status', 'unknown')
        new_status = data.get('new_status', 'unknown')
        print(f"   🔄 Task {task_id}: {old_status} → {new_status}")
    
    def on_task_finished(data):
        task_id = data.get('task_id', 'unknown')
        duration = data.get('duration', 0)
        print(f"   ✅ Task {task_id} finished in {duration:.2f}s")
    
    # Register event handlers
    register_event_handler("agent_created", on_agent_created)
    register_event_handler("task_created", on_task_created)
    register_event_handler("task_status_changed", on_task_status_changed)
    register_event_handler("task_finished", on_task_finished)
    
    print("✅ Event handlers registered!")
    
    # Step 3: Use codegen normally - API unchanged!
    print("\n3. Using codegen with enhanced functionality...")
    print("   Note: This will use the standard codegen API")
    
    try:
        # Import and use codegen normally
        from codegen.agents.agent import Agent
        
        # Create agent (you would use your real org_id and token)
        print("   Creating agent...")
        agent = Agent(
            org_id="11",  # Replace with your org_id
            token="demo_token",  # Replace with your actual token
            base_url="https://codegen-sh-rest-api.modal.run"
        )
        
        # The agent now has enhanced functionality!
        print("   🎯 Agent created with enhanced contexten integration!")
        
        # Get integration metrics
        metrics = agent.get_integration_metrics()
        print(f"   📊 Agents created: {metrics['agents_created']}")
        print(f"   📊 Tasks run: {metrics['tasks_run']}")
        print(f"   📊 Uptime: {metrics['uptime_seconds']:.2f}s")
        
        # Example task (commented out since we don't have real credentials)
        print("\n   Example task creation (commented out - requires real credentials):")
        print("   # task = agent.run('Which github repos can you currently access?')")
        print("   # task.wait_for_completion(timeout=300)")
        print("   # print(task.result)")
        
    except ImportError as e:
        print(f"   ❌ Could not import codegen: {e}")
        print("   Make sure you have installed codegen: pip install codegen")
        return
    except Exception as e:
        print(f"   ⚠️  Note: {e}")
        print("   (This is expected without real credentials)")
    
    # Step 4: Show overlay metrics
    print("\n4. Overlay metrics and status...")
    from contexten.extensions.codegen_agent_api import get_overlay_metrics
    
    metrics = get_overlay_metrics()
    if metrics['applied']:
        integration_metrics = metrics.get('integration_metrics', {})
        print(f"   📊 Overlay calls: {integration_metrics.get('overlay_calls', 0)}")
        print(f"   📊 Agents created: {integration_metrics.get('agents_created', 0)}")
        print(f"   📊 Tasks run: {integration_metrics.get('tasks_run', 0)}")
        print(f"   📊 Errors: {integration_metrics.get('errors', 0)}")
        print(f"   📊 Event handlers: {integration_metrics.get('event_handlers', {})}")
    else:
        print("   ❌ Overlay not applied")
    
    print("\n🎉 Example completed!")
    print("\nKey points:")
    print("- The original codegen API is preserved")
    print("- Enhanced functionality is added transparently")
    print("- Events are emitted for monitoring and integration")
    print("- Metrics are collected automatically")
    print("- All contexten ecosystem features are available")


if __name__ == "__main__":
    main()

