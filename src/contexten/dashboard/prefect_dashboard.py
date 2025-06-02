"""
Prefect Dashboard Integration for Contexten

This module provides a comprehensive web interface for managing Prefect workflows,
monitoring system health, and controlling autonomous CI/CD operations through
the contexten dashboard.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..orchestration import (
    PrefectOrchestrator,
    AutonomousWorkflowType,
    OrchestrationConfig,
    get_workflow_metadata,
    get_workflows_by_category,
    WorkflowCategory,
    WorkflowPriority
)

logger = logging.getLogger(__name__)


class PrefectDashboardManager:
    """
    Comprehensive Prefect dashboard manager providing full orchestration
    functionality through a web interface.
    """
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.orchestrator: Optional[PrefectOrchestrator] = None
        self.router = APIRouter(prefix="/prefect", tags=["prefect"])
        self.templates = Jinja2Templates(directory="src/contexten/dashboard/templates")
        self._setup_routes()
        
    async def initialize(self) -> None:
        """Initialize the Prefect orchestrator"""
        try:
            self.orchestrator = PrefectOrchestrator(self.config)
            await self.orchestrator.initialize()
            logger.info("Prefect Dashboard Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Prefect Dashboard Manager: {e}")
            raise
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes for Prefect dashboard"""
        
        # Dashboard pages
        self.router.add_api_route("/", self.dashboard_home, methods=["GET"], response_class=HTMLResponse)
        self.router.add_api_route("/workflows", self.workflows_page, methods=["GET"], response_class=HTMLResponse)
        self.router.add_api_route("/monitoring", self.monitoring_page, methods=["GET"], response_class=HTMLResponse)
        self.router.add_api_route("/configuration", self.configuration_page, methods=["GET"], response_class=HTMLResponse)
        
        # API endpoints
        self.router.add_api_route("/api/status", self.get_system_status, methods=["GET"])
        self.router.add_api_route("/api/workflows", self.get_workflows, methods=["GET"])
        self.router.add_api_route("/api/workflows/trigger", self.trigger_workflow, methods=["POST"])
        self.router.add_api_route("/api/workflows/{workflow_id}/status", self.get_workflow_status, methods=["GET"])
        self.router.add_api_route("/api/workflows/{workflow_id}/cancel", self.cancel_workflow, methods=["POST"])
        self.router.add_api_route("/api/workflows/history", self.get_workflow_history, methods=["GET"])
        self.router.add_api_route("/api/metrics", self.get_metrics, methods=["GET"])
        self.router.add_api_route("/api/health", self.get_health_status, methods=["GET"])
        self.router.add_api_route("/api/components", self.get_component_analysis, methods=["GET"])
        self.router.add_api_route("/api/components/analyze", self.trigger_component_analysis, methods=["POST"])
        self.router.add_api_route("/api/configuration", self.get_configuration, methods=["GET"])
        self.router.add_api_route("/api/configuration", self.update_configuration, methods=["POST"])
        
        # Real-time endpoints
        self.router.add_api_route("/api/live/metrics", self.get_live_metrics, methods=["GET"])
        self.router.add_api_route("/api/live/logs", self.get_live_logs, methods=["GET"])
        
        # Bulk operations
        self.router.add_api_route("/api/workflows/bulk/trigger", self.bulk_trigger_workflows, methods=["POST"])
        self.router.add_api_route("/api/workflows/bulk/cancel", self.bulk_cancel_workflows, methods=["POST"])
    
    # Dashboard Pages
    
    async def dashboard_home(self, request: Request) -> HTMLResponse:
        """Main Prefect dashboard page"""
        try:
            # Get system overview data
            status = await self.get_system_status_data()
            metrics = await self.get_metrics_data()
            recent_workflows = await self.get_recent_workflows_data(limit=10)
            
            context = {
                "request": request,
                "title": "Prefect Orchestration Dashboard",
                "status": status,
                "metrics": metrics,
                "recent_workflows": recent_workflows,
                "workflow_categories": [cat.value for cat in WorkflowCategory],
                "workflow_types": [wf.value for wf in AutonomousWorkflowType]
            }
            
            return self.templates.TemplateResponse("prefect_dashboard.html", context)
            
        except Exception as e:
            logger.error(f"Error loading dashboard home: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def workflows_page(self, request: Request) -> HTMLResponse:
        """Workflows management page"""
        try:
            workflows = await self.get_workflows_data()
            workflow_types = []
            
            for workflow_type in AutonomousWorkflowType:
                metadata = get_workflow_metadata(workflow_type)
                workflow_types.append({
                    "type": workflow_type.value,
                    "name": workflow_type.value.replace("_", " ").title(),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", WorkflowCategory.SYSTEM).value,
                    "priority": metadata.get("priority", WorkflowPriority.NORMAL).value,
                    "estimated_duration": metadata.get("estimated_duration_minutes", 15),
                    "requires_approval": metadata.get("requires_human_approval", False)
                })
            
            context = {
                "request": request,
                "title": "Workflow Management",
                "workflows": workflows,
                "workflow_types": workflow_types,
                "categories": [cat.value for cat in WorkflowCategory]
            }
            
            return self.templates.TemplateResponse("prefect_workflows.html", context)
            
        except Exception as e:
            logger.error(f"Error loading workflows page: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def monitoring_page(self, request: Request) -> HTMLResponse:
        """System monitoring page"""
        try:
            health_status = await self.get_health_status_data()
            metrics = await self.get_metrics_data()
            
            context = {
                "request": request,
                "title": "System Monitoring",
                "health_status": health_status,
                "metrics": metrics,
                "alert_thresholds": self.config.alert_thresholds
            }
            
            return self.templates.TemplateResponse("prefect_monitoring.html", context)
            
        except Exception as e:
            logger.error(f"Error loading monitoring page: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def configuration_page(self, request: Request) -> HTMLResponse:
        """Configuration management page"""
        try:
            config_data = await self.get_configuration_data()
            
            context = {
                "request": request,
                "title": "Configuration",
                "configuration": config_data,
                "integrations": self.config.get_enabled_integrations()
            }
            
            return self.templates.TemplateResponse("prefect_configuration.html", context)
            
        except Exception as e:
            logger.error(f"Error loading configuration page: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # API Endpoints
    
    async def get_system_status(self) -> JSONResponse:
        """Get comprehensive system status"""
        try:
            status = await self.get_system_status_data()
            return JSONResponse(content=status)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_workflows(self) -> JSONResponse:
        """Get all workflows"""
        try:
            workflows = await self.get_workflows_data()
            return JSONResponse(content=workflows)
        except Exception as e:
            logger.error(f"Error getting workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def trigger_workflow(self, request: Request) -> JSONResponse:
        """Trigger a workflow"""
        try:
            data = await request.json()
            workflow_type = AutonomousWorkflowType(data["workflow_type"])
            parameters = data.get("parameters", {})
            priority = data.get("priority", 5)
            
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            run_id = await self.orchestrator.trigger_workflow(
                workflow_type, parameters, priority
            )
            
            return JSONResponse(content={
                "success": True,
                "run_id": run_id,
                "workflow_type": workflow_type.value,
                "message": f"Workflow {workflow_type.value} triggered successfully"
            })
            
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_workflow_status(self, workflow_id: str) -> JSONResponse:
        """Get workflow status"""
        try:
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            status = await self.orchestrator.get_workflow_status(workflow_id)
            
            if not status:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return JSONResponse(content={
                "id": str(status.id),
                "name": status.name,
                "state": status.state_type.value,
                "created_time": status.created_time.isoformat() if status.created_time else None,
                "start_time": status.start_time.isoformat() if status.start_time else None,
                "end_time": status.end_time.isoformat() if status.end_time else None,
                "total_run_time": status.total_run_time.total_seconds() if status.total_run_time else None,
                "parameters": status.parameters
            })
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def cancel_workflow(self, workflow_id: str) -> JSONResponse:
        """Cancel a workflow"""
        try:
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            success = await self.orchestrator.cancel_workflow(workflow_id)
            
            return JSONResponse(content={
                "success": success,
                "message": f"Workflow {workflow_id} {'cancelled' if success else 'could not be cancelled'}"
            })
            
        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_workflow_history(self, limit: int = 50, workflow_type: Optional[str] = None) -> JSONResponse:
        """Get workflow execution history"""
        try:
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            workflow_enum = None
            if workflow_type:
                workflow_enum = AutonomousWorkflowType(workflow_type)
            
            history = await self.orchestrator.get_workflow_history(workflow_enum, limit)
            
            history_data = []
            for run in history:
                history_data.append({
                    "id": str(run.id),
                    "name": run.name,
                    "state": run.state_type.value,
                    "created_time": run.created_time.isoformat() if run.created_time else None,
                    "start_time": run.start_time.isoformat() if run.start_time else None,
                    "end_time": run.end_time.isoformat() if run.end_time else None,
                    "total_run_time": run.total_run_time.total_seconds() if run.total_run_time else None,
                    "parameters": run.parameters
                })
            
            return JSONResponse(content=history_data)
            
        except Exception as e:
            logger.error(f"Error getting workflow history: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_metrics(self) -> JSONResponse:
        """Get system metrics"""
        try:
            metrics = await self.get_metrics_data()
            return JSONResponse(content=metrics)
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_health_status(self) -> JSONResponse:
        """Get health status"""
        try:
            health = await self.get_health_status_data()
            return JSONResponse(content=health)
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_component_analysis(self) -> JSONResponse:
        """Get component analysis data"""
        try:
            # Get available components for analysis
            components = [
                "contexten/agents",
                "contexten/orchestration", 
                "graph_sitter/gscli",
                "graph_sitter/git",
                "graph_sitter/visualizations",
                "graph_sitter/ai",
                "graph_sitter/codebase",
                "codemods",
                "build_system",
                "testing"
            ]
            
            # Get recent component analysis results
            recent_analyses = await self.get_recent_component_analyses()
            
            return JSONResponse(content={
                "available_components": components,
                "recent_analyses": recent_analyses
            })
            
        except Exception as e:
            logger.error(f"Error getting component analysis: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def trigger_component_analysis(self, request: Request) -> JSONResponse:
        """Trigger component analysis"""
        try:
            data = await request.json()
            component = data["component"]
            linear_issue_id = data.get("linear_issue_id")
            
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            run_id = await self.orchestrator.trigger_component_analysis(
                component, linear_issue_id
            )
            
            return JSONResponse(content={
                "success": True,
                "run_id": run_id,
                "component": component,
                "message": f"Component analysis for {component} triggered successfully"
            })
            
        except Exception as e:
            logger.error(f"Error triggering component analysis: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_configuration(self) -> JSONResponse:
        """Get configuration"""
        try:
            config_data = await self.get_configuration_data()
            return JSONResponse(content=config_data)
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_configuration(self, request: Request) -> JSONResponse:
        """Update configuration"""
        try:
            data = await request.json()
            
            # Update configuration (in a real implementation, this would persist changes)
            updated_fields = []
            
            if "max_concurrent_workflows" in data:
                self.config.max_concurrent_workflows = data["max_concurrent_workflows"]
                updated_fields.append("max_concurrent_workflows")
            
            if "auto_recovery_enabled" in data:
                self.config.auto_recovery_enabled = data["auto_recovery_enabled"]
                updated_fields.append("auto_recovery_enabled")
            
            if "monitoring_enabled" in data:
                self.config.monitoring_enabled = data["monitoring_enabled"]
                updated_fields.append("monitoring_enabled")
            
            if "alert_thresholds" in data:
                self.config.alert_thresholds.update(data["alert_thresholds"])
                updated_fields.append("alert_thresholds")
            
            return JSONResponse(content={
                "success": True,
                "updated_fields": updated_fields,
                "message": "Configuration updated successfully"
            })
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_live_metrics(self) -> JSONResponse:
        """Get live metrics for real-time updates"""
        try:
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            metrics = await self.orchestrator.get_metrics()
            
            # Add timestamp for real-time updates
            metrics["timestamp"] = datetime.now().isoformat()
            
            return JSONResponse(content=metrics)
            
        except Exception as e:
            logger.error(f"Error getting live metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_live_logs(self, limit: int = 100) -> JSONResponse:
        """Get live logs"""
        try:
            # In a real implementation, this would stream logs from the orchestrator
            logs = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "message": "System operating normally",
                    "component": "orchestrator"
                }
            ]
            
            return JSONResponse(content=logs)
            
        except Exception as e:
            logger.error(f"Error getting live logs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def bulk_trigger_workflows(self, request: Request) -> JSONResponse:
        """Trigger multiple workflows"""
        try:
            data = await request.json()
            workflow_requests = data["workflows"]
            
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            results = []
            for workflow_request in workflow_requests:
                try:
                    workflow_type = AutonomousWorkflowType(workflow_request["workflow_type"])
                    parameters = workflow_request.get("parameters", {})
                    priority = workflow_request.get("priority", 5)
                    
                    run_id = await self.orchestrator.trigger_workflow(
                        workflow_type, parameters, priority
                    )
                    
                    results.append({
                        "workflow_type": workflow_type.value,
                        "run_id": run_id,
                        "success": True
                    })
                    
                except Exception as e:
                    results.append({
                        "workflow_type": workflow_request.get("workflow_type", "unknown"),
                        "error": str(e),
                        "success": False
                    })
            
            return JSONResponse(content={
                "results": results,
                "total": len(workflow_requests),
                "successful": len([r for r in results if r["success"]]),
                "failed": len([r for r in results if not r["success"]])
            })
            
        except Exception as e:
            logger.error(f"Error bulk triggering workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def bulk_cancel_workflows(self, request: Request) -> JSONResponse:
        """Cancel multiple workflows"""
        try:
            data = await request.json()
            workflow_ids = data["workflow_ids"]
            
            if not self.orchestrator:
                raise HTTPException(status_code=503, detail="Orchestrator not initialized")
            
            results = []
            for workflow_id in workflow_ids:
                try:
                    success = await self.orchestrator.cancel_workflow(workflow_id)
                    results.append({
                        "workflow_id": workflow_id,
                        "success": success
                    })
                except Exception as e:
                    results.append({
                        "workflow_id": workflow_id,
                        "error": str(e),
                        "success": False
                    })
            
            return JSONResponse(content={
                "results": results,
                "total": len(workflow_ids),
                "successful": len([r for r in results if r["success"]]),
                "failed": len([r for r in results if not r["success"]])
            })
            
        except Exception as e:
            logger.error(f"Error bulk cancelling workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Helper methods
    
    async def get_system_status_data(self) -> Dict[str, Any]:
        """Get system status data"""
        if not self.orchestrator:
            return {"status": "not_initialized", "message": "Orchestrator not initialized"}
        
        try:
            metrics = await self.orchestrator.get_metrics()
            health = await self.orchestrator.autonomous_orchestrator.monitor.check_system_health()
            
            return {
                "status": "operational",
                "health_score": health.get("health_score", 0),
                "active_workflows": metrics.get("active_workflows", 0),
                "total_workflows": metrics.get("total_workflows_executed", 0),
                "success_rate": metrics.get("success_rate_percent", 0),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system status data: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_workflows_data(self) -> List[Dict[str, Any]]:
        """Get workflows data"""
        if not self.orchestrator:
            return []
        
        try:
            active_workflows = await self.orchestrator.list_active_workflows()
            
            workflows = []
            for workflow in active_workflows:
                workflows.append({
                    "id": str(workflow.id),
                    "name": workflow.name,
                    "state": workflow.state_type.value,
                    "created_time": workflow.created_time.isoformat() if workflow.created_time else None,
                    "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                    "parameters": workflow.parameters
                })
            
            return workflows
        except Exception as e:
            logger.error(f"Error getting workflows data: {e}")
            return []
    
    async def get_recent_workflows_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflows data"""
        if not self.orchestrator:
            return []
        
        try:
            history = await self.orchestrator.get_workflow_history(limit=limit)
            
            workflows = []
            for workflow in history:
                workflows.append({
                    "id": str(workflow.id),
                    "name": workflow.name,
                    "state": workflow.state_type.value,
                    "created_time": workflow.created_time.isoformat() if workflow.created_time else None,
                    "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
                    "total_run_time": workflow.total_run_time.total_seconds() if workflow.total_run_time else None
                })
            
            return workflows
        except Exception as e:
            logger.error(f"Error getting recent workflows data: {e}")
            return []
    
    async def get_metrics_data(self) -> Dict[str, Any]:
        """Get metrics data"""
        if not self.orchestrator:
            return {}
        
        try:
            return await self.orchestrator.get_metrics()
        except Exception as e:
            logger.error(f"Error getting metrics data: {e}")
            return {}
    
    async def get_health_status_data(self) -> Dict[str, Any]:
        """Get health status data"""
        if not self.orchestrator:
            return {"status": "unknown", "components": {}}
        
        try:
            return await self.orchestrator.autonomous_orchestrator.monitor.check_system_health()
        except Exception as e:
            logger.error(f"Error getting health status data: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_configuration_data(self) -> Dict[str, Any]:
        """Get configuration data"""
        return {
            "max_concurrent_workflows": self.config.max_concurrent_workflows,
            "auto_recovery_enabled": self.config.auto_recovery_enabled,
            "monitoring_enabled": self.config.monitoring_enabled,
            "health_check_interval_minutes": self.config.health_check_interval_minutes,
            "alert_thresholds": self.config.alert_thresholds,
            "enabled_integrations": self.config.get_enabled_integrations(),
            "workflow_retry_attempts": self.config.workflow_retry_attempts
        }
    
    async def get_recent_component_analyses(self) -> List[Dict[str, Any]]:
        """Get recent component analyses"""
        # In a real implementation, this would query the database for recent analyses
        return [
            {
                "component": "contexten/agents",
                "status": "completed",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "issues_found": 3,
                "linear_issue_id": "ZAM-1084"
            },
            {
                "component": "graph_sitter/gscli",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "linear_issue_id": "ZAM-1085"
            }
        ]
    
    async def shutdown(self) -> None:
        """Shutdown the dashboard manager"""
        if self.orchestrator:
            await self.orchestrator.shutdown()
        logger.info("Prefect Dashboard Manager shutdown complete")

