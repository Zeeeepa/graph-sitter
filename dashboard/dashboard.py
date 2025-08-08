"""
Comprehensive Codebase Analysis Dashboard

A professional Reflex application for analyzing codebases with:
- Interactive tree visualization
- Real-time issue detection
- Dead code analysis
- Important function identification
- Comprehensive statistics
"""

import reflex as rx
from .src.state.app_state import AppState
from .src.pages.dashboard_page import dashboard_page
from .src.components.layout.header import header
from .src.components.layout.footer import footer
from .src.styles.theme import theme_styles

# Create the main app
app = rx.App(
    style=theme_styles,
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        "/styles/custom.css"
    ]
)

def index() -> rx.Component:
    """Main dashboard page."""
    return rx.vstack(
        header(),
        dashboard_page(),
        footer(),
        min_height="100vh",
        width="100%",
        spacing="0",
        align="stretch"
    )

# Add pages
app.add_page(
    index,
    route="/",
    title="Codebase Analysis Dashboard",
    description="Comprehensive codebase analysis with tree visualization, issue detection, and dead code analysis"
)

# Add custom CSS
app.add_custom_head_tag(
    rx.script("""
        // Custom JavaScript for enhanced interactions
        window.addEventListener('DOMContentLoaded', function() {
            console.log('Codebase Analysis Dashboard loaded');
        });
    """)
)

