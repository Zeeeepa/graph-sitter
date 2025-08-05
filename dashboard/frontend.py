"""
REAL PRODUCTION CODEBASE ANALYSIS FRONTEND
Interactive dashboard using Reflex with real graph-sitter integration
"""

import reflex as rx
import asyncio
import httpx
from typing import Dict, List, Any, Optional
import json

# State management
class DashboardState(rx.State):
    """Main dashboard state"""
    
    # Analysis state
    repo_url: str = ""
    language: str = "python"
    analysis_id: str = ""
    analysis_status: str = "idle"  # idle, analyzing, completed, error
    progress: int = 0
    error_message: str = ""
    
    # Results
    tree_structure: Dict[str, Any] = {}
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = {}
    codebase_summary: str = ""
    stats: Dict[str, int] = {}
    important_functions: List[Dict[str, Any]] = []
    dead_code: List[Dict[str, Any]] = []
    all_issues: List[Dict[str, Any]] = []
    
    # UI state
    selected_node: Dict[str, Any] = {}
    show_issues_panel: bool = False
    show_summary_panel: bool = True
    filter_severity: str = "all"
    expanded_nodes: List[str] = []
    
    def set_repo_url(self, value: str):
        """Set repository URL"""
        self.repo_url = value
    
    def set_language(self, value: str):
        """Set language"""
        self.language = value
    
    def set_filter_severity(self, value: str):
        """Set filter severity"""
        self.filter_severity = value
    
    async def start_analysis(self):
        """Start codebase analysis"""
        if not self.repo_url:
            self.error_message = "Please enter a repository URL"
            return
            
        self.analysis_status = "analyzing"
        self.progress = 0
        self.error_message = ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/analyze",
                    json={
                        "repo_url": self.repo_url,
                        "language": self.language if self.language != "auto" else None
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.analysis_id = result["analysis_id"]
                    # Start polling for status
                    await self.poll_analysis_status()
                else:
                    self.analysis_status = "error"
                    self.error_message = f"Failed to start analysis: {response.text}"
                    
        except Exception as e:
            self.analysis_status = "error"
            self.error_message = f"Error starting analysis: {str(e)}"
    
    async def poll_analysis_status(self):
        """Poll analysis status until completion"""
        max_attempts = 300  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts and self.analysis_status == "analyzing":
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:8000/analysis/{self.analysis_id}/status",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get("status", "unknown")
                        self.progress = result.get("progress", 0)
                        
                        if status == "completed":
                            self.analysis_status = "completed"
                            await self.load_analysis_results()
                            break
                        elif status == "error":
                            self.analysis_status = "error"
                            self.error_message = result.get("error", "Unknown error")
                            break
                            
                await asyncio.sleep(2)  # Poll every 2 seconds
                attempt += 1
                
            except Exception as e:
                self.error_message = f"Error polling status: {str(e)}"
                break
    
    async def load_analysis_results(self):
        """Load complete analysis results"""
        try:
            async with httpx.AsyncClient() as client:
                # Load tree structure
                tree_response = await client.get(
                    f"http://localhost:8000/analysis/{self.analysis_id}/tree",
                    timeout=30.0
                )
                
                if tree_response.status_code == 200:
                    tree_data = tree_response.json()
                    self.tree_structure = tree_data["tree"]
                    self.total_issues = tree_data["total_issues"]
                    self.issues_by_severity = tree_data["issues_by_severity"]
                
                # Load summary
                summary_response = await client.get(
                    f"http://localhost:8000/analysis/{self.analysis_id}/summary",
                    timeout=30.0
                )
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    self.codebase_summary = summary_data["summary"]
                    self.stats = summary_data["stats"]
                    self.important_functions = summary_data["important_functions"]
                    self.dead_code = summary_data["dead_code"]
                
                # Load issues
                issues_response = await client.get(
                    f"http://localhost:8000/analysis/{self.analysis_id}/issues",
                    timeout=30.0
                )
                
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                    self.all_issues = issues_data["issues"]
                    
        except Exception as e:
            self.error_message = f"Error loading results: {str(e)}"
    
    def select_node(self, node_data: Dict[str, Any]):
        """Select a tree node"""
        self.selected_node = node_data
        
    def toggle_issues_panel(self):
        """Toggle issues panel visibility"""
        self.show_issues_panel = not self.show_issues_panel
        
    def toggle_summary_panel(self):
        """Toggle summary panel visibility"""
        self.show_summary_panel = not self.show_summary_panel
        
    def set_filter_severity(self, severity: str):
        """Set issue severity filter"""
        self.filter_severity = severity
        
    def toggle_node_expansion(self, node_path: str):
        """Toggle node expansion in tree"""
        if node_path in self.expanded_nodes:
            self.expanded_nodes.remove(node_path)
        else:
            self.expanded_nodes.append(node_path)

def severity_badge(severity: str, count: int) -> rx.Component:
    """Create severity badge"""
    colors = {
        "critical": "red",
        "major": "orange", 
        "minor": "yellow"
    }
    
    return rx.badge(
        f"{severity.title()}: {count}",
        color_scheme=colors.get(severity, "gray"),
        size="sm"
    )

def issue_card(issue: Dict[str, Any]) -> rx.Component:
    """Create issue card"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    issue["type"].replace("_", " ").title(),
                    color_scheme="blue",
                    size="sm"
                ),
                severity_badge(issue["severity"], 1),
                spacing="2"
            ),
            rx.text(
                issue["description"],
                font_weight="bold",
                size="sm"
            ),
            rx.text(
                f"File: {issue['file_path']}:{issue['line_number']}",
                size="xs",
                color="gray"
            ),
            rx.text(
                f"Symbol: {issue['symbol_name']}",
                size="xs",
                color="gray"
            ),
            rx.text(
                issue["suggestion"],
                size="xs",
                color="green"
            ),
            spacing="1",
            align="start"
        ),
        size="sm",
        width="100%"
    )

def tree_node(node: Dict[str, Any], level: int = 0) -> rx.Component:
    """Render tree node recursively"""
    indent = level * 20
    
    # Node icon based on type
    if node["type"] == "folder":
        icon = "📁"
    elif node["type"] == "file":
        if node["name"].endswith(".py"):
            icon = "🐍"
        elif node["name"].endswith((".ts", ".tsx", ".js", ".jsx")):
            icon = "📜"
        else:
            icon = "📄"
    else:
        icon = "📄"
    
    # Issue count
    issue_count = len(node.get("issues", []))
    
    return rx.vstack(
        rx.hstack(
            rx.spacer(width=f"{indent}px"),
            rx.text(icon, size="sm"),
            rx.text(
                node["name"],
                size="sm",
                font_weight="medium" if node["type"] == "folder" else "normal"
            ),
            rx.cond(
                issue_count > 0,
                rx.badge(
                    str(issue_count),
                    color_scheme="red",
                    size="xs"
                )
            ),
            spacing="2",
            align="center",
            cursor="pointer",
            on_click=DashboardState.select_node(node),
            _hover={"bg": "gray.100"}
        ),
        # Children (if expanded)
        rx.cond(
            node["path"] in DashboardState.expanded_nodes,
            rx.vstack(
                *[tree_node(child, level + 1) for child in node.get("children", [])],
                spacing="1"
            )
        ),
        spacing="1",
        align="start",
        width="100%"
    )

def analysis_form() -> rx.Component:
    """Analysis input form"""
    return rx.card(
        rx.vstack(
            rx.heading("Codebase Analysis Dashboard", size="lg"),
            rx.text("Enter a repository URL to analyze with real graph-sitter integration"),
            
            rx.hstack(
                rx.input(
                    placeholder="https://github.com/user/repo",
                    value=DashboardState.repo_url,
                    on_change=DashboardState.set_repo_url,
                    width="400px"
                ),
                rx.select(
                    ["auto", "python", "typescript"],
                    value=DashboardState.language,
                    on_change=DashboardState.set_language,
                    width="120px"
                ),
                rx.button(
                    "Analyze",
                    on_click=DashboardState.start_analysis,
                    loading=DashboardState.analysis_status == "analyzing",
                    color_scheme="blue"
                ),
                spacing="3"
            ),
            
            # Progress bar
            rx.cond(
                DashboardState.analysis_status == "analyzing",
                rx.vstack(
                    rx.progress(
                        value=DashboardState.progress,
                        width="100%"
                    ),
                    rx.text(f"Progress: {DashboardState.progress}%", size="sm"),
                    spacing="2"
                )
            ),
            
            # Error message
            rx.cond(
                DashboardState.error_message != "",
                rx.alert(
                    rx.alert_icon(),
                    rx.alert_title("Error"),
                    rx.alert_description(DashboardState.error_message),
                    status="error"
                )
            ),
            
            spacing="4",
            align="center"
        ),
        width="100%",
        max_width="800px"
    )

def stats_panel() -> rx.Component:
    """Statistics panel"""
    return rx.card(
        rx.vstack(
            rx.heading("Statistics", size="md"),
            rx.grid(
                rx.stat(
                    rx.stat_label("Total Files"),
                    rx.stat_number(DashboardState.stats.get("total_files", 0))
                ),
                rx.stat(
                    rx.stat_label("Total Functions"),
                    rx.stat_number(DashboardState.stats.get("total_functions", 0))
                ),
                rx.stat(
                    rx.stat_label("Total Classes"),
                    rx.stat_number(DashboardState.stats.get("total_classes", 0))
                ),
                rx.stat(
                    rx.stat_label("Total Issues"),
                    rx.stat_number(DashboardState.total_issues)
                ),
                columns="4",
                spacing="4"
            ),
            
            rx.heading("Issues by Severity", size="sm"),
            rx.hstack(
                severity_badge("critical", DashboardState.issues_by_severity.get("critical", 0)),
                severity_badge("major", DashboardState.issues_by_severity.get("major", 0)),
                severity_badge("minor", DashboardState.issues_by_severity.get("minor", 0)),
                spacing="3"
            ),
            
            spacing="4",
            align="start"
        ),
        width="100%"
    )

def tree_panel() -> rx.Component:
    """Interactive tree structure panel"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Codebase Structure", size="md"),
                rx.button(
                    "Toggle Issues",
                    on_click=DashboardState.toggle_issues_panel,
                    size="sm",
                    variant="outline"
                ),
                justify="between",
                width="100%"
            ),
            
            rx.divider(),
            
            # Tree structure
            rx.scroll_area(
                rx.cond(
                    DashboardState.tree_structure != {},
                    tree_node(DashboardState.tree_structure),
                    rx.text("No tree structure available", color="gray")
                ),
                height="600px",
                width="100%"
            ),
            
            spacing="3",
            align="start"
        ),
        width="100%",
        height="700px"
    )

def issues_panel() -> rx.Component:
    """Issues panel"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Issues", size="md"),
                rx.select(
                    ["all", "critical", "major", "minor"],
                    value=DashboardState.filter_severity,
                    on_change=DashboardState.set_filter_severity,
                    size="sm"
                ),
                justify="between",
                width="100%"
            ),
            
            rx.divider(),
            
            # Issues list
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        DashboardState.all_issues,
                        lambda issue: rx.cond(
                            (DashboardState.filter_severity == "all") | 
                            (issue["severity"] == DashboardState.filter_severity),
                            issue_card(issue)
                        )
                    ),
                    spacing="2",
                    width="100%"
                ),
                height="600px",
                width="100%"
            ),
            
            spacing="3",
            align="start"
        ),
        width="100%",
        height="700px"
    )

def summary_panel() -> rx.Component:
    """Summary panel"""
    return rx.card(
        rx.vstack(
            rx.heading("Codebase Summary", size="md"),
            rx.divider(),
            
            rx.scroll_area(
                rx.vstack(
                    # Codebase summary
                    rx.text_area(
                        value=DashboardState.codebase_summary,
                        read_only=True,
                        height="200px",
                        width="100%"
                    ),
                    
                    # Important functions
                    rx.cond(
                        len(DashboardState.important_functions) > 0,
                        rx.vstack(
                            rx.heading("Important Functions", size="sm"),
                            rx.vstack(
                                rx.foreach(
                                    DashboardState.important_functions,
                                    lambda func: rx.card(
                                        rx.vstack(
                                            rx.text(func["name"], font_weight="bold"),
                                            rx.text(f"File: {func['filepath']}", size="sm", color="gray"),
                                            rx.text(f"Type: {func['type']}", size="sm", color="blue"),
                                            spacing="1"
                                        ),
                                        size="sm"
                                    )
                                ),
                                spacing="2"
                            ),
                            spacing="3",
                            align="start"
                        )
                    ),
                    
                    # Dead code
                    rx.cond(
                        len(DashboardState.dead_code) > 0,
                        rx.vstack(
                            rx.heading("Dead Code", size="sm"),
                            rx.vstack(
                                rx.foreach(
                                    DashboardState.dead_code,
                                    lambda dead: rx.card(
                                        rx.vstack(
                                            rx.text(f"{dead['type']}: {dead['name']}", font_weight="bold"),
                                            rx.text(f"File: {dead['filepath']}", size="sm", color="gray"),
                                            rx.text(f"Reason: {dead['reason']}", size="sm", color="red"),
                                            spacing="1"
                                        ),
                                        size="sm"
                                    )
                                ),
                                spacing="2"
                            ),
                            spacing="3",
                            align="start"
                        )
                    ),
                    
                    spacing="4",
                    align="start"
                ),
                height="600px",
                width="100%"
            ),
            
            spacing="3",
            align="start"
        ),
        width="100%",
        height="700px"
    )

def main_dashboard() -> rx.Component:
    """Main dashboard layout"""
    return rx.vstack(
        # Analysis form
        analysis_form(),
        
        # Results (only show when analysis is completed)
        rx.cond(
            DashboardState.analysis_status == "completed",
            rx.vstack(
                # Stats panel
                stats_panel(),
                
                # Main content area
                rx.hstack(
                    # Tree structure (left)
                    tree_panel(),
                    
                    # Issues panel (center) - conditional
                    rx.cond(
                        DashboardState.show_issues_panel,
                        issues_panel()
                    ),
                    
                    # Summary panel (right) - conditional
                    rx.cond(
                        DashboardState.show_summary_panel,
                        summary_panel()
                    ),
                    
                    spacing="4",
                    align="start",
                    width="100%"
                ),
                
                spacing="4",
                width="100%"
            )
        ),
        
        spacing="6",
        padding="4",
        width="100%",
        max_width="1400px",
        margin="0 auto"
    )

def index() -> rx.Component:
    """Main page"""
    return rx.container(
        main_dashboard(),
        size="full"
    )

# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

app.add_page(index, route="/")
