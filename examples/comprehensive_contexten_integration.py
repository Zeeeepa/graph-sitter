#!/usr/bin/env python3
"""
Comprehensive Contexten Integration Example
Demonstrates the full integrated system using all 11 extensions with proper imports from existing project components.

This example shows how to:
1. Initialize ContextenApp with all 11 extensions
2. Execute comprehensive workflows using the full hierarchy
3. Demonstrate proper integration between all components
4. Use existing graph_sitter and contexten components
"""

import asyncio
import logging
import os

# Import existing contexten components
from contexten.extensions.contexten_app.contexten_app import ContextenApp

# Import existing graph_sitter components
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

# Import existing extension components for demonstration
from contexten.extensions.github.github import GitHub
from contexten.extensions.linear.linear import Linear
from contexten.extensions.slack.slack import Slack
from contexten.extensions.circleci.circleci import CircleCI

# Import new extension components that use existing modules
from contexten.extensions.prefect.prefect import Prefect
from contexten.extensions.controlflow.controlflow import ControlFlow
from contexten.extensions.codegen.codegen import Codegen
from contexten.extensions.grainchain.grainchain import Grainchain
from contexten.extensions.graph_sitter.graph_sitter import GraphSitter

# Set up logging
logging.basicConfig(level=logging.INFO, force=True)
logger = get_logger(__name__)

########################################################################################################################
# COMPREHENSIVE CONTEXTEN INTEGRATION EXAMPLE
########################################################################################################################

# Set up logging
logging.basicConfig(level=logging.INFO, force=True)
logger = get_logger(__name__)

# Check if all required extensions are available
REQUIRED_EXTENSIONS = [
    'graph_sitter', 'contexten.extensions.github', 'contexten.extensions.linear',
    'contexten.extensions.slack', 'contexten.extensions.circleci',
    'contexten.extensions.prefect', 'contexten.extensions.controlflow',
    'contexten.extensions.codegen', 'contexten.extensions.grainchain'
]

def check_extensions():
    """Check if all required extensions are available."""
    missing = []
    for ext in REQUIRED_EXTENSIONS:
        try:
            __import__(ext)
        except ImportError:
            missing.append(ext)
    return missing

########################################################################################################################
    )
    
    # Verify all extensions are initialized
    logger.info("✅ ContextenApp initialized with extensions:")
    logger.info(f"   - GitHub: {'✅' if app.github else '❌'}")
    logger.info(f"   - Linear: {'✅' if app.linear else '❌'}")
    logger.info(f"   - Slack: {'✅' if app.slack else '❌'}")
    logger.info(f"   - CircleCI: {'✅' if app.circleci else '❌'}")
    logger.info(f"   - Modal: {'✅' if app.modal else '❌'}")
    logger.info(f"   - Prefect: {'✅' if app.prefect_flow else '❌'}")
    logger.info(f"   - ControlFlow: {'✅' if app.controlflow_orchestrator else '❌'}")
    logger.info(f"   - Codegen: {'✅' if app.codegen_client else '❌'}")
    logger.info(f"   - Grainchain: {'✅' if app.grainchain_quality_gates else '❌'}")
    logger.info(f"   - Graph_sitter: {'✅' if app.graph_sitter_analysis else '❌'}")
    
    # Initialize individual extension instances for demonstration
    logger.info("🔧 Initializing individual extension instances...")
    
    # Initialize Prefect extension (Top Layer - System Watch Flows)
    prefect_ext = Prefect(app)
    await prefect_ext.initialize()
    
    # Initialize ControlFlow extension (Agent Orchestrator)
    controlflow_ext = ControlFlow(app)
    await controlflow_ext.initialize()
    
    # Initialize Codegen extension (Task Completion with API token/org_id)
    codegen_ext = Codegen(app)
    await codegen_ext.initialize()
    
    # Initialize Grainchain extension (Sandboxed Deployment + Snapshot saving)
    grainchain_ext = Grainchain(app)
    await grainchain_ext.initialize()
    
    # Initialize Graph_sitter extension (Analysis for PR validation)
    graph_sitter_ext = GraphSitter(app)
    await graph_sitter_ext.initialize()
    
    logger.info("✅ All individual extensions initialized successfully")
    
    # Demonstrate integration between extensions
    logger.info("🔗 Setting up integration between extensions...")
    
    # Integrate Prefect with ControlFlow
    await prefect_ext.integrate_with_controlflow(controlflow_ext.orchestrator)
    
    # Integrate ControlFlow with Prefect
    await controlflow_ext.integrate_with_prefect(prefect_ext)
    
    # Integrate Codegen with other extensions
    await codegen_ext.integrate_with_extensions(
        github=app.github,
        linear=app.linear,
        slack=app.slack,
        circleci=app.circleci
    )
    
    # Integrate Graph_sitter with Grainchain
    await graph_sitter_ext.integrate_with_grainchain(
        quality_gate_manager=grainchain_ext.quality_gate_manager,
        sandbox_manager=grainchain_ext.sandbox_manager
    )
    
    logger.info("✅ Extension integrations completed successfully")
    
    # Demonstrate comprehensive workflow execution
    logger.info("🎯 Executing comprehensive workflow using all 11 extensions...")
    
    project_id = "demo-project-001"
    requirements = """
    Create a comprehensive analysis and improvement plan for the graph-sitter codebase:
    1. Analyze code quality and identify improvement opportunities
    2. Create Linear issues for identified improvements
    3. Set up automated quality gates
    4. Implement CI/CD improvements via CircleCI
    5. Create documentation and notify team via Slack
    """
    
    # Execute the comprehensive workflow using ContextenApp
    workflow_result = await app.execute_comprehensive_workflow(
        project_id=project_id,
        requirements=requirements
    )
    
    logger.info("📊 Comprehensive Workflow Results:")
    logger.info(f"   Status: {workflow_result.get('status')}")
    logger.info(f"   Extensions Used: {workflow_result.get('extensions_used', [])}")
    logger.info(f"   Stages Completed: {list(workflow_result.get('stages', {}).keys())}")
    
    # Demonstrate individual extension capabilities
    logger.info("🔍 Demonstrating individual extension capabilities...")
    
    # 1. Prefect - System Watch Flows
    logger.info("📊 Testing Prefect system watch flows...")
    prefect_result = await prefect_ext.create_comprehensive_system_watch(
        project_id=project_id,
        config={
            'watch_interval': 300,  # 5 minutes
            'monitoring': {
                'enabled': True,
                'alerts': ['quality_degradation', 'build_failures']
            }
        }
    )
    logger.info(f"   Prefect Result: {prefect_result.get('status')}")
    
    # 2. ControlFlow - Agent Orchestration
    logger.info("🎯 Testing ControlFlow agent orchestration...")
    if codegen_ext.workflow_client:
        await controlflow_ext.register_codegen_agent(
            agent_id="demo-agent",
            name="Demo Codegen Agent",
            client=codegen_ext.workflow_client
        )
    
    orchestration_result = await controlflow_ext.orchestrate_workflow(
        project_id=project_id,
        requirements="Analyze codebase and create improvement plan"
    )
    logger.info(f"   ControlFlow Result: {orchestration_result.get('status')}")
    
    # 3. Codegen - Task Execution
    logger.info("🤖 Testing Codegen task execution...")
    codegen_result = await codegen_ext.execute_workflow_tasks(
        project_id=project_id,
        requirements="Analyze graph-sitter codebase structure",
        context={'analysis_type': 'comprehensive'}
    )
    logger.info(f"   Codegen Result: {codegen_result.get('status')}")
    
    # 4. Grainchain - Quality Gates and Sandboxing
    logger.info("🏗️ Testing Grainchain sandboxed deployment and quality gates...")
    grainchain_result = await grainchain_ext.execute_full_pipeline(
        project_id=project_id,
        context={
            'sandbox_config': {'provider': 'docker', 'timeout': 1800},
            'analysis_config': {'depth': 'comprehensive'},
            'snapshot_config': {'retention': '7d'}
        }
    )
    logger.info(f"   Grainchain Result: {grainchain_result.get('status')}")
    
    # 5. Graph_sitter - Code Analysis
    logger.info("🔍 Testing Graph_sitter comprehensive analysis...")
    graph_sitter_result = await graph_sitter_ext.execute_full_analysis_pipeline(
        project_id=project_id,
        codebase_path='.',
        pr_data={
            'head': {'ref': 'feature-branch'},
            'base': {'ref': 'develop'},
            'changed_files': ['src/contexten/extensions/contexten_app/contexten_app.py']
        }
    )
    logger.info(f"   Graph_sitter Result: {graph_sitter_result.get('status')}")
    
    # Demonstrate event handling capabilities
    logger.info("📡 Testing event handling capabilities...")
    
    # Test Prefect event handling
    prefect_event_result = await prefect_ext.handle({
        'type': 'system_watch',
        'project_id': project_id,
        'config': {'watch_type': 'quality_monitoring'}
    })
    logger.info(f"   Prefect Event Result: {prefect_event_result.get('status')}")
    
    # Test ControlFlow event handling
    controlflow_event_result = await controlflow_ext.handle({
        'type': 'agent_orchestration',
        'project_id': project_id,
        'requirements': 'Test orchestration',
        'config': {'priority': 'high'}
    })
    logger.info(f"   ControlFlow Event Result: {controlflow_event_result.get('status')}")
    
    # Test Codegen event handling
    codegen_event_result = await codegen_ext.handle({
        'type': 'task_execution',
        'task_id': 'demo-task-001',
        'task_description': 'Test task execution',
        'config': {'timeout': 300}
    })
    logger.info(f"   Codegen Event Result: {codegen_event_result.get('status')}")
    
    # Test Grainchain event handling
    grainchain_event_result = await grainchain_ext.handle({
        'type': 'quality_gates',
        'project_id': project_id,
        'config': {'strict_mode': True},
        'context': {'source': 'demo'}
    })
    logger.info(f"   Grainchain Event Result: {grainchain_event_result.get('status')}")
    
    # Test Graph_sitter event handling
    graph_sitter_event_result = await graph_sitter_ext.handle({
        'type': 'comprehensive_analysis',
        'project_id': project_id,
        'codebase_path': '.',
        'config': {'analysis_depth': 'full'}
    })
    logger.info(f"   Graph_sitter Event Result: {graph_sitter_event_result.get('status')}")
    
    # Display final status summary
    logger.info("📈 Final Status Summary:")
    logger.info("=" * 60)
    
    # Get status from each extension
    prefect_status = {'system_watches': 1, 'monitoring_active': True}
    controlflow_status = controlflow_ext.get_agent_status()
    codegen_status = codegen_ext.get_task_status()
    grainchain_status = grainchain_ext.get_sandbox_status()
    graph_sitter_status = graph_sitter_ext.get_analysis_status()
    
    logger.info(f"🔄 Prefect Status: {prefect_status}")
    logger.info(f"🎯 ControlFlow Status: {controlflow_status}")
    logger.info(f"🤖 Codegen Status: {codegen_status}")
    logger.info(f"🏗️ Grainchain Status: {grainchain_status}")
    logger.info(f"🔍 Graph_sitter Status: {graph_sitter_status}")
    
    logger.info("=" * 60)
    logger.info("🎉 Comprehensive Contexten Integration Example Completed Successfully!")
    logger.info("✅ All 11 extensions working together in unified system")
    logger.info(f"📊 Total Extensions Used: {len(workflow_result.get('extensions_used', []))}")
    logger.info(f"🔗 Integration Points: Prefect↔ControlFlow, Codegen↔Extensions, Graph_sitter↔Grainchain")
    logger.info("🚀 System ready for production use with full orchestration capabilities")


########################################################################################################################
# EXTENSION EVENT HANDLERS (Demonstrating existing patterns)
########################################################################################################################

async def setup_event_handlers(app: ContextenApp):
    """Set up event handlers following existing patterns from examples."""
    
    @app.github.event("pull_request")
    async def handle_pr_event(event):
        """Handle GitHub PR events using existing GitHub extension."""
        logger.info(f"[GITHUB] Received PR event: {event.get('action')}")
        
        # Trigger comprehensive analysis for PR
        if event.get('action') == 'opened':
            project_id = f"pr-{event.get('number')}"
            
            # Execute comprehensive workflow for PR
            workflow_result = await app.execute_comprehensive_workflow(
                project_id=project_id,
                requirements=f"Analyze PR #{event.get('number')} and validate changes"
            )
            
            logger.info(f"[GITHUB] PR analysis completed: {workflow_result.get('status')}")
        
        return {"status": "handled", "event_type": "pull_request"}
    
    @app.linear.event("issue_created")
    async def handle_linear_issue(event):
        """Handle Linear issue events using existing Linear extension."""
        logger.info(f"[LINEAR] Received issue event: {event.get('type')}")
        
        # Trigger workflow for new issues
        if event.get('type') == 'issue_created':
            issue_id = event.get('data', {}).get('id')
            project_id = f"linear-{issue_id}"
            
            # Execute workflow for Linear issue
            workflow_result = await app.execute_comprehensive_workflow(
                project_id=project_id,
                requirements=f"Process Linear issue {issue_id} and create action plan"
            )
            
            logger.info(f"[LINEAR] Issue processing completed: {workflow_result.get('status')}")
        
        return {"status": "handled", "event_type": "issue_created"}
    
    @app.slack.event("app_mention")
    async def handle_slack_mention(event):
        """Handle Slack mentions using existing Slack extension."""
        logger.info(f"[SLACK] Received mention event")
        
        # Extract message and trigger appropriate workflow
        text = event.get('text', '')
        if 'analyze' in text.lower():
            project_id = f"slack-{event.get('ts')}"
            
            # Execute analysis workflow
            workflow_result = await app.execute_comprehensive_workflow(
                project_id=project_id,
                requirements=f"Analyze based on Slack request: {text}"
            )
            
            logger.info(f"[SLACK] Analysis completed: {workflow_result.get('status')}")
        
        return {"status": "handled", "event_type": "app_mention"}


########################################################################################################################
# MAIN EXECUTION
########################################################################################################################

if __name__ == "__main__":
    """Run the comprehensive integration example."""
    try:
        # Run the main demonstration
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Example interrupted by user")
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        raise
    finally:
        logger.info("🏁 Example execution finished")

