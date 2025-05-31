"""Chat interface API routes."""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...services.chat_service import ChatService, ChatSession
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class CreateSessionRequest(BaseModel):
    """Request model for creating a chat session."""
    project_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    """Request model for sending a chat message."""
    message: str
    include_code_analysis: bool = False


class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class ChatSessionResponse(BaseModel):
    """Response model for chat sessions."""
    session_id: str
    project_id: Optional[str]
    context: Dict[str, Any]
    created_at: str
    updated_at: str


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    analysis_type: str = "overview"


def get_chat_service(request: Request) -> ChatService:
    """Dependency to get chat service."""
    if not hasattr(request.app.state, "chat_service"):
        raise HTTPException(status_code=503, detail="Chat service not available")
    return request.app.state.chat_service


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request_data: CreateSessionRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Create a new chat session."""
    try:
        session = await chat_service.create_session(
            project_id=request_data.project_id,
            context=request_data.context,
        )
        
        return ChatSessionResponse(
            session_id=session.session_id,
            project_id=session.project_id,
            context=session.context,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get a chat session by ID."""
    try:
        session = await chat_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        return ChatSessionResponse(
            session_id=session.session_id,
            project_id=session.project_id,
            context=session.context,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat session")


@router.post("/sessions/{session_id}/messages")
async def send_chat_message(
    session_id: str,
    request_data: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Send a message to a chat session."""
    try:
        response = await chat_service.send_message(
            session_id=session_id,
            message=request_data.message,
            include_code_analysis=request_data.include_code_analysis,
        )
        
        if response is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        return {
            "response": response,
            "session_id": session_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get("/sessions/{session_id}/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get chat history for a session."""
    try:
        history = await chat_service.get_session_history(session_id)
        
        return [
            ChatMessageResponse(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                metadata=msg["metadata"],
            )
            for msg in history
        ]
        
    except Exception as e:
        logger.error(f"Error fetching chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")


@router.delete("/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Clear a chat session."""
    try:
        success = await chat_service.clear_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        return {"message": "Chat session cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat session")


@router.post("/analysis/{project_id}")
async def get_code_analysis(
    project_id: str,
    request_data: CodeAnalysisRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get code analysis for a project."""
    try:
        analysis = await chat_service.get_code_analysis(
            project_id=project_id,
            analysis_type=request_data.analysis_type,
        )
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Code analysis not available")
            
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting code analysis for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get code analysis")


@router.post("/requirements-prompt/{project_id}")
async def generate_requirements_prompt(
    project_id: str,
    project_description: Optional[str] = None,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Generate a requirements prompt for a project."""
    try:
        prompt = await chat_service.generate_requirements_prompt(
            project_id=project_id,
            project_description=project_description,
        )
        
        return {
            "prompt": prompt,
            "project_id": project_id,
        }
        
    except Exception as e:
        logger.error(f"Error generating requirements prompt for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate requirements prompt")


@router.post("/quick-chat")
async def quick_chat(
    request_data: SendMessageRequest,
    project_id: Optional[str] = None,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Send a quick chat message without creating a persistent session."""
    try:
        # Create temporary session
        session = await chat_service.create_session(
            project_id=project_id,
            context={"temporary": True}
        )
        
        # Send message
        response = await chat_service.send_message(
            session_id=session.session_id,
            message=request_data.message,
            include_code_analysis=request_data.include_code_analysis,
        )
        
        # Clear temporary session
        await chat_service.clear_session(session.session_id)
        
        return {
            "response": response,
            "message": request_data.message,
        }
        
    except Exception as e:
        logger.error(f"Error in quick chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process quick chat")


@router.get("/models/available")
async def get_available_models():
    """Get list of available AI models."""
    try:
        # Return available Anthropic models
        models = [
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "description": "Balanced performance and speed",
                "max_tokens": 4000,
                "default": True,
            },
            {
                "id": "claude-3-opus-20240229", 
                "name": "Claude 3 Opus",
                "description": "Highest performance for complex tasks",
                "max_tokens": 4000,
                "default": False,
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fastest responses for simple tasks",
                "max_tokens": 4000,
                "default": False,
            },
        ]
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Error fetching available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available models")


@router.get("/stats/usage")
async def get_chat_usage_stats(
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get chat usage statistics."""
    try:
        # In a real implementation, this would come from database/analytics
        stats = {
            "total_sessions": len(chat_service.sessions),
            "active_sessions": len([
                s for s in chat_service.sessions.values()
                if len(s.messages) > 1  # Has more than just system message
            ]),
            "total_messages": sum(
                len(s.messages) for s in chat_service.sessions.values()
            ),
            "average_messages_per_session": 0,
            "most_common_analysis_types": [
                "overview",
                "complexity",
                "dependencies"
            ],
        }
        
        if stats["total_sessions"] > 0:
            stats["average_messages_per_session"] = round(
                stats["total_messages"] / stats["total_sessions"], 2
            )
            
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching chat usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat usage statistics")


@router.post("/feedback/{session_id}")
async def submit_chat_feedback(
    session_id: str,
    feedback: Dict[str, Any],
    chat_service: ChatService = Depends(get_chat_service),
):
    """Submit feedback for a chat session."""
    try:
        session = await chat_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        # In a real implementation, this would store feedback in database
        logger.info(f"Received feedback for session {session_id}: {feedback}")
        
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

