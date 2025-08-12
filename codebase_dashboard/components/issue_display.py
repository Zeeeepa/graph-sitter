"""
Issue Display Component

Shows detailed issue information with filtering and context viewing.
"""

import reflex as rx
from typing import Dict, List, Any
from ..state.app_state import AppState


def issues_panel() -> rx.Component:
    """Issues panel with filtering and detailed view."""
    return rx.box(
        rx.vstack(
            # Panel header
            rx.hstack(
                rx.heading("🐛 Issues", size="5"),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=16),
                    variant="ghost",
                    size="2",
                    on_click=AppState.toggle_issues_panel
                ),
                width="100%",
                align="center"
            ),
            
            # Issue filters
            rx.hstack(
                rx.button(
                    f"All ({AppState.total_issues})",
                    variant="soft" if AppState.issue_filter_severity == "all" else "ghost",
                    size="2",
                    on_click=AppState.set_issue_filter("all")
                ),
                rx.button(
                    f"Critical ({AppState.get_issue_count_by_severity('critical')})",
                    variant="soft" if AppState.issue_filter_severity == "critical" else "ghost",
                    color_scheme="red",
                    size="2",
                    on_click=AppState.set_issue_filter("critical")
                ),
                rx.button(
                    f"Major ({AppState.get_issue_count_by_severity('major')})",
                    variant="soft" if AppState.issue_filter_severity == "major" else "ghost",
                    color_scheme="orange",
                    size="2",
                    on_click=AppState.set_issue_filter("major")
                ),
                rx.button(
                    f"Minor ({AppState.get_issue_count_by_severity('minor')})",
                    variant="soft" if AppState.issue_filter_severity == "minor" else "ghost",
                    color_scheme="yellow",
                    size="2",
                    on_click=AppState.set_issue_filter("minor")
                ),
                spacing="2",
                wrap="wrap"
            ),
            
            # Issues list
            rx.box(
                rx.cond(
                    len(AppState.get_filtered_issues()) > 0,
                    rx.vstack(
                        rx.foreach(
                            AppState.get_filtered_issues(),
                            lambda issue: issue_item(issue)
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    rx.center(
                        rx.text(
                            "No issues found",
                            size="3",
                            color="var(--gray-10)"
                        ),
                        height="100px"
                    )
                ),
                max_height="400px",
                overflow_y="auto",
                width="100%"
            ),
            
            spacing="4",
            width="100%"
        ),
        
        padding="1rem",
        border="1px solid var(--gray-6)",
        border_radius="8px",
        background="white",
        width="100%"
    )


def issue_item(issue: Dict[str, Any]) -> rx.Component:
    """Individual issue item."""
    return rx.box(
        rx.vstack(
            # Issue header
            rx.hstack(
                # Severity indicator
                severity_badge(issue.get("severity", "minor")),
                
                # Issue type
                rx.text(
                    issue.get("type", "unknown").replace("_", " ").title(),
                    size="3",
                    weight="medium"
                ),
                
                rx.spacer(),
                
                # File location
                rx.text(
                    f"{issue.get('file_path', 'unknown')}:{issue.get('line_number', 0)}",
                    size="2",
                    color="var(--gray-10)"
                ),
                
                width="100%",
                align="center"
            ),
            
            # Issue message
            rx.text(
                issue.get("message", "No message"),
                size="2",
                color="var(--gray-11)"
            ),
            
            # Function/class context
            rx.cond(
                issue.get("function_name") or issue.get("class_name"),
                rx.hstack(
                    rx.cond(
                        issue.get("function_name"),
                        rx.badge(
                            f"fn: {issue['function_name']}",
                            variant="soft",
                            color_scheme="blue",
                            size="1"
                        )
                    ),
                    rx.cond(
                        issue.get("class_name"),
                        rx.badge(
                            f"class: {issue['class_name']}",
                            variant="soft",
                            color_scheme="green",
                            size="1"
                        )
                    ),
                    spacing="2"
                )
            ),
            
            # Suggestion
            rx.cond(
                issue.get("suggestion"),
                rx.box(
                    rx.text(
                        "💡 Suggestion:",
                        size="2",
                        weight="medium",
                        color="var(--blue-11)"
                    ),
                    rx.text(
                        issue.get("suggestion", ""),
                        size="2",
                        color="var(--gray-11)",
                        font_family="monospace",
                        background="var(--gray-3)",
                        padding="4px 8px",
                        border_radius="4px"
                    ),
                    width="100%"
                )
            ),
            
            spacing="2",
            align="start",
            width="100%"
        ),
        
        padding="12px",
        border="1px solid var(--gray-6)",
        border_radius="6px",
        background="var(--gray-2)",
        _hover={"background": "var(--gray-3)"},
        cursor="pointer",
        on_click=AppState.select_issue(issue),
        width="100%"
    )


def severity_badge(severity: str) -> rx.Component:
    """Severity badge component."""
    color_map = {
        "critical": "red",
        "major": "orange", 
        "minor": "yellow"
    }
    
    icon_map = {
        "critical": "⚠️",
        "major": "👉",
        "minor": "🔍"
    }
    
    return rx.badge(
        f"{icon_map.get(severity, '🔍')} {severity.title()}",
        variant="soft",
        color_scheme=color_map.get(severity, "gray"),
        size="1"
    )


def issue_detail_modal() -> rx.Component:
    """Detailed issue view modal."""
    return rx.cond(
        AppState.selected_issue,
        rx.dialog.root(
            rx.dialog.trigger(rx.box()),  # Hidden trigger
            rx.dialog.content(
                rx.dialog.title("Issue Details"),
                
                rx.vstack(
                    # Issue header
                    rx.hstack(
                        severity_badge(AppState.selected_issue.get("severity", "minor")),
                        rx.text(
                            AppState.selected_issue.get("type", "unknown").replace("_", " ").title(),
                            size="4",
                            weight="bold"
                        ),
                        spacing="3"
                    ),
                    
                    # Location
                    rx.text(
                        f"📍 {AppState.selected_issue.get('file_path', 'unknown')}:{AppState.selected_issue.get('line_number', 0)}",
                        size="3",
                        color="var(--gray-11)"
                    ),
                    
                    # Message
                    rx.box(
                        rx.text("Message:", size="3", weight="medium"),
                        rx.text(
                            AppState.selected_issue.get("message", "No message"),
                            size="3",
                            color="var(--gray-11)"
                        ),
                        width="100%"
                    ),
                    
                    # Context
                    rx.cond(
                        AppState.selected_issue.get("context"),
                        rx.box(
                            rx.text("Context:", size="3", weight="medium"),
                            rx.code_block(
                                AppState.selected_issue.get("context", ""),
                                language="python",
                                width="100%"
                            ),
                            width="100%"
                        )
                    ),
                    
                    # Suggestion
                    rx.cond(
                        AppState.selected_issue.get("suggestion"),
                        rx.box(
                            rx.text("💡 Suggestion:", size="3", weight="medium", color="var(--blue-11)"),
                            rx.text(
                                AppState.selected_issue.get("suggestion", ""),
                                size="3",
                                color="var(--gray-11)",
                                font_family="monospace",
                                background="var(--gray-3)",
                                padding="8px",
                                border_radius="4px"
                            ),
                            width="100%"
                        )
                    ),
                    
                    spacing="4",
                    width="100%"
                ),
                
                rx.dialog.close(
                    rx.button("Close", variant="soft")
                ),
                
                max_width="600px"
            ),
            open=AppState.selected_issue is not None
        )
    )
