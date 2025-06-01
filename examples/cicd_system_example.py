#!/usr/bin/env python3
"""
Comprehensive Graph-Sitter CI/CD System Example

This example demonstrates the complete CI/CD system with:
- Task management and execution
- Pipeline orchestration
- Codegen SDK integration
- OpenEvolve continuous learning
- Self-healing capabilities
- Analytics and monitoring
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Import all CI/CD components
from src.graph_sitter.cicd import (
    TaskManager, Task, TaskType, TaskStatus,
    PipelineEngine, Pipeline, PipelineStep, StepType,
    CodegenClient, CodegenAgent, AgentType,
    OpenEvolveClient, Evaluation, EvaluationType,
    SelfHealingSystem, IncidentSeverity,
    AnalyticsEngine, MetricsCollector, MetricType
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GraphSitterCICD:
    """
    Complete Graph-Sitter CI/CD system orchestrator
    """
    
    def __init__(self, organization_id: str, codegen_org_id: str, codegen_token: str):
        self.organization_id = organization_id
        
        # Initialize core components
        self.metrics_collector = MetricsCollector(organization_id)
        self.task_manager = TaskManager(organization_id)
        self.pipeline_engine = PipelineEngine(organization_id, self.task_manager)
        self.codegen_client = CodegenClient(organization_id, codegen_org_id, codegen_token)
        self.openevolve_client = OpenEvolveClient(organization_id)
        self.self_healing_system = SelfHealingSystem(organization_id)
        self.analytics_engine = AnalyticsEngine(organization_id, self.metrics_collector)
        
        # System state
        self.running = False
        
    async def start(self) -> None:
        """Start the complete CI/CD system"""
        logger.info("Starting Graph-Sitter CI/CD system...")
        
        # Start all subsystems
        await self.self_healing_system.start()
        
        self.running = True
        logger.info("Graph-Sitter CI/CD system started successfully")
    
    async def stop(self) -> None:
        """Stop the CI/CD system"""
        logger.info("Stopping Graph-Sitter CI/CD system...")
        
        self.running = False
        await self.self_healing_system.stop()
        
        logger.info("Graph-Sitter CI/CD system stopped")
    
    async def create_sample_workflow(self) -> Dict[str, Any]:
        """Create a sample workflow demonstrating all capabilities"""
        logger.info("Creating sample workflow...")
        
        # 1. Create Codegen agents
        logger.info("Setting up Codegen agents...")
        
        code_analyzer = CodegenAgent(
            name="Code Analyzer",
            description="Analyzes code quality and suggests improvements",
            agent_type=AgentType.ANALYZER,
            capabilities=["code_analysis", "quality_assessment", "security_scan"]
        )
        analyzer_id = await self.codegen_client.create_agent(code_analyzer)
        
        code_generator = CodegenAgent(
            name="Code Generator",
            description="Generates code based on specifications",
            agent_type=AgentType.GENERAL,
            capabilities=["code_generation", "documentation", "testing"]
        )
        generator_id = await self.codegen_client.create_agent(code_generator)
        
        # 2. Create tasks
        logger.info("Creating tasks...")
        
        analysis_task = Task(
            title="Analyze codebase for improvements",
            description="Perform comprehensive code analysis to identify improvement opportunities",
            task_type=TaskType.ANALYSIS,
            priority=2,
            estimated_hours=2.0
        )
        analysis_task_id = await self.task_manager.create_task(analysis_task)
        
        feature_task = Task(
            title="Implement new feature",
            description="Implement the new user authentication feature",
            task_type=TaskType.FEATURE,
            priority=1,
            estimated_hours=8.0,
            dependencies=[analysis_task_id]
        )
        feature_task_id = await self.task_manager.create_task(feature_task)
        
        test_task = Task(
            title="Create comprehensive tests",
            description="Create unit and integration tests for the new feature",
            task_type=TaskType.TEST,
            priority=2,
            estimated_hours=4.0,
            dependencies=[feature_task_id]
        )
        test_task_id = await self.task_manager.create_task(test_task)
        
        # 3. Create pipeline
        logger.info("Creating CI/CD pipeline...")
        
        pipeline = Pipeline(
            name="Feature Development Pipeline",
            description="Complete pipeline for feature development with analysis, implementation, and testing",
            pipeline_type="feature_development",
            trigger_events=["task_created", "code_changed"]
        )
        
        # Add pipeline steps
        pipeline.add_step(PipelineStep(
            name="Code Analysis",
            step_order=1,
            step_type=StepType.CODEGEN_TASK,
            configuration={
                "task": {
                    "title": "Automated Code Analysis",
                    "description": "Analyze code quality and security"
                },
                "agent_id": analyzer_id
            }
        ))
        
        pipeline.add_step(PipelineStep(
            name="Feature Implementation",
            step_order=2,
            step_type=StepType.CODEGEN_TASK,
            configuration={
                "task": {
                    "title": "Feature Implementation",
                    "description": "Implement the requested feature"
                },
                "agent_id": generator_id
            }
        ))
        
        pipeline.add_step(PipelineStep(
            name="Test Generation",
            step_order=3,
            step_type=StepType.CODEGEN_TASK,
            configuration={
                "task": {
                    "title": "Test Generation",
                    "description": "Generate comprehensive tests"
                },
                "agent_id": generator_id
            }
        ))
        
        pipeline.add_step(PipelineStep(
            name="Quality Gate",
            step_order=4,
            step_type=StepType.CONDITION,
            configuration={
                "condition": "step_Code_Analysis_result.get('quality_score', 0) >= 80"
            }
        ))
        
        pipeline_id = await self.pipeline_engine.create_pipeline(pipeline)
        
        # 4. Execute workflow
        logger.info("Executing workflow...")
        
        # Execute pipeline
        pipeline_execution = await self.pipeline_engine.execute_pipeline(
            pipeline_id,
            trigger_event="manual_trigger",
            context={"project": "sample_project", "feature": "user_authentication"}
        )
        
        # Execute tasks
        task_executions = await self.task_manager.execute_workflow([
            analysis_task_id, feature_task_id, test_task_id
        ])
        
        # 5. Collect metrics
        logger.info("Collecting metrics...")
        
        await self.metrics_collector.collect_batch_metrics([
            {"name": "pipeline_execution_time", "value": pipeline_execution.duration_seconds or 0, "type": "timer", "unit": "seconds"},
            {"name": "task_success_rate", "value": 100.0, "type": "gauge", "unit": "%"},
            {"name": "code_quality_score", "value": 85.5, "type": "gauge", "unit": "score"},
            {"name": "test_coverage", "value": 92.3, "type": "gauge", "unit": "%"}
        ])
        
        # 6. Trigger OpenEvolve evaluation
        logger.info("Triggering OpenEvolve evaluation...")
        
        evaluation = Evaluation(
            target_type="pipeline",
            target_id=pipeline_id,
            evaluation_type=EvaluationType.WORKFLOW_OPTIMIZATION,
            context_data={
                "pipeline_execution_id": pipeline_execution.id,
                "task_executions": [te.id for te in task_executions.values()],
                "metrics": {
                    "execution_time": pipeline_execution.duration_seconds,
                    "success_rate": 100.0,
                    "quality_score": 85.5
                }
            }
        )
        
        evaluation_id = await self.openevolve_client.submit_evaluation(evaluation)
        
        # Wait for evaluation results (in real scenario, this would be async)
        await asyncio.sleep(1)
        evaluation_result = await self.openevolve_client.get_evaluation_result(evaluation_id)
        
        # 7. Perform analytics
        logger.info("Performing analytics...")
        
        performance_analysis = await self.analytics_engine.analyze_performance(
            "pipeline", pipeline_id, period_days=1
        )
        
        quality_analysis = await self.analytics_engine.analyze_quality(
            "pipeline", pipeline_id, period_days=1
        )
        
        # Detect patterns
        patterns = await self.analytics_engine.detect_patterns(period_days=1)
        
        # Get optimization recommendations
        recommendations = await self.analytics_engine.get_optimization_recommendations()
        
        # 8. Simulate an incident for self-healing demonstration
        logger.info("Simulating incident for self-healing demonstration...")
        
        incident_id = await self.self_healing_system.detect_incident(
            incident_type="performance_degradation",
            error_message="Pipeline execution time exceeded threshold: 300s > 180s",
            context={"pipeline_id": pipeline_id, "execution_time": 300},
            severity=IncidentSeverity.MEDIUM
        )
        
        # Wait for self-healing to process
        await asyncio.sleep(2)
        
        # 9. Get system health
        system_health = await self.self_healing_system.get_system_health()
        health_score = await self.analytics_engine.get_system_health_score()
        
        return {
            "workflow_summary": {
                "pipeline_id": pipeline_id,
                "pipeline_execution_id": pipeline_execution.id,
                "task_executions": len(task_executions),
                "agents_used": 2,
                "evaluation_id": evaluation_id
            },
            "performance_metrics": {
                "pipeline_duration_seconds": pipeline_execution.duration_seconds,
                "pipeline_status": pipeline_execution.status.value,
                "task_success_rate": len([te for te in task_executions.values() if te.status == TaskStatus.COMPLETED]) / len(task_executions) * 100
            },
            "analysis_results": {
                "performance_score": performance_analysis.score,
                "quality_score": quality_analysis.score,
                "patterns_detected": len(patterns),
                "recommendations_count": len(recommendations)
            },
            "openevolve_results": {
                "evaluation_status": evaluation_result.status.value if evaluation_result else "pending",
                "effectiveness_score": evaluation_result.effectiveness_score if evaluation_result else None,
                "improvements_identified": len(evaluation_result.generated_solutions) if evaluation_result else 0
            },
            "self_healing": {
                "incident_id": incident_id,
                "system_health_score": system_health["overall_health_score"],
                "active_incidents": system_health["active_incidents"]
            },
            "system_health": health_score
        }
    
    async def demonstrate_continuous_learning(self) -> Dict[str, Any]:
        """Demonstrate continuous learning capabilities"""
        logger.info("Demonstrating continuous learning...")
        
        # 1. Discover patterns from historical data
        patterns = await self.openevolve_client.discover_patterns("system_metrics", time_range_days=30)
        
        # 2. Apply learned patterns
        pattern_applications = []
        for pattern in patterns[:2]:  # Apply first 2 patterns
            application_result = await self.openevolve_client.apply_pattern(
                pattern.id,
                context={"target_type": "system", "optimization_goal": "performance"}
            )
            pattern_applications.append(application_result)
        
        # 3. Get improvement recommendations
        recommendations = await self.openevolve_client.get_system_improvement_recommendations()
        
        # 4. Get learning metrics
        learning_metrics = await self.openevolve_client.get_learning_metrics()
        
        return {
            "patterns_discovered": len(patterns),
            "patterns_applied": len([app for app in pattern_applications if app["applied"]]),
            "improvement_recommendations": len(recommendations),
            "learning_effectiveness": learning_metrics["pattern_metrics"]["avg_pattern_effectiveness"],
            "system_learning_rate": learning_metrics["improvement_metrics"]["system_learning_rate"]
        }
    
    async def demonstrate_self_healing(self) -> Dict[str, Any]:
        """Demonstrate self-healing capabilities"""
        logger.info("Demonstrating self-healing capabilities...")
        
        # 1. Simulate various incidents
        incidents = []
        
        # Memory issue
        memory_incident = await self.self_healing_system.detect_incident(
            "memory_exhaustion",
            "Memory usage exceeded 95%: 96.5% > 95%",
            context={"memory_usage": 96.5, "threshold": 95},
            severity=IncidentSeverity.CRITICAL
        )
        incidents.append(memory_incident)
        
        # Database connection issue
        db_incident = await self.self_healing_system.detect_incident(
            "database_connection_failure",
            "Database connection pool exhausted",
            context={"active_connections": 100, "max_connections": 100},
            severity=IncidentSeverity.HIGH
        )
        incidents.append(db_incident)
        
        # Performance degradation
        perf_incident = await self.self_healing_system.detect_incident(
            "performance_degradation",
            "Response time degraded: 2500ms > 2000ms",
            context={"response_time": 2500, "threshold": 2000},
            severity=IncidentSeverity.MEDIUM
        )
        incidents.append(perf_incident)
        
        # 2. Wait for self-healing to process incidents
        await asyncio.sleep(3)
        
        # 3. Get incident metrics
        incident_metrics = await self.self_healing_system.get_incident_metrics()
        
        # 4. Get system health after healing
        system_health = await self.self_healing_system.get_system_health()
        
        return {
            "incidents_created": len(incidents),
            "auto_resolution_rate": incident_metrics["auto_resolution_rate"],
            "avg_resolution_time": incident_metrics["avg_resolution_time_seconds"],
            "system_health_score": system_health["overall_health_score"],
            "recovery_procedures_available": incident_metrics["recovery_procedures"]["total"]
        }


async def main():
    """Main demonstration function"""
    logger.info("Starting Graph-Sitter CI/CD System Demonstration")
    
    # Initialize system
    cicd_system = GraphSitterCICD(
        organization_id="demo_org_001",
        codegen_org_id="323",  # Your Codegen org ID
        codegen_token="your_codegen_token_here"  # Your Codegen token
    )
    
    try:
        # Start the system
        await cicd_system.start()
        
        # Run demonstrations
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATION 1: Complete Workflow")
        logger.info("="*60)
        
        workflow_results = await cicd_system.create_sample_workflow()
        
        logger.info("\nWorkflow Results:")
        logger.info(f"  Pipeline executed: {workflow_results['workflow_summary']['pipeline_id']}")
        logger.info(f"  Task success rate: {workflow_results['performance_metrics']['task_success_rate']:.1f}%")
        logger.info(f"  Performance score: {workflow_results['analysis_results']['performance_score']:.1f}")
        logger.info(f"  Quality score: {workflow_results['analysis_results']['quality_score']:.1f}")
        logger.info(f"  System health: {workflow_results['system_health']['overall_score']:.1f}")
        
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATION 2: Continuous Learning")
        logger.info("="*60)
        
        learning_results = await cicd_system.demonstrate_continuous_learning()
        
        logger.info("\nContinuous Learning Results:")
        logger.info(f"  Patterns discovered: {learning_results['patterns_discovered']}")
        logger.info(f"  Patterns applied: {learning_results['patterns_applied']}")
        logger.info(f"  Improvement recommendations: {learning_results['improvement_recommendations']}")
        logger.info(f"  Learning effectiveness: {learning_results['learning_effectiveness']:.1f}")
        
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATION 3: Self-Healing")
        logger.info("="*60)
        
        healing_results = await cicd_system.demonstrate_self_healing()
        
        logger.info("\nSelf-Healing Results:")
        logger.info(f"  Incidents processed: {healing_results['incidents_created']}")
        logger.info(f"  Auto-resolution rate: {healing_results['auto_resolution_rate']:.1%}")
        logger.info(f"  Avg resolution time: {healing_results['avg_resolution_time']:.1f}s")
        logger.info(f"  System health after healing: {healing_results['system_health_score']:.1f}")
        
        # Final system status
        logger.info("\n" + "="*60)
        logger.info("FINAL SYSTEM STATUS")
        logger.info("="*60)
        
        # Get comprehensive system metrics
        agent_performance = await cicd_system.codegen_client.get_agent_performance(
            list(cicd_system.codegen_client.agents.keys())[0] if cicd_system.codegen_client.agents else "none"
        )
        
        cost_analysis = await cicd_system.codegen_client.get_cost_analysis(time_period_days=1)
        
        logger.info("\nCodegen Integration:")
        logger.info(f"  Active agents: {len(cicd_system.codegen_client.agents)}")
        logger.info(f"  Total cost: ${cost_analysis['total_cost']:.2f}")
        logger.info(f"  Tasks executed: {cost_analysis['task_count']}")
        
        logger.info("\nOpenEvolve Integration:")
        logger.info(f"  Total evaluations: {cicd_system.openevolve_client.metrics['total_evaluations']}")
        logger.info(f"  Patterns discovered: {cicd_system.openevolve_client.metrics['patterns_discovered']}")
        logger.info(f"  Improvements identified: {cicd_system.openevolve_client.metrics['total_improvements_identified']}")
        
        logger.info("\nSelf-Healing System:")
        logger.info(f"  Total incidents: {cicd_system.self_healing_system.metrics['total_incidents']}")
        logger.info(f"  Auto-resolved: {cicd_system.self_healing_system.metrics['auto_resolved_incidents']}")
        logger.info(f"  System availability: {cicd_system.self_healing_system.metrics['system_availability']:.1f}%")
        
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATION COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise
    finally:
        # Stop the system
        await cicd_system.stop()


if __name__ == "__main__":
    asyncio.run(main())

