#!/usr/bin/env python3
"""
Real Graph-Sitter Dashboard with Actual Codebase Analysis
This integrates the real codebase analyzer with the Reflex dashboard.
"""

import reflex as rx
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from real_codebase_analyzer import RealCodebaseAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    print("⚠️ Real analyzer not available")


class RealDashboardState(rx.State):
    """Real dashboard state with actual analysis integration."""
    
    # Codebase selection
    available_codebases: List[str] = []
    selected_codebase: str = ""
    selected_codebase_path: str = ""
    codebase_loaded: bool = False
    
    # Analysis state
    analysis_running: bool = False
    analysis_progress: float = 0.0
    analysis_status: str = "Ready"
    analysis_complete: bool = False
    
    # Real analysis results
    real_results: Dict[str, Any] = {}
    
    # Quick stats (real data)
    total_files: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_symbols: int = 0
    lines_of_code: int = 0
    functions_count: int = 0
    classes_count: int = 0
    imports_count: int = 0
    test_files: int = 0
    
    # Health metrics (real data)
    maintainability_index: float = 0.0
    technical_debt_score: int = 0
    test_coverage_estimate: float = 0.0
    health_status: str = "Unknown"
    
    # Complex symbols
    complex_symbols: List[Dict[str, Any]] = []
    
    # Messages
    success_message: str = ""
    error_message: str = ""
    
    # Current tab
    current_tab: str = "overview"
    
    def __init__(self, *args, **kwargs):
        """Initialize the real dashboard state."""
        super().__init__(*args, **kwargs)
        self.detect_available_codebases()
    
    def detect_available_codebases(self):
        """Detect available codebases."""
        codebases = []
        
        # Current directory
        current_dir = Path.cwd()
        
        # Look for Graph-Sitter root
        if current_dir.name == "reflex_dashboard":
            graph_sitter_root = current_dir.parent.parent
            if (graph_sitter_root / "src" / "graph_sitter").exists():
                codebases.append("Graph-Sitter Core")
                self.selected_codebase_path = str(graph_sitter_root)
        else:
            codebases.append("Current Directory")
            self.selected_codebase_path = str(current_dir)
        
        self.available_codebases = codebases
        if codebases:
            self.selected_codebase = codebases[0]
    
    def select_codebase(self, codebase: str):
        """Select a codebase."""
        self.selected_codebase = codebase
        self.codebase_loaded = False
        self.analysis_complete = False
        self.clear_messages()
    
    def load_codebase(self):
        """Load the selected codebase."""
        if not self.selected_codebase:
            self.set_error("No codebase selected")
            return
        
        try:
            # Verify path exists
            path = Path(self.selected_codebase_path)
            if not path.exists():
                self.set_error(f"Path does not exist: {self.selected_codebase_path}")
                return
            
            self.codebase_loaded = True
            self.set_success(f"Loaded codebase: {self.selected_codebase}")
            
        except Exception as e:
            self.set_error(f"Failed to load codebase: {str(e)}")
    
    async def run_real_analysis(self):
        """Run real analysis on the loaded codebase."""
        if not self.codebase_loaded:
            self.set_error("No codebase loaded")
            return
        
        if not ANALYZER_AVAILABLE:
            self.set_error("Real analyzer not available")
            return
        
        self.analysis_running = True
        self.analysis_progress = 0.0
        self.analysis_status = "Initializing real analysis..."
        self.clear_messages()
        
        try:
            # Create real analyzer
            analyzer = RealCodebaseAnalyzer(self.selected_codebase_path)
            
            # Update progress during analysis
            self.analysis_status = "Scanning files..."
            self.analysis_progress = 10.0
            await asyncio.sleep(0.1)
            
            # Run the real analysis
            self.analysis_status = "Running comprehensive analysis..."
            self.analysis_progress = 20.0
            
            # This runs the actual analysis
            results = await analyzer.run_full_analysis()
            
            # Store real results
            self.real_results = results
            
            # Update stats with real data
            metrics = results.get('metrics', {})
            health = results.get('health', {})
            
            self.total_files = metrics.get('files', {}).get('python', 0) + metrics.get('files', {}).get('javascript', 0) + metrics.get('files', {}).get('typescript', 0)
            self.lines_of_code = metrics.get('lines_of_code', 0)
            self.functions_count = metrics.get('functions', 0)
            self.classes_count = metrics.get('classes', 0)
            self.imports_count = metrics.get('imports', 0)
            self.test_files = metrics.get('test_files', 0)
            
            self.total_errors = health.get('error_count', 0)
            self.total_warnings = health.get('warning_count', 0)
            self.total_symbols = len(results.get('symbols', []))
            
            # Health metrics
            self.maintainability_index = health.get('maintainability_index', 0.0)
            self.technical_debt_score = health.get('technical_debt_score', 0)
            self.test_coverage_estimate = health.get('test_coverage_estimate', 0.0)
            self.health_status = health.get('health_status', 'Unknown')
            
            # Complex symbols (top 10)
            all_symbols = results.get('symbols', [])
            complex_symbols = [s for s in all_symbols if 'complexity' in s]
            self.complex_symbols = sorted(complex_symbols, key=lambda x: x['complexity'], reverse=True)[:10]
            
            self.analysis_progress = 100.0
            self.analysis_complete = True
            self.set_success("Real analysis completed successfully!")
            
        except Exception as e:
            self.set_error(f"Analysis failed: {str(e)}")
        finally:
            self.analysis_running = False
            self.analysis_status = "Ready"
    
    def set_tab(self, tab: str):
        """Set the current tab."""
        self.current_tab = tab
    
    def set_success(self, message: str):
        """Set success message."""
        self.success_message = message
        self.error_message = ""
    
    def set_error(self, message: str):
        """Set error message."""
        self.error_message = message
        self.success_message = ""
    
    def clear_messages(self):
        """Clear all messages."""
        self.success_message = ""
        self.error_message = ""


def create_real_header() -> rx.Component:
    """Create the real dashboard header."""
    return rx.hstack(
        # Logo and title
        rx.hstack(
            rx.icon("activity", size=32, color="blue"),
            rx.vstack(
                rx.heading("Graph-Sitter Real Analysis Dashboard", size="lg"),
                rx.text("Live Codebase Analysis with Real Data", size="sm", color="gray"),
                spacing="0",
                align="start"
            ),
            spacing="3",
            align="center"
        ),
        
        # Real stats badges
        rx.hstack(
            rx.badge(
                rx.hstack(
                    rx.icon("file", size=16),
                    rx.text(RealDashboardState.total_files),
                    spacing="1"
                ),
                color="blue",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("code", size=16),
                    rx.text(f"{RealDashboardState.lines_of_code:,}"),
                    spacing="1"
                ),
                color="purple",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("alert-circle", size=16),
                    rx.text(RealDashboardState.total_errors),
                    spacing="1"
                ),
                color="red",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("alert-triangle", size=16),
                    rx.text(RealDashboardState.total_warnings),
                    spacing="1"
                ),
                color="yellow",
                variant="soft"
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("zap", size=16),
                    rx.text(RealDashboardState.functions_count),
                    spacing="1"
                ),
                color="green",
                variant="soft"
            ),
            spacing="2"
        ),
        
        # Analysis button
        rx.button(
            rx.cond(
                RealDashboardState.analysis_running,
                rx.hstack(
                    rx.spinner(size="4"),
                    rx.text("Analyzing..."),
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("play", size=16),
                    rx.text("Run Real Analysis"),
                    spacing="2"
                )
            ),
            on_click=RealDashboardState.run_real_analysis,
            disabled=~RealDashboardState.codebase_loaded | RealDashboardState.analysis_running,
            color_scheme="blue"
        ),
        
        justify="between",
        align="center",
        width="100%",
        padding="4",
        border_bottom="1px solid var(--gray-6)"
    )


def create_real_sidebar() -> rx.Component:
    """Create the real dashboard sidebar."""
    return rx.vstack(
        # Codebase selection
        rx.vstack(
            rx.heading("Codebase", size="md"),
            rx.select(
                RealDashboardState.available_codebases,
                value=RealDashboardState.selected_codebase,
                on_change=RealDashboardState.select_codebase,
                width="100%"
            ),
            rx.button(
                rx.cond(
                    RealDashboardState.codebase_loaded,
                    rx.hstack(
                        rx.icon("check", size=16),
                        rx.text("Loaded"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("folder-open", size=16),
                        rx.text("Load Codebase"),
                        spacing="2"
                    )
                ),
                on_click=RealDashboardState.load_codebase,
                disabled=RealDashboardState.codebase_loaded,
                width="100%",
                color_scheme=rx.cond(RealDashboardState.codebase_loaded, "green", "blue")
            ),
            rx.text(
                f"Path: {RealDashboardState.selected_codebase_path}",
                size="xs",
                color="gray",
                font_family="mono"
            ),
            spacing="3",
            align="start",
            width="100%"
        ),
        
        # Navigation tabs
        rx.vstack(
            rx.heading("Navigation", size="md"),
            rx.vstack(
                rx.button(
                    rx.hstack(
                        rx.icon("home", size=16),
                        rx.text("Overview"),
                        spacing="2"
                    ),
                    on_click=lambda: RealDashboardState.set_tab("overview"),
                    variant=rx.cond(RealDashboardState.current_tab == "overview", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("bar-chart", size=16),
                        rx.text("Metrics"),
                        spacing="2"
                    ),
                    on_click=lambda: RealDashboardState.set_tab("metrics"),
                    variant=rx.cond(RealDashboardState.current_tab == "metrics", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("code", size=16),
                        rx.text("Symbols"),
                        spacing="2"
                    ),
                    on_click=lambda: RealDashboardState.set_tab("symbols"),
                    variant=rx.cond(RealDashboardState.current_tab == "symbols", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("alert-triangle", size=16),
                        rx.text("Issues"),
                        spacing="2"
                    ),
                    on_click=lambda: RealDashboardState.set_tab("issues"),
                    variant=rx.cond(RealDashboardState.current_tab == "issues", "solid", "ghost"),
                    width="100%",
                    justify="start"
                ),
                spacing="2",
                width="100%"
            ),
            spacing="3",
            align="start",
            width="100%"
        ),
        
        # Analysis progress
        rx.cond(
            RealDashboardState.analysis_running,
            rx.vstack(
                rx.heading("Analysis Progress", size="md"),
                rx.vstack(
                    rx.text(RealDashboardState.analysis_status, size="sm"),
                    rx.progress(value=RealDashboardState.analysis_progress, width="100%"),
                    rx.text(f"{RealDashboardState.analysis_progress:.1f}%", size="sm", color="gray"),
                    spacing="2",
                    width="100%"
                ),
                spacing="3",
                align="start",
                width="100%"
            )
        ),
        
        # Health indicator
        rx.cond(
            RealDashboardState.analysis_complete,
            rx.vstack(
                rx.heading("Health Status", size="md"),
                rx.vstack(
                    rx.badge(
                        RealDashboardState.health_status,
                        color_scheme=rx.cond(
                            RealDashboardState.health_status == "Excellent", "green",
                            rx.cond(
                                RealDashboardState.health_status == "Good", "blue",
                                rx.cond(
                                    RealDashboardState.health_status == "Fair", "yellow",
                                    "red"
                                )
                            )
                        ),
                        size="lg"
                    ),
                    rx.text(f"Maintainability: {RealDashboardState.maintainability_index}/100", size="sm"),
                    rx.text(f"Tech Debt: {RealDashboardState.technical_debt_score}", size="sm"),
                    spacing="2",
                    width="100%"
                ),
                spacing="3",
                align="start",
                width="100%"
            )
        ),
        
        spacing="6",
        align="start",
        width="100%",
        padding="4"
    )


def create_real_overview_tab() -> rx.Component:
    """Create the real overview tab."""
    return rx.vstack(
        rx.heading("Real Codebase Analysis Results", size="xl"),
        
        rx.cond(
            RealDashboardState.analysis_complete,
            rx.vstack(
                # Real stats grid
                rx.grid(
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("file", size=24, color="blue"),
                                rx.text("Files", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(RealDashboardState.total_files, size="3xl", weight="bold", color="blue"),
                            rx.text("Total files analyzed", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("code", size=24, color="purple"),
                                rx.text("Lines", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(f"{RealDashboardState.lines_of_code:,}", size="3xl", weight="bold", color="purple"),
                            rx.text("Lines of code", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("zap", size=24, color="green"),
                                rx.text("Functions", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(RealDashboardState.functions_count, size="3xl", weight="bold", color="green"),
                            rx.text("Functions detected", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("box", size=24, color="orange"),
                                rx.text("Classes", size="lg", weight="bold"),
                                justify="between",
                                width="100%"
                            ),
                            rx.text(RealDashboardState.classes_count, size="3xl", weight="bold", color="orange"),
                            rx.text("Classes detected", size="sm", color="gray"),
                            spacing="2",
                            align="start"
                        ),
                        width="100%"
                    ),
                    columns="2",
                    spacing="4",
                    width="100%"
                ),
                
                # Health metrics card
                rx.card(
                    rx.vstack(
                        rx.heading("Codebase Health Metrics", size="lg"),
                        rx.grid(
                            rx.vstack(
                                rx.text("Maintainability Index", weight="bold"),
                                rx.text(f"{RealDashboardState.maintainability_index}/100", size="xl", color="blue"),
                                spacing="1",
                                align="center"
                            ),
                            rx.vstack(
                                rx.text("Technical Debt Score", weight="bold"),
                                rx.text(RealDashboardState.technical_debt_score, size="xl", color="red"),
                                spacing="1",
                                align="center"
                            ),
                            rx.vstack(
                                rx.text("Test Coverage Est.", weight="bold"),
                                rx.text(f"{RealDashboardState.test_coverage_estimate:.1f}%", size="xl", color="green"),
                                spacing="1",
                                align="center"
                            ),
                            rx.vstack(
                                rx.text("Overall Health", weight="bold"),
                                rx.badge(
                                    RealDashboardState.health_status,
                                    color_scheme=rx.cond(
                                        RealDashboardState.health_status == "Excellent", "green",
                                        rx.cond(
                                            RealDashboardState.health_status == "Good", "blue",
                                            rx.cond(
                                                RealDashboardState.health_status == "Fair", "yellow",
                                                "red"
                                            )
                                        )
                                    ),
                                    size="lg"
                                ),
                                spacing="1",
                                align="center"
                            ),
                            columns="4",
                            spacing="4",
                            width="100%"
                        ),
                        spacing="4",
                        align="start"
                    ),
                    width="100%"
                ),
                
                spacing="6",
                width="100%"
            ),
            rx.vstack(
                rx.icon("play", size=48, color="gray"),
                rx.text("Run real analysis to see results", size="lg", color="gray"),
                rx.text("Click 'Run Real Analysis' to analyze the actual Graph-Sitter codebase", size="sm", color="gray"),
                spacing="3",
                align="center",
                padding="8"
            )
        ),
        
        spacing="6",
        align="start",
        width="100%"
    )


def create_real_symbols_tab() -> rx.Component:
    """Create the real symbols tab."""
    return rx.vstack(
        rx.heading("Complex Symbols Analysis", size="xl"),
        
        rx.cond(
            RealDashboardState.analysis_complete,
            rx.vstack(
                rx.text(f"Showing the most complex symbols from {RealDashboardState.total_symbols} total symbols", color="gray"),
                
                rx.cond(
                    len(RealDashboardState.complex_symbols) > 0,
                    rx.vstack(
                        *[
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.badge(
                                            symbol["type"].title(),
                                            color_scheme="blue",
                                            variant="soft"
                                        ),
                                        rx.badge(
                                            f"Complexity: {symbol['complexity']}",
                                            color_scheme=rx.cond(
                                                symbol["complexity"] > 20, "red",
                                                rx.cond(symbol["complexity"] > 10, "yellow", "green")
                                            )
                                        ),
                                        justify="between",
                                        width="100%"
                                    ),
                                    rx.text(symbol["name"], size="lg", weight="bold"),
                                    rx.text(
                                        f"{symbol['file']}:{symbol['line']}",
                                        size="sm",
                                        color="gray",
                                        font_family="mono"
                                    ),
                                    spacing="2",
                                    align="start"
                                ),
                                width="100%"
                            )
                            for symbol in RealDashboardState.complex_symbols
                        ],
                        spacing="3",
                        width="100%"
                    ),
                    rx.text("No complex symbols found", color="gray")
                ),
                
                spacing="4",
                width="100%"
            ),
            rx.text("Run analysis to see complex symbols", color="gray")
        ),
        
        spacing="6",
        align="start",
        width="100%"
    )


def create_real_main_content() -> rx.Component:
    """Create the real main content area."""
    return rx.vstack(
        # Messages
        rx.cond(
            RealDashboardState.success_message != "",
            rx.callout(
                RealDashboardState.success_message,
                icon="check",
                color_scheme="green",
                width="100%"
            )
        ),
        rx.cond(
            RealDashboardState.error_message != "",
            rx.callout(
                RealDashboardState.error_message,
                icon="alert-triangle",
                color_scheme="red",
                width="100%"
            )
        ),
        
        # Tab content
        rx.cond(
            RealDashboardState.current_tab == "overview",
            create_real_overview_tab(),
            rx.cond(
                RealDashboardState.current_tab == "symbols",
                create_real_symbols_tab(),
                rx.vstack(
                    rx.heading(f"{RealDashboardState.current_tab.title()} Analysis", size="xl"),
                    rx.text("This tab shows real analysis data (implementation in progress)", color="gray"),
                    spacing="4",
                    align="start",
                    width="100%"
                )
            )
        ),
        
        spacing="4",
        width="100%",
        padding="4"
    )


def real_index() -> rx.Component:
    """Real dashboard page."""
    return rx.vstack(
        create_real_header(),
        rx.hstack(
            create_real_sidebar(),
            create_real_main_content(),
            spacing="0",
            width="100%",
            height="calc(100vh - 120px)",
            align="start"
        ),
        spacing="0",
        width="100%",
        height="100vh"
    )


# Create the app
app = rx.App(
    style={
        "font_family": "Inter, sans-serif",
        "background_color": "var(--gray-1)",
    }
)

app.add_page(real_index, route="/")

if __name__ == "__main__":
    print("🚀 Starting Real Graph-Sitter Dashboard...")
    print("📊 This dashboard shows actual analysis results from the Graph-Sitter codebase!")
    print("🌐 Access at: http://localhost:3000")
