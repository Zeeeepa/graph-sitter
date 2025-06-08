"""
Codegen SDK Planning Engine for Single-User Dashboard

AI-powered planning using Codegen SDK with direct API integration.
Takes requirements text, calls Codegen API, parses response into actionable tasks.
"""

import logging
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardPlan, DashboardTask, TaskStatus, GraphSitterAnalysis
from ..codegen.codegen import Codegen

logger = get_logger(__name__)


class PlanningEngine:
    """
    Handles plan generation using Codegen SDK with analysis context.
    
    Features:
    - AI-powered plan generation from requirements
    - Integration with Graph-sitter analysis for context
    - Task breakdown and dependency analysis
    - Direct Codegen SDK integration
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.plans: Dict[str, DashboardPlan] = {}
        self.codegen: Optional[Codegen] = None
        
    async def initialize(self):
        """Initialize the planning engine"""
        logger.info("Initializing PlanningEngine...")
        
        # Get Codegen integration
        if self.dashboard.settings_manager.is_extension_enabled("codegen"):
            org_id = self.dashboard.settings_manager.get_api_credential("codegen_org_id")
            token = self.dashboard.settings_manager.get_api_credential("codegen_token")
            
            if org_id and token:
                self.codegen = Codegen({
                    "org_id": org_id,
                    "api_token": token
                })
                await self.codegen.initialize()
                logger.info("Codegen SDK integration initialized")
            else:
                logger.warning("Codegen credentials not configured")
        else:
            logger.warning("Codegen extension disabled")
            
    async def generate_plan(self, project_id: str, requirements: str, analysis: Optional[GraphSitterAnalysis] = None) -> Optional[DashboardPlan]:
        """
        Generate a plan using Codegen SDK
        
        Args:
            project_id: Project ID to generate plan for
            requirements: User requirements text
            analysis: Optional Graph-sitter analysis for context
            
        Returns:
            Generated plan or None if failed
        """
        try:
            logger.info(f"Generating plan for project {project_id}")
            
            # Get project details
            project = await self.dashboard.project_manager.get_project(project_id)
            if not project:
                logger.error(f"Project not found: {project_id}")
                return None
                
            # Create plan ID
            plan_id = f"plan_{project_id}_{int(datetime.now().timestamp())}"
            
            # Build context for Codegen
            context = self._build_planning_context(project, requirements, analysis)
            
            # Generate plan using Codegen SDK
            if self.codegen:
                codegen_response = await self._call_codegen_api(context)
                if not codegen_response:
                    logger.error("Failed to get response from Codegen API")
                    return None
            else:
                # Fallback: create a simple plan without Codegen
                logger.warning("Codegen not available, creating simple plan")
                codegen_response = self._create_fallback_plan(requirements, analysis)
                
            # Parse response into tasks
            tasks = self._parse_codegen_response(plan_id, project_id, codegen_response)
            
            # Create plan
            plan = DashboardPlan(
                plan_id=plan_id,
                project_id=project_id,
                title=f"Plan for {project.name}",
                description=f"Generated plan based on requirements: {requirements[:100]}...",
                requirements=requirements,
                status="draft",
                tasks=tasks,
                codegen_response=codegen_response,
                based_on_analysis=analysis.project_id if analysis else None,
                estimated_duration=sum(task.estimated_duration or 30 for task in tasks)
            )
            
            # Store plan
            self.plans[plan_id] = plan
            
            # Update project
            project.current_plan_id = plan_id
            await self.dashboard.project_manager.update_project_status(project_id, "planned")
            
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "plan_generated",
                "planning_engine",
                project_id=project_id,
                data={
                    "plan_id": plan_id,
                    "task_count": len(tasks),
                    "estimated_duration": plan.estimated_duration
                }
            )
            
            logger.info(f"Generated plan {plan_id} with {len(tasks)} tasks")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            return None
            
    def _build_planning_context(self, project, requirements: str, analysis: Optional[GraphSitterAnalysis]) -> str:
        """Build context string for Codegen API"""
        context_parts = [
            f"Project: {project.name}",
            f"Repository: {project.github_owner}/{project.github_repo}",
            f"Requirements: {requirements}",
            ""
        ]
        
        # Add analysis context if available
        if analysis:
            context_parts.extend([
                "Code Analysis Results:",
                f"- Quality Score: {analysis.quality_score:.2f}",
                f"- Complexity Score: {analysis.complexity_score:.2f}",
                f"- Test Coverage: {analysis.test_coverage:.2f}%",
                ""
            ])
            
            if analysis.errors:
                context_parts.append(f"Found {len(analysis.errors)} code errors:")
                for error in analysis.errors[:5]:  # Limit to first 5
                    context_parts.append(f"  - {error.file_path}:{error.line_number}: {error.message}")
                context_parts.append("")
                
            if analysis.missing_features:
                context_parts.append(f"Missing features identified:")
                for feature in analysis.missing_features[:3]:  # Limit to first 3
                    context_parts.append(f"  - {feature.feature_name}: {feature.description}")
                context_parts.append("")
                
            if analysis.config_issues:
                context_parts.append(f"Configuration issues found:")
                for issue in analysis.config_issues[:3]:  # Limit to first 3
                    context_parts.append(f"  - {issue.config_file}: {issue.message}")
                context_parts.append("")
                
        context_parts.extend([
            "Please create a detailed plan with specific, actionable tasks.",
            "Each task should include:",
            "- Clear title and description",
            "- Task type (code_change, deployment, analysis, testing, etc.)",
            "- Estimated duration in minutes",
            "- Dependencies on other tasks",
            "",
            "Focus on practical implementation steps that can be executed by AI agents."
        ])
        
        return "\n".join(context_parts)
        
    async def _call_codegen_api(self, context: str) -> Dict[str, Any]:
        """Call Codegen API to generate plan"""
        try:
            # Use Codegen SDK to generate plan
            response = await self.codegen.create_task(
                prompt=context,
                task_type="planning"
            )
            
            if response and response.get("success"):
                return {
                    "success": True,
                    "plan": response.get("result", ""),
                    "task_id": response.get("task_id"),
                    "raw_response": response
                }
            else:
                logger.error(f"Codegen API error: {response}")
                return {"success": False, "error": "API call failed"}
                
        except Exception as e:
            logger.error(f"Codegen API call failed: {e}")
            return {"success": False, "error": str(e)}
            
    def _create_fallback_plan(self, requirements: str, analysis: Optional[GraphSitterAnalysis]) -> Dict[str, Any]:
        """Create a simple fallback plan when Codegen is not available"""
        tasks = []
        
        # Basic task structure based on requirements
        if "fix" in requirements.lower() or "bug" in requirements.lower():
            tasks.append({
                "title": "Analyze and Fix Issues",
                "description": "Identify and resolve bugs or issues in the codebase",
                "task_type": "code_change",
                "estimated_duration": 60
            })
            
        if "feature" in requirements.lower() or "add" in requirements.lower():
            tasks.append({
                "title": "Implement New Feature",
                "description": "Develop and integrate the requested feature",
                "task_type": "code_change",
                "estimated_duration": 120
            })
            
        if "test" in requirements.lower():
            tasks.append({
                "title": "Add Tests",
                "description": "Create comprehensive tests for the changes",
                "task_type": "testing",
                "estimated_duration": 45
            })
            
        # Add analysis-based tasks
        if analysis:
            if analysis.errors:
                tasks.append({
                    "title": "Fix Code Errors",
                    "description": f"Resolve {len(analysis.errors)} identified code errors",
                    "task_type": "code_change",
                    "estimated_duration": len(analysis.errors) * 10
                })
                
            if analysis.config_issues:
                tasks.append({
                    "title": "Fix Configuration Issues",
                    "description": f"Resolve {len(analysis.config_issues)} configuration problems",
                    "task_type": "configuration",
                    "estimated_duration": 30
                })
                
        # Default tasks if nothing specific
        if not tasks:
            tasks.extend([
                {
                    "title": "Code Analysis",
                    "description": "Perform comprehensive code analysis",
                    "task_type": "analysis",
                    "estimated_duration": 30
                },
                {
                    "title": "Implement Requirements",
                    "description": "Implement the specified requirements",
                    "task_type": "code_change",
                    "estimated_duration": 90
                },
                {
                    "title": "Testing and Validation",
                    "description": "Test and validate the implementation",
                    "task_type": "testing",
                    "estimated_duration": 45
                }
            ])
            
        return {
            "success": True,
            "plan": "Fallback plan generated based on requirements analysis",
            "tasks": tasks,
            "fallback": True
        }
        
    def _parse_codegen_response(self, plan_id: str, project_id: str, response: Dict[str, Any]) -> List[DashboardTask]:
        """Parse Codegen response into task objects"""
        tasks = []
        
        try:
            if response.get("fallback"):
                # Handle fallback response
                task_data = response.get("tasks", [])
            else:
                # Try to parse Codegen response
                plan_text = response.get("plan", "")
                task_data = self._extract_tasks_from_text(plan_text)
                
            # Create task objects
            for i, task_info in enumerate(task_data):
                task_id = f"task_{plan_id}_{i+1}"
                
                task = DashboardTask(
                    task_id=task_id,
                    project_id=project_id,
                    plan_id=plan_id,
                    title=task_info.get("title", f"Task {i+1}"),
                    description=task_info.get("description", ""),
                    task_type=task_info.get("task_type", "code_change"),
                    status=TaskStatus.PENDING,
                    estimated_duration=task_info.get("estimated_duration", 60),
                    depends_on=task_info.get("depends_on", [])
                )
                
                tasks.append(task)
                
        except Exception as e:
            logger.error(f"Failed to parse Codegen response: {e}")
            # Create a single default task
            tasks.append(DashboardTask(
                task_id=f"task_{plan_id}_1",
                project_id=project_id,
                plan_id=plan_id,
                title="Execute Plan",
                description="Execute the generated plan",
                task_type="code_change",
                status=TaskStatus.PENDING,
                estimated_duration=90
            ))
            
        return tasks
        
    def _extract_tasks_from_text(self, plan_text: str) -> List[Dict[str, Any]]:
        """Extract task information from plan text"""
        tasks = []
        
        # Simple parsing logic - look for numbered lists or bullet points
        lines = plan_text.split('\n')
        current_task = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for task indicators
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('- ', '* ')) or
                line.startswith('Task')):
                
                # Save previous task
                if current_task:
                    tasks.append(current_task)
                    
                # Start new task
                title = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- *')
                current_task = {
                    "title": title,
                    "description": "",
                    "task_type": "code_change",
                    "estimated_duration": 60
                }
            elif current_task and line:
                # Add to description
                current_task["description"] += f" {line}"
                
        # Add last task
        if current_task:
            tasks.append(current_task)
            
        # If no tasks found, create a default one
        if not tasks:
            tasks.append({
                "title": "Execute Plan",
                "description": plan_text[:200] + "..." if len(plan_text) > 200 else plan_text,
                "task_type": "code_change",
                "estimated_duration": 90
            })
            
        return tasks
        
    async def get_plan(self, plan_id: str) -> Optional[DashboardPlan]:
        """Get a plan by ID"""
        return self.plans.get(plan_id)
        
    async def get_project_plans(self, project_id: str) -> List[DashboardPlan]:
        """Get all plans for a project"""
        return [plan for plan in self.plans.values() if plan.project_id == project_id]
        
    async def update_plan_status(self, plan_id: str, status: str) -> bool:
        """Update plan status"""
        try:
            if plan_id not in self.plans:
                return False
                
            plan = self.plans[plan_id]
            old_status = plan.status
            plan.status = status
            
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "plan_status_changed",
                "planning_engine",
                project_id=plan.project_id,
                data={"plan_id": plan_id, "old_status": old_status, "new_status": status}
            )
            
            logger.info(f"Updated plan {plan_id} status: {old_status} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update plan status: {e}")
            return False

