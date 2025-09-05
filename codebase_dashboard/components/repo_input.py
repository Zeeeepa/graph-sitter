"""
Repository Input Component

Provides the interface for entering repository URLs and triggering analysis.
"""

import reflex as rx
from ..state.app_state import AppState, AnalysisStatus


def repo_input_section() -> rx.Component:
    """Repository input section with URL field and analyze button."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "🔍 Repository Analysis",
                size="6",
                margin_bottom="1rem"
            ),
            
            rx.text(
                "Enter a GitHub repository URL or local path to analyze the codebase structure, "
                "detect issues, find dead code, and identify important functions.",
                size="3",
                color="var(--gray-11)",
                margin_bottom="1.5rem"
            ),
            
            rx.hstack(
                rx.input(
                    placeholder="https://github.com/owner/repository or /path/to/local/repo",
                    value=AppState.repo_url,
                    on_change=AppState.set_repo_url,
                    size="3",
                    width="100%",
                    max_width="600px",
                    disabled=AppState.analysis_status == AnalysisStatus.ANALYZING.value
                ),
                
                rx.button(
                    rx.cond(
                        AppState.analysis_status == AnalysisStatus.ANALYZING.value,
                        rx.hstack(
                            rx.spinner(size="4"),
                            "Analyzing...",
                            spacing="2"
                        ),
                        rx.hstack(
                            rx.icon("search", size=16),
                            "Analyze",
                            spacing="2"
                        )
                    ),
                    on_click=AppState.analyze_repository,
                    disabled=AppState.analysis_status == AnalysisStatus.ANALYZING.value,
                    size="3",
                    color_scheme="blue"
                ),
                
                spacing="3",
                width="100%",
                align="center"
            ),
            
            # Example repositories
            rx.cond(
                AppState.analysis_status == AnalysisStatus.IDLE.value,
                rx.vstack(
                    rx.text(
                        "💡 Try these example repositories:",
                        size="2",
                        color="var(--gray-10)",
                        margin_top="1rem"
                    ),
                    
                    rx.hstack(
                        example_repo_button(
                            "https://github.com/Zeeeepa/graph-sitter",
                            "Graph-sitter (Python)"
                        ),
                        example_repo_button(
                            "https://github.com/reflex-dev/reflex",
                            "Reflex (Python)"
                        ),
                        example_repo_button(
                            "https://github.com/microsoft/vscode",
                            "VS Code (TypeScript)"
                        ),
                        spacing="2",
                        wrap="wrap"
                    ),
                    
                    spacing="2",
                    align="center"
                )
            ),
            
            spacing="4",
            align="center",
            width="100%"
        ),
        
        padding="2rem",
        border="1px solid var(--gray-6)",
        border_radius="12px",
        background="white",
        width="100%"
    )


def example_repo_button(url: str, label: str) -> rx.Component:
    """Create an example repository button."""
    return rx.button(
        label,
        variant="ghost",
        size="2",
        color_scheme="gray",
        on_click=lambda: AppState.set_repo_url(url)
    )


def analysis_summary() -> rx.Component:
    """Display analysis summary when completed."""
    return rx.cond(
        AppState.analysis_status == AnalysisStatus.COMPLETED.value,
        rx.box(
            rx.hstack(
                rx.icon("check_circle", size=20, color="var(--green-9)"),
                rx.vstack(
                    rx.text(
                        "Analysis completed successfully!",
                        size="4",
                        weight="medium",
                        color="var(--green-11)"
                    ),
                    rx.text(
                        f"Duration: {AppState.analysis_duration:.1f}s | "
                        f"Files: {AppState.codebase_stats['total_files']} | "
                        f"Functions: {AppState.codebase_stats['total_functions']} | "
                        f"Issues: {AppState.total_issues}",
                        size="2",
                        color="var(--gray-11)"
                    ),
                    spacing="1",
                    align="start"
                ),
                spacing="3",
                align="center"
            ),
            padding="1rem",
            border="1px solid var(--green-6)",
            border_radius="8px",
            background="var(--green-2)",
            margin_top="1rem"
        )
    )
