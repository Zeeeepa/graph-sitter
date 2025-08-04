"""
Main dashboard state management.

This module contains the root state class that coordinates all dashboard functionality.
"""

import reflex as rx
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
import json
from datetime import datetime


class DashboardState(rx.State):
    """Main dashboard state that coordinates all functionality."""
    
    # Application state
    current_page: str = "dashboard"
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""
    
    # Codebase state
    selected_codebase_path: str = ""
    codebase_loaded: bool = False
    available_codebases: List[Dict[str, Any]] = []
    
    # Analysis state
    analysis_running: bool = False
    analysis_progress: float = 0.0
    analysis_status: str = "Ready"
    last_analysis_time: str = ""
    
    # UI state
    sidebar_collapsed: bool = False
    active_tab: str = "overview"
    theme_mode: str = "light"
    
    # Quick stats for header
    total_files: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_symbols: int = 0
    
    # Analysis results storage
    analysis_results: Dict[str, Any] = {}
    
    def __init__(self, *args, **kwargs):
        """Initialize the dashboard state."""
        super().__init__(*args, **kwargs)
        self._initialize_available_codebases()
    
    def _initialize_available_codebases(self):
        """Initialize the list of available codebases."""
        try:
            # Look for common codebase locations
            current_dir = Path(".")
            parent_dir = Path("..")
            
            codebases = []
            
            # Add current directory if it has Python files
            if self._has_python_files(current_dir):
                codebases.append({
                    "name": "Current Directory",
                    "path": str(current_dir.resolve()),
                    "description": "Current working directory",
                    "file_count": self._count_python_files(current_dir)
                })
            
            # Add src directory if it exists
            src_dir = current_dir / "src"
            if src_dir.exists() and self._has_python_files(src_dir):
                codebases.append({
                    "name": "Source Directory",
                    "path": str(src_dir.resolve()),
                    "description": "Source code directory",
                    "file_count": self._count_python_files(src_dir)
                })
            
            # Add graph_sitter source if it exists
            gs_src = current_dir / "src" / "graph_sitter"
            if gs_src.exists():
                codebases.append({
                    "name": "Graph-Sitter Core",
                    "path": str(gs_src.resolve()),
                    "description": "Graph-sitter core library",
                    "file_count": self._count_python_files(gs_src)
                })
            
            self.available_codebases = codebases
            
        except Exception as e:
            print(f"Error initializing codebases: {e}")
            self.available_codebases = []
    
    def _has_python_files(self, path: Path) -> bool:
        """Check if directory has Python files."""
        try:
            return any(path.rglob("*.py"))
        except Exception:
            return False
    
    def _count_python_files(self, path: Path) -> int:
        """Count Python files in directory."""
        try:
            return len(list(path.rglob("*.py")))
        except Exception:
            return 0
    
    # Event handlers
    def set_current_page(self, page: str):
        """Set the current page."""
        self.current_page = page
    
    def toggle_sidebar(self):
        """Toggle sidebar collapsed state."""
        self.sidebar_collapsed = not self.sidebar_collapsed
    
    def set_active_tab(self, tab: str):
        """Set the active tab."""
        self.active_tab = tab
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
    
    def select_codebase(self, codebase_path: str):
        """Select a codebase for analysis."""
        self.selected_codebase_path = codebase_path
        self.codebase_loaded = False
        self.clear_messages()
        
        # Reset stats
        self.total_files = 0
        self.total_errors = 0
        self.total_warnings = 0
        self.total_symbols = 0
    
    async def load_codebase(self):
        """Load the selected codebase."""
        if not self.selected_codebase_path:
            self.set_error("No codebase selected")
            return
        
        self.is_loading = True
        self.clear_messages()
        
        try:
            # Simulate codebase loading
            await asyncio.sleep(1)
            
            # Update basic stats
            path = Path(self.selected_codebase_path)
            if path.exists():
                self.total_files = self._count_python_files(path)
                self.codebase_loaded = True
                self.set_success(f"Loaded codebase: {path.name}")
            else:
                self.set_error("Codebase path does not exist")
                
        except Exception as e:
            self.set_error(f"Failed to load codebase: {str(e)}")
        finally:
            self.is_loading = False
    
    async def run_analysis(self):
        """Run comprehensive analysis on the loaded codebase."""
        if not self.codebase_loaded:
            self.set_error("No codebase loaded")
            return
        
        self.analysis_running = True
        self.analysis_progress = 0.0
        self.analysis_status = "Starting analysis..."
        self.clear_messages()
        
        try:
            # Import and initialize the analyzer
            from ..analysis.unified_analyzer import UnifiedAnalyzer
            
            analyzer = UnifiedAnalyzer(self.selected_codebase_path)
            
            # Progress callback
            async def progress_callback(status: str, progress: float):
                self.analysis_status = status
                self.analysis_progress = progress
                await asyncio.sleep(0.1)  # Allow UI to update
            
            # Run the analysis
            results = await analyzer.run_comprehensive_analysis(progress_callback)
            
            if "error" in results:
                self.set_error(results["error"])
                return
            
            # Update stats from real analysis results
            health = results.get("codebase_health", {})
            self.total_files = health.get("total_files", 0)
            self.total_errors = health.get("total_errors", 0)
            self.total_warnings = health.get("total_warnings", 0)
            self.total_symbols = health.get("total_symbols", 0)
            self.last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Store analysis results for other components
            self.analysis_results = results
            
            self.set_success("Analysis completed successfully!")
            
        except Exception as e:
            self.set_error(f"Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.analysis_running = False
            self.analysis_status = "Ready"
    
    def clear_messages(self):
        """Clear error and success messages."""
        self.error_message = ""
        self.success_message = ""
    
    def set_error(self, message: str):
        """Set an error message."""
        self.error_message = message
        self.success_message = ""
    
    def set_success(self, message: str):
        """Set a success message."""
        self.success_message = message
        self.error_message = ""
    
    # Computed properties
    @rx.var
    def analysis_progress_percent(self) -> str:
        """Get analysis progress as percentage string."""
        return f"{self.analysis_progress:.0f}%"
    
    @rx.var
    def has_messages(self) -> bool:
        """Check if there are any messages to display."""
        return bool(self.error_message or self.success_message)
    
    @rx.var
    def codebase_name(self) -> str:
        """Get the name of the selected codebase."""
        if self.selected_codebase_path:
            return Path(self.selected_codebase_path).name
        return "No codebase selected"
    
    @rx.var
    def analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of analysis results."""
        return {
            "files": self.total_files,
            "errors": self.total_errors,
            "warnings": self.total_warnings,
            "symbols": self.total_symbols,
            "last_run": self.last_analysis_time
        }
