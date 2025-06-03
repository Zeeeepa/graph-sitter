"""
Codegen SDK Integration Module

This module provides enhanced integration with the Codegen SDK,
enabling programmatic interaction with AI Software Engineers.
"""

from .autogenlib.codegen_client import CodegenClient
from .autogenlib.task_manager import TaskManager
from .autogenlib.batch_processor import BatchProcessor

__version__ = "1.0.0"
__all__ = ["CodegenClient", "TaskManager", "BatchProcessor"]

