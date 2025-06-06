"""
Graph-sitter Configuration Manager

Manages advanced graph-sitter configuration options based on
https://graph-sitter.com/introduction/advanced-settings
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.configs.models.secrets import SecretsConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    CodebaseConfig = None
    SecretsConfig = None


class GraphSitterConfigManager:
    """Manages graph-sitter configuration for analysis."""
    
    def __init__(self, config=None):
        """Initialize configuration manager."""
        self.config = config
    
    def create_optimized_config(self, analysis_type: str = "comprehensive") -> Optional[CodebaseConfig]:
        """
        Create optimized CodebaseConfig for different analysis types.
        
        Args:
            analysis_type: Type of analysis (comprehensive, fast, debug)
            
        Returns:
            Optimized CodebaseConfig or None if graph-sitter not available
        """
        if not GRAPH_SITTER_AVAILABLE:
            logger.warning("Graph-sitter not available, cannot create config")
            return None
        
        if analysis_type == "comprehensive":
            return self._create_comprehensive_config()
        elif analysis_type == "fast":
            return self._create_fast_config()
        elif analysis_type == "debug":
            return self._create_debug_config()
        else:
            return self._create_default_config()
    
    def _create_comprehensive_config(self) -> CodebaseConfig:
        """Create config for comprehensive analysis."""
        return CodebaseConfig(
            debug=False,
            verify_graph=True,
            track_graph=True,
            method_usages=True,
            sync_enabled=True,
            full_range_index=True,
            ignore_process_errors=True,
            disable_graph=False,
            disable_file_parse=False,
            exp_lazy_graph=False,
            generics=True,
            py_resolve_syspath=True,
            allow_external=False,
            ts_dependency_manager=True,
            ts_language_engine=True,
            v8_ts_engine=False,
            unpacking_assignment_partial_removal=True
        )
    
    def _create_fast_config(self) -> CodebaseConfig:
        """Create config for fast analysis."""
        return CodebaseConfig(
            debug=False,
            verify_graph=False,
            track_graph=False,
            method_usages=True,
            sync_enabled=False,
            full_range_index=False,
            ignore_process_errors=True,
            disable_graph=False,
            disable_file_parse=False,
            exp_lazy_graph=True,
            generics=False,
            py_resolve_syspath=False,
            allow_external=False,
            ts_dependency_manager=False,
            ts_language_engine=False,
            v8_ts_engine=False,
            unpacking_assignment_partial_removal=False
        )
    
    def _create_debug_config(self) -> CodebaseConfig:
        """Create config for debugging."""
        return CodebaseConfig(
            debug=True,
            verify_graph=True,
            track_graph=True,
            method_usages=True,
            sync_enabled=True,
            full_range_index=True,
            ignore_process_errors=False,
            disable_graph=False,
            disable_file_parse=False,
            exp_lazy_graph=False,
            generics=True,
            py_resolve_syspath=True,
            allow_external=True,
            ts_dependency_manager=True,
            ts_language_engine=True,
            v8_ts_engine=False,
            unpacking_assignment_partial_removal=True
        )
    
    def _create_default_config(self) -> CodebaseConfig:
        """Create default config."""
        return CodebaseConfig(
            debug=False,
            method_usages=True,
            generics=True,
            ignore_process_errors=True
        )

