"""
Codebase Analysis Dashboard - Main Reflex Application

A comprehensive dashboard for analyzing codebases using graph-sitter,
providing interactive tree visualization, error detection, and dead code analysis.
"""

import reflex as rx
from typing import Dict, List, Any, Optional
import asyncio
import httpx
from datetime import datetime

from .state.app_state import AppState
from .pages.dashboard import dashboard_page
from .components.tree_view import TreeView
from .components.repo_input import RepoInput
from .components.issue_display import IssueDisplay
from .styles.app_styles import get_app_styles


class CodebaseDashboard(rx.App):
    """Main Reflex application for codebase analysis dashboard."""
    
    def __init__(self):
        super().__init__(
            state=AppState,
            stylesheets=[
                "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
                "https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css"
            ],
            theme=rx.theme(
                appearance="light",
                has_background=True,
                radius="medium",
                accent_color="blue",
            )
        )


def index() -> rx.Component:
    """Main dashboard page."""
    return rx.box(
        # Header
        rx.hstack(
            rx.heading(
                "🔍 Codebase Analysis Dashboard",
                size="8",
                color="var(--accent-9)",
                font_weight="700"
            ),
            rx.spacer(),
            rx.badge(
                "Powered by Graph-sitter",
                variant="soft",
                color_scheme="blue"
            ),
            width="100%",
            padding="1rem 2rem",
            border_bottom="1px solid var(--gray-6)",
            background="var(--gray-1)",
            align="center"
        ),
        
        # Main content
        rx.container(
            dashboard_page(),
            max_width="1400px",
            padding="2rem",
            width="100%"
        ),
        
        width="100%",
        min_height="100vh",
        background="var(--gray-2)",
        style=get_app_styles()
    )


# Create the app instance
app = CodebaseDashboard()

# Add the main page
app.add_page(index, route="/")

# Add additional routes if needed
app.add_page(
    lambda: rx.text("Analysis Results", size="6"),
    route="/analysis/[analysis_id]"
)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )
