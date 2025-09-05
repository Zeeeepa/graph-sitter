"""
Error Modal Component

Modal dialog for displaying error messages to users.
"""

import reflex as rx
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES


def error_modal() -> rx.Component:
    """Error modal component."""
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(
                    rx.hstack(
                        rx.icon(
                            tag="warning",
                            color=COLORS["error"]["600"],
                            size="lg"
                        ),
                        rx.heading(
                            "Error",
                            size="lg",
                            color=COLORS["error"]["700"]
                        ),
                        spacing=SPACING["sm"],
                        align="center"
                    )
                ),
                
                rx.modal_body(
                    rx.text(
                        AppState.error_message,
                        color=COLORS["gray"]["700"],
                        line_height="1.6"
                    )
                ),
                
                rx.modal_footer(
                    rx.hstack(
                        rx.button(
                            "Close",
                            on_click=AppState.close_error_modal,
                            style=COMPONENT_STYLES["button_primary"]
                        ),
                        spacing=SPACING["sm"]
                    )
                ),
                
                max_width="500px",
                background="white",
                border_radius="12px",
                box_shadow="0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"
            )
        ),
        
        is_open=AppState.show_error_modal,
        on_close=AppState.close_error_modal,
        size="md",
        is_centered=True
    )

