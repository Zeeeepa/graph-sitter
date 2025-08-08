"""
Footer Component

Bottom footer with links and information.
"""

import reflex as rx
from ...styles.theme import COLORS, SPACING


def footer() -> rx.Component:
    """Main footer component."""
    return rx.box(
        rx.hstack(
            # Left side - Copyright and info
            rx.hstack(
                rx.text(
                    "© 2024 Codebase Analysis Dashboard",
                    color=COLORS["gray"]["600"],
                    size="sm"
                ),
                rx.text(
                    "•",
                    color=COLORS["gray"]["400"],
                    size="sm"
                ),
                rx.text(
                    "Built with Reflex & graph-sitter",
                    color=COLORS["gray"]["600"],
                    size="sm"
                ),
                spacing=SPACING["sm"],
                align="center"
            ),
            
            # Right side - Links
            rx.hstack(
                rx.link(
                    "Documentation",
                    href="https://graph-sitter.com",
                    color=COLORS["primary"]["600"],
                    size="sm",
                    _hover={"color": COLORS["primary"]["700"]}
                ),
                rx.text(
                    "•",
                    color=COLORS["gray"]["400"],
                    size="sm"
                ),
                rx.link(
                    "GitHub",
                    href="https://github.com/Zeeeepa/graph-sitter",
                    color=COLORS["primary"]["600"],
                    size="sm",
                    _hover={"color": COLORS["primary"]["700"]}
                ),
                rx.text(
                    "•",
                    color=COLORS["gray"]["400"],
                    size="sm"
                ),
                rx.link(
                    "Reflex",
                    href="https://reflex.dev",
                    color=COLORS["primary"]["600"],
                    size="sm",
                    _hover={"color": COLORS["primary"]["700"]}
                ),
                spacing=SPACING["sm"],
                align="center"
            ),
            
            justify="between",
            align="center",
            width="100%"
        ),
        
        background="white",
        border_top=f"1px solid {COLORS['gray']['200']}",
        padding=f"{SPACING['lg']} {SPACING['xl']}",
        margin_top="auto"
    )

