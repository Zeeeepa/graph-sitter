"""
Statistics Display Component

Shows codebase statistics and analysis overview.
"""

import reflex as rx
from ..state.app_state import AppState


def stats_display() -> rx.Component:
    """Statistics overview display."""
    return rx.box(
        rx.grid(
            # Files stat
            stat_card(
                "📁",
                "Files",
                AppState.codebase_stats["total_files"],
                "Source files analyzed"
            ),
            
            # Functions stat
            stat_card(
                "⚡",
                "Functions", 
                AppState.codebase_stats["total_functions"],
                "Functions discovered"
            ),
            
            # Classes stat
            stat_card(
                "🏗️",
                "Classes",
                AppState.codebase_stats["total_classes"], 
                "Classes found"
            ),
            
            # Lines of code stat
            stat_card(
                "📝",
                "Lines of Code",
                AppState.codebase_stats["lines_of_code"],
                "Total lines analyzed"
            ),
            
            # Issues stat
            stat_card(
                "🐛",
                "Issues",
                AppState.total_issues,
                "Issues detected",
                color_scheme="red" if AppState.get_issue_count_by_severity("critical") > 0 else "orange" if AppState.total_issues > 0 else "green"
            ),
            
            # Dead code stat
            stat_card(
                "💀",
                "Dead Code",
                len(AppState.dead_code_functions) + len(AppState.dead_code_classes),
                "Unused code detected",
                color_scheme="orange"
            ),
            
            columns="6",
            spacing="4",
            width="100%"
        ),
        
        padding="1rem",
        border="1px solid var(--gray-6)",
        border_radius="8px",
        background="white",
        margin_bottom="2rem"
    )


def stat_card(icon: str, title: str, value: int, description: str, color_scheme: str = "blue") -> rx.Component:
    """Individual statistic card."""
    return rx.box(
        rx.vstack(
            rx.text(icon, size="6"),
            rx.text(
                str(value),
                size="6",
                weight="bold",
                color=f"var(--{color_scheme}-11)"
            ),
            rx.text(
                title,
                size="3",
                weight="medium",
                color="var(--gray-11)"
            ),
            rx.text(
                description,
                size="1",
                color="var(--gray-9)",
                text_align="center"
            ),
            spacing="1",
            align="center"
        ),
        
        padding="1rem",
        border=f"1px solid var(--{color_scheme}-6)",
        border_radius="8px",
        background=f"var(--{color_scheme}-2)",
        text_align="center",
        min_height="120px",
        display="flex",
        align_items="center",
        justify_content="center"
    )
