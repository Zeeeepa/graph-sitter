"""
Codegen API Client for Web-Eval-Agent Dashboard

Handles integration with the Codegen API for automated development workflows.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Callable
import json
from datetime import datetime

import aiohttp
from pydantic import BaseModel

from models import AgentResponse, ResponseType

logger = logging.getLogger(__name__)


class CodegenSession(BaseModel):
    """Codegen API session model."""
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    project_context: Optional[str] = None
    responses: List[AgentResponse] = []
    metadata: Dict[str, Any] = {}


class CodegenClient:
    """Codegen API client for automated development workflows."""
    
    def __init__(self):
        """Initialize Codegen client."""
        self.api_key = os.getenv("CODEGEN_API_KEY")
        self.org_id = os.getenv("CODEGEN_ORG_ID")
        self.base_url = os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com")
        self.timeout = int(os.getenv("CODEGEN_TIMEOUT", "300"))
        
        self.session = None
        self.active_sessions: Dict[str, CodegenSession] = {}
        
        if not self.api_key:
            logger.warning("CODEGEN_API_KEY not set - Codegen integration disabled")
        if not self.org_id:
            logger.warning("CODEGEN_ORG_ID not set - Codegen integration disabled")
    
    async def initialize(self):
        """Initialize HTTP session and validate API access."""
        if not self.api_key or not self.org_id:
            logger.warning("Codegen client not initialized - missing credentials")
            return
        
        # Create HTTP session with authentication
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "WebEvalAgent-Dashboard/1.0"
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        # Validate API access
        try:
            await self._validate_api_access()
            logger.info("Codegen API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to validate Codegen API access: {e}")
            await self.session.close()
            self.session = None
    
    async def shutdown(self):
        """Shutdown HTTP session."""
        if self.session:
            await self.session.close()
            logger.info("Codegen API client shutdown")
    
    async def _validate_api_access(self):
        """Validate API access by checking organization info."""
        if not self.session:
            raise RuntimeError("HTTP session not initialized")
        
        url = f"{self.base_url}/v1/organizations/{self.org_id}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                org_info = await response.json()
                logger.info(f"Validated access to organization: {org_info.get('name', self.org_id)}")
            elif response.status == 401:
                raise ValueError("Invalid API key")
            elif response.status == 403:
                raise ValueError("Access denied to organization")
            elif response.status == 404:
                raise ValueError("Organization not found")
            else:
                response.raise_for_status()
    
    async def start_session(
        self, 
        project_context: str, 
        initial_prompt: str,
        repository_url: Optional[str] = None,
        branch: Optional[str] = None
    ) -> CodegenSession:
        """Start a new Codegen API session."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        # Prepare session data
        session_data = {
            "organization_id": self.org_id,
            "context": project_context,
            "initial_prompt": initial_prompt,
            "metadata": {
                "source": "web-eval-agent-dashboard",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if repository_url:
            session_data["repository_url"] = repository_url
        if branch:
            session_data["branch"] = branch
        
        # Create session via API
        url = f"{self.base_url}/v1/sessions"
        
        async with self.session.post(url, json=session_data) as response:
            if response.status == 201:
                session_info = await response.json()
                
                # Create session object
                codegen_session = CodegenSession(
                    id=session_info["id"],
                    status=session_info["status"],
                    created_at=datetime.fromisoformat(session_info["created_at"]),
                    updated_at=datetime.fromisoformat(session_info["updated_at"]),
                    project_context=project_context,
                    metadata=session_info.get("metadata", {})
                )
                
                # Store session
                self.active_sessions[codegen_session.id] = codegen_session
                
                # Start monitoring session for responses
                asyncio.create_task(self._monitor_session(codegen_session.id))
                
                logger.info(f"Started Codegen session: {codegen_session.id}")
                return codegen_session
                
            else:
                error_data = await response.json() if response.content_type == "application/json" else {}
                error_message = error_data.get("error", f"HTTP {response.status}")
                raise RuntimeError(f"Failed to start Codegen session: {error_message}")
    
    async def continue_session(self, session_id: str, continuation_text: str) -> CodegenSession:
        """Continue an existing Codegen session."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Send continuation message
        url = f"{self.base_url}/v1/sessions/{session_id}/continue"
        
        continuation_data = {
            "message": continuation_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with self.session.post(url, json=continuation_data) as response:
            if response.status == 200:
                session_info = await response.json()
                
                # Update session
                codegen_session = self.active_sessions[session_id]
                codegen_session.status = session_info["status"]
                codegen_session.updated_at = datetime.fromisoformat(session_info["updated_at"])
                
                logger.info(f"Continued Codegen session: {session_id}")
                return codegen_session
                
            else:
                error_data = await response.json() if response.content_type == "application/json" else {}
                error_message = error_data.get("error", f"HTTP {response.status}")
                raise RuntimeError(f"Failed to continue session: {error_message}")
    
    async def confirm_plan(self, session_id: str, confirmation_message: str = "Proceed") -> CodegenSession:
        """Confirm a proposed plan in a Codegen session."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Send plan confirmation
        url = f"{self.base_url}/v1/sessions/{session_id}/confirm-plan"
        
        confirmation_data = {
            "confirmation": confirmation_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with self.session.post(url, json=confirmation_data) as response:
            if response.status == 200:
                session_info = await response.json()
                
                # Update session
                codegen_session = self.active_sessions[session_id]
                codegen_session.status = session_info["status"]
                codegen_session.updated_at = datetime.fromisoformat(session_info["updated_at"])
                
                logger.info(f"Confirmed plan for session: {session_id}")
                return codegen_session
                
            else:
                error_data = await response.json() if response.content_type == "application/json" else {}
                error_message = error_data.get("error", f"HTTP {response.status}")
                raise RuntimeError(f"Failed to confirm plan: {error_message}")
    
    async def modify_plan(self, session_id: str, modification_text: str) -> CodegenSession:
        """Request plan modification in a Codegen session."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Send plan modification request
        url = f"{self.base_url}/v1/sessions/{session_id}/modify-plan"
        
        modification_data = {
            "modification": modification_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        async with self.session.post(url, json=modification_data) as response:
            if response.status == 200:
                session_info = await response.json()
                
                # Update session
                codegen_session = self.active_sessions[session_id]
                codegen_session.status = session_info["status"]
                codegen_session.updated_at = datetime.fromisoformat(session_info["updated_at"])
                
                logger.info(f"Requested plan modification for session: {session_id}")
                return codegen_session
                
            else:
                error_data = await response.json() if response.content_type == "application/json" else {}
                error_message = error_data.get("error", f"HTTP {response.status}")
                raise RuntimeError(f"Failed to modify plan: {error_message}")
    
    async def get_session_status(self, session_id: str) -> Optional[CodegenSession]:
        """Get current status of a Codegen session."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        url = f"{self.base_url}/v1/sessions/{session_id}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                session_info = await response.json()
                
                # Update or create session object
                if session_id in self.active_sessions:
                    codegen_session = self.active_sessions[session_id]
                    codegen_session.status = session_info["status"]
                    codegen_session.updated_at = datetime.fromisoformat(session_info["updated_at"])
                else:
                    codegen_session = CodegenSession(
                        id=session_info["id"],
                        status=session_info["status"],
                        created_at=datetime.fromisoformat(session_info["created_at"]),
                        updated_at=datetime.fromisoformat(session_info["updated_at"]),
                        metadata=session_info.get("metadata", {})
                    )
                    self.active_sessions[session_id] = codegen_session
                
                return codegen_session
                
            elif response.status == 404:
                # Session not found
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                return None
            else:
                response.raise_for_status()
    
    async def cancel_session(self, session_id: str) -> bool:
        """Cancel a Codegen session."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        url = f"{self.base_url}/v1/sessions/{session_id}/cancel"
        
        async with self.session.post(url) as response:
            if response.status == 200:
                # Remove from active sessions
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                logger.info(f"Cancelled Codegen session: {session_id}")
                return True
            else:
                logger.error(f"Failed to cancel session {session_id}: HTTP {response.status}")
                return False
    
    async def _monitor_session(self, session_id: str):
        """Monitor a session for new responses."""
        if not self.session:
            return
        
        logger.info(f"Starting session monitoring for: {session_id}")
        
        while session_id in self.active_sessions:
            try:
                # Check for new responses
                url = f"{self.base_url}/v1/sessions/{session_id}/responses"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        responses_data = await response.json()
                        
                        # Process new responses
                        session = self.active_sessions[session_id]
                        current_response_count = len(session.responses)
                        
                        for response_data in responses_data["responses"][current_response_count:]:
                            agent_response = self._parse_agent_response(response_data)
                            session.responses.append(agent_response)
                            
                            # Update session status
                            session.updated_at = datetime.utcnow()
                            
                            logger.info(f"New response for session {session_id}: {agent_response.type}")
                        
                        # Check if session is complete
                        if responses_data.get("status") in ["completed", "failed", "cancelled"]:
                            session.status = responses_data["status"]
                            logger.info(f"Session {session_id} completed with status: {session.status}")
                            break
                    
                    elif response.status == 404:
                        # Session no longer exists
                        logger.warning(f"Session {session_id} no longer exists")
                        break
                    
                    else:
                        logger.error(f"Error monitoring session {session_id}: HTTP {response.status}")
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                logger.info(f"Session monitoring cancelled for: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error monitoring session {session_id}: {e}")
                await asyncio.sleep(10)  # Wait longer on error
        
        # Clean up session
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Stopped session monitoring for: {session_id}")
    
    def _parse_agent_response(self, response_data: Dict[str, Any]) -> AgentResponse:
        """Parse agent response from API data."""
        response_type = ResponseType(response_data.get("type", "regular"))
        
        agent_response = AgentResponse(
            type=response_type,
            content=response_data.get("content", ""),
            metadata=response_data.get("metadata", {})
        )
        
        # Parse type-specific data
        if response_type == ResponseType.PLAN:
            agent_response.plan = response_data.get("plan", {})
        elif response_type == ResponseType.PR:
            agent_response.pr_number = response_data.get("pr_number")
            agent_response.pr_url = response_data.get("pr_url")
        
        return agent_response
    
    def get_session(self, session_id: str) -> Optional[CodegenSession]:
        """Get a session from local cache."""
        return self.active_sessions.get(session_id)
    
    def get_latest_response(self, session_id: str) -> Optional[AgentResponse]:
        """Get the latest response from a session."""
        session = self.active_sessions.get(session_id)
        if session and session.responses:
            return session.responses[-1]
        return None
    
    async def list_active_sessions(self) -> List[CodegenSession]:
        """List all active sessions."""
        return list(self.active_sessions.values())
    
    async def get_organization_info(self) -> Optional[Dict[str, Any]]:
        """Get organization information."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        url = f"{self.base_url}/v1/organizations/{self.org_id}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to get organization info: HTTP {response.status}")
                return None
    
    async def get_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Get API usage statistics."""
        if not self.session:
            raise RuntimeError("Codegen client not initialized")
        
        url = f"{self.base_url}/v1/organizations/{self.org_id}/usage"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to get usage stats: HTTP {response.status}")
                return None


# Session extension for easier access
class CodegenSession:
    """Extended session class with convenience methods."""
    
    def __init__(self, id: str, status: str, created_at: datetime, updated_at: datetime, 
                 project_context: Optional[str] = None, responses: Optional[List[AgentResponse]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.project_context = project_context
        self.responses = responses or []
        self.metadata = metadata or {}
    
    def get_latest_response(self) -> Optional[AgentResponse]:
        """Get the latest response."""
        return self.responses[-1] if self.responses else None
    
    def get_responses_by_type(self, response_type: ResponseType) -> List[AgentResponse]:
        """Get all responses of a specific type."""
        return [r for r in self.responses if r.type == response_type]
    
    def has_plan_response(self) -> bool:
        """Check if session has a plan response."""
        return any(r.type == ResponseType.PLAN for r in self.responses)
    
    def has_pr_response(self) -> bool:
        """Check if session has a PR response."""
        return any(r.type == ResponseType.PR for r in self.responses)
    
    def get_pr_numbers(self) -> List[int]:
        """Get all PR numbers from PR responses."""
        pr_numbers = []
        for response in self.responses:
            if response.type == ResponseType.PR and response.pr_number:
                pr_numbers.append(response.pr_number)
        return pr_numbers
    
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.status in ["running", "waiting_for_input", "processing"]
    
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.status in ["completed", "failed", "cancelled"]
