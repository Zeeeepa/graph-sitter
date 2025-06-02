#!/usr/bin/env python3
"""
Autonomous Orchestrator CLI Script

This script provides command-line interface for managing the autonomous CI/CD
orchestration system, integrating Prefect workflows with Codegen SDK, Linear,
GitHub, and graph-sitter.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from contexten.orchestration import (
    AutonomousOrchestrator,
    PrefectOrchestrator,
    AutonomousWorkflowType,
    OrchestrationConfig
)


class AutonomousOrchestrationCLI:
    """
    Command-line interface for autonomous orchestration management
    """
    
    def __init__(self):
        self.config = OrchestrationConfig()
        self.orchestrator: Optional[PrefectOrchestrator] = None
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.config.log_file_path or 'orchestrator.log')
            ]
        )
        return logging.getLogger(__name__)
    
    async def initialize_orchestration(self) -> None:
        """Initialize the orchestration system"""
        print("🚀 Initializing Autonomous Orchestration System...")
        
        try:
            self.orchestrator = PrefectOrchestrator(self.config)
            await self.orchestrator.initialize()
            
            print("✅ Orchestration system initialized successfully")
            await self.display_system_status()
            
        except Exception as e:
            print(f"❌ Failed to initialize orchestration system: {e}")
            self.logger.error(f"Initialization failed: {e}")
            raise
    
    async def trigger_workflow_by_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Trigger workflows based on events"""
        print(f"📡 Processing event: {event_type}")
        
        if not self.orchestrator:
            await self.initialize_orchestration()
        
        # Map events to workflow types
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
            },
            "component_analysis": AutonomousWorkflowType.COMPONENT_ANALYSIS
        }
        
        workflows_to_trigger = []
        
        if event_type == "workflow_run.completed":
            conclusion = event_data.get("conclusion", "unknown")
            if conclusion in event_workflow_mapping[event_type]:
                workflows_to_trigger.append(event_workflow_mapping[event_type][conclusion])
        
        elif event_type == "schedule":
            schedule_type = event_data.get("schedule_type", "health_check")
            if schedule_type in event_workflow_mapping[event_type]:
                workflow_type = event_workflow_mapping[event_type][schedule_type]
                if isinstance(workflow_type, list):
                    workflows_to_trigger.extend(workflow_type)
                else:
                    workflows_to_trigger.append(workflow_type)
        
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
                self.logger.error(f"Failed to trigger {workflow_type.value}: {e}")
        
        if triggered_runs:
            print(f"🎯 Successfully triggered {len(triggered_runs)} workflows")
        else:
            print("⚠️ No workflows were triggered for this event")
    
    async def execute_autonomous_operation(
        self, 
        operation_type: str, 
        parameters: Dict[str, Any],
        wait_for_completion: bool = False
    ) -> str:
        """Execute a specific autonomous operation"""
        print(f"🤖 Executing autonomous operation: {operation_type}")
        
        if not self.orchestrator:
            await self.initialize_orchestration()
        
        # Map operation types to workflow types
        operation_mapping = {
            "failure_analysis": AutonomousWorkflowType.FAILURE_ANALYSIS,
            "performance_monitoring": AutonomousWorkflowType.PERFORMANCE_MONITORING,
            "dependency_management": AutonomousWorkflowType.DEPENDENCY_MANAGEMENT,
            "security_audit": AutonomousWorkflowType.SECURITY_AUDIT,
            "test_optimization": AutonomousWorkflowType.TEST_OPTIMIZATION,
            "health_check": AutonomousWorkflowType.HEALTH_CHECK,
            "component_analysis": AutonomousWorkflowType.COMPONENT_ANALYSIS,
            "code_quality_check": AutonomousWorkflowType.CODE_QUALITY_CHECK,
            "linear_sync": AutonomousWorkflowType.LINEAR_SYNC,
            "github_automation": AutonomousWorkflowType.GITHUB_AUTOMATION
        }
        
        if operation_type not in operation_mapping:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        workflow_type = operation_mapping[operation_type]
        
        try:
            run_id = await self.orchestrator.trigger_workflow(
                workflow_type, 
                parameters
            )
            print(f"✅ Started {operation_type} operation: {run_id}")
            
            # Wait for completion if requested
            if wait_for_completion:
                await self.wait_for_workflow_completion(run_id)
            
            return run_id
            
        except Exception as e:
            print(f"❌ Failed to execute {operation_type} operation: {e}")
            self.logger.error(f"Failed to execute {operation_type}: {e}")
            raise
    
    async def wait_for_workflow_completion(self, run_id: str, timeout_seconds: int = 3600) -> None:
        """Wait for a workflow to complete"""
        print(f"⏳ Waiting for workflow completion: {run_id}")
        
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        start_time = datetime.now()
        
        while True:
            # Check if workflow is complete
            execution = await self.orchestrator.get_workflow_status(run_id)
            
            if execution and execution.state_type.value in ["COMPLETED", "FAILED", "CANCELLED"]:
                print(f"✅ Workflow {run_id} completed with status: {execution.state_type.value}")
                
                if execution.state_type.value == "COMPLETED":
                    print(f"📊 Result available in Prefect UI")
                elif execution.state_type.value == "FAILED":
                    print(f"❌ Workflow failed - check Prefect UI for details")
                
                return
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout_seconds:
                print(f"⏰ Workflow {run_id} timed out after {timeout_seconds} seconds")
                break
            
            # Wait before checking again
            await asyncio.sleep(30)
    
    async def display_system_status(self) -> None:
        """Display current system status"""
        print("\n📊 System Status:")
        print("=" * 50)
        
        try:
            if not self.orchestrator:
                print("❌ Orchestrator not initialized")
                return
            
            # Get orchestration metrics
            metrics = await self.orchestrator.get_metrics()
            
            print(f"Active Workflows: {metrics.get('active_workflows', 0)}")
            print(f"Total Executed: {metrics.get('total_workflows_executed', 0)}")
            print(f"Success Rate: {metrics.get('success_rate_percent', 0):.1f}%")
            print(f"Error Rate: {metrics.get('error_rate_percent', 0):.1f}%")
            print(f"System Health: {metrics.get('system_health_score', 0):.1f}%")
            
            # Get autonomous metrics
            autonomous_metrics = metrics.get('autonomous_metrics', {})
            system_metrics = autonomous_metrics.get('system_metrics')
            
            if system_metrics:
                print(f"\n🖥️ System Resources:")
                print(f"  CPU Usage: {system_metrics.get('cpu_usage_percent', 0):.1f}%")
                print(f"  Memory Usage: {system_metrics.get('memory_usage_percent', 0):.1f}%")
                print(f"  Disk Usage: {system_metrics.get('disk_usage_percent', 0):.1f}%")
            
            # Get component health
            component_health = autonomous_metrics.get('component_health', {})
            if component_health:
                print(f"\n🏥 Component Health:")
                for component_name, health in component_health.items():
                    status = health.get('status', 'unknown')
                    score = health.get('health_score', 0)
                    status_emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
                    print(f"  {status_emoji} {component_name}: {score:.1f}%")
            
            # Get recent alerts
            recent_alerts = autonomous_metrics.get('recent_alerts', [])
            if recent_alerts:
                print(f"\n🚨 Recent Alerts:")
                for alert_batch in recent_alerts[-3:]:  # Last 3 alert batches
                    alerts = alert_batch.get('alerts', [])
                    timestamp = alert_batch.get('timestamp', '')
                    if alerts:
                        print(f"  {timestamp}:")
                        for alert in alerts:
                            print(f"    - {alert}")
            
        except Exception as e:
            print(f"❌ Failed to get system status: {e}")
            self.logger.error(f"Failed to get system status: {e}")
        
        print("=" * 50)
    
    async def run_health_check(self) -> None:
        """Run a comprehensive health check"""
        print("🏥 Running system health check...")
        
        if not self.orchestrator:
            await self.initialize_orchestration()
        
        try:
            # Trigger health check workflow
            run_id = await self.orchestrator.trigger_health_check()
            print(f"✅ Health check started: {run_id}")
            
            # Wait for completion
            await self.wait_for_workflow_completion(run_id, timeout_seconds=300)
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            self.logger.error(f"Health check failed: {e}")
    
    async def run_component_analysis(
        self, 
        component: str, 
        linear_issue_id: Optional[str] = None
    ) -> None:
        """Run component analysis"""
        print(f"🔍 Running component analysis for: {component}")
        
        if not self.orchestrator:
            await self.initialize_orchestration()
        
        try:
            run_id = await self.orchestrator.trigger_component_analysis(
                component, 
                linear_issue_id
            )
            print(f"✅ Component analysis started: {run_id}")
            
            # Wait for completion
            await self.wait_for_workflow_completion(run_id, timeout_seconds=1800)  # 30 minutes
            
        except Exception as e:
            print(f"❌ Component analysis failed: {e}")
            self.logger.error(f"Component analysis failed: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown the orchestration system"""
        print("🛑 Shutting down orchestration system...")
        
        try:
            if self.orchestrator:
                await self.orchestrator.shutdown()
            print("✅ Orchestration system shutdown complete")
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
            self.logger.error(f"Shutdown error: {e}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Autonomous Orchestration Manager")
    parser.add_argument("--action", required=True, choices=[
        "initialize", "trigger", "execute", "health-check", "status", 
        "component-analysis", "shutdown"
    ], help="Action to perform")
    
    parser.add_argument("--event-type", help="Event type (for trigger action)")
    parser.add_argument("--event-data", help="Event data as JSON (for trigger action)")
    parser.add_argument("--operation", help="Operation type (for execute action)")
    parser.add_argument("--parameters", help="Operation parameters as JSON")
    parser.add_argument("--component", help="Component name (for component-analysis)")
    parser.add_argument("--linear-issue-id", help="Linear issue ID (for component-analysis)")
    parser.add_argument("--wait", action="store_true", help="Wait for completion")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = AutonomousOrchestrationCLI()
    
    try:
        if args.action == "initialize":
            await cli.initialize_orchestration()
        
        elif args.action == "trigger":
            if not args.event_type:
                print("❌ --event-type is required for trigger action")
                sys.exit(1)
            
            event_data = {}
            if args.event_data:
                event_data = json.loads(args.event_data)
            
            await cli.trigger_workflow_by_event(args.event_type, event_data)
        
        elif args.action == "execute":
            if not args.operation:
                print("❌ --operation is required for execute action")
                sys.exit(1)
            
            parameters = {}
            if args.parameters:
                parameters = json.loads(args.parameters)
            
            await cli.execute_autonomous_operation(
                args.operation, 
                parameters, 
                wait_for_completion=args.wait
            )
        
        elif args.action == "health-check":
            await cli.run_health_check()
        
        elif args.action == "component-analysis":
            if not args.component:
                print("❌ --component is required for component-analysis action")
                sys.exit(1)
            
            await cli.run_component_analysis(args.component, args.linear_issue_id)
        
        elif args.action == "status":
            if not cli.orchestrator:
                await cli.initialize_orchestration()
            await cli.display_system_status()
        
        elif args.action == "shutdown":
            await cli.shutdown()
    
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        await cli.shutdown()
    
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

