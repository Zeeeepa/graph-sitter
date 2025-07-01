"""
Enhanced Data Models for Single-User Dashboard System

Simplified models that connect all 11 extensions effectively:
- Modal: Infrastructure scaling
- Contexten App: Main orchestrator  
- Prefect: Workflow orchestration
- ControlFlow: Agent orchestration
- Codegen: AI planning and execution
- GitHub: Repository management
- Linear: Task management
- Slack: Notifications
- CircleCI: CI/CD monitoring
- GrainChain: Sandboxed deployments
- Graph-sitter: Code analysis
"""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Core Status Enums
class ProjectStatus(str, Enum):
    DISCOVERED = "discovered"
    PINNED = "pinned"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    PLANNING = "planning"
    PLANNED = "planned"
    EXECUTING = "executing"
    DEPLOYED = "deployed"
    COMPLETED = "completed"
    FAILED = "failed"

class FlowStatus(str, Enum):
    INACTIVE = "inactive"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DeploymentStatus(str, Enum):
    NOT_DEPLOYED = "not_deployed"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    TESTING = "testing"
    VALIDATED = "validated"
    FAILED = "failed"

# Graph-sitter Analysis Models
@dataclass
class CodeError:
    """Represents a code error found by Graph-sitter analysis"""
    file_path: str
    line_number: int
    column: int
    error_type: str  # syntax, logic, type, etc.
    message: str
    severity: str  # error, warning, info
    suggestion: Optional[str] = None

@dataclass
class MissingFeature:
    """Represents a missing feature detected by analysis"""
    feature_name: str
    description: str
    file_path: str
    suggested_implementation: Optional[str] = None
    priority: str = "medium"  # high, medium, low

@dataclass
class ConfigIssue:
    """Represents configuration issues found in the codebase"""
    config_file: str
    issue_type: str  # missing_key, wrong_value, deprecated, etc.
    message: str
    suggested_fix: Optional[str] = None

@dataclass
class GraphSitterAnalysis:
    """Complete Graph-sitter analysis results"""
    project_id: str
    analysis_timestamp: datetime
    errors: List[CodeError] = field(default_factory=list)
    missing_features: List[MissingFeature] = field(default_factory=list)
    config_issues: List[ConfigIssue] = field(default_factory=list)
    quality_score: float = 0.0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    test_coverage: float = 0.0
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    security_issues: List[Dict[str, Any]] = field(default_factory=list)
    performance_issues: List[Dict[str, Any]] = field(default_factory=list)

# GrainChain Deployment Models
@dataclass
class TestResult:
    """Test result from GrainChain sandbox"""
    test_name: str
    status: str  # passed, failed, skipped
    duration: float
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class SandboxEnvironment:
    """GrainChain sandbox environment details"""
    sandbox_id: str
    environment_type: str  # development, staging, production
    resources: Dict[str, Any]  # CPU, memory, storage
    status: str  # creating, ready, running, stopped, destroyed
    created_at: datetime
    url: Optional[str] = None

@dataclass
class DeploymentSnapshot:
    """GrainChain deployment snapshot"""
    snapshot_id: str
    deployment_id: str
    created_at: datetime
    description: str
    size_mb: float
    status: str  # creating, ready, restoring, failed

@dataclass
class GrainChainDeployment:
    """Complete GrainChain deployment information"""
    deployment_id: str
    project_id: str
    sandbox: SandboxEnvironment
    status: DeploymentStatus
    test_results: List[TestResult] = field(default_factory=list)
    snapshots: List[DeploymentSnapshot] = field(default_factory=list)
    deployment_logs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

# Core Project Models
@dataclass
class DashboardProject:
    """Main project entity connecting all extensions"""
    # Core identification
    project_id: str
    name: str
    github_repo: str
    github_owner: str
    
    # Status tracking
    status: ProjectStatus = ProjectStatus.DISCOVERED
    flow_status: FlowStatus = FlowStatus.INACTIVE
    
    # Extension integrations
    github_data: Dict[str, Any] = field(default_factory=dict)  # GitHub API data
    linear_project_id: Optional[str] = None  # Linear project ID
    linear_team_id: Optional[str] = None  # Linear team ID
    
    # Analysis and deployment
    analysis: Optional[GraphSitterAnalysis] = None
    deployment: Optional[GrainChainDeployment] = None
    
    # Workflow tracking
    current_plan_id: Optional[str] = None
    active_workflow_id: Optional[str] = None
    
    # Metadata
    pinned: bool = False
    pinned_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Configuration
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: ProjectStatus):
        """Update project status with timestamp"""
        self.status = new_status
        self.updated_at = datetime.now()

@dataclass
class DashboardTask:
    """Task entity connecting Linear, Codegen, and workflow execution"""
    # Core identification
    task_id: str
    project_id: str
    plan_id: str
    
    # Task details
    title: str
    description: str
    task_type: str  # code_change, deployment, analysis, etc.
    
    # Status and progress
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    
    # Extension integrations
    linear_issue_id: Optional[str] = None  # Linear issue ID
    github_pr_id: Optional[str] = None  # GitHub PR ID
    codegen_task_id: Optional[str] = None  # Codegen SDK task ID
    circleci_pipeline_id: Optional[str] = None  # CircleCI pipeline ID
    
    # Execution details
    assigned_agent: Optional[str] = None  # ControlFlow agent
    execution_logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Other task IDs
    blocks: List[str] = field(default_factory=list)  # Tasks blocked by this
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # minutes

@dataclass
class DashboardPlan:
    """Plan entity from Codegen SDK with task breakdown"""
    # Core identification
    plan_id: str
    project_id: str
    
    # Plan details
    title: str
    description: str
    requirements: str  # Original user requirements
    
    # Status
    status: str = "draft"  # draft, approved, executing, completed, failed
    
    # Tasks
    tasks: List[DashboardTask] = field(default_factory=list)
    
    # Codegen integration
    codegen_response: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis integration
    based_on_analysis: Optional[str] = None  # Analysis ID used for planning
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "user"  # Single user system
    estimated_duration: Optional[int] = None  # Total estimated minutes

# Workflow and Event Models
@dataclass
class WorkflowEvent:
    """Event in the workflow system"""
    event_id: str
    event_type: str
    source: str  # Which extension generated the event
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SystemHealth:
    """System health status for all extensions"""
    extension_status: Dict[str, str] = field(default_factory=dict)  # extension_name -> status
    last_check: datetime = field(default_factory=datetime.now)
    issues: List[str] = field(default_factory=list)

# Configuration Models
@dataclass
class ExtensionConfig:
    """Configuration for individual extensions"""
    extension_name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)

@dataclass
class DashboardConfig:
    """Main dashboard configuration"""
    # Extension configurations
    extensions: Dict[str, ExtensionConfig] = field(default_factory=dict)
    
    # Global settings
    auto_deploy: bool = True
    auto_analyze: bool = True
    notification_level: str = "normal"  # minimal, normal, verbose
    
    # Database
    database_url: str = "sqlite:///dashboard.db"
    
    # Paths
    workspace_path: str = "./workspace"
    logs_path: str = "./logs"

# Utility functions for model management
def create_project_from_github(repo_url: str, repo_data: Dict[str, Any]) -> DashboardProject:
    """Create a project from GitHub repository data"""
    # Extract owner and repo name from URL
    parts = repo_url.replace("https://github.com/", "").split("/")
    owner, repo_name = parts[0], parts[1]
    
    project_id = f"{owner}_{repo_name}"
    
    return DashboardProject(
        project_id=project_id,
        name=repo_data.get("name", repo_name),
        github_repo=repo_name,
        github_owner=owner,
        github_data=repo_data,
        status=ProjectStatus.DISCOVERED
    )

def create_analysis_from_graph_sitter(project_id: str, analysis_data: Dict[str, Any]) -> GraphSitterAnalysis:
    """Create analysis object from Graph-sitter results"""
    return GraphSitterAnalysis(
        project_id=project_id,
        analysis_timestamp=datetime.now(),
        errors=[CodeError(**error) for error in analysis_data.get("errors", [])],
        missing_features=[MissingFeature(**feature) for feature in analysis_data.get("missing_features", [])],
        config_issues=[ConfigIssue(**issue) for issue in analysis_data.get("config_issues", [])],
        quality_score=analysis_data.get("quality_score", 0.0),
        complexity_score=analysis_data.get("complexity_score", 0.0),
        maintainability_score=analysis_data.get("maintainability_score", 0.0),
        test_coverage=analysis_data.get("test_coverage", 0.0),
        dependencies=analysis_data.get("dependencies", {}),
        security_issues=analysis_data.get("security_issues", []),
        performance_issues=analysis_data.get("performance_issues", [])
    )

def create_deployment_for_project(project_id: str, sandbox_config: Dict[str, Any]) -> GrainChainDeployment:
    """Create a new deployment for a project"""
    deployment_id = f"deploy_{project_id}_{int(datetime.now().timestamp())}"
    sandbox_id = f"sandbox_{deployment_id}"
    
    sandbox = SandboxEnvironment(
        sandbox_id=sandbox_id,
        environment_type=sandbox_config.get("type", "development"),
        resources=sandbox_config.get("resources", {}),
        status="creating",
        created_at=datetime.now()
    )
    
    return GrainChainDeployment(
        deployment_id=deployment_id,
        project_id=project_id,
        sandbox=sandbox,
        status=DeploymentStatus.NOT_DEPLOYED
    )

