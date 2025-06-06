"""
Strands Orchestrator
Proper orchestration using Strands tools ecosystem
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio
from enum import Enum

from .strands_workflow import StrandsWorkflowManager
from .strands_mcp import StrandsMCPManager
from .strands_controlflow import StrandsControlFlowManager
from .strands_prefect import StrandsPrefectManager

logger = logging.getLogger(__name__)


class OrchestrationLayer(str, Enum):
    """Orchestration layers in the Strands ecosystem"""
    WORKFLOW = "workflow"  # Strands workflow layer
    MCP = "mcp"           # MCP agent layer
    CONTROLFLOW = "controlflow"  # ControlFlow integration
    PREFECT = "prefect"   # Prefect integration


class StrandsOrchestrator:
    """
    Main orchestrator using proper Strands tools ecosystem
    Coordinates workflow, MCP, ControlFlow, and Prefect layers
    """
    
    def __init__(self):
        self.workflow_manager = StrandsWorkflowManager()
        self.mcp_manager = StrandsMCPManager()
        self.controlflow_manager = StrandsControlFlowManager()
        self.prefect_manager = StrandsPrefectManager()
        
        self.active_orchestrations: Dict[str, Dict[str, Any]] = {}
        self.layer_status: Dict[OrchestrationLayer, bool] = {}
        
    async def initialize(self) -> Dict[OrchestrationLayer, bool]:
        """Initialize all orchestration layers"""
        try:
            logger.info("Initializing Strands orchestrator...")
            
            # Initialize workflow layer
            workflow_success = await self.workflow_manager.initialize()
            self.layer_status[OrchestrationLayer.WORKFLOW] = workflow_success
            
            # Initialize MCP layer
            mcp_success = await self.mcp_manager.initialize()
            self.layer_status[OrchestrationLayer.MCP] = mcp_success
            
            # Initialize ControlFlow layer
            controlflow_success = await self.controlflow_manager.initialize()
            self.layer_status[OrchestrationLayer.CONTROLFLOW] = controlflow_success
            
            # Initialize Prefect layer
            prefect_success = await self.prefect_manager.initialize()
            self.layer_status[OrchestrationLayer.PREFECT] = prefect_success
            
            logger.info(f"Strands orchestrator initialized. Layer status: {self.layer_status}")
            return self.layer_status
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands orchestrator: {e}")
            raise
    
    async def create_multi_layer_orchestration(self, config: Dict[str, Any]) -> str:
        """Create a multi-layer orchestration using Strands tools"""
        try:
            orchestration_id = f"orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            orchestration = {
                'id': orchestration_id,
                'name': config.get('name', 'Unnamed Orchestration'),
                'description': config.get('description', ''),
                'layers': config.get('layers', [OrchestrationLayer.WORKFLOW]),
                'status': 'created',
                'created_at': datetime.now().isoformat(),
                'workflow_id': None,
                'mcp_sessions': [],
                'controlflow_tasks': [],
                'prefect_flows': []
            }
            
            # Create workflow if workflow layer is requested
            if OrchestrationLayer.WORKFLOW in config.get('layers', []):
                if self.layer_status.get(OrchestrationLayer.WORKFLOW, False):
                    workflow_config = config.get('workflow', {})
                    workflow = await self.workflow_manager.create_workflow(workflow_config)
                    orchestration['workflow_id'] = workflow['id']
                    logger.info(f"Created workflow {workflow['id']} for orchestration {orchestration_id}")
            
            # Create MCP sessions if MCP layer is requested
            if OrchestrationLayer.MCP in config.get('layers', []):
                if self.layer_status.get(OrchestrationLayer.MCP, False):
                    mcp_configs = config.get('mcp_agents', [])
                    for mcp_config in mcp_configs:
                        session_id = await self.mcp_manager.create_agent_session(mcp_config)
                        orchestration['mcp_sessions'].append(session_id)
                        logger.info(f"Created MCP session {session_id} for orchestration {orchestration_id}")
            
            # Create ControlFlow tasks if ControlFlow layer is requested
            if OrchestrationLayer.CONTROLFLOW in config.get('layers', []):
                if self.layer_status.get(OrchestrationLayer.CONTROLFLOW, False):
                    controlflow_tasks = config.get('controlflow_tasks', [])
                    orchestration['controlflow_tasks'] = controlflow_tasks
                    logger.info(f"Created ControlFlow tasks for orchestration {orchestration_id}")
            
            # Create Prefect flows if Prefect layer is requested
            if OrchestrationLayer.PREFECT in config.get('layers', []):
                if self.layer_status.get(OrchestrationLayer.PREFECT, False):
                    prefect_flows = config.get('prefect_flows', [])
                    orchestration['prefect_flows'] = prefect_flows
                    logger.info(f"Created Prefect flows for orchestration {orchestration_id}")
            
            self.active_orchestrations[orchestration_id] = orchestration
            logger.info(f"Created multi-layer orchestration: {orchestration_id}")
            
            return orchestration_id
            
        except Exception as e:
            logger.error(f"Failed to create multi-layer orchestration: {e}")
            raise
    
    async def execute_orchestration(self, orchestration_id: str) -> Dict[str, Any]:
        """Execute a multi-layer orchestration"""
        try:
            if orchestration_id not in self.active_orchestrations:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            orchestration = self.active_orchestrations[orchestration_id]
            orchestration['status'] = 'running'
            orchestration['started_at'] = datetime.now().isoformat()
            
            results = {
                'orchestration_id': orchestration_id,
                'status': 'running',
                'layer_results': {}
            }
            
            # Execute workflow layer
            if orchestration['workflow_id']:
                try:
                    workflow_result = await self.workflow_manager.execute_workflow(orchestration['workflow_id'])
                    results['layer_results']['workflow'] = workflow_result
                    logger.info(f"Executed workflow for orchestration {orchestration_id}")
                except Exception as e:
                    logger.error(f"Workflow execution failed for orchestration {orchestration_id}: {e}")
                    results['layer_results']['workflow'] = {'error': str(e)}
            
            # Execute MCP sessions
            if orchestration['mcp_sessions']:
                mcp_results = []
                for session_id in orchestration['mcp_sessions']:
                    try:
                        # Execute a default task for each MCP session
                        task = {
                            'type': 'status_check',
                            'parameters': {'check_type': 'health'}
                        }
                        mcp_result = await self.mcp_manager.execute_agent_task(session_id, task)
                        mcp_results.append(mcp_result)
                        logger.info(f"Executed MCP task for session {session_id}")
                    except Exception as e:
                        logger.error(f"MCP task execution failed for session {session_id}: {e}")
                        mcp_results.append({'session_id': session_id, 'error': str(e)})
                
                results['layer_results']['mcp'] = mcp_results
            
            # Execute ControlFlow tasks
            if orchestration['controlflow_tasks']:
                controlflow_results = []
                for task in orchestration['controlflow_tasks']:
                    try:
                        result = await self.controlflow_manager.execute_task(task)
                        controlflow_results.append(result)
                        logger.info(f"Executed ControlFlow task {task['id']}")
                    except Exception as e:
                        logger.error(f"ControlFlow task execution failed for task {task['id']}: {e}")
                        controlflow_results.append({'task_id': task['id'], 'error': str(e)})
                
                results['layer_results']['controlflow'] = controlflow_results
            
            # Execute Prefect flows
            if orchestration['prefect_flows']:
                prefect_results = []
                for flow in orchestration['prefect_flows']:
                    try:
                        result = await self.prefect_manager.execute_flow(flow)
                        prefect_results.append(result)
                        logger.info(f"Executed Prefect flow {flow['id']}")
                    except Exception as e:
                        logger.error(f"Prefect flow execution failed for flow {flow['id']}: {e}")
                        prefect_results.append({'flow_id': flow['id'], 'error': str(e)})
                
                results['layer_results']['prefect'] = prefect_results
            
            orchestration['status'] = 'completed'
            orchestration['completed_at'] = datetime.now().isoformat()
            results['status'] = 'completed'
            
            logger.info(f"Completed orchestration execution: {orchestration_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute orchestration {orchestration_id}: {e}")
            if orchestration_id in self.active_orchestrations:
                self.active_orchestrations[orchestration_id]['status'] = 'failed'
                self.active_orchestrations[orchestration_id]['error'] = str(e)
            raise
    
    async def get_orchestration_status(self, orchestration_id: str) -> Dict[str, Any]:
        """Get orchestration status"""
        try:
            if orchestration_id not in self.active_orchestrations:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            orchestration = self.active_orchestrations[orchestration_id]
            
            status = {
                'orchestration_id': orchestration_id,
                'name': orchestration['name'],
                'status': orchestration['status'],
                'created_at': orchestration['created_at'],
                'layers': orchestration['layers'],
                'layer_status': {}
            }
            
            # Get workflow status
            if orchestration['workflow_id']:
                try:
                    workflow_status = await self.workflow_manager.get_workflow_status(orchestration['workflow_id'])
                    status['layer_status']['workflow'] = workflow_status
                except Exception as e:
                    status['layer_status']['workflow'] = {'error': str(e)}
            
            # Get MCP session statuses
            if orchestration['mcp_sessions']:
                mcp_statuses = []
                for session_id in orchestration['mcp_sessions']:
                    try:
                        session_status = await self.mcp_manager.get_session_status(session_id)
                        mcp_statuses.append(session_status)
                    except Exception as e:
                        mcp_statuses.append({'session_id': session_id, 'error': str(e)})
                
                status['layer_status']['mcp'] = mcp_statuses
            
            # Get ControlFlow task statuses
            if orchestration['controlflow_tasks']:
                controlflow_statuses = []
                for task in orchestration['controlflow_tasks']:
                    try:
                        task_status = await self.controlflow_manager.get_task_status(task['id'])
                        controlflow_statuses.append(task_status)
                    except Exception as e:
                        controlflow_statuses.append({'task_id': task['id'], 'error': str(e)})
                
                status['layer_status']['controlflow'] = controlflow_statuses
            
            # Get Prefect flow statuses
            if orchestration['prefect_flows']:
                prefect_statuses = []
                for flow in orchestration['prefect_flows']:
                    try:
                        flow_status = await self.prefect_manager.get_flow_status(flow['id'])
                        prefect_statuses.append(flow_status)
                    except Exception as e:
                        prefect_statuses.append({'flow_id': flow['id'], 'error': str(e)})
                
                status['layer_status']['prefect'] = prefect_statuses
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get orchestration status {orchestration_id}: {e}")
            raise
    
    async def list_orchestrations(self) -> List[Dict[str, Any]]:
        """List all orchestrations"""
        try:
            orchestrations = []
            for orchestration_id, orchestration in self.active_orchestrations.items():
                orchestrations.append({
                    'id': orchestration_id,
                    'name': orchestration['name'],
                    'status': orchestration['status'],
                    'created_at': orchestration['created_at'],
                    'layers': orchestration['layers']
                })
            
            return orchestrations
        except Exception as e:
            logger.error(f"Failed to list orchestrations: {e}")
            return []
    
    async def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel an orchestration"""
        try:
            if orchestration_id not in self.active_orchestrations:
                return False
            
            orchestration = self.active_orchestrations[orchestration_id]
            
            # Cancel workflow
            if orchestration['workflow_id']:
                await self.workflow_manager.cancel_workflow(orchestration['workflow_id'])
            
            # Close MCP sessions
            for session_id in orchestration['mcp_sessions']:
                await self.mcp_manager.close_session(session_id)
            
            # Cancel ControlFlow tasks
            if orchestration['controlflow_tasks']:
                for task in orchestration['controlflow_tasks']:
                    await self.controlflow_manager.cancel_task(task['id'])
            
            # Cancel Prefect flows
            if orchestration['prefect_flows']:
                for flow in orchestration['prefect_flows']:
                    await self.prefect_manager.cancel_flow(flow['id'])
            
            # TODO: Cancel ControlFlow and Prefect in step 3
            
            orchestration['status'] = 'cancelled'
            orchestration['cancelled_at'] = datetime.now().isoformat()
            
            logger.info(f"Cancelled orchestration: {orchestration_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel orchestration {orchestration_id}: {e}")
            return False
    
    async def get_layer_health(self) -> Dict[str, Any]:
        """Get health status of all orchestration layers"""
        try:
            health = {
                'overall_status': 'healthy',
                'layers': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Check workflow layer health
            if self.layer_status.get(OrchestrationLayer.WORKFLOW, False):
                workflows = await self.workflow_manager.list_workflows()
                health['layers']['workflow'] = {
                    'status': 'healthy',
                    'active_workflows': len(workflows)
                }
            else:
                health['layers']['workflow'] = {
                    'status': 'unavailable',
                    'message': 'Strands workflow tools not available'
                }
            
            # Check MCP layer health
            if self.layer_status.get(OrchestrationLayer.MCP, False):
                sessions = await self.mcp_manager.list_active_sessions()
                health['layers']['mcp'] = {
                    'status': 'healthy',
                    'active_sessions': len(sessions)
                }
            else:
                health['layers']['mcp'] = {
                    'status': 'unavailable',
                    'message': 'Strands MCP tools not available'
                }
            
            # Check ControlFlow layer health
            if self.layer_status.get(OrchestrationLayer.CONTROLFLOW, False):
                tasks = await self.controlflow_manager.list_tasks()
                health['layers']['controlflow'] = {
                    'status': 'healthy',
                    'active_tasks': len(tasks)
                }
            else:
                health['layers']['controlflow'] = {
                    'status': 'unavailable',
                    'message': 'Strands ControlFlow tools not available'
                }
            
            # Check Prefect layer health
            if self.layer_status.get(OrchestrationLayer.PREFECT, False):
                flows = await self.prefect_manager.list_flows()
                health['layers']['prefect'] = {
                    'status': 'healthy',
                    'active_flows': len(flows)
                }
            else:
                health['layers']['prefect'] = {
                    'status': 'unavailable',
                    'message': 'Strands Prefect tools not available'
                }
            
            # Determine overall status
            unhealthy_layers = [layer for layer, info in health['layers'].items() 
                             if info['status'] not in ['healthy', 'pending']]
            if unhealthy_layers:
                health['overall_status'] = 'degraded'
                health['unhealthy_layers'] = unhealthy_layers
            
            return health
            
        except Exception as e:
            logger.error(f"Failed to get layer health: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
