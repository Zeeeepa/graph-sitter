"""
Codebase Analysis Dashboard Demo

A working Reflex application demonstrating the dashboard functionality.
"""

import reflex as rx

class State(rx.State):
    """Application state."""
    
    # Repository input
    repo_url: str = ""
    
    # Analysis state
    analyzing: bool = False
    progress: int = 0
    message: str = ""
    
    # Results
    show_results: bool = False
    
    def analyze_repo(self):
        """Start repository analysis."""
        if not self.repo_url:
            return
            
        self.analyzing = True
        self.progress = 0
        self.message = "Starting analysis..."
        
        # Simulate progress
        return self.simulate_progress()
    
    def simulate_progress(self):
        """Simulate analysis progress."""
        steps = [
            "Cloning repository...",
            "Parsing files...", 
            "Analyzing structure...",
            "Detecting issues...",
            "Complete!"
        ]
        
        for i, step in enumerate(steps):
            self.message = step
            self.progress = int((i + 1) / len(steps) * 100)
            yield
            
        self.analyzing = False
        self.show_results = True

def index():
    """Main page."""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("🔍 Codebase Analysis Dashboard", size="2xl", margin_bottom="2rem"),
            
            # Input section
            rx.vstack(
                rx.heading("Repository Analysis", size="lg"),
                rx.text("Enter a repository URL to analyze:", color="gray.600"),
                rx.hstack(
                    rx.input(
                        placeholder="https://github.com/owner/repo",
                        value=State.repo_url,
                        on_change=State.set_repo_url,
                        width="400px"
                    ),
                    rx.button(
                        "Analyze",
                        on_click=State.analyze_repo,
                        disabled=State.analyzing,
                        color_scheme="blue"
                    ),
                    spacing="1rem"
                ),
                spacing="1rem",
                align="start",
                width="100%"
            ),
            
            # Progress section
            rx.cond(
                State.analyzing,
                rx.vstack(
                    rx.heading("Analysis in Progress", size="lg"),
                    rx.text(State.message),
                    rx.progress(value=State.progress, width="400px"),
                    rx.text(f"{State.progress}% complete"),
                    spacing="1rem",
                    align="start"
                )
            ),
            
            # Results section
            rx.cond(
                State.show_results,
                rx.vstack(
                    rx.heading("Analysis Results", size="lg"),
                    rx.grid(
                        rx.stat(
                            rx.stat_label("Total Files"),
                            rx.stat_number("127"),
                            rx.stat_help_text("Python, JS, TS")
                        ),
                        rx.stat(
                            rx.stat_label("Issues Found"),
                            rx.stat_number("23"),
                            rx.stat_help_text("5 critical, 18 minor")
                        ),
                        rx.stat(
                            rx.stat_label("Dead Code"),
                            rx.stat_number("8"),
                            rx.stat_help_text("Unused functions")
                        ),
                        columns=3,
                        spacing="2rem"
                    ),
                    rx.divider(),
                    rx.heading("Sample Issues", size="md"),
                    rx.vstack(
                        rx.alert(
                            rx.alert_icon(),
                            rx.box(
                                rx.alert_title("Missing Type Annotation"),
                                rx.alert_description("Function 'process_data' missing type hints")
                            ),
                            status="warning"
                        ),
                        rx.alert(
                            rx.alert_icon(),
                            rx.box(
                                rx.alert_title("Unused Function"),
                                rx.alert_description("Function 'old_helper' is never called")
                            ),
                            status="error"
                        ),
                        spacing="1rem",
                        width="100%"
                    ),
                    spacing="2rem",
                    align="start",
                    width="100%"
                )
            ),
            
            spacing="3rem",
            align="start",
            width="100%"
        ),
        max_width="800px",
        padding="2rem"
    )

# Create app
app = rx.App()
app.add_page(index, route="/")
