"""
Loading Spinner Component

Reusable loading spinner with customizable size and message.
"""

import reflex as rx
from ...styles.theme import COLORS, SPACING


def loading_spinner(
    message: str = "Loading...",
    size: str = "md",
    show_message: bool = True
) -> rx.Component:
    """
    Loading spinner component.
    
    Args:
        message: Loading message to display
        size: Size of spinner (sm, md, lg)
        show_message: Whether to show the message
    """
    size_map = {
        "sm": "16px",
        "md": "24px", 
        "lg": "32px"
    }
    
    spinner_size = size_map.get(size, "24px")
    
    return rx.vstack(
        rx.spinner(
            size=spinner_size,
            color=COLORS["primary"]["600"],
            thickness="3px"
        ),
        
        rx.cond(
            show_message,
            rx.text(
                message,
                color=COLORS["gray"]["600"],
                font_weight="500",
                text_align="center"
            )
        ),
        
        spacing=SPACING["md"],
        align="center",
        justify="center"
    )


def loading_overlay(message: str = "Loading...") -> rx.Component:
    """Full-screen loading overlay."""
    return rx.box(
        rx.vstack(
            loading_spinner(message, size="lg"),
            spacing=SPACING["lg"],
            align="center",
            justify="center",
            height="100%"
        ),
        
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        background="rgba(255, 255, 255, 0.8)",
        backdrop_filter="blur(4px)",
        z_index="9999",
        display="flex",
        align_items="center",
        justify_content="center"
    )


def inline_loading(message: str = "Loading...") -> rx.Component:
    """Inline loading indicator for smaller spaces."""
    return rx.hstack(
        rx.spinner(
            size="16px",
            color=COLORS["primary"]["600"],
            thickness="2px"
        ),
        rx.text(
            message,
            color=COLORS["gray"]["600"],
            size="sm"
        ),
        spacing=SPACING["sm"],
        align="center"
    )

