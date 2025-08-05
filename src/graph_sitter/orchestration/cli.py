"""
Orchestration CLI

Command-line interface for the multi-platform orchestration system.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import click
from datetime import datetime

from .engine.orchestrator import MultiPlatformOrchestrator, OrchestrationConfig
from .workflow.models import Workflow, WorkflowStep, WorkflowTemplate
from .triggers.models import Trigger, TriggerCondition, TriggerAction, ConditionOperator, TriggerType
from .events.models import Event, EventType


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def orchestration(ctx, verbose):
    """Multi-Platform Orchestration & Workflow Management CLI"""
    ctx.ensure_object(dict)
    
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize orchestrator
    config = OrchestrationConfig()
    ctx.obj['orchestrator'] = MultiPlatformOrchestrator(config)


@orchestration.group()
def workflow():
    """Workflow management commands"""
    pass


@workflow.command()
@click.option('--name', required=True, help='Workflow name')
@click.option('--description', required=True, help='Workflow description')
@click.option('--file', '-f', type=click.File('r'), help='Load workflow from JSON file')
@click.pass_context
def create(ctx, name, description, file):
    """Create a new workflow"""
    if file:
        workflow_data = json.load(file)
        workflow = Workflow(**workflow_data)
    else:
        workflow = Workflow(
            id=name.lower().replace(' ', '_'),
            name=name,
            description=description
        )
    
    # Register workflow
    orchestrator = ctx.obj['orchestrator']
    success = orchestrator.workflow_manager.register_workflow(workflow)
    
    if success:
        click.echo(f"✅ Created workflow: {workflow.id}")
    else:
        click.echo(f"❌ Failed to create workflow: {workflow.id}")


@workflow.command()
@click.pass_context
def list(ctx):
    """List all workflows"""
    orchestrator = ctx.obj['orchestrator']
    workflows = orchestrator.workflow_manager.list_workflows()
    
    if not workflows:
        click.echo("No workflows found")
        return
    
    click.echo("\n📋 Workflows:")
    for wf in workflows:
        click.echo(f"  • {wf['id']} - {wf['name']} ({wf['steps']} steps)")


@workflow.command()
@click.argument('workflow_id')
@click.option('--context', '-c', help='Execution context as JSON string')
@click.pass_context
def execute(ctx, workflow_id, context):
    """Execute a workflow"""
    orchestrator = ctx.obj['orchestrator']
    
    # Parse context
    exec_context = {}
    if context:
        try:
            exec_context = json.loads(context)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON context")
            return
    
    async def run_workflow():
        try:
            await orchestrator.start()
            execution = await orchestrator.execute_workflow(workflow_id, exec_context)
            click.echo(f"✅ Started workflow execution: {execution.id}")
            
            # Wait for completion (simplified)
            await asyncio.sleep(2)
            status = await orchestrator.get_workflow_status(execution.id)
            if status:
                click.echo(f"Status: {status['status']}")
            
        except Exception as e:
            click.echo(f"❌ Workflow execution failed: {e}")
        finally:
            await orchestrator.stop()
    
    asyncio.run(run_workflow())


@orchestration.group()
def trigger():
    """Trigger management commands"""
    pass


@trigger.command()
@click.option('--name', required=True, help='Trigger name')
@click.option('--description', required=True, help='Trigger description')
@click.option('--event-type', multiple=True, help='Event types to listen for')
@click.option('--platform', multiple=True, help='Platforms to monitor')
@click.option('--workflow-id', required=True, help='Workflow to execute')
@click.pass_context
def create(ctx, name, description, event_type, platform, workflow_id):
    """Create a new trigger"""
    trigger = Trigger(
        id=name.lower().replace(' ', '_'),
        name=name,
        description=description,
        trigger_type=TriggerType.EVENT,
        event_types=list(event_type),
        platforms=list(platform)
    )
    
    # Add workflow action
    action = TriggerAction(
        action_type='workflow',
        parameters={'workflow_id': workflow_id}
    )
    trigger.add_action(action)
    
    # Register trigger
    orchestrator = ctx.obj['orchestrator']
    success = orchestrator.trigger_system.register_trigger(trigger)
    
    if success:
        click.echo(f"✅ Created trigger: {trigger.id}")
    else:
        click.echo(f"❌ Failed to create trigger: {trigger.id}")


@trigger.command()
@click.pass_context
def list(ctx):
    """List all triggers"""
    orchestrator = ctx.obj['orchestrator']
    triggers = orchestrator.trigger_system.get_triggers()
    
    if not triggers:
        click.echo("No triggers found")
        return
    
    click.echo("\n🎯 Triggers:")
    for trig in triggers:
        status_emoji = "✅" if trig['status'] == 'active' else "❌"
        click.echo(f"  {status_emoji} {trig['id']} - {trig['name']} ({trig['type']})")


@orchestration.group()
def event():
    """Event management commands"""
    pass


@event.command()
@click.option('--platform', required=True, help='Source platform')
@click.option('--type', 'event_type', required=True, help='Event type')
@click.option('--data', help='Event data as JSON string')
@click.pass_context
def simulate(ctx, platform, event_type, data):
    """Simulate an event for testing"""
    # Parse event data
    event_data = {}
    if data:
        try:
            event_data = json.loads(data)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON data")
            return
    
    event_data['event_type'] = event_type
    
    async def send_event():
        try:
            orchestrator = ctx.obj['orchestrator']
            await orchestrator.start()
            
            await orchestrator.handle_platform_event(platform, event_data)
            click.echo(f"✅ Simulated {event_type} event from {platform}")
            
        except Exception as e:
            click.echo(f"❌ Event simulation failed: {e}")
        finally:
            await orchestrator.stop()
    
    asyncio.run(send_event())


@orchestration.group()
def status():
    """Status and monitoring commands"""
    pass


@status.command()
@click.pass_context
def overview(ctx):
    """Show orchestration system overview"""
    async def show_status():
        try:
            orchestrator = ctx.obj['orchestrator']
            await orchestrator.start()
            
            metrics = await orchestrator.get_orchestration_metrics()
            
            click.echo("\n🎼 Multi-Platform Orchestration Status")
            click.echo("=" * 40)
            click.echo(f"Status: {metrics['status']}")
            click.echo(f"Active Workflows: {metrics['active_workflows']}")
            
            click.echo("\n🔗 Platform Integrations:")
            for platform, status in metrics['integrations'].items():
                status_emoji = "✅" if status.get('running') else "❌"
                click.echo(f"  {status_emoji} {platform.title()}")
            
            click.echo("\n📊 Component Metrics:")
            wf_metrics = metrics.get('workflow_manager', {})
            click.echo(f"  Workflows: {wf_metrics.get('total_workflows', 0)}")
            click.echo(f"  Executions: {wf_metrics.get('total_executions', 0)}")
            
            event_metrics = metrics.get('event_correlator', {})
            click.echo(f"  Events: {event_metrics.get('total_events', 0)}")
            click.echo(f"  Correlations: {event_metrics.get('total_correlations', 0)}")
            
            trigger_metrics = metrics.get('trigger_system', {})
            click.echo(f"  Triggers: {trigger_metrics.get('total_triggers', 0)}")
            click.echo(f"  Active Triggers: {trigger_metrics.get('active_triggers', 0)}")
            
        except Exception as e:
            click.echo(f"❌ Failed to get status: {e}")
        finally:
            await orchestrator.stop()
    
    asyncio.run(show_status())


@status.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    async def check_health():
        try:
            orchestrator = ctx.obj['orchestrator']
            await orchestrator.start()
            
            metrics = await orchestrator.get_orchestration_metrics()
            
            click.echo("\n🏥 Health Check")
            click.echo("=" * 20)
            
            overall_healthy = True
            
            # Check integrations
            for platform, status in metrics['integrations'].items():
                health = status.get('health', {})
                is_healthy = health.get('healthy', False)
                
                if is_healthy:
                    click.echo(f"✅ {platform.title()}: Healthy")
                else:
                    click.echo(f"❌ {platform.title()}: Unhealthy - {health.get('details', {}).get('error', 'Unknown error')}")
                    overall_healthy = False
            
            # Overall status
            if overall_healthy:
                click.echo("\n✅ System is healthy")
            else:
                click.echo("\n❌ System has health issues")
            
        except Exception as e:
            click.echo(f"❌ Health check failed: {e}")
        finally:
            await orchestrator.stop()
    
    asyncio.run(check_health())


@orchestration.command()
@click.option('--config-file', '-c', type=click.File('r'), help='Configuration file')
@click.pass_context
def start(ctx, config_file):
    """Start the orchestration system"""
    config = OrchestrationConfig()
    
    if config_file:
        config_data = json.load(config_file)
        # Update config with file data
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    orchestrator = MultiPlatformOrchestrator(config)
    
    async def run_orchestrator():
        try:
            click.echo("🚀 Starting Multi-Platform Orchestrator...")
            await orchestrator.start()
            click.echo("✅ Orchestrator started successfully")
            click.echo("Press Ctrl+C to stop")
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping orchestrator...")
        except Exception as e:
            click.echo(f"❌ Orchestrator error: {e}")
        finally:
            await orchestrator.stop()
            click.echo("✅ Orchestrator stopped")
    
    asyncio.run(run_orchestrator())


if __name__ == '__main__':
    orchestration()

