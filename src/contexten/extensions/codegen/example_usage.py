#!/usr/bin/env python3
"""
Example usage of the Codegen Package Overlay System

This example demonstrates how to use the overlay system and the enhanced
functionality it provides while maintaining the original API.
"""

import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("🚀 Codegen Package Overlay System - Example Usage")
    print("=" * 60)
    
    # Step 1: Check if overlay is applied
    print("\n1. Checking overlay status...")
    try:
        from codegen.contexten.integration import get_metrics
        print("   ✅ Overlay is applied and working!")
        
        metrics = get_metrics()
        print(f"   📊 Current metrics: {metrics}")
        
    except ImportError:
        print("   ❌ Overlay not applied yet")
        print("   Run: python src/contexten/extensions/codegen/apply_overlay.py")
        return
    
    # Step 2: Set up event handlers
    print("\n2. Setting up event handlers...")
    from codegen.contexten.integration import register_event_handler
    
    def on_agent_created(data):
        print(f"   🤖 Agent created: org_id={data.get('org_id', 'unknown')}")
    
    def on_task_starting(data):
        prompt = data.get('prompt', 'unknown')
        print(f"   🚀 Task starting: {prompt}")
    
    def on_task_created(data):
        task_id = data.get('task_id', 'unknown')
        duration = data.get('duration', 0)
        print(f"   📝 Task created: {task_id} (took {duration:.3f}s)")
    
    def on_task_error(data):
        error = data.get('error', 'unknown')
        print(f"   ❌ Task error: {error}")
    
    # Register event handlers
    register_event_handler("agent_created", on_agent_created)
    register_event_handler("task_starting", on_task_starting)
    register_event_handler("task_created", on_task_created)
    register_event_handler("task_error", on_task_error)
    
    print("   ✅ Event handlers registered!")
    
    # Step 3: Use the enhanced codegen package
    print("\n3. Using enhanced codegen package...")
    print("   Note: Using the EXACT same import as always!")
    
    try:
        # Import exactly as users always have
        from codegen.agents.agent import Agent
        
        print("   ✅ Successfully imported Agent class")
        
        # Create agent (events will be emitted automatically)
        print("   Creating agent...")
        agent = Agent(
            org_id="11",  # Replace with your org_id
            token="demo_token",  # Replace with your actual token
            base_url="https://codegen-sh-rest-api.modal.run"
        )
        
        print("   ✅ Agent created with enhanced functionality!")
        
        # Show enhanced methods
        print("\n   Enhanced methods available:")
        
        # Get contexten metrics
        metrics = agent.get_contexten_metrics()
        print(f"   📊 Contexten metrics: {metrics}")
        
        # Add a callback
        def agent_callback(data):
            print(f"   📞 Agent callback triggered: {data}")
        
        agent.add_callback(agent_callback)
        print("   ✅ Added callback to agent")
        
        # Example of enhanced run (commented out since we don't have real credentials)
        print("\n   Example enhanced task creation (commented out - requires real credentials):")
        print("   # task = agent.run_enhanced('Which github repos can you currently access?')")
        print("   # print(f'Task ID: {task.id}')")
        print("   # print(f'Task status: {task.status}')")
        
        # Show that original methods still work
        print("\n   Original methods still work:")
        print(f"   agent.get_status() available: {hasattr(agent, 'get_status')}")
        print(f"   agent.run() available: {hasattr(agent, 'run')}")
        
    except ImportError as e:
        print(f"   ❌ Could not import codegen: {e}")
        print("   Make sure you have installed codegen: pip install codegen")
        return
    except Exception as e:
        print(f"   ⚠️  Note: {e}")
        print("   (This is expected without real credentials)")
    
    # Step 4: Show contexten modules
    print("\n4. Exploring contexten modules...")
    
    try:
        # Integration module
        from codegen.contexten.integration import get_integration
        integration = get_integration()
        print(f"   📡 Integration status: enabled={integration.enabled}")
        
        # Metrics module
        from codegen.contexten.metrics import get_metrics_collector
        metrics_collector = get_metrics_collector()
        all_metrics = metrics_collector.get_metrics()
        print(f"   📊 Detailed metrics: {all_metrics}")
        
        # Events module
        from codegen.contexten.events import EventType
        print(f"   📅 Available event types: {list(EventType)}")
        
        # Monitoring module
        from codegen.contexten.monitoring import get_system_info, run_health_checks
        system_info = get_system_info()
        print(f"   💻 System info: {system_info}")
        
        health_checks = run_health_checks()
        print(f"   🏥 Health status: {health_checks['overall_status']}")
        
    except ImportError as e:
        print(f"   ❌ Could not import contexten modules: {e}")
    
    # Step 5: Demonstrate metrics tracking
    print("\n5. Demonstrating metrics tracking...")
    
    try:
        from codegen.contexten.metrics import increment, set_gauge, start_timer, end_timer
        
        # Increment some counters
        increment("example_operations")
        increment("api_calls", 3)
        
        # Set some gauges
        set_gauge("example_load", 0.42)
        set_gauge("active_sessions", 7)
        
        # Use timers
        start_timer("example_operation")
        time.sleep(0.1)  # Simulate work
        duration = end_timer("example_operation")
        
        print(f"   ⏱️  Example operation took {duration:.3f}s")
        
        # Show updated metrics
        final_metrics = get_metrics()
        print(f"   📊 Final metrics: {final_metrics}")
        
    except ImportError as e:
        print(f"   ❌ Could not access metrics: {e}")
    
    print("\n🎉 Example completed successfully!")
    print("\nKey takeaways:")
    print("- The original codegen API is completely preserved")
    print("- Enhanced functionality is added transparently")
    print("- Events are emitted automatically for monitoring")
    print("- Metrics are collected without user intervention")
    print("- All contexten ecosystem features are available")
    print("- Users can continue using: from codegen.agents.agent import Agent")


if __name__ == "__main__":
    main()

