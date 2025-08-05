"""
Repository Input Component

Input form for entering repository URL and starting analysis.
"""

import reflex as rx
from ...state.app_state import AppState
from ...styles.theme import COLORS, SPACING, COMPONENT_STYLES
from ..common.loading_spinner import inline_loading


class RepositoryInputState(rx.State):
    """State for repository input form."""
    
    repo_url_input: str = ""
    
    def update_repo_url(self, value: str):
        """Update the repository URL input."""
        self.repo_url_input = value
    
    def set_example_repo(self):
        """Set example repository URL."""
        self.repo_url_input = "https://github.com/Zeeeepa/graph-sitter"
    
    def set_local_project(self):
        """Set local project path."""
        self.repo_url_input = "./local-project"
    
    async def submit_analysis(self):
        """Submit the analysis request."""
        if self.repo_url_input.strip():
            await AppState.start_analysis(self.repo_url_input.strip())


def repository_input() -> rx.Component:
    """Repository input form component."""
    return rx.box(
        rx.vstack(
            # Title and description
            rx.vstack(
                rx.heading(
                    "Analyze Your Codebase",
                    size="xl",
                    color=COLORS["gray"]["900"],
                    text_align="center"
                ),
                rx.text(
                    "Enter a GitHub repository URL or local path to start comprehensive analysis",
                    color=COLORS["gray"]["600"],
                    text_align="center",
                    max_width="600px"
                ),
                spacing=SPACING["sm"],
                align="center"
            ),
            
            # Input form
            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder="https://github.com/owner/repository or /path/to/local/repo",
                        value=RepositoryInputState.repo_url_input,
                        on_change=RepositoryInputState.update_repo_url,
                        style=COMPONENT_STYLES["input"],
                        width="500px",
                        size="lg",
                        disabled=AppState.loading
                    ),
                    
                    rx.button(
                        rx.cond(
                            AppState.loading,
                            inline_loading("Analyzing..."),
                            rx.hstack(
                                rx.icon(tag="search", size="sm"),
                                "Analyze",
                                spacing=SPACING["sm"],
                                align="center"
                            )
                        ),
                        on_click=RepositoryInputState.submit_analysis,
                        style=COMPONENT_STYLES["button_primary"],
                        size="lg",
                        disabled=AppState.loading,
                        min_width="120px"
                    ),
                    
                    spacing=SPACING["md"],
                    align="center"
                ),
                
                # Example URLs
                rx.vstack(
                    rx.text(
                        "Examples:",
                        color=COLORS["gray"]["500"],
                        size="sm",
                        font_weight="500"
                    ),
                    rx.hstack(
                        rx.button(
                            "https://github.com/Zeeeepa/graph-sitter",
                            on_click=RepositoryInputState.set_example_repo,
                            variant="ghost",
                            size="sm",
                            color=COLORS["primary"]["600"],
                            _hover={"background": COLORS["primary"]["50"]}
                        ),
                        rx.button(
                            "./local-project",
                            on_click=RepositoryInputState.set_local_project,
                            variant="ghost",
                            size="sm",
                            color=COLORS["primary"]["600"],
                            _hover={"background": COLORS["primary"]["50"]}
                        ),
                        spacing=SPACING["sm"],
                        wrap="wrap",
                        justify="center"
                    ),
                    spacing=SPACING["xs"],
                    align="center"
                ),
                
                spacing=SPACING["lg"],
                align="center",
                width="100%"
            ),
            
            # Features preview
            rx.vstack(
                rx.text(
                    "What you'll get:",
                    color=COLORS["gray"]["700"],
                    font_weight="600",
                    size="lg"
                ),
                rx.grid(
                    # Feature 1
                    rx.vstack(
                        rx.icon(
                            tag="tree",
                            size="2xl",
                            color=COLORS["primary"]["600"]
                        ),
                        rx.text(
                            "Interactive Tree",
                            font_weight="600",
                            color=COLORS["gray"]["900"]
                        ),
                        rx.text(
                            "Navigate your codebase structure with visual indicators",
                            color=COLORS["gray"]["600"],
                            text_align="center",
                            size="sm"
                        ),
                        spacing=SPACING["sm"],
                        align="center",
                        text_align="center"
                    ),
                    
                    # Feature 2
                    rx.vstack(
                        rx.icon(
                            tag="bug",
                            size="2xl",
                            color=COLORS["warning"]["600"]
                        ),
                        rx.text(
                            "Issue Detection",
                            font_weight="600",
                            color=COLORS["gray"]["900"]
                        ),
                        rx.text(
                            "Find type annotations, unused code, and complexity issues",
                            color=COLORS["gray"]["600"],
                            text_align="center",
                            size="sm"
                        ),
                        spacing=SPACING["sm"],
                        align="center",
                        text_align="center"
                    ),
                    
                    # Feature 3
                    rx.vstack(
                        rx.icon(
                            tag="trash",
                            size="2xl",
                            color=COLORS["error"]["600"]
                        ),
                        rx.text(
                            "Dead Code Analysis",
                            font_weight="600",
                            color=COLORS["gray"]["900"]
                        ),
                        rx.text(
                            "Identify unused functions, classes, and imports",
                            color=COLORS["gray"]["600"],
                            text_align="center",
                            size="sm"
                        ),
                        spacing=SPACING["sm"],
                        align="center",
                        text_align="center"
                    ),
                    
                    # Feature 4
                    rx.vstack(
                        rx.icon(
                            tag="star",
                            size="2xl",
                            color=COLORS["success"]["600"]
                        ),
                        rx.text(
                            "Important Functions",
                            font_weight="600",
                            color=COLORS["gray"]["900"]
                        ),
                        rx.text(
                            "Discover entry points and frequently called functions",
                            color=COLORS["gray"]["600"],
                            text_align="center",
                            size="sm"
                        ),
                        spacing=SPACING["sm"],
                        align="center",
                        text_align="center"
                    ),
                    
                    columns=[1, 2, 4],
                    spacing=SPACING["xl"],
                    width="100%"
                ),
                
                spacing=SPACING["xl"],
                align="center",
                width="100%"
            ),
            
            spacing=SPACING["2xl"],
            align="center",
            width="100%",
            max_width="1200px",
            margin="0 auto"
        ),
        
        padding=SPACING["3xl"],
        min_height="80vh",
        display="flex",
        align_items="center",
        justify_content="center"
    )
