"""
Analysis Progress Component

Shows real-time progress during codebase analysis.
"""

import reflex as rx
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES
from ..common.progress_bar import progress_bar, circular_progress
from ..common.loading_spinner import loading_spinner


def analysis_progress() -> rx.Component:
    """Analysis progress display component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.vstack(
                rx.heading(
                    "Analyzing Repository",
                    size="xl",
                    color=COLORS["gray"]["900"],
                    text_align="center"
                ),
                rx.text(
                    AppState.repository_name,
                    color=COLORS["primary"]["600"],
                    font_weight="600",
                    size="lg",
                    text_align="center"
                ),
                spacing=SPACING["sm"],
                align="center"
            ),
            
            # Progress visualization
            rx.hstack(
                # Circular progress
                rx.vstack(
                    circular_progress(
                        value=AppState.analysis_progress,
                        size="120px",
                        thickness="8px"
                    ),
                    rx.text(
                        "Overall Progress",
                        color=COLORS["gray"]["600"],
                        size="sm",
                        text_align="center"
                    ),
                    spacing=SPACING["sm"],
                    align="center"
                ),
                
                # Progress details
                rx.vstack(
                    rx.vstack(
                        rx.text(
                            "Current Step:",
                            color=COLORS["gray"]["700"],
                            font_weight="600"
                        ),
                        rx.text(
                            AppState.analysis_message,
                            color=COLORS["primary"]["600"],
                            font_weight="500"
                        ),
                        spacing=SPACING["xs"],
                        align="start"
                    ),
                    
                    progress_bar(
                        value=AppState.analysis_progress,
                        height="12px"
                    ),
                    
                    rx.hstack(
                        rx.text(
                            "Repository:",
                            color=COLORS["gray"]["600"],
                            size="sm"
                        ),
                        rx.text(
                            AppState.repository_url,
                            color=COLORS["gray"]["800"],
                            size="sm",
                            font_family="mono"
                        ),
                        spacing=SPACING["sm"]
                    ),
                    
                    rx.hstack(
                        rx.text(
                            "Started:",
                            color=COLORS["gray"]["600"],
                            size="sm"
                        ),
                        rx.text(
                            AppState.analysis_start_time.strftime("%H:%M:%S") if AppState.analysis_start_time else "Unknown",
                            color=COLORS["gray"]["800"],
                            size="sm"
                        ),
                        spacing=SPACING["sm"]
                    ),
                    
                    spacing=SPACING["lg"],
                    align="start",
                    flex="1"
                ),
                
                spacing=SPACING["2xl"],
                align="center",
                width="100%"
            ),
            
            # Analysis steps
            rx.vstack(
                rx.text(
                    "Analysis Steps:",
                    color=COLORS["gray"]["700"],
                    font_weight="600",
                    size="lg"
                ),
                
                rx.vstack(
                    # Step 1: Building codebase
                    rx.hstack(
                        rx.cond(
                            AppState.analysis_progress >= 20,
                            rx.icon(
                                tag="check_circle",
                                color=COLORS["success"]["600"],
                                size="sm"
                            ),
                            rx.cond(
                                AppState.analysis_progress >= 0,
                                rx.spinner(
                                    size="16px",
                                    color=COLORS["primary"]["600"]
                                ),
                                rx.icon(
                                    tag="circle",
                                    color=COLORS["gray"]["400"],
                                    size="sm"
                                )
                            )
                        ),
                        rx.text(
                            "Building codebase structure",
                            color=COLORS["gray"]["700"]
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    ),
                    
                    # Step 2: Detecting issues
                    rx.hstack(
                        rx.cond(
                            AppState.analysis_progress >= 50,
                            rx.icon(
                                tag="check_circle",
                                color=COLORS["success"]["600"],
                                size="sm"
                            ),
                            rx.cond(
                                AppState.analysis_progress >= 20,
                                rx.spinner(
                                    size="16px",
                                    color=COLORS["primary"]["600"]
                                ),
                                rx.icon(
                                    tag="circle",
                                    color=COLORS["gray"]["400"],
                                    size="sm"
                                )
                            )
                        ),
                        rx.text(
                            "Detecting issues and problems",
                            color=COLORS["gray"]["700"]
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    ),
                    
                    # Step 3: Analyzing dead code
                    rx.hstack(
                        rx.cond(
                            AppState.analysis_progress >= 75,
                            rx.icon(
                                tag="check_circle",
                                color=COLORS["success"]["600"],
                                size="sm"
                            ),
                            rx.cond(
                                AppState.analysis_progress >= 50,
                                rx.spinner(
                                    size="16px",
                                    color=COLORS["primary"]["600"]
                                ),
                                rx.icon(
                                    tag="circle",
                                    color=COLORS["gray"]["400"],
                                    size="sm"
                                )
                            )
                        ),
                        rx.text(
                            "Analyzing dead code and unused elements",
                            color=COLORS["gray"]["700"]
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    ),
                    
                    # Step 4: Identifying important functions
                    rx.hstack(
                        rx.cond(
                            AppState.analysis_progress >= 90,
                            rx.icon(
                                tag="check_circle",
                                color=COLORS["success"]["600"],
                                size="sm"
                            ),
                            rx.cond(
                                AppState.analysis_progress >= 75,
                                rx.spinner(
                                    size="16px",
                                    color=COLORS["primary"]["600"]
                                ),
                                rx.icon(
                                    tag="circle",
                                    color=COLORS["gray"]["400"],
                                    size="sm"
                                )
                            )
                        ),
                        rx.text(
                            "Identifying important functions and entry points",
                            color=COLORS["gray"]["700"]
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    ),
                    
                    # Step 5: Generating results
                    rx.hstack(
                        rx.cond(
                            AppState.analysis_progress >= 100,
                            rx.icon(
                                tag="check_circle",
                                color=COLORS["success"]["600"],
                                size="sm"
                            ),
                            rx.cond(
                                AppState.analysis_progress >= 90,
                                rx.spinner(
                                    size="16px",
                                    color=COLORS["primary"]["600"]
                                ),
                                rx.icon(
                                    tag="circle",
                                    color=COLORS["gray"]["400"],
                                    size="sm"
                                )
                            )
                        ),
                        rx.text(
                            "Generating tree structure and statistics",
                            color=COLORS["gray"]["700"]
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    ),
                    
                    spacing=SPACING["md"],
                    align="start",
                    width="100%"
                ),
                
                spacing=SPACING["lg"],
                align="start",
                width="100%"
            ),
            
            # Cancel button
            rx.button(
                "Cancel Analysis",
                on_click=AppState.reset_analysis,
                style=COMPONENT_STYLES["button_secondary"],
                size="sm"
            ),
            
            spacing=SPACING["2xl"],
            align="center",
            width="100%",
            max_width="800px",
            margin="0 auto"
        ),
        
        padding=SPACING["3xl"],
        min_height="80vh",
        display="flex",
        align_items="center",
        justify_content="center"
    )

