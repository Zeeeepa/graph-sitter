"""
Main layout components for the dashboard.

This module contains the primary layout structure including header, sidebar, and main content area.
"""

import reflex as rx
from ..state.dashboard_state import DashboardState


def create_header() -> rx.Component:
    """Create the main header with navigation and stats."""
    return rx.hstack(
        # Logo and title
        rx.hstack(
            rx.icon("activity", size=24, color="blue.500"),
            rx.heading("Graph-Sitter Dashboard", size="lg", color="gray.800"),
            spacing="3",
            align_items="center"
        ),
        
        # Quick stats
        rx.hstack(
            rx.badge(
                rx.hstack(
                    rx.icon("file-text", size=16),
                    rx.text(DashboardState.total_files),
                    spacing="1",
                    align_items="center"
                ),
                variant="soft",
                color_scheme="blue"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("alert-circle", size=16),
                    rx.text(DashboardState.total_errors),
                    spacing="1",
                    align_items="center"
                ),
                variant="soft",
                color_scheme="red"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("alert-triangle", size=16),
                    rx.text(DashboardState.total_warnings),
                    spacing="1",
                    align_items="center"
                ),
                variant="soft",
                color_scheme="yellow"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("code", size=16),
                    rx.text(DashboardState.total_symbols),
                    spacing="1",
                    align_items="center"
                ),
                variant="soft",
                color_scheme="green"
            ),
            spacing="3"
        ),
        
        # Actions
        rx.hstack(
            rx.button(
                rx.icon("refresh-cw", size=16),
                "Analyze",
                on_click=DashboardState.run_analysis,
                loading=DashboardState.analysis_running,
                disabled=~DashboardState.codebase_loaded,
                variant="solid",
                color_scheme="blue"
            ),
            rx.button(
                rx.icon("settings", size=16),
                variant="ghost"
            ),
            rx.button(
                rx.icon("sun" if DashboardState.theme_mode == "light" else "moon", size=16),
                on_click=DashboardState.toggle_theme,
                variant="ghost"
            ),
            spacing="2"
        ),
        
        justify="between",
        align_items="center",
        width="100%",
        padding="1rem",
        border_bottom="1px solid",
        border_color="gray.200",
        bg="white"
    )


def create_sidebar() -> rx.Component:
    """Create the sidebar with navigation and codebase selection."""
    return rx.vstack(
        # Codebase selection
        rx.vstack(
            rx.heading("Codebase", size="sm", color="gray.600"),
            rx.select(
                [cb["name"] for cb in DashboardState.available_codebases],
                placeholder="Select codebase...",
                on_change=lambda value: DashboardState.select_codebase(
                    next((cb["path"] for cb in DashboardState.available_codebases if cb["name"] == value), "")
                ),
                width="100%"
            ),
            rx.cond(
                DashboardState.selected_codebase_path != "",
                rx.vstack(
                    rx.text(f"Path: {DashboardState.codebase_name}", size="sm", color="gray.500"),
                    rx.button(
                        "Load Codebase",
                        on_click=DashboardState.load_codebase,
                        loading=DashboardState.is_loading,
                        disabled=DashboardState.codebase_loaded,
                        width="100%",
                        variant="outline"
                    ),
                    spacing="2",
                    width="100%"
                )
            ),
            spacing="3",
            width="100%",
            align_items="start"
        ),
        
        rx.divider(),
        
        # Navigation tabs
        rx.vstack(
            rx.heading("Analysis", size="sm", color="gray.600"),
            rx.vstack(
                create_nav_item("overview", "Overview", "home"),
                create_nav_item("files", "File Tree", "folder"),
                create_nav_item("symbols", "Symbols", "code"),
                create_nav_item("errors", "Diagnostics", "alert-circle"),
                create_nav_item("deadcode", "Dead Code", "trash-2"),
                create_nav_item("metrics", "Metrics", "bar-chart"),
                spacing="1",
                width="100%"
            ),
            spacing="3",
            width="100%",
            align_items="start"
        ),
        
        rx.spacer(),
        
        # Analysis progress
        rx.cond(
            DashboardState.analysis_running,
            rx.vstack(
                rx.text("Analysis Progress", size="sm", weight="medium"),
                rx.progress(
                    value=DashboardState.analysis_progress,
                    width="100%"
                ),
                rx.text(
                    DashboardState.analysis_status,
                    size="sm",
                    color="gray.500"
                ),
                spacing="2",
                width="100%"
            )
        ),
        
        spacing="4",
        width="250px",
        height="100vh",
        padding="1rem",
        border_right="1px solid",
        border_color="gray.200",
        bg="gray.50",
        align_items="start"
    )


def create_nav_item(tab_id: str, label: str, icon: str) -> rx.Component:
    """Create a navigation item."""
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label),
            spacing="2",
            align_items="center"
        ),
        on_click=lambda: DashboardState.set_active_tab(tab_id),
        variant="ghost" if DashboardState.active_tab != tab_id else "soft",
        color_scheme="blue" if DashboardState.active_tab == tab_id else "gray",
        justify="start",
        width="100%"
    )


def create_main_content() -> rx.Component:
    """Create the main content area."""
    return rx.vstack(
        # Messages
        rx.cond(
            DashboardState.has_messages,
            rx.vstack(
                rx.cond(
                    DashboardState.error_message != "",
                    rx.callout(
                        DashboardState.error_message,
                        icon="alert-circle",
                        color_scheme="red"
                    )
                ),
                rx.cond(
                    DashboardState.success_message != "",
                    rx.callout(
                        DashboardState.success_message,
                        icon="check-circle",
                        color_scheme="green"
                    )
                ),
                spacing="2",
                width="100%"
            )
        ),
        
        # Tab content
        rx.match(
            DashboardState.active_tab,
            ("overview", create_overview_tab()),
            ("files", create_files_tab()),
            ("symbols", create_symbols_tab()),
            ("errors", create_errors_tab()),
            ("deadcode", create_deadcode_tab()),
            ("metrics", create_metrics_tab()),
            create_overview_tab()  # default
        ),
        
        spacing="4",
        width="100%",
        height="100%",
        padding="1rem",
        align_items="start"
    )


def create_overview_tab() -> rx.Component:
    """Create the overview tab content."""
    return rx.vstack(
        rx.heading("Dashboard Overview", size="xl"),
        
        rx.cond(
            DashboardState.codebase_loaded,
            rx.vstack(
                # Stats cards
                rx.hstack(
                    create_stat_card("Files", DashboardState.total_files, "file-text", "blue"),
                    create_stat_card("Errors", DashboardState.total_errors, "alert-circle", "red"),
                    create_stat_card("Warnings", DashboardState.total_warnings, "alert-triangle", "yellow"),
                    create_stat_card("Symbols", DashboardState.total_symbols, "code", "green"),
                    spacing="4",
                    width="100%"
                ),
                
                # Analysis status
                rx.card(
                    rx.vstack(
                        rx.heading("Analysis Status", size="md"),
                        rx.hstack(
                            rx.icon("activity", size=20, color="blue.500"),
                            rx.text(
                                DashboardState.analysis_status,
                                size="lg",
                                weight="medium"
                            ),
                            spacing="2",
                            align_items="center"
                        ),
                        rx.cond(
                            DashboardState.last_analysis_time != "",
                            rx.text(
                                f"Last analysis: {DashboardState.last_analysis_time}",
                                size="sm",
                                color="gray.500"
                            )
                        ),
                        spacing="3",
                        align_items="start"
                    ),
                    width="100%"
                ),
                
                spacing="6",
                width="100%"
            ),
            
            # No codebase loaded
            rx.card(
                rx.vstack(
                    rx.icon("folder-open", size=48, color="gray.400"),
                    rx.heading("No Codebase Loaded", size="lg", color="gray.600"),
                    rx.text(
                        "Select and load a codebase from the sidebar to begin analysis.",
                        color="gray.500",
                        text_align="center"
                    ),
                    spacing="4",
                    align_items="center"
                ),
                width="100%",
                padding="3rem"
            )
        ),
        
        spacing="6",
        width="100%",
        align_items="start"
    )


def create_stat_card(title: str, value: int, icon: str, color: str) -> rx.Component:
    """Create a statistics card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=20, color=f"{color}.500"),
                rx.text(title, size="sm", color="gray.600"),
                justify="between",
                width="100%"
            ),
            rx.text(
                str(value),
                size="2xl",
                weight="bold",
                color=f"{color}.600"
            ),
            spacing="2",
            align_items="start"
        ),
        width="200px"
    )


def create_files_tab() -> rx.Component:
    """Create the files tab content."""
    from .file_tree import create_file_tree, create_file_details_panel, create_file_content_viewer
    
    return rx.vstack(
        rx.heading("File Explorer", size="xl"),
        
        rx.hstack(
            # File tree
            rx.vstack(
                create_file_tree(),
                width="400px",
                height="600px",
                overflow="auto",
                border="1px solid",
                border_color="gray.200",
                border_radius="md",
                padding="1rem"
            ),
            
            # File details and content
            rx.vstack(
                create_file_details_panel(),
                create_file_content_viewer(),
                spacing="4",
                width="100%",
                align_items="start"
            ),
            
            spacing="4",
            width="100%",
            align_items="start"
        ),
        
        spacing="4",
        width="100%",
        align_items="start"
    )


def create_symbols_tab() -> rx.Component:
    """Create the symbols tab content."""
    return rx.vstack(
        rx.heading("Symbol Tree", size="xl"),
        rx.text("Symbol tree visualization will be implemented here.", color="gray.500"),
        spacing="4",
        width="100%"
    )


def create_errors_tab() -> rx.Component:
    """Create the errors tab content."""
    return rx.vstack(
        rx.heading("LSP Diagnostics", size="xl"),
        rx.text("LSP error diagnostics will be displayed here.", color="gray.500"),
        spacing="4",
        width="100%"
    )


def create_deadcode_tab() -> rx.Component:
    """Create the dead code tab content."""
    return rx.vstack(
        rx.heading("Dead Code Analysis", size="xl"),
        rx.text("Dead code detection results will be shown here.", color="gray.500"),
        spacing="4",
        width="100%"
    )


def create_metrics_tab() -> rx.Component:
    """Create the metrics tab content."""
    return rx.vstack(
        rx.heading("Codebase Metrics", size="xl"),
        rx.text("Detailed metrics and charts will be displayed here.", color="gray.500"),
        spacing="4",
        width="100%"
    )


def create_main_layout() -> rx.Component:
    """Create the main dashboard layout."""
    return rx.vstack(
        create_header(),
        rx.hstack(
            create_sidebar(),
            create_main_content(),
            spacing="0",
            width="100%",
            height="calc(100vh - 80px)"
        ),
        spacing="0",
        width="100%",
        height="100vh"
    )
