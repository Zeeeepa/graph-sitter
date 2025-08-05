"""
Results View Component

Main results container with tab navigation for switching between different analysis views.
Displays tree structure, issues, dead code, important functions, and statistics.
"""

import reflex as rx
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES
from .tree_visualization import tree_visualization
from .issues_display import issues_display
from .dead_code_display import dead_code_display
from .important_functions_display import important_functions_display
from .statistics_display import statistics_display


def results_view() -> rx.Component:
    """Main results view with tab navigation."""
    return rx.box(
        rx.vstack(
            # Results header with repository info and summary
            rx.box(
                rx.vstack(
                    # Repository header
                    rx.hstack(
                        rx.vstack(
                            rx.heading(
                                AppState.repository_name,
                                size="xl",
                                color=COLORS["gray"]["900"],
                                margin="0"
                            ),
                            rx.text(
                                AppState.repository_url,
                                color=COLORS["gray"]["600"],
                                font_family="mono",
                                size="sm",
                                margin="0"
                            ),
                            spacing="0",
                            align="start"
                        ),
                        
                        # Quick stats
                        rx.hstack(
                            _create_stat_badge(
                                "Files",
                                AppState.stats_data.get("total_files", 0),
                                "📁",
                                COLORS["blue"]["600"]
                            ),
                            _create_stat_badge(
                                "Issues",
                                AppState.stats_data.get("total_issues", 0),
                                "⚠️",
                                COLORS["warning"]["600"]
                            ),
                            _create_stat_badge(
                                "Functions",
                                AppState.stats_data.get("total_functions", 0),
                                "⚡",
                                COLORS["green"]["600"]
                            ),
                            _create_stat_badge(
                                "Dead Code",
                                AppState.stats_data.get("dead_code_count", 0),
                                "💀",
                                COLORS["error"]["600"]
                            ),
                            spacing=SPACING["md"],
                            wrap="wrap"
                        ),
                        
                        justify="between",
                        align="start",
                        width="100%"
                    ),
                    
                    spacing=SPACING["lg"]
                ),
                
                **COMPONENT_STYLES["card"],
                margin_bottom=SPACING["lg"]
            ),
            
            # Tab navigation
            rx.tabs(
                rx.tab_list(
                    rx.tab(
                        rx.hstack(
                            rx.icon(tag="tree", size="sm"),
                            "Tree Structure",
                            spacing=SPACING["sm"],
                            align="center"
                        ),
                        value="tree"
                    ),
                    rx.tab(
                        rx.hstack(
                            rx.icon(tag="bug", size="sm"),
                            "Issues",
                            rx.cond(
                                AppState.stats_data.get("total_issues", 0) > 0,
                                rx.badge(
                                    AppState.stats_data.get("total_issues", 0),
                                    color_scheme="red",
                                    size="sm"
                                )
                            ),
                            spacing=SPACING["sm"],
                            align="center"
                        ),
                        value="issues"
                    ),
                    rx.tab(
                        rx.hstack(
                            rx.icon(tag="trash", size="sm"),
                            "Dead Code",
                            rx.cond(
                                AppState.stats_data.get("dead_code_count", 0) > 0,
                                rx.badge(
                                    AppState.stats_data.get("dead_code_count", 0),
                                    color_scheme="orange",
                                    size="sm"
                                )
                            ),
                            spacing=SPACING["sm"],
                            align="center"
                        ),
                        value="dead_code"
                    ),
                    rx.tab(
                        rx.hstack(
                            rx.icon(tag="star", size="sm"),
                            "Important Functions",
                            spacing=SPACING["sm"],
                            align="center"
                        ),
                        value="important_functions"
                    ),
                    rx.tab(
                        rx.hstack(
                            rx.icon(tag="bar_chart", size="sm"),
                            "Statistics",
                            spacing=SPACING["sm"],
                            align="center"
                        ),
                        value="statistics"
                    ),
                    
                    border_bottom=f"1px solid {COLORS['gray']['200']}",
                    margin_bottom=SPACING["lg"]
                ),
                
                # Tab panels
                rx.tab_panels(
                    rx.tab_panel(
                        tree_visualization(),
                        value="tree"
                    ),
                    rx.tab_panel(
                        issues_display(),
                        value="issues"
                    ),
                    rx.tab_panel(
                        dead_code_display(),
                        value="dead_code"
                    ),
                    rx.tab_panel(
                        important_functions_display(),
                        value="important_functions"
                    ),
                    rx.tab_panel(
                        statistics_display(),
                        value="statistics"
                    )
                ),
                
                value=AppState.active_tab,
                on_change=AppState.set_active_tab,
                variant="enclosed",
                color_scheme="blue",
                width="100%"
            ),
            
            spacing="0",
            width="100%"
        ),
        
        padding=SPACING["xl"],
        width="100%",
        max_width="1400px",
        margin="0 auto"
    )


def _create_stat_badge(label: str, value: int, icon: str, color: str) -> rx.Component:
    """Create a stat badge for the header."""
    return rx.hstack(
        rx.text(
            icon,
            font_size="1.2em"
        ),
        rx.vstack(
            rx.text(
                str(value),
                font_weight="700",
                font_size="1.1em",
                color=color,
                margin="0"
            ),
            rx.text(
                label,
                color=COLORS["gray"]["600"],
                size="sm",
                margin="0"
            ),
            spacing="0",
            align="start"
        ),
        
        spacing=SPACING["sm"],
        align="center",
        padding=SPACING["sm"],
        border_radius=COMPONENT_STYLES["card"]["border_radius"],
        background=COLORS["gray"]["50"],
        border=f"1px solid {COLORS['gray']['200']}"
    )

