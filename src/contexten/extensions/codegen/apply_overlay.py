#!/usr/bin/env python3
"""
Codegen Package Overlay System

This script applies contexten extensions to an existing pip-installed codegen package.
It modifies the installed package to add enhanced functionality while preserving
the original API: from codegen.agents.agent import Agent

Usage:
    python src/contexten/extensions/codegen/apply_overlay.py

This will:
1. Detect the installed codegen package
2. Inject enhanced functionality into the package
3. Add contexten integration modules
4. Preserve the original import: from codegen.agents.agent import Agent
"""

import sys
import os
import importlib
import importlib.util
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodegenOverlayError(Exception):
    """Exception raised when overlay application fails."""
    pass


class CodegenPackageLocator:
    """Locates and validates the installed codegen package."""
    
    @staticmethod
    def find_codegen_package() -> Dict[str, Any]:
        """
        Find the installed codegen package and return its location and info.
        
        Returns:
            Dictionary with package information
            
        Raises:
            CodegenOverlayError: If codegen package is not found
        """
        try:
            # Import codegen to get its location
            import codegen
            
            # Get package path
            package_path = Path(codegen.__file__).parent
            
            # Validate structure
            agents_path = package_path / "agents"
            if not agents_path.exists():
                raise CodegenOverlayError(f"Codegen package at {package_path} missing 'agents' directory")
            
            agent_file = agents_path / "agent.py"
            if not agent_file.exists():
                raise CodegenOverlayError(f"Codegen package missing 'agents/agent.py' file")
            
            # Get version
            version = getattr(codegen, "__version__", "unknown")
            
            package_info = {
                "package_path": package_path,
                "agents_path": agents_path,
                "agent_file": agent_file,
                "version": version,
                "writable": os.access(package_path, os.W_OK)
            }
            
            logger.info(f"Found codegen package v{version} at {package_path}")
            logger.info(f"Package writable: {package_info['writable']}")
            
            return package_info
            
        except ImportError:
            raise CodegenOverlayError(
                "Codegen package not found. Please install it with: pip install codegen"
            )
        except Exception as e:
            raise CodegenOverlayError(f"Error locating codegen package: {e}")
    
    @staticmethod
    def validate_package_structure(package_info: Dict[str, Any]) -> bool:
        """
        Validate that the codegen package has the expected structure.
        
        Args:
            package_info: Package information from find_codegen_package()
            
        Returns:
            True if package structure is valid
            
        Raises:
            CodegenOverlayError: If package structure is invalid
        """
        # Check if we can import the expected classes
        try:
            from codegen.agents.agent import Agent
            from codegen.agents.task import AgentTask
            
            # Validate Agent class has expected methods
            required_methods = ["run", "get_status"]
            for method in required_methods:
                if not hasattr(Agent, method):
                    raise CodegenOverlayError(f"Agent class missing required method: {method}")
            
            # Validate AgentTask class has expected attributes
            required_attrs = ["id", "status", "refresh"]
            for attr in required_attrs:
                if not hasattr(AgentTask, attr):
                    raise CodegenOverlayError(f"AgentTask class missing required attribute: {attr}")
            
            logger.info("Codegen package structure validation passed")
            return True
            
        except ImportError as e:
            raise CodegenOverlayError(f"Failed to import codegen classes: {e}")


class ContextenExtensions:
    """Creates contexten extension modules for the codegen package."""
    
    def __init__(self, package_info: Dict[str, Any]):
        self.package_info = package_info
        self.package_path = package_info["package_path"]
        self.contexten_path = self.package_path / "contexten"
    
    def create_contexten_module(self):
        """Create the contexten integration module."""
        # Create contexten directory
        self.contexten_path.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = self.contexten_path / "__init__.py"
        init_content = '''"""
Contexten integration for codegen package.

This module provides contexten ecosystem integration for the codegen package.
"""

from .integration import ContextenIntegration
from .events import EventSystem
from .metrics import MetricsCollector
from .monitoring import HealthMonitor

__all__ = [
    "ContextenIntegration",
    "EventSystem", 
    "MetricsCollector",
    "HealthMonitor"
]
'''
        init_file.write_text(init_content)
        logger.info(f"Created {init_file}")
    
    def create_integration_module(self):
        """Create the main integration module."""
        integration_file = self.contexten_path / "integration.py"
        integration_content = '''"""
Main contexten integration for codegen package.
"""

import time
import logging
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__)


class ContextenIntegration:
    """Main contexten integration class."""
    
    def __init__(self):
        self.start_time = time.time()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.metrics = {
            "agents_created": 0,
            "tasks_run": 0,
            "overlay_calls": 0,
            "errors": 0
        }
        self.enabled = True
        
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered event handler for {event_type}")
    
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        if not self.enabled:
            return
            
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler failed for {event_type}: {e}")
                self.metrics["errors"] += 1
    
    def increment_metric(self, metric_name: str, value: int = 1):
        """Increment a metric."""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics."""
        uptime = time.time() - self.start_time
        return {
            **self.metrics,
            "uptime_seconds": uptime,
            "event_handlers": {
                event_type: len(handlers) 
                for event_type, handlers in self.event_handlers.items()
            },
            "enabled": self.enabled
        }
    
    def enable(self):
        """Enable contexten integration."""
        self.enabled = True
        logger.info("Contexten integration enabled")
    
    def disable(self):
        """Disable contexten integration."""
        self.enabled = False
        logger.info("Contexten integration disabled")


# Global integration instance
_integration = ContextenIntegration()


def get_integration() -> ContextenIntegration:
    """Get the global integration instance."""
    return _integration


def register_event_handler(event_type: str, handler: Callable):
    """Register an event handler globally."""
    _integration.register_event_handler(event_type, handler)


def emit_event(event_type: str, data: Dict[str, Any]):
    """Emit an event globally."""
    _integration.emit_event(event_type, data)


def get_metrics() -> Dict[str, Any]:
    """Get global metrics."""
    return _integration.get_metrics()
'''
        integration_file.write_text(integration_content)
        logger.info(f"Created {integration_file}")
    
    def create_events_module(self):
        """Create the events module."""
        events_file = self.contexten_path / "events.py"
        events_content = '''"""
Event system for codegen contexten integration.
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime


class EventType(str, Enum):
    """Event types for codegen operations."""
    AGENT_CREATED = "agent_created"
    TASK_STARTING = "task_starting"
    TASK_CREATED = "task_created"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_FINISHED = "task_finished"
    TASK_ERROR = "task_error"
    TASK_TIMEOUT = "task_timeout"
    OVERLAY_APPLIED = "overlay_applied"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "codegen"


class EventSystem:
    """Event system for codegen operations."""
    
    def __init__(self):
        self.handlers = {}
    
    def register(self, event_type: EventType, handler):
        """Register an event handler."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def emit(self, event_type: EventType, data: Dict[str, Any]):
        """Emit an event."""
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data
        )
        
        handlers = self.handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Event handler error: {e}")
'''
        events_file.write_text(events_content)
        logger.info(f"Created {events_file}")
    
    def create_metrics_module(self):
        """Create the metrics module."""
        metrics_file = self.contexten_path / "metrics.py"
        metrics_content = '''"""
Metrics collection for codegen contexten integration.
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict


class MetricsCollector:
    """Collects and manages metrics for codegen operations."""
    
    def __init__(self):
        self.start_time = time.time()
        self.counters = defaultdict(int)
        self.timers = {}
        self.gauges = {}
        
    def increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric."""
        self.counters[metric_name] += value
    
    def start_timer(self, timer_name: str):
        """Start a timer."""
        self.timers[timer_name] = time.time()
    
    def end_timer(self, timer_name: str) -> Optional[float]:
        """End a timer and return duration."""
        if timer_name in self.timers:
            duration = time.time() - self.timers[timer_name]
            del self.timers[timer_name]
            return duration
        return None
    
    def set_gauge(self, gauge_name: str, value: Any):
        """Set a gauge value."""
        self.gauges[gauge_name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "active_timers": list(self.timers.keys()),
            "gauges": dict(self.gauges)
        }
    
    def reset(self):
        """Reset all metrics."""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()
        self.start_time = time.time()


# Global metrics collector
_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _metrics


def increment(metric_name: str, value: int = 1):
    """Increment a counter globally."""
    _metrics.increment(metric_name, value)


def start_timer(timer_name: str):
    """Start a timer globally."""
    _metrics.start_timer(timer_name)


def end_timer(timer_name: str) -> Optional[float]:
    """End a timer globally."""
    return _metrics.end_timer(timer_name)


def set_gauge(gauge_name: str, value: Any):
    """Set a gauge globally."""
    _metrics.set_gauge(gauge_name, value)


def get_metrics() -> Dict[str, Any]:
    """Get all metrics globally."""
    return _metrics.get_metrics()
'''
        metrics_file.write_text(metrics_content)
        logger.info(f"Created {metrics_file}")
    
    def create_monitoring_module(self):
        """Create the monitoring module."""
        monitoring_file = self.contexten_path / "monitoring.py"
        monitoring_content = '''"""
Health monitoring for codegen contexten integration.
"""

import time
import psutil
import os
from typing import Dict, Any, List
from datetime import datetime


class HealthMonitor:
    """Health monitoring for codegen operations."""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = []
        
    def add_health_check(self, name: str, check_func):
        """Add a health check function."""
        self.checks.append((name, check_func))
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "checks": {},
            "overall_status": "healthy"
        }
        
        for name, check_func in self.checks:
            try:
                result = check_func()
                results["checks"][name] = {
                    "status": "healthy",
                    "result": result
                }
            except Exception as e:
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["overall_status"] = "degraded"
        
        return results
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids()),
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
        except Exception as e:
            return {"error": str(e)}


# Global health monitor
_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor."""
    return _monitor


def add_health_check(name: str, check_func):
    """Add a health check globally."""
    _monitor.add_health_check(name, check_func)


def run_health_checks() -> Dict[str, Any]:
    """Run health checks globally."""
    return _monitor.run_health_checks()


def get_system_info() -> Dict[str, Any]:
    """Get system info globally."""
    return _monitor.get_system_info()
'''
        monitoring_file.write_text(monitoring_content)
        logger.info(f"Created {monitoring_file}")
    
    def create_all_modules(self):
        """Create all contexten modules."""
        logger.info("Creating contexten extension modules...")
        self.create_contexten_module()
        self.create_integration_module()
        self.create_events_module()
        self.create_metrics_module()
        self.create_monitoring_module()
        logger.info("All contexten modules created successfully")


class AgentEnhancer:
    """Enhances the Agent class with contexten functionality."""
    
    def __init__(self, package_info: Dict[str, Any]):
        self.package_info = package_info
        self.agent_file = package_info["agent_file"]
    
    def backup_original_agent(self):
        """Create a backup of the original agent.py file."""
        backup_file = self.agent_file.with_suffix('.py.original')
        if not backup_file.exists():
            shutil.copy2(self.agent_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
    
    def enhance_agent_file(self):
        """Enhance the agent.py file with contexten integration."""
        # Read original content
        original_content = self.agent_file.read_text()
        
        # Check if already enhanced
        if "# CONTEXTEN_ENHANCED" in original_content:
            logger.info("Agent file already enhanced")
            return
        
        # Create enhanced content
        enhanced_content = self._create_enhanced_agent_content(original_content)
        
        # Write enhanced content
        self.agent_file.write_text(enhanced_content)
        logger.info(f"Enhanced {self.agent_file}")
    
    def _create_enhanced_agent_content(self, original_content: str) -> str:
        """Create enhanced agent content."""
        # Add contexten imports at the top
        contexten_imports = '''# CONTEXTEN_ENHANCED
import time
import logging
from typing import Optional, Callable, List, Dict, Any

# Import contexten integration
try:
    from ..contexten.integration import get_integration, emit_event
    from ..contexten.metrics import increment, start_timer, end_timer
    from ..contexten.events import EventType
    _CONTEXTEN_AVAILABLE = True
except ImportError:
    _CONTEXTEN_AVAILABLE = False

logger = logging.getLogger(__name__)

'''
        
        # Find the Agent class definition
        lines = original_content.split('\n')
        enhanced_lines = []
        in_agent_class = False
        agent_class_indent = 0
        
        # Add imports at the beginning
        enhanced_lines.append(contexten_imports)
        
        for i, line in enumerate(lines):
            # Skip existing imports that might conflict
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if 'contexten' not in line:
                    enhanced_lines.append(line)
                continue
            
            # Detect Agent class
            if line.strip().startswith('class Agent'):
                in_agent_class = True
                agent_class_indent = len(line) - len(line.lstrip())
                enhanced_lines.append(line)
                
                # Add contexten initialization to __init__
                enhanced_lines.append('')
                enhanced_lines.append(' ' * (agent_class_indent + 4) + '# Contexten integration')
                enhanced_lines.append(' ' * (agent_class_indent + 4) + 'def __init__(self, *args, **kwargs):')
                enhanced_lines.append(' ' * (agent_class_indent + 8) + 'super().__init__(*args, **kwargs) if hasattr(super(), "__init__") else None')
                enhanced_lines.append(' ' * (agent_class_indent + 8) + 'self._contexten_callbacks = []')
                enhanced_lines.append(' ' * (agent_class_indent + 8) + 'if _CONTEXTEN_AVAILABLE:')
                enhanced_lines.append(' ' * (agent_class_indent + 12) + 'increment("agents_created")')
                enhanced_lines.append(' ' * (agent_class_indent + 12) + 'emit_event(EventType.AGENT_CREATED, {')
                enhanced_lines.append(' ' * (agent_class_indent + 16) + '"org_id": getattr(self, "org_id", None),')
                enhanced_lines.append(' ' * (agent_class_indent + 16) + '"timestamp": time.time()')
                enhanced_lines.append(' ' * (agent_class_indent + 12) + '})')
                enhanced_lines.append('')
                continue
            
            # Detect end of Agent class
            if in_agent_class and line.strip() and not line.startswith(' '):
                in_agent_class = False
                
                # Add enhanced methods before class ends
                enhanced_methods = self._get_enhanced_methods(agent_class_indent)
                enhanced_lines.extend(enhanced_methods)
                enhanced_lines.append('')
            
            enhanced_lines.append(line)
        
        # If we're still in the Agent class at the end, add methods
        if in_agent_class:
            enhanced_methods = self._get_enhanced_methods(agent_class_indent)
            enhanced_lines.extend(enhanced_methods)
        
        return '\n'.join(enhanced_lines)
    
    def _get_enhanced_methods(self, indent: int) -> List[str]:
        """Get enhanced methods to add to Agent class."""
        methods = []
        base_indent = ' ' * (indent + 4)
        
        methods.extend([
            base_indent + 'def add_callback(self, callback: Callable):',
            base_indent + '    """Add a callback for agent events."""',
            base_indent + '    self._contexten_callbacks.append(callback)',
            '',
            base_indent + 'def get_contexten_metrics(self) -> Dict[str, Any]:',
            base_indent + '    """Get contexten metrics."""',
            base_indent + '    if _CONTEXTEN_AVAILABLE:',
            base_indent + '        from ..contexten.metrics import get_metrics',
            base_indent + '        return get_metrics()',
            base_indent + '    return {}',
            '',
            base_indent + 'def run_enhanced(self, prompt: str, **kwargs):',
            base_indent + '    """Enhanced run method with contexten integration."""',
            base_indent + '    if _CONTEXTEN_AVAILABLE:',
            base_indent + '        start_timer("task_execution")',
            base_indent + '        increment("tasks_run")',
            base_indent + '        emit_event(EventType.TASK_STARTING, {',
            base_indent + '            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,',
            base_indent + '            "timestamp": time.time()',
            base_indent + '        })',
            '',
            base_indent + '    try:',
            base_indent + '        # Call original run method',
            base_indent + '        result = self.run(prompt, **kwargs)',
            '',
            base_indent + '        if _CONTEXTEN_AVAILABLE:',
            base_indent + '            duration = end_timer("task_execution")',
            base_indent + '            emit_event(EventType.TASK_CREATED, {',
            base_indent + '                "task_id": getattr(result, "id", None),',
            base_indent + '                "duration": duration,',
            base_indent + '                "timestamp": time.time()',
            base_indent + '            })',
            '',
            base_indent + '        return result',
            '',
            base_indent + '    except Exception as e:',
            base_indent + '        if _CONTEXTEN_AVAILABLE:',
            base_indent + '            increment("errors")',
            base_indent + '            emit_event(EventType.TASK_ERROR, {',
            base_indent + '                "error": str(e),',
            base_indent + '                "timestamp": time.time()',
            base_indent + '            })',
            base_indent + '        raise',
            ''
        ])
        
        return methods


class OverlayApplicator:
    """Main class that applies the overlay to the codegen package."""
    
    def __init__(self):
        self.package_info = None
        self.applied = False
    
    def detect_package(self):
        """Detect and validate the codegen package."""
        logger.info("Detecting codegen package...")
        self.package_info = CodegenPackageLocator.find_codegen_package()
        
        if not self.package_info["writable"]:
            raise CodegenOverlayError(
                f"Codegen package at {self.package_info['package_path']} is not writable. "
                "Try running with sudo or in a virtual environment."
            )
        
        logger.info("Validating package structure...")
        CodegenPackageLocator.validate_package_structure(self.package_info)
        
        logger.info("Package detection and validation completed successfully")
    
    def apply_overlay(self):
        """Apply the overlay to the codegen package."""
        if self.applied:
            logger.warning("Overlay already applied")
            return
        
        if not self.package_info:
            raise CodegenOverlayError("Package not detected. Call detect_package() first.")
        
        logger.info("Applying contexten overlay to codegen package...")
        
        try:
            # Create contexten extension modules
            extensions = ContextenExtensions(self.package_info)
            extensions.create_all_modules()
            
            # Enhance the Agent class
            enhancer = AgentEnhancer(self.package_info)
            enhancer.backup_original_agent()
            enhancer.enhance_agent_file()
            
            self.applied = True
            logger.info("Overlay applied successfully!")
            
            # Emit overlay applied event
            try:
                from codegen.contexten.integration import emit_event
                from codegen.contexten.events import EventType
                emit_event(EventType.OVERLAY_APPLIED, {
                    "package_version": self.package_info.get("version", "unknown"),
                    "package_path": str(self.package_info.get("package_path", "unknown")),
                    "timestamp": time.time()
                })
            except ImportError:
                pass  # Contexten modules not yet importable
            
        except Exception as e:
            logger.error(f"Failed to apply overlay: {e}")
            raise CodegenOverlayError(f"Overlay application failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overlay status."""
        return {
            "applied": self.applied,
            "package_info": self.package_info,
            "timestamp": time.time()
        }


def main():
    """Main function to apply the overlay."""
    print("🚀 Codegen Package Overlay System")
    print("=" * 50)
    
    try:
        # Create and run overlay applicator
        applicator = OverlayApplicator()
        
        print("\n1. Detecting codegen package...")
        applicator.detect_package()
        
        package_info = applicator.package_info
        print(f"   ✅ Found codegen v{package_info['version']}")
        print(f"   📍 Location: {package_info['package_path']}")
        print(f"   ✏️  Writable: {package_info['writable']}")
        
        print("\n2. Applying overlay...")
        applicator.apply_overlay()
        
        print("\n✅ Overlay applied successfully!")
        print("\nYou can now use the enhanced codegen package:")
        print("   from codegen.agents.agent import Agent")
        print("   agent = Agent(org_id='11', token='your_token')")
        print("   # Agent now has contexten integration!")
        
        print("\nEnhanced features available:")
        print("   - agent.get_contexten_metrics()")
        print("   - agent.add_callback(callback_function)")
        print("   - agent.run_enhanced(prompt)")
        print("   - Automatic event emission")
        print("   - Metrics collection")
        
        print(f"\n📊 Status: {applicator.get_status()}")
        
        return applicator
        
    except CodegenOverlayError as e:
        print(f"\n❌ Overlay application failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

