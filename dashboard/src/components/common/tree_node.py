"""
Tree Node Component

Individual tree node component with expand/collapse functionality,
issue indicators, and interactive styling.
"""

import reflex as rx
from typing import Dict, Any, Callable
from ...styles.theme import COLORS, SPACING
from ...utils.formatters import format_node_type, format_issue_severity


def tree_node(
    node: Dict[str, Any],
    depth: int,
    is_expanded: bool,
    is_selected: bool,
    has_children: bool,
    on_click: Callable,
    on_expand: Callable
) -> rx.Component:
    """
    Individual tree node component.
    
    Args:
        node: Node data dictionary
        depth: Nesting depth for indentation
        is_expanded: Whether the node is expanded
        is_selected: Whether the node is selected
        has_children: Whether the node has children
        on_click: Click handler for node selection
        on_expand: Click handler for expand/collapse
    """
    node_name = node.get("name", "Unknown")
    node_type = node.get("type", "file")
    node_path = node.get("path", "")
    issues = node.get("issues", [])
    
    # Get node styling
    node_style = format_node_type(node_type)
    
    # Calculate indentation
    indent_width = f"{depth * 20}px"
    
    # Determine background color
    bg_color = "white"
    if is_selected:
        bg_color = COLORS["primary"]["50"]
    
    # Count issues by severity
    critical_issues = len([i for i in issues if i.get("severity") == "critical"])
    major_issues = len([i for i in issues if i.get("severity") == "major"])
    minor_issues = len([i for i in issues if i.get("severity") == "minor"])
    
    return rx.box(
        rx.hstack(
            # Indentation spacer
            rx.box(width=indent_width),
            
            # Expand/collapse button
            rx.box(
                rx.cond(
                    has_children,
                    rx.button(
                        rx.icon(
                            tag="chevron_right" if not is_expanded else "chevron_down",
                            size="sm",
                            color=COLORS["gray"]["600"]
                        ),
                        on_click=lambda: on_expand(node.get("path", "")),
                        variant="ghost",
                        size="sm",
                        padding="2px",
                        min_width="24px",
                        height="24px"
                    ),
                    rx.box(width="24px")  # Spacer for alignment
                ),
                width="24px"
            ),
            
            # Node icon
            rx.text(
                node_style["icon"],
                font_size="1.1em",
                color=node_style["color"]
            ),
            
            # Node name
            rx.text(
                node_name,
                color=COLORS["gray"]["800"],
                font_weight="500" if node_type == "folder" else "400",
                font_size="0.9em",
                cursor="pointer",
                _hover={"color": COLORS["primary"]["600"]},
                on_click=lambda: on_click(node.get("path", "")),
                flex="1"
            ),
            
            # Issue indicators
            rx.hstack(
                # Critical issues
                rx.cond(
                    critical_issues > 0,
                    rx.badge(
                        f"{critical_issues}",
                        color_scheme="red",
                        size="sm",
                        variant="solid"
                    )
                ),
                
                # Major issues
                rx.cond(
                    major_issues > 0,
                    rx.badge(
                        f"{major_issues}",
                        color_scheme="orange",
                        size="sm",
                        variant="solid"
                    )
                ),
                
                # Minor issues
                rx.cond(
                    minor_issues > 0,
                    rx.badge(
                        f"{minor_issues}",
                        color_scheme="yellow",
                        size="sm",
                        variant="solid"
                    )
                ),
                
                spacing=SPACING["xs"]
            ),
            
            spacing=SPACING["sm"],
            align="center",
            width="100%"
        ),
        
        background=bg_color,
        border_left=f"3px solid {COLORS['primary']['500']}" if is_selected else "3px solid transparent",
        padding=f"{SPACING['xs']} {SPACING['sm']}",
        cursor="pointer",
        _hover={
            "background": COLORS["gray"]["50"] if not is_selected else COLORS["primary"]["100"]
        },
        on_click=lambda: on_click(node.get("path", "")),
        width="100%"
    )


def tree_node_details(node: Dict[str, Any]) -> rx.Component:
    """Detailed view of a selected tree node."""
    if not node:
        return rx.box()
    
    node_name = node.get("name", "Unknown")
    node_type = node.get("type", "file")
    node_path = node.get("path", "")
    issues = node.get("issues", [])
    
    return rx.box(
        rx.vstack(
            # Node header
            rx.hstack(
                rx.text(
                    format_node_type(node_type)["icon"],
                    font_size="1.5em"
                ),
                rx.vstack(
                    rx.heading(
                        node_name,
                        size="md",
                        color=COLORS["gray"]["900"],
                        margin="0"
                    ),
                    rx.text(
                        node_path,
                        color=COLORS["gray"]["600"],
                        font_family="mono",
                        size="sm",
                        margin="0"
                    ),
                    spacing="0",
                    align="start"
                ),
                spacing=SPACING["md"],
                align="center"
            ),
            
            # Issues list
            rx.cond(
                len(issues) > 0,
                rx.vstack(
                    rx.text(
                        f"Issues ({len(issues)}):",
                        font_weight="600",
                        color=COLORS["gray"]["700"]
                    ),
                    
                    rx.vstack(
                        *[
                            _create_issue_item(issue)
                            for issue in issues[:5]  # Show first 5 issues
                        ],
                        spacing=SPACING["sm"],
                        width="100%"
                    ),
                    
                    rx.cond(
                        len(issues) > 5,
                        rx.text(
                            f"... and {len(issues) - 5} more issues",
                            color=COLORS["gray"]["500"],
                            size="sm",
                            font_style="italic"
                        )
                    ),
                    
                    spacing=SPACING["md"],
                    align="start",
                    width="100%"
                ),
                
                rx.text(
                    "No issues found",
                    color=COLORS["success"]["600"],
                    font_weight="500"
                )
            ),
            
            spacing=SPACING["lg"],
            align="start",
            width="100%"
        ),
        
        background="white",
        border=f"1px solid {COLORS['gray']['200']}",
        border_radius="8px",
        padding=SPACING["lg"],
        box_shadow="0 2px 4px rgba(0, 0, 0, 0.1)"
    )


def _create_issue_item(issue: Dict[str, Any]) -> rx.Component:
    """Create an issue item for the node details."""
    severity = issue.get("severity", "minor")
    severity_info = format_issue_severity(severity)
    
    return rx.hstack(
        rx.text(
            severity_info["icon"],
            font_size="1em"
        ),
        
        rx.vstack(
            rx.text(
                issue.get("message", "Unknown issue"),
                color=COLORS["gray"]["800"],
                font_weight="500",
                size="sm",
                margin="0"
            ),
            rx.text(
                f"Line {issue.get('line_number', 0)} • {issue.get('type', 'unknown').replace('_', ' ').title()}",
                color=COLORS["gray"]["600"],
                size="xs",
                margin="0"
            ),
            spacing="0",
            align="start",
            flex="1"
        ),
        
        rx.badge(
            severity_info["label"],
            color_scheme=severity_info["color"],
            size="sm"
        ),
        
        spacing=SPACING["sm"],
        align="start",
        width="100%",
        padding=SPACING["sm"],
        background=severity_info["bg_color"],
        border=f"1px solid {severity_info['border_color']}",
        border_radius="6px"
    )
