"""
Application State Management for Codebase Dashboard

Manages the global state for repository analysis, tree data, issues, and UI state.
"""

import reflex as rx
from typing import Dict, List, Any, Optional, Union
import asyncio
import httpx
from datetime import datetime
from enum import Enum


class AnalysisStatus(Enum):
    """Analysis status enumeration."""
    IDLE = "idle"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"


class IssueSeverity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class TreeNodeType(Enum):
    """Tree node types."""
    FOLDER = "folder"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"


class AppState(rx.State):
    """Main application state for the codebase dashboard."""
    
    # Repository and Analysis State
    repo_url: str = ""
    analysis_status: str = AnalysisStatus.IDLE.value
    analysis_progress: int = 0
    analysis_message: str = ""
    analysis_id: Optional[str] = None
    analysis_start_time: Optional[datetime] = None
    analysis_duration: Optional[float] = None
    
    # Tree Structure Data
    tree_data: Dict[str, Any] = {}
    expanded_nodes: List[str] = []
    selected_node: Optional[str] = None
    
    # Issues and Errors
    issues: List[Dict[str, Any]] = []
    issues_by_severity: Dict[str, List[Dict[str, Any]]] = {
        "critical": [],
        "major": [],
        "minor": []
    }
    total_issues: int = 0
    
    # Dead Code Analysis
    dead_code_functions: List[Dict[str, Any]] = []
    dead_code_classes: List[Dict[str, Any]] = []
    dead_code_imports: List[Dict[str, Any]] = []
    
    # Important Functions and Entry Points
    entry_points: List[Dict[str, Any]] = []
    important_functions: List[Dict[str, Any]] = []
    most_called_functions: List[Dict[str, Any]] = []
    recursive_functions: List[Dict[str, Any]] = []
    
    # Codebase Statistics
    codebase_stats: Dict[str, Any] = {
        "total_files": 0,
        "total_functions": 0,
        "total_classes": 0,
        "total_imports": 0,
        "lines_of_code": 0
    }
    
    # UI State
    show_issues_panel: bool = False
    show_dead_code_panel: bool = False
    show_important_functions_panel: bool = False
    selected_issue: Optional[Dict[str, Any]] = None
    issue_filter_severity: str = "all"
    
    # Backend API Configuration
    backend_url: str = "http://localhost:8000"
    
    async def analyze_repository(self):
        """Trigger repository analysis."""
        if not self.repo_url.strip():
            self.analysis_status = AnalysisStatus.ERROR.value
            self.analysis_message = "Please enter a repository URL"
            return
        
        self.analysis_status = AnalysisStatus.ANALYZING.value
        self.analysis_progress = 0
        self.analysis_message = "Starting analysis..."
        self.analysis_start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient() as client:
                # Start analysis
                response = await client.post(
                    f"{self.backend_url}/api/analyze",
                    json={"repo_url": self.repo_url},
                    timeout=300.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.analysis_id = result.get("analysis_id")
                    
                    # Poll for progress updates
                    await self._poll_analysis_progress()
                else:
                    self.analysis_status = AnalysisStatus.ERROR.value
                    self.analysis_message = f"Analysis failed: {response.text}"
                    
        except Exception as e:
            self.analysis_status = AnalysisStatus.ERROR.value
            self.analysis_message = f"Error: {str(e)}"
    
    async def _poll_analysis_progress(self):
        """Poll for analysis progress updates."""
        if not self.analysis_id:
            return
        
        try:
            async with httpx.AsyncClient() as client:
                while self.analysis_status == AnalysisStatus.ANALYZING.value:
                    response = await client.get(
                        f"{self.backend_url}/api/analysis/{self.analysis_id}/status"
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        self.analysis_progress = status_data.get("progress", 0)
                        self.analysis_message = status_data.get("message", "")
                        
                        if status_data.get("status") == "completed":
                            await self._load_analysis_results()
                            break
                        elif status_data.get("status") == "error":
                            self.analysis_status = AnalysisStatus.ERROR.value
                            self.analysis_message = status_data.get("error", "Analysis failed")
                            break
                    
                    await asyncio.sleep(2)  # Poll every 2 seconds
                    
        except Exception as e:
            self.analysis_status = AnalysisStatus.ERROR.value
            self.analysis_message = f"Error polling status: {str(e)}"
    
    async def _load_analysis_results(self):
        """Load complete analysis results."""
        if not self.analysis_id:
            return
        
        try:
            async with httpx.AsyncClient() as client:
                # Load tree structure
                tree_response = await client.get(
                    f"{self.backend_url}/api/analysis/{self.analysis_id}/tree"
                )
                if tree_response.status_code == 200:
                    self.tree_data = tree_response.json()
                
                # Load issues
                issues_response = await client.get(
                    f"{self.backend_url}/api/analysis/{self.analysis_id}/issues"
                )
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                    self.issues = issues_data.get("issues", [])
                    self.issues_by_severity = issues_data.get("by_severity", {})
                    self.total_issues = len(self.issues)
                
                # Load dead code analysis
                dead_code_response = await client.get(
                    f"{self.backend_url}/api/analysis/{self.analysis_id}/dead_code"
                )
                if dead_code_response.status_code == 200:
                    dead_code_data = dead_code_response.json()
                    self.dead_code_functions = dead_code_data.get("functions", [])
                    self.dead_code_classes = dead_code_data.get("classes", [])
                    self.dead_code_imports = dead_code_data.get("imports", [])
                
                # Load important functions
                important_response = await client.get(
                    f"{self.backend_url}/api/analysis/{self.analysis_id}/important_functions"
                )
                if important_response.status_code == 200:
                    important_data = important_response.json()
                    self.entry_points = important_data.get("entry_points", [])
                    self.important_functions = important_data.get("important_functions", [])
                    self.most_called_functions = important_data.get("most_called", [])
                    self.recursive_functions = important_data.get("recursive", [])
                
                # Load codebase statistics
                stats_response = await client.get(
                    f"{self.backend_url}/api/analysis/{self.analysis_id}/stats"
                )
                if stats_response.status_code == 200:
                    self.codebase_stats = stats_response.json()
                
                # Analysis completed
                self.analysis_status = AnalysisStatus.COMPLETED.value
                self.analysis_message = "Analysis completed successfully"
                if self.analysis_start_time:
                    self.analysis_duration = (datetime.now() - self.analysis_start_time).total_seconds()
                
        except Exception as e:
            self.analysis_status = AnalysisStatus.ERROR.value
            self.analysis_message = f"Error loading results: {str(e)}"
    
    def toggle_node_expansion(self, node_path: str):
        """Toggle expansion state of a tree node."""
        if node_path in self.expanded_nodes:
            self.expanded_nodes.remove(node_path)
        else:
            self.expanded_nodes.append(node_path)
    
    def select_node(self, node_path: str):
        """Select a tree node."""
        self.selected_node = node_path
        
        # Load node-specific data if needed
        if self.tree_data.get(node_path, {}).get("issues"):
            self.show_issues_panel = True
    
    def select_issue(self, issue: Dict[str, Any]):
        """Select an issue for detailed view."""
        self.selected_issue = issue
        self.show_issues_panel = True
    
    def toggle_issues_panel(self):
        """Toggle the issues panel visibility."""
        self.show_issues_panel = not self.show_issues_panel
    
    def toggle_dead_code_panel(self):
        """Toggle the dead code panel visibility."""
        self.show_dead_code_panel = not self.show_dead_code_panel
    
    def toggle_important_functions_panel(self):
        """Toggle the important functions panel visibility."""
        self.show_important_functions_panel = not self.show_important_functions_panel
    
    def set_issue_filter(self, severity: str):
        """Set the issue filter by severity."""
        self.issue_filter_severity = severity
    
    def get_filtered_issues(self) -> List[Dict[str, Any]]:
        """Get issues filtered by current severity filter."""
        if self.issue_filter_severity == "all":
            return self.issues
        return self.issues_by_severity.get(self.issue_filter_severity, [])
    
    def get_issue_count_by_severity(self, severity: str) -> int:
        """Get issue count for a specific severity."""
        return len(self.issues_by_severity.get(severity, []))
    
    def reset_analysis(self):
        """Reset analysis state for new analysis."""
        self.analysis_status = AnalysisStatus.IDLE.value
        self.analysis_progress = 0
        self.analysis_message = ""
        self.analysis_id = None
        self.analysis_start_time = None
        self.analysis_duration = None
        self.tree_data = {}
        self.expanded_nodes = []
        self.selected_node = None
        self.issues = []
        self.issues_by_severity = {"critical": [], "major": [], "minor": []}
        self.total_issues = 0
        self.dead_code_functions = []
        self.dead_code_classes = []
        self.dead_code_imports = []
        self.entry_points = []
        self.important_functions = []
        self.most_called_functions = []
        self.recursive_functions = []
        self.codebase_stats = {
            "total_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_imports": 0,
            "lines_of_code": 0
        }
        self.show_issues_panel = False
        self.show_dead_code_panel = False
        self.show_important_functions_panel = False
        self.selected_issue = None
        self.issue_filter_severity = "all"
