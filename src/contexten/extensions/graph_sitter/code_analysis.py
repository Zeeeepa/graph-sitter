#!/usr/bin/env python3
"""
🚀 SUPER COMPREHENSIVE SINGLE-MODE ANALYSIS 🚀

Simple, powerful single-function interface for complete codebase analysis
with interactive exploration capabilities.

Usage:
    from contexten.extensions.graph_sitter.code_analysis import analyze_codebase
    result = analyze_codebase("/path/to/code")
    print(f"Explore your code at: {result.interactive_url}")

Features:
- Complete analysis in one function call
- Interactive web interface for exploration
- All Phase 1 & Phase 2 features enabled
- Automatic report generation
- Local web server for exploration
- Comprehensive results with insights
"""

import logging
import time
import webbrowser
import threading
from pathlib import Path
from typing import Union, Optional, Dict, Any
from dataclasses import dataclass, field
import tempfile
import os
import json

logger = logging.getLogger(__name__)

# Import the comprehensive analysis system
try:
    from .analysis import (
        ComprehensiveAnalysisEngine,
        AnalysisConfig,
        AnalysisResult,
        AnalysisPresets
    )
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Analysis system not available: {e}")
    ANALYSIS_AVAILABLE = False

# Try to import web server capabilities
try:
    import http.server
    import socketserver
    from urllib.parse import urlparse, parse_qs
    WEB_SERVER_AVAILABLE = True
except ImportError:
    WEB_SERVER_AVAILABLE = False

# Try to import additional dependencies
try:
    import webbrowser
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False


@dataclass
class CodeAnalysisResult:
    """
    Comprehensive analysis result with interactive exploration capabilities.
    """
    # Basic information
    path: str
    analysis_time: float
    timestamp: str
    
    # Core metrics
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_lines: int = 0
    
    # Analysis results
    import_loops: int = 0
    dead_code_items: int = 0
    training_data_items: int = 0
    security_issues: int = 0
    performance_issues: int = 0
    quality_score: float = 0.0
    
    # Interactive exploration
    interactive_url: Optional[str] = None
    report_path: Optional[str] = None
    web_server_port: Optional[int] = None
    
    # Detailed results (hidden from simple interface)
    _detailed_results: Optional[AnalysisResult] = field(default=None, repr=False)
    _web_server: Optional[Any] = field(default=None, repr=False)
    
    def __str__(self) -> str:
        """String representation of analysis results."""
        return f"""
🚀 COMPREHENSIVE CODE ANALYSIS COMPLETE
{'=' * 50}
📁 Path: {self.path}
⏱️  Analysis Time: {self.analysis_time:.2f}s
📊 Files: {self.total_files} | Functions: {self.total_functions} | Classes: {self.total_classes}
📏 Lines of Code: {self.total_lines:,}

🔍 ANALYSIS RESULTS
Import Loops: {self.import_loops}
Dead Code: {self.dead_code_items}
Security Issues: {self.security_issues}
Performance Issues: {self.performance_issues}
Quality Score: {self.quality_score:.1f}/10

🌐 INTERACTIVE EXPLORATION
{f"🔗 Open: {self.interactive_url}" if self.interactive_url else "❌ Interactive URL not available"}
{f"📄 Report: {self.report_path}" if self.report_path else ""}
        """.strip()
    
    def open_browser(self):
        """Open the interactive analysis in the default browser."""
        if self.interactive_url and BROWSER_AVAILABLE:
            webbrowser.open(self.interactive_url)
            print(f"🌐 Opening interactive analysis: {self.interactive_url}")
        else:
            print("❌ Browser opening not available")
    
    def stop_server(self):
        """Stop the web server if running."""
        if self._web_server:
            try:
                self._web_server.shutdown()
                print("🛑 Web server stopped")
            except Exception as e:
                logger.warning(f"Error stopping web server: {e}")


class InteractiveWebServer:
    """Simple web server for interactive code exploration."""
    
    def __init__(self, report_path: str, port: int = 8000):
        self.report_path = report_path
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self) -> str:
        """Start the web server and return the URL."""
        try:
            # Create a simple HTTP handler
            class AnalysisHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=os.path.dirname(report_path), **kwargs)
                
                def do_GET(self):
                    if self.path == '/' or self.path == '/index.html':
                        # Serve the analysis report
                        self.path = '/' + os.path.basename(report_path)
                    super().do_GET()
                
                def log_message(self, format, *args):
                    # Suppress server logs
                    pass
            
            # Find available port
            for port_attempt in range(self.port, self.port + 100):
                try:
                    self.server = socketserver.TCPServer(("", port_attempt), AnalysisHandler)
                    self.port = port_attempt
                    break
                except OSError:
                    continue
            
            if not self.server:
                raise Exception("No available ports found")
            
            # Start server in background thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            url = f"http://localhost:{self.port}"
            logger.info(f"Web server started at {url}")
            return url
        
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
            return None
    
    def stop(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1.0)


def analyze_codebase(
    path: Union[str, Path],
    auto_open: bool = True,
    port: int = 8000,
    include_interactive: bool = True
) -> CodeAnalysisResult:
    """
    🚀 SUPER COMPREHENSIVE SINGLE-MODE ANALYSIS
    
    Performs complete codebase analysis with all features enabled and
    creates an interactive web interface for exploration.
    
    Args:
        path: Path to the codebase to analyze
        auto_open: Automatically open browser to interactive analysis
        port: Port for web server (will find available port if busy)
        include_interactive: Generate interactive web interface
    
    Returns:
        CodeAnalysisResult with interactive exploration capabilities
    
    Example:
        >>> from contexten.extensions.graph_sitter.code_analysis import analyze_codebase
        >>> result = analyze_codebase("/path/to/code")
        >>> print(result)
        >>> result.open_browser()  # Open interactive analysis
    """
    start_time = time.time()
    path_str = str(path)
    
    print(f"🚀 Starting comprehensive analysis of: {path_str}")
    
    if not ANALYSIS_AVAILABLE:
        print("❌ Analysis system not available")
        return CodeAnalysisResult(
            path=path_str,
            analysis_time=0.0,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            interactive_url=None
        )
    
    try:
        # Create comprehensive configuration with all features enabled
        config = AnalysisConfig(
            # Phase 1 features - all enabled
            detect_import_loops=True,
            detect_dead_code=True,
            generate_training_data=True,
            analyze_graph_structure=True,
            enhanced_metrics=True,
            
            # Phase 2 features - all enabled
            enable_query_patterns=True,
            query_categories=['function', 'class', 'security', 'performance', 'design_pattern'],
            generate_html_report=include_interactive,
            report_theme='professional',
            include_interactive_charts=True,
            
            # Performance optimization
            enable_performance_optimization=True,
            enable_caching=True,
            enable_parallel_processing=True,
            cache_backend='memory',
            
            # Advanced configuration
            optimization_level='balanced',
            enable_lazy_graph=True,
            enable_method_usages=True,
            enable_generics=True,
            
            # Limits for comprehensive analysis
            max_functions=1000,
            max_classes=500
        )
        
        # Create and run analysis engine
        engine = ComprehensiveAnalysisEngine(config)
        detailed_result = engine.analyze(path, config)
        
        # Calculate quality score
        quality_score = _calculate_quality_score(detailed_result)
        
        # Count issues
        security_issues = sum(1 for qr in detailed_result.query_results 
                            if hasattr(qr, 'pattern') and qr.pattern.category == 'security')
        performance_issues = sum(1 for qr in detailed_result.query_results 
                               if hasattr(qr, 'pattern') and qr.pattern.category == 'performance')
        
        # Create result object
        result = CodeAnalysisResult(
            path=path_str,
            analysis_time=time.time() - start_time,
            timestamp=detailed_result.timestamp,
            total_files=detailed_result.total_files,
            total_functions=detailed_result.total_functions,
            total_classes=detailed_result.total_classes,
            total_lines=detailed_result.total_lines,
            import_loops=len(detailed_result.import_loops),
            dead_code_items=len(detailed_result.dead_code),
            training_data_items=len(detailed_result.training_data),
            security_issues=security_issues,
            performance_issues=performance_issues,
            quality_score=quality_score,
            report_path=detailed_result.html_report_path,
            _detailed_results=detailed_result
        )
        
        # Set up interactive web server if report was generated
        if include_interactive and detailed_result.html_report_path and WEB_SERVER_AVAILABLE:
            try:
                web_server = InteractiveWebServer(detailed_result.html_report_path, port)
                interactive_url = web_server.start()
                
                if interactive_url:
                    result.interactive_url = interactive_url
                    result.web_server_port = web_server.port
                    result._web_server = web_server
                    
                    print(f"🌐 Interactive analysis available at: {interactive_url}")
                    
                    # Auto-open browser if requested
                    if auto_open and BROWSER_AVAILABLE:
                        threading.Timer(1.0, lambda: webbrowser.open(interactive_url)).start()
                        print("🔗 Opening in browser...")
            
            except Exception as e:
                logger.warning(f"Could not start web server: {e}")
        
        # Print summary
        print(f"✅ Analysis complete in {result.analysis_time:.2f}s")
        print(f"📊 Analyzed {result.total_files} files, {result.total_functions} functions, {result.total_classes} classes")
        
        if result.import_loops > 0:
            print(f"⚠️  Found {result.import_loops} import loops")
        if result.dead_code_items > 0:
            print(f"🗑️  Found {result.dead_code_items} dead code items")
        if result.security_issues > 0:
            print(f"🔒 Found {result.security_issues} security issues")
        if result.performance_issues > 0:
            print(f"⚡ Found {result.performance_issues} performance issues")
        
        print(f"🏆 Quality Score: {result.quality_score:.1f}/10")
        
        return result
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return CodeAnalysisResult(
            path=path_str,
            analysis_time=time.time() - start_time,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            interactive_url=None
        )


def _calculate_quality_score(result: AnalysisResult) -> float:
    """Calculate a quality score from 0-10 based on analysis results."""
    try:
        score = 10.0  # Start with perfect score
        
        # Deduct for issues
        if result.total_functions > 0:
            # Import loops penalty
            import_loop_ratio = len(result.import_loops) / max(result.total_files, 1)
            score -= min(import_loop_ratio * 20, 3.0)  # Max 3 points deduction
            
            # Dead code penalty
            dead_code_ratio = len(result.dead_code) / max(result.total_functions, 1)
            score -= min(dead_code_ratio * 10, 2.0)  # Max 2 points deduction
            
            # Security issues penalty
            security_issues = sum(1 for qr in result.query_results 
                                if hasattr(qr, 'pattern') and qr.pattern.category == 'security')
            if security_issues > 0:
                score -= min(security_issues * 0.5, 2.0)  # Max 2 points deduction
            
            # Performance issues penalty
            performance_issues = sum(1 for qr in result.query_results 
                                   if hasattr(qr, 'pattern') and qr.pattern.category == 'performance')
            if performance_issues > 0:
                score -= min(performance_issues * 0.3, 1.5)  # Max 1.5 points deduction
            
            # Function complexity bonus/penalty
            if result.enhanced_function_metrics:
                avg_complexity = sum(f.complexity for f in result.enhanced_function_metrics) / len(result.enhanced_function_metrics)
                if avg_complexity > 10:
                    score -= min((avg_complexity - 10) * 0.1, 1.5)  # Penalty for high complexity
                elif avg_complexity < 5:
                    score += 0.5  # Bonus for low complexity
        
        return max(0.0, min(10.0, score))  # Clamp between 0 and 10
    
    except Exception as e:
        logger.warning(f"Error calculating quality score: {e}")
        return 5.0  # Default neutral score


def quick_analyze(path: Union[str, Path]) -> CodeAnalysisResult:
    """
    Quick analysis with performance optimizations.
    
    Args:
        path: Path to the codebase to analyze
    
    Returns:
        CodeAnalysisResult with basic metrics
    """
    return analyze_codebase(path, auto_open=False, include_interactive=False)


def analyze_and_explore(path: Union[str, Path], port: int = 8000) -> CodeAnalysisResult:
    """
    Comprehensive analysis with automatic browser opening.
    
    Args:
        path: Path to the codebase to analyze
        port: Port for web server
    
    Returns:
        CodeAnalysisResult with interactive exploration
    """
    return analyze_codebase(path, auto_open=True, port=port, include_interactive=True)


# Convenience aliases
analyze = analyze_codebase
comprehensive_analysis = analyze_codebase


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m contexten.extensions.graph_sitter.code_analysis <path>")
        sys.exit(1)
    
    path = sys.argv[1]
    print(f"🚀 Analyzing: {path}")
    
    result = analyze_codebase(path)
    print(result)
    
    if result.interactive_url:
        print(f"\n🌐 Interactive analysis: {result.interactive_url}")
        print("Press Ctrl+C to stop the server")
        
        try:
            # Keep the server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            result.stop_server()
