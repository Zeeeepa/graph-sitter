"""
LSP Protocol Implementation for Serena Server Communication

This module implements the Language Server Protocol (LSP) for communication
with Serena analysis servers, providing structured message handling and
protocol compliance.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """LSP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class ErrorCode(Enum):
    """LSP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    REQUEST_CANCELLED = -32800
    CONTENT_MODIFIED = -32801


@dataclass
class LSPError:
    """LSP error representation."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        error_dict: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            error_dict["data"] = self.data
        return error_dict


@dataclass
class LSPMessage:
    """Base LSP message."""
    jsonrpc: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class LSPRequest(LSPMessage):
    """LSP request message."""
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, method: str, params: Optional[Dict[str, Any]] = None) -> 'LSPRequest':
        return cls(
            jsonrpc="2.0",
            id=str(uuid.uuid4()),
            method=method,
            params=params
        )


@dataclass
class LSPResponse(LSPMessage):
    """LSP response message."""
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[LSPError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        response_dict: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            response_dict["error"] = self.error.to_dict()
        else:
            response_dict["result"] = self.result
        return response_dict


@dataclass
class LSPNotification(LSPMessage):
    """LSP notification message."""
    method: str
    params: Optional[Dict[str, Any]] = None


class ProtocolHandler:
    """
    Handles LSP protocol message parsing, validation, and routing.
    
    Features:
    - Message parsing and validation
    - Request/response correlation
    - Notification handling
    - Error handling and reporting
    - Protocol compliance checking
    """
    
    def __init__(self):
        self._pending_requests: Dict[Union[str, int], asyncio.Future] = {}
        self._notification_handlers: Dict[str, List[Callable]] = {}
        self._request_handlers: Dict[str, Callable] = {}
        self._message_id_counter = 0
    
    def generate_message_id(self) -> str:
        """Generate a unique message ID."""
        self._message_id_counter += 1
        return f"serena_{self._message_id_counter}"
    
    def parse_message(self, raw_message: str) -> Union[LSPRequest, LSPResponse, LSPNotification]:
        """
        Parse a raw LSP message string into appropriate message object.
        
        Args:
            raw_message: Raw JSON string message
            
        Returns:
            Parsed LSP message object
            
        Raises:
            ValueError: If message is invalid or malformed
        """
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LSP message: {e}")
        
        # Validate jsonrpc version
        if data.get("jsonrpc") != "2.0":
            raise ValueError("Invalid or missing jsonrpc version")
        
        # Determine message type and parse accordingly
        if "id" in data:
            if "method" in data:
                # Request
                return LSPRequest(
                    jsonrpc="2.0",
                    id=data["id"],
                    method=data["method"],
                    params=data.get("params")
                )
            else:
                # Response
                error_data = data.get("error")
                error = None
                if error_data:
                    error = LSPError(
                        code=error_data["code"],
                        message=error_data["message"],
                        data=error_data.get("data")
                    )
                
                return LSPResponse(
                    jsonrpc="2.0",
                    id=data["id"],
                    result=data.get("result"),
                    error=error
                )
        else:
            # Notification
            if "method" not in data:
                raise ValueError("Notification missing method")
            
            return LSPNotification(
                jsonrpc="2.0",
                method=data["method"],
                params=data.get("params")
            )
    
    def create_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> LSPRequest:
        """Create a new LSP request with unique ID."""
        return LSPRequest(
            jsonrpc="2.0",
            id=self.generate_message_id(),
            method=method,
            params=params
        )
    
    def create_response(self, request_id: Union[str, int], 
                       result: Optional[Any] = None,
                       error: Optional[LSPError] = None) -> LSPResponse:
        """Create an LSP response for a given request."""
        return LSPResponse(
            jsonrpc="2.0",
            id=request_id,
            result=result,
            error=error
        )
    
    def create_notification(self, method: str, 
                          params: Optional[Dict[str, Any]] = None) -> LSPNotification:
        """Create an LSP notification."""
        return LSPNotification(
            jsonrpc="2.0",
            method=method,
            params=params
        )
    
    def create_error_response(self, request_id: Union[str, int], 
                            code: ErrorCode, message: str,
                            data: Optional[Any] = None) -> LSPResponse:
        """Create an error response."""
        error = LSPError(code=code.value, message=message, data=data)
        return LSPResponse(jsonrpc="2.0", id=request_id, error=error)
    
    def register_request_handler(self, method: str, handler: Callable):
        """Register a handler for incoming requests."""
        self._request_handlers[method] = handler
    
    def register_notification_handler(self, method: str, handler: Callable):
        """Register a handler for incoming notifications."""
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)
    
    async def handle_message(self, message: Union[LSPRequest, LSPResponse, LSPNotification]) -> Optional[LSPResponse]:
        """
        Handle an incoming LSP message.
        
        Args:
            message: Parsed LSP message
            
        Returns:
            Response message if handling a request, None otherwise
        """
        try:
            if isinstance(message, LSPRequest):
                return await self._handle_request(message)
            elif isinstance(message, LSPResponse):
                await self._handle_response(message)
            elif isinstance(message, LSPNotification):
                await self._handle_notification(message)
        except Exception as e:
            logger.error(f"Error handling LSP message: {e}")
            if isinstance(message, LSPRequest):
                return self.create_error_response(
                    message.id,
                    ErrorCode.INTERNAL_ERROR,
                    f"Internal error: {str(e)}"
                )
        
        return None
    
    async def _handle_request(self, request: LSPRequest) -> LSPResponse:
        """Handle incoming request."""
        handler = self._request_handlers.get(request.method)
        
        if not handler:
            return self.create_error_response(
                request.id,
                ErrorCode.METHOD_NOT_FOUND,
                f"Method '{request.method}' not found"
            )
        
        try:
            result = await handler(request.params or {})
            return self.create_response(request.id, result=result)
        except Exception as e:
            return self.create_error_response(
                request.id,
                ErrorCode.INTERNAL_ERROR,
                f"Handler error: {str(e)}"
            )
    
    async def _handle_response(self, response: LSPResponse):
        """Handle incoming response."""
        future = self._pending_requests.get(response.id)
        if future and not future.done():
            if response.error:
                future.set_exception(
                    Exception(f"LSP Error {response.error.code}: {response.error.message}")
                )
            else:
                future.set_result(response.result)
            
            del self._pending_requests[response.id]
    
    async def _handle_notification(self, notification: LSPNotification):
        """Handle incoming notification."""
        handlers = self._notification_handlers.get(notification.method, [])
        
        for handler in handlers:
            try:
                await handler(notification.params or {})
            except Exception as e:
                logger.error(f"Error in notification handler for {notification.method}: {e}")
    
    def track_request(self, request: LSPRequest) -> asyncio.Future:
        """Track a request for response correlation."""
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request.id] = future
        return future
    
    def cancel_request(self, request_id: Union[str, int]):
        """Cancel a pending request."""
        future = self._pending_requests.get(request_id)
        if future and not future.done():
            future.cancel()
            del self._pending_requests[request_id]
    
    def get_pending_requests(self) -> List[Union[str, int]]:
        """Get list of pending request IDs."""
        return list(self._pending_requests.keys())
    
    def cleanup_completed_requests(self):
        """Clean up completed or cancelled requests."""
        completed_ids = [
            req_id for req_id, future in self._pending_requests.items()
            if future.done()
        ]
        
        for req_id in completed_ids:
            del self._pending_requests[req_id]


class SerenaProtocolExtensions:
    """
    Serena-specific LSP protocol extensions.
    
    Defines custom methods and capabilities specific to Serena analysis servers.
    """
    
    # Serena-specific methods
    SERENA_ANALYZE_FILE = "serena/analyzeFile"
    SERENA_GET_ERRORS = "serena/getErrors"
    SERENA_GET_COMPREHENSIVE_ERRORS = "serena/getComprehensiveErrors"
    SERENA_ANALYZE_CODEBASE = "serena/analyzeCodebase"
    SERENA_GET_CONTEXT = "serena/getContext"
    SERENA_REFRESH_ANALYSIS = "serena/refreshAnalysis"
    
    # Serena-specific notifications
    SERENA_ANALYSIS_COMPLETE = "serena/analysisComplete"
    SERENA_ERROR_UPDATED = "serena/errorUpdated"
    SERENA_PROGRESS = "serena/progress"
    
    @staticmethod
    def create_analyze_file_request(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Create parameters for file analysis request."""
        params: Dict[str, Any] = {"uri": f"file://{file_path}"}
        if content is not None:
            params["content"] = content
        return params
    
    @staticmethod
    def create_get_errors_request(file_path: Optional[str] = None, 
                                severity_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create parameters for error retrieval request."""
        params: Dict[str, Any] = {}
        if file_path:
            params["uri"] = f"file://{file_path}"
        if severity_filter:
            params["severityFilter"] = severity_filter
        return params
    
    @staticmethod
    def create_comprehensive_errors_request(include_context: bool = True,
                                          include_suggestions: bool = True,
                                          max_errors: Optional[int] = None) -> Dict[str, Any]:
        """Create parameters for comprehensive error analysis request."""
        params: Dict[str, Any] = {
            "includeContext": include_context,
            "includeSuggestions": include_suggestions
        }
        if max_errors is not None:
            params["maxErrors"] = max_errors
        return params
    
    @staticmethod
    def create_analyze_codebase_request(root_path: str, 
                                      file_patterns: Optional[List[str]] = None,
                                      exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create parameters for codebase analysis request."""
        params: Dict[str, Any] = {"rootUri": f"file://{root_path}"}
        if file_patterns:
            params["includePatterns"] = file_patterns
        if exclude_patterns:
            params["excludePatterns"] = exclude_patterns
        return params
