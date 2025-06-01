#!/usr/bin/env python3
"""
Autonomous Orchestrator Integration Script

This script integrates the existing autonomous CI/CD scripts with the new
Prefect-based orchestration system, providing centralized coordination
and monitoring.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from contexten.orchestration import PrefectOrchestrator, AutonomousWorkflowType


class AutonomousOrchestrationManager:
    """
    Manager for autonomous CI/CD operations using Prefect orchestration
    """
    
    def __init__(self):
        # Get configuration from environment
        self.codegen_org_id = os.environ.get('CODEGEN_ORG_ID')
        self.codegen_token = os.environ.get('CODEGEN_TOKEN')
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        self.prefect_api_url = os.environ.get('PREFECT_API_URL')
        
        if not self.codegen_org_id or not self.codegen_token:
            raise ValueError("CODEGEN_ORG_ID and CODEGEN_TOKEN must be set")
        
        # Initialize orchestrator
        self.orchestrator = PrefectOrchestrator(
            codegen_org_id=self.codegen_org_id,
            codegen_token=self.codegen_token,
            github_token=self.github_token,
            slack_webhook_url=self.slack_webhook_url,
            prefect_api_url=self.prefect_api_url
        )
    
    async def initialize_orchestration(self):
        """Initialize the orchestration system"""
        
        print("🚀 Initializing Prefect-based orchestration system...")
        
        try:
            await self.orchestrator.initialize()
            print("✅ Orchestration system initialized successfully")
            
            # Display system status
            await self.display_system_status()
            
        except Exception as e:
            print(f"❌ Failed to initialize orchestration system: {e}")
            raise
    
    async def trigger_workflow_by_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger workflows based on GitHub events"""
        
        print(f"📡 Processing event: {event_type}")
        
        # Map GitHub events to workflow types
        event_workflow_mapping = {
            "workflow_run.completed": {
                "failure": AutonomousWorkflowType.FAILURE_ANALYSIS,
                "success": AutonomousWorkflowType.PERFORMANCE_MONITORING
            },
            "push": AutonomousWorkflowType.PERFORMANCE_MONITORING,
            "schedule": {
                "daily": [
                    AutonomousWorkflowType.DEPENDENCY_MANAGEMENT,
                    AutonomousWorkflowType.SECURITY_AUDIT
                ],
                "health_check": AutonomousWorkflowType.HEALTH_CHECK
            }
        }
        
        workflows_to_trigger = []
        
        if event_type == "workflow_run.completed":
            conclusion = event_data.get("conclusion", "unknown")
            if conclusion in event_workflow_mapping[event_type]:
                workflows_to_trigger.append(event_workflow_mapping[event_type][conclusion])
        
        elif event_type in event_workflow_mapping:
            workflow_type = event_workflow_mapping[event_type]
            if isinstance(workflow_type, list):
                workflows_to_trigger.extend(workflow_type)
            else:
                workflows_to_trigger.append(workflow_type)
        
        # Trigger workflows
        triggered_runs = []
        for workflow_type in workflows_to_trigger:
            try:
                run_id = await self.orchestrator.trigger_workflow(
                    workflow_type, 
                    parameters=event_data
                )
                triggered_runs.append({
                    "workflow_type": workflow_type.value,
                    "run_id": run_id
                })
                print(f"✅ Triggered {workflow_type.value} workflow: {run_id}")
                
            except Exception as e:
                print(f"❌ Failed to trigger {workflow_type.value} workflow: {e}")
        
        return triggered_runs
    
    async def execute_autonomous_operation(self, operation_type: str, parameters: Dict[str, Any]):
        """Execute a specific autonomous operation"""
        
        print(f"🤖 Executing autonomous operation: {operation_type}")
        
        # Map operation types to workflow types
        operation_mapping = {
            "failure_analysis": AutonomousWorkflowType.FAILURE_ANALYSIS,
            "performance_monitoring": AutonomousWorkflowType.PERFORMANCE_MONITORING,
            "dependency_management": AutonomousWorkflowType.DEPENDENCY_MANAGEMENT,
            "security_audit": AutonomousWorkflowType.SECURITY_AUDIT,
            "test_optimization": AutonomousWorkflowType.TEST_OPTIMIZATION,
            "health_check": AutonomousWorkflowType.HEALTH_CHECK
        }
        
        if operation_type not in operation_mapping:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        workflow_type = operation_mapping[operation_type]
        
        try:
            run_id = await self.orchestrator.trigger_workflow(workflow_type, parameters)
            print(f"✅ Started {operation_type} operation: {run_id}")
            
            # Wait for completion if requested
            if parameters.get("wait_for_completion", False):
                await self.wait_for_workflow_completion(run_id)
            
            return run_id
            
        except Exception as e:
            print(f"❌ Failed to execute {operation_type} operation: {e}")
            raise
    
    async def wait_for_workflow_completion(self, run_id: str, timeout_seconds: int = 3600):
        """Wait for a workflow to complete"""
        
        print(f"⏳ Waiting for workflow completion: {run_id}")
        
        start_time = datetime.now()
        
        while True:
            # Check if workflow is complete
            execution = await self.orchestrator.get_workflow_status(run_id)
            
            if execution and execution.status.value in ["completed", "failed", "cancelled"]:
                print(f"✅ Workflow {run_id} completed with status: {execution.status.value}")
                
                if execution.status.value == "completed":
                    print(f"📊 Result: {execution.result}")
                elif execution.status.value == "failed":
                    print(f"❌ Error: {execution.error_message}")
                
                return execution
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout_seconds:
                print(f"⏰ Workflow {run_id} timed out after {timeout_seconds} seconds")
                break
            
            # Wait before checking again
            await asyncio.sleep(30)
        
        return None
    
    async def display_system_status(self):
        """Display current system status"""
        
        print("\n📊 System Status:")
        print("=" * 50)
        
        try:
            # Get orchestration metrics
            metrics = await self.orchestrator.get_metrics()
            
            print(f"Active Workflows: {metrics.active_workflows}")
            print(f"Total Executed: {metrics.total_workflows_executed}")
            print(f"Success Rate: {((metrics.successful_workflows / max(metrics.total_workflows_executed, 1)) * 100):.1f}%")
            print(f"Error Rate: {metrics.error_rate_percent:.1f}%")
            print(f"System Health: {metrics.system_health_score:.1f}%")
            
            # Get health status
            health_status = await self.orchestrator.monitor.check_system_health()
            
            print(f"\n🏥 Health Status: {health_status['status'].upper()}")
            
            for component_name, component_health in health_status['components'].items():
                status_emoji = "✅" if component_health['status'] == "healthy" else "⚠️" if component_health['status'] == "degraded" else "❌"
                print(f"  {status_emoji} {component_name}: {component_health['health_score']:.1f}%")
            
            if health_status['alerts']:
                print(f"\n🚨 Alerts:")
                for alert in health_status['alerts']:
                    print(f"  - {alert}")
            
        except Exception as e:
            print(f"❌ Failed to get system status: {e}")
        
        print("=" * 50)
    
    async def run_health_check(self):
        """Run a comprehensive health check"""
        
        print("🏥 Running system health check...")
        
        try:
            # Trigger health check workflow
            run_id = await self.orchestrator.trigger_workflow(
                AutonomousWorkflowType.HEALTH_CHECK,
                parameters={"comprehensive": True}
            )
            
            print(f"✅ Health check started: {run_id}")
            
            # Wait for completion
            execution = await self.wait_for_workflow_completion(run_id, timeout_seconds=300)
            
            if execution and execution.status.value == "completed":
                health_result = execution.result
                print(f"📊 Health Check Results:")
                print(json.dumps(health_result, indent=2))
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    async def shutdown(self):
        """Shutdown the orchestration system"""
        
        print("🛑 Shutting down orchestration system...")
        
        try:
            await self.orchestrator.shutdown()
            print("✅ Orchestration system shutdown complete")
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="Autonomous Orchestration Manager")
    parser.add_argument("--action", required=True, choices=[
        "initialize", "trigger", "execute", "health-check", "status", "shutdown"
    ], help="Action to perform")
    
    parser.add_argument("--event-type", help="GitHub event type (for trigger action)")
    parser.add_argument("--event-data", help="GitHub event data as JSON (for trigger action)")
    parser.add_argument("--operation", help="Operation type (for execute action)")
    parser.add_argument("--parameters", help="Operation parameters as JSON")
    parser.add_argument("--wait", action="store_true", help="Wait for completion")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = AutonomousOrchestrationManager()
    
    try:
        if args.action == "initialize":
            await manager.initialize_orchestration()
        
        elif args.action == "trigger":
            if not args.event_type:
                print("❌ --event-type is required for trigger action")
                sys.exit(1)
            
            event_data = {}
            if args.event_data:
                event_data = json.loads(args.event_data)
            
            await manager.initialize_orchestration()
            triggered_runs = await manager.trigger_workflow_by_event(args.event_type, event_data)
            
            print(f"✅ Triggered {len(triggered_runs)} workflows:")
            for run in triggered_runs:
                print(f"  - {run['workflow_type']}: {run['run_id']}")
        
        elif args.action == "execute":
            if not args.operation:
                print("❌ --operation is required for execute action")
                sys.exit(1)
            
            parameters = {}
            if args.parameters:
                parameters = json.loads(args.parameters)
            
            if args.wait:
                parameters["wait_for_completion"] = True
            
            await manager.initialize_orchestration()
            run_id = await manager.execute_autonomous_operation(args.operation, parameters)
            
            print(f"✅ Operation {args.operation} started: {run_id}")
        
        elif args.action == "health-check":
            await manager.initialize_orchestration()
            await manager.run_health_check()
        
        elif args.action == "status":
            await manager.initialize_orchestration()
            await manager.display_system_status()
        
        elif args.action == "shutdown":
            await manager.initialize_orchestration()
            await manager.shutdown()
    
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        await manager.shutdown()
    
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

