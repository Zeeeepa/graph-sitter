"""
Command Line Interface for the Enhanced Orchestrator
"""

import asyncio
import click
import json
import yaml
from pathlib import Path
from typing import Optional

from .orchestrator import EnhancedOrchestrator
from .config import ConfigManager, ContextenConfig
from .examples import run_all_examples


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config: Optional[str], debug: bool):
    """Enhanced Orchestrator CLI - SDK-Python and Strands-Agents Integration"""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['debug'] = debug


@cli.command()
@click.pass_context
def start(ctx):
    """Start the Enhanced Orchestrator"""
    async def _start():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        config = config_manager.get_config()
        
        if ctx.obj.get('debug'):
            config.debug = True
            config.logging.level = "DEBUG"
        
        orchestrator = EnhancedOrchestrator(config)
        
        try:
            click.echo("🚀 Starting Enhanced Orchestrator...")
            await orchestrator.start()
            click.echo("✅ Orchestrator started successfully")
            
            # Keep running until interrupted
            click.echo("Press Ctrl+C to stop...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                click.echo("\n🛑 Stopping orchestrator...")
                
        finally:
            await orchestrator.stop()
            click.echo("✅ Orchestrator stopped")
    
    asyncio.run(_start())


@cli.command()
@click.option('--agent-name', default='cli_agent', help='Agent name')
@click.option('--provider', default='bedrock', help='Model provider')
@click.option('--model', help='Model ID')
@click.option('--temperature', default=0.3, help='Model temperature')
@click.option('--tools', help='Comma-separated list of tools')
@click.pass_context
def create_agent(ctx, agent_name: str, provider: str, model: Optional[str], temperature: float, tools: Optional[str]):
    """Create a new agent"""
    async def _create_agent():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        orchestrator = EnhancedOrchestrator(config_manager.get_config())
        
        try:
            await orchestrator.start()
            
            agent_config = {
                "name": agent_name,
                "model_provider": provider,
                "temperature": temperature
            }
            
            if model:
                agent_config["model_id"] = model
            
            tool_list = []
            if tools:
                tool_list = [tool.strip() for tool in tools.split(',')]
            
            agent_id = await orchestrator.create_agent(
                agent_config=agent_config,
                tools=tool_list
            )
            
            click.echo(f"✅ Created agent: {agent_id}")
            click.echo(f"   Name: {agent_name}")
            click.echo(f"   Provider: {provider}")
            click.echo(f"   Tools: {tool_list}")
            
        finally:
            await orchestrator.stop()
    
    asyncio.run(_create_agent())


@cli.command()
@click.option('--task-id', required=True, help='Task ID')
@click.option('--description', required=True, help='Task description')
@click.option('--agent-id', help='Agent ID to use')
@click.option('--config-file', help='Task configuration JSON file')
@click.pass_context
def execute_task(ctx, task_id: str, description: str, agent_id: Optional[str], config_file: Optional[str]):
    """Execute a task"""
    async def _execute_task():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        orchestrator = EnhancedOrchestrator(config_manager.get_config())
        
        try:
            await orchestrator.start()
            
            # Load task configuration
            task_config = {"description": description}
            
            if config_file and Path(config_file).exists():
                with open(config_file, 'r') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                    task_config.update(file_config)
            
            click.echo(f"🚀 Executing task: {task_id}")
            click.echo(f"   Description: {description}")
            
            result = await orchestrator.execute_task(
                task_id=task_id,
                task_config=task_config,
                agent_id=agent_id
            )
            
            click.echo("✅ Task completed")
            click.echo(f"   Status: {result['status']}")
            click.echo(f"   Result: {json.dumps(result['result'], indent=2)}")
            
        finally:
            await orchestrator.stop()
    
    asyncio.run(_execute_task())


@cli.command()
@click.pass_context
def status(ctx):
    """Get orchestrator status"""
    async def _status():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        orchestrator = EnhancedOrchestrator(config_manager.get_config())
        
        try:
            await orchestrator.start()
            
            # Get health status
            health = orchestrator.get_health_status()
            
            click.echo("🔍 System Status:")
            for component, status in health.items():
                if component != "timestamp":
                    icon = "✅" if status in ["healthy", True] else "❌"
                    click.echo(f"   {icon} {component}: {status}")
            
            # Get statistics
            memory_stats = await orchestrator.get_memory_stats()
            event_stats = await orchestrator.get_event_stats()
            cicd_status = await orchestrator.get_cicd_status()
            
            click.echo("\n📊 Statistics:")
            click.echo(f"   Memory entries: {memory_stats.get('cache_size', 0)}")
            click.echo(f"   Events processed: {event_stats.get('total_events', 0)}")
            click.echo(f"   CI/CD executions: {cicd_status.get('total_executions', 0)}")
            click.echo(f"   Active tasks: {health.get('active_tasks', 0)}")
            
        finally:
            await orchestrator.stop()
    
    asyncio.run(_status())


@cli.command()
@click.pass_context
def optimize(ctx):
    """Optimize the orchestrator system"""
    async def _optimize():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        orchestrator = EnhancedOrchestrator(config_manager.get_config())
        
        try:
            await orchestrator.start()
            
            click.echo("🔧 Starting system optimization...")
            
            optimization_results = await orchestrator.optimize_system()
            
            click.echo("✅ Optimization completed:")
            for component, result in optimization_results.items():
                click.echo(f"   {component}: {result}")
            
        finally:
            await orchestrator.stop()
    
    asyncio.run(_optimize())


@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command()
@click.option('--output', '-o', default='contexten_config.yaml', help='Output file path')
def create_sample(output: str):
    """Create a sample configuration file"""
    config_manager = ConfigManager()
    
    if config_manager.create_sample_config(output):
        click.echo(f"✅ Sample configuration created: {output}")
    else:
        click.echo("❌ Failed to create sample configuration")


@config.command()
@click.option('--config', '-c', help='Configuration file to validate')
def validate(config: Optional[str]):
    """Validate configuration file"""
    config_manager = ConfigManager(config)
    
    is_valid, errors = config_manager.validate_config()
    
    if is_valid:
        click.echo("✅ Configuration is valid")
    else:
        click.echo("❌ Configuration validation failed:")
        for error in errors:
            click.echo(f"   - {error}")


@config.command()
@click.option('--config', '-c', help='Configuration file to show')
def show(config: Optional[str]):
    """Show current configuration"""
    config_manager = ConfigManager(config)
    config_obj = config_manager.get_config()
    
    # Convert to dictionary and display
    import dataclasses
    config_dict = dataclasses.asdict(config_obj)
    
    click.echo("📋 Current Configuration:")
    click.echo(yaml.dump(config_dict, default_flow_style=False, indent=2))


@cli.command()
def examples():
    """Run example demonstrations"""
    click.echo("🧪 Running Enhanced Orchestrator examples...")
    asyncio.run(run_all_examples())


@cli.command()
@click.option('--pipeline', required=True, help='Pipeline name to execute')
@click.option('--params', help='Pipeline parameters as JSON')
@click.pass_context
def run_pipeline(ctx, pipeline: str, params: Optional[str]):
    """Execute a CI/CD pipeline"""
    async def _run_pipeline():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        orchestrator = EnhancedOrchestrator(config_manager.get_config())
        
        try:
            await orchestrator.start()
            
            # Parse parameters
            parameters = {}
            if params:
                parameters = json.loads(params)
            
            click.echo(f"🚀 Executing pipeline: {pipeline}")
            
            execution_id = await orchestrator.autonomous_cicd.execute_pipeline(
                pipeline_name=pipeline,
                parameters=parameters
            )
            
            click.echo(f"✅ Pipeline started: {execution_id}")
            
            # Monitor execution
            click.echo("📊 Monitoring execution...")
            while True:
                status = await orchestrator.autonomous_cicd.get_execution_status(execution_id)
                if status:
                    click.echo(f"   Status: {status['status']}")
                    if status['status'] in ['success', 'failed', 'cancelled']:
                        break
                await asyncio.sleep(2)
            
            # Get final logs
            logs = await orchestrator.autonomous_cicd.get_execution_logs(execution_id)
            if logs:
                click.echo("\n📝 Execution logs:")
                for log in logs[-5:]:  # Show last 5 logs
                    click.echo(f"   {log}")
            
        finally:
            await orchestrator.stop()
    
    asyncio.run(_run_pipeline())


@cli.command()
@click.option('--query', help='Search query for memory')
@click.option('--limit', default=10, help='Maximum results to return')
@click.pass_context
def memory_search(ctx, query: Optional[str], limit: int):
    """Search memory for stored contexts"""
    async def _memory_search():
        config_manager = ConfigManager(ctx.obj.get('config_path'))
        orchestrator = EnhancedOrchestrator(config_manager.get_config())
        
        try:
            await orchestrator.start()
            
            if query:
                click.echo(f"🔍 Searching memory for: {query}")
                results = await orchestrator.memory_manager.retrieve_context(
                    query=query,
                    limit=limit
                )
                
                if results.get('results'):
                    click.echo(f"✅ Found {len(results['results'])} results:")
                    for i, result in enumerate(results['results'][:limit], 1):
                        click.echo(f"   {i}. {result['context_id']} (similarity: {result.get('similarity', 0):.2f})")
                else:
                    click.echo("❌ No results found")
            else:
                # Show recent entries
                results = await orchestrator.memory_manager.retrieve_context(limit=limit)
                recent_entries = results.get('recent_entries', [])
                
                if recent_entries:
                    click.echo(f"📚 Recent memory entries ({len(recent_entries)}):")
                    for entry in recent_entries:
                        click.echo(f"   - {entry['context_id']} ({entry['timestamp']})")
                else:
                    click.echo("❌ No memory entries found")
            
        finally:
            await orchestrator.stop()
    
    asyncio.run(_memory_search())


if __name__ == '__main__':
    cli()

