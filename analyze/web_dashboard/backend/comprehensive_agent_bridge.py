#!/usr/bin/env python3
"""
Comprehensive Agent Bridge for Graph-sitter Dashboard Integration
================================================================

This module provides a comprehensive bridge between the full-featured graph-sitter 
agents (CodeAgent and ChatAgent) and the web dashboard, enabling real-time agent 
interaction with complete comprehension capabilities through WebSocket connections.

Uses the existing LangChain-based agents with full transaction management, memory,
and advanced reasoning capabilities.
"""

import asyncio
import json
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from uuid import uuid4

# Import existing graph-sitter agents (LangChain-based)
from graph_sitter.agents.code_agent import CodeAgent
from graph_sitter.agents.chat_agent import ChatAgent

# Import analysis functions for enhanced responses
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Import deep analysis for comprehensive insights
try:
    from graph_sitter.analysis.analysis import DeepCodebaseAnalyzer
    DEEP_ANALYSIS_AVAILABLE = True
except ImportError:
    DEEP_ANALYSIS_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveAgentSession:
    """Comprehensive agent session with full LangChain capabilities."""
    
    def __init__(self, codebase, session_id: str = None, agent_type: str = "chat"):
        self.codebase = codebase
        self.session_id = session_id or str(uuid4())
        self.agent_type = agent_type
        self.thread_id = str(uuid4())
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.conversation_history = []
        
        # Initialize the appropriate agent with full capabilities
        try:
            if agent_type == "code":
                self.agent = CodeAgent(
                    codebase=codebase,
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest",
                    memory=True,
                    thread_id=self.thread_id
                )
                logger.info(f"Initialized CodeAgent for session {self.session_id}")
            else:
                self.agent = ChatAgent(
                    codebase=codebase,
                    model_provider="anthropic", 
                    model_name="claude-3-5-sonnet-latest",
                    memory=True
                )
                logger.info(f"Initialized ChatAgent for session {self.session_id}")
                
            # Initialize deep analyzer if available
            if DEEP_ANALYSIS_AVAILABLE:
                self.deep_analyzer = DeepCodebaseAnalyzer(codebase)
                logger.info("Deep analysis capabilities enabled")
            else:
                self.deep_analyzer = None
                
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query with full comprehension capabilities."""
        try:
            self.last_activity = datetime.now()
            
            # Add query to conversation history
            self.conversation_history.append({
                "timestamp": self.last_activity.isoformat(),
                "type": "query",
                "content": query,
                "context": context or {}
            })
            
            # Enhance query with context if needed
            enhanced_query = await self._enhance_query_with_context(query, context)
            
            # Process with the full-featured agent
            logger.info(f"Processing query with {self.agent_type} agent: {query[:100]}...")
            
            if self.agent_type == "code":
                # Use CodeAgent for code-related queries
                response = await asyncio.to_thread(
                    self.agent.run, 
                    enhanced_query, 
                    thread_id=self.thread_id
                )
            else:
                # Use ChatAgent for general queries
                response = await asyncio.to_thread(
                    self.agent.run,
                    enhanced_query,
                    thread_id=self.thread_id
                )
            
            # Add response to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "response",
                "content": response,
                "agent_type": self.agent_type
            })
            
            # Generate additional insights if requested
            insights = await self._generate_additional_insights(query, response, context)
            
            return {
                "session_id": self.session_id,
                "response": response,
                "insights": insights,
                "agent_type": self.agent_type,
                "thread_id": self.thread_id,
                "timestamp": datetime.now().isoformat(),
                "conversation_length": len(self.conversation_history)
            }
            
        except Exception as e:
            error_response = {
                "session_id": self.session_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"Error processing query: {e}")
            return error_response
    
    async def _enhance_query_with_context(self, query: str, context: Dict[str, Any] = None) -> str:
        """Enhance query with additional context for better comprehension."""
        if not context:
            return query
        
        enhanced_parts = [query]
        
        # Add codebase context if requested
        if context.get("include_codebase_summary"):
            try:
                summary = get_codebase_summary(self.codebase)
                enhanced_parts.append(f"\nCodebase Context:\n{summary}")
            except Exception as e:
                logger.warning(f"Could not add codebase summary: {e}")
        
        # Add file context if specified
        if context.get("focus_files"):
            try:
                files = list(self.codebase.files)
                focus_files = [f for f in files if f.name in context["focus_files"]]
                for file in focus_files[:3]:  # Limit to 3 files
                    file_summary = get_file_summary(file)
                    enhanced_parts.append(f"\nFile Context ({file.name}):\n{file_summary}")
            except Exception as e:
                logger.warning(f"Could not add file context: {e}")
        
        # Add deep analysis context if available and requested
        if context.get("include_deep_analysis") and self.deep_analyzer:
            try:
                metrics = self.deep_analyzer.analyze_comprehensive_metrics()
                if "error" not in metrics:
                    basic_counts = metrics.get("basic_counts", {})
                    enhanced_parts.append(f"\nDeep Analysis Context:\n{json.dumps(basic_counts, indent=2)}")
            except Exception as e:
                logger.warning(f"Could not add deep analysis context: {e}")
        
        return "\n".join(enhanced_parts)
    
    async def _generate_additional_insights(self, query: str, response: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate additional insights based on the query and response."""
        insights = {}
        
        try:
            # Generate code-related insights
            if any(keyword in query.lower() for keyword in ['function', 'class', 'file', 'code']):
                insights["code_analysis"] = await self._get_code_insights(query)
            
            # Generate architectural insights
            if any(keyword in query.lower() for keyword in ['architecture', 'structure', 'design', 'pattern']):
                insights["architectural_analysis"] = await self._get_architectural_insights()
            
            # Generate complexity insights
            if any(keyword in query.lower() for keyword in ['complex', 'refactor', 'improve', 'optimize']):
                insights["complexity_analysis"] = await self._get_complexity_insights()
            
            # Generate dependency insights
            if any(keyword in query.lower() for keyword in ['import', 'dependency', 'coupling', 'module']):
                insights["dependency_analysis"] = await self._get_dependency_insights()
                
        except Exception as e:
            logger.warning(f"Could not generate additional insights: {e}")
            insights["error"] = str(e)
        
        return insights
    
    async def _get_code_insights(self, query: str) -> Dict[str, Any]:
        """Get code-related insights."""
        try:
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            
            return {
                "total_files": len(files),
                "total_functions": len(functions),
                "total_classes": len(classes),
                "top_files_by_symbols": [
                    {"name": f.name, "symbols": len(f.symbols)} 
                    for f in sorted(files, key=lambda x: len(x.symbols), reverse=True)[:5]
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_architectural_insights(self) -> Dict[str, Any]:
        """Get architectural insights."""
        try:
            if not self.deep_analyzer:
                return {"error": "Deep analysis not available"}
            
            metrics = self.deep_analyzer.analyze_comprehensive_metrics()
            if "error" in metrics:
                return {"error": metrics["error"]}
            
            architectural_metrics = metrics.get("architectural_metrics", {})
            return {
                "coupling_metrics": architectural_metrics.get("coupling_metrics", {}),
                "cohesion_metrics": architectural_metrics.get("cohesion_metrics", {}),
                "inheritance_metrics": architectural_metrics.get("inheritance_metrics", {})
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_complexity_insights(self) -> Dict[str, Any]:
        """Get complexity insights."""
        try:
            if not self.deep_analyzer:
                return {"error": "Deep analysis not available"}
            
            hotspots = self.deep_analyzer.analyze_hotspots()
            if "error" in hotspots:
                return {"error": hotspots["error"]}
            
            return {
                "complex_functions": hotspots.get("complex_functions", [])[:5],
                "large_classes": hotspots.get("large_classes", [])[:5],
                "potential_issues": len(hotspots.get("potential_issues", []))
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_dependency_insights(self) -> Dict[str, Any]:
        """Get dependency insights."""
        try:
            files = list(self.codebase.files)
            all_imports = []
            for file in files:
                all_imports.extend(file.imports)
            
            # Count import frequencies
            import_names = [imp.name for imp in all_imports if hasattr(imp, 'name')]
            from collections import Counter
            import_counter = Counter(import_names)
            
            return {
                "total_imports": len(all_imports),
                "unique_imports": len(set(import_names)),
                "most_imported": dict(import_counter.most_common(10)),
                "files_with_most_imports": [
                    {"name": f.name, "imports": len(f.imports)}
                    for f in sorted(files, key=lambda x: len(x.imports), reverse=True)[:5]
                ]
            }
        except Exception as e:
            return {"error": str(e)}

class ComprehensiveAgentBridge:
    """Comprehensive agent bridge managing multiple agent sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, ComprehensiveAgentSession] = {}
        self.active_connections: Dict[str, Any] = {}
        
    async def create_session(self, codebase, agent_type: str = "chat", session_id: str = None) -> ComprehensiveAgentSession:
        """Create a new comprehensive agent session."""
        try:
            session = ComprehensiveAgentSession(codebase, session_id, agent_type)
            self.sessions[session.session_id] = session
            logger.info(f"Created {agent_type} agent session: {session.session_id}")
            return session
        except Exception as e:
            logger.error(f"Error creating agent session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ComprehensiveAgentSession]:
        """Get an existing agent session."""
        return self.sessions.get(session_id)
    
    async def process_query(self, session_id: str, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query through an agent session."""
        session = await self.get_session(session_id)
        if not session:
            return {
                "error": f"Session {session_id} not found",
                "timestamp": datetime.now().isoformat()
            }
        
        return await session.process_query(query, context)
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Clean up inactive sessions."""
        current_time = datetime.now()
        inactive_sessions = []
        
        for session_id, session in self.sessions.items():
            age_hours = (current_time - session.last_activity).total_seconds() / 3600
            if age_hours > max_age_hours:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up inactive session: {session_id}")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        return {
            "total_sessions": len(self.sessions),
            "session_types": {
                "chat": len([s for s in self.sessions.values() if s.agent_type == "chat"]),
                "code": len([s for s in self.sessions.values() if s.agent_type == "code"])
            },
            "active_connections": len(self.active_connections),
            "timestamp": datetime.now().isoformat()
        }

# Global bridge instance
comprehensive_agent_bridge = ComprehensiveAgentBridge()

# WebSocket connection manager for real-time agent interaction
class AgentConnectionManager:
    """Manages WebSocket connections for real-time agent interaction."""
    
    def __init__(self):
        self.active_connections: List[Any] = []
        self.session_connections: Dict[str, List[Any]] = {}
    
    async def connect(self, websocket, session_id: str = None):
        """Connect a WebSocket for agent interaction."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = []
            self.session_connections[session_id].append(websocket)
        
        logger.info(f"Agent WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket, session_id: str = None):
        """Disconnect a WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if session_id and session_id in self.session_connections:
            if websocket in self.session_connections[session_id]:
                self.session_connections[session_id].remove(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        logger.info(f"Agent WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to all connections for a specific session."""
        if session_id in self.session_connections:
            disconnected = []
            for connection in self.session_connections[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to session {session_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection, session_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager
agent_connection_manager = AgentConnectionManager()

# Export the main components
__all__ = [
    'ComprehensiveAgentSession',
    'ComprehensiveAgentBridge', 
    'AgentConnectionManager',
    'comprehensive_agent_bridge',
    'agent_connection_manager'
]
