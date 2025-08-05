"""
Simple Codebase Analysis Dashboard Demo

A minimal working version to demonstrate the dashboard functionality.
"""

import reflex as rx
from typing import Dict, List, Any

# Simple state for demo
class DashboardState(rx.State):
    """Simple state for the dashboard demo."""
    
    # Repository input
    repository_url: str = ""
    
    # Analysis status
    is_analyzing: bool = False
    analysis_progress: float = 0.0
    analysis_message: str = ""
    
    # Mock results
    show_results: bool = False
    
    def start_analysis(self):
        """Start mock analysis."""
        if not self.repository_url:
            return
        
        self.is_analyzing = True
        self.analysis_progress = 0.0
        self.analysis_message = "Starting analysis..."
        
        # Simulate analysis completion
        import asyncio
        asyncio.create_task(self._simulate_analysis())
    
    async def _simulate_analysis(self):
        """Simulate analysis progress."""
        import asyncio
        
        steps = [
            "Cloning repository...",
            "Parsing source files...",
            "Analyzing code structure...",
            "Detecting issues...",
            "Generating report...",
            "Analysis complete!"
        ]
        
        for i, step in enumerate(steps):
            await asyncio.sleep(1)
            self.analysis_message = step
            self.analysis_progress = (i + 1) / len(steps) * 100
            
        self.is_analyzing = False
        self.show_results = True

def header() -> rx.Component:
    """Dashboard header."""
    return rx.hstack(
        rx.heading("🔍 Codebase Analysis Dashboard", size="lg"),
        rx.spacer(),
        rx.text("Powered by Reflex + graph-sitter", color="gray.600"),
        width="100%",
        padding="1rem",
        border_bottom="1px solid #e2e8f0",
        background="white"
    )

def repository_input() -> rx.Component:
    """Repository input form."""
    return rx.vstack(
        rx.heading("Repository Analysis", size="md"),
        rx.text("Enter a GitHub repository URL or local path to analyze:", color="gray.600"),
        rx.hstack(
            rx.input(
                placeholder="https://github.com/owner/repository",
                value=DashboardState.repository_url,
                on_change=DashboardState.set_repository_url,
                width="400px"
            ),
            rx.button(
                "Analyze",
                on_click=DashboardState.start_analysis,
                disabled=DashboardState.is_analyzing,
                background="blue.500",
                color="white",
                _hover={"background": "blue.600"}
            ),
            spacing="1rem"
        ),
        spacing="1rem",
        align="start"
    )

def analysis_progress() -> rx.Component:
    """Analysis progress display."""
    return rx.cond(
        DashboardState.is_analyzing,
        rx.vstack(
            rx.heading("Analysis in Progress", size="md"),
            rx.text(DashboardState.analysis_message),
            rx.progress(
                value=DashboardState.analysis_progress,
                width="400px",
                color_scheme="blue"
            ),
            rx.text(f"{DashboardState.analysis_progress:.0f}% complete"),
            spacing="1rem",
            align="start"
        )
    )

def mock_results() -> rx.Component:
    """Mock analysis results."""
    return rx.cond(
        DashboardState.show_results,
        rx.vstack(
            rx.heading("Analysis Results", size="md"),
            rx.hstack(
                rx.stat(
                    rx.stat_label("Total Files"),
                    rx.stat_number("127"),
                    rx.stat_help_text("Python, JS, TS files")
                ),
                rx.stat(
                    rx.stat_label("Issues Found"),
                    rx.stat_number("23"),
                    rx.stat_help_text("5 critical, 12 major, 6 minor")
                ),
                rx.stat(
                    rx.stat_label("Dead Code"),
                    rx.stat_number("8"),
                    rx.stat_help_text("Unused functions/classes")
                ),
                spacing="2rem"
            ),
            rx.divider(),
            rx.heading("Sample Issues", size="sm"),
            rx.vstack(
                rx.alert(
                    rx.alert_icon(),
                    rx.alert_title("Missing Type Annotation"),
                    rx.alert_description("Function 'process_data' in /src/utils.py missing type hints"),
                    status="warning"
                ),
                rx.alert(
                    rx.alert_icon(),
                    rx.alert_title("Unused Function"),
                    rx.alert_description("Function 'old_helper' in /src/legacy.py is never called"),
                    status="error"
                ),
                rx.alert(
                    rx.alert_icon(),
                    rx.alert_title("Empty Function"),
                    rx.alert_description("Function 'todo_implement' in /src/features.py has no implementation"),
                    status="info"
                ),
                spacing="1rem",
                width="100%"
            ),
            spacing="2rem",
            align="start",
            width="100%"
        )
    )

def index() -> rx.Component:
    """Main dashboard page."""
    return rx.vstack(
        header(),
        rx.container(
            rx.vstack(
                repository_input(),
                analysis_progress(),
                mock_results(),
                spacing="3rem",
                align="start",
                width="100%"
            ),
            max_width="800px",
            padding="2rem"
        ),
        min_height="100vh",
        width="100%",
        background="gray.50"
    )

# Create app
app = rx.App()
app.add_page(
    index,
    route="/",
    title="Codebase Analysis Dashboard",
    description="Analyze your codebase for issues, dead code, and important functions"
)
