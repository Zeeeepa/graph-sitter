"""
Important Functions Display Component

Shows entry points, most called functions, and other important code elements.
"""

import reflex as rx
from typing import Dict, List, Any
from ..state.app_state import AppState


def important_functions_panel() -> rx.Component:
    """Important functions analysis panel."""
    return rx.box(
        rx.vstack(
            # Panel header
            rx.hstack(
                rx.heading("⭐ Important Functions", size="5"),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=16),
                    variant="ghost",
                    size="2",
                    on_click=AppState.toggle_important_functions_panel
                ),
                width="100%",
                align="center"
            ),
            
            # Function categories
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger(
                        f"Entry Points ({len(AppState.entry_points)})",
                        value="entry_points"
                    ),
                    rx.tabs.trigger(
                        f"Most Called ({len(AppState.most_called_functions)})",
                        value="most_called"
                    ),
                    rx.tabs.trigger(
                        f"Complex ({len(AppState.important_functions)})",
                        value="complex"
                    ),
                    rx.tabs.trigger(
                        f"Recursive ({len(AppState.recursive_functions)})",
                        value="recursive"
                    ),
                ),
                
                rx.tabs.content(
                    important_functions_list(AppState.entry_points, "entry_point"),
                    value="entry_points"
                ),
                
                rx.tabs.content(
                    important_functions_list(AppState.most_called_functions, "most_called"),
                    value="most_called"
                ),
                
                rx.tabs.content(
                    important_functions_list(AppState.important_functions, "complex"),
                    value="complex"
                ),
                
                rx.tabs.content(
                    important_functions_list(AppState.recursive_functions, "recursive"),
                    value="recursive"
                ),
                
                default_value="entry_points",
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


def important_functions_list(items: List[Dict[str, Any]], category: str) -> rx.Component:
    """List of important functions."""
    return rx.box(
        rx.cond(
            len(items) > 0,
            rx.vstack(
                rx.foreach(
                    items,
                    lambda item: important_function_item(item, category)
                ),
                spacing="2",
                width="100%"
            ),
            rx.center(
                rx.vstack(
                    rx.icon("info", size=32, color="var(--blue-9)"),
                    rx.text(
                        f"No {category.replace('_', ' ')} found",
                        size="3",
                        color="var(--blue-11)",
                        weight="medium"
                    ),
                    rx.text(
                        get_empty_message(category),
                        size="2",
                        color="var(--gray-10)",
                        text_align="center"
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


def important_function_item(item: Dict[str, Any], category: str) -> rx.Component:
    """Individual important function item."""
    return rx.box(
        rx.vstack(
            # Function header
            rx.hstack(
                # Category icon
                rx.text(
                    get_category_icon(category),
                    size="4"
                ),
                
                # Function name
                rx.text(
                    item.get("name", "Unknown"),
                    size="3",
                    weight="medium",
                    font_family="monospace"
                ),
                
                rx.spacer(),
                
                # Metrics
                rx.hstack(
                    rx.cond(
                        item.get("call_count"),
                        rx.badge(
                            f"{item['call_count']} calls",
                            variant="soft",
                            color_scheme="blue",
                            size="1"
                        )
                    ),
                    rx.cond(
                        item.get("outgoing_calls"),
                        rx.badge(
                            f"{item['outgoing_calls']} out",
                            variant="soft",
                            color_scheme="green",
                            size="1"
                        )
                    ),
                    spacing="1"
                ),
                
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
            
            # Reason/description
            rx.text(
                item.get("reason", "No description provided"),
                size="2",
                color="var(--gray-11)",
                font_style="italic"
            ),
            
            spacing="1",
            align="start",
            width="100%"
        ),
        
        padding="12px",
        border=f"1px solid var(--{get_category_color(category)}-6)",
        border_radius="6px",
        background=f"var(--{get_category_color(category)}-2)",
        width="100%"
    )


def get_category_icon(category: str) -> str:
    """Get icon for function category."""
    icons = {
        "entry_point": "🚀",
        "most_called": "📞",
        "complex": "🔧",
        "recursive": "🔄"
    }
    return icons.get(category, "⚡")


def get_category_color(category: str) -> str:
    """Get color scheme for function category."""
    colors = {
        "entry_point": "yellow",
        "most_called": "blue",
        "complex": "orange",
        "recursive": "purple"
    }
    return colors.get(category, "gray")


def get_empty_message(category: str) -> str:
    """Get empty state message for category."""
    messages = {
        "entry_point": "No main entry points detected in the codebase.",
        "most_called": "No frequently called functions found.",
        "complex": "No complex functions detected.",
        "recursive": "No recursive functions found."
    }
    return messages.get(category, "No functions found in this category.")
