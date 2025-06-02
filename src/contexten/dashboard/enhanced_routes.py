"""
Enhanced Dashboard Routes

Additional API routes for comprehensive flow management, project tracking,
and system monitoring in the contexten dashboard.
"""

import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from .flow_manager import flow_manager, FlowStatus, FlowPriority
from .project_manager import project_manager, ProjectStatus, ProjectHealth, RequirementStatus

logger = logging.getLogger(__name__)


def setup_enhanced_routes(app, agents=None, monitor=None, orchestrator=None):
    """Setup enhanced dashboard routes."""
    
    # Flow Management Routes
    @app.get("/api/flows")
    async def get_flows(status: str = None, project_id: str = None):
        """Get flows with optional filtering."""
        try:
            status_filter = FlowStatus(status) if status else None
            flows = flow_manager.list_flows(status=status_filter, project_id=project_id)
            return {
                "flows": [
                    {
                        "id": flow.id,
                        "name": flow.name,
                        "status": flow.status.value,
                        "progress": flow.progress,
                        "created_at": flow.created_at.isoformat(),
                        "template_id": flow.template_id,
                        "project_id": flow.project_id,
                        "priority": flow.priority.value,
                        "current_stage": flow.current_stage
                    }
                    for flow in flows
                ]
            }
        except Exception as e:
            logger.error(f"Error getting flows: {e}")
            return {"error": str(e)}
    
    @app.post("/api/flows/create")
    async def create_flow(flow_data: dict):
        """Create a new flow execution."""
        try:
            template_id = flow_data.get("template_id")
            if not template_id:
                raise HTTPException(status_code=400, detail="template_id is required")
            
            parameters = flow_data.get("parameters", {})
            name = flow_data.get("name")
            priority = FlowPriority(flow_data.get("priority", "normal"))
            project_id = flow_data.get("project_id")
            created_by = flow_data.get("created_by")
            
            flow = await flow_manager.create_flow(
                template_id=template_id,
                parameters=parameters,
                name=name,
                priority=priority,
                project_id=project_id,
                created_by=created_by
            )
            
            if flow:
                return {
                    "success": True,
                    "flow_id": flow.id,
                    "flow": {
                        "id": flow.id,
                        "name": flow.name,
                        "status": flow.status.value,
                        "template_id": flow.template_id,
                        "priority": flow.priority.value
                    }
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to create flow")
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating flow: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/flows/{flow_id}/start")
    async def start_flow(flow_id: str):
        """Start a flow execution."""
        try:
            success = await flow_manager.start_flow(flow_id)
            if success:
                return {"success": True, "message": f"Flow {flow_id} started"}
            else:
                raise HTTPException(status_code=400, detail="Failed to start flow")
        except Exception as e:
            logger.error(f"Error starting flow {flow_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/flows/{flow_id}")
    async def get_flow_details(flow_id: str):
        """Get detailed flow information."""
        try:
            flow = flow_manager.get_flow(flow_id)
            if flow:
                return {
                    "flow": {
                        "id": flow.id,
                        "name": flow.name,
                        "status": flow.status.value,
                        "priority": flow.priority.value,
                        "progress": flow.progress,
                        "current_stage": flow.current_stage,
                        "parameters": flow.parameters,
                        "template_id": flow.template_id,
                        "project_id": flow.project_id,
                        "created_by": flow.created_by,
                        "created_at": flow.created_at.isoformat(),
                        "started_at": flow.started_at.isoformat() if flow.started_at else None,
                        "completed_at": flow.completed_at.isoformat() if flow.completed_at else None,
                        "logs": flow.logs[-20:],  # Last 20 log entries
                        "error_message": flow.error_message,
                        "result": flow.result
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Flow not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting flow details: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/flows/{flow_id}/stop")
    async def stop_flow(flow_id: str):
        """Stop a running flow."""
        try:
            success = await flow_manager.stop_flow(flow_id)
            if success:
                return {"success": True, "message": f"Flow {flow_id} stopped"}
            else:
                raise HTTPException(status_code=400, detail="Failed to stop flow")
        except Exception as e:
            logger.error(f"Error stopping flow {flow_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Flow Templates Routes
    @app.get("/api/flow-templates")
    async def get_flow_templates(category: str = None):
        """Get available flow templates."""
        try:
            templates = flow_manager.template_manager.list_templates(category=category)
            return {
                "templates": [
                    {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "workflow_type": template.workflow_type,
                        "estimated_duration": template.estimated_duration,
                        "parameters": [
                            {
                                "name": param.name,
                                "type": param.type,
                                "description": param.description,
                                "required": param.required,
                                "default": param.default,
                                "options": param.options,
                                "validation_rules": param.validation_rules
                            }
                            for param in template.parameters
                        ],
                        "tags": template.tags,
                        "dependencies": template.dependencies,
                        "created_at": template.created_at.isoformat(),
                        "updated_at": template.updated_at.isoformat()
                    }
                    for template in templates
                ]
            }
        except Exception as e:
            logger.error(f"Error getting flow templates: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/flow-templates/{template_id}")
    async def get_flow_template(template_id: str):
        """Get a specific flow template."""
        try:
            template = flow_manager.template_manager.get_template(template_id)
            if template:
                return {
                    "template": {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "workflow_type": template.workflow_type,
                        "estimated_duration": template.estimated_duration,
                        "parameters": [
                            {
                                "name": param.name,
                                "type": param.type,
                                "description": param.description,
                                "required": param.required,
                                "default": param.default,
                                "options": param.options,
                                "validation_rules": param.validation_rules
                            }
                            for param in template.parameters
                        ],
                        "tags": template.tags,
                        "dependencies": template.dependencies
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Template not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting flow template: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Project Management Routes
    @app.get("/api/projects/pinned")
    async def get_pinned_projects(status: str = None, health: str = None):
        """Get all pinned projects."""
        try:
            status_filter = ProjectStatus(status) if status else None
            health_filter = ProjectHealth(health) if health else None
            projects = project_manager.list_projects(status=status_filter, health=health_filter)
            
            return {
                "projects": [
                    {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "repository_url": project.repository_url,
                        "status": project.status.value,
                        "health": project.health.value,
                        "owner": project.owner,
                        "team_members": project.team_members,
                        "tags": project.tags,
                        "pinned_at": project.pinned_at.isoformat(),
                        "pinned_by": project.pinned_by,
                        "last_activity": project.last_activity.isoformat() if project.last_activity else None,
                        "requirements_count": len(project.requirements),
                        "flow_configurations_count": len(project.flow_configurations),
                        "github_repo_id": project.github_repo_id,
                        "linear_project_id": project.linear_project_id,
                        "slack_channel_id": project.slack_channel_id
                    }
                    for project in projects
                ]
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting pinned projects: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/projects/pin")
    async def pin_project(project_data: dict):
        """Pin a new project."""
        try:
            required_fields = ["name", "repository_url", "owner"]
            for field in required_fields:
                if field not in project_data:
                    raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
            
            pinned_by = project_data.get("pinned_by", "system")
            project = await project_manager.pin_project(project_data, pinned_by)
            
            if project:
                return {
                    "success": True,
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "status": project.status.value,
                        "health": project.health.value,
                        "pinned_at": project.pinned_at.isoformat()
                    }
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to pin project")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error pinning project: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/projects/{project_id}/pin")
    async def unpin_project(project_id: str):
        """Unpin a project."""
        try:
            success = await project_manager.unpin_project(project_id)
            if success:
                return {"success": True, "message": f"Project {project_id} unpinned"}
            else:
                raise HTTPException(status_code=404, detail="Project not found or not pinned")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error unpinning project: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}")
    async def get_project_details(project_id: str):
        """Get detailed project information."""
        try:
            project = project_manager.get_project(project_id)
            if project:
                return {
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "repository_url": project.repository_url,
                        "status": project.status.value,
                        "health": project.health.value,
                        "owner": project.owner,
                        "team_members": project.team_members,
                        "tags": project.tags,
                        "requirements": [
                            {
                                "id": req.id,
                                "title": req.title,
                                "status": req.status.value,
                                "priority": req.priority,
                                "category": req.category
                            }
                            for req in project.requirements
                        ],
                        "metrics": {
                            "code_quality_score": project.metrics.code_quality_score,
                            "test_coverage": project.metrics.test_coverage,
                            "bug_count": project.metrics.bug_count,
                            "open_issues": project.metrics.open_issues,
                            "closed_issues": project.metrics.closed_issues,
                            "active_prs": project.metrics.active_prs,
                            "deployment_frequency": project.metrics.deployment_frequency,
                            "lead_time": project.metrics.lead_time,
                            "mttr": project.metrics.mttr,
                            "change_failure_rate": project.metrics.change_failure_rate,
                            "uptime_percentage": project.metrics.uptime_percentage
                        },
                        "flow_configurations": list(project.flow_configurations.keys()),
                        "notification_preferences": project.notification_preferences,
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat(),
                        "last_activity": project.last_activity.isoformat() if project.last_activity else None,
                        "github_repo_id": project.github_repo_id,
                        "linear_project_id": project.linear_project_id,
                        "slack_channel_id": project.slack_channel_id
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}/dashboard")
    async def get_project_dashboard(project_id: str):
        """Get comprehensive project dashboard data."""
        try:
            dashboard_data = await project_manager.get_project_dashboard_data(project_id)
            if "error" in dashboard_data:
                if dashboard_data["error"] == "Project not found":
                    raise HTTPException(status_code=404, detail="Project not found")
                else:
                    raise HTTPException(status_code=500, detail=dashboard_data["error"])
            return dashboard_data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting project dashboard: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/projects/{project_id}")
    async def update_project(project_id: str, updates: dict):
        """Update a project."""
        try:
            success = await project_manager.update_project(project_id, updates)
            if success:
                return {"success": True, "message": f"Project {project_id} updated"}
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Requirements Management Routes
    @app.post("/api/projects/{project_id}/requirements")
    async def add_requirement(project_id: str, requirement_data: dict):
        """Add a requirement to a project."""
        try:
            required_fields = ["title"]
            for field in required_fields:
                if field not in requirement_data:
                    raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
            
            requirement = await project_manager.add_requirement(project_id, requirement_data)
            if requirement:
                return {
                    "success": True,
                    "requirement": {
                        "id": requirement.id,
                        "title": requirement.title,
                        "description": requirement.description,
                        "status": requirement.status.value,
                        "priority": requirement.priority,
                        "category": requirement.category,
                        "created_at": requirement.created_at.isoformat()
                    }
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to add requirement")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding requirement: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}/requirements")
    async def get_requirements(project_id: str, status: str = None):
        """Get requirements for a project."""
        try:
            status_filter = RequirementStatus(status) if status else None
            requirements = await project_manager.requirements_manager.get_requirements(
                project_id, status=status_filter
            )
            
            return {
                "requirements": [
                    {
                        "id": req.id,
                        "title": req.title,
                        "description": req.description,
                        "status": req.status.value,
                        "priority": req.priority,
                        "category": req.category,
                        "assignee": req.assignee,
                        "estimated_hours": req.estimated_hours,
                        "actual_hours": req.actual_hours,
                        "dependencies": req.dependencies,
                        "tags": req.tags,
                        "created_at": req.created_at.isoformat(),
                        "updated_at": req.updated_at.isoformat(),
                        "due_date": req.due_date.isoformat() if req.due_date else None,
                        "completed_at": req.completed_at.isoformat() if req.completed_at else None,
                        "linear_issue_id": req.linear_issue_id,
                        "github_issue_id": req.github_issue_id
                    }
                    for req in requirements
                ]
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting requirements: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}/requirements/stats")
    async def get_requirement_stats(project_id: str):
        """Get requirement statistics for a project."""
        try:
            stats = await project_manager.requirements_manager.get_requirement_stats(project_id)
            return {"stats": stats}
        except Exception as e:
            logger.error(f"Error getting requirement stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # System Health and Monitoring Routes
    @app.get("/api/system/health")
    async def get_system_health():
        """Get system health status."""
        try:
            if monitor:
                health_data = await monitor.get_health_status()
                return health_data
            else:
                return {
                    "status": "unknown",
                    "message": "System monitor not available",
                    "components": {
                        "flow_manager": "active",
                        "project_manager": "active",
                        "dashboard": "active"
                    }
                }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"status": "error", "message": str(e)}
    
    @app.get("/api/system/metrics")
    async def get_system_metrics():
        """Get system performance metrics."""
        try:
            if monitor:
                metrics = await monitor.get_metrics()
                return {"metrics": metrics}
            else:
                return {
                    "metrics": {
                        "active_flows": len(flow_manager.executions),
                        "pinned_projects": len(project_manager.pinned_projects),
                        "flow_templates": len(flow_manager.template_manager.templates)
                    },
                    "message": "Limited metrics available - monitor not configured"
                }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"metrics": {}, "error": str(e)}
    
    # WebSocket endpoint for real-time flow updates
    @app.websocket("/ws/flows/{flow_id}")
    async def flow_websocket(websocket: WebSocket, flow_id: str):
        """WebSocket endpoint for real-time flow updates."""
        await websocket.accept()
        await flow_manager.progress_tracker.add_websocket_connection(flow_id, websocket)
        
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                try:
                    data = await websocket.receive_text()
                    # Echo back for heartbeat
                    await websocket.send_json({"type": "heartbeat", "timestamp": data})
                except WebSocketDisconnect:
                    break
        except Exception as e:
            logger.error(f"WebSocket error for flow {flow_id}: {e}")
        finally:
            await flow_manager.progress_tracker.remove_websocket_connection(flow_id, websocket)
    
    # Agent Execution Routes
    @app.post("/api/agents/{agent_type}/execute")
    async def execute_agent_task(agent_type: str, task_data: dict):
        """Execute a task using a specific agent."""
        try:
            if not agents or agent_type not in agents:
                raise HTTPException(status_code=404, detail=f"Agent {agent_type} not available")
            
            agent = agents[agent_type]
            
            # Handle different agent types
            if agent_type == "codegen" and hasattr(agent, 'run'):
                prompt = task_data.get("prompt")
                if not prompt:
                    raise HTTPException(status_code=400, detail="Prompt is required for codegen agent")
                
                task = agent.run(prompt=prompt)
                return {
                    "success": True,
                    "task_id": task.id if hasattr(task, 'id') else None,
                    "status": task.status if hasattr(task, 'status') else "submitted",
                    "agent": agent_type
                }
            elif agent_type in ["chat", "code"]:
                # Handle chat and code agents
                message = task_data.get("message") or task_data.get("prompt")
                if not message:
                    raise HTTPException(status_code=400, detail="Message or prompt is required")
                
                # Execute agent task (implementation depends on agent interface)
                result = {"message": f"Task executed by {agent_type} agent", "input": message}
                return {
                    "success": True,
                    "result": result,
                    "agent": agent_type
                }
            else:
                # Generic agent execution
                return {
                    "success": True,
                    "result": f"Task executed by {agent_type} agent",
                    "agent": agent_type,
                    "task_data": task_data
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing agent task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Dashboard Statistics Route
    @app.get("/api/dashboard/stats")
    async def get_dashboard_stats():
        """Get overall dashboard statistics."""
        try:
            # Flow statistics
            all_flows = flow_manager.list_flows()
            flow_stats = {
                "total": len(all_flows),
                "running": len([f for f in all_flows if f.status == FlowStatus.RUNNING]),
                "completed": len([f for f in all_flows if f.status == FlowStatus.COMPLETED]),
                "failed": len([f for f in all_flows if f.status == FlowStatus.FAILED]),
                "pending": len([f for f in all_flows if f.status == FlowStatus.PENDING])
            }
            
            # Project statistics
            all_projects = project_manager.list_projects()
            project_stats = {
                "total": len(all_projects),
                "active": len([p for p in all_projects if p.status == ProjectStatus.ACTIVE]),
                "healthy": len([p for p in all_projects if p.health in [ProjectHealth.EXCELLENT, ProjectHealth.GOOD]]),
                "warning": len([p for p in all_projects if p.health == ProjectHealth.WARNING]),
                "critical": len([p for p in all_projects if p.health == ProjectHealth.CRITICAL])
            }
            
            # Template statistics
            templates = flow_manager.template_manager.list_templates()
            template_stats = {
                "total": len(templates),
                "categories": len(set(t.category for t in templates))
            }
            
            return {
                "flows": flow_stats,
                "projects": project_stats,
                "templates": template_stats,
                "agents": {
                    "available": list(agents.keys()) if agents else [],
                    "count": len(agents) if agents else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    logger.info("Enhanced dashboard routes configured successfully")

