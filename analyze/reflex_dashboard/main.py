#!/usr/bin/env python3
"""
Graph-Sitter Reflex Dashboard - Main Application

A comprehensive interactive dashboard for codebase analysis using Reflex.
Integrates with graph-sitter's analysis capabilities to provide:
- Interactive file tree navigation
- Real-time LSP diagnostics
- Symbol tree visualization  
- Dead code analysis
- Codebase health metrics
- Serena integration features
"""

import reflex as rx
from components.layout import create_main_layout
from state.dashboard_state import DashboardState


def index() -> rx.Component:
    """Main dashboard page."""
    return create_main_layout()


def about() -> rx.Component:
    """About page with dashboard information."""
    return rx.container(
        rx.vstack(
            rx.heading("Graph-Sitter Analysis Dashboard", size="2xl"),
            rx.text(
                "A comprehensive codebase analysis tool built with Reflex and graph-sitter.",
                size="lg",
                color="gray.600"
            ),
            rx.divider(),
            rx.vstack(
                rx.heading("Features", size="xl"),
                rx.unordered_list(
                    rx.list_item("🔍 Interactive codebase exploration"),
                    rx.list_item("📊 Real-time analysis metrics"),
                    rx.list_item("🌳 Symbol tree visualization"),
                    rx.list_item("❌ LSP error diagnostics"),
                    rx.list_item("💀 Dead code detection"),
                    rx.list_item("⚡ Serena integration"),
                ),
                align_items="start",
                spacing="4"
            ),
            rx.vstack(
                rx.heading("Technology Stack", size="xl"),
                rx.unordered_list(
                    rx.list_item("🐍 Python with Reflex framework"),
                    rx.list_item("🌳 Graph-sitter for code analysis"),
                    rx.list_item("🔧 LSP integration via Serena"),
                    rx.list_item("📡 Real-time WebSocket updates"),
                ),
                align_items="start",
                spacing="4"
            ),
            spacing="6",
            align_items="start"
        ),
        max_width="800px",
        padding="2rem"
    )


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ]
)

# Add pages
app.add_page(
    index,
    route="/",
    title="Graph-Sitter Dashboard",
    description="Interactive codebase analysis dashboard"
)

app.add_page(
    about,
    route="/about",
    title="About - Graph-Sitter Dashboard",
    description="About the Graph-Sitter analysis dashboard"
)


if __name__ == "__main__":
    # For development
    app._compile()
