"""
Codegen SDK service with enhanced prompt engineering and real-time monitoring
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from codegen import Agent
from backend.config import settings, PROMPT_TEMPLATES
from backend.database import DatabaseManager, AgentTask
from backend.services.websocket_manager import WebSocketManager


class EnhancedAgentTask:
    """Enhanced wrapper around Codegen AgentTask with real-time monitoring"""
    
    def __init__(self, codegen_task, project_id: str, original_prompt: str, enhanced_prompt: str):
        self.id = str(uuid.uuid4())
        self.codegen_task = codegen_task
        self.project_id = project_id
        self.original_prompt = original_prompt
        self.enhanced_prompt = enhanced_prompt
        self.status = codegen_task.status
        self.result = codegen_task.result
        self.web_url = codegen_task.web_url
        self.created_at = datetime.now()
        self.status_history = []
        
    async def refresh_with_monitoring(self, websocket_manager: WebSocketManager):
        """Refresh task status and broadcast updates"""
        old_status = self.status
        self.codegen_task.refresh()
        self.status = self.codegen_task.status
        self.result = self.codegen_task.result
        
        # Track status changes
        if old_status != self.status:
            self.status_history.append({
                "status": self.status,
                "timestamp": datetime.now().isoformat(),
                "message": f"Status changed from {old_status} to {self.status}"
            })
            
            # Update database
            await DatabaseManager.update_agent_status(
                self.id, 
                self.status, 
                f"Agent task status updated to {self.status}"
            )
            
            # Broadcast real-time update
            await websocket_manager.broadcast({
                "type": "agent_status_update",
                "task_id": self.id,
                "project_id": self.project_id,
                "status": self.status,
                "result": self.result[:200] + "..." if self.result and len(self.result) > 200 else self.result,
                "web_url": self.web_url,
                "timestamp": datetime.now().isoformat(),
                "progress_info": self._extract_progress_info()
            })
    
    def _extract_progress_info(self) -> Dict[str, Any]:
        """Extract progress information from result or status"""
        progress_info = {
            "current_action": "Processing...",
            "progress_percentage": 0,
            "estimated_completion": None
        }
        
        # Map status to progress percentage
        status_progress = {
            "pending": 0,
            "running": 25,
            "processing": 50,
            "completing": 75,
            "completed": 100,
            "failed": 0
        }
        
        progress_info["progress_percentage"] = status_progress.get(self.status, 0)
        
        # Extract current action from result if available
        if self.result:
            # Simple heuristic to extract current action
            if "Creating PR" in self.result:
                progress_info["current_action"] = "Creating Pull Request"
            elif "Analyzing code" in self.result:
                progress_info["current_action"] = "Analyzing Code"
            elif "Running tests" in self.result:
                progress_info["current_action"] = "Running Tests"
            elif "Deploying" in self.result:
                progress_info["current_action"] = "Deploying Changes"
        
        return progress_info


class PromptEnhancer:
    """Advanced prompt enhancement techniques for better agent performance"""
    
    @staticmethod
    def enhance_prompt(
        original_prompt: str, 
        context: Dict[str, Any], 
        enhancement_type: str = "general"
    ) -> tuple[str, Dict[str, Any]]:
        """
        Enhance prompt using various techniques
        
        Args:
            original_prompt: The original user prompt
            context: Project and workflow context
            enhancement_type: Type of enhancement (code_analysis, pr_creation, etc.)
        
        Returns:
            Tuple of (enhanced_prompt, enhancement_metadata)
        """
        techniques_used = []
        enhanced_prompt = original_prompt
        
        # 1. Context Injection
        if context.get("repo_name"):
            enhanced_prompt = f"Repository: {context['repo_name']}\n\n{enhanced_prompt}"
            techniques_used.append("context_injection")
        
        # 2. Template-based Enhancement
        if enhancement_type in PROMPT_TEMPLATES:
            template = PROMPT_TEMPLATES[enhancement_type]
            enhanced_prompt = template.format(
                original_prompt=original_prompt,
                context=json.dumps(context, indent=2),
                **context
            )
            techniques_used.append(f"template_{enhancement_type}")
        
        # 3. Chain-of-Thought Enhancement
        if "analyze" in original_prompt.lower() or "review" in original_prompt.lower():
            enhanced_prompt += "\n\nPlease think through this step by step:\n"
            enhanced_prompt += "1. First, understand the current state\n"
            enhanced_prompt += "2. Identify what needs to be changed\n"
            enhanced_prompt += "3. Plan the implementation approach\n"
            enhanced_prompt += "4. Execute the changes\n"
            enhanced_prompt += "5. Validate the results\n"
            techniques_used.append("chain_of_thought")
        
        # 4. Role-based Enhancement
        role_keywords = {
            "security": "You are a security expert",
            "performance": "You are a performance optimization specialist",
            "testing": "You are a testing and QA expert",
            "deployment": "You are a DevOps and deployment specialist"
        }
        
        for keyword, role in role_keywords.items():
            if keyword in original_prompt.lower():
                enhanced_prompt = f"{role}. {enhanced_prompt}"
                techniques_used.append(f"role_{keyword}")
                break
        
        # 5. Constraint Addition
        enhanced_prompt += "\n\nImportant constraints:"
        enhanced_prompt += "\n- Follow existing code style and patterns"
        enhanced_prompt += "\n- Ensure backwards compatibility"
        enhanced_prompt += "\n- Include appropriate error handling"
        enhanced_prompt += "\n- Add tests for new functionality"
        enhanced_prompt += "\n- Document any breaking changes"
        techniques_used.append("constraint_addition")
        
        # 6. Output Format Specification
        enhanced_prompt += "\n\nPlease provide:"
        enhanced_prompt += "\n- Clear summary of changes made"
        enhanced_prompt += "\n- Links to created PRs or issues"
        enhanced_prompt += "\n- Any important notes or warnings"
        techniques_used.append("output_format")
        
        # 7. Length Optimization
        if len(enhanced_prompt) > settings.MAX_PROMPT_LENGTH:
            # Truncate while preserving important parts
            lines = enhanced_prompt.split('\n')
            truncated_lines = []
            current_length = 0
            
            for line in lines:
                if current_length + len(line) > settings.MAX_PROMPT_LENGTH - 100:
                    truncated_lines.append("... (truncated for length)")
                    break
                truncated_lines.append(line)
                current_length += len(line)
            
            enhanced_prompt = '\n'.join(truncated_lines)
            techniques_used.append("length_optimization")
        
        enhancement_metadata = {
            "techniques_used": techniques_used,
            "original_length": len(original_prompt),
            "enhanced_length": len(enhanced_prompt),
            "enhancement_type": enhancement_type,
            "context_keys": list(context.keys())
        }
        
        return enhanced_prompt, enhancement_metadata


class CodegenService:
    """Enhanced Codegen service with monitoring and prompt engineering"""
    
    def __init__(self, token: str, org_id: int, websocket_manager: WebSocketManager = None):
        self.agent = Agent(token=token, org_id=org_id)
        self.websocket_manager = websocket_manager or WebSocketManager()
        self.active_tasks: Dict[str, EnhancedAgentTask] = {}
        self.prompt_enhancer = PromptEnhancer()
        
    async def enhance_prompt(self, prompt: str, project: Any) -> str:
        """Enhance prompt with project context"""
        context = {
            "repo_name": project.repo_name,
            "owner": project.owner,
            "branch": project.default_branch,
            "requirements": project.requirements,
            "plan": project.plan,
            "focus_areas": ["code_quality", "security", "performance"],
            "quality_standards": ["PEP8", "type_hints", "documentation"],
            "environment": "development",
            "deployment_target": "staging"
        }
        
        # Determine enhancement type based on prompt content
        enhancement_type = "general"
        if any(word in prompt.lower() for word in ["analyze", "review", "check"]):
            enhancement_type = "code_analysis"
        elif any(word in prompt.lower() for word in ["create pr", "pull request", "merge"]):
            enhancement_type = "pr_creation"
        elif any(word in prompt.lower() for word in ["deploy", "deployment", "release"]):
            enhancement_type = "deployment_validation"
        elif any(word in prompt.lower() for word in ["workflow", "orchestrate", "automate"]):
            enhancement_type = "workflow_orchestration"
        
        enhanced_prompt, metadata = self.prompt_enhancer.enhance_prompt(
            prompt, context, enhancement_type
        )
        
        return enhanced_prompt
    
    async def execute_agent(self, prompt: str, project_id: str = None) -> EnhancedAgentTask:
        """Execute Codegen agent with enhanced monitoring"""
        # Get project context if provided
        project = None
        if project_id:
            project = await DatabaseManager.get_project(project_id)
        
        # Enhance prompt
        enhanced_prompt = prompt
        enhancement_metadata = {}
        
        if project:
            enhanced_prompt, enhancement_metadata = self.prompt_enhancer.enhance_prompt(
                prompt, 
                {
                    "repo_name": project.repo_name,
                    "owner": project.owner,
                    "branch": project.default_branch,
                    "requirements": project.requirements,
                    "plan": project.plan
                }
            )
        
        # Execute agent
        codegen_task = self.agent.run(enhanced_prompt)
        
        # Create enhanced task wrapper
        enhanced_task = EnhancedAgentTask(
            codegen_task=codegen_task,
            project_id=project_id or "unknown",
            original_prompt=prompt,
            enhanced_prompt=enhanced_prompt
        )
        
        # Store task for monitoring
        self.active_tasks[enhanced_task.id] = enhanced_task
        
        # Save to database
        await self._save_agent_task(enhanced_task, enhancement_metadata)
        
        # Start monitoring in background
        asyncio.create_task(self._monitor_task(enhanced_task))
        
        return enhanced_task
    
    async def _save_agent_task(self, task: EnhancedAgentTask, enhancement_metadata: Dict):
        """Save agent task to database"""
        task_data = {
            "id": task.id,
            "project_id": task.project_id,
            "codegen_task_id": str(task.codegen_task.id) if task.codegen_task.id else None,
            "original_prompt": task.original_prompt,
            "enhanced_prompt": task.enhanced_prompt,
            "prompt_enhancement_techniques": enhancement_metadata,
            "status": task.status,
            "result": task.result,
            "web_url": task.web_url,
            "metadata": {
                "created_at": task.created_at.isoformat(),
                "status_history": task.status_history
            }
        }
        
        # Save to database (implement actual database save)
        # await DatabaseManager.create_agent_task(task_data)
    
    async def _monitor_task(self, task: EnhancedAgentTask):
        """Monitor task status and broadcast updates"""
        while task.status not in ["completed", "failed"]:
            await task.refresh_with_monitoring(self.websocket_manager)
            await asyncio.sleep(5)  # Check every 5 seconds
        
        # Final status update
        await task.refresh_with_monitoring(self.websocket_manager)
        
        # Remove from active tasks
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            await task.refresh_with_monitoring(self.websocket_manager)
            
            return {
                "id": task.id,
                "status": task.status,
                "result": task.result,
                "web_url": task.web_url,
                "progress_info": task._extract_progress_info(),
                "status_history": task.status_history,
                "original_prompt": task.original_prompt[:100] + "..." if len(task.original_prompt) > 100 else task.original_prompt,
                "enhanced_prompt": task.enhanced_prompt[:100] + "..." if len(task.enhanced_prompt) > 100 else task.enhanced_prompt
            }
        
        return None
    
    async def get_all_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks with their current status"""
        tasks = []
        for task in self.active_tasks.values():
            await task.refresh_with_monitoring(self.websocket_manager)
            tasks.append({
                "id": task.id,
                "project_id": task.project_id,
                "status": task.status,
                "progress_info": task._extract_progress_info(),
                "created_at": task.created_at.isoformat(),
                "web_url": task.web_url
            })
        
        return tasks

