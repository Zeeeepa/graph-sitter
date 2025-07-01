"""
Core Multi-Project Manager

Focused multi-project management leveraging existing graph-sitter analysis
capabilities with Codegen SDK integration and quality gates.
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
from graph_sitter import Codebase
from graph_sitter.analysis import EnhancedCodebaseAnalyzer
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ProjectType(str, Enum):
    """Project type enumeration"""
    GITHUB_REPO = "github_repo"
    LOCAL_DIRECTORY = "local_directory"


class FlowStatus(str, Enum):
    """Flow status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProjectConfig:
    """Simplified project configuration"""
    id: str
    name: str
    type: ProjectType
    path: str  # Local path or will be cloned to this path
    source_url: Optional[str] = None
    branch: str = "main"
    description: str = ""
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class QualityGate:
    """Quality gate configuration"""
    id: str
    name: str
    project_id: str
    conditions: Dict[str, Any]  # e.g., {"health_score": {"min": 80}, "complexity": {"max": 10}}
    actions: List[str]  # e.g., ["block_deployment", "create_issue", "notify_team"]
    enabled: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class FlowExecution:
    """Simple flow execution tracking"""
    id: str
    project_id: str
    flow_type: str  # "analysis", "quality_gate", "codegen_task"
    status: FlowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    triggered_by: str = "system"


class CoreMultiProjectManager:
    """
    Core multi-project manager that leverages existing graph-sitter analysis
    and provides Codegen SDK integration with quality gates.
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
        
        # Core data
        self.projects: Dict[str, ProjectConfig] = {}
        self.analyzers: Dict[str, EnhancedCodebaseAnalyzer] = {}
        self.quality_gates: Dict[str, QualityGate] = {}
        self.executions: Dict[str, FlowExecution] = {}
        
        # Active tracking
        self.active_projects: Set[str] = set()
        self.running_executions: Dict[str, FlowExecution] = {}
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._event_stream_task: Optional[asyncio.Task] = None
        
        # Event streaming
        self.event_subscribers: List[asyncio.Queue] = []
    
    async def start(self) -> None:
        """Start the multi-project manager"""
        logger.info("Starting Core Multi-Project Manager...")
        
        # Initialize Codegen SDK
        if self.codegen_org_id and self.codegen_token:
            try:
                self.codegen_agent = CodegenAgent(
                    org_id=self.codegen_org_id,
                    token=self.codegen_token
                )
                logger.info("Codegen SDK initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Codegen SDK: {e}")
        
        # Load persisted data
        await self._load_data()
        
        # Start background tasks
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._event_stream_task = asyncio.create_task(self._event_stream_loop())
        
        logger.info("Core Multi-Project Manager started")
    
    async def stop(self) -> None:
        """Stop the multi-project manager"""
        logger.info("Stopping Core Multi-Project Manager...")
        
        # Cancel background tasks
        for task in [self._monitoring_task, self._event_stream_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Save data
        await self._save_data()
        
        logger.info("Core Multi-Project Manager stopped")
    
    # Project Management API
    async def add_project(self, project: ProjectConfig) -> bool:
        """Add a new project"""
        try:
            # Create analyzer for the project
            if project.type == ProjectType.LOCAL_DIRECTORY:
                codebase = Codebase(project.path)
            else:
                # For GitHub repos, assume they're cloned to the path
                codebase = Codebase(project.path)
            
            analyzer = EnhancedCodebaseAnalyzer(codebase, project.id)
            
            self.projects[project.id] = project
            self.analyzers[project.id] = analyzer
            self.active_projects.add(project.id)
            
            await self._save_data()
            await self._emit_event("project_added", {"project_id": project.id, "name": project.name})
            
            logger.info(f"Added project: {project.name}")
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
    
    async def remove_project(self, project_id: str) -> bool:
        """Remove a project"""
        if project_id not in self.projects:
            return False
        
        # Stop any running executions
        for execution_id, execution in list(self.running_executions.items()):
            if execution.project_id == project_id:
                execution.status = FlowStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.error = "Project removed"
                del self.running_executions[execution_id]
        
        # Remove project data
        del self.projects[project_id]
        if project_id in self.analyzers:
            del self.analyzers[project_id]
        self.active_projects.discard(project_id)
        
        await self._save_data()
        await self._emit_event("project_removed", {"project_id": project_id})
        
        return True
    
    # Analysis API leveraging existing graph-sitter capabilities
    async def analyze_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Run analysis on a project using existing graph-sitter analysis"""
        if project_id not in self.analyzers:
            return None
        
        execution_id = f"analysis_{project_id}_{int(datetime.utcnow().timestamp())}"
        execution = FlowExecution(
            id=execution_id,
            project_id=project_id,
            flow_type="analysis",
            status=FlowStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        self.executions[execution_id] = execution
        self.running_executions[execution_id] = execution
        
        try:
            analyzer = self.analyzers[project_id]
            
            # Use existing comprehensive analysis
            report = analyzer.run_full_analysis()
            
            # Format for our API
            result = {
                "project_id": project_id,
                "health_score": report.health_score,
                "summary": report.summary,
                "metrics": report.metrics,
                "issues": report.issues,
                "recommendations": report.recommendations,
                "timestamp": report.timestamp
            }
            
            execution.status = FlowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.result = result
            
            # Check quality gates
            await self._check_quality_gates(project_id, result)
            
            await self._emit_event("analysis_completed", {
                "project_id": project_id,
                "health_score": report.health_score,
                "execution_id": execution_id
            })
            
            return result
            
        except Exception as e:
            execution.status = FlowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)
            
            logger.error(f"Analysis failed for {project_id}: {e}")
            return None
        
        finally:
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
            await self._save_data()
    
    # Quality Gates API
    async def add_quality_gate(self, gate: QualityGate) -> bool:
        """Add a quality gate"""
        try:
            self.quality_gates[gate.id] = gate
            await self._save_data()
            
            logger.info(f"Added quality gate: {gate.name} for project {gate.project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add quality gate: {e}")
            return False
    
    async def get_quality_gates(self, project_id: Optional[str] = None) -> List[QualityGate]:
        """Get quality gates"""
        gates = list(self.quality_gates.values())
        if project_id:
            gates = [g for g in gates if g.project_id == project_id]
        return gates
    
    async def _check_quality_gates(self, project_id: str, analysis_result: Dict[str, Any]) -> None:
        """Check quality gates for a project"""
        gates = await self.get_quality_gates(project_id)
        
        for gate in gates:
            if not gate.enabled:
                continue
            
            gate_passed = await self._evaluate_quality_gate(gate, analysis_result)
            
            await self._emit_event("quality_gate_checked", {
                "project_id": project_id,
                "gate_id": gate.id,
                "gate_name": gate.name,
                "passed": gate_passed,
                "analysis_result": analysis_result
            })
            
            if not gate_passed:
                await self._execute_quality_gate_actions(gate, analysis_result)
    
    async def _evaluate_quality_gate(self, gate: QualityGate, analysis_result: Dict[str, Any]) -> bool:
        """Evaluate if a quality gate passes"""
        try:
            for condition_key, condition_value in gate.conditions.items():
                if condition_key == "health_score":
                    health_score = analysis_result.get("health_score", 0)
                    if "min" in condition_value and health_score < condition_value["min"]:
                        return False
                    if "max" in condition_value and health_score > condition_value["max"]:
                        return False
                
                elif condition_key == "issues_count":
                    issues_count = len(analysis_result.get("issues", []))
                    if "max" in condition_value and issues_count > condition_value["max"]:
                        return False
                
                # Add more condition types as needed
            
            return True
        except Exception as e:
            logger.error(f"Error evaluating quality gate {gate.id}: {e}")
            return False
    
    async def _execute_quality_gate_actions(self, gate: QualityGate, analysis_result: Dict[str, Any]) -> None:
        """Execute actions when quality gate fails"""
        for action in gate.actions:
            try:
                if action == "create_linear_issue" and self.codegen_agent:
                    await self._create_linear_issue_for_quality_gate(gate, analysis_result)
                elif action == "block_deployment":
                    await self._emit_event("deployment_blocked", {
                        "project_id": gate.project_id,
                        "gate_id": gate.id,
                        "reason": "Quality gate failed"
                    })
                elif action == "notify_team":
                    await self._emit_event("team_notification", {
                        "project_id": gate.project_id,
                        "gate_id": gate.id,
                        "message": f"Quality gate '{gate.name}' failed"
                    })
            except Exception as e:
                logger.error(f"Failed to execute action {action} for gate {gate.id}: {e}")
    
    async def _create_linear_issue_for_quality_gate(self, gate: QualityGate, analysis_result: Dict[str, Any]) -> None:
        """Create Linear issue when quality gate fails"""
        if not self.codegen_agent:
            return
        
        project = self.projects.get(gate.project_id)
        if not project:
            return
        
        # Create issue description
        issues = analysis_result.get("issues", [])
        recommendations = analysis_result.get("recommendations", [])
        health_score = analysis_result.get("health_score", 0)
        
        description = f"""
Quality gate '{gate.name}' failed for project {project.name}.

**Health Score:** {health_score:.1f}/100

**Issues Found:** {len(issues)}
{chr(10).join([f"- {issue.get('description', 'Unknown issue')}" for issue in issues[:5]])}

**Recommendations:**
{chr(10).join([f"- {rec}" for rec in recommendations[:3]])}

**Quality Gate Conditions:**
{json.dumps(gate.conditions, indent=2)}
        """
        
        prompt = f"""
Create a Linear issue for a failed quality gate:

Title: Quality Gate Failed: {gate.name} - {project.name}
Description: {description}

Please create this issue and assign it to the appropriate team member.
        """
        
        try:
            task = self.codegen_agent.run(prompt=prompt)
            # Don't wait for completion, let it run in background
            logger.info(f"Created Linear issue task for quality gate {gate.id}")
        except Exception as e:
            logger.error(f"Failed to create Linear issue task: {e}")
    
    # Codegen Integration API
    async def execute_codegen_task(self, project_id: str, prompt: str, triggered_by: str = "user") -> Optional[str]:
        """Execute a Codegen task for a project"""
        if not self.codegen_agent:
            logger.error("Codegen agent not available")
            return None
        
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return None
        
        execution_id = f"codegen_{project_id}_{int(datetime.utcnow().timestamp())}"
        execution = FlowExecution(
            id=execution_id,
            project_id=project_id,
            flow_type="codegen_task",
            status=FlowStatus.RUNNING,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by
        )
        
        self.executions[execution_id] = execution
        self.running_executions[execution_id] = execution
        
        try:
            project = self.projects[project_id]
            
            # Add project context to prompt
            context_prompt = f"""
Project: {project.name}
Path: {project.path}
Type: {project.type.value}
Description: {project.description}

Task: {prompt}
            """
            
            task = self.codegen_agent.run(prompt=context_prompt)
            
            # Wait for completion with timeout
            max_wait = 300  # 5 minutes
            waited = 0
            while task.status not in ["completed", "failed"] and waited < max_wait:
                await asyncio.sleep(5)
                task.refresh()
                waited += 5
            
            if task.status == "completed":
                execution.status = FlowStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.result = {"codegen_result": task.result}
                
                await self._emit_event("codegen_task_completed", {
                    "project_id": project_id,
                    "execution_id": execution_id,
                    "result": task.result
                })
                
                return execution_id
            else:
                execution.status = FlowStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.error = f"Codegen task failed or timed out: {task.status}"
                
                return execution_id
                
        except Exception as e:
            execution.status = FlowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)
            
            logger.error(f"Codegen task failed for {project_id}: {e}")
            return execution_id
        
        finally:
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
            await self._save_data()
    
    # Event Streaming API
    async def subscribe_to_events(self) -> asyncio.Queue:
        """Subscribe to real-time events"""
        queue = asyncio.Queue()
        self.event_subscribers.append(queue)
        return queue
    
    def unsubscribe_from_events(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from events"""
        if queue in self.event_subscribers:
            self.event_subscribers.remove(queue)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to all subscribers"""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Send to all subscribers
        for queue in self.event_subscribers[:]:  # Copy list to avoid modification during iteration
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Remove full queues
                self.event_subscribers.remove(queue)
            except Exception as e:
                logger.error(f"Error sending event to subscriber: {e}")
                self.event_subscribers.remove(queue)
    
    # Status and Monitoring API
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "projects": {
                "total": len(self.projects),
                "active": len(self.active_projects)
            },
            "quality_gates": {
                "total": len(self.quality_gates),
                "enabled": len([g for g in self.quality_gates.values() if g.enabled])
            },
            "executions": {
                "total": len(self.executions),
                "running": len(self.running_executions),
                "completed": len([e for e in self.executions.values() if e.status == FlowStatus.COMPLETED]),
                "failed": len([e for e in self.executions.values() if e.status == FlowStatus.FAILED])
            },
            "codegen_available": self.codegen_agent is not None,
            "event_subscribers": len(self.event_subscribers)
        }
    
    async def get_executions(self, project_id: Optional[str] = None, limit: int = 50) -> List[FlowExecution]:
        """Get execution history"""
        executions = list(self.executions.values())
        if project_id:
            executions = [e for e in executions if e.project_id == project_id]
        
        # Sort by start time, most recent first
        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]
    
    # Background Tasks
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                # Monitor project health
                for project_id in self.active_projects:
                    await self._monitor_project_health(project_id)
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)
    
    async def _event_stream_loop(self) -> None:
        """Background event streaming loop"""
        while True:
            try:
                # Clean up closed queues
                self.event_subscribers = [q for q in self.event_subscribers if not q.empty() or q.qsize() < 100]
                
                await asyncio.sleep(60)  # Cleanup every minute
            except Exception as e:
                logger.error(f"Error in event stream loop: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_project_health(self, project_id: str) -> None:
        """Monitor individual project health"""
        try:
            # Run periodic analysis for active projects
            if project_id in self.analyzers:
                # Check if we need to run analysis (e.g., every hour)
                recent_executions = [
                    e for e in self.executions.values()
                    if e.project_id == project_id and 
                    e.flow_type == "analysis" and
                    (datetime.utcnow() - e.started_at).total_seconds() < 3600
                ]
                
                if not recent_executions:
                    logger.info(f"Running periodic health check for {project_id}")
                    await self.analyze_project(project_id)
        except Exception as e:
            logger.error(f"Error monitoring project {project_id}: {e}")
    
    # Data Persistence
    async def _save_data(self) -> None:
        """Save data to disk"""
        try:
            data = {
                "projects": {pid: asdict(project) for pid, project in self.projects.items()},
                "quality_gates": {gid: asdict(gate) for gid, gate in self.quality_gates.items()},
                "executions": {eid: asdict(execution) for eid, execution in self.executions.items()},
                "active_projects": list(self.active_projects)
            }
            
            # Convert datetime objects to ISO strings
            data = self._serialize_datetime_objects(data)
            
            async with aiofiles.open(self.data_dir / "core_multi_project_data.json", "w") as f:
                await f.write(json.dumps(data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    async def _load_data(self) -> None:
        """Load data from disk"""
        try:
            data_file = self.data_dir / "core_multi_project_data.json"
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
                project = ProjectConfig(**project_data)
                self.projects[pid] = project
                
                # Recreate analyzer if project path exists
                try:
                    if Path(project.path).exists():
                        codebase = Codebase(project.path)
                        self.analyzers[pid] = EnhancedCodebaseAnalyzer(codebase, pid)
                except Exception as e:
                    logger.warning(f"Could not create analyzer for project {pid}: {e}")
            
            # Load quality gates
            for gid, gate_data in data.get("quality_gates", {}).items():
                self.quality_gates[gid] = QualityGate(**gate_data)
            
            # Load executions
            for eid, exec_data in data.get("executions", {}).items():
                exec_data["status"] = FlowStatus(exec_data["status"])
                self.executions[eid] = FlowExecution(**exec_data)
            
            # Load active projects
            self.active_projects = set(data.get("active_projects", []))
            
            logger.info(f"Loaded {len(self.projects)} projects, {len(self.quality_gates)} quality gates")
            
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


# Chat Integration Helper
async def handle_chat_command(
    manager: CoreMultiProjectManager,
    message: str,
    project_id: Optional[str] = None,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Handle chat commands for multi-project management"""
    message_lower = message.lower()
    
    if "analyze" in message_lower and project_id:
        result = await manager.analyze_project(project_id)
        if result:
            health_score = result.get("health_score", 0)
            issues_count = len(result.get("issues", []))
            return {
                "message": f"🔍 Analysis completed for project {project_id}\n• Health Score: {health_score:.1f}/100\n• Issues Found: {issues_count}",
                "type": "success",
                "data": result
            }
        else:
            return {
                "message": f"❌ Failed to analyze project {project_id}",
                "type": "error"
            }
    
    elif "create" in message_lower and "issue" in message_lower and project_id:
        if manager.codegen_agent:
            execution_id = await manager.execute_codegen_task(
                project_id=project_id,
                prompt=f"Create a Linear issue based on this request: {message}",
                triggered_by=user_email or "chat_user"
            )
            return {
                "message": f"🎫 Creating Linear issue for project {project_id}...",
                "type": "success",
                "execution_id": execution_id
            }
        else:
            return {
                "message": "❌ Codegen agent not available for Linear integration",
                "type": "error"
            }
    
    elif "status" in message_lower:
        if project_id:
            project = await manager.get_project(project_id)
            executions = await manager.get_executions(project_id, limit=5)
            running = [e for e in executions if e.status == FlowStatus.RUNNING]
            
            return {
                "message": f"📊 Project Status: {project.name if project else 'Unknown'}\n• Running Executions: {len(running)}\n• Recent Executions: {len(executions)}",
                "type": "status",
                "data": {"project": project, "executions": executions}
            }
        else:
            status = await manager.get_system_status()
            return {
                "message": f"📊 System Status\n• Projects: {status['projects']['total']}\n• Running Executions: {status['executions']['running']}\n• Quality Gates: {status['quality_gates']['total']}",
                "type": "status",
                "data": status
            }
    
    elif "quality gate" in message_lower and project_id:
        gates = await manager.get_quality_gates(project_id)
        return {
            "message": f"🚪 Quality Gates for project {project_id}: {len(gates)} configured",
            "type": "info",
            "data": {"gates": gates}
        }
    
    else:
        return {
            "message": "Available commands:\n• 'analyze' - Run code analysis\n• 'create issue' - Create Linear issue\n• 'status' - Show status\n• 'quality gate' - Show quality gates",
            "type": "help"
        }

