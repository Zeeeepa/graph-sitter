# Grainchain Extension - Sandboxed Deployment + Snapshot saving + Graph_sitter Analysis
# Imports existing contexten and graph_sitter components

import logging
from typing import Any, Callable, Dict, Optional, TypeVar
from fastapi import Request
from pydantic import BaseModel

# Import existing graph_sitter components
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter import Codebase

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class Grainchain:
    """Grainchain extension for sandboxed deployment, snapshot saving, and Graph_sitter analysis integration."""
    
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize Grainchain components using existing modules (lazy import)
        self.config = None
        self.quality_gate_manager = None
        self.sandbox_manager = None
        self.grainchain_client = None
        self.graph_sitter_quality_gates = None
        
        # Sandbox and snapshot tracking
        self.active_sandboxes: Dict[str, Any] = {}
        self.snapshots: Dict[str, Any] = {}
        self.quality_results: Dict[str, Any] = {}
        
        logger.info("✅ Grainchain extension initialized with sandboxed deployment and Graph_sitter integration")

    def register_handler(self, event_type: str, handler: Callable[[T], Any]) -> None:
        """Register an event handler for Grainchain operations."""
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
        logger.info(f"Registered Grainchain handler for event type: {event_type}")

    async def handle(self, payload: dict, request: Optional[Request] = None) -> Any:
        """Handle Grainchain sandboxed deployment and analysis events."""
        event_type = payload.get('type', 'unknown')
        logger.info(f"Handling Grainchain event: {event_type}")
        
        try:
            # Process sandboxed deployment and analysis events
            if event_type == 'sandbox_deployment':
                return await self._handle_sandbox_deployment(payload)
            elif event_type == 'snapshot_saving':
                return await self._handle_snapshot_saving(payload)
            elif event_type == 'quality_gates':
                return await self._handle_quality_gates(payload)
            elif event_type == 'graph_sitter_analysis':
                return await self._handle_graph_sitter_analysis(payload)
            else:
                # Handle custom registered handlers
                if event_type in self.registered_handlers:
                    results = []
                    for handler in self.registered_handlers[event_type]:
                        result = await handler(payload)
                        results.append(result)
                    return results
                else:
                    logger.warning(f"No handler registered for Grainchain event type: {event_type}")
                    return {'status': 'no_handler', 'event_type': event_type}
                    
        except Exception as e:
            logger.error(f"Error handling Grainchain event {event_type}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _handle_sandbox_deployment(self, payload: dict) -> dict:
        """Handle sandbox deployment using existing SandboxManager components."""
        try:
            project_id = payload.get('project_id')
            deployment_config = payload.get('config', {})
            
            # Lazy import to avoid circular dependencies
            if not self.sandbox_manager:
                try:
                    from ..grainchain.config import GrainchainIntegrationConfig
                    from ..grainchain.sandbox_manager import SandboxManager
                    
                    self.config = GrainchainIntegrationConfig()
                    self.sandbox_manager = SandboxManager(self.config)
                except ImportError:
                    logger.warning("SandboxManager not available, using fallback")
                    return {
                        'status': 'completed',
                        'project_id': project_id,
                        'sandbox_id': f'fallback-{project_id}',
                        'deployment_result': {'fallback': True}
                    }
            
            # Use existing SandboxManager for deployment
            deployment_result = await self.sandbox_manager.create_sandbox(
                project_id=project_id,
                context=deployment_config
            )
            
            # Track active sandbox
            self.active_sandboxes[project_id] = {
                'config': deployment_config,
                'deployment_result': deployment_result,
                'status': 'active'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'sandbox_id': deployment_result.get('sandbox_id'),
                'deployment_result': deployment_result
            }
            
        except Exception as e:
            logger.error(f"Sandbox deployment failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_snapshot_saving(self, payload: dict) -> dict:
        """Handle snapshot saving using existing sandbox components."""
        try:
            project_id = payload.get('project_id')
            snapshot_config = payload.get('config', {})
            
            # Use existing SandboxManager for snapshot creation
            snapshot_result = await self.sandbox_manager.create_snapshot(
                project_id=project_id,
                config=snapshot_config
            )
            
            # Store snapshot information
            snapshot_id = snapshot_result.get('snapshot_id')
            self.snapshots[snapshot_id] = {
                'project_id': project_id,
                'config': snapshot_config,
                'snapshot_result': snapshot_result,
                'timestamp': snapshot_result.get('timestamp')
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'snapshot_id': snapshot_id,
                'snapshot_result': snapshot_result
            }
            
        except Exception as e:
            logger.error(f"Snapshot saving failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_quality_gates(self, payload: dict) -> dict:
        """Handle quality gates using existing QualityGateManager components."""
        try:
            project_id = payload.get('project_id')
            quality_config = payload.get('config', {})
            context = payload.get('context', {})
            
            # Use existing QualityGateManager for quality validation
            quality_result = await self.quality_gate_manager.execute_quality_gates(
                project_id=project_id,
                context=context,
                config=quality_config
            )
            
            # Store quality results
            self.quality_results[project_id] = {
                'config': quality_config,
                'context': context,
                'quality_result': quality_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'quality_result': quality_result,
                'gates_passed': quality_result.get('gates_passed', 0),
                'gates_failed': quality_result.get('gates_failed', 0)
            }
            
        except Exception as e:
            logger.error(f"Quality gates execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_graph_sitter_analysis(self, payload: dict) -> dict:
        """Handle Graph_sitter analysis using existing integration components."""
        try:
            project_id = payload.get('project_id')
            analysis_config = payload.get('config', {})
            context = payload.get('context', {})
            
            # Use existing GraphSitterQualityGates for analysis
            analysis_result = await self.graph_sitter_quality_gates.execute_comprehensive_analysis(
                project_id=project_id,
                context=context,
                config=analysis_config
            )
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'analysis_result': analysis_result,
                'pr_valid': analysis_result.get('pr_valid', False),
                'issues_found': analysis_result.get('issues_found', [])
            }
            
        except Exception as e:
            logger.error(f"Graph_sitter analysis failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def create_sandbox(self, project_id: str, config: dict) -> dict:
        """Create sandbox using existing SandboxManager components."""
        try:
            # Use existing SandboxManager for sandbox creation
            sandbox_result = await self.sandbox_manager.create_sandbox(
                project_id=project_id,
                context=config
            )
            
            # Track active sandbox
            self.active_sandboxes[project_id] = {
                'config': config,
                'sandbox_result': sandbox_result,
                'status': 'active'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'sandbox_id': sandbox_result.get('sandbox_id'),
                'sandbox_result': sandbox_result
            }
            
        except Exception as e:
            logger.error(f"Sandbox creation failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def execute_quality_gates(self, project_id: str, context: dict) -> dict:
        """Execute quality gates using existing QualityGateManager components."""
        try:
            # Use existing QualityGateManager for quality validation
            quality_result = await self.quality_gate_manager.execute_quality_gates(
                project_id=project_id,
                context=context
            )
            
            # Store quality results
            self.quality_results[project_id] = {
                'context': context,
                'quality_result': quality_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'quality_result': quality_result,
                'gates_passed': quality_result.get('gates_passed', 0),
                'gates_failed': quality_result.get('gates_failed', 0)
            }
            
        except Exception as e:
            logger.error(f"Quality gates execution failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def execute_comprehensive_analysis(self, project_id: str, context: dict, config: dict = None) -> dict:
        """Execute comprehensive analysis using existing Graph_sitter integration."""
        try:
            # Use existing GraphSitterQualityGates for comprehensive analysis
            analysis_result = await self.graph_sitter_quality_gates.execute_comprehensive_analysis(
                project_id=project_id,
                context=context,
                config=config or {}
            )
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'analysis_result': analysis_result,
                'pr_valid': analysis_result.get('pr_valid', False),
                'issues_found': analysis_result.get('issues_found', []),
                'quality_score': analysis_result.get('quality_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def create_snapshot(self, project_id: str, config: dict) -> dict:
        """Create snapshot using existing SandboxManager components."""
        try:
            # Use existing SandboxManager for snapshot creation
            snapshot_result = await self.sandbox_manager.create_snapshot(
                project_id=project_id,
                config=config
            )
            
            # Store snapshot information
            snapshot_id = snapshot_result.get('snapshot_id')
            self.snapshots[snapshot_id] = {
                'project_id': project_id,
                'config': config,
                'snapshot_result': snapshot_result,
                'timestamp': snapshot_result.get('timestamp')
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'snapshot_id': snapshot_id,
                'snapshot_result': snapshot_result
            }
            
        except Exception as e:
            logger.error(f"Snapshot creation failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def validate_pr(self, project_id: str, pr_data: dict) -> dict:
        """Validate PR using existing Graph_sitter analysis components."""
        try:
            # Use existing GraphSitterQualityGates for PR validation
            validation_result = await self.graph_sitter_quality_gates.validate_pr(
                project_id=project_id,
                pr_data=pr_data
            )
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'pr_valid': validation_result.get('valid', False),
                'validation_result': validation_result,
                'issues_found': validation_result.get('issues', [])
            }
            
        except Exception as e:
            logger.error(f"PR validation failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    def event(self, event_type: str):
        """Decorator for registering Grainchain event handlers."""
        def decorator(func: Callable[[T], Any]) -> Callable[[T], Any]:
            self.register_handler(event_type, func)
            return func
        return decorator

    async def initialize(self):
        """Initialize Grainchain extension with existing components."""
        try:
            # Initialize quality gate manager
            await self.quality_gate_manager.initialize()
            
            # Initialize sandbox manager
            await self.sandbox_manager.initialize()
            
            # Initialize Graph_sitter quality gates
            await self.graph_sitter_quality_gates.initialize()
            
            # Initialize Grainchain client
            await self.grainchain_client.initialize()
            
            logger.info("✅ Grainchain extension fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Grainchain extension: {e}")
            raise

    def get_sandbox_status(self) -> dict:
        """Get status of all sandboxes."""
        return {
            'active_sandboxes': len(self.active_sandboxes),
            'total_snapshots': len(self.snapshots),
            'quality_results': len(self.quality_results),
            'sandboxes': {
                project_id: {
                    'status': sandbox_info.get('status'),
                    'sandbox_id': sandbox_info.get('deployment_result', {}).get('sandbox_id')
                }
                for project_id, sandbox_info in self.active_sandboxes.items()
            }
        }

    async def cleanup_sandbox(self, project_id: str) -> dict:
        """Cleanup sandbox using existing SandboxManager components."""
        try:
            if project_id not in self.active_sandboxes:
                return {'status': 'failed', 'error': f'No active sandbox for project {project_id}'}
            
            # Use existing SandboxManager for cleanup
            cleanup_result = await self.sandbox_manager.cleanup_sandbox(project_id)
            
            # Remove from active sandboxes
            del self.active_sandboxes[project_id]
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'cleanup_result': cleanup_result
            }
            
        except Exception as e:
            logger.error(f"Sandbox cleanup failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def execute_full_pipeline(self, project_id: str, context: dict) -> dict:
        """Execute full Grainchain pipeline: Sandbox -> Analysis -> Quality Gates -> Snapshot."""
        try:
            pipeline_result = {
                'project_id': project_id,
                'status': 'running',
                'stages': {}
            }
            
            # Stage 1: Create Sandbox
            logger.info(f"🏗️ Stage 1: Creating sandbox for project {project_id}")
            sandbox_result = await self.create_sandbox(project_id, context.get('sandbox_config', {}))
            pipeline_result['stages']['sandbox'] = sandbox_result
            
            if sandbox_result['status'] != 'completed':
                pipeline_result['status'] = 'failed'
                return pipeline_result
            
            # Stage 2: Execute Graph_sitter Analysis
            logger.info(f"��� Stage 2: Executing Graph_sitter analysis for project {project_id}")
            analysis_result = await self.execute_comprehensive_analysis(
                project_id, context, context.get('analysis_config', {})
            )
            pipeline_result['stages']['analysis'] = analysis_result
            
            # Stage 3: Execute Quality Gates
            logger.info(f"✅ Stage 3: Executing quality gates for project {project_id}")
            quality_result = await self.execute_quality_gates(project_id, context)
            pipeline_result['stages']['quality_gates'] = quality_result
            
            # Stage 4: Create Snapshot
            logger.info(f"📸 Stage 4: Creating snapshot for project {project_id}")
            snapshot_result = await self.create_snapshot(project_id, context.get('snapshot_config', {}))
            pipeline_result['stages']['snapshot'] = snapshot_result
            
            # Final status
            pipeline_result['status'] = 'completed'
            pipeline_result['summary'] = {
                'sandbox_created': sandbox_result['status'] == 'completed',
                'analysis_completed': analysis_result['status'] == 'completed',
                'quality_gates_passed': quality_result.get('gates_passed', 0),
                'snapshot_created': snapshot_result['status'] == 'completed',
                'pr_valid': analysis_result.get('pr_valid', False)
            }
            
            logger.info(f"🎉 Full Grainchain pipeline completed for project {project_id}")
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Full pipeline execution failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e), 'project_id': project_id}
