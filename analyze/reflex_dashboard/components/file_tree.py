"""
File tree component for codebase navigation.

This module provides an interactive file tree that integrates with graph-sitter
to display and navigate codebase structure.
"""

import reflex as rx
from typing import List, Dict, Any
from ..state.codebase_state import CodebaseState


def create_file_tree() -> rx.Component:
    """Create the main file tree component."""
    return rx.vstack(
        # File tree header
        rx.hstack(
            rx.heading("File Explorer", size="md"),
            rx.spacer(),
            rx.button(
                rx.icon("refresh-cw", size=16),
                on_click=CodebaseState.refresh_file_tree,
                variant="ghost",
                size="sm"
            ),
            width="100%",
            align_items="center"
        ),
        
        # Search bar
        rx.input(
            placeholder="Search files...",
            value=CodebaseState.file_search_query,
            on_change=CodebaseState.set_file_search_query,
            width="100%"
        ),
        
        # File filters
        rx.hstack(
            rx.checkbox(
                "Python",
                checked=CodebaseState.show_python_files,
                on_change=CodebaseState.toggle_python_files
            ),
            rx.checkbox(
                "TypeScript",
                checked=CodebaseState.show_typescript_files,
                on_change=CodebaseState.toggle_typescript_files
            ),
            rx.checkbox(
                "Other",
                checked=CodebaseState.show_other_files,
                on_change=CodebaseState.toggle_other_files
            ),
            spacing="3",
            width="100%"
        ),
        
        rx.divider(),
        
        # File tree content
        rx.cond(
            CodebaseState.file_tree_loading,
            rx.vstack(
                rx.spinner(size="lg"),
                rx.text("Loading file tree...", color="gray.500"),
                spacing="3",
                align_items="center",
                padding="2rem"
            ),
            rx.cond(
                CodebaseState.filtered_file_tree,
                rx.vstack(
                    rx.foreach(
                        CodebaseState.filtered_file_tree,
                        create_file_tree_node
                    ),
                    spacing="1",
                    width="100%",
                    align_items="start"
                ),
                rx.vstack(
                    rx.icon("folder-x", size=32, color="gray.400"),
                    rx.text("No files found", color="gray.500"),
                    spacing="2",
                    align_items="center",
                    padding="2rem"
                )
            )
        ),
        
        spacing="3",
        width="100%",
        height="100%",
        align_items="start"
    )


def create_file_tree_node(node: Dict[str, Any]) -> rx.Component:
    """Create a file tree node (file or directory)."""
    return rx.cond(
        node["is_directory"],
        create_directory_node(node),
        create_file_node(node)
    )


def create_directory_node(node: Dict[str, Any]) -> rx.Component:
    """Create a directory node in the file tree."""
    return rx.vstack(
        # Directory header
        rx.button(
            rx.hstack(
                rx.icon(
                    "chevron-right" if not node.get("expanded", False) else "chevron-down",
                    size=16,
                    color="gray.500"
                ),
                rx.icon("folder", size=16, color="blue.500"),
                rx.text(node["name"], size="sm"),
                rx.spacer(),
                rx.badge(
                    str(node.get("file_count", 0)),
                    variant="soft",
                    color_scheme="blue",
                    size="sm"
                ),
                spacing="2",
                align_items="center",
                width="100%"
            ),
            on_click=lambda: CodebaseState.toggle_directory(node["path"]),
            variant="ghost",
            justify="start",
            width="100%",
            padding="0.25rem"
        ),
        
        # Directory children (if expanded)
        rx.cond(
            node.get("expanded", False) & (len(node.get("children", [])) > 0),
            rx.vstack(
                rx.foreach(
                    node["children"],
                    create_file_tree_node
                ),
                spacing="1",
                width="100%",
                padding_left="1rem",
                align_items="start"
            )
        ),
        
        spacing="0",
        width="100%",
        align_items="start"
    )


def create_file_node(node: Dict[str, Any]) -> rx.Component:
    """Create a file node in the file tree."""
    # Determine file icon and color based on extension
    file_icon, icon_color = get_file_icon_and_color(node.get("extension", ""))
    
    return rx.button(
        rx.hstack(
            rx.icon(file_icon, size=16, color=icon_color),
            rx.text(node["name"], size="sm"),
            rx.spacer(),
            # Show error/warning indicators if available
            rx.cond(
                node.get("error_count", 0) > 0,
                rx.badge(
                    str(node["error_count"]),
                    variant="soft",
                    color_scheme="red",
                    size="sm"
                )
            ),
            rx.cond(
                node.get("warning_count", 0) > 0,
                rx.badge(
                    str(node["warning_count"]),
                    variant="soft",
                    color_scheme="yellow",
                    size="sm"
                )
            ),
            spacing="2",
            align_items="center",
            width="100%"
        ),
        on_click=lambda: CodebaseState.select_file(node["path"]),
        variant="ghost" if CodebaseState.selected_file_path != node["path"] else "soft",
        color_scheme="blue" if CodebaseState.selected_file_path == node["path"] else "gray",
        justify="start",
        width="100%",
        padding="0.25rem"
    )


def get_file_icon_and_color(extension: str) -> tuple[str, str]:
    """Get appropriate icon and color for file extension."""
    icon_map = {
        ".py": ("file-code", "green.500"),
        ".ts": ("file-code", "blue.500"),
        ".tsx": ("file-code", "blue.600"),
        ".js": ("file-code", "yellow.500"),
        ".jsx": ("file-code", "yellow.600"),
        ".json": ("file-text", "orange.500"),
        ".md": ("file-text", "gray.600"),
        ".txt": ("file-text", "gray.500"),
        ".yml": ("file-text", "purple.500"),
        ".yaml": ("file-text", "purple.500"),
        ".toml": ("file-text", "brown.500"),
        ".cfg": ("settings", "gray.500"),
        ".ini": ("settings", "gray.500"),
    }
    
    return icon_map.get(extension.lower(), ("file", "gray.400"))


def create_file_details_panel() -> rx.Component:
    """Create a panel showing details of the selected file."""
    return rx.cond(
        CodebaseState.selected_file_path != "",
        rx.card(
            rx.vstack(
                # File header
                rx.hstack(
                    rx.icon("file", size=20, color="blue.500"),
                    rx.heading(CodebaseState.selected_file_name, size="md"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("x", size=16),
                        on_click=CodebaseState.clear_file_selection,
                        variant="ghost",
                        size="sm"
                    ),
                    width="100%",
                    align_items="center"
                ),
                
                rx.divider(),
                
                # File info
                rx.vstack(
                    rx.hstack(
                        rx.text("Path:", weight="medium", size="sm"),
                        rx.text(CodebaseState.selected_file_path, size="sm", color="gray.600"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.text("Size:", weight="medium", size="sm"),
                        rx.text(f"{CodebaseState.selected_file_size} bytes", size="sm", color="gray.600"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.text("Lines:", weight="medium", size="sm"),
                        rx.text(str(CodebaseState.selected_file_lines), size="sm", color="gray.600"),
                        spacing="2"
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%"
                ),
                
                # File actions
                rx.hstack(
                    rx.button(
                        rx.icon("eye", size=16),
                        "View",
                        on_click=CodebaseState.view_file_content,
                        variant="outline",
                        size="sm"
                    ),
                    rx.button(
                        rx.icon("search", size=16),
                        "Analyze",
                        on_click=CodebaseState.analyze_file,
                        variant="outline",
                        size="sm"
                    ),
                    spacing="2",
                    width="100%"
                ),
                
                spacing="3",
                align_items="start",
                width="100%"
            ),
            width="100%"
        )
    )


def create_file_content_viewer() -> rx.Component:
    """Create a file content viewer."""
    return rx.cond(
        CodebaseState.file_content_visible,
        rx.card(
            rx.vstack(
                # Content header
                rx.hstack(
                    rx.heading("File Content", size="md"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("x", size=16),
                        on_click=CodebaseState.hide_file_content,
                        variant="ghost",
                        size="sm"
                    ),
                    width="100%",
                    align_items="center"
                ),
                
                rx.divider(),
                
                # Content area
                rx.cond(
                    CodebaseState.file_content_loading,
                    rx.vstack(
                        rx.spinner(),
                        rx.text("Loading file content...", color="gray.500"),
                        spacing="2",
                        align_items="center",
                        padding="2rem"
                    ),
                    rx.code_block(
                        CodebaseState.file_content,
                        language=CodebaseState.selected_file_language,
                        width="100%",
                        max_height="400px",
                        overflow="auto"
                    )
                ),
                
                spacing="3",
                width="100%",
                align_items="start"
            ),
            width="100%"
        )
    )
