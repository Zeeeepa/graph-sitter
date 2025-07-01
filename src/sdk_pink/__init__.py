"""
SDK Pink - Enhanced codebase analysis with Pink integration

This module provides the Pink-enhanced codebase functionality that was
previously named codegen_sdk_pink, now renamed to Sdk_Pink.
"""

from .codebase import Codebase
from .analyzer import PinkAnalyzer
from .types import PinkAnalysisResult, PinkConfig

__version__ = "1.0.0"
__all__ = ["Codebase", "PinkAnalyzer", "PinkAnalysisResult", "PinkConfig"]

