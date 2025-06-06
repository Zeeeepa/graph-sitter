"""
Codegen SDK integration for the Dashboard extension.

This module provides integration with the Codegen SDK for automated plan generation,
task breakdown, and AI-powered development workflow orchestration.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from codegen import Agent
    CODEGEN_AVAILABLE = True
except ImportError:
    CODEGEN_AVAILABLE = False
    Agent = None

from .models import WorkflowPlan, WorkflowTask, TaskStatus

logger = logging.getLogger(__name__)


class CodegenPlanGenerator:
    """Codegen SDK integration for automated plan generation."""
    
    def __init__(self, org_id: Optional[str] = None, token: Optional[str] = None):
        """Initialize Codegen plan generator.
        
        Args:
            org_id: Codegen organization ID. If None, uses environment variable.
            token: Codegen API token. If None, uses environment variable.
        """
        self.org_id = org_id or os.getenv("CODEGEN_ORG_ID")
        self.token = token or os.getenv("CODEGEN_TOKEN")
        self.agent = None
        
        if not self.org_id or not self.token:
            logger.warning("Codegen credentials not provided. Plan generation may not work.")
    
    async def initialize(self):
        """Initialize the Codegen agent."""
        if CODEGEN_AVAILABLE and self.org_id and self.token:
            try:
                self.agent = Agent(org_id=self.org_id, token=self.token)
                logger.info("Codegen plan generator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Codegen agent: {e}")
                self.agent = None
        else:
            logger.warning("Codegen plan generator not fully initialized (missing dependencies or credentials)")
    
    async def generate_plan(
        self, 
        project_id: str, 
        requirements: str, 
        title: str, 
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a workflow plan using Codegen SDK.
        
        Args:
            project_id: Project ID for context
            requirements: User requirements text
            title: Plan title
            description: Plan description
            context: Additional context information
            
        Returns:
            Generated plan dictionary
        """
        if not self.agent:
            logger.warning("Codegen agent not available, generating fallback plan")
            return await self._generate_fallback_plan(requirements, title, description)
        
        try:
            # Construct the prompt for Codegen
            prompt = self._build_plan_prompt(requirements, title, description, context)
            
            # Run the Codegen agent
            task = self.agent.run(prompt=prompt)
            
            # Wait for completion (with timeout)
            max_attempts = 30  # 5 minutes with 10-second intervals
            attempts = 0
            
            while attempts < max_attempts:
                task.refresh()
                
                if task.status == "completed":
                    result = task.result
                    logger.info(f"Codegen plan generation completed for project {project_id}")
                    return await self._parse_codegen_result(result, requirements)
                elif task.status == "failed":
                    logger.error(f"Codegen plan generation failed: {task.result}")
                    break
                
                attempts += 1
                await asyncio.sleep(10)  # Wait 10 seconds before checking again
            
            # If we reach here, the task didn't complete in time
            logger.warning("Codegen plan generation timed out, generating fallback plan")
            return await self._generate_fallback_plan(requirements, title, description)
            
        except Exception as e:
            logger.error(f"Failed to generate plan with Codegen: {e}")
            return await self._generate_fallback_plan(requirements, title, description)
    
    def _build_plan_prompt(
        self, 
        requirements: str, 
        title: str, 
        description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for Codegen plan generation.
        
        Args:
            requirements: User requirements
            title: Plan title
            description: Plan description
            context: Additional context
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
Create a comprehensive development plan for the following project:

Title: {title}
Description: {description}

Requirements:
{requirements}

Please create a detailed plan that includes:

1. **Task Breakdown**: Break down the requirements into specific, actionable tasks
2. **Dependencies**: Identify task dependencies and execution order
3. **Estimates**: Provide time estimates for each task
4. **Implementation Strategy**: Suggest implementation approaches
5. **Quality Gates**: Define validation and testing requirements
6. **Risk Assessment**: Identify potential risks and mitigation strategies

Format the response as a structured plan with:
- Clear task titles and descriptions
- Priority levels (1-5)
- Estimated hours for each task
- Task types (code, review, test, deploy, etc.)
- Dependencies between tasks
- Acceptance criteria for each task

Focus on creating a plan that can be executed through automated workflows with GitHub PR creation, Linear issue management, and quality validation.
"""
        
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"
        
        return prompt
    
    async def _parse_codegen_result(self, result: str, requirements: str) -> Dict[str, Any]:
        """Parse Codegen result into structured plan format.
        
        Args:
            result: Raw result from Codegen
            requirements: Original requirements
            
        Returns:
            Structured plan dictionary
        """
        try:
            # TODO: Implement sophisticated parsing of Codegen result
            # For now, create a structured plan based on the result
            
            plan = {
                "generated_by": "codegen",
                "timestamp": datetime.utcnow().isoformat(),
                "raw_result": result,
                "requirements": requirements,
                "tasks": await self._extract_tasks_from_result(result),
                "summary": await self._extract_summary_from_result(result),
                "complexity_score": await self._calculate_complexity_score(result),
                "estimated_duration": await self._extract_duration_from_result(result),
                "risk_assessment": await self._extract_risks_from_result(result)
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to parse Codegen result: {e}")
            return await self._generate_fallback_plan(requirements, "Generated Plan", "AI-generated plan")
    
    async def _extract_tasks_from_result(self, result: str) -> List[Dict[str, Any]]:
        """Extract tasks from Codegen result.
        
        Args:
            result: Codegen result text
            
        Returns:
            List of task dictionaries
        """
        # TODO: Implement sophisticated task extraction
        # For now, create sample tasks based on common patterns
        
        tasks = [
            {
                "title": "Setup Project Structure",
                "description": "Initialize project structure and dependencies",
                "task_type": "setup",
                "priority": 1,
                "estimated_hours": 2.0,
                "dependencies": [],
                "acceptance_criteria": ["Project structure created", "Dependencies installed"]
            },
            {
                "title": "Implement Core Features",
                "description": "Develop main functionality based on requirements",
                "task_type": "code",
                "priority": 2,
                "estimated_hours": 8.0,
                "dependencies": ["Setup Project Structure"],
                "acceptance_criteria": ["Core features implemented", "Unit tests written"]
            },
            {
                "title": "Code Review and Testing",
                "description": "Review code quality and run comprehensive tests",
                "task_type": "review",
                "priority": 3,
                "estimated_hours": 4.0,
                "dependencies": ["Implement Core Features"],
                "acceptance_criteria": ["Code review completed", "All tests passing"]
            },
            {
                "title": "Documentation and Deployment",
                "description": "Create documentation and deploy to production",
                "task_type": "deploy",
                "priority": 4,
                "estimated_hours": 3.0,
                "dependencies": ["Code Review and Testing"],
                "acceptance_criteria": ["Documentation complete", "Successfully deployed"]
            }
        ]
        
        return tasks
    
    async def _extract_summary_from_result(self, result: str) -> str:
        """Extract summary from Codegen result."""
        # TODO: Implement summary extraction
        return "AI-generated development plan with automated task breakdown and workflow orchestration."
    
    async def _calculate_complexity_score(self, result: str) -> float:
        """Calculate complexity score from Codegen result."""
        # TODO: Implement complexity calculation
        return 3.5  # Medium complexity
    
    async def _extract_duration_from_result(self, result: str) -> int:
        """Extract estimated duration from Codegen result."""
        # TODO: Implement duration extraction
        return 17  # Total hours from sample tasks
    
    async def _extract_risks_from_result(self, result: str) -> List[str]:
        """Extract risk assessment from Codegen result."""
        # TODO: Implement risk extraction
        return [
            "Dependency conflicts may arise during setup",
            "Complex requirements may require additional clarification",
            "Testing coverage may need enhancement"
        ]
    
    async def _generate_fallback_plan(self, requirements: str, title: str, description: str) -> Dict[str, Any]:
        """Generate a fallback plan when Codegen is not available.
        
        Args:
            requirements: User requirements
            title: Plan title
            description: Plan description
            
        Returns:
            Fallback plan dictionary
        """
        logger.info("Generating fallback plan")
        
        # Analyze requirements to create basic task breakdown
        tasks = await self._analyze_requirements_for_tasks(requirements)
        
        plan = {
            "generated_by": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
            "requirements": requirements,
            "title": title,
            "description": description,
            "tasks": tasks,
            "summary": f"Basic plan generated for: {title}",
            "complexity_score": 2.5,
            "estimated_duration": sum(task.get("estimated_hours", 2) for task in tasks),
            "risk_assessment": [
                "Plan generated without AI assistance",
                "May require manual refinement",
                "Task breakdown may need adjustment"
            ]
        }
        
        return plan
    
    async def _analyze_requirements_for_tasks(self, requirements: str) -> List[Dict[str, Any]]:
        """Analyze requirements text to generate basic tasks.
        
        Args:
            requirements: Requirements text
            
        Returns:
            List of basic task dictionaries
        """
        # Simple keyword-based task generation
        tasks = []
        
        # Common development phases
        base_tasks = [
            {
                "title": "Requirements Analysis",
                "description": "Analyze and clarify project requirements",
                "task_type": "analysis",
                "priority": 1,
                "estimated_hours": 2.0,
                "dependencies": []
            },
            {
                "title": "Design and Planning",
                "description": "Create technical design and implementation plan",
                "task_type": "design",
                "priority": 2,
                "estimated_hours": 4.0,
                "dependencies": ["Requirements Analysis"]
            },
            {
                "title": "Implementation",
                "description": "Implement the required functionality",
                "task_type": "code",
                "priority": 3,
                "estimated_hours": 8.0,
                "dependencies": ["Design and Planning"]
            },
            {
                "title": "Testing and Validation",
                "description": "Test implementation and validate requirements",
                "task_type": "test",
                "priority": 4,
                "estimated_hours": 4.0,
                "dependencies": ["Implementation"]
            }
        ]
        
        # Add specific tasks based on keywords in requirements
        requirements_lower = requirements.lower()
        
        if "api" in requirements_lower or "endpoint" in requirements_lower:
            tasks.append({
                "title": "API Development",
                "description": "Develop API endpoints and documentation",
                "task_type": "code",
                "priority": 3,
                "estimated_hours": 6.0,
                "dependencies": ["Design and Planning"]
            })
        
        if "database" in requirements_lower or "data" in requirements_lower:
            tasks.append({
                "title": "Database Setup",
                "description": "Design and implement database schema",
                "task_type": "code",
                "priority": 2,
                "estimated_hours": 4.0,
                "dependencies": ["Design and Planning"]
            })
        
        if "ui" in requirements_lower or "frontend" in requirements_lower or "interface" in requirements_lower:
            tasks.append({
                "title": "Frontend Development",
                "description": "Develop user interface components",
                "task_type": "code",
                "priority": 3,
                "estimated_hours": 8.0,
                "dependencies": ["Design and Planning"]
            })
        
        if "test" in requirements_lower or "testing" in requirements_lower:
            tasks.append({
                "title": "Automated Testing",
                "description": "Implement automated test suite",
                "task_type": "test",
                "priority": 4,
                "estimated_hours": 6.0,
                "dependencies": ["Implementation"]
            })
        
        # Combine base tasks with specific tasks
        all_tasks = base_tasks + tasks
        
        # Add acceptance criteria to all tasks
        for task in all_tasks:
            if "acceptance_criteria" not in task:
                task["acceptance_criteria"] = [
                    f"{task['title']} completed successfully",
                    "Code review passed",
                    "Documentation updated"
                ]
        
        return all_tasks
    
    async def create_linear_issues_from_plan(self, plan: Dict[str, Any], project_id: str) -> List[str]:
        """Create Linear issues from a generated plan.
        
        Args:
            plan: Generated plan dictionary
            project_id: Project ID for context
            
        Returns:
            List of created Linear issue IDs
        """
        # TODO: Implement Linear issue creation
        # This would integrate with the Linear extension to create issues
        logger.info(f"Creating Linear issues for plan in project {project_id}")
        return []
    
    async def create_github_issues_from_plan(self, plan: Dict[str, Any], owner: str, repo: str) -> List[str]:
        """Create GitHub issues from a generated plan.
        
        Args:
            plan: Generated plan dictionary
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of created GitHub issue IDs
        """
        # TODO: Implement GitHub issue creation
        # This would integrate with the GitHub integration to create issues
        logger.info(f"Creating GitHub issues for plan in {owner}/{repo}")
        return []

