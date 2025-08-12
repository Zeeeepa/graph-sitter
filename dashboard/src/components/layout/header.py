"""
Header Component

Top navigation bar with branding, status, and controls.
"""

import reflex as rx
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES


def header() -> rx.Component:
    """Main header component."""
    return rx.box(
        rx.hstack(
            # Logo and title
            rx.hstack(
                rx.image(
                    src="/logo.svg",
                    alt="Codebase Analysis Dashboard",
                    width="32px",
                    height="32px"
                ),
                rx.vstack(
                    rx.heading(
                        "Codebase Analysis Dashboard",
                        size="lg",
                        color=COLORS["gray"]["900"],
                        margin="0"
                    ),
                    rx.text(
                        "Powered by graph-sitter & Tree-sitter",
                        size="sm",
                        color=COLORS["gray"]["600"],
                        margin="0"
                    ),
                    spacing="0",
                    align="start"
                ),
                spacing=SPACING["md"],
                align="center"
            ),
            
            # Status and controls
            rx.hstack(
                # Analysis status indicator
                rx.cond(
                    AppState.analysis_status == "analyzing",
                    rx.hstack(
                        rx.spinner(size="sm", color=COLORS["primary"]["600"]),
                        rx.text(
                            AppState.analysis_message,
                            color=COLORS["primary"]["600"],
                            font_weight="500"
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    )
                ),
                
                rx.cond(
                    AppState.analysis_status == "completed",
                    rx.hstack(
                        rx.icon(
                            tag="check_circle",
                            color=COLORS["success"]["600"],
                            size="sm"
                        ),
                        rx.text(
                            f"Analysis completed in {AppState.analysis_duration:.1f}s",
                            color=COLORS["success"]["600"],
                            font_weight="500"
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    )
                ),
                
                rx.cond(
                    AppState.analysis_status == "error",
                    rx.hstack(
                        rx.icon(
                            tag="warning",
                            color=COLORS["error"]["600"],
                            size="sm"
                        ),
                        rx.text(
                            "Analysis failed",
                            color=COLORS["error"]["600"],
                            font_weight="500"
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    )
                ),
                
                # Repository info
                rx.cond(
                    AppState.repository_name != "",
                    rx.vstack(
                        rx.text(
                            AppState.repository_name,
                            font_weight="600",
                            color=COLORS["gray"]["900"],
                            margin="0"
                        ),
                        rx.text(
                            AppState.repository_owner,
                            size="sm",
                            color=COLORS["gray"]["600"],
                            margin="0"
                        ),
                        spacing="0",
                        align="end"
                    )
                ),
                
                # Reset button
                rx.cond(
                    AppState.analysis_status != "idle",
                    rx.button(
                        rx.icon(tag="refresh", size="sm"),
                        "New Analysis",
                        on_click=AppState.reset_analysis,
                        style=COMPONENT_STYLES["button_secondary"],
                        size="sm"
                    )
                ),
                
                spacing=SPACING["lg"],
                align="center"
            ),
            
            justify="between",
            align="center",
            width="100%"
        ),
        
        background="white",
        border_bottom=f"1px solid {COLORS['gray']['200']}",
        padding=f"{SPACING['lg']} {SPACING['xl']}",
        position="sticky",
        top="0",
        z_index="50",
        box_shadow=COMPONENT_STYLES["card"]["box_shadow"]
    )

