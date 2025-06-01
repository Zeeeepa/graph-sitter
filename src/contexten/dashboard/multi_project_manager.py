"""
Multi-Project Manager

This module provides comprehensive multi-project management capabilities for the
contexten dashboard, including project configuration, requirement tracking,
CI/CD flow orchestration, and cross-project analysis.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiofiles

from codegen import Agent as CodegenAgent
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ProjectType(str, Enum):
    """Project type enumeration"""
    GITHUB_REPO = "github_repo"
    LOCAL_DIRECTORY = "local_directory"
    REMOTE_GIT = "remote_git"
    DOCKER_PROJECT = "docker_project"


class FlowStatus(str, Enum):
    """CI/CD Flow status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ExecutionStatus(str, Enum):
    """Flow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProjectConfig:
    """Project configuration"""
    id: str
    name: str
    type: ProjectType
    source_url: str
    branch: str = "main"
    description: str = ""
    tags: List[str] = None
    settings: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ProjectRequirement:
    """Project requirement/task"""
    id: str
    project_id: str
    title: str
    description: str = ""
    priority: int = 1
    status: str = "open"
    labels: List[str] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CICDFlow:
    """CI/CD Flow configuration"""
    id: str
    project_id: str
    name: str
    description: str = ""
    workflow_id: str = ""
    status: FlowStatus = FlowStatus.IDLE
    trigger_conditions: Dict[str, Any] = None
    auto_start: bool = False
    schedule: Optional[str] = None
    settings: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        if self.trigger_conditions is None:
            self.trigger_conditions = {}
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class FlowExecution:
    """Flow execution instance"""
    id: str
    flow_id: str
    project_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_step: str = ""
    triggered_by: str = ""
    error: Optional[str] = None
    logs: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []
        if self.metadata is None:
            self.metadata = {}


class MultiProjectManager:
    """
    Comprehensive multi-project management system with CI/CD orchestration,
    requirement tracking, and cross-project analysis capabilities.
    """
    
    def __init__(
        self,
        data_dir: str = "data/multi_project",
        codegen_org_id: Optional[str] = None,
        codegen_token: Optional[str] = None
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Codegen SDK integration
        self.codegen_org_id = codegen_org_id
        self.codegen_token = codegen_token
        self.codegen_agent: Optional[CodegenAgent] = None
        
        # Data storage
        self.projects: Dict[str, ProjectConfig] = {}
        self.requirements: Dict[str, List[ProjectRequirement]] = {}
        self.flows: Dict[str, List[CICDFlow]] = {}
        self.executions: Dict[str, FlowExecution] = {}
        
        # Active projects and flows
        self.active_projects: Set[str] = set()
        self.running_flows: Dict[str, FlowExecution] = {}
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._flow_scheduler_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "projects_count": 0,
            "active_projects": 0,
            "total_requirements": 0,
            "total_flows": 0,
            "running_flows": 0,
            "completed_executions": 0,
            "failed_executions": 0,
            "start_time": datetime.utcnow()
        }
    
    async def start(self) -> None:
        """Start the multi-project manager"""
        logger.info("Starting Multi-Project Manager...")
        
        # Initialize Codegen SDK if credentials are available
        if self.codegen_org_id and self.codegen_token:
            try:
                self.codegen_agent = CodegenAgent(
                    org_id=self.codegen_org_id,
                    token=self.codegen_token
                )
                logger.info("Codegen SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Codegen SDK: {e}")
        
        # Load persisted data
        await self._load_data()
        
        # Start background tasks
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._flow_scheduler_task = asyncio.create_task(self._flow_scheduler_loop())
        
        logger.info("Multi-Project Manager started successfully")
    
    async def stop(self) -> None:
        """Stop the multi-project manager"""
        logger.info("Stopping Multi-Project Manager...")
        
        # Cancel background tasks
        for task in [self._monitoring_task, self._flow_scheduler_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Save data
        await self._save_data()
        
        logger.info("Multi-Project Manager stopped")
    
    # Project Management
    async def add_project(self, project: ProjectConfig) -> bool:
        """Add a new project"""
        try:
            self.projects[project.id] = project
            self.requirements[project.id] = []
            self.flows[project.id] = []
            
            # Activate project by default
            self.active_projects.add(project.id)
            
            await self._save_data()
            self._update_stats()
            
            logger.info(f"Added project: {project.name} ({project.id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add project {project.id}: {e}")
            return False
    
    async def get_projects(self, active_only: bool = False) -> List[ProjectConfig]:
        """Get all projects"""
        projects = list(self.projects.values())
        if active_only:
            projects = [p for p in projects if p.id in self.active_projects]
        return projects
    
    async def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        """Get a specific project"""
        return self.projects.get(project_id)
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project configuration"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.utcnow()
        await self._save_data()
        return True
    
    async def remove_project(self, project_id: str) -> bool:
        """Remove a project"""
        if project_id not in self.projects:
            return False
        
        # Stop any running flows for this project
        for execution_id, execution in list(self.running_flows.items()):
            if execution.project_id == project_id:
                await self.stop_flow_execution(execution_id)
        
        # Remove project data
        del self.projects[project_id]
        del self.requirements[project_id]
        del self.flows[project_id]
        self.active_projects.discard(project_id)
        
        await self._save_data()
        self._update_stats()
        return True
    
    # Requirement Management
    async def add_requirement(self, requirement: ProjectRequirement) -> bool:
        """Add a requirement to a project"""
        if requirement.project_id not in self.projects:
            return False
        
        self.requirements[requirement.project_id].append(requirement)
        await self._save_data()
        self._update_stats()
        return True
    
    async def get_requirements(self, project_id: str) -> List[ProjectRequirement]:
        """Get requirements for a project"""
        return self.requirements.get(project_id, [])
    
    async def update_requirement(self, requirement_id: str, updates: Dict[str, Any]) -> bool:
        """Update a requirement"""
        for project_requirements in self.requirements.values():
            for req in project_requirements:
                if req.id == requirement_id:
                    for key, value in updates.items():
                        if hasattr(req, key):
                            setattr(req, key, value)
                    req.updated_at = datetime.utcnow()
                    await self._save_data()
                    return True
        return False
    
    # CI/CD Flow Management
    async def create_flow(self, flow: CICDFlow) -> bool:
        """Create a new CI/CD flow"""
        if flow.project_id not in self.projects:
            return False
        
        self.flows[flow.project_id].append(flow)
        await self._save_data()
        self._update_stats()
        return True
    
    async def get_flows(self, project_id: str) -> List[CICDFlow]:
        """Get flows for a project"""
        return self.flows.get(project_id, [])
    
    async def start_flow(self, flow_id: str, triggered_by: str = "system") -> Optional[str]:
        """Start a CI/CD flow execution"""
        # Find the flow
        flow = None
        for project_flows in self.flows.values():
            for f in project_flows:
                if f.id == flow_id:
                    flow = f
                    break
            if flow:
                break
        
        if not flow:
            logger.error(f"Flow {flow_id} not found")
            return None
        
        # Create execution
        execution = FlowExecution(
            id=str(uuid.uuid4()),
            flow_id=flow_id,
            project_id=flow.project_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by
        )
        
        self.executions[execution.id] = execution
        self.running_flows[execution.id] = execution
        
        # Update flow status
        flow.status = FlowStatus.RUNNING
        flow.last_run = datetime.utcnow()
        flow.run_count += 1
        
        # Start execution in background
        asyncio.create_task(self._execute_flow(execution))
        
        await self._save_data()
        self._update_stats()
        
        logger.info(f"Started flow execution: {execution.id}")
        return execution.id
    
    async def stop_flow_execution(self, execution_id: str) -> bool:
        """Stop a running flow execution"""
        if execution_id not in self.running_flows:
            return False
        
        execution = self.running_flows[execution_id]
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        
        # Remove from running flows
        del self.running_flows[execution_id]
        
        # Update flow status
        for project_flows in self.flows.values():
            for flow in project_flows:
                if flow.id == execution.flow_id:
                    flow.status = FlowStatus.IDLE
                    break
        
        await self._save_data()
        self._update_stats()
        return True
    
    async def get_flow_executions(self, flow_id: str, limit: int = 10) -> List[FlowExecution]:
        """Get execution history for a flow"""
        executions = [
            exec for exec in self.executions.values()
            if exec.flow_id == flow_id
        ]
        # Sort by start time, most recent first
        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]
    
    async def get_running_flows(self) -> Dict[str, FlowExecution]:
        """Get all currently running flows"""
        return self.running_flows.copy()
    
    # Analysis and Monitoring
    async def analyze_projects(self, project_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform multi-project analysis"""
        target_projects = project_ids or list(self.projects.keys())
        
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "projects_analyzed": len(target_projects),
            "summary": {},
            "cross_project_insights": {},
            "recommendations": []
        }
        
        # Basic project analysis
        for project_id in target_projects:
            if project_id not in self.projects:
                continue
            
            project = self.projects[project_id]
            requirements = self.requirements.get(project_id, [])
            flows = self.flows.get(project_id, [])
            
            project_analysis = {
                "project_name": project.name,
                "project_type": project.type.value,
                "requirements_count": len(requirements),
                "flows_count": len(flows),
                "active_flows": len([f for f in flows if f.status == FlowStatus.RUNNING]),
                "health_score": await self._calculate_project_health_score(project_id)
            }
            
            analysis["summary"][project_id] = project_analysis
        
        # Cross-project insights
        analysis["cross_project_insights"] = await self._generate_cross_project_insights(target_projects)
        
        # Generate recommendations
        analysis["recommendations"] = await self._generate_project_recommendations(target_projects)
        
        return analysis
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.stats["start_time"]).total_seconds(),
            "projects": {
                "total": len(self.projects),
                "active": len(self.active_projects),
                "types": self._get_project_type_distribution()
            },
            "requirements": {
                "total": sum(len(reqs) for reqs in self.requirements.values()),
                "by_status": self._get_requirement_status_distribution()
            },
            "flows": {
                "total": sum(len(flows) for flows in self.flows.values()),
                "running": len(self.running_flows),
                "by_status": self._get_flow_status_distribution()
            },
            "executions": {
                "total": len(self.executions),
                "completed": len([e for e in self.executions.values() if e.status == ExecutionStatus.COMPLETED]),
                "failed": len([e for e in self.executions.values() if e.status == ExecutionStatus.FAILED])
            },
            "codegen_integration": {
                "enabled": self.codegen_agent is not None,
                "org_id": self.codegen_org_id if self.codegen_agent else None
            }
        }
    
    # Private methods
    async def _execute_flow(self, execution: FlowExecution) -> None:
        """Execute a CI/CD flow"""
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.current_step = "Initializing"
            execution.progress = 0.1
            
            # Get flow configuration
            flow = None
            for project_flows in self.flows.values():
                for f in project_flows:
                    if f.id == execution.flow_id:
                        flow = f
                        break
                if flow:
                    break
            
            if not flow:
                raise Exception(f"Flow {execution.flow_id} not found")
            
            # Execute flow steps using Codegen SDK if available
            if self.codegen_agent and flow.workflow_id:
                execution.current_step = "Running Codegen workflow"
                execution.progress = 0.5
                
                # Use Codegen SDK to execute the workflow
                task = self.codegen_agent.run(
                    prompt=f"Execute workflow {flow.workflow_id} for project {execution.project_id}"
                )
                
                # Monitor task progress
                while task.status not in ["completed", "failed"]:
                    await asyncio.sleep(5)
                    task.refresh()
                    execution.progress = min(0.9, execution.progress + 0.1)
                
                if task.status == "completed":
                    execution.status = ExecutionStatus.COMPLETED
                    execution.progress = 1.0
                    execution.current_step = "Completed"
                    
                    # Update flow success count
                    flow.success_count += 1
                else:
                    execution.status = ExecutionStatus.FAILED
                    execution.error = f"Codegen task failed: {task.result}"
                    flow.failure_count += 1
            else:
                # Simulate flow execution for demo purposes
                steps = ["Preparing", "Building", "Testing", "Deploying", "Finalizing"]
                for i, step in enumerate(steps):
                    execution.current_step = step
                    execution.progress = (i + 1) / len(steps)
                    await asyncio.sleep(2)  # Simulate work
                
                execution.status = ExecutionStatus.COMPLETED
                flow.success_count += 1
            
            execution.completed_at = datetime.utcnow()
            flow.status = FlowStatus.IDLE
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            # Update flow failure count
            for project_flows in self.flows.values():
                for f in project_flows:
                    if f.id == execution.flow_id:
                        f.failure_count += 1
                        f.status = FlowStatus.IDLE
                        break
            
            logger.error(f"Flow execution {execution.id} failed: {e}")
        
        finally:
            # Remove from running flows
            if execution.id in self.running_flows:
                del self.running_flows[execution.id]
            
            await self._save_data()
            self._update_stats()
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                # Monitor project health
                for project_id in self.active_projects:
                    await self._monitor_project_health(project_id)
                
                # Check for auto-start flows
                await self._check_auto_start_flows()
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _flow_scheduler_loop(self) -> None:
        """Background flow scheduler loop"""
        while True:
            try:
                # Check scheduled flows
                await self._check_scheduled_flows()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in flow scheduler loop: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_project_health(self, project_id: str) -> None:
        """Monitor individual project health"""
        # Implementation for project health monitoring
        pass
    
    async def _check_auto_start_flows(self) -> None:
        """Check for flows that should auto-start"""
        for project_flows in self.flows.values():
            for flow in project_flows:
                if flow.auto_start and flow.status == FlowStatus.IDLE:
                    # Check trigger conditions
                    if await self._evaluate_trigger_conditions(flow):
                        await self.start_flow(flow.id, "auto-trigger")
    
    async def _check_scheduled_flows(self) -> None:
        """Check for scheduled flows"""
        # Implementation for scheduled flow checking
        pass
    
    async def _evaluate_trigger_conditions(self, flow: CICDFlow) -> bool:
        """Evaluate if flow trigger conditions are met"""
        # Implementation for trigger condition evaluation
        return False
    
    async def _calculate_project_health_score(self, project_id: str) -> float:
        """Calculate project health score"""
        # Basic health score calculation
        requirements = self.requirements.get(project_id, [])
        flows = self.flows.get(project_id, [])
        
        if not requirements and not flows:
            return 0.5  # Neutral score for empty projects
        
        # Calculate based on requirement completion and flow success rates
        completed_requirements = len([r for r in requirements if r.status == "completed"])
        requirement_score = completed_requirements / len(requirements) if requirements else 1.0
        
        successful_flows = sum(f.success_count for f in flows)
        total_flow_runs = sum(f.run_count for f in flows)
        flow_score = successful_flows / total_flow_runs if total_flow_runs > 0 else 1.0
        
        return (requirement_score + flow_score) / 2
    
    async def _generate_cross_project_insights(self, project_ids: List[str]) -> Dict[str, Any]:
        """Generate cross-project insights"""
        insights = {
            "common_technologies": [],
            "shared_dependencies": [],
            "collaboration_opportunities": [],
            "resource_optimization": []
        }
        
        # Analyze project types and technologies
        project_types = {}
        for project_id in project_ids:
            if project_id in self.projects:
                project_type = self.projects[project_id].type.value
                project_types[project_type] = project_types.get(project_type, 0) + 1
        
        insights["common_technologies"] = list(project_types.keys())
        
        return insights
    
    async def _generate_project_recommendations(self, project_ids: List[str]) -> List[str]:
        """Generate project recommendations"""
        recommendations = []
        
        # Analyze project health and suggest improvements
        for project_id in project_ids:
            if project_id not in self.projects:
                continue
            
            health_score = await self._calculate_project_health_score(project_id)
            if health_score < 0.5:
                recommendations.append(f"Project {self.projects[project_id].name} needs attention - low health score")
            
            flows = self.flows.get(project_id, [])
            if not flows:
                recommendations.append(f"Consider adding CI/CD flows to project {self.projects[project_id].name}")
        
        return recommendations
    
    def _get_project_type_distribution(self) -> Dict[str, int]:
        """Get distribution of project types"""
        distribution = {}
        for project in self.projects.values():
            project_type = project.type.value
            distribution[project_type] = distribution.get(project_type, 0) + 1
        return distribution
    
    def _get_requirement_status_distribution(self) -> Dict[str, int]:
        """Get distribution of requirement statuses"""
        distribution = {}
        for requirements in self.requirements.values():
            for req in requirements:
                status = req.status
                distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def _get_flow_status_distribution(self) -> Dict[str, int]:
        """Get distribution of flow statuses"""
        distribution = {}
        for flows in self.flows.values():
            for flow in flows:
                status = flow.status.value
                distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def _update_stats(self) -> None:
        """Update internal statistics"""
        self.stats.update({
            "projects_count": len(self.projects),
            "active_projects": len(self.active_projects),
            "total_requirements": sum(len(reqs) for reqs in self.requirements.values()),
            "total_flows": sum(len(flows) for flows in self.flows.values()),
            "running_flows": len(self.running_flows),
            "completed_executions": len([e for e in self.executions.values() if e.status == ExecutionStatus.COMPLETED]),
            "failed_executions": len([e for e in self.executions.values() if e.status == ExecutionStatus.FAILED])
        })
    
    async def _save_data(self) -> None:
        """Save data to disk"""
        try:
            data = {
                "projects": {pid: asdict(project) for pid, project in self.projects.items()},
                "requirements": {
                    pid: [asdict(req) for req in reqs] 
                    for pid, reqs in self.requirements.items()
                },
                "flows": {
                    pid: [asdict(flow) for flow in flows] 
                    for pid, flows in self.flows.items()
                },
                "executions": {eid: asdict(execution) for eid, execution in self.executions.items()},
                "active_projects": list(self.active_projects),
                "stats": self.stats
            }
            
            # Convert datetime objects to ISO strings
            data = self._serialize_datetime_objects(data)
            
            async with aiofiles.open(self.data_dir / "multi_project_data.json", "w") as f:
                await f.write(json.dumps(data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    async def _load_data(self) -> None:
        """Load data from disk"""
        try:
            data_file = self.data_dir / "multi_project_data.json"
            if not data_file.exists():
                logger.info("No existing data file found, starting fresh")
                return
            
            async with aiofiles.open(data_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
            
            # Deserialize data
            data = self._deserialize_datetime_objects(data)
            
            # Load projects
            for pid, project_data in data.get("projects", {}).items():
                project_data["type"] = ProjectType(project_data["type"])
                self.projects[pid] = ProjectConfig(**project_data)
            
            # Load requirements
            for pid, req_list in data.get("requirements", {}).items():
                self.requirements[pid] = [
                    ProjectRequirement(**req_data) for req_data in req_list
                ]
            
            # Load flows
            for pid, flow_list in data.get("flows", {}).items():
                flows = []
                for flow_data in flow_list:
                    flow_data["status"] = FlowStatus(flow_data["status"])
                    flows.append(CICDFlow(**flow_data))
                self.flows[pid] = flows
            
            # Load executions
            for eid, exec_data in data.get("executions", {}).items():
                exec_data["status"] = ExecutionStatus(exec_data["status"])
                execution = FlowExecution(**exec_data)
                self.executions[eid] = execution
                
                # Add to running flows if still running
                if execution.status == ExecutionStatus.RUNNING:
                    self.running_flows[eid] = execution
            
            # Load active projects
            self.active_projects = set(data.get("active_projects", []))
            
            # Load stats
            self.stats.update(data.get("stats", {}))
            
            logger.info(f"Loaded {len(self.projects)} projects, {len(self.executions)} executions")
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
    
    def _serialize_datetime_objects(self, obj: Any) -> Any:
        """Recursively serialize datetime objects to ISO strings"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime_objects(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        else:
            return obj
    
    def _deserialize_datetime_objects(self, obj: Any) -> Any:
        """Recursively deserialize ISO strings to datetime objects"""
        if isinstance(obj, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(obj)
            except (ValueError, TypeError):
                return obj
        elif isinstance(obj, dict):
            return {k: self._deserialize_datetime_objects(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetime_objects(item) for item in obj]
        else:
            return obj

