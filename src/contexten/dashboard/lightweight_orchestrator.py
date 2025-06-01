"""
Lightweight CI/CD Orchestrator

A focused orchestration system that leverages graph-sitter's existing advanced
analysis capabilities without duplicating functionality. Focuses on workflow
coordination and Codegen SDK integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from codegen import Agent as CodegenAgent
from graph_sitter import Codebase
from graph_sitter.analysis import EnhancedCodebaseAnalyzer
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WorkflowType(str, Enum):
    """Simple workflow types focused on orchestration"""
    CODE_ANALYSIS = "code_analysis"
    CODEGEN_TASK = "codegen_task"
    CUSTOM = "custom"


@dataclass
class SimpleWorkflow:
    """Lightweight workflow definition"""
    id: str
    name: str
    type: WorkflowType
    project_path: str
    codegen_prompt: str
    auto_trigger: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WorkflowExecution:
    """Simple execution tracking"""
    id: str
    workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


class LightweightOrchestrator:
    """
    Focused orchestrator that leverages existing graph-sitter analysis
    capabilities and provides Codegen SDK integration for workflow automation.
    """
    
    def __init__(
        self,
        codegen_org_id: Optional[str] = None,
        codegen_token: Optional[str] = None
    ):
        self.codegen_org_id = codegen_org_id
        self.codegen_token = codegen_token
        self.codegen_agent: Optional[CodegenAgent] = None
        
        # Simple storage
        self.workflows: Dict[str, SimpleWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.project_analyzers: Dict[str, EnhancedCodebaseAnalyzer] = {}
        
        # Background task
        self._monitoring_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the lightweight orchestrator"""
        logger.info("Starting Lightweight Orchestrator...")
        
        # Initialize Codegen SDK if available
        if self.codegen_org_id and self.codegen_token:
            try:
                self.codegen_agent = CodegenAgent(
                    org_id=self.codegen_org_id,
                    token=self.codegen_token
                )
                logger.info("Codegen SDK initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Codegen SDK: {e}")
        
        # Start monitoring
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Lightweight Orchestrator started")
    
    async def stop(self) -> None:
        """Stop the orchestrator"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Lightweight Orchestrator stopped")
    
    def add_project(self, project_id: str, project_path: str) -> bool:
        """Add a project for analysis"""
        try:
            codebase = Codebase(project_path)
            analyzer = EnhancedCodebaseAnalyzer(codebase, project_id)
            self.project_analyzers[project_id] = analyzer
            logger.info(f"Added project: {project_id} at {project_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to add project {project_id}: {e}")
            return False
    
    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        workflow_type: WorkflowType,
        project_path: str,
        codegen_prompt: str,
        auto_trigger: bool = False
    ) -> bool:
        """Create a simple workflow"""
        try:
            workflow = SimpleWorkflow(
                id=workflow_id,
                name=name,
                type=workflow_type,
                project_path=project_path,
                codegen_prompt=codegen_prompt,
                auto_trigger=auto_trigger
            )
            self.workflows[workflow_id] = workflow
            logger.info(f"Created workflow: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str) -> Optional[str]:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return None
        
        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{int(datetime.utcnow().timestamp())}"
        
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow()
        )
        self.executions[execution_id] = execution
        
        try:
            if workflow.type == WorkflowType.CODE_ANALYSIS:
                result = await self._execute_analysis_workflow(workflow)
            elif workflow.type == WorkflowType.CODEGEN_TASK:
                result = await self._execute_codegen_workflow(workflow)
            else:
                result = await self._execute_custom_workflow(workflow)
            
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.result = result
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            return execution_id
            
        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)
            
            logger.error(f"Workflow {workflow_id} failed: {e}")
            return execution_id
    
    async def _execute_analysis_workflow(self, workflow: SimpleWorkflow) -> str:
        """Execute code analysis using existing graph-sitter capabilities"""
        try:
            # Use existing graph-sitter analysis
            codebase = Codebase(workflow.project_path)
            analyzer = EnhancedCodebaseAnalyzer(codebase)
            
            # Run the comprehensive analysis that already exists
            report = analyzer.run_full_analysis()
            
            # Format results for dashboard
            result = {
                "analysis_type": "comprehensive",
                "health_score": report.health_score,
                "summary": report.summary,
                "issues_count": len(report.issues),
                "recommendations_count": len(report.recommendations),
                "timestamp": report.timestamp
            }
            
            return f"Analysis completed. Health Score: {report.health_score:.1f}/100"
            
        except Exception as e:
            logger.error(f"Analysis workflow failed: {e}")
            raise
    
    async def _execute_codegen_workflow(self, workflow: SimpleWorkflow) -> str:
        """Execute Codegen SDK task"""
        if not self.codegen_agent:
            raise Exception("Codegen SDK not available")
        
        try:
            # Add project context to the prompt
            codebase = Codebase(workflow.project_path)
            
            # Get basic project info for context
            context_prompt = f"""
            Project Analysis Context:
            - Total Files: {len(codebase.files)}
            - Total Functions: {len(codebase.functions)}
            - Total Classes: {len(codebase.classes)}
            
            Task: {workflow.codegen_prompt}
            """
            
            # Execute with Codegen SDK
            task = self.codegen_agent.run(prompt=context_prompt)
            
            # Wait for completion with timeout
            max_wait = 300  # 5 minutes
            waited = 0
            while task.status not in ["completed", "failed"] and waited < max_wait:
                await asyncio.sleep(5)
                task.refresh()
                waited += 5
            
            if task.status == "completed":
                return f"Codegen task completed: {task.result}"
            else:
                raise Exception(f"Codegen task failed or timed out: {task.status}")
                
        except Exception as e:
            logger.error(f"Codegen workflow failed: {e}")
            raise
    
    async def _execute_custom_workflow(self, workflow: SimpleWorkflow) -> str:
        """Execute custom workflow"""
        # For custom workflows, just use Codegen SDK with the prompt
        return await self._execute_codegen_workflow(workflow)
    
    async def get_project_analysis(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis for a project using existing capabilities"""
        if project_id not in self.project_analyzers:
            return None
        
        try:
            analyzer = self.project_analyzers[project_id]
            report = analyzer.run_full_analysis()
            
            return {
                "project_id": project_id,
                "health_score": report.health_score,
                "summary": report.summary,
                "metrics": report.metrics,
                "issues": report.issues,
                "recommendations": report.recommendations,
                "timestamp": report.timestamp
            }
        except Exception as e:
            logger.error(f"Failed to get analysis for {project_id}: {e}")
            return None
    
    async def trigger_analysis_for_project(self, project_id: str) -> Optional[str]:
        """Trigger analysis workflow for a project"""
        if project_id not in self.project_analyzers:
            return None
        
        analyzer = self.project_analyzers[project_id]
        workflow_id = f"analysis_{project_id}_{int(datetime.utcnow().timestamp())}"
        
        # Create and execute analysis workflow
        success = self.create_workflow(
            workflow_id=workflow_id,
            name=f"Analysis for {project_id}",
            workflow_type=WorkflowType.CODE_ANALYSIS,
            project_path=analyzer.codebase.root_path,
            codegen_prompt=f"Analyze project {project_id} for code quality and issues"
        )
        
        if success:
            return await self.execute_workflow(workflow_id)
        return None
    
    def get_workflows(self) -> List[SimpleWorkflow]:
        """Get all workflows"""
        return list(self.workflows.values())
    
    def get_executions(self, workflow_id: Optional[str] = None) -> List[WorkflowExecution]:
        """Get executions, optionally filtered by workflow"""
        executions = list(self.executions.values())
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        return sorted(executions, key=lambda x: x.started_at, reverse=True)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get simple system status"""
        running_executions = [e for e in self.executions.values() if e.status == "running"]
        completed_executions = [e for e in self.executions.values() if e.status == "completed"]
        failed_executions = [e for e in self.executions.values() if e.status == "failed"]
        
        return {
            "projects": len(self.project_analyzers),
            "workflows": len(self.workflows),
            "executions": {
                "total": len(self.executions),
                "running": len(running_executions),
                "completed": len(completed_executions),
                "failed": len(failed_executions)
            },
            "codegen_available": self.codegen_agent is not None
        }
    
    async def _monitoring_loop(self) -> None:
        """Simple monitoring loop"""
        while True:
            try:
                # Check for auto-trigger workflows
                for workflow in self.workflows.values():
                    if workflow.auto_trigger:
                        # Simple auto-trigger logic - could be enhanced
                        recent_executions = [
                            e for e in self.executions.values()
                            if e.workflow_id == workflow.id and
                            (datetime.utcnow() - e.started_at).total_seconds() < 3600
                        ]
                        
                        if not recent_executions:
                            logger.info(f"Auto-triggering workflow: {workflow.name}")
                            await self.execute_workflow(workflow.id)
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)


# Chat interface helpers
async def handle_chat_command(
    orchestrator: LightweightOrchestrator,
    message: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Handle simple chat commands"""
    message_lower = message.lower()
    
    if "analyze" in message_lower and project_id:
        execution_id = await orchestrator.trigger_analysis_for_project(project_id)
        if execution_id:
            return {
                "message": f"🔍 Started analysis for project {project_id}",
                "execution_id": execution_id,
                "type": "success"
            }
        else:
            return {
                "message": f"❌ Failed to start analysis for project {project_id}",
                "type": "error"
            }
    
    elif "status" in message_lower:
        status = orchestrator.get_system_status()
        return {
            "message": f"📊 System Status:\n• Projects: {status['projects']}\n• Workflows: {status['workflows']}\n• Running: {status['executions']['running']}",
            "type": "status",
            "data": status
        }
    
    elif "create" in message_lower and "workflow" in message_lower:
        return {
            "message": "To create a workflow, please specify:\n• Project path\n• Workflow type (analysis/codegen/custom)\n• Task description",
            "type": "help"
        }
    
    else:
        return {
            "message": "Available commands:\n• 'analyze' - Run code analysis\n• 'status' - Show system status\n• 'create workflow' - Create new workflow",
            "type": "help"
        }

