"""
Basic usage example for the self-healing architecture.

This example demonstrates how to set up and use the self-healing system
for automated error detection, diagnosis, and recovery.
"""

import asyncio
import logging
from datetime import datetime

from graph_sitter.self_healing import (
    SelfHealingConfig,
    ErrorDetectionService,
    DiagnosisEngine,
    RecoverySystem,
    HealthMonitor,
    ErrorEvent,
    ErrorType,
    ErrorSeverity,
)
from graph_sitter.self_healing.orchestrator import SelfHealingOrchestrator


async def basic_example():
    """Basic example of using the self-healing system."""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting self-healing system example")
    
    # Create configuration
    config = SelfHealingConfig(
        enabled=True,
        log_level="INFO",
    )
    
    # Initialize the orchestrator
    orchestrator = SelfHealingOrchestrator(config)
    
    try:
        # Start the self-healing system
        await orchestrator.start()
        logger.info("Self-healing system started")
        
        # Simulate an error event
        error_event = ErrorEvent(
            error_type=ErrorType.MEMORY_LEAK,
            severity=ErrorSeverity.HIGH,
            message="Memory usage exceeded 90%",
            context={
                "current_memory": 92.5,
                "threshold": 85.0,
                "component": "web_server",
            },
            source_component="web_server",
            detected_at=datetime.utcnow(),
            tags=["performance", "memory"],
        )
        
        logger.info(f"Simulating error event: {error_event.message}")
        
        # Handle the error event
        incident_id = await orchestrator.handle_error_event(error_event)
        
        if incident_id:
            logger.info(f"Error event handled, incident ID: {incident_id}")
            
            # Monitor incident progress
            for i in range(10):  # Check for up to 10 iterations
                await asyncio.sleep(2)  # Wait 2 seconds between checks
                
                status = await orchestrator.get_incident_status(incident_id)
                if status:
                    logger.info(f"Incident status: {status['status']}")
                    
                    if status['resolved'] or status['status'] in ['escalated', 'escalation_failed']:
                        break
                else:
                    logger.warning("Could not get incident status")
                    break
        
        # Get system status
        system_status = orchestrator.get_system_status()
        logger.info(f"System status: {system_status}")
        
        # Get effectiveness report
        effectiveness_report = orchestrator.get_effectiveness_report()
        logger.info(f"Effectiveness report: {effectiveness_report}")
        
    finally:
        # Stop the self-healing system
        await orchestrator.stop()
        logger.info("Self-healing system stopped")


async def monitoring_example():
    """Example of using individual monitoring components."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting monitoring example")
    
    # Create health monitor
    health_monitor = HealthMonitor(update_interval=10)  # Check every 10 seconds
    
    # Add event handlers
    def on_health_update(metrics):
        logger.info(f"Health update: {len(metrics)} metrics collected")
        for name, metric in metrics.items():
            logger.info(f"  {name}: {metric.current_value:.1f} ({metric.status.value})")
    
    def on_status_change(new_status):
        logger.info(f"System health status changed to: {new_status.value}")
    
    health_monitor.add_health_handler(on_health_update)
    health_monitor.add_status_handler(on_status_change)
    
    try:
        # Start monitoring
        await health_monitor.start()
        logger.info("Health monitoring started")
        
        # Let it run for 30 seconds
        await asyncio.sleep(30)
        
        # Get system status
        status = health_monitor.get_system_status()
        logger.info(f"Final system status: {status}")
        
    finally:
        # Stop monitoring
        await health_monitor.stop()
        logger.info("Health monitoring stopped")


async def error_detection_example():
    """Example of using the error detection service."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting error detection example")
    
    # Create error detection service
    from graph_sitter.self_healing.models.config import ErrorDetectionConfig
    
    config = ErrorDetectionConfig(
        monitoring_interval=5,  # Check every 5 seconds
        threshold_cpu=75.0,     # Lower threshold for demo
        threshold_memory=80.0,
    )
    
    error_detection = ErrorDetectionService(config)
    
    # Add error handler
    def on_error_detected(error_event):
        logger.info(f"Error detected: {error_event.error_type.value} - {error_event.message}")
        logger.info(f"  Severity: {error_event.severity.value}")
        logger.info(f"  Context: {error_event.context}")
    
    error_detection.add_error_handler(on_error_detected)
    
    try:
        # Start error detection
        await error_detection.start()
        logger.info("Error detection started")
        
        # Let it run for 20 seconds
        await asyncio.sleep(20)
        
    finally:
        # Stop error detection
        await error_detection.stop()
        logger.info("Error detection stopped")


if __name__ == "__main__":
    print("Self-Healing Architecture Examples")
    print("==================================")
    
    print("\n1. Running basic example...")
    asyncio.run(basic_example())
    
    print("\n2. Running monitoring example...")
    asyncio.run(monitoring_example())
    
    print("\n3. Running error detection example...")
    asyncio.run(error_detection_example())
    
    print("\nAll examples completed!")

