# Prefect Extension - Top Layer System Watch Flows
# Imports existing contexten and graph_sitter components

import logging
from typing import Any, Callable, Dict, Optional, TypeVar
from fastapi import Request
from pydantic import BaseModel

# Import existing contexten components
from contexten.extensions.modal.interface import EventHandlerManagerProtocol
from contexten.extensions.prefect.flow import PrefectFlow
from contexten.extensions.prefect.workflow_pipeline import PrefectWorkflowPipeline

# Import existing graph_sitter components
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter import Codebase

# Import existing controlflow components for orchestration
from ..controlflow.orchestrator import FlowOrchestrator

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class Prefect(EventHandlerManagerProtocol):
    """Prefect extension for top-layer system watch flows and orchestration."""
    
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize Prefect components using existing modules
        self.flow = PrefectFlow(app=app)
        self.pipeline = PrefectWorkflowPipeline(name=f"{app.name}_prefect_pipeline")
        
        # Integration with other extensions
        self.controlflow_integration: Optional[FlowOrchestrator] = None
        
        logger.info("✅ Prefect extension initialized with system watch flows")

    def register_handler(self, event_type: str, handler: Callable[[T], Any]) -> None:
        """Register an event handler for Prefect flows."""
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
        logger.info(f"Registered Prefect handler for event type: {event_type}")

    async def handle(self, payload: dict, request: Optional[Request] = None) -> Any:
        """Handle Prefect flow events and system watch triggers."""
        event_type = payload.get('type', 'unknown')
        logger.info(f"Handling Prefect event: {event_type}")
        
        try:
            # Process system watch flows
            if event_type == 'system_watch':
                return await self._handle_system_watch(payload)
            elif event_type == 'workflow_trigger':
                return await self._handle_workflow_trigger(payload)
            elif event_type == 'flow_monitoring':
                return await self._handle_flow_monitoring(payload)
            else:
                # Handle custom registered handlers
                if event_type in self.registered_handlers:
                    results = []
                    for handler in self.registered_handlers[event_type]:
                        result = await handler(payload)
                        results.append(result)
                    return results
                else:
                    logger.warning(f"No handler registered for Prefect event type: {event_type}")
                    return {'status': 'no_handler', 'event_type': event_type}
                    
        except Exception as e:
            logger.error(f"Error handling Prefect event {event_type}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _handle_system_watch(self, payload: dict) -> dict:
        """Handle system watch flows using existing Prefect components."""
        try:
            project_id = payload.get('project_id')
            watch_config = payload.get('config', {})
            
            # Use existing PrefectFlow for system monitoring
            watch_result = await self.flow.create_system_watch_flow(
                project_id=project_id,
                config=watch_config
            )
            
            return {
                'status': 'completed',
                'flow_id': watch_result.get('flow_id'),
                'watch_config': watch_config,
                'project_id': project_id
            }
            
        except Exception as e:
            logger.error(f"System watch flow failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_workflow_trigger(self, payload: dict) -> dict:
        """Handle workflow triggers using existing pipeline components."""
        try:
            project_id = payload.get('project_id')
            requirements = payload.get('requirements')
            trigger_type = payload.get('trigger_type', 'manual')
            
            # Use existing PrefectWorkflowPipeline for execution
            from ..prefect.workflow_pipeline import PipelineContext
            
            context = PipelineContext(
                project_id=project_id,
                requirements=requirements,
                config={'trigger_type': trigger_type},
                variables={'source': 'prefect_extension'}
            )
            
            pipeline_result = await self.pipeline.execute_pipeline(context)
            
            return {
                'status': 'completed',
                'pipeline_result': pipeline_result,
                'trigger_type': trigger_type,
                'project_id': project_id
            }
            
        except Exception as e:
            logger.error(f"Workflow trigger failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_flow_monitoring(self, payload: dict) -> dict:
        """Handle flow monitoring using existing monitoring components."""
        try:
            flow_id = payload.get('flow_id')
            monitoring_config = payload.get('config', {})
            
            # Use existing monitoring capabilities
            from ..prefect.monitoring import PrefectMonitoring
            
            monitoring = PrefectMonitoring()
            monitoring_result = await monitoring.monitor_flow(
                flow_id=flow_id,
                config=monitoring_config
            )
            
            return {
                'status': 'completed',
                'monitoring_result': monitoring_result,
                'flow_id': flow_id
            }
            
        except Exception as e:
            logger.error(f"Flow monitoring failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def integrate_with_controlflow(self, controlflow_orchestrator: FlowOrchestrator):
        """Integrate Prefect with ControlFlow orchestrator."""
        try:
            self.controlflow_integration = controlflow_orchestrator
            
            # Register Prefect flows with ControlFlow
            await controlflow_orchestrator.register_flow_provider(
                provider_id="prefect",
                provider_name="Prefect System Flows",
                flow_handler=self.flow
            )
            
            logger.info("✅ Prefect integrated with ControlFlow orchestrator")
            
        except Exception as e:
            logger.error(f"Failed to integrate Prefect with ControlFlow: {e}")

    async def create_comprehensive_system_watch(self, project_id: str, config: dict) -> dict:
        """Create comprehensive system watch using all integrated components."""
        try:
            # Create system watch flow using existing components
            watch_flow = await self.flow.create_system_watch_flow(
                project_id=project_id,
                config=config
            )
            
            # Set up monitoring using existing monitoring components
            from ..prefect.monitoring import PrefectMonitoring
            monitoring = PrefectMonitoring()
            
            monitoring_setup = await monitoring.setup_flow_monitoring(
                flow_id=watch_flow.get('flow_id'),
                config=config.get('monitoring', {})
            )
            
            # Integrate with ControlFlow if available
            if self.controlflow_integration:
                await self.controlflow_integration.register_system_watch(
                    watch_id=watch_flow.get('flow_id'),
                    project_id=project_id,
                    config=config
                )
            
            return {
                'status': 'completed',
                'watch_flow': watch_flow,
                'monitoring': monitoring_setup,
                'project_id': project_id,
                'integrated_with_controlflow': self.controlflow_integration is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive system watch: {e}")
            return {'status': 'failed', 'error': str(e)}

    def event(self, event_type: str):
        """Decorator for registering Prefect event handlers."""
        def decorator(func: Callable[[T], Any]) -> Callable[[T], Any]:
            self.register_handler(event_type, func)
            return func
        return decorator

    async def initialize(self):
        """Initialize Prefect extension with existing components."""
        try:
            # Initialize flow components
            await self.flow.initialize()
            
            # Initialize pipeline components
            await self.pipeline.initialize()
            
            logger.info("✅ Prefect extension fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Prefect extension: {e}")
            raise
