#!/usr/bin/env python3
"""
OpenEvolve Integration Example

This example demonstrates how to use the OpenEvolve integration module
for continuous learning and system evolution.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from graph_sitter.openevolve import EvaluationService
from graph_sitter.openevolve.models import EvaluationTrigger, EvaluationStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockDatabaseSession:
    """Mock database session for demonstration purposes."""
    
    def __init__(self):
        self.evaluations = {}
        self.improvements = {}
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def query(self, model):
        return MockQuery()


class MockQuery:
    """Mock query object for demonstration."""
    
    def filter(self, *args):
        return self
    
    def first(self):
        return None
    
    def all(self):
        return []
    
    def order_by(self, *args):
        return self
    
    def offset(self, offset):
        return self
    
    def limit(self, limit):
        return self


async def demonstrate_basic_usage():
    """Demonstrate basic OpenEvolve integration usage."""
    logger.info("=== Basic Usage Demonstration ===")
    
    # Initialize configuration
    config = OpenEvolveConfig()
    
    # Check if properly configured
    if not config.is_configured:
        logger.warning("OpenEvolve not configured. Set OPENEVOLVE_API_KEY environment variable.")
        logger.info("Using mock mode for demonstration...")
        config.api_key = "demo_key"  # For demonstration only
    
    # Initialize mock database session
    session = MockDatabaseSession()
    
    try:
        # Initialize service
        async with EvaluationService(config, session) as service:
            logger.info("OpenEvolve service initialized successfully")
            
            # Start background processing
            service.start_processing()
            logger.info("Background evaluation processing started")
            
            # Demonstrate triggering evaluations
            await demonstrate_evaluation_triggering(service)
            
            # Demonstrate monitoring
            await demonstrate_monitoring(service)
            
            # Demonstrate system improvements
            await demonstrate_improvements(service)
            
            # Stop processing
            service.stop_processing()
            logger.info("Background processing stopped")
            
    except Exception as e:
        logger.error(f"Error in demonstration: {e}")


async def demonstrate_evaluation_triggering(service: EvaluationService):
    """Demonstrate different ways to trigger evaluations."""
    logger.info("\n--- Evaluation Triggering ---")
    
    # Example 1: Task failure evaluation
    try:
        task_failure_context = {
            "task_id": "data_processing_task_001",
            "error_type": "timeout",
            "duration": 300,
            "resource_usage": {
                "cpu": 0.85,
                "memory": 0.92,
                "disk_io": 0.45
            },
            "input_size": 1024000,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        eval_id = await service.trigger_evaluation(
            trigger_event=EvaluationTrigger.TASK_FAILURE,
            context=task_failure_context,
            priority=2,  # High priority
            metadata={
                "component": "data_processor",
                "version": "1.2.3",
                "environment": "production"
            }
        )
        
        logger.info(f"Task failure evaluation triggered: {eval_id}")
        
    except Exception as e:
        logger.error(f"Failed to trigger task failure evaluation: {e}")
    
    # Example 2: Performance degradation evaluation
    try:
        performance_context = {
            "metrics": {
                "response_time": 2.5,  # seconds
                "throughput": 150,     # requests/second
                "error_rate": 0.05,    # 5%
                "cpu_usage": 0.78,
                "memory_usage": 0.82
            },
            "baseline_metrics": {
                "response_time": 1.2,
                "throughput": 300,
                "error_rate": 0.01,
                "cpu_usage": 0.45,
                "memory_usage": 0.55
            },
            "degradation_percentage": 45.2,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        eval_id = await service.trigger_evaluation(
            trigger_event=EvaluationTrigger.PERFORMANCE_DEGRADATION,
            context=performance_context,
            priority=3,
            metadata={
                "service": "api_gateway",
                "region": "us-west-2",
                "load_balancer": "lb-001"
            }
        )
        
        logger.info(f"Performance degradation evaluation triggered: {eval_id}")
        
    except Exception as e:
        logger.error(f"Failed to trigger performance evaluation: {e}")
    
    # Example 3: Manual evaluation
    try:
        manual_context = {
            "reason": "weekly_system_review",
            "requested_by": "system_admin",
            "focus_areas": [
                "security_vulnerabilities",
                "performance_optimization",
                "resource_utilization"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        eval_id = await service.trigger_evaluation(
            trigger_event=EvaluationTrigger.MANUAL,
            context=manual_context,
            priority=5,  # Normal priority
            metadata={
                "review_type": "weekly",
                "scope": "full_system"
            }
        )
        
        logger.info(f"Manual evaluation triggered: {eval_id}")
        
    except Exception as e:
        logger.error(f"Failed to trigger manual evaluation: {e}")


async def demonstrate_monitoring(service: EvaluationService):
    """Demonstrate evaluation monitoring capabilities."""
    logger.info("\n--- Evaluation Monitoring ---")
    
    try:
        # Get evaluation summary
        summary = await service.get_evaluation_summary(days=7)
        logger.info(f"Evaluation Summary (last 7 days):")
        logger.info(f"  Total evaluations: {summary.total_evaluations}")
        logger.info(f"  Completed: {summary.completed_evaluations}")
        logger.info(f"  Failed: {summary.failed_evaluations}")
        logger.info(f"  Success rate: {summary.success_rate:.1f}%")
        
        if summary.average_execution_time:
            logger.info(f"  Average execution time: {summary.average_execution_time:.2f}s")
        
        if summary.average_improvement_score:
            logger.info(f"  Average improvement score: {summary.average_improvement_score:.2f}")
        
        # List recent evaluations
        recent_evaluations = await service.list_evaluations(limit=5)
        logger.info(f"\nRecent evaluations ({len(recent_evaluations)}):")
        
        for eval_result in recent_evaluations:
            logger.info(f"  {eval_result.id}: {eval_result.status}")
        
        # List failed evaluations
        failed_evaluations = await service.list_evaluations(
            status=EvaluationStatus.FAILED,
            limit=3
        )
        
        if failed_evaluations:
            logger.info(f"\nRecent failed evaluations ({len(failed_evaluations)}):")
            for eval_result in failed_evaluations:
                logger.info(f"  {eval_result.id}: {eval_result.error_message}")
        
    except Exception as e:
        logger.error(f"Error in monitoring demonstration: {e}")


async def demonstrate_improvements(service: EvaluationService):
    """Demonstrate system improvement handling."""
    logger.info("\n--- System Improvements ---")
    
    try:
        # This would typically be called after evaluations complete
        # For demonstration, we'll show the process
        
        logger.info("System improvement process:")
        logger.info("1. Evaluations complete and generate improvement recommendations")
        logger.info("2. Improvements are stored in the database with priority and impact scores")
        logger.info("3. High-priority improvements can be automatically applied")
        logger.info("4. Results are tracked for effectiveness measurement")
        
        # Example improvement types that might be generated:
        example_improvements = [
            {
                "type": "cache_optimization",
                "description": "Implement Redis caching for frequently accessed data",
                "priority": 2,
                "estimated_impact": 0.25,
                "complexity": "medium"
            },
            {
                "type": "query_optimization", 
                "description": "Add database indexes for slow queries",
                "priority": 1,
                "estimated_impact": 0.40,
                "complexity": "low"
            },
            {
                "type": "resource_scaling",
                "description": "Increase memory allocation for data processing workers",
                "priority": 3,
                "estimated_impact": 0.15,
                "complexity": "low"
            }
        ]
        
        logger.info("\nExample improvements that might be generated:")
        for improvement in example_improvements:
            logger.info(f"  {improvement['type']}: {improvement['description']}")
            logger.info(f"    Priority: {improvement['priority']}, Impact: {improvement['estimated_impact']:.0%}")
        
    except Exception as e:
        logger.error(f"Error in improvements demonstration: {e}")


async def demonstrate_event_driven_integration():
    """Demonstrate event-driven integration patterns."""
    logger.info("\n=== Event-Driven Integration ===")
    
    class SystemEventHandler:
        """Example system event handler."""
        
        def __init__(self, evaluation_service: EvaluationService):
            self.evaluation_service = evaluation_service
        
        async def on_task_failure(self, task_id: str, error: Exception, context: Dict[str, Any]):
            """Handle task failure events."""
            logger.info(f"Task failure detected: {task_id}")
            
            try:
                await self.evaluation_service.trigger_evaluation(
                    trigger_event=EvaluationTrigger.TASK_FAILURE,
                    context={
                        "task_id": task_id,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        **context
                    },
                    priority=2
                )
                logger.info(f"Evaluation triggered for task failure: {task_id}")
            except Exception as e:
                logger.error(f"Failed to trigger evaluation for task {task_id}: {e}")
        
        async def on_performance_alert(self, metrics: Dict[str, float], thresholds: Dict[str, float]):
            """Handle performance alert events."""
            logger.info("Performance degradation detected")
            
            try:
                await self.evaluation_service.trigger_evaluation(
                    trigger_event=EvaluationTrigger.PERFORMANCE_DEGRADATION,
                    context={
                        "current_metrics": metrics,
                        "thresholds": thresholds,
                        "degradation_detected": True,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    priority=3
                )
                logger.info("Evaluation triggered for performance degradation")
            except Exception as e:
                logger.error(f"Failed to trigger performance evaluation: {e}")
    
    # Initialize configuration and service
    config = OpenEvolveConfig()
    if not config.is_configured:
        config.api_key = "demo_key"  # For demonstration
    
    session = MockDatabaseSession()
    
    try:
        async with EvaluationService(config, session) as service:
            handler = SystemEventHandler(service)
            
            # Simulate events
            await handler.on_task_failure(
                task_id="batch_job_001",
                error=TimeoutError("Task exceeded 5 minute timeout"),
                context={
                    "duration": 320,
                    "resource_usage": {"cpu": 0.95, "memory": 0.88},
                    "input_records": 50000
                }
            )
            
            await handler.on_performance_alert(
                metrics={
                    "response_time": 3.2,
                    "throughput": 120,
                    "error_rate": 0.08
                },
                thresholds={
                    "response_time": 2.0,
                    "throughput": 200,
                    "error_rate": 0.02
                }
            )
            
    except Exception as e:
        logger.error(f"Error in event-driven demonstration: {e}")


async def demonstrate_api_integration():
    """Demonstrate REST API integration."""
    logger.info("\n=== REST API Integration ===")
    
    logger.info("The OpenEvolve module provides a complete REST API:")
    logger.info("  POST /api/v1/openevolve/evaluations - Create evaluation")
    logger.info("  GET  /api/v1/openevolve/evaluations/{id} - Get evaluation")
    logger.info("  GET  /api/v1/openevolve/evaluations - List evaluations")
    logger.info("  DELETE /api/v1/openevolve/evaluations/{id} - Cancel evaluation")
    logger.info("  GET  /api/v1/openevolve/summary - Get evaluation summary")
    logger.info("  GET  /api/v1/openevolve/health - Health check")
    
    logger.info("\nExample API usage:")
    logger.info("""
    # Create evaluation
    curl -X POST "http://localhost:8000/api/v1/openevolve/evaluations" \\
      -H "Content-Type: application/json" \\
      -d '{
        "trigger_event": "task_failure",
        "context": {"task_id": "task_123"},
        "priority": 3
      }'
    
    # Get evaluation summary
    curl "http://localhost:8000/api/v1/openevolve/summary?days=30"
    
    # Health check
    curl "http://localhost:8000/api/v1/openevolve/health"
    """)


async def main():
    """Main demonstration function."""
    logger.info("OpenEvolve Integration Module Demonstration")
    logger.info("=" * 50)
    
    # Check environment
    api_key = os.getenv("OPENEVOLVE_API_KEY")
    if api_key:
        logger.info("✅ OpenEvolve API key found")
    else:
        logger.warning("⚠️  OpenEvolve API key not found - using demo mode")
    
    try:
        # Run demonstrations
        await demonstrate_basic_usage()
        await demonstrate_event_driven_integration()
        await demonstrate_api_integration()
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Demonstration completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Set up your OpenEvolve API key")
        logger.info("2. Configure your database with the migration script")
        logger.info("3. Integrate the service into your application")
        logger.info("4. Set up event handlers for your specific use cases")
        logger.info("5. Monitor evaluation results and apply improvements")
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

