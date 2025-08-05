"""Chat service for AI-powered conversations and code analysis."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from ..utils.cache import CacheManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ChatMessage:
    """Chat message model."""
    
    def __init__(self, 
                 role: str,
                 content: str,
                 timestamp: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}


class ChatSession:
    """Chat session model."""
    
    def __init__(self, 
                 session_id: str,
                 project_id: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.project_id = project_id
        self.context = context or {}
        self.messages: List[ChatMessage] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class ChatService:
    """Service for AI-powered chat interface and code analysis."""
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize chat service.
        
        Args:
            anthropic_api_key: Anthropic API key for Claude integration
        """
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            logger.warning("No Anthropic API key provided, chat functionality will be limited")
            
        self.cache = CacheManager()
        self.sessions: Dict[str, ChatSession] = {}
        
        # Anthropic API configuration
        self.anthropic_base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-sonnet-20240229"
        
    async def create_session(self, 
                           project_id: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> ChatSession:
        """Create a new chat session.
        
        Args:
            project_id: Associated project ID
            context: Initial context for the session
            
        Returns:
            New chat session
        """
        session_id = f"chat_{datetime.utcnow().timestamp()}"
        
        session = ChatSession(
            session_id=session_id,
            project_id=project_id,
            context=context or {}
        )
        
        # Add system message with context
        system_message = await self._generate_system_message(project_id, context)
        session.messages.append(ChatMessage(
            role="system",
            content=system_message
        ))
        
        self.sessions[session_id] = session
        logger.info(f"Created chat session {session_id} for project {project_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get an existing chat session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Chat session or None if not found
        """
        return self.sessions.get(session_id)
    
    async def send_message(self, 
                         session_id: str,
                         message: str,
                         include_code_analysis: bool = False) -> Optional[str]:
        """Send a message to the chat session and get AI response.
        
        Args:
            session_id: Session ID
            message: User message
            include_code_analysis: Whether to include code analysis in response
            
        Returns:
            AI response or None if error
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None
            
        # Add user message
        user_message = ChatMessage(role="user", content=message)
        session.messages.append(user_message)
        
        try:
            # Prepare context for AI
            context = await self._prepare_context(session, include_code_analysis)
            
            # Get AI response
            response = await self._get_ai_response(session.messages, context)
            
            if response:
                # Add assistant message
                assistant_message = ChatMessage(role="assistant", content=response)
                session.messages.append(assistant_message)
                
                session.updated_at = datetime.utcnow()
                
                return response
            else:
                return "I'm sorry, I couldn't process your request at the moment."
                
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return "I encountered an error while processing your request."
    
    async def get_code_analysis(self, 
                              project_id: str,
                              analysis_type: str = "overview") -> Optional[Dict[str, Any]]:
        """Get code analysis for a project using code_agent.py integration.
        
        Args:
            project_id: Project ID to analyze
            analysis_type: Type of analysis (overview, complexity, dependencies, etc.)
            
        Returns:
            Analysis results or None if error
        """
        cache_key = f"code_analysis_{project_id}_{analysis_type}"
        cached_analysis = await self.cache.get(cache_key)
        
        if cached_analysis:
            return cached_analysis
            
        try:
            # This would integrate with the existing code_agent.py
            # For now, return a mock analysis
            analysis = {
                "project_id": project_id,
                "analysis_type": analysis_type,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": f"Code analysis for {project_id}",
                "metrics": {
                    "total_files": 0,
                    "total_lines": 0,
                    "complexity_score": 0,
                    "test_coverage": 0,
                },
                "recommendations": [
                    "Consider adding more unit tests",
                    "Review code complexity in core modules",
                    "Update documentation for public APIs"
                ],
                "dependencies": [],
                "issues": [],
            }
            
            # Cache for 30 minutes
            await self.cache.set(cache_key, analysis, ttl=1800)
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting code analysis for {project_id}: {e}")
            return None
    
    async def generate_requirements_prompt(self, 
                                         project_id: str,
                                         project_description: Optional[str] = None) -> str:
        """Generate a prompt for requirements gathering using Codegen API integration.
        
        Args:
            project_id: Project ID
            project_description: Optional project description
            
        Returns:
            Generated prompt for requirements
        """
        try:
            # Get code analysis
            analysis = await self.get_code_analysis(project_id, "overview")
            
            prompt_parts = [
                f"Generate comprehensive requirements for the project '{project_id}'.",
                "",
                "Please analyze the following information and create detailed requirements:",
                "",
            ]
            
            if project_description:
                prompt_parts.extend([
                    "Project Description:",
                    project_description,
                    "",
                ])
                
            if analysis:
                prompt_parts.extend([
                    "Code Analysis Summary:",
                    f"- Total files: {analysis['metrics']['total_files']}",
                    f"- Total lines: {analysis['metrics']['total_lines']}",
                    f"- Complexity score: {analysis['metrics']['complexity_score']}",
                    "",
                    "Recommendations:",
                ])
                
                for rec in analysis['recommendations']:
                    prompt_parts.append(f"- {rec}")
                    
                prompt_parts.append("")
                
            prompt_parts.extend([
                "Please provide requirements in the following categories:",
                "1. Functional Requirements",
                "2. Non-Functional Requirements", 
                "3. Technical Requirements",
                "4. Business Requirements",
                "",
                "For each requirement, include:",
                "- Clear title and description",
                "- Priority level (low, medium, high, critical)",
                "- Acceptance criteria",
                "- Dependencies (if any)",
            ])
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error generating requirements prompt: {e}")
            return f"Generate requirements for project '{project_id}'"
    
    async def _generate_system_message(self, 
                                     project_id: Optional[str],
                                     context: Optional[Dict[str, Any]]) -> str:
        """Generate system message for chat session.
        
        Args:
            project_id: Project ID
            context: Session context
            
        Returns:
            System message content
        """
        system_parts = [
            "You are an AI assistant specialized in software development and project management.",
            "You have access to GitHub project information, Linear issues, and code analysis capabilities.",
            "",
            "Your capabilities include:",
            "- Analyzing code structure and complexity",
            "- Generating project requirements",
            "- Providing development recommendations",
            "- Helping with project planning and management",
            "- Integrating with GitHub and Linear workflows",
            "",
        ]
        
        if project_id:
            system_parts.extend([
                f"Current project context: {project_id}",
                "You can access project information, code analysis, and related issues.",
                "",
            ])
            
        if context:
            system_parts.extend([
                "Additional context:",
                str(context),
                "",
            ])
            
        system_parts.extend([
            "Please provide helpful, accurate, and actionable responses.",
            "When discussing code or technical topics, be specific and provide examples when appropriate.",
            "If you need more information to provide a complete answer, ask clarifying questions.",
        ])
        
        return "\n".join(system_parts)
    
    async def _prepare_context(self, 
                             session: ChatSession,
                             include_code_analysis: bool) -> Dict[str, Any]:
        """Prepare context for AI response.
        
        Args:
            session: Chat session
            include_code_analysis: Whether to include code analysis
            
        Returns:
            Context dictionary
        """
        context = {
            "session_id": session.session_id,
            "project_id": session.project_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if session.project_id and include_code_analysis:
            analysis = await self.get_code_analysis(session.project_id)
            if analysis:
                context["code_analysis"] = analysis
                
        return context
    
    async def _get_ai_response(self, 
                             messages: List[ChatMessage],
                             context: Dict[str, Any]) -> Optional[str]:
        """Get AI response from Anthropic Claude.
        
        Args:
            messages: Chat messages
            context: Additional context
            
        Returns:
            AI response or None if error
        """
        if not self.anthropic_api_key:
            return "AI chat is not configured. Please provide an Anthropic API key."
            
        try:
            # Prepare messages for Anthropic API
            api_messages = []
            system_message = None
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    api_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                    
            # Add context to the last user message if available
            if context and api_messages:
                last_message = api_messages[-1]
                if last_message["role"] == "user":
                    context_str = f"\n\nContext: {context}"
                    last_message["content"] += context_str
                    
            headers = {
                "Authorization": f"Bearer {self.anthropic_api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 4000,
                "messages": api_messages
            }
            
            if system_message:
                payload["system"] = system_message
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.anthropic_base_url}/messages",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("content", [])
                        if content and len(content) > 0:
                            return content[0].get("text", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Anthropic API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear a chat session.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            True if session was cleared, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared chat session {session_id}")
            return True
        return False
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message dictionaries
        """
        session = self.sessions.get(session_id)
        if not session:
            return []
            
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in session.messages
            if msg.role != "system"  # Exclude system messages from history
        ]

