"""
Issue Modal Component

Detailed modal dialog for displaying comprehensive issue information
including context, suggestions, and code snippets.
"""

import reflex as rx
from typing import Dict, Any, Callable
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES
from ...utils.formatters import format_issue_severity, format_issue_type, format_file_path


def issue_modal(
    issue: Dict[str, Any],
    is_open: bool,
    on_close: Callable
) -> rx.Component:
    """
    Detailed issue modal component.
    
    Args:
        issue: Issue data dictionary
        is_open: Whether the modal is open
        on_close: Close handler
    """
    if not issue:
        return rx.fragment()
    
    severity = issue.get("severity", "minor")
    severity_info = format_issue_severity(severity)
    issue_type = issue.get("type", "unknown")
    message = issue.get("message", "Unknown issue")
    file_path = issue.get("file_path", "")
    line_number = issue.get("line_number", 0)
    column = issue.get("column", 0)
    function_name = issue.get("function_name")
    class_name = issue.get("class_name")
    context = issue.get("context", "")
    suggestion = issue.get("suggestion", "")
    
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(
                    rx.hstack(
                        rx.text(
                            severity_info["icon"],
                            font_size="1.5em",
                            color=severity_info["color"]
                        ),
                        rx.vstack(
                            rx.heading(
                                format_issue_type(issue_type),
                                size="lg",
                                color=COLORS["gray"]["900"],
                                margin="0"
                            ),
                            rx.badge(
                                severity_info["label"],
                                color_scheme=severity_info["color"],
                                size="sm"
                            ),
                            spacing=SPACING["xs"],
                            align="start"
                        ),
                        spacing=SPACING["md"],
                        align="center",
                        width="100%"
                    )
                ),
                
                rx.modal_body(
                    rx.vstack(
                        # Issue message
                        rx.box(
                            rx.text(
                                "Issue Description:",
                                font_weight="600",
                                color=COLORS["gray"]["700"],
                                margin_bottom=SPACING["sm"]
                            ),
                            rx.text(
                                message,
                                color=COLORS["gray"]["800"],
                                line_height="1.6"
                            ),
                            margin_bottom=SPACING["lg"]
                        ),
                        
                        # Location information
                        rx.box(
                            rx.text(
                                "Location:",
                                font_weight="600",
                                color=COLORS["gray"]["700"],
                                margin_bottom=SPACING["sm"]
                            ),
                            rx.vstack(
                                rx.hstack(
                                    rx.icon(tag="file", size="sm", color=COLORS["gray"]["500"]),
                                    rx.text(
                                        "File:",
                                        font_weight="500",
                                        color=COLORS["gray"]["600"]
                                    ),
                                    rx.text(
                                        file_path,
                                        font_family="mono",
                                        color=COLORS["gray"]["800"]
                                    ),
                                    spacing=SPACING["sm"],
                                    align="center"
                                ),
                                
                                rx.hstack(
                                    rx.icon(tag="map_pin", size="sm", color=COLORS["gray"]["500"]),
                                    rx.text(
                                        "Position:",
                                        font_weight="500",
                                        color=COLORS["gray"]["600"]
                                    ),
                                    rx.text(
                                        f"Line {line_number}, Column {column}",
                                        font_family="mono",
                                        color=COLORS["gray"]["800"]
                                    ),
                                    spacing=SPACING["sm"],
                                    align="center"
                                ),
                                
                                rx.cond(
                                    function_name or class_name,
                                    rx.hstack(
                                        rx.icon(tag="code", size="sm", color=COLORS["gray"]["500"]),
                                        rx.text(
                                            "Context:",
                                            font_weight="500",
                                            color=COLORS["gray"]["600"]
                                        ),
                                        rx.text(
                                            f"{class_name + '.' if class_name else ''}{function_name or ''}",
                                            font_family="mono",
                                            color=COLORS["gray"]["800"]
                                        ),
                                        spacing=SPACING["sm"],
                                        align="center"
                                    )
                                ),
                                
                                spacing=SPACING["sm"],
                                align="start"
                            ),
                            margin_bottom=SPACING["lg"]
                        ),
                        
                        # Code context
                        rx.cond(
                            context,
                            rx.box(
                                rx.text(
                                    "Code Context:",
                                    font_weight="600",
                                    color=COLORS["gray"]["700"],
                                    margin_bottom=SPACING["sm"]
                                ),
                                rx.box(
                                    rx.text(
                                        context,
                                        font_family="mono",
                                        font_size="0.85em",
                                        color=COLORS["gray"]["800"],
                                        white_space="pre-wrap"
                                    ),
                                    background=COLORS["gray"]["50"],
                                    border=f"1px solid {COLORS['gray']['200']}",
                                    border_radius="6px",
                                    padding=SPACING["md"],
                                    overflow="auto",
                                    max_height="200px"
                                ),
                                margin_bottom=SPACING["lg"]
                            )
                        ),
                        
                        # Suggestion
                        rx.cond(
                            suggestion,
                            rx.box(
                                rx.text(
                                    "Suggested Fix:",
                                    font_weight="600",
                                    color=COLORS["success"]["700"],
                                    margin_bottom=SPACING["sm"]
                                ),
                                rx.box(
                                    rx.text(
                                        suggestion,
                                        color=COLORS["gray"]["800"],
                                        line_height="1.6"
                                    ),
                                    background=COLORS["success"]["50"],
                                    border=f"1px solid {COLORS['success']['200']}",
                                    border_radius="6px",
                                    padding=SPACING["md"]
                                ),
                                margin_bottom=SPACING["lg"]
                            )
                        ),
                        
                        # Issue metadata
                        rx.box(
                            rx.text(
                                "Issue Details:",
                                font_weight="600",
                                color=COLORS["gray"]["700"],
                                margin_bottom=SPACING["sm"]
                            ),
                            rx.grid(
                                rx.hstack(
                                    rx.text("Type:", font_weight="500", color=COLORS["gray"]["600"]),
                                    rx.text(format_issue_type(issue_type), color=COLORS["gray"]["800"]),
                                    spacing=SPACING["sm"]
                                ),
                                rx.hstack(
                                    rx.text("Severity:", font_weight="500", color=COLORS["gray"]["600"]),
                                    rx.text(severity_info["label"], color=severity_info["color"], font_weight="500"),
                                    spacing=SPACING["sm"]
                                ),
                                rx.hstack(
                                    rx.text("ID:", font_weight="500", color=COLORS["gray"]["600"]),
                                    rx.text(issue.get("id", "N/A"), font_family="mono", color=COLORS["gray"]["800"]),
                                    spacing=SPACING["sm"]
                                ),
                                columns=1,
                                spacing=SPACING["sm"]
                            )
                        ),
                        
                        spacing="0",
                        align="start",
                        width="100%"
                    )
                ),
                
                rx.modal_footer(
                    rx.hstack(
                        rx.button(
                            "Close",
                            on_click=on_close,
                            style=COMPONENT_STYLES["button_secondary"]
                        ),
                        rx.button(
                            rx.icon(tag="external_link", size="sm"),
                            "Open in Editor",
                            style=COMPONENT_STYLES["button_primary"],
                            disabled=True  # TODO: Implement editor integration
                        ),
                        spacing=SPACING["sm"]
                    )
                ),
                
                max_width="700px",
                background="white",
                border_radius="12px",
                box_shadow="0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"
            )
        ),
        
        is_open=is_open,
        on_close=on_close,
        size="xl",
        is_centered=True
    )

