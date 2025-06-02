"""
Chat Manager for Dashboard

This module manages chat interactions with the ChatAgent and coordinates
with Linear Agents for monitoring and task execution.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
import asyncio
import logging

from ...shared.logging.get_logger import get_logger
from ..agents.chat_agent import ChatAgent
from ..agents.langchain.agent import create_agent_with_tools
from ..agents.tools.linear.linear import LinearIssueTool, LinearCommentTool, LinearWebhookTool
from ..extensions.github.enhanced_agent import EnhancedGitHubAgent, GitHubAgentConfig
from ..extensions.linear.enhanced_agent import EnhancedLinearAgent, LinearAgentConfig
from graph_sitter import Codebase

logger = get_logger(__name__)

class ChatManager:
    """Manages chat interactions and agent coordination"""
    
    def __init__(self):
        self.chat_agents: Dict[str, ChatAgent] = {}
        self.linear_agents: Dict[str, EnhancedLinearAgent] = {}
        self.github_agents: Dict[str, EnhancedGitHubAgent] = {}
        self.monitoring_agents: Dict[str, Any] = {}
        self.active_threads: Dict[str, Dict[str, Any]] = {}
        
    async def process_chat_message(
        self, 
        message: str, 
        thread_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_tokens: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process a chat message and return response with potential actions"""
        
        if thread_id is None:
            thread_id = str(uuid4())
            
        # Get or create chat agent for this thread
        chat_agent = await self._get_chat_agent(thread_id, project_id)
        
        try:
            # Process the message with the chat agent
            response, updated_thread_id = chat_agent.chat(message, thread_id)
            
            # Analyze the response for actionable items
            plan = await self._analyze_for_plan(response, project_id)
            agents = []
            
            # If we have a plan and user tokens, create monitoring agents
            if plan and user_tokens:
                agents = await self._create_monitoring_agents(plan, project_id, user_tokens)
            
            return {
                "response": response,
                "thread_id": updated_thread_id,
                "plan": plan,
                "agents": agents,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "thread_id": thread_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_chat_agent(self, thread_id: str, project_id: Optional[str] = None) -> ChatAgent:
        """Get or create a chat agent for the thread"""
        
        if thread_id not in self.chat_agents:
            # Create codebase if we have a project
            codebase = None
            if project_id:
                try:
                    # This would need to be adapted based on how you want to handle codebases
                    # For now, we'll create a basic chat agent without codebase tools
                    pass
                except Exception as e:
                    logger.warning(f"Could not create codebase for project {project_id}: {e}")
            
            # Create chat agent with enhanced system prompt for planning
            system_prompt = """You are an AI assistant specialized in creating structured development plans. 
            When users describe project requirements, you should:
            
            1. Break down the requirements into clear, actionable tasks
            2. Suggest a logical implementation order
            3. Identify potential challenges and dependencies
            4. Recommend specific Linear issues and GitHub workflows
            5. Provide detailed implementation guidance
            
            Always structure your responses to be clear and actionable, focusing on practical next steps."""
            
            # For now, create a basic chat agent
            # In a full implementation, you'd integrate with the actual ChatAgent
            self.chat_agents[thread_id] = MockChatAgent(system_prompt)
            
        return self.chat_agents[thread_id]
    
    async def _analyze_for_plan(self, response: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze the response to extract actionable plans"""
        
        # Simple keyword-based analysis for demo
        # In a real implementation, this would use more sophisticated NLP
        
        plan_keywords = ["implement", "create", "build", "develop", "add", "feature", "task"]
        linear_keywords = ["issue", "ticket", "task", "story", "epic"]
        github_keywords = ["repository", "branch", "pull request", "commit"]
        
        has_plan = any(keyword in response.lower() for keyword in plan_keywords)
        has_linear = any(keyword in response.lower() for keyword in linear_keywords)
        has_github = any(keyword in response.lower() for keyword in github_keywords)
        
        if has_plan:
            return {
                "type": "implementation_plan",
                "has_linear_tasks": has_linear,
                "has_github_tasks": has_github,
                "project_id": project_id,
                "summary": "Implementation plan identified",
                "created_at": datetime.now().isoformat()
            }
        
        return None
    
    async def _create_monitoring_agents(
        self, 
        plan: Dict[str, Any], 
        project_id: Optional[str],
        user_tokens: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Create monitoring agents based on the plan"""
        
        agents = []
        
        try:
            # Create Linear monitoring agent if needed
            if plan.get("has_linear_tasks") and user_tokens.get("linear_token"):
                linear_agent = await self._create_linear_monitoring_agent(
                    project_id, user_tokens["linear_token"]
                )
                if linear_agent:
                    agents.append({
                        "id": linear_agent["id"],
                        "name": "Linear Monitor",
                        "type": "linear_monitoring",
                        "status": "active",
                        "description": "Monitoring Linear issues, comments, and updates"
                    })
            
            # Create GitHub monitoring agent if needed
            if plan.get("has_github_tasks") and user_tokens.get("github_token"):
                github_agent = await self._create_github_monitoring_agent(
                    project_id, user_tokens["github_token"]
                )
                if github_agent:
                    agents.append({
                        "id": github_agent["id"],
                        "name": "GitHub Monitor",
                        "type": "github_monitoring", 
                        "status": "active",
                        "description": "Monitoring PRs, branches, and comments"
                    })
                    
        except Exception as e:
            logger.error(f"Error creating monitoring agents: {e}")
        
        return agents
    
    async def _create_linear_monitoring_agent(
        self, 
        project_id: Optional[str], 
        linear_token: str
    ) -> Optional[Dict[str, Any]]:
        """Create a Linear monitoring agent"""
        
        try:
            agent_id = str(uuid4())
            
            # Configure Linear agent for monitoring
            config = LinearAgentConfig(
                api_key=linear_token,
                auto_assignment=True,
                workflow_automation=True
            )
            
            # Create enhanced Linear agent
            linear_agent = EnhancedLinearAgent(config)
            await linear_agent.start()
            
            # Store the agent
            self.linear_agents[agent_id] = linear_agent
            
            # Start monitoring task
            asyncio.create_task(self._monitor_linear_changes(agent_id, project_id))
            
            return {
                "id": agent_id,
                "agent": linear_agent,
                "project_id": project_id,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating Linear monitoring agent: {e}")
            return None
    
    async def _create_github_monitoring_agent(
        self, 
        project_id: Optional[str], 
        github_token: str
    ) -> Optional[Dict[str, Any]]:
        """Create a GitHub monitoring agent"""
        
        try:
            agent_id = str(uuid4())
            
            # Configure GitHub agent for monitoring
            config = GitHubAgentConfig(
                token=github_token,
                workflow_automation=True
            )
            
            # Create enhanced GitHub agent
            github_agent = EnhancedGitHubAgent(config)
            await github_agent.start()
            
            # Store the agent
            self.github_agents[agent_id] = github_agent
            
            # Start monitoring task
            asyncio.create_task(self._monitor_github_changes(agent_id, project_id))
            
            return {
                "id": agent_id,
                "agent": github_agent,
                "project_id": project_id,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating GitHub monitoring agent: {e}")
            return None
    
    async def _monitor_linear_changes(self, agent_id: str, project_id: Optional[str]):
        """Monitor Linear for changes"""
        
        logger.info(f"Starting Linear monitoring for agent {agent_id}")
        
        try:
            agent = self.linear_agents.get(agent_id)
            if not agent:
                return
            
            # Monitoring loop
            while agent_id in self.linear_agents:
                try:
                    # Check for new issues, comments, etc.
                    # This would integrate with the Linear webhook system
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in Linear monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"Linear monitoring agent {agent_id} failed: {e}")
        finally:
            # Cleanup
            if agent_id in self.linear_agents:
                await self.linear_agents[agent_id].stop()
                del self.linear_agents[agent_id]
    
    async def _monitor_github_changes(self, agent_id: str, project_id: Optional[str]):
        """Monitor GitHub for changes"""
        
        logger.info(f"Starting GitHub monitoring for agent {agent_id}")
        
        try:
            agent = self.github_agents.get(agent_id)
            if not agent:
                return
            
            # Monitoring loop
            while agent_id in self.github_agents:
                try:
                    # Check for new PRs, branches, comments, etc.
                    # This would integrate with the GitHub webhook system
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in GitHub monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"GitHub monitoring agent {agent_id} failed: {e}")
        finally:
            # Cleanup
            if agent_id in self.github_agents:
                await self.github_agents[agent_id].stop()
                del self.github_agents[agent_id]
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a monitoring agent"""
        
        try:
            # Check Linear agents
            if agent_id in self.linear_agents:
                await self.linear_agents[agent_id].stop()
                del self.linear_agents[agent_id]
                return True
            
            # Check GitHub agents
            if agent_id in self.github_agents:
                await self.github_agents[agent_id].stop()
                del self.github_agents[agent_id]
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        
        return {
            "linear_issues": 0,  # Would be populated by actual monitoring
            "pull_requests": 0,
            "comments": 0,
            "branches": 0,
            "recent_activity": [],
            "active_agents": len(self.linear_agents) + len(self.github_agents),
            "timestamp": datetime.now().isoformat()
        }


class MockChatAgent:
    """Mock chat agent for demonstration"""
    
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def chat(self, message: str, thread_id: str) -> tuple[str, str]:
        """Mock chat implementation"""
        
        if thread_id not in self.conversations:
            self.conversations[thread_id] = []
        
        # Add user message
        self.conversations[thread_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate mock response based on keywords
        response = self._generate_mock_response(message)
        
        # Add assistant response
        self.conversations[thread_id].append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response, thread_id
    
    def _generate_mock_response(self, message: str) -> str:
        """Generate a mock response based on the input"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["implement", "create", "build", "develop"]):
            return """I'll help you create a structured implementation plan. Based on your requirements, here's what I recommend:

**Implementation Plan:**

1. **Project Setup & Architecture**
   - Set up project structure and dependencies
   - Configure development environment
   - Create initial documentation

2. **Core Feature Development**
   - Break down features into manageable tasks
   - Implement core functionality first
   - Add supporting features incrementally

3. **Integration & Testing**
   - Integrate with external services
   - Implement comprehensive testing
   - Set up CI/CD pipeline

4. **Deployment & Monitoring**
   - Deploy to staging environment
   - Set up monitoring and logging
   - Deploy to production

I'll create Linear issues for each major task and set up GitHub workflows for the development process. Would you like me to proceed with creating the specific issues and monitoring agents?"""
        
        elif any(word in message_lower for word in ["help", "assist", "support"]):
            return """I'm here to help you plan and execute your development projects! I can:

- **Create structured implementation plans** from your requirements
- **Generate Linear issues** with detailed task breakdowns  
- **Set up GitHub workflows** for your development process
- **Monitor progress** across Linear and GitHub
- **Coordinate development tasks** and track dependencies

Just describe what you'd like to build or accomplish, and I'll create a comprehensive plan with automated tracking and monitoring."""
        
        else:
            return f"""I understand you want to work on: "{message}"

Let me help you create a structured approach to this. Could you provide more details about:

1. **Specific goals** - What exactly do you want to achieve?
2. **Technical requirements** - Any specific technologies or constraints?
3. **Timeline** - When do you need this completed?
4. **Resources** - What team members or tools are available?

With these details, I can create a comprehensive implementation plan with Linear issues and GitHub integration."""

