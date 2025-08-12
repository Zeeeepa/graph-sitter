"""
Dead Code Display Component

Shows unused functions, classes, and imports.
"""

import reflex as rx
from typing import Dict, List, Any
from ..state.app_state import AppState


def dead_code_panel() -> rx.Component:
    """Dead code analysis panel."""
    return rx.box(
        rx.vstack(
            # Panel header
            rx.hstack(
                rx.heading("💀 Dead Code", size="5"),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=16),
                    variant="ghost",
                    size="2",
                    on_click=AppState.toggle_dead_code_panel
                ),
                width="100%",
                align="center"
            ),
            
            # Dead code categories
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger(
                        f"Functions ({len(AppState.dead_code_functions)})",
                        value="functions"
                    ),
                    rx.tabs.trigger(
                        f"Classes ({len(AppState.dead_code_classes)})",
                        value="classes"
                    ),
                    rx.tabs.trigger(
                        f"Imports ({len(AppState.dead_code_imports)})",
                        value="imports"
                    ),
                ),
                
                rx.tabs.content(
                    dead_code_list(AppState.dead_code_functions, "function"),
                    value="functions"
                ),
                
                rx.tabs.content(
                    dead_code_list(AppState.dead_code_classes, "class"),
                    value="classes"
                ),
                
                rx.tabs.content(
                    dead_code_list(AppState.dead_code_imports, "import"),
                    value="imports"
                ),
                
                default_value="functions",
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


def dead_code_list(items: List[Dict[str, Any]], item_type: str) -> rx.Component:
    """List of dead code items."""
    return rx.box(
        rx.cond(
            len(items) > 0,
            rx.vstack(
                rx.foreach(
                    items,
                    lambda item: dead_code_item(item, item_type)
                ),
                spacing="2",
                width="100%"
            ),
            rx.center(
                rx.vstack(
                    rx.icon("check_circle", size=32, color="var(--green-9)"),
                    rx.text(
                        f"No unused {item_type}s found",
                        size="3",
                        color="var(--green-11)",
                        weight="medium"
                    ),
                    rx.text(
                        "Great! Your code is clean.",
                        size="2",
                        color="var(--gray-10)"
                    ),
                    spacing="2",
                    align="center"
                ),
                height="150px"
            )
        ),
        max_height="300px",
        overflow_y="auto",
        width="100%"
    )


def dead_code_item(item: Dict[str, Any], item_type: str) -> rx.Component:
    """Individual dead code item."""
    return rx.box(
        rx.vstack(
            # Item header
            rx.hstack(
                # Type icon
                rx.text(
                    "⚡" if item_type == "function" else 
                    "🏗️" if item_type == "class" else "📦",
                    size="4"
                ),
                
                # Item name
                rx.text(
                    item.get("name", "Unknown"),
                    size="3",
                    weight="medium",
                    font_family="monospace"
                ),
                
                rx.spacer(),
                
                # Location
                rx.text(
                    f"Line {item.get('line_number', 0)}",
                    size="2",
                    color="var(--gray-10)"
                ),
                
                width="100%",
                align="center"
            ),
            
            # File path
            rx.text(
                item.get("file_path", "unknown"),
                size="2",
                color="var(--gray-9)",
                font_family="monospace"
            ),
            
            # Reason
            rx.text(
                item.get("reason", "No reason provided"),
                size="2",
                color="var(--gray-11)",
                font_style="italic"
            ),
            
            spacing="1",
            align="start",
            width="100%"
        ),
        
        padding="12px",
        border="1px solid var(--orange-6)",
        border_radius="6px",
        background="var(--orange-2)",
        width="100%"
    )
