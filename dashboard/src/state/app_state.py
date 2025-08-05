"""
Application State Management

Centralized state management for the codebase analysis dashboard.
Handles all data, API interactions, and UI state.
"""

import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import reflex as rx

from ..services.api_client import APIClient
from ..utils.formatters import format_file_size, format_duration
from ..utils.validators import validate_repository_url


class AnalysisState(rx.State):
    """State for analysis data and operations."""
    
    # Analysis data
    current_analysis_id: str = ""
    analysis_status: str = "idle"  # idle, analyzing, completed, error
    analysis_progress: float = 0.0
    analysis_message: str = ""
    analysis_start_time: Optional[datetime] = None
    analysis_duration: float = 0.0
    
    # Repository information
    repository_url: str = ""
    repository_name: str = ""
    repository_owner: str = ""
    
    # Tree structure data
    tree_data: Dict[str, Any] = {}
    expanded_nodes: Set[str] = set()
    selected_node: str = ""
    
    # Issues data
    all_issues: List[Dict[str, Any]] = []
    filtered_issues: List[Dict[str, Any]] = []
    issue_filter_severity: str = "all"  # all, critical, major, minor
    issue_filter_type: str = "all"
    
    # Dead code analysis
    dead_code_data: Dict[str, List[Dict[str, Any]]] = {
        "functions": [],
        "classes": [],
        "imports": []
    }
    
    # Important functions
    important_functions_data: Dict[str, List[Dict[str, Any]]] = {
        "entry_points": [],
        "important_functions": [],
        "most_called": [],
        "recursive": []
    }
    
    # Statistics
    stats_data: Dict[str, Any] = {
        "total_files": 0,
        "total_functions": 0,
        "total_classes": 0,
        "total_lines": 0,
        "total_issues": 0,
        "critical_issues": 0,
        "major_issues": 0,
        "minor_issues": 0,
        "dead_code_count": 0
    }
    
    # UI state
    active_tab: str = "tree"  # tree, issues, dead_code, important_functions, stats
    loading: bool = False
    error_message: str = ""
    show_error_modal: bool = False
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
    
    async def start_analysis(self, repo_url: str):
        """Start a new codebase analysis."""
        try:
            # Validate repository URL
            if not validate_repository_url(repo_url):
                self.error_message = "Invalid repository URL. Please provide a valid GitHub URL or local path."
                self.show_error_modal = True
                return
            
            # Reset state
            self.repository_url = repo_url
            self.analysis_status = "analyzing"
            self.analysis_progress = 0.0
            self.analysis_message = "Starting analysis..."
            self.analysis_start_time = datetime.now()
            self.loading = True
            self.error_message = ""
            
            # Extract repository info
            if repo_url.startswith("https://github.com/"):
                parts = repo_url.replace("https://github.com/", "").split("/")
                if len(parts) >= 2:
                    self.repository_owner = parts[0]
                    self.repository_name = parts[1].replace(".git", "")
            else:
                self.repository_name = repo_url.split("/")[-1]
                self.repository_owner = "local"
            
            # Start analysis via API
            response = await self.api_client.start_analysis(repo_url)
            self.current_analysis_id = response["analysis_id"]
            
            # Start polling for updates
            await self._poll_analysis_status()
            
        except Exception as e:
            self.analysis_status = "error"
            self.error_message = f"Failed to start analysis: {str(e)}"
            self.show_error_modal = True
            self.loading = False
    
    async def _poll_analysis_status(self):
        """Poll the analysis status until completion."""
        while self.analysis_status == "analyzing":
            try:
                status_data = await self.api_client.get_analysis_status(self.current_analysis_id)
                
                self.analysis_status = status_data.get("status", "analyzing")
                self.analysis_progress = status_data.get("progress", 0.0)
                self.analysis_message = status_data.get("message", "Analyzing...")
                
                if self.analysis_status == "completed":
                    await self._load_analysis_results()
                    break
                elif self.analysis_status == "error":
                    self.error_message = status_data.get("error", "Analysis failed")
                    self.show_error_modal = True
                    break
                
                # Wait before next poll
                await asyncio.sleep(2)
                
            except Exception as e:
                self.analysis_status = "error"
                self.error_message = f"Failed to get analysis status: {str(e)}"
                self.show_error_modal = True
                break
        
        self.loading = False
        if self.analysis_start_time:
            self.analysis_duration = (datetime.now() - self.analysis_start_time).total_seconds()
    
    async def _load_analysis_results(self):
        """Load all analysis results."""
        try:
            # Load tree structure
            tree_response = await self.api_client.get_analysis_tree(self.current_analysis_id)
            self.tree_data = tree_response.get("tree", {})
            
            # Load issues
            issues_response = await self.api_client.get_analysis_issues(self.current_analysis_id)
            self.all_issues = issues_response.get("issues", [])
            self.filtered_issues = self.all_issues.copy()
            
            # Load dead code analysis
            dead_code_response = await self.api_client.get_analysis_dead_code(self.current_analysis_id)
            self.dead_code_data = dead_code_response.get("dead_code", {
                "functions": [],
                "classes": [],
                "imports": []
            })
            
            # Load important functions
            important_functions_response = await self.api_client.get_analysis_important_functions(self.current_analysis_id)
            self.important_functions_data = important_functions_response.get("important_functions", {
                "entry_points": [],
                "important_functions": [],
                "most_called": [],
                "recursive": []
            })
            
            # Load statistics
            stats_response = await self.api_client.get_analysis_stats(self.current_analysis_id)
            self.stats_data = stats_response.get("stats", {})
            
            self.analysis_message = "Analysis completed successfully!"
            
        except Exception as e:
            self.error_message = f"Failed to load analysis results: {str(e)}"
            self.show_error_modal = True
    
    def toggle_node_expansion(self, node_path: str):
        """Toggle the expansion state of a tree node."""
        if node_path in self.expanded_nodes:
            self.expanded_nodes.remove(node_path)
        else:
            self.expanded_nodes.add(node_path)
    
    def select_node(self, node_path: str):
        """Select a tree node."""
        self.selected_node = node_path
    
    def set_active_tab(self, tab: str):
        """Set the active tab."""
        self.active_tab = tab
    
    def filter_issues(self, severity: str = "all", issue_type: str = "all"):
        """Filter issues by severity and type."""
        if severity is not None:
            self.issue_filter_severity = severity
        if issue_type is not None:
            self.issue_filter_type = issue_type
        
        # Apply filters
        filtered = self.all_issues.copy()
        
        if self.issue_filter_severity != "all":
            filtered = [issue for issue in filtered if issue.get("severity") == self.issue_filter_severity]
        
        if self.issue_filter_type != "all":
            filtered = [issue for issue in filtered if issue.get("type") == self.issue_filter_type]
        
        self.filtered_issues = filtered
    
    def close_error_modal(self):
        """Close the error modal."""
        self.show_error_modal = False
        self.error_message = ""
    
    def reset_analysis(self):
        """Reset the analysis state."""
        self.current_analysis_id = ""
        self.analysis_status = "idle"
        self.analysis_progress = 0.0
        self.analysis_message = ""
        self.analysis_start_time = None
        self.analysis_duration = 0.0
        self.repository_url = ""
        self.repository_name = ""
        self.repository_owner = ""
        self.tree_data = {}
        self.expanded_nodes = set()
        self.selected_node = ""
        self.all_issues = []
        self.filtered_issues = []
        self.dead_code_data = {"functions": [], "classes": [], "imports": []}
        self.important_functions_data = {"entry_points": [], "important_functions": [], "most_called": [], "recursive": []}
        self.stats_data = {}
        self.active_tab = "tree"
        self.loading = False
        self.error_message = ""
        self.show_error_modal = False


# Create global state instance
AppState = AnalysisState
