"""
Serena Core Integration

Main orchestrator for all Serena LSP capabilities in graph-sitter.
"""

import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge, ErrorInfo
from graph_sitter.core.codebase import Codebase
from .types import SerenaCapability, SerenaConfig

logger = get_logger(__name__)


class SerenaCore:
    """
    Core Serena integration for graph-sitter.
    
    Orchestrates all Serena LSP capabilities and provides unified interface
    for real-time code intelligence, refactoring, and advanced analysis.
    """
    
    def __init__(self, codebase: Codebase, config: Optional[SerenaConfig] = None):
        self.codebase = codebase
        self.config = config or SerenaConfig()
        self.repo_path = Path(codebase.repo_path)
        
        # Core components
        self.lsp_bridge = SerenaLSPBridge(str(self.repo_path))
        self._capabilities: Dict[SerenaCapability, Any] = {}
        self._event_loop = None
        self._background_thread = None
        self._shutdown_event = threading.Event()
        
        # Initialize capabilities
        self._initialize_capabilities()
        
        # Start background processing if realtime is enabled
        if self.config.realtime_analysis:
            self._start_background_processing()
    
    def _initialize_capabilities(self) -> None:
        """Initialize enabled Serena capabilities."""
        try:
            for capability in self.config.enabled_capabilities:
                self._initialize_capability(capability)
            
            logger.info(f"Serena initialized with {len(self._capabilities)} capabilities")
            
        except Exception as e:
            logger.error(f"Failed to initialize Serena capabilities: {e}")
    
    def _initialize_capability(self, capability: SerenaCapability) -> None:
        """Initialize a specific capability."""
        try:
            if capability == SerenaCapability.INTELLIGENCE:
                from .intelligence import CodeIntelligence
                self._capabilities[capability] = CodeIntelligence(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.REFACTORING:
                from .refactoring import RefactoringEngine
                self._capabilities[capability] = RefactoringEngine(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.ACTIONS:
                from .actions import CodeActions
                self._capabilities[capability] = CodeActions(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.GENERATION:
                from .generation import CodeGenerator
                self._capabilities[capability] = CodeGenerator(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.SEARCH:
                from .search import SemanticSearch
                self._capabilities[capability] = SemanticSearch(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.ANALYSIS:
                from .analysis import RealtimeAnalyzer
                self._capabilities[capability] = RealtimeAnalyzer(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.REALTIME:
                from .realtime import RealtimeAnalyzer
                self._capabilities[capability] = RealtimeAnalyzer(self.codebase, self.lsp_bridge)
            
            elif capability == SerenaCapability.SYMBOLS:
                from .symbols import SymbolIntelligence
                self._capabilities[capability] = SymbolIntelligence(self.codebase, self.lsp_bridge)
            
            logger.debug(f"Initialized {capability.value} capability")
            
        except ImportError as e:
            logger.warning(f"Could not initialize {capability.value}: {e}")
        except Exception as e:
            logger.error(f"Error initializing {capability.value}: {e}")
    
    def _start_background_processing(self) -> None:
        """Start background thread for real-time processing."""
        if self._background_thread is not None:
            return
        
        self._background_thread = threading.Thread(
            target=self._background_worker,
            daemon=True,
            name="SerenaBackgroundWorker"
        )
        self._background_thread.start()
        logger.info("Started Serena background processing")
    
    def _background_worker(self) -> None:
        """Background worker for real-time analysis."""
        try:
            # Create event loop for async operations
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            
            # Start real-time analyzer if available
            if SerenaCapability.REALTIME in self._capabilities:
                realtime_analyzer = self._capabilities[SerenaCapability.REALTIME]
                self._event_loop.run_until_complete(
                    realtime_analyzer.start_monitoring()
                )
            
            # Keep running until shutdown
            while not self._shutdown_event.is_set():
                self._event_loop.run_until_complete(asyncio.sleep(0.1))
                
        except Exception as e:
            logger.error(f"Error in background worker: {e}")
        finally:
            if self._event_loop:
                self._event_loop.close()
    
    # Intelligence Methods
    def get_symbol_info(self, file_path: str, line: int, character: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Get detailed symbol information at the specified position."""
        if SerenaCapability.INTELLIGENCE not in self._capabilities:
            raise ValueError("Intelligence capability not enabled")
        
        intelligence = self._capabilities[SerenaCapability.INTELLIGENCE]
        return intelligence.get_symbol_info(file_path, line, character, **kwargs)
    
    def generate_code(self, prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Generate code based on the provided prompt."""
        if SerenaCapability.GENERATION not in self._capabilities:
            # Fallback to intelligence capability for basic generation
            if SerenaCapability.INTELLIGENCE not in self._capabilities:
                raise ValueError("Neither generation nor intelligence capability enabled")
            intelligence = self._capabilities[SerenaCapability.INTELLIGENCE]
            return intelligence.generate_code(prompt, **kwargs)
        
        generator = self._capabilities[SerenaCapability.GENERATION]
        return generator.generate_code(prompt, **kwargs)
    
    def get_completions(self, file_path: str, line: int, character: int, **kwargs) -> List[Dict[str, Any]]:
        """Get code completions at the specified position."""
        if SerenaCapability.INTELLIGENCE not in self._capabilities:
            return []
        
        intelligence = self._capabilities[SerenaCapability.INTELLIGENCE]
        return intelligence.get_completions(file_path, line, character, **kwargs)
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get hover information for symbol at position."""
        if SerenaCapability.INTELLIGENCE not in self._capabilities:
            return None
        
        intelligence = self._capabilities[SerenaCapability.INTELLIGENCE]
        return intelligence.get_hover_info(file_path, line, character)
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get signature help for function call at position."""
        if SerenaCapability.INTELLIGENCE not in self._capabilities:
            return None
        
        intelligence = self._capabilities[SerenaCapability.INTELLIGENCE]
        return intelligence.get_signature_help(file_path, line, character)
    
    # Refactoring Methods
    def rename_symbol(self, file_path: str, line: int, character: int, new_name: str, preview: bool = False) -> Dict[str, Any]:
        """Rename symbol at position across all files."""
        if SerenaCapability.REFACTORING not in self._capabilities:
            return {"success": False, "error": "Refactoring capability not available"}
        
        refactoring = self._capabilities[SerenaCapability.REFACTORING]
        return refactoring.rename_symbol(file_path, line, character, new_name, preview)
    
    def extract_method(self, file_path: str, start_line: int, end_line: int, method_name: str, **kwargs) -> Dict[str, Any]:
        """Extract selected code into a new method."""
        if SerenaCapability.REFACTORING not in self._capabilities:
            return {"success": False, "error": "Refactoring capability not available"}
        
        refactoring = self._capabilities[SerenaCapability.REFACTORING]
        return refactoring.extract_method(file_path, start_line, end_line, method_name, **kwargs)
    
    def extract_variable(self, file_path: str, line: int, character: int, variable_name: str, **kwargs) -> Dict[str, Any]:
        """Extract expression into a variable."""
        if SerenaCapability.REFACTORING not in self._capabilities:
            return {"success": False, "error": "Refactoring capability not available"}
        
        refactoring = self._capabilities[SerenaCapability.REFACTORING]
        return refactoring.extract_variable(file_path, line, character, variable_name, **kwargs)
    
    # Code Actions Methods
    def get_code_actions(self, file_path: str, start_line: int, end_line: int, context: List[str] = None) -> List[Dict[str, Any]]:
        """Get available code actions for the specified range."""
        if SerenaCapability.ACTIONS not in self._capabilities:
            return []
        
        actions = self._capabilities[SerenaCapability.ACTIONS]
        return actions.get_code_actions(file_path, start_line, end_line, context or [])
    
    def apply_code_action(self, action_id: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Apply a specific code action."""
        if SerenaCapability.ACTIONS not in self._capabilities:
            return {"success": False, "error": "Code actions capability not available"}
        
        actions = self._capabilities[SerenaCapability.ACTIONS]
        return actions.apply_code_action(action_id, file_path, **kwargs)
    
    def organize_imports(self, file_path: str, remove_unused: bool = True, sort_imports: bool = True) -> Dict[str, Any]:
        """Organize imports in the specified file."""
        if SerenaCapability.ACTIONS not in self._capabilities:
            return {"success": False, "error": "Code actions capability not available"}
        
        actions = self._capabilities[SerenaCapability.ACTIONS]
        return actions.organize_imports(file_path, remove_unused, sort_imports)
    
    # Generation Methods
    def generate_boilerplate(self, template: str, context: Dict[str, Any], target_file: str = None) -> Dict[str, Any]:
        """Generate boilerplate code from template."""
        if SerenaCapability.GENERATION not in self._capabilities:
            return {"success": False, "error": "Code generation capability not available"}
        
        generator = self._capabilities[SerenaCapability.GENERATION]
        return generator.generate_boilerplate(template, context, target_file)
    
    def generate_tests(self, target_function: str, test_types: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate tests for the specified function."""
        if SerenaCapability.GENERATION not in self._capabilities:
            return {"success": False, "error": "Code generation capability not available"}
        
        generator = self._capabilities[SerenaCapability.GENERATION]
        return generator.generate_tests(target_function, test_types or ["unit"], **kwargs)
    
    def generate_documentation(self, target: str, format: str = "docstring", **kwargs) -> Dict[str, Any]:
        """Generate documentation for the specified target."""
        if SerenaCapability.GENERATION not in self._capabilities:
            return {"success": False, "error": "Code generation capability not available"}
        
        generator = self._capabilities[SerenaCapability.GENERATION]
        return generator.generate_documentation(target, format, **kwargs)
    
    # Search Methods
    def semantic_search(self, query: str, language: str = "natural", **kwargs) -> List[Dict[str, Any]]:
        """Perform semantic search across the codebase."""
        if SerenaCapability.SEARCH not in self._capabilities:
            return []
        
        search = self._capabilities[SerenaCapability.SEARCH]
        return search.semantic_search(query, language, **kwargs)
    
    def find_code_patterns(self, pattern: str, suggest_improvements: bool = False) -> List[Dict[str, Any]]:
        """Find code patterns matching the specified pattern."""
        if SerenaCapability.SEARCH not in self._capabilities:
            return []
        
        search = self._capabilities[SerenaCapability.SEARCH]
        return search.find_code_patterns(pattern, suggest_improvements)
    
    def find_similar_code(self, reference_code: str, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find code similar to the reference code."""
        if SerenaCapability.SEARCH not in self._capabilities:
            return []
        
        search = self._capabilities[SerenaCapability.SEARCH]
        return search.find_similar_code(reference_code, similarity_threshold)
    
    # Symbol Intelligence Methods
    def get_symbol_context(self, symbol: str, include_dependencies: bool = True, **kwargs) -> Dict[str, Any]:
        """Get comprehensive context for a symbol."""
        if SerenaCapability.SYMBOLS not in self._capabilities:
            return {}
        
        symbols = self._capabilities[SerenaCapability.SYMBOLS]
        return symbols.get_symbol_context(symbol, include_dependencies, **kwargs)
    
    def analyze_symbol_impact(self, symbol: str, change_type: str) -> Dict[str, Any]:
        """Analyze the impact of changing a symbol."""
        if SerenaCapability.SYMBOLS not in self._capabilities:
            return {}
        
        symbols = self._capabilities[SerenaCapability.SYMBOLS]
        return symbols.analyze_symbol_impact(symbol, change_type)
    
    # Real-time Methods
    def enable_realtime_analysis(self, watch_patterns: List[str] = None, auto_refresh: bool = True) -> bool:
        """Enable real-time analysis with file watching."""
        if SerenaCapability.REALTIME not in self._capabilities:
            return False
        
        realtime = self._capabilities[SerenaCapability.REALTIME]
        return realtime.enable_analysis(watch_patterns or self.config.file_watch_patterns, auto_refresh)
    
    def disable_realtime_analysis(self) -> bool:
        """Disable real-time analysis."""
        if SerenaCapability.REALTIME not in self._capabilities:
            return False
        
        realtime = self._capabilities[SerenaCapability.REALTIME]
        return realtime.disable_analysis()
    
    # Analysis Methods
    def analyze_file(self, file_path: str, force: bool = False) -> Optional[Dict[str, Any]]:
        """Analyze a specific file for issues and metrics."""
        if SerenaCapability.ANALYSIS not in self._capabilities:
            raise ValueError("Analysis capability not enabled")
        
        analyzer = self._capabilities[SerenaCapability.ANALYSIS]
        result = analyzer.analyze_file(file_path, force=force)
        return result.__dict__ if result else None
    
    def get_analysis_results(self, file_paths: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Get analysis results for specified files or all analyzed files."""
        if SerenaCapability.ANALYSIS not in self._capabilities:
            raise ValueError("Analysis capability not enabled")
        
        analyzer = self._capabilities[SerenaCapability.ANALYSIS]
        results = analyzer.get_analysis_results(file_paths)
        return {path: result.__dict__ for path, result in results.items()}
    
    def queue_file_analysis(self, file_path: str) -> None:
        """Queue a file for background analysis."""
        if SerenaCapability.ANALYSIS not in self._capabilities:
            raise ValueError("Analysis capability not enabled")
        
        analyzer = self._capabilities[SerenaCapability.ANALYSIS]
        analyzer.queue_analysis(file_path)
    
    def start_analysis_engine(self) -> None:
        """Start the real-time analysis engine."""
        if SerenaCapability.ANALYSIS not in self._capabilities:
            raise ValueError("Analysis capability not enabled")
        
        analyzer = self._capabilities[SerenaCapability.ANALYSIS]
        analyzer.start()
    
    def stop_analysis_engine(self) -> None:
        """Stop the real-time analysis engine."""
        if SerenaCapability.ANALYSIS not in self._capabilities:
            raise ValueError("Analysis capability not enabled")
        
        analyzer = self._capabilities[SerenaCapability.ANALYSIS]
        analyzer.stop()
    
    # Utility Methods
    def get_diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics from LSP bridge."""
        return self.lsp_bridge.get_diagnostics()
    
    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        return self.lsp_bridge.get_file_diagnostics(file_path)
    
    def refresh_diagnostics(self) -> None:
        """Refresh diagnostic information."""
        self.lsp_bridge.refresh_diagnostics()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of Serena integration."""
        capability_status = {}
        for cap, instance in self._capabilities.items():
            if hasattr(instance, 'get_status'):
                capability_status[cap.value] = instance.get_status()
            else:
                capability_status[cap.value] = {"available": True}
        
        return {
            "enabled_capabilities": [cap.value for cap in self.config.enabled_capabilities],
            "active_capabilities": list(capability_status.keys()),
            "realtime_analysis": self.config.realtime_analysis,
            "background_thread_active": self._background_thread is not None and self._background_thread.is_alive(),
            "lsp_bridge_status": self.lsp_bridge.get_status(),
            "capability_details": capability_status
        }
    
    def shutdown(self) -> None:
        """Shutdown Serena integration and cleanup resources."""
        logger.info("Shutting down Serena integration")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Shutdown capabilities
        for capability, instance in self._capabilities.items():
            try:
                if hasattr(instance, 'shutdown'):
                    instance.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {capability.value}: {e}")
        
        # Shutdown LSP bridge
        self.lsp_bridge.shutdown()
        
        # Wait for background thread
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=5.0)
        
        # Close event loop
        if self._event_loop and not self._event_loop.is_closed():
            self._event_loop.close()
        
        logger.info("Serena integration shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
