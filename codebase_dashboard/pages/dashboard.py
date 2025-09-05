"""
Main Dashboard Page Component

The primary interface for repository analysis with input controls,
tree visualization, and analysis results panels.
"""

import reflex as rx
from typing import Dict, List, Any
from ..state.app_state import AppState, AnalysisStatus
from ..components.repo_input import repo_input_section
from ..components.tree_view import tree_view_section
from ..components.issue_display import issues_panel
from ..components.stats_display import stats_display
from ..components.dead_code_display import dead_code_panel
from ..components.important_functions_display import important_functions_panel


def dashboard_page() -> rx.Component:
    """Main dashboard page layout."""
    return rx.vstack(
        # Repository input section
        repo_input_section(),
        
        # Analysis progress indicator
        rx.cond(
            AppState.analysis_status == AnalysisStatus.ANALYZING.value,
            rx.box(
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.vstack(
                        rx.text(
                            AppState.analysis_message,
                            size="3",
                            weight="medium"
                        ),
                        rx.progress(
                            value=AppState.analysis_progress,
                            max=100,
                            width="300px"
                        ),
                        spacing="2",
                        align="start"
                    ),
                    spacing="4",
                    align="center"
                ),
                padding="1rem",
                border="1px solid var(--blue-6)",
                border_radius="8px",
                background="var(--blue-2)",
                width="100%"
            )
        ),
        
        # Error display
        rx.cond(
            AppState.analysis_status == AnalysisStatus.ERROR.value,
            rx.callout(
                AppState.analysis_message,
                icon="triangle_alert",
                color_scheme="red",
                width="100%"
            )
        ),
        
        # Main content area (only show when analysis is completed)
        rx.cond(
            AppState.analysis_status == AnalysisStatus.COMPLETED.value,
            rx.vstack(
                # Statistics overview
                stats_display(),
                
                # Main content grid
                rx.grid(
                    # Left column - Tree view
                    rx.box(
                        rx.heading("📁 Codebase Structure", size="5", margin_bottom="1rem"),
                        tree_view_section(),
                        padding="1rem",
                        border="1px solid var(--gray-6)",
                        border_radius="8px",
                        background="white",
                        height="600px",
                        overflow="auto"
                    ),
                    
                    # Right column - Analysis panels
                    rx.vstack(
                        # Issues panel
                        rx.cond(
                            AppState.show_issues_panel,
                            issues_panel()
                        ),
                        
                        # Dead code panel
                        rx.cond(
                            AppState.show_dead_code_panel,
                            dead_code_panel()
                        ),
                        
                        # Important functions panel
                        rx.cond(
                            AppState.show_important_functions_panel,
                            important_functions_panel()
                        ),
                        
                        spacing="4",
                        width="100%"
                    ),
                    
                    columns="2",
                    spacing="6",
                    width="100%"
                ),
                
                # Control buttons
                control_buttons(),
                
                spacing="6",
                width="100%"
            )
        ),
        
        spacing="6",
        width="100%",
        align="stretch"
    )


def control_buttons() -> rx.Component:
    """Control buttons for toggling different panels."""
    return rx.hstack(
        rx.button(
            rx.icon("bug", size=16),
            f"Issues ({AppState.total_issues})",
            variant="soft",
            color_scheme="red" if AppState.get_issue_count_by_severity("critical") > 0 else "gray",
            on_click=AppState.toggle_issues_panel
        ),
        
        rx.button(
            rx.icon("trash", size=16),
            f"Dead Code ({len(AppState.dead_code_functions) + len(AppState.dead_code_classes)})",
            variant="soft",
            color_scheme="orange",
            on_click=AppState.toggle_dead_code_panel
        ),
        
        rx.button(
            rx.icon("star", size=16),
            f"Important Functions ({len(AppState.important_functions)})",
            variant="soft",
            color_scheme="blue",
            on_click=AppState.toggle_important_functions_panel
        ),
        
        rx.spacer(),
        
        rx.button(
            rx.icon("refresh_cw", size=16),
            "New Analysis",
            variant="outline",
            on_click=AppState.reset_analysis
        ),
        
        spacing="3",
        width="100%",
        align="center"
    )
