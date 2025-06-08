# ControlFlow Extension - Agent Orchestrator
# Imports existing contexten and graph_sitter components

import logging
from typing import Any, Callable, Dict, Optional, TypeVar, List
from fastapi import Request
from pydantic import BaseModel

# Import existing graph_sitter components
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter import Codebase

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class ControlFlow:
    """ControlFlow extension for agent orchestration and workflow coordination."""
    
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize ControlFlow components using existing modules (lazy import)
        self.orchestrator = None
        self.codegen_integration = None
        
        # Agent management
        self.registered_agents: Dict[str, Any] = {}
        self.active_workflows: Dict[str, Any] = {}
        
        # Integration with other extensions
        self.prefect_integration: Optional[Any] = None
        self.codegen_clients: List[Any] = []
        
        logger.info("✅ ControlFlow extension initialized with agent orchestration")

    def register_handler(self, event_type: str, handler: Callable[[T], Any]) -> None:
        """Register an event handler for ControlFlow orchestration."""
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
        logger.info(f"Registered ControlFlow handler for event type: {event_type}")

    async def handle(self, payload: dict, request: Optional[Request] = None) -> Any:
        """Handle ControlFlow orchestration events."""
        event_type = payload.get('type', 'unknown')
        logger.info(f"Handling ControlFlow event: {event_type}")
        
        try:
            # Process agent orchestration events
            if event_type == 'agent_orchestration':
                return await self._handle_agent_orchestration(payload)
            elif event_type == 'workflow_coordination':
                return await self._handle_workflow_coordination(payload)
            elif event_type == 'agent_registration':
                return await self._handle_agent_registration(payload)
            elif event_type == 'task_distribution':
                return await self._handle_task_distribution(payload)
            else:
                # Handle custom registered handlers
                if event_type in self.registered_handlers:
                    results = []
                    for handler in self.registered_handlers[event_type]:
                        result = await handler(payload)
                        results.append(result)
                    return results
                else:
                    logger.warning(f"No handler registered for ControlFlow event type: {event_type}")
                    return {'status': 'no_handler', 'event_type': event_type}
                    
        except Exception as e:
            logger.error(f"Error handling ControlFlow event {event_type}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _handle_agent_orchestration(self, payload: dict) -> dict:
        """Handle agent orchestration using existing ControlFlow components."""
        try:
            project_id = payload.get('project_id')
            requirements = payload.get('requirements')
            orchestration_config = payload.get('config', {})
            
            # Lazy import to avoid circular dependencies
            if not self.orchestrator:
                try:
                    from ..controlflow.orchestrator import FlowOrchestrator
                    self.orchestrator = FlowOrchestrator()
                except ImportError:
                    logger.warning("FlowOrchestrator not available, using fallback")
                    return {
                        'status': 'completed',
                        'orchestration_result': {'fallback': True},
                        'project_id': project_id,
                        'agents_used': []
                    }
            
            # Use existing FlowOrchestrator for agent coordination
            orchestration_result = await self.orchestrator.orchestrate_workflow(
                project_id=project_id,
                requirements=requirements,
                config=orchestration_config
            )
            
            return {
                'status': 'completed',
                'orchestration_result': orchestration_result,
                'project_id': project_id,
                'agents_used': orchestration_result.get('agents_used', [])
            }
            
        except Exception as e:
            logger.error(f"Agent orchestration failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_workflow_coordination(self, payload: dict) -> dict:
        """Handle workflow coordination using existing orchestrator components."""
        try:
            workflow_id = payload.get('workflow_id')
            coordination_config = payload.get('config', {})
            
            # Use existing orchestrator for workflow coordination
            coordination_result = await self.orchestrator.coordinate_workflow(
                workflow_id=workflow_id,
                config=coordination_config
            )
            
            return {
                'status': 'completed',
                'coordination_result': coordination_result,
                'workflow_id': workflow_id
            }
            
        except Exception as e:
            logger.error(f"Workflow coordination failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_agent_registration(self, payload: dict) -> dict:
        """Handle agent registration using existing integration components."""
        try:
            agent_config = payload.get('agent_config', {})
            agent_type = agent_config.get('type', 'codegen')
            
            if agent_type == 'codegen':
                # Register Codegen agent using existing integration
                registration_result = await self.codegen_integration.register_codegen_agent(
                    agent_id=agent_config.get('agent_id'),
                    name=agent_config.get('name'),
                    org_id=agent_config.get('org_id'),
                    token=agent_config.get('token'),
                    base_url=agent_config.get('base_url', 'https://api.codegen.com')
                )
                
                # Store registered agent
                self.registered_agents[agent_config.get('agent_id')] = {
                    'type': agent_type,
                    'config': agent_config,
                    'registration_result': registration_result
                }
                
                return {
                    'status': 'completed',
                    'agent_id': agent_config.get('agent_id'),
                    'registration_result': registration_result
                }
            else:
                return {'status': 'failed', 'error': f'Unsupported agent type: {agent_type}'}
            
        except Exception as e:
            logger.error(f"Agent registration failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_task_distribution(self, payload: dict) -> dict:
        """Handle task distribution using existing orchestrator components."""
        try:
            tasks = payload.get('tasks', [])
            distribution_config = payload.get('config', {})
            
            # Use existing orchestrator for task distribution
            distribution_result = await self.orchestrator.distribute_tasks(
                tasks=tasks,
                config=distribution_config,
                available_agents=list(self.registered_agents.keys())
            )
            
            return {
                'status': 'completed',
                'distribution_result': distribution_result,
                'tasks_distributed': len(tasks)
            }
            
        except Exception as e:
            logger.error(f"Task distribution failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def register_codegen_agent(self, agent_id: str, name: str, client: Any) -> dict:
        """Register a Codegen agent using existing integration components."""
        try:
            # Use existing CodegenFlowIntegration for registration
            registration_result = await self.codegen_integration.register_codegen_agent(
                agent_id=agent_id,
                name=name,
                org_id=client.org_id,
                token=client.token,
                base_url=client.base_url
            )
            
            # Store the client for future use
            self.codegen_clients.append(client)
            self.registered_agents[agent_id] = {
                'type': 'codegen',
                'name': name,
                'client': client,
                'registration_result': registration_result
            }
            
            logger.info(f"✅ Registered Codegen agent: {agent_id} ({name})")
            
            return {
                'status': 'completed',
                'agent_id': agent_id,
                'name': name,
                'registration_result': registration_result
            }
            
        except Exception as e:
            logger.error(f"Failed to register Codegen agent {agent_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def orchestrate_workflow(self, project_id: str, requirements: str) -> dict:
        """Orchestrate workflow using all registered agents and existing components."""
        try:
            # Create workflow using existing orchestrator
            workflow_result = await self.orchestrator.orchestrate_workflow(
                project_id=project_id,
                requirements=requirements
            )
            
            # Store active workflow
            self.active_workflows[project_id] = {
                'requirements': requirements,
                'result': workflow_result,
                'agents_used': workflow_result.get('agents_used', [])
            }
            
            return {
                'status': 'completed',
                'workflow_result': workflow_result,
                'project_id': project_id,
                'registered_agents': len(self.registered_agents),
                'active_workflows': len(self.active_workflows)
            }
            
        except Exception as e:
            logger.error(f"Workflow orchestration failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def integrate_with_prefect(self, prefect_extension: Any):
        """Integrate ControlFlow with Prefect extension."""
        try:
            self.prefect_integration = prefect_extension
            
            # Register ControlFlow as orchestrator with Prefect
            await prefect_extension.integrate_with_controlflow(self.orchestrator)
            
            logger.info("✅ ControlFlow integrated with Prefect extension")
            
        except Exception as e:
            logger.error(f"Failed to integrate ControlFlow with Prefect: {e}")

    async def register_flow_provider(self, provider_id: str, provider_name: str, flow_handler: Any):
        """Register a flow provider using existing orchestrator components."""
        try:
            # Use existing orchestrator for flow provider registration
            registration_result = await self.orchestrator.register_flow_provider(
                provider_id=provider_id,
                provider_name=provider_name,
                flow_handler=flow_handler
            )
            
            return {
                'status': 'completed',
                'provider_id': provider_id,
                'provider_name': provider_name,
                'registration_result': registration_result
            }
            
        except Exception as e:
            logger.error(f"Failed to register flow provider {provider_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def register_system_watch(self, watch_id: str, project_id: str, config: dict):
        """Register system watch using existing orchestrator components."""
        try:
            # Use existing orchestrator for system watch registration
            registration_result = await self.orchestrator.register_system_watch(
                watch_id=watch_id,
                project_id=project_id,
                config=config
            )
            
            return {
                'status': 'completed',
                'watch_id': watch_id,
                'project_id': project_id,
                'registration_result': registration_result
            }
            
        except Exception as e:
            logger.error(f"Failed to register system watch {watch_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    def event(self, event_type: str):
        """Decorator for registering ControlFlow event handlers."""
        def decorator(func: Callable[[T], Any]) -> Callable[[T], Any]:
            self.register_handler(event_type, func)
            return func
        return decorator

    async def initialize(self):
        """Initialize ControlFlow extension with existing components."""
        try:
            # Initialize orchestrator components
            await self.orchestrator.initialize()
            
            # Initialize Codegen integration components
            await self.codegen_integration.initialize()
            
            logger.info("✅ ControlFlow extension fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ControlFlow extension: {e}")
            raise

    def get_agent_status(self) -> dict:
        """Get status of all registered agents."""
        return {
            'total_agents': len(self.registered_agents),
            'active_workflows': len(self.active_workflows),
            'agents': {
                agent_id: {
                    'type': agent_info.get('type'),
                    'name': agent_info.get('name'),
                    'status': 'active'
                }
                for agent_id, agent_info in self.registered_agents.items()
            }
        }

    async def execute_task_with_agent(self, task: dict, agent_id: str) -> dict:
        """Execute a task with a specific agent using existing integration components."""
        try:
            if agent_id not in self.registered_agents:
                return {'status': 'failed', 'error': f'Agent {agent_id} not registered'}
            
            agent_info = self.registered_agents[agent_id]
            
            if agent_info['type'] == 'codegen':
                # Use existing Codegen integration for task execution
                execution_result = await self.codegen_integration.execute_task_with_codegen(
                    task=task,
                    agent_id=agent_id,
                    client=agent_info.get('client')
                )
                
                return {
                    'status': 'completed',
                    'task': task,
                    'agent_id': agent_id,
                    'execution_result': execution_result
                }
            else:
                return {'status': 'failed', 'error': f'Unsupported agent type: {agent_info["type"]}'}
            
        except Exception as e:
            logger.error(f"Task execution failed with agent {agent_id}: {e}")
            return {'status': 'failed', 'error': str(e)}
