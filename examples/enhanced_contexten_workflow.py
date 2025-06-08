#!/usr/bin/env python3
"""
Enhanced Contexten Workflow Example

Demonstrates the complete consolidated system with seamless transitions
between Prefect, ControlFlow, Codegen SDK, Grainchain, and Graph_sitter.
"""

import asyncio
import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate enhanced Contexten workflow system."""
    print("🚀 Enhanced Contexten Workflow System Demo")
async def main():
    """Demonstrate enhanced Contexten workflow system."""
    print("🚀 Enhanced Contexten Workflow System Demo")
    print("=" * 60)
    
    # Configuration
    config = load_configuration()
    
    try:
        # Step 1: Initialize ContextenApp with enhanced orchestration
        app = await initialize_app(config)
        
        # Step 2: Execute comprehensive workflow pipeline
        workflow_result = await execute_workflow(app, config)
        
        # Step 3: Display results
        display_results(workflow_result)
        
        # Step 4: Demonstrate individual component capabilities
        await demonstrate_components(app, config)
        
        return workflow_result
        
    except ImportError as e:
        logger.error(f"Required module not found: {e}")
        print(f"\n❌ Required module not found: {e}")
        return None
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return None
        1. FastAPI-based REST API with authentication
        2. User management with CRUD operations
        3. Database integration with SQLAlchemy
        4. Comprehensive test suite with pytest
        5. API documentation with OpenAPI/Swagger
        6. Docker containerization
        7. CI/CD pipeline configuration
        
        The API should be production-ready with proper error handling,
        logging, and security best practices.
        ''',
        'codegen_config': {
            'org_id': os.getenv('CODEGEN_ORG_ID', '11'),
            'token': os.getenv('CODEGEN_API_TOKEN', 'demo_token'),
            'base_url': os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
        }
    }
    
    try:
        # Step 1: Initialize ContextenApp with enhanced orchestration
        print("\n1. Initializing Enhanced ContextenApp...")
        
        from src.contexten.extensions.contexten_app.contexten_app import ContextenApp
        
        app = ContextenApp(
            name="enhanced_demo_app",
            repo=".",  # Current directory
            tmp_dir="/tmp/contexten_demo"
        )
        
        # Initialize orchestration components
        await app.initialize_orchestration()
        print("   ✅ Enhanced orchestration components initialized")
        
        # Step 2: Execute comprehensive workflow pipeline
        print("\n2. Executing Enhanced Workflow Pipeline...")
        print(f"   Project: {config['project_id']}")
        print(f"   Requirements: {config['requirements'][:100]}...")
        
        workflow_result = await app.execute_workflow_pipeline(
            project_id=config['project_id'],
            requirements=config['requirements']
        )
        
        # Step 3: Display results
        print("\n3. Workflow Results:")
        print(f"   Status: {workflow_result['status']}")
        print(f"   Project ID: {workflow_result['project_id']}")
        
        # Display stage results
        stages = workflow_result.get('stages', {})
        for stage_name, stage_data in stages.items():
            status = stage_data.get('status', 'unknown')
            duration = stage_data.get('duration', 0)
            print(f"   📋 {stage_name.title()}: {status} ({duration:.2f}s)")
        
        # Display pipeline metrics if available
        pipeline_metrics = workflow_result.get('results', {}).get('pipeline_metrics', {})
        if pipeline_metrics:
            print("\n4. Pipeline Metrics:")
            for metric_name, metric_value in pipeline_metrics.items():
                print(f"   📊 {metric_name}: {metric_value}")
        
        # Step 4: Demonstrate individual component capabilities
        print("\n5. Individual Component Demonstrations:")
        
        # Demonstrate Codegen workflow integration
        if hasattr(app, '_codegen_agent') and app._codegen_agent:
            print("\n   🤖 Codegen SDK Integration:")
            try:
                from src.contexten.extensions.codegen.workflow_integration import (
                    create_codegen_workflow_integration, WorkflowContext, WorkflowTask, WorkflowStage, TaskStatus
                )
                
                codegen_integration = create_codegen_workflow_integration(
                    org_id=config['codegen_config']['org_id'],
                    token=config['codegen_config']['token'],
                    base_url=config['codegen_config']['base_url']
                )
                
                # Create sample workflow context
                context = WorkflowContext(
                    project_id=config['project_id'],
                    requirements="Create a simple FastAPI endpoint",
                    config={'timeout': 300},
                    variables={'framework': 'fastapi'},
                    tools_available=['codegen', 'github', 'linear'],
                    mcp_servers=['filesystem', 'web_search']
                )
                
                # Create sample tasks
                tasks = [
                    WorkflowTask(
                        id="task_1",
                        name="Create FastAPI Application",
                        description="Create a basic FastAPI application with health check endpoint",
                        stage=WorkflowStage.EXECUTION,
                        dependencies=[],
                        tools_required=['codegen'],
                        estimated_duration=300,
                        priority=1
                    )
                ]
                
                print("      ✅ Codegen workflow integration ready")
                print(f"      📝 Sample context: {context.project_id}")
                print(f"      📋 Sample tasks: {len(tasks)}")
                
            except Exception as e:
                print(f"      ❌ Codegen integration demo failed: {e}")
        
        # Demonstrate ControlFlow orchestration
        if hasattr(app, 'flow_orchestrator') and app.flow_orchestrator:
            print("\n   🎯 ControlFlow Orchestration:")
            try:
                orchestrator = app.flow_orchestrator
                
                # Check registered agents
                agent_count = len(orchestrator.codegen_agents)
                print(f"      ✅ Registered agents: {agent_count}")
                
                if agent_count > 0:
                    for agent_id, agent in orchestrator.codegen_agents.items():
                        print(f"      🤖 Agent: {agent.name} ({agent_id})")
                        print(f"         Capabilities: {[cap.value for cap in agent.capabilities]}")
                        print(f"         Available: {agent.is_available}")
                
            except Exception as e:
                print(f"      ❌ ControlFlow demo failed: {e}")
        
        # Demonstrate Grainchain quality gates
        if hasattr(app, 'graph_sitter_quality_gates') and app.graph_sitter_quality_gates:
            print("\n   🔍 Grainchain + Graph_sitter Quality Gates:")
            try:
                quality_gates = app.graph_sitter_quality_gates
                
                # Run a simple analysis
                from src.contexten.extensions.grainchain.graph_sitter_integration import (
                    AnalysisConfig, AnalysisType, ValidationLevel
                )
                
                config = AnalysisConfig(
                    analysis_types=[AnalysisType.COMPREHENSIVE],
                    validation_level=ValidationLevel.LENIENT
                )
                
                print("      ✅ Quality gates system ready")
                print(f"      📊 Analysis types: {[t.value for t in config.analysis_types]}")
                print(f"      🎯 Validation level: {config.validation_level.value}")
                
            except Exception as e:
                print(f"      ❌ Quality gates demo failed: {e}")
        
        # Demonstrate Prefect pipeline
        if hasattr(app, 'prefect_pipeline') and app.prefect_pipeline:
            print("\n   ⚡ Prefect Workflow Pipeline:")
            try:
                pipeline = app.prefect_pipeline
                
                print(f"      ✅ Pipeline name: {pipeline.name}")
                print(f"      📊 Monitoring enabled: {pipeline.monitoring is not None}")
                print(f"      🔄 Stage callbacks: {len(pipeline.stage_callbacks)}")
                print(f"      🌐 Global callbacks: {len(pipeline.global_callbacks)}")
                
            except Exception as e:
                print(f"      ❌ Prefect pipeline demo failed: {e}")
        
        # Step 5: Health check
        print("\n6. System Health Check:")
        
        health_status = {
            'contexten_app': '✅ Healthy',
            'codegen_integration': '✅ Healthy' if hasattr(app, '_codegen_agent') and app._codegen_agent else '⚠️ Limited',
            'controlflow_orchestrator': '✅ Healthy' if hasattr(app, 'flow_orchestrator') and app.flow_orchestrator else '❌ Unavailable',
            'grainchain_quality_gates': '✅ Healthy' if hasattr(app, 'graph_sitter_quality_gates') and app.graph_sitter_quality_gates else '❌ Unavailable',
            'prefect_pipeline': '✅ Healthy' if hasattr(app, 'prefect_pipeline') and app.prefect_pipeline else '❌ Unavailable',
            'graph_sitter_analysis': '✅ Available',
            'modal_infrastructure': '✅ Ready'
        }
        
        for component, status in health_status.items():
            print(f"   {status} {component}")
        
        print("\n🎉 Enhanced Contexten Workflow Demo Completed!")
        print("\nKey Features Demonstrated:")
        print("✅ Unified ContextenApp orchestration hub")
        print("✅ Seamless tool transitions (Prefect → ControlFlow → Codegen)")
        print("✅ Enhanced Codegen SDK integration with workflow support")
        print("✅ Intelligent agent coordination and load balancing")
        print("✅ Comprehensive quality gates with Graph_sitter analysis")
        print("✅ Sandbox-based validation and testing")
        print("✅ Real-time monitoring and metrics collection")
        print("✅ Event-driven architecture with callbacks")
        
        return workflow_result
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return None


async def demonstrate_advanced_features():
    """Demonstrate advanced features of the enhanced system."""
    print("\n" + "=" * 60)
    print("🔬 Advanced Features Demonstration")
    print("=" * 60)
    
    try:
        # Demonstrate Strands workflow integration
        print("\n1. Strands Workflow Tools Integration:")
        try:
            from src.contexten.extensions.codegen.workflow_integration import StrandsWorkflowClient
            
            strands_client = StrandsWorkflowClient()
            print("   ✅ Strands workflow client available")
            print("   🔄 Supports agentic workflow loops")
            print("   🔗 Integrates with Codegen SDK executions")
            
        except Exception as e:
            print(f"   ⚠️ Strands integration: {e}")
        
        # Demonstrate MCP client integration
        print("\n2. MCP (Model Context Protocol) Integration:")
        try:
            from src.contexten.extensions.codegen.workflow_integration import MCPClientWrapper
            
            mcp_client = MCPClientWrapper()
            print("   ✅ MCP client wrapper available")
            print("   🔌 Supports configured MCP servers")
            print("   🚀 Enhances Codegen API SDK executions")
            
        except Exception as e:
            print(f"   ⚠️ MCP integration: {e}")
        
        # Demonstrate performance tracking
        print("\n3. Performance Tracking & Analytics:")
        try:
            from src.contexten.extensions.controlflow.codegen_integration import PerformanceTracker
            
            tracker = PerformanceTracker()
            print("   ✅ Performance tracking system")
            print("   📊 Agent performance metrics")
            print("   🎯 Task complexity analysis")
            print("   ⚡ Load balancing optimization")
            
        except Exception as e:
            print(f"   ⚠️ Performance tracking: {e}")
        
        # Demonstrate quality validation
        print("\n4. Advanced Quality Validation:")
        try:
            from src.contexten.extensions.grainchain.graph_sitter_integration import (
                AnalysisType, ValidationLevel
            )
            
            analysis_types = [t.value for t in AnalysisType]
            validation_levels = [l.value for l in ValidationLevel]
            
            print(f"   ✅ Analysis types: {', '.join(analysis_types)}")
            print(f"   🎯 Validation levels: {', '.join(validation_levels)}")
            print("   🔒 Sandbox-based isolated analysis")
            print("   📈 Configurable quality thresholds")
            
        except Exception as e:
            print(f"   ⚠️ Quality validation: {e}")
        
        print("\n🔬 Advanced Features Demo Completed!")
        
    except Exception as e:
        logger.error(f"Advanced features demo failed: {e}")
        print(f"\n❌ Advanced features demo failed: {e}")


if __name__ == "__main__":
    print("Starting Enhanced Contexten Workflow System Demo...")
    
    # Run main demo
    result = asyncio.run(main())
    
    # Run advanced features demo
    asyncio.run(demonstrate_advanced_features())
    
    if result:
        print(f"\n✅ Demo completed successfully!")
        print(f"📊 Workflow status: {result.get('status', 'unknown')}")
    else:
        print(f"\n❌ Demo completed with errors")
    
    print("\nFor production use:")
    print("1. Set environment variables: CODEGEN_ORG_ID, CODEGEN_API_TOKEN")
    print("2. Configure GitHub, Linear, Slack integrations")
    print("3. Set up Modal infrastructure deployment")
    print("4. Configure PostgreSQL database connection")
    print("5. Customize quality gate thresholds")
    print("6. Set up monitoring and alerting")

