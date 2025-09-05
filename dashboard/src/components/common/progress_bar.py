"""
Progress Bar Component

Animated progress bar for showing analysis progress.
"""

import reflex as rx
from ...styles.theme import COLORS, SPACING


def progress_bar(
    value: float,
    max_value: float = 100.0,
    show_percentage: bool = True,
    color: str = None,
    height: str = "8px"
) -> rx.Component:
    """
    Progress bar component.
    
    Args:
        value: Current progress value
        max_value: Maximum progress value
        show_percentage: Whether to show percentage text
        color: Progress bar color (defaults to primary)
        height: Height of the progress bar
    """
    if color is None:
        color = COLORS["primary"]["600"]
    
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    
    return rx.vstack(
        rx.cond(
            show_percentage,
            rx.hstack(
                rx.text(
                    "Progress",
                    color=COLORS["gray"]["700"],
                    font_weight="500",
                    size="sm"
                ),
                rx.text(
                    f"{percentage:.1f}%",
                    color=COLORS["gray"]["600"],
                    size="sm"
                ),
                justify="between",
                width="100%"
            )
        ),
        
        rx.box(
            rx.box(
                width=f"{percentage}%",
                height="100%",
                background=color,
                border_radius="inherit",
                transition="width 0.3s ease-in-out"
            ),
            
            width="100%",
            height=height,
            background=COLORS["gray"]["200"],
            border_radius="4px",
            overflow="hidden"
        ),
        
        spacing=SPACING["sm"],
        width="100%"
    )


def circular_progress(
    value: float,
    max_value: float = 100.0,
    size: str = "60px",
    thickness: str = "4px",
    color: str = None
) -> rx.Component:
    """
    Circular progress indicator.
    
    Args:
        value: Current progress value
        max_value: Maximum progress value
        size: Size of the circular progress
        thickness: Thickness of the progress ring
        color: Progress color (defaults to primary)
    """
    if color is None:
        color = COLORS["primary"]["600"]
    
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    
    return rx.circular_progress(
        rx.circular_progress_label(
            f"{percentage:.0f}%",
            color=COLORS["gray"]["700"],
            font_weight="600",
            font_size="12px"
        ),
        value=percentage,
        size=size,
        thickness=thickness,
        color=color,
        track_color=COLORS["gray"]["200"]
    )

