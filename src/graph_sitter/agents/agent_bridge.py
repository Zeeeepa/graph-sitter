#!/usr/bin/env python3
"""
Agent Bridge for Existing Graph-sitter Agent Infrastructure
==========================================================

This module bridges existing CodeAgent and ChatAgent classes with the web
dashboard through WebSocket connections. It leverages the existing LangChain
integration without modification.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import logging
from datetime import datetime
from uuid import uuid4

# Add graph-sitter to path
current_dir = Path(__file__).parent
graph_sitter_root = current_dir.parent.parent
src_path = graph_sitter_root / "src"
sys.path.insert(0, str(src_path))

# Import existing agent infrastructure
from graph_sitter.agents.code_agent import CodeAgent
from graph_sitter.agents.chat_agent import ChatAgent
from graph_sitter import Codebase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentSession:
    """Represents an active agent session."""
    
    def __init__(self, session_id: str, agent_type: str, codebase: Codebase, websocket):
        self.session_id = session_id
        self.agent_type = agent_type
        self.codebase = codebase
        self.websocket = websocket
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.conversation_history = []
        
        # Initialize appropriate agent using existing classes
        if agent_type == "code":
            self.agent = CodeAgent(codebase)
        elif agent_type == "chat":
            self.agent = ChatAgent(codebase)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def add_to_history(self, message_type: str, content: str, response: str = None):
        """Add interaction to conversation history."""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": message_type,
            "content": content,
            "response": response
        })
        # Keep only last 50 interactions
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

class AgentBridge:
    """Bridge between existing agents and dashboard WebSocket connections."""
    
    def __init__(self):
        self.active_sessions: Dict[str, AgentSession] = {}
        self.websocket_sessions: Dict = {}  # websocket -> session_id mapping
        self.codebase_cache: Dict[str, Codebase] = {}
        
    async def create_agent_session(self, websocket, repo_url: str, agent_type: str) -> str:
        """Create new agent session using existing agent classes."""
        try:
            # Get or load codebase
            if repo_url not in self.codebase_cache:
                await self.send_agent_message(websocket, "Loading codebase...", "status")
                codebase = Codebase.from_repo(repo_url)
                self.codebase_cache[repo_url] = codebase
                await self.send_agent_message(websocket, "Codebase loaded successfully", "status")
            else:
                codebase = self.codebase_cache[repo_url]
            
            # Create session
            session_id = str(uuid4())
            session = AgentSession(session_id, agent_type, codebase, websocket)
            
            self.active_sessions[session_id] = session
            self.websocket_sessions[websocket] = session_id
            
            logger.info(f"Created {agent_type} agent session {session_id} for {repo_url}")
            
            # Send session created message
            await self.send_agent_message(websocket, {
                "session_id": session_id,
                "agent_type": agent_type,
                "repo_url": repo_url,
                "status": "ready"
            }, "session_created")
            
            return session_id
            
        except Exception as e:
            error_msg = f"Error creating agent session: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            await self.send_agent_error(websocket, error_msg)
            raise
    
    async def handle_agent_query(self, websocket, session_id: str, query: str) -> Dict[str, Any]:
        """Handle agent query using existing agent functionality."""
        try:
            if session_id not in self.active_sessions:
                await self.send_agent_error(websocket, f"Session {session_id} not found")
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            session.update_activity()
            
            # Send processing message
            await self.send_agent_message(websocket, "Processing query...", "processing")
            
            # Use existing agent run method
            if session.agent_type == "code":
                # CodeAgent.run() method
                response = await self.run_code_agent_query(session, query, websocket)
            elif session.agent_type == "chat":
                # ChatAgent.run() method
                response = await self.run_chat_agent_query(session, query, websocket)
            else:
                response = {"error": f"Unknown agent type: {session.agent_type}"}
            
            # Add to conversation history
            session.add_to_history("query", query, str(response))
            
            # Send response
            await self.send_agent_message(websocket, {
                "session_id": session_id,
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }, "agent_response")
            
            return response
            
        except Exception as e:
            error_msg = f"Error handling agent query: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            await self.send_agent_error(websocket, error_msg)
            return {"error": error_msg}
    
    async def run_code_agent_query(self, session: AgentSession, query: str, websocket) -> str:
        """Run query using existing CodeAgent."""
        try:
            # Use existing CodeAgent.run method
            # Note: This might be synchronous, so we'll run it in a thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Create a thread ID for this session if not exists
            thread_id = getattr(session, 'thread_id', None)
            if not thread_id:
                thread_id = str(uuid4())
                session.thread_id = thread_id
            
            # Run the agent query
            def run_agent():
                try:
                    # Use existing agent run method with thread_id for memory
                    return session.agent.run(query, thread_id=thread_id)
                except Exception as e:
                    logger.error(f"Error in CodeAgent.run: {e}")
                    return f"Error: {str(e)}"
            
            # Run in thread pool to avoid blocking
            response = await loop.run_in_executor(None, run_agent)
            
            return response
            
        except Exception as e:
            logger.error(f"Error running CodeAgent query: {e}")
            return f"Error: {str(e)}"
    
    async def run_chat_agent_query(self, session: AgentSession, query: str, websocket) -> str:
        """Run query using existing ChatAgent."""
        try:
            # Use existing ChatAgent.run method
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Create a thread ID for this session if not exists
            thread_id = getattr(session, 'thread_id', None)
            if not thread_id:
                thread_id = str(uuid4())
                session.thread_id = thread_id
            
            # Run the agent query
            def run_agent():
                try:
                    # Use existing agent run method with thread_id for memory
                    return session.agent.run(query, thread_id=thread_id)
                except Exception as e:
                    logger.error(f"Error in ChatAgent.run: {e}")
                    return f"Error: {str(e)}"
            
            # Run in thread pool to avoid blocking
            response = await loop.run_in_executor(None, run_agent)
            
            return response
            
        except Exception as e:
            logger.error(f"Error running ChatAgent query: {e}")
            return f"Error: {str(e)}"
    
    async def get_session_info(self, websocket, session_id: str) -> Dict[str, Any]:
        """Get information about an agent session."""
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            return {
                "session_id": session_id,
                "agent_type": session.agent_type,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "conversation_count": len(session.conversation_history),
                "codebase_info": {
                    "total_files": len(list(session.codebase.files)),
                    "total_functions": len(list(session.codebase.functions)),
                    "total_classes": len(list(session.codebase.classes))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {"error": str(e)}
    
    async def get_conversation_history(self, websocket, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            if session_id not in self.active_sessions:
                return []
            
            session = self.active_sessions[session_id]
            return session.conversation_history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def close_session(self, websocket, session_id: str = None):
        """Close agent session."""
        try:
            # Get session ID from websocket if not provided
            if not session_id and websocket in self.websocket_sessions:
                session_id = self.websocket_sessions[websocket]
            
            if session_id and session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Closed agent session {session_id}")
            
            if websocket in self.websocket_sessions:
                del self.websocket_sessions[websocket]
                
        except Exception as e:
            logger.error(f"Error closing session: {e}")
    
    async def send_agent_message(self, websocket, message: Any, message_type: str):
        """Send message to websocket."""
        try:
            data = {
                "type": f"agent_{message_type}",
                "data": message,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending agent message: {e}")
    
    async def send_agent_error(self, websocket, error_message: str):
        """Send error message to websocket."""
        try:
            data = {
                "type": "agent_error",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending agent error: {e}")
    
    def cleanup_inactive_sessions(self, max_idle_minutes: int = 30):
        """Clean up inactive sessions."""
        try:
            current_time = datetime.now()
            inactive_sessions = []
            
            for session_id, session in self.active_sessions.items():
                idle_time = (current_time - session.last_activity).total_seconds() / 60
                if idle_time > max_idle_minutes:
                    inactive_sessions.append(session_id)
            
            for session_id in inactive_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up inactive session {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")

# Global agent bridge instance
agent_bridge = AgentBridge()

async def handle_agent_websocket_message(websocket, data: dict):
    """Handle incoming agent WebSocket messages."""
    try:
        message_type = data.get("type")
        
        if message_type == "create_session":
            repo_url = data.get("repo_url")
            agent_type = data.get("agent_type", "chat")  # Default to chat agent
            
            if not repo_url:
                await agent_bridge.send_agent_error(websocket, "Repository URL is required")
                return
            
            session_id = await agent_bridge.create_agent_session(websocket, repo_url, agent_type)
            
        elif message_type == "agent_query":
            session_id = data.get("session_id")
            query = data.get("query")
            
            if not session_id or not query:
                await agent_bridge.send_agent_error(websocket, "Session ID and query are required")
                return
            
            await agent_bridge.handle_agent_query(websocket, session_id, query)
            
        elif message_type == "get_session_info":
            session_id = data.get("session_id")
            
            if not session_id:
                await agent_bridge.send_agent_error(websocket, "Session ID is required")
                return
            
            info = await agent_bridge.get_session_info(websocket, session_id)
            await agent_bridge.send_agent_message(websocket, info, "session_info")
            
        elif message_type == "get_history":
            session_id = data.get("session_id")
            
            if not session_id:
                await agent_bridge.send_agent_error(websocket, "Session ID is required")
                return
            
            history = await agent_bridge.get_conversation_history(websocket, session_id)
            await agent_bridge.send_agent_message(websocket, history, "conversation_history")
            
        elif message_type == "close_session":
            session_id = data.get("session_id")
            await agent_bridge.close_session(websocket, session_id)
            await agent_bridge.send_agent_message(websocket, {"status": "closed"}, "session_closed")
            
        else:
            await agent_bridge.send_agent_error(websocket, f"Unknown message type: {message_type}")
            
    except Exception as e:
        error_msg = f"Error handling agent WebSocket message: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        await agent_bridge.send_agent_error(websocket, error_msg)

# Periodic cleanup task
async def periodic_session_cleanup():
    """Periodic cleanup of inactive sessions."""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            agent_bridge.cleanup_inactive_sessions()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

# Start cleanup task
asyncio.create_task(periodic_session_cleanup())

# Export for use in main application
__all__ = [
    'AgentBridge',
    'AgentSession',
    'agent_bridge',
    'handle_agent_websocket_message'
]
