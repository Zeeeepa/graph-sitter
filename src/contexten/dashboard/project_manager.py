"""
Project Management System

Comprehensive project management with pinning, requirements tracking,
health monitoring, and flow configuration for contexten projects.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import os
from pathlib import Path

from pydantic import BaseModel, Field
import aiofiles

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    MAINTENANCE = "maintenance"


class ProjectHealth(Enum):
    """Project health status."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class RequirementStatus(Enum):
    """Requirement status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class ProjectRequirement:
    """Individual project requirement."""
    id: str
    title: str
    description: str
    status: RequirementStatus
    priority: str  # low, medium, high, critical
    category: str  # feature, bugfix, maintenance, security
    assignee: Optional[str] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    linear_issue_id: Optional[str] = None
    github_issue_id: Optional[str] = None


@dataclass
class ProjectMetrics:
    """Project health and performance metrics."""
    code_quality_score: float = 0.0
    test_coverage: float = 0.0
    bug_count: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    active_prs: int = 0
    deployment_frequency: float = 0.0  # deployments per week
    lead_time: float = 0.0  # hours from commit to deployment
    mttr: float = 0.0  # mean time to recovery in hours
    change_failure_rate: float = 0.0  # percentage
    last_deployment: Optional[datetime] = None
    last_incident: Optional[datetime] = None
    uptime_percentage: float = 100.0


@dataclass
class FlowConfiguration:
    """Flow configuration for a project."""
    flow_template_id: str
    parameters: Dict[str, Any]
    enabled: bool = True
    auto_trigger: bool = False
    trigger_conditions: List[str] = field(default_factory=list)
    schedule: Optional[str] = None  # cron expression
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


@dataclass
class PinnedProject:
    """Pinned project with comprehensive management data."""
    id: str
    name: str
    description: str
    repository_url: str
    status: ProjectStatus
    health: ProjectHealth
    owner: str
    team_members: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    requirements: List[ProjectRequirement] = field(default_factory=list)
    metrics: ProjectMetrics = field(default_factory=ProjectMetrics)
    flow_configurations: Dict[str, FlowConfiguration] = field(default_factory=dict)
    pinned_by: str = ""
    pinned_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    
    # Integration IDs
    github_repo_id: Optional[str] = None
    linear_project_id: Optional[str] = None
    slack_channel_id: Optional[str] = None
    
    # Configuration
    auto_sync_enabled: bool = True
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "flow_completion": True,
        "requirement_updates": True,
        "health_alerts": True,
        "deployment_notifications": True
    })


class RequirementsManager:
    """Manages project requirements and their lifecycle."""
    
    def __init__(self):
        self.requirements_cache: Dict[str, List[ProjectRequirement]] = {}
    
    async def add_requirement(self, project_id: str, requirement: ProjectRequirement) -> bool:
        """Add a new requirement to a project."""
        try:
            if project_id not in self.requirements_cache:
                self.requirements_cache[project_id] = []
            
            requirement.created_at = datetime.now()
            requirement.updated_at = datetime.now()
            
            self.requirements_cache[project_id].append(requirement)
            
            logger.info(f"Added requirement {requirement.id} to project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add requirement: {e}")
            return False
    
    async def update_requirement(self, project_id: str, requirement_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing requirement."""
        try:
            if project_id not in self.requirements_cache:
                return False
            
            for req in self.requirements_cache[project_id]:
                if req.id == requirement_id:
                    # Update allowed fields
                    allowed_fields = [
                        'title', 'description', 'status', 'priority', 'category',
                        'assignee', 'estimated_hours', 'actual_hours', 'dependencies',
                        'tags', 'due_date', 'linear_issue_id', 'github_issue_id'
                    ]
                    
                    for field, value in updates.items():
                        if field in allowed_fields:
                            setattr(req, field, value)
                    
                    req.updated_at = datetime.now()
                    
                    # Set completion time if status changed to completed
                    if updates.get('status') == RequirementStatus.COMPLETED and not req.completed_at:
                        req.completed_at = datetime.now()
                    
                    logger.info(f"Updated requirement {requirement_id} in project {project_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update requirement: {e}")
            return False
    
    async def get_requirements(self, project_id: str, status: RequirementStatus = None) -> List[ProjectRequirement]:
        """Get requirements for a project, optionally filtered by status."""
        if project_id not in self.requirements_cache:
            return []
        
        requirements = self.requirements_cache[project_id]
        
        if status:
            requirements = [req for req in requirements if req.status == status]
        
        return sorted(requirements, key=lambda r: r.created_at, reverse=True)
    
    async def get_requirement_stats(self, project_id: str) -> Dict[str, Any]:
        """Get requirement statistics for a project."""
        requirements = await self.get_requirements(project_id)
        
        if not requirements:
            return {
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "completion_rate": 0.0,
                "overdue_count": 0
            }
        
        stats = {
            "total": len(requirements),
            "by_status": {},
            "by_priority": {},
            "completion_rate": 0.0,
            "overdue_count": 0
        }
        
        # Count by status
        for status in RequirementStatus:
            count = len([r for r in requirements if r.status == status])
            stats["by_status"][status.value] = count
        
        # Count by priority
        priorities = ["low", "medium", "high", "critical"]
        for priority in priorities:
            count = len([r for r in requirements if r.priority == priority])
            stats["by_priority"][priority] = count
        
        # Calculate completion rate
        completed = stats["by_status"].get("completed", 0)
        stats["completion_rate"] = (completed / len(requirements)) * 100 if requirements else 0
        
        # Count overdue requirements
        now = datetime.now()
        overdue = [r for r in requirements if r.due_date and r.due_date < now and r.status != RequirementStatus.COMPLETED]
        stats["overdue_count"] = len(overdue)
        
        return stats


class ProjectHealthMonitor:
    """Monitors and assesses project health."""
    
    def __init__(self):
        self.health_cache: Dict[str, ProjectMetrics] = {}
    
    async def assess_project_health(self, project: PinnedProject) -> ProjectHealth:
        """Assess overall project health based on metrics."""
        try:
            metrics = project.metrics
            score = 0
            max_score = 100
            
            # Code quality (20 points)
            score += min(20, metrics.code_quality_score * 20)
            
            # Test coverage (20 points)
            score += min(20, metrics.test_coverage * 20)
            
            # Bug count (15 points) - fewer bugs = higher score
            if metrics.bug_count == 0:
                score += 15
            elif metrics.bug_count <= 5:
                score += 10
            elif metrics.bug_count <= 10:
                score += 5
            
            # Issue resolution rate (15 points)
            total_issues = metrics.open_issues + metrics.closed_issues
            if total_issues > 0:
                resolution_rate = metrics.closed_issues / total_issues
                score += resolution_rate * 15
            
            # Deployment frequency (10 points)
            if metrics.deployment_frequency >= 1:  # At least weekly
                score += 10
            elif metrics.deployment_frequency >= 0.5:  # Bi-weekly
                score += 7
            elif metrics.deployment_frequency >= 0.25:  # Monthly
                score += 5
            
            # Change failure rate (10 points) - lower is better
            if metrics.change_failure_rate <= 0.05:  # 5% or less
                score += 10
            elif metrics.change_failure_rate <= 0.15:  # 15% or less
                score += 7
            elif metrics.change_failure_rate <= 0.30:  # 30% or less
                score += 5
            
            # MTTR (10 points) - lower is better
            if metrics.mttr <= 1:  # 1 hour or less
                score += 10
            elif metrics.mttr <= 4:  # 4 hours or less
                score += 7
            elif metrics.mttr <= 24:  # 24 hours or less
                score += 5
            
            # Determine health level
            health_percentage = (score / max_score) * 100
            
            if health_percentage >= 90:
                return ProjectHealth.EXCELLENT
            elif health_percentage >= 75:
                return ProjectHealth.GOOD
            elif health_percentage >= 50:
                return ProjectHealth.WARNING
            else:
                return ProjectHealth.CRITICAL
                
        except Exception as e:
            logger.error(f"Failed to assess project health: {e}")
            return ProjectHealth.UNKNOWN
    
    async def update_metrics(self, project_id: str, metrics_update: Dict[str, Any]) -> bool:
        """Update project metrics."""
        try:
            if project_id not in self.health_cache:
                self.health_cache[project_id] = ProjectMetrics()
            
            metrics = self.health_cache[project_id]
            
            # Update allowed metric fields
            allowed_fields = [
                'code_quality_score', 'test_coverage', 'bug_count', 'open_issues',
                'closed_issues', 'active_prs', 'deployment_frequency', 'lead_time',
                'mttr', 'change_failure_rate', 'last_deployment', 'last_incident',
                'uptime_percentage'
            ]
            
            for field, value in metrics_update.items():
                if field in allowed_fields:
                    setattr(metrics, field, value)
            
            logger.info(f"Updated metrics for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return False
    
    async def get_health_alerts(self, project: PinnedProject) -> List[Dict[str, Any]]:
        """Get health alerts for a project."""
        alerts = []
        metrics = project.metrics
        
        # Critical alerts
        if metrics.bug_count > 20:
            alerts.append({
                "level": "critical",
                "message": f"High bug count: {metrics.bug_count} open bugs",
                "metric": "bug_count",
                "value": metrics.bug_count
            })
        
        if metrics.change_failure_rate > 0.5:
            alerts.append({
                "level": "critical",
                "message": f"High change failure rate: {metrics.change_failure_rate:.1%}",
                "metric": "change_failure_rate",
                "value": metrics.change_failure_rate
            })
        
        if metrics.uptime_percentage < 95:
            alerts.append({
                "level": "critical",
                "message": f"Low uptime: {metrics.uptime_percentage:.1f}%",
                "metric": "uptime_percentage",
                "value": metrics.uptime_percentage
            })
        
        # Warning alerts
        if metrics.test_coverage < 0.7:
            alerts.append({
                "level": "warning",
                "message": f"Low test coverage: {metrics.test_coverage:.1%}",
                "metric": "test_coverage",
                "value": metrics.test_coverage
            })
        
        if metrics.deployment_frequency < 0.25:  # Less than monthly
            alerts.append({
                "level": "warning",
                "message": "Low deployment frequency",
                "metric": "deployment_frequency",
                "value": metrics.deployment_frequency
            })
        
        if metrics.mttr > 24:  # More than 24 hours
            alerts.append({
                "level": "warning",
                "message": f"High MTTR: {metrics.mttr:.1f} hours",
                "metric": "mttr",
                "value": metrics.mttr
            })
        
        return alerts


class ProjectManager:
    """Main project management coordinator."""
    
    def __init__(self, data_dir: str = "data/projects"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.pinned_projects: Dict[str, PinnedProject] = {}
        self.requirements_manager = RequirementsManager()
        self.health_monitor = ProjectHealthMonitor()
        
        # Load existing projects
        asyncio.create_task(self._load_projects())
    
    async def _load_projects(self):
        """Load pinned projects from storage."""
        try:
            projects_file = self.data_dir / "pinned_projects.json"
            if projects_file.exists():
                async with aiofiles.open(projects_file, 'r') as f:
                    data = json.loads(await f.read())
                    
                for project_data in data.get('projects', []):
                    project = self._dict_to_project(project_data)
                    self.pinned_projects[project.id] = project
                    
                logger.info(f"Loaded {len(self.pinned_projects)} pinned projects")
                
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
    
    async def _save_projects(self):
        """Save pinned projects to storage."""
        try:
            projects_file = self.data_dir / "pinned_projects.json"
            data = {
                'projects': [self._project_to_dict(project) for project in self.pinned_projects.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            async with aiofiles.open(projects_file, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    def _project_to_dict(self, project: PinnedProject) -> Dict[str, Any]:
        """Convert project to dictionary for serialization."""
        data = asdict(project)
        # Convert enums to strings
        data['status'] = project.status.value
        data['health'] = project.health.value
        
        # Convert requirements
        data['requirements'] = []
        for req in project.requirements:
            req_dict = asdict(req)
            req_dict['status'] = req.status.value
            data['requirements'].append(req_dict)
        
        return data
    
    def _dict_to_project(self, data: Dict[str, Any]) -> PinnedProject:
        """Convert dictionary to project object."""
        # Convert enums from strings
        data['status'] = ProjectStatus(data.get('status', 'active'))
        data['health'] = ProjectHealth(data.get('health', 'unknown'))
        
        # Convert requirements
        requirements = []
        for req_data in data.get('requirements', []):
            req_data['status'] = RequirementStatus(req_data.get('status', 'pending'))
            # Convert datetime strings back to datetime objects
            for date_field in ['created_at', 'updated_at', 'due_date', 'completed_at']:
                if req_data.get(date_field):
                    req_data[date_field] = datetime.fromisoformat(req_data[date_field])
            requirements.append(ProjectRequirement(**req_data))
        
        data['requirements'] = requirements
        
        # Convert datetime strings back to datetime objects
        for date_field in ['pinned_at', 'created_at', 'updated_at', 'last_activity']:
            if data.get(date_field):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # Handle metrics
        if 'metrics' in data:
            metrics_data = data['metrics']
            for date_field in ['last_deployment', 'last_incident']:
                if metrics_data.get(date_field):
                    metrics_data[date_field] = datetime.fromisoformat(metrics_data[date_field])
            data['metrics'] = ProjectMetrics(**metrics_data)
        
        return PinnedProject(**data)
    
    async def pin_project(self, project_data: Dict[str, Any], pinned_by: str) -> Optional[PinnedProject]:
        """Pin a new project."""
        try:
            project_id = project_data.get('id') or str(uuid.uuid4())
            
            if project_id in self.pinned_projects:
                logger.warning(f"Project {project_id} is already pinned")
                return self.pinned_projects[project_id]
            
            project = PinnedProject(
                id=project_id,
                name=project_data['name'],
                description=project_data.get('description', ''),
                repository_url=project_data['repository_url'],
                status=ProjectStatus(project_data.get('status', 'active')),
                health=ProjectHealth.UNKNOWN,
                owner=project_data['owner'],
                team_members=project_data.get('team_members', []),
                tags=project_data.get('tags', []),
                pinned_by=pinned_by,
                github_repo_id=project_data.get('github_repo_id'),
                linear_project_id=project_data.get('linear_project_id'),
                slack_channel_id=project_data.get('slack_channel_id')
            )
            
            self.pinned_projects[project_id] = project
            await self._save_projects()
            
            logger.info(f"Pinned project {project_id}: {project.name}")
            return project
            
        except Exception as e:
            logger.error(f"Failed to pin project: {e}")
            return None
    
    async def unpin_project(self, project_id: str) -> bool:
        """Unpin a project."""
        try:
            if project_id not in self.pinned_projects:
                logger.warning(f"Project {project_id} is not pinned")
                return False
            
            del self.pinned_projects[project_id]
            await self._save_projects()
            
            logger.info(f"Unpinned project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unpin project: {e}")
            return False
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update a pinned project."""
        try:
            if project_id not in self.pinned_projects:
                logger.warning(f"Project {project_id} not found")
                return False
            
            project = self.pinned_projects[project_id]
            
            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'status', 'owner', 'team_members',
                'tags', 'github_repo_id', 'linear_project_id', 'slack_channel_id',
                'auto_sync_enabled', 'notification_preferences'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'status' and isinstance(value, str):
                        value = ProjectStatus(value)
                    setattr(project, field, value)
            
            project.updated_at = datetime.now()
            project.last_activity = datetime.now()
            
            # Update health assessment
            project.health = await self.health_monitor.assess_project_health(project)
            
            await self._save_projects()
            
            logger.info(f"Updated project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update project: {e}")
            return False
    
    def get_project(self, project_id: str) -> Optional[PinnedProject]:
        """Get a pinned project by ID."""
        return self.pinned_projects.get(project_id)
    
    def list_projects(self, status: ProjectStatus = None, health: ProjectHealth = None) -> List[PinnedProject]:
        """List pinned projects with optional filtering."""
        projects = list(self.pinned_projects.values())
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        if health:
            projects = [p for p in projects if p.health == health]
        
        return sorted(projects, key=lambda p: p.pinned_at, reverse=True)
    
    async def add_requirement(self, project_id: str, requirement_data: Dict[str, Any]) -> Optional[ProjectRequirement]:
        """Add a requirement to a project."""
        try:
            if project_id not in self.pinned_projects:
                logger.warning(f"Project {project_id} not found")
                return None
            
            requirement = ProjectRequirement(
                id=requirement_data.get('id') or str(uuid.uuid4()),
                title=requirement_data['title'],
                description=requirement_data.get('description', ''),
                status=RequirementStatus(requirement_data.get('status', 'pending')),
                priority=requirement_data.get('priority', 'medium'),
                category=requirement_data.get('category', 'feature'),
                assignee=requirement_data.get('assignee'),
                estimated_hours=requirement_data.get('estimated_hours'),
                dependencies=requirement_data.get('dependencies', []),
                tags=requirement_data.get('tags', []),
                due_date=requirement_data.get('due_date'),
                linear_issue_id=requirement_data.get('linear_issue_id'),
                github_issue_id=requirement_data.get('github_issue_id')
            )
            
            project = self.pinned_projects[project_id]
            project.requirements.append(requirement)
            project.updated_at = datetime.now()
            project.last_activity = datetime.now()
            
            await self.requirements_manager.add_requirement(project_id, requirement)
            await self._save_projects()
            
            logger.info(f"Added requirement {requirement.id} to project {project_id}")
            return requirement
            
        except Exception as e:
            logger.error(f"Failed to add requirement: {e}")
            return None
    
    async def get_project_dashboard_data(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a project."""
        try:
            project = self.get_project(project_id)
            if not project:
                return {"error": "Project not found"}
            
            # Get requirement statistics
            req_stats = await self.requirements_manager.get_requirement_stats(project_id)
            
            # Get health alerts
            health_alerts = await self.health_monitor.get_health_alerts(project)
            
            # Calculate project statistics
            total_flows = len(project.flow_configurations)
            active_flows = len([fc for fc in project.flow_configurations.values() if fc.enabled])
            
            return {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status.value,
                    "health": project.health.value,
                    "owner": project.owner,
                    "team_members": project.team_members,
                    "tags": project.tags,
                    "last_activity": project.last_activity.isoformat() if project.last_activity else None
                },
                "requirements": req_stats,
                "metrics": asdict(project.metrics),
                "health_alerts": health_alerts,
                "flows": {
                    "total": total_flows,
                    "active": active_flows,
                    "configurations": list(project.flow_configurations.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}


# Global project manager instance
project_manager = ProjectManager()

