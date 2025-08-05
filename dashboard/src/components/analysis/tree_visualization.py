"""
Tree Visualization Component

Interactive tree component for navigating codebase structure with issue indicators,
expandable nodes, and visual styling for different node types.
"""

import reflex as rx
from typing import Dict, Any, List
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES
from ...utils.formatters import format_file_path, format_node_type, format_issue_severity
from ..common.tree_node import tree_node


class TreeState(rx.State):
    """State for tree visualization interactions."""
    
    search_query: str = ""
    show_only_issues: bool = False
    
    def update_search(self, query: str):
        """Update the search query."""
        self.search_query = query.lower()
    
    def toggle_issues_filter(self):
        """Toggle showing only nodes with issues."""
        self.show_only_issues = not self.show_only_issues
    
    def should_show_node(self, node: Dict[str, Any]) -> bool:
        """Determine if a node should be shown based on filters."""
        # Search filter
        if self.search_query:
            node_name = node.get("name", "").lower()
            node_path = node.get("path", "").lower()
            if self.search_query not in node_name and self.search_query not in node_path:
                # Check if any child matches
                if not self._has_matching_child(node, self.search_query):
                    return False
        
        # Issues filter
        if self.show_only_issues:
            if not node.get("issues", []) and not self._has_issues_in_children(node):
                return False
        
        return True
    
    def _has_matching_child(self, node: Dict[str, Any], query: str) -> bool:
        """Check if any child node matches the search query."""
        for child in node.get("children", []):
            child_name = child.get("name", "").lower()
            child_path = child.get("path", "").lower()
            if query in child_name or query in child_path:
                return True
            if self._has_matching_child(child, query):
                return True
        return False
    
    def _has_issues_in_children(self, node: Dict[str, Any]) -> bool:
        """Check if any child node has issues."""
        for child in node.get("children", []):
            if child.get("issues", []):
                return True
            if self._has_issues_in_children(child):
                return True
        return False


def tree_visualization() -> rx.Component:
    """Main tree visualization component."""
    return rx.vstack(
        # Tree controls
        rx.hstack(
            # Search bar
            rx.hstack(
                rx.icon(tag="search", size="sm", color=COLORS["gray"]["500"]),
                rx.input(
                    placeholder="Search files and folders...",
                    value=TreeState.search_query,
                    on_change=TreeState.update_search,
                    style=COMPONENT_STYLES["input"],
                    width="300px"
                ),
                spacing=SPACING["sm"],
                align="center"
            ),
            
            # Filter controls
            rx.hstack(
                rx.checkbox(
                    "Show only items with issues",
                    is_checked=TreeState.show_only_issues,
                    on_change=TreeState.toggle_issues_filter,
                    color_scheme="red"
                ),
                
                rx.button(
                    rx.icon(tag="refresh", size="sm"),
                    "Expand All",
                    style=COMPONENT_STYLES["button_secondary"],
                    size="sm"
                ),
                
                rx.button(
                    rx.icon(tag="minimize", size="sm"),
                    "Collapse All",
                    style=COMPONENT_STYLES["button_secondary"],
                    size="sm"
                ),
                
                spacing=SPACING["md"]
            ),
            
            justify="between",
            align="center",
            width="100%",
            margin_bottom=SPACING["lg"]
        ),
        
        # Tree structure
        rx.box(
            rx.cond(
                AppState.tree_data,
                _render_tree_node(AppState.tree_data, 0),
                rx.vstack(
                    rx.icon(
                        tag="folder",
                        size="3xl",
                        color=COLORS["gray"]["400"]
                    ),
                    rx.text(
                        "No tree data available",
                        color=COLORS["gray"]["500"],
                        size="lg"
                    ),
                    spacing=SPACING["md"],
                    align="center",
                    padding=SPACING["3xl"]
                )
            ),
            
            **COMPONENT_STYLES["card"],
            min_height="500px",
            overflow="auto"
        ),
        
        # Tree legend
        rx.box(
            rx.vstack(
                rx.text(
                    "Legend:",
                    font_weight="600",
                    color=COLORS["gray"]["700"],
                    margin_bottom=SPACING["sm"]
                ),
                
                rx.grid(
                    _create_legend_item("📁", "Folder", COLORS["blue"]["600"]),
                    _create_legend_item("📄", "File", COLORS["gray"]["600"]),
                    _create_legend_item("⚡", "Function", COLORS["green"]["600"]),
                    _create_legend_item("🏗️", "Class", COLORS["purple"]["600"]),
                    _create_legend_item("🚀", "Entry Point", COLORS["yellow"]["600"]),
                    _create_legend_item("⭐", "Important", COLORS["orange"]["600"]),
                    _create_legend_item("💀", "Dead Code", COLORS["red"]["600"]),
                    _create_legend_item("⚠️", "Critical Issue", COLORS["error"]["600"]),
                    _create_legend_item("👉", "Major Issue", COLORS["warning"]["600"]),
                    _create_legend_item("🔍", "Minor Issue", COLORS["warning"]["500"]),
                    
                    columns=[2, 3, 5],
                    spacing=SPACING["sm"],
                    width="100%"
                ),
                
                spacing=SPACING["sm"],
                align="start"
            ),
            
            **COMPONENT_STYLES["card"],
            background=COLORS["gray"]["50"],
            margin_top=SPACING["lg"]
        ),
        
        spacing="0",
        width="100%"
    )


def _render_tree_node(node: Dict[str, Any], depth: int) -> rx.Component:
    """Render a single tree node with its children."""
    node_path = node.get("path", "")
    has_children = bool(node.get("children", []))
    
    return rx.vstack(
        # Node itself
        tree_node(
            node=node,
            depth=depth,
            is_expanded=node_path in AppState.expanded_nodes,
            is_selected=node_path == AppState.selected_node,
            has_children=has_children,
            on_click=AppState.select_node,
            on_expand=AppState.toggle_node_expansion
        ),
        
        # Children (if expanded and has children)
        rx.cond(
            (node_path in AppState.expanded_nodes) and has_children,
            rx.vstack(
                *[
                    _render_tree_node(child, depth + 1)
                    for child in node.get("children", [])
                ],
                spacing="0",
                width="100%"
            )
        ),
        
        spacing="0",
        width="100%"
    )


def _create_legend_item(icon: str, label: str, color: str) -> rx.Component:
    """Create a legend item."""
    return rx.hstack(
        rx.text(icon, font_size="1em"),
        rx.text(
            label,
            color=color,
            size="sm",
            font_weight="500"
        ),
        spacing=SPACING["xs"],
        align="center"
    )


def _get_all_node_paths(node: Dict[str, Any]) -> List[str]:
    """Get all node paths for expand all functionality."""
    paths = []
    if node.get("path"):
        paths.append(node["path"])
    
    for child in node.get("children", []):
        paths.extend(_get_all_node_paths(child))
    
    return paths
