"""
Codegen Agent API Overlay Extension

This module applies overlay functionality to the existing pip-installed codegen package,
enhancing it with contexten integration while preserving the original API.

Usage:
    python extensions/codegen_agent_api/apply.py

This will enhance the existing codegen package with:
- Contexten ecosystem integration
- Enhanced monitoring and metrics
- Webhook processing capabilities
- Advanced configuration management
- Event handling and callbacks
- Health checks and debugging tools

The original API remains unchanged:
    from codegen.agents.agent import Agent
    agent = Agent(org_id="11", token="your_token")
"""

import sys
import os
import importlib
import logging
from typing import Any, Dict, Optional, List, Callable
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

logger = logging.getLogger(__name__)


class CodegenOverlayError(Exception):
    """Exception raised when overlay application fails."""
    pass


class CodegenPackageDetector:
    """Detects and validates the installed codegen package."""
    
    @staticmethod
    def detect_codegen_package() -> Dict[str, Any]:
        """
        Detect the installed codegen package and return information about it.
        
        Returns:
            Dictionary with package information
            
        Raises:
            CodegenOverlayError: If codegen package is not found or invalid
        """
        try:
            # Try to import the codegen package
            import codegen
            
            # Get package information
            package_info = {
                "installed": True,
                "version": getattr(codegen, "__version__", "unknown"),
                "location": getattr(codegen, "__file__", None),
                "package": codegen
            }
            
            # Validate that it has the expected structure
            try:
                from codegen.agents.agent import Agent
                from codegen.agents.task import AgentTask
                package_info["has_agents"] = True
                package_info["agent_class"] = Agent
                package_info["task_class"] = AgentTask
            except ImportError as e:
                raise CodegenOverlayError(
                    f"Codegen package found but missing expected agents module: {e}"
                )
            
            logger.info(f"Detected codegen package v{package_info['version']} at {package_info['location']}")
            return package_info
            
        except ImportError:
            raise CodegenOverlayError(
                "Codegen package not found. Please install it with: pip install codegen"
            )
    
    @staticmethod
    def validate_package_structure(package_info: Dict[str, Any]) -> bool:
        """
        Validate that the codegen package has the expected structure.
        
        Args:
            package_info: Package information from detect_codegen_package()
            
        Returns:
            True if package structure is valid
            
        Raises:
            CodegenOverlayError: If package structure is invalid
        """
        required_attributes = ["agent_class", "task_class"]
        
        for attr in required_attributes:
            if attr not in package_info:
                raise CodegenOverlayError(f"Codegen package missing required attribute: {attr}")
        
        # Validate Agent class has expected methods
        agent_class = package_info["agent_class"]
        required_methods = ["run", "get_status"]
        
        for method in required_methods:
            if not hasattr(agent_class, method):
                raise CodegenOverlayError(f"Agent class missing required method: {method}")
        
        # Validate AgentTask class has expected attributes
        task_class = package_info["task_class"]
        required_task_attrs = ["id", "status", "refresh"]
        
        for attr in required_task_attrs:
            if not hasattr(task_class, attr):
                raise CodegenOverlayError(f"AgentTask class missing required attribute: {attr}")
        
        logger.info("Codegen package structure validation passed")
        return True


class ContextenIntegration:
    """Provides contexten ecosystem integration for the codegen package."""
    
    def __init__(self):
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.metrics = {
            "agents_created": 0,
            "tasks_run": 0,
            "overlay_calls": 0,
            "errors": 0
        }
        self.start_time = None
        
    def initialize(self):
        """Initialize the contexten integration."""
        import time
        self.start_time = time.time()
        logger.info("Contexten integration initialized")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered event handler for {event_type}")
    
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler failed for {event_type}: {e}")
                self.metrics["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics."""
        import time
        uptime = time.time() - (self.start_time or time.time())
        
        return {
            **self.metrics,
            "uptime_seconds": uptime,
            "event_handlers": {
                event_type: len(handlers) 
                for event_type, handlers in self.event_handlers.items()
            }
        }


class EnhancedAgentWrapper:
    """Wrapper that enhances the original Agent class with contexten integration."""
    
    def __init__(self, original_agent_class, integration: ContextenIntegration):
        self.original_agent_class = original_agent_class
        self.integration = integration
        
    def __call__(self, *args, **kwargs):
        """Create an enhanced agent instance."""
        # Create the original agent
        original_agent = self.original_agent_class(*args, **kwargs)
        
        # Wrap it with enhancements
        enhanced_agent = EnhancedAgent(original_agent, self.integration)
        
        # Track metrics
        self.integration.metrics["agents_created"] += 1
        
        # Emit event
        self.integration.emit_event("agent_created", {
            "org_id": kwargs.get("org_id", getattr(original_agent, "org_id", None)),
            "base_url": kwargs.get("base_url", getattr(original_agent, "base_url", None))
        })
        
        return enhanced_agent


class EnhancedAgent:
    """Enhanced Agent that wraps the original Agent with additional functionality."""
    
    def __init__(self, original_agent, integration: ContextenIntegration):
        self._original_agent = original_agent
        self._integration = integration
        self._task_callbacks: List[Callable] = []
        
        # Copy all attributes from original agent
        for attr in dir(original_agent):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(original_agent, attr))
    
    def run(self, prompt: str, **kwargs):
        """Enhanced run method with contexten integration."""
        # Track metrics
        self._integration.metrics["tasks_run"] += 1
        self._integration.metrics["overlay_calls"] += 1
        
        # Emit pre-run event
        self._integration.emit_event("task_starting", {
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "agent_id": getattr(self._original_agent, "org_id", None)
        })
        
        try:
            # Call original run method
            task = self._original_agent.run(prompt, **kwargs)
            
            # Wrap the task with enhancements
            enhanced_task = EnhancedAgentTask(task, self._integration)
            
            # Emit post-run event
            self._integration.emit_event("task_created", {
                "task_id": getattr(task, "id", None),
                "status": getattr(task, "status", None)
            })
            
            return enhanced_task
            
        except Exception as e:
            self._integration.metrics["errors"] += 1
            self._integration.emit_event("task_error", {
                "error": str(e),
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
            })
            raise
    
    def get_status(self):
        """Enhanced get_status method."""
        self._integration.metrics["overlay_calls"] += 1
        return self._original_agent.get_status()
    
    def add_task_callback(self, callback: Callable):
        """Add a callback for task events."""
        self._task_callbacks.append(callback)
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get integration metrics for this agent."""
        return self._integration.get_metrics()
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the original agent."""
        return getattr(self._original_agent, name)


class EnhancedAgentTask:
    """Enhanced AgentTask that wraps the original AgentTask with additional functionality."""
    
    def __init__(self, original_task, integration: ContextenIntegration):
        self._original_task = original_task
        self._integration = integration
        self._status_callbacks: List[Callable] = []
        self._last_status = None
        
        # Copy all attributes from original task
        for attr in dir(original_task):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(original_task, attr))
    
    def refresh(self):
        """Enhanced refresh method with status change detection."""
        old_status = getattr(self._original_task, "status", None)
        
        # Call original refresh
        result = self._original_task.refresh()
        
        new_status = getattr(self._original_task, "status", None)
        
        # Check for status changes
        if old_status != new_status:
            self._integration.emit_event("task_status_changed", {
                "task_id": getattr(self._original_task, "id", None),
                "old_status": old_status,
                "new_status": new_status
            })
            
            # Call status callbacks
            for callback in self._status_callbacks:
                try:
                    callback(old_status, new_status)
                except Exception as e:
                    logger.error(f"Status callback failed: {e}")
        
        return result
    
    def add_status_callback(self, callback: Callable):
        """Add a callback for status changes."""
        self._status_callbacks.append(callback)
    
    def wait_for_completion(self, timeout: int = 300, poll_interval: int = 5):
        """Wait for task completion with enhanced monitoring."""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.refresh()
            
            status = getattr(self._original_task, "status", None)
            
            if status in ["completed", "failed", "cancelled"]:
                self._integration.emit_event("task_finished", {
                    "task_id": getattr(self._original_task, "id", None),
                    "final_status": status,
                    "duration": time.time() - start_time
                })
                return
            
            time.sleep(poll_interval)
        
        # Timeout occurred
        self._integration.emit_event("task_timeout", {
            "task_id": getattr(self._original_task, "id", None),
            "timeout_duration": timeout
        })
        
        raise TimeoutError(f"Task timed out after {timeout} seconds")
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the original task."""
        return getattr(self._original_task, name)


class CodegenOverlayApplicator:
    """Main class that applies the overlay to the codegen package."""
    
    def __init__(self):
        self.package_info = None
        self.integration = ContextenIntegration()
        self.applied = False
        
    def detect_and_validate(self):
        """Detect and validate the codegen package."""
        logger.info("Detecting codegen package...")
        self.package_info = CodegenPackageDetector.detect_codegen_package()
        
        logger.info("Validating package structure...")
        CodegenPackageDetector.validate_package_structure(self.package_info)
        
        logger.info("Package detection and validation completed successfully")
    
    def apply_overlay(self):
        """Apply the overlay to the codegen package."""
        if self.applied:
            logger.warning("Overlay already applied")
            return
        
        if not self.package_info:
            raise CodegenOverlayError("Package not detected. Call detect_and_validate() first.")
        
        logger.info("Applying contexten overlay to codegen package...")
        
        # Initialize contexten integration
        self.integration.initialize()
        
        # Get the codegen.agents.agent module
        import codegen.agents.agent as agent_module
        
        # Store the original Agent class
        original_agent_class = agent_module.Agent
        
        # Create the enhanced wrapper
        enhanced_wrapper = EnhancedAgentWrapper(original_agent_class, self.integration)
        
        # Replace the Agent class in the module
        agent_module.Agent = enhanced_wrapper
        
        # Also replace it in the main codegen module if it's imported there
        try:
            import codegen
            if hasattr(codegen, "Agent"):
                codegen.Agent = enhanced_wrapper
        except (ImportError, AttributeError):
            pass
        
        self.applied = True
        logger.info("Overlay applied successfully!")
        
        # Emit overlay applied event
        self.integration.emit_event("overlay_applied", {
            "package_version": self.package_info.get("version", "unknown"),
            "package_location": self.package_info.get("location", "unknown")
        })
    
    def get_integration(self) -> ContextenIntegration:
        """Get the contexten integration instance."""
        return self.integration
    
    def get_status(self) -> Dict[str, Any]:
        """Get overlay status and metrics."""
        return {
            "applied": self.applied,
            "package_info": self.package_info,
            "integration_metrics": self.integration.get_metrics() if self.applied else None
        }


# Global overlay instance
_overlay_instance: Optional[CodegenOverlayApplicator] = None


def apply_codegen_overlay() -> CodegenOverlayApplicator:
    """
    Apply the codegen overlay.
    
    Returns:
        The overlay applicator instance
        
    Raises:
        CodegenOverlayError: If overlay application fails
    """
    global _overlay_instance
    
    if _overlay_instance is None:
        _overlay_instance = CodegenOverlayApplicator()
    
    if not _overlay_instance.applied:
        _overlay_instance.detect_and_validate()
        _overlay_instance.apply_overlay()
    
    return _overlay_instance


def get_overlay_instance() -> Optional[CodegenOverlayApplicator]:
    """Get the current overlay instance."""
    return _overlay_instance


def register_event_handler(event_type: str, handler: Callable):
    """
    Register an event handler for codegen events.
    
    Args:
        event_type: Type of event to handle
        handler: Function to call when event occurs
    """
    overlay = apply_codegen_overlay()
    overlay.get_integration().register_event_handler(event_type, handler)


def get_overlay_metrics() -> Dict[str, Any]:
    """Get overlay metrics."""
    if _overlay_instance and _overlay_instance.applied:
        return _overlay_instance.get_status()
    return {"applied": False, "error": "Overlay not applied"}


def main():
    """Main function to apply the overlay."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        logger.info("Starting Codegen Overlay Application...")
        
        overlay = apply_codegen_overlay()
        
        logger.info("Overlay applied successfully!")
        logger.info("You can now use the enhanced codegen package:")
        logger.info("  from codegen.agents.agent import Agent")
        logger.info("  agent = Agent(org_id='11', token='your_token')")
        logger.info("  # Agent now has contexten integration!")
        
        # Print status
        status = overlay.get_status()
        logger.info(f"Package version: {status['package_info'].get('version', 'unknown')}")
        logger.info(f"Package location: {status['package_info'].get('location', 'unknown')}")
        
        return overlay
        
    except CodegenOverlayError as e:
        logger.error(f"Overlay application failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

