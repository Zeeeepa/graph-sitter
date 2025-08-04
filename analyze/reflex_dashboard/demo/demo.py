"""
Simple demo version of the Graph-Sitter Reflex Dashboard.
This version demonstrates the core functionality without complex imports.
"""

import reflex as rx
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import os


class DashboardState(rx.State):
    """Main dashboard state."""
    
    # Codebase selection
    available_codebases: List[str] = []
    selected_codebase: str = ""
    selected_codebase_path: str = ""
    codebase_loaded: bool = False
    
    # Analysis state
    analysis_running: bool = False
    analysis_progress: float = 0.0
    analysis_status: str = "Ready"
    
    # Quick stats
    total_files: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_symbols: int = 0
    
    # Messages
    success_message: str = ""
    error_message: str = ""
    
    # Current tab
    current_tab: str = "overview"
    
    def __init__(self, *args, **kwargs):
        """Initialize the dashboard state."""
        super().__init__(*args, **kwargs)
        self.detect_available_codebases()
    
    def detect_available_codebases(self):
        """Detect available codebases."""
        codebases = []
        
        # Current directory
        current_dir = Path.cwd()
        codebases.append(f"Current Directory ({current_dir.name})")
        
        # Parent directories
        if current_dir.parent.name == "reflex_dashboard":
            # We're in the dashboard, look for graph-sitter
            graph_sitter_root = current_dir.parent.parent
            if (graph_sitter_root / "src" / "graph_sitter").exists():
                codebases.append(f"Graph-Sitter Core ({graph_sitter_root.name})")
        
        # Look for common source directories
        for src_dir in ["src", "lib", "app"]:
            if (current_dir / src_dir).exists():
                codebases.append(f"{src_dir.title()} Directory")
        
        self.available_codebases = codebases
        if codebases:
            self.selected_codebase = codebases[0]
    
    def select_codebase(self, codebase: str):
        """Select a codebase."""
        self.selected_codebase = codebase
        self.codebase_loaded = False
        self.clear_messages()
    
    def load_codebase(self):
        """Load the selected codebase."""
        if not self.selected_codebase:
            self.set_error("No codebase selected")
            return
        
        try:
            # Determine the path based on selection
            current_dir = Path.cwd()
            
            if "Current Directory" in self.selected_codebase:
                self.selected_codebase_path = str(current_dir)
            elif "Graph-Sitter Core" in self.selected_codebase:
                self.selected_codebase_path = str(current_dir.parent.parent)
            elif "Src Directory" in self.selected_codebase:
                self.selected_codebase_path = str(current_dir / "src")
            else:
                self.selected_codebase_path = str(current_dir)
            
            # Count files for demo
            path = Path(self.selected_codebase_path)
            python_files = list(path.rglob("*.py"))
            self.total_files = len(python_files)
            
            self.codebase_loaded = True
            self.set_success(f"Loaded codebase: {self.selected_codebase}")
            
        except Exception as e:
            self.set_error(f"Failed to load codebase: {str(e)}")
    
    async def run_analysis(self):
        """Run analysis on the loaded codebase."""
        if not self.codebase_loaded:
            self.set_error("No codebase loaded")
            return
        
        self.analysis_running = True
        self.analysis_progress = 0.0
        self.analysis_status = "Starting analysis..."
        self.clear_messages()
        
        try:
            # Simulate analysis steps
            steps = [
                ("Scanning files...", 20),
                ("Analyzing Python files...", 40),
                ("Collecting metrics...", 60),
                ("Calculating health scores...", 80),
                ("Generating report...", 100)
            ]
            
            for status, progress in steps:
                self.analysis_status = status
                self.analysis_progress = progress
                await asyncio.sleep(1)  # Simulate work
            
            # Mock results
            path = Path(self.selected_codebase_path)
            python_files = list(path.rglob("*.py"))
            
            self.total_files = len(python_files)
            self.total_errors = max(0, len(python_files) // 10)  # Mock errors
            self.total_warnings = max(0, len(python_files) // 5)  # Mock warnings
            self.total_symbols = len(python_files) * 15  # Mock symbols
            
            self.set_success("Analysis completed successfully!")
            
        except Exception as e:
            self.set_error(f"Analysis failed: {str(e)}")
        finally:
            self.analysis_running = False
            self.analysis_status = "Ready"
    
    def set_tab(self, tab: str):
        """Set the current tab."""
        self.current_tab = tab
    
    def set_success(self, message: str):
        """Set success message."""
        self.success_message = message
        self.error_message = ""
    
    def set_error(self, message: str):
        """Set error message."""
        self.error_message = message
        self.success_message = ""
    
    def clear_messages(self):
        """Clear all messages."""
        self.success_message = ""
        self.error_message = ""


def create_header() -> rx.Component:
    """Create the dashboard header."""
    return rx.hstack(
        # Logo and title
        rx.hstack(
            rx.icon("activity", size=32, color="blue"),
            rx.vstack(
                rx.heading("Graph-Sitter Dashboard", size="lg"),
                rx.text("Interactive Codebase Analysis", size="sm", color="gray"),
                spacing="0",
                align="start"
            ),
            spacing="3",
            align="center"
        ),
        
        # Stats badges
        rx.hstack(
            rx.badge(
                rx.hstack(
                    rx.icon("file", size=16),
                    rx.text(DashboardState.total_files),
                    spacing="1"
                ),
                color="blue",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("alert-circle", size=16),
                    rx.text(DashboardState.total_errors),
                    spacing="1"
                ),
                color="red",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("alert-triangle", size=16),
                    rx.text(DashboardState.total_warnings),
                    spacing="1"
                ),
                color="yellow",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("code", size=16),
                    rx.text(DashboardState.total_symbols),
                    spacing="1"
                ),
                color="green",
                variant="soft"
            ),
            spacing="2"
        ),
        
        # Analysis button
        rx.button(
            rx.cond(
                DashboardState.analysis_running,
                rx.hstack(
                    rx.spinner(size="4"),
                    rx.text("Analyzing..."),
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("play", size=16),
                    rx.text("Analyze"),
                    spacing="2"
                )
            ),
            on_click=DashboardState.run_analysis,
            disabled=~DashboardState.codebase_loaded | DashboardState.analysis_running,
            color_scheme="blue"
        ),
        
        justify="between",
        align="center",
        width="100%",
        padding="4",
        border_bottom="1px solid var(--gray-6)"
    )


def create_sidebar() -> rx.Component:
    """Create the dashboard sidebar."""
    return rx.vstack(
        # Codebase selection
        rx.vstack(
            rx.heading("Codebase", size="md"),
            rx.select(
                DashboardState.available_codebases,
                value=DashboardState.selected_codebase,
                on_change=DashboardState.select_codebase,
                width="100%"
            ),
            rx.button(
                rx.cond(
                    DashboardState.codebase_loaded,
                    rx.hstack(
                        rx.icon("check", size=16),
                        rx.text("Loaded"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("folder-open", size=16),
                        rx.text("Load Codebase"),
                        spacing="2"
                    )
                ),
                on_click=DashboardState.load_codebase,
                disabled=DashboardState.codebase_loaded,
                width="100%",
                color_scheme=rx.cond(DashboardState.codebase_loaded, "green", "blue")
            ),
            spacing="3",
            align="start",
            width="100%"
        ),
        
        # Navigation tabs
        rx.vstack(
            rx.heading("Navigation", size="md"),
            rx.vstack(
                rx.button(
                    rx.hstack(
                        rx.icon("home", size=16),
                        rx.text("Overview"),
                        spacing="2"
                    ),
                    on_click=lambda: DashboardState.set_tab("overview"),
                    variant=rx.cond(DashboardState.current_tab == "overview", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("folder", size=16),
                        rx.text("Files"),
                        spacing="2"
                    ),
                    on_click=lambda: DashboardState.set_tab("files"),
                    variant=rx.cond(DashboardState.current_tab == "files", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("code", size=16),
                        rx.text("Symbols"),
                        spacing="2"
                    ),
                    on_click=lambda: DashboardState.set_tab("symbols"),
                    variant=rx.cond(DashboardState.current_tab == "symbols", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("alert-triangle", size=16),
                        rx.text("Diagnostics"),
                        spacing="2"
                    ),
                    on_click=lambda: DashboardState.set_tab("diagnostics"),
                    variant=rx.cond(DashboardState.current_tab == "diagnostics", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                spacing="2",
                width="100%"
            ),
            spacing="3",
            align="start",
            width="100%"
        ),
        
        # Analysis progress
        rx.cond(
            DashboardState.analysis_running,
            rx.vstack(
                rx.heading("Analysis Progress", size="md"),
                rx.vstack(
                    rx.text(DashboardState.analysis_status, size="sm"),
                    rx.progress(value=DashboardState.analysis_progress, width="100%"),
                    rx.text(f"{DashboardState.analysis_progress}%", size="sm", color="gray"),
                    spacing="2",
                    width="100%"
                ),
                spacing="3",
                align="start",
                width="100%"
            )
        ),
        
        spacing="6",
        align="start",
        width="100%",
        padding="4"
    )


def create_main_content() -> rx.Component:
    """Create the main content area."""
    return rx.vstack(
        # Messages
        rx.cond(
            DashboardState.success_message != "",
            rx.callout(
                DashboardState.success_message,
                icon="check",
                color_scheme="green",
                width="100%"
            )
        ),
        rx.cond(
            DashboardState.error_message != "",
            rx.callout(
                DashboardState.error_message,
                icon="alert-triangle",
                color_scheme="red",
                width="100%"
            )
        ),
        
        # Tab content
        rx.cond(
            DashboardState.current_tab == "overview",
            create_overview_tab(),
            rx.cond(
                DashboardState.current_tab == "files",
                create_files_tab(),
                rx.cond(
                    DashboardState.current_tab == "symbols",
                    create_symbols_tab(),
                    create_diagnostics_tab()
                )
            )
        ),
        
        spacing="4",
        width="100%",
        padding="4"
    )


def create_overview_tab() -> rx.Component:
    """Create the overview tab."""
    return rx.vstack(
        rx.heading("Codebase Overview", size="xl"),
        
        rx.cond(
            DashboardState.codebase_loaded,
            rx.vstack(
                # Stats grid
                rx.grid(
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("file", size=24, color="blue"),
                                rx.text("Files", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(DashboardState.total_files, size="3xl", weight="bold", color="blue"),
                            rx.text("Python files detected", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("alert-circle", size=24, color="red"),
                                rx.text("Errors", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(DashboardState.total_errors, size="3xl", weight="bold", color="red"),
                            rx.text("Critical issues found", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("alert-triangle", size=24, color="yellow"),
                                rx.text("Warnings", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(DashboardState.total_warnings, size="3xl", weight="bold", color="yellow"),
                            rx.text("Potential improvements", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("code", size=24, color="green"),
                                rx.text("Symbols", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(DashboardState.total_symbols, size="3xl", weight="bold", color="green"),
                            rx.text("Functions and classes", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    columns="2",
                    spacing="4",
                    width="100%"
                ),
                
                # Codebase info
                rx.card(
                    rx.vstack(
                        rx.heading("Codebase Information", size="lg"),
                        rx.vstack(
                            rx.hstack(
                                rx.text("Path:", weight="bold"),
                                rx.text(DashboardState.selected_codebase_path, font_family="mono", size="sm"),
                                spacing="2"
                            ),
                            rx.hstack(
                                rx.text("Selected:", weight="bold"),
                                rx.text(DashboardState.selected_codebase),
                                spacing="2"
                            ),
                            spacing="2",
                            align="start"
                        ),
                        spacing="3",
                        align="start"
                    ),
                    width="100%"
                ),
                
                spacing="6",
                width="100%"
            ),
            rx.vstack(
                rx.icon("folder-open", size=48, color="gray"),
                rx.text("No codebase loaded", size="lg", color="gray"),
                rx.text("Select and load a codebase to view analysis results", size="sm", color="gray"),
                spacing="3",
                align="center",
                padding="8"
            )
        ),
        
        spacing="6",
        align="start",
        width="100%"
    )


def create_files_tab() -> rx.Component:
    """Create the files tab."""
    return rx.vstack(
        rx.heading("File Explorer", size="xl"),
        rx.text("Interactive file tree and content viewer (coming soon)", color="gray"),
        spacing="4",
        align="start",
        width="100%"
    )


def create_symbols_tab() -> rx.Component:
    """Create the symbols tab."""
    return rx.vstack(
        rx.heading("Symbol Analysis", size="xl"),
        rx.text("Function and class analysis with complexity metrics (coming soon)", color="gray"),
        spacing="4",
        align="start",
        width="100%"
    )


def create_diagnostics_tab() -> rx.Component:
    """Create the diagnostics tab."""
    return rx.vstack(
        rx.heading("LSP Diagnostics", size="xl"),
        rx.text("Error and warning analysis with navigation (coming soon)", color="gray"),
        spacing="4",
        align="start",
        width="100%"
    )


def index() -> rx.Component:
    """Main dashboard page."""
    return rx.vstack(
        create_header(),
        rx.hstack(
            create_sidebar(),
            create_main_content(),
            spacing="0",
            width="100%",
            height="calc(100vh - 120px)",
            align="start"
        ),
        spacing="0",
        width="100%",
        height="100vh"
    )


# Create the app
app = rx.App(
    style={
        "font_family": "Inter, sans-serif",
        "background_color": "var(--gray-1)",
    }
)

app.add_page(index, route="/")
