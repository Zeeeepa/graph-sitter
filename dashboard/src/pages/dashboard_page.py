"""
Main Dashboard Page

The primary page that orchestrates all dashboard components based on analysis state.
"""

import reflex as rx
from ..state.app_state import AppState
from ..components.analysis.repository_input import repository_input
from ..components.analysis.analysis_progress import analysis_progress
from ..components.analysis.results_view import results_view
from ..components.common.error_modal import error_modal


def dashboard_page() -> rx.Component:
    """Main dashboard page component."""
    return rx.box(
        # Error modal (always present, shown conditionally)
        error_modal(),
        
        # Main content based on analysis state
        rx.cond(
            AppState.analysis_status == "idle",
            repository_input()
        ),
        
        rx.cond(
            AppState.analysis_status == "analyzing",
            analysis_progress()
        ),
        
        rx.cond(
            AppState.analysis_status == "completed",
            results_view()
        ),
        
        rx.cond(
            AppState.analysis_status == "error",
            repository_input()  # Show input form again on error
        ),
        
        width="100%",
        min_height="calc(100vh - 140px)",  # Account for header and footer
        flex="1"
    )
