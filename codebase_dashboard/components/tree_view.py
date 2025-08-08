"""
Tree View Component

Interactive tree visualization showing codebase structure with issue indicators,
entry points, and dead code markers.
"""

import reflex as rx
from typing import Dict, List, Any
from ..state.app_state import AppState


def tree_view_section() -> rx.Component:
    """Main tree view section."""
    return rx.box(
        rx.cond(
            AppState.tree_data,
            rx.vstack(
                # Tree controls
                rx.hstack(
                    rx.button(
                        rx.icon("expand", size=14),
                        "Expand All",
                        variant="ghost",
                        size="2",
                        on_click=lambda: None  # TODO: Implement expand all
                    ),
                    rx.button(
                        rx.icon("collapse", size=14),
                        "Collapse All",
                        variant="ghost",
                        size="2",
                        on_click=lambda: None  # TODO: Implement collapse all
                    ),
                    spacing="2"
                ),
                
                # Tree structure
                rx.box(
                    rx.foreach(
                        AppState.tree_data,
                        lambda file_path, file_data: tree_node(file_path, file_data)
                    ),
                    width="100%"
                ),
                
                spacing="3",
                width="100%"
            ),
            
            # Empty state
            rx.center(
                rx.vstack(
                    rx.icon("folder", size=48, color="var(--gray-8)"),
                    rx.text(
                        "No codebase structure available",
                        size="4",
                        color="var(--gray-10)"
                    ),
                    rx.text(
                        "Run an analysis to see the codebase tree",
                        size="2",
                        color="var(--gray-9)"
                    ),
                    spacing="2",
                    align="center"
                ),
                height="200px"
            )
        ),
        width="100%"
    )


def tree_node(file_path: str, file_data: Dict[str, Any]) -> rx.Component:
    """Individual tree node component."""
    return rx.box(
        rx.hstack(
            # Expand/collapse button (if has children)
            rx.cond(
                len(file_data.get("children", [])) > 0,
                rx.button(
                    rx.cond(
                        file_path.is_in(AppState.expanded_nodes),
                        rx.icon("chevron_down", size=14),
                        rx.icon("chevron_right", size=14)
                    ),
                    variant="ghost",
                    size="1",
                    on_click=AppState.toggle_node_expansion(file_path)
                ),
                rx.box(width="24px")  # Spacer for alignment
            ),
            
            # File/folder icon with status indicators
            rx.hstack(
                # Base icon
                rx.cond(
                    file_data.get("type") == "folder",
                    rx.icon("folder", size=16, color="var(--blue-9)"),
                    rx.icon("file", size=16, color="var(--gray-9)")
                ),
                
                # Status indicators
                rx.cond(
                    file_data.get("is_entry_point", False),
                    rx.badge("EP", variant="soft", color_scheme="yellow", size="1")
                ),
                
                rx.cond(
                    file_data.get("is_important", False),
                    rx.badge("IMP", variant="soft", color_scheme="orange", size="1")
                ),
                
                rx.cond(
                    file_data.get("is_dead_code", False),
                    rx.badge("DEAD", variant="soft", color_scheme="red", size="1")
                ),
                
                spacing="1"
            ),
            
            # File name
            rx.text(
                file_data.get("name", "Unknown"),
                size="3",
                weight="medium" if file_data.get("is_entry_point") or file_data.get("is_important") else "normal",
                color="var(--yellow-11)" if file_data.get("is_entry_point") else 
                      "var(--orange-11)" if file_data.get("is_important") else
                      "var(--gray-11)"
            ),
            
            rx.spacer(),
            
            # Issue indicators
            issue_indicators(file_data.get("issue_counts", {})),
            
            # File metrics
            rx.text(
                f"{file_data.get('lines_of_code', 0)} LOC",
                size="1",
                color="var(--gray-9)"
            ),
            
            spacing="2",
            align="center",
            width="100%"
        ),
        
        # Children (if expanded)
        rx.cond(
            file_path.is_in(AppState.expanded_nodes) & (len(file_data.get("children", [])) > 0),
            rx.box(
                rx.foreach(
                    file_data.get("children", []),
                    lambda child_path, child_data: tree_node(child_path, child_data)
                ),
                margin_left="24px",
                border_left="1px solid var(--gray-6)",
                padding_left="12px"
            )
        ),
        
        padding="4px 8px",
        border_radius="4px",
        _hover={"background": "var(--gray-3)"},
        cursor="pointer",
        on_click=AppState.select_node(file_path),
        background="var(--blue-3)" if file_path == AppState.selected_node else "transparent",
        width="100%"
    )


def issue_indicators(issue_counts: Dict[str, int]) -> rx.Component:
    """Issue count indicators."""
    return rx.hstack(
        # Critical issues
        rx.cond(
            issue_counts.get("critical", 0) > 0,
            rx.badge(
                f"⚠️ {issue_counts['critical']}",
                variant="soft",
                color_scheme="red",
                size="1"
            )
        ),
        
        # Major issues
        rx.cond(
            issue_counts.get("major", 0) > 0,
            rx.badge(
                f"👉 {issue_counts['major']}",
                variant="soft",
                color_scheme="orange",
                size="1"
            )
        ),
        
        # Minor issues
        rx.cond(
            issue_counts.get("minor", 0) > 0,
            rx.badge(
                f"🔍 {issue_counts['minor']}",
                variant="soft",
                color_scheme="yellow",
                size="1"
            )
        ),
        
        spacing="1"
    )


def tree_legend() -> rx.Component:
    """Legend explaining tree indicators."""
    return rx.box(
        rx.heading("Legend", size="4", margin_bottom="0.5rem"),
        
        rx.vstack(
            rx.hstack(
                rx.badge("EP", variant="soft", color_scheme="yellow", size="1"),
                rx.text("Entry Point", size="2"),
                spacing="2",
                align="center"
            ),
            
            rx.hstack(
                rx.badge("IMP", variant="soft", color_scheme="orange", size="1"),
                rx.text("Important Function", size="2"),
                spacing="2",
                align="center"
            ),
            
            rx.hstack(
                rx.badge("DEAD", variant="soft", color_scheme="red", size="1"),
                rx.text("Dead Code", size="2"),
                spacing="2",
                align="center"
            ),
            
            rx.hstack(
                rx.text("⚠️", size="2"),
                rx.text("Critical Issues", size="2"),
                spacing="2",
                align="center"
            ),
            
            rx.hstack(
                rx.text("👉", size="2"),
                rx.text("Major Issues", size="2"),
                spacing="2",
                align="center"
            ),
            
            rx.hstack(
                rx.text("🔍", size="2"),
                rx.text("Minor Issues", size="2"),
                spacing="2",
                align="center"
            ),
            
            spacing="2",
            align="start"
        ),
        
        padding="1rem",
        border="1px solid var(--gray-6)",
        border_radius="8px",
        background="var(--gray-2)",
        margin_top="1rem"
    )
