"""
Multi-Project Management System

This module provides comprehensive multi-project management capabilities,
allowing users to select, manage, and monitor multiple projects simultaneously
with autonomous CI/CD workflows.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from ..extensions.github.enhanced_agent import EnhancedGitHubAgent
from ..extensions.linear.enhanced_agent import EnhancedLinearAgent
from .workflow_automation import WorkflowAutomationEngine, WorkflowDefinition, WorkflowExecution
from .orchestrator_integration import OrchestratorDashboardIntegration
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)

class ProjectType(Enum):
    """Types of projects supported"""
    GITHUB_REPOSITORY = "github_repository"
    LOCAL_DIRECTORY = "local_directory"
    REMOTE_GIT = "remote_git"
    DOCKER_PROJECT = "docker_project"

class ProjectStatus(Enum):
    """Project status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ANALYZING = "analyzing"
    ERROR = "error"
    ARCHIVED = "archived"

class FlowStatus(Enum):
    """CI/CD Flow status states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProjectConfig:
    """Configuration for a project"""
    id: str
    name: str
    type: ProjectType
    source_url: str
    branch: str = "main"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ProjectRequirement:
    """Requirements for a project"""
    id: str
    project_id: str
    title: str
    description: str
    priority: int = 1  # 1-5 scale
    labels: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CICDFlow:
    """CI/CD Flow definition"""
    id: str
    project_id: str
    name: str
    description: str
    workflow_id: str
    status: FlowStatus
    trigger_conditions: Dict[str, Any]
    auto_start: bool = False
    schedule: Optional[str] = None  # Cron expression
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FlowExecution:
    """Individual flow execution instance"""
    id: str
    flow_id: str
    project_id: str
    status: FlowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_step: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    triggered_by: str = "manual"

class MultiProjectManager:
    """Comprehensive multi-project management system"""
    
    def __init__(self, 
                 github_agent: Optional[EnhancedGitHubAgent] = None,
                 linear_agent: Optional[EnhancedLinearAgent] = None,
                 orchestrator: Optional[OrchestratorDashboardIntegration] = None):
        self.github_agent = github_agent
        self.linear_agent = linear_agent
        self.orchestrator = orchestrator
        self.workflow_engine = WorkflowAutomationEngine(orchestrator) if orchestrator else None
        
        # Project storage
        self.projects: Dict[str, ProjectConfig] = {}
        self.requirements: Dict[str, List[ProjectRequirement]] = {}
        self.flows: Dict[str, List[CICDFlow]] = {}
        self.executions: Dict[str, FlowExecution] = {}
        
        # Active monitoring
        self.active_projects: Set[str] = set()
        self.running_flows: Dict[str, FlowExecution] = {}
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._scheduler_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the multi-project manager"""
        logger.info("Starting Multi-Project Manager...")
        
        # Start background monitoring
        self._monitoring_task = asyncio.create_task(self._monitor_projects())
        self._scheduler_task = asyncio.create_task(self._flow_scheduler())
        
        logger.info("Multi-Project Manager started successfully")
    
    async def stop(self):
        """Stop the multi-project manager"""
        logger.info("Stopping Multi-Project Manager...")
        
        # Cancel background tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._scheduler_task:
            self._scheduler_task.cancel()
            
        # Stop running flows
        for execution in self.running_flows.values():
            await self.stop_flow_execution(execution.id)
        
        logger.info("Multi-Project Manager stopped")
    
    # Project Management
    async def add_project(self, config: ProjectConfig) -> bool:
        """Add a new project to the system"""
        try:
            # Validate project configuration
            if not await self._validate_project_config(config):
                return False
            
            # Initialize project structure
            self.projects[config.id] = config
            self.requirements[config.id] = []
            self.flows[config.id] = []
            
            # Add to active projects if configured
            if config.settings.get("auto_activate", False):
                self.active_projects.add(config.id)
            
            logger.info(f"Added project: {config.name} ({config.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add project {config.name}: {e}")
            return False
    
    async def remove_project(self, project_id: str) -> bool:
        """Remove a project from the system"""
        try:
            if project_id not in self.projects:
                return False
            
            # Stop any running flows
            project_flows = self.flows.get(project_id, [])
            for flow in project_flows:
                if flow.status == FlowStatus.RUNNING:
                    await self.stop_flow(flow.id)
            
            # Remove from active projects
            self.active_projects.discard(project_id)
            
            # Clean up data
            del self.projects[project_id]
            del self.requirements[project_id]
            del self.flows[project_id]
            
            logger.info(f"Removed project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove project {project_id}: {e}")
            return False
    
    async def get_projects(self, active_only: bool = False) -> List[ProjectConfig]:
        """Get list of projects"""
        if active_only:
            return [self.projects[pid] for pid in self.active_projects if pid in self.projects]
        return list(self.projects.values())
    
    async def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        """Get specific project configuration"""
        return self.projects.get(project_id)
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project configuration"""
        try:
            if project_id not in self.projects:
                return False
            
            project = self.projects[project_id]
            
            # Update allowed fields
            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            project.updated_at = datetime.now()
            logger.info(f"Updated project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return False
    
    # Requirements Management
    async def add_requirement(self, requirement: ProjectRequirement) -> bool:
        """Add a requirement to a project"""
        try:
            if requirement.project_id not in self.projects:
                return False
            
            if requirement.project_id not in self.requirements:
                self.requirements[requirement.project_id] = []
            
            self.requirements[requirement.project_id].append(requirement)
            
            # Auto-trigger flows if configured
            await self._check_requirement_triggers(requirement)
            
            logger.info(f"Added requirement: {requirement.title} to project {requirement.project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add requirement: {e}")
            return False
    
    async def get_requirements(self, project_id: str) -> List[ProjectRequirement]:
        """Get requirements for a project"""
        return self.requirements.get(project_id, [])
    
    async def update_requirement(self, requirement_id: str, updates: Dict[str, Any]) -> bool:
        """Update a requirement"""
        try:
            for project_reqs in self.requirements.values():
                for req in project_reqs:
                    if req.id == requirement_id:
                        for key, value in updates.items():
                            if hasattr(req, key):
                                setattr(req, key, value)
                        logger.info(f"Updated requirement: {requirement_id}")
                        return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update requirement {requirement_id}: {e}")
            return False
    
    # CI/CD Flow Management
    async def create_flow(self, flow: CICDFlow) -> bool:
        """Create a new CI/CD flow"""
        try:
            if flow.project_id not in self.projects:
                return False
            
            if flow.project_id not in self.flows:
                self.flows[flow.project_id] = []
            
            self.flows[flow.project_id].append(flow)
            
            logger.info(f"Created flow: {flow.name} for project {flow.project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create flow: {e}")
            return False
    
    async def start_flow(self, flow_id: str, triggered_by: str = "manual") -> Optional[str]:
        """Start a CI/CD flow execution"""
        try:
            flow = await self._find_flow(flow_id)
            if not flow:
                return None
            
            # Create execution instance
            execution = FlowExecution(
                id=str(uuid.uuid4()),
                flow_id=flow_id,
                project_id=flow.project_id,
                status=FlowStatus.RUNNING,
                started_at=datetime.now(),
                triggered_by=triggered_by
            )
            
            self.executions[execution.id] = execution
            self.running_flows[execution.id] = execution
            
            # Start workflow execution
            if self.workflow_engine:
                await self._execute_flow_workflow(execution)
            
            # Update flow statistics
            flow.last_run = datetime.now()
            flow.run_count += 1
            
            logger.info(f"Started flow execution: {execution.id}")
            return execution.id
            
        except Exception as e:
            logger.error(f"Failed to start flow {flow_id}: {e}")
            return None
    
    async def stop_flow_execution(self, execution_id: str) -> bool:
        """Stop a running flow execution"""
        try:
            if execution_id not in self.executions:
                return False
            
            execution = self.executions[execution_id]
            execution.status = FlowStatus.CANCELLED
            execution.completed_at = datetime.now()
            
            # Remove from running flows
            self.running_flows.pop(execution_id, None)
            
            logger.info(f"Stopped flow execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop flow execution {execution_id}: {e}")
            return False
    
    async def get_flows(self, project_id: str) -> List[CICDFlow]:
        """Get flows for a project"""
        return self.flows.get(project_id, [])
    
    async def get_flow_executions(self, flow_id: str, limit: int = 10) -> List[FlowExecution]:
        """Get recent executions for a flow"""
        executions = [e for e in self.executions.values() if e.flow_id == flow_id]
        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]
    
    async def get_running_flows(self) -> Dict[str, FlowExecution]:
        """Get all currently running flows"""
        return self.running_flows.copy()
    
    # Multi-Project Analysis
    async def analyze_projects(self, project_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform comprehensive analysis across multiple projects"""
        try:
            target_projects = project_ids or list(self.projects.keys())
            
            analysis_results = {
                "timestamp": datetime.now().isoformat(),
                "projects_analyzed": len(target_projects),
                "project_summaries": {},
                "cross_project_insights": {},
                "recommendations": []
            }
            
            # Analyze each project
            for project_id in target_projects:
                if project_id in self.projects:
                    project_analysis = await self._analyze_single_project(project_id)
                    analysis_results["project_summaries"][project_id] = project_analysis
            
            # Cross-project analysis
            analysis_results["cross_project_insights"] = await self._cross_project_analysis(target_projects)
            
            # Generate recommendations
            analysis_results["recommendations"] = await self._generate_multi_project_recommendations(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Failed to analyze projects: {e}")
            return {"error": str(e)}
    
    # System Status and Monitoring
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "projects": {
                "total": len(self.projects),
                "active": len(self.active_projects),
                "inactive": len(self.projects) - len(self.active_projects)
            },
            "flows": {
                "total": sum(len(flows) for flows in self.flows.values()),
                "running": len(self.running_flows),
                "idle": sum(1 for flows in self.flows.values() for flow in flows if flow.status == FlowStatus.IDLE)
            },
            "executions": {
                "total": len(self.executions),
                "running": len(self.running_flows),
                "completed_today": len([e for e in self.executions.values() 
                                     if e.completed_at and e.completed_at.date() == datetime.now().date()])
            },
            "requirements": {
                "total": sum(len(reqs) for reqs in self.requirements.values()),
                "pending": sum(1 for reqs in self.requirements.values() for req in reqs if req.status == "pending"),
                "in_progress": sum(1 for reqs in self.requirements.values() for req in reqs if req.status == "in_progress")
            }
        }
    
    # Private helper methods
    async def _validate_project_config(self, config: ProjectConfig) -> bool:
        """Validate project configuration"""
        if not config.name or not config.source_url:
            return False
        
        # Check for duplicate IDs
        if config.id in self.projects:
            return False
        
        # Validate source URL based on type
        if config.type == ProjectType.GITHUB_REPOSITORY:
            return await self._validate_github_repo(config.source_url)
        
        return True
    
    async def _validate_github_repo(self, repo_url: str) -> bool:
        """Validate GitHub repository access"""
        if not self.github_agent:
            return False
        
        try:
            # Extract owner/repo from URL
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                repo_info = await self.github_agent.get_repository(owner, repo)
                return repo_info is not None
        except Exception:
            pass
        
        return False
    
    async def _monitor_projects(self):
        """Background task to monitor active projects"""
        while True:
            try:
                for project_id in self.active_projects.copy():
                    await self._check_project_health(project_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in project monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _flow_scheduler(self):
        """Background task to handle scheduled flows"""
        while True:
            try:
                current_time = datetime.now()
                
                for flows in self.flows.values():
                    for flow in flows:
                        if (flow.schedule and flow.next_run and 
                            current_time >= flow.next_run and 
                            flow.status == FlowStatus.IDLE):
                            
                            await self.start_flow(flow.id, "scheduled")
                            
                            # Calculate next run time
                            flow.next_run = self._calculate_next_run(flow.schedule, current_time)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flow scheduler: {e}")
                await asyncio.sleep(30)
    
    async def _check_project_health(self, project_id: str):
        """Check health of a specific project"""
        # Implementation for project health monitoring
        pass
    
    async def _check_requirement_triggers(self, requirement: ProjectRequirement):
        """Check if requirement should trigger any flows"""
        project_flows = self.flows.get(requirement.project_id, [])
        
        for flow in project_flows:
            if flow.auto_start and self._matches_trigger_conditions(requirement, flow.trigger_conditions):
                await self.start_flow(flow.id, f"requirement:{requirement.id}")
    
    def _matches_trigger_conditions(self, requirement: ProjectRequirement, conditions: Dict[str, Any]) -> bool:
        """Check if requirement matches flow trigger conditions"""
        # Check labels
        if "labels" in conditions:
            required_labels = set(conditions["labels"])
            requirement_labels = set(requirement.labels)
            if not required_labels.intersection(requirement_labels):
                return False
        
        # Check priority
        if "min_priority" in conditions:
            if requirement.priority < conditions["min_priority"]:
                return False
        
        # Check keywords in title/description
        if "keywords" in conditions:
            text = f"{requirement.title} {requirement.description}".lower()
            keywords = [kw.lower() for kw in conditions["keywords"]]
            if not any(kw in text for kw in keywords):
                return False
        
        return True
    
    async def _find_flow(self, flow_id: str) -> Optional[CICDFlow]:
        """Find a flow by ID across all projects"""
        for flows in self.flows.values():
            for flow in flows:
                if flow.id == flow_id:
                    return flow
        return None
    
    async def _execute_flow_workflow(self, execution: FlowExecution):
        """Execute the workflow for a flow"""
        # Implementation for workflow execution
        pass
    
    async def _analyze_single_project(self, project_id: str) -> Dict[str, Any]:
        """Analyze a single project"""
        project = self.projects[project_id]
        requirements = self.requirements.get(project_id, [])
        flows = self.flows.get(project_id, [])
        
        return {
            "project_info": {
                "name": project.name,
                "type": project.type.value,
                "status": "active" if project_id in self.active_projects else "inactive",
                "last_updated": project.updated_at.isoformat()
            },
            "requirements": {
                "total": len(requirements),
                "pending": len([r for r in requirements if r.status == "pending"]),
                "in_progress": len([r for r in requirements if r.status == "in_progress"]),
                "completed": len([r for r in requirements if r.status == "completed"])
            },
            "flows": {
                "total": len(flows),
                "active": len([f for f in flows if f.status == FlowStatus.RUNNING]),
                "success_rate": self._calculate_flow_success_rate(flows)
            }
        }
    
    async def _cross_project_analysis(self, project_ids: List[str]) -> Dict[str, Any]:
        """Perform cross-project analysis"""
        return {
            "common_patterns": [],
            "shared_dependencies": [],
            "optimization_opportunities": [],
            "resource_utilization": {}
        }
    
    async def _generate_multi_project_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on multi-project analysis"""
        recommendations = []
        
        # Add basic recommendations based on analysis
        if analysis["projects_analyzed"] > 1:
            recommendations.append("Consider implementing shared CI/CD templates across projects")
        
        return recommendations
    
    def _calculate_flow_success_rate(self, flows: List[CICDFlow]) -> float:
        """Calculate success rate for flows"""
        if not flows:
            return 0.0
        
        total_runs = sum(flow.run_count for flow in flows)
        if total_runs == 0:
            return 0.0
        
        total_successes = sum(flow.success_count for flow in flows)
        return (total_successes / total_runs) * 100
    
    def _calculate_next_run(self, schedule: str, current_time: datetime) -> datetime:
        """Calculate next run time based on cron schedule"""
        # Simple implementation - in production, use a proper cron parser
        return current_time + timedelta(hours=1)

