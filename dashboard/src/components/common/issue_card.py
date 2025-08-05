"""
Issue Card Component

Individual issue card component for displaying issue information
in a clean, clickable format with severity indicators.
"""

import reflex as rx
from typing import Dict, Any, Callable
from ...styles.theme import COLORS, SPACING
from ...utils.formatters import format_issue_severity, format_issue_type, format_file_path


def issue_card(issue: Dict[str, Any], on_click: Callable) -> rx.Component:
    """
    Individual issue card component.
    
    Args:
        issue: Issue data dictionary
        on_click: Click handler for showing issue details
    """
    severity = issue.get("severity", "minor")
    severity_info = format_issue_severity(severity)
    issue_type = issue.get("type", "unknown")
    message = issue.get("message", "Unknown issue")
    file_path = issue.get("file_path", "")
    line_number = issue.get("line_number", 0)
    function_name = issue.get("function_name")
    class_name = issue.get("class_name")
    
    return rx.box(
        rx.hstack(
            # Severity indicator
            rx.box(
                rx.text(
                    severity_info["icon"],
                    font_size="1.2em",
                    color=severity_info["color"]
                ),
                width="40px",
                display="flex",
                align_items="center",
                justify_content="center"
            ),
            
            # Issue content
            rx.vstack(
                # Issue message
                rx.text(
                    message,
                    color=COLORS["gray"]["800"],
                    font_weight="600",
                    font_size="0.95em",
                    margin="0"
                ),
                
                # Issue metadata
                rx.hstack(
                    # File and line
                    rx.hstack(
                        rx.icon(tag="file", size="xs", color=COLORS["gray"]["500"]),
                        rx.text(
                            format_file_path(file_path, 40),
                            color=COLORS["gray"]["600"],
                            font_family="mono",
                            size="sm"
                        ),
                        rx.cond(
                            line_number > 0,
                            rx.text(
                                f":{line_number}",
                                color=COLORS["primary"]["600"],
                                font_family="mono",
                                size="sm",
                                font_weight="500"
                            )
                        ),
                        spacing=SPACING["xs"],
                        align="center"
                    ),
                    
                    # Function/Class context
                    rx.cond(
                        function_name or class_name,
                        rx.hstack(
                            rx.icon(tag="code", size="xs", color=COLORS["gray"]["500"]),
                            rx.text(
                                f"{class_name + '.' if class_name else ''}{function_name or ''}",
                                color=COLORS["gray"]["600"],
                                font_family="mono",
                                size="sm"
                            ),
                            spacing=SPACING["xs"],
                            align="center"
                        )
                    ),
                    
                    spacing=SPACING["md"],
                    wrap="wrap"
                ),
                
                spacing=SPACING["xs"],
                align="start",
                flex="1"
            ),
            
            # Issue type and severity badges
            rx.vstack(
                rx.badge(
                    format_issue_type(issue_type),
                    color_scheme="gray",
                    size="sm",
                    variant="outline"
                ),
                rx.badge(
                    severity_info["label"],
                    color_scheme=severity_info["color"],
                    size="sm",
                    variant="solid"
                ),
                spacing=SPACING["xs"],
                align="end"
            ),
            
            spacing=SPACING["md"],
            align="start",
            width="100%"
        ),
        
        background="white",
        border=f"1px solid {COLORS['gray']['200']}",
        border_left=f"4px solid {severity_info['color']}",
        border_radius="8px",
        padding=SPACING["md"],
        cursor="pointer",
        transition="all 0.2s ease",
        _hover={
            "background": COLORS["gray"]["50"],
            "border_color": severity_info["color"],
            "box_shadow": "0 2px 8px rgba(0, 0, 0, 0.1)"
        },
        on_click=on_click,
        width="100%"
    )


def issue_summary_card(
    title: str,
    count: int,
    severity: str,
    description: str = ""
) -> rx.Component:
    """Summary card for issue counts by severity or type."""
    severity_info = format_issue_severity(severity)
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    severity_info["icon"],
                    font_size="1.5em",
                    color=severity_info["color"]
                ),
                rx.vstack(
                    rx.text(
                        str(count),
                        font_size="1.8em",
                        font_weight="700",
                        color=severity_info["color"],
                        margin="0"
                    ),
                    rx.text(
                        title,
                        font_weight="600",
                        color=COLORS["gray"]["700"],
                        margin="0"
                    ),
                    spacing="0",
                    align="start"
                ),
                spacing=SPACING["md"],
                align="center",
                width="100%"
            ),
            
            rx.cond(
                description,
                rx.text(
                    description,
                    color=COLORS["gray"]["600"],
                    size="sm",
                    text_align="center"
                )
            ),
            
            spacing=SPACING["sm"],
            align="center"
        ),
        
        background=severity_info["bg_color"],
        border=f"1px solid {severity_info['border_color']}",
        border_radius="12px",
        padding=SPACING["lg"],
        text_align="center",
        min_width="150px"
    )
