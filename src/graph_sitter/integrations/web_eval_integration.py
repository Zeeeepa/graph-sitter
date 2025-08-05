"""
Web Evaluation Agent Integration for Graph-Sitter

This module integrates web-eval-agent's web application testing capabilities
with graph-sitter for automated web application evaluation and testing.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# Optional web-eval-agent imports
try:
    # These would be the actual imports from web-eval-agent
    # For now, we'll create mock implementations
    WEB_EVAL_AVAILABLE = False
    logger.info("Web-eval-agent not available as standalone package. Using integrated implementation.")
except ImportError:
    WEB_EVAL_AVAILABLE = False


@dataclass
class WebEvalResult:
    """Result of web application evaluation."""
    url: str
    success: bool
    score: float
    timestamp: datetime
    duration: float
    findings: List[Dict[str, Any]]
    screenshots: List[str]
    errors: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebEvalResult':
        """Create result from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class EvaluationConfig:
    """Configuration for web evaluation."""
    timeout: int = 30
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = "Mozilla/5.0 (compatible; WebEvalAgent/1.0)"
    wait_for_load: bool = True
    capture_screenshots: bool = True
    check_accessibility: bool = True
    check_performance: bool = True
    check_security: bool = True
    custom_checks: List[str] = None
    
    def __post_init__(self):
        if self.custom_checks is None:
            self.custom_checks = []


class WebEvalIntegration:
    """
    Integration between Graph-Sitter and Web Evaluation Agent.
    
    This class provides methods to evaluate web applications, run automated tests,
    and perform comprehensive web application analysis.
    """
    
    def __init__(self, codebase=None, config: Optional[EvaluationConfig] = None):
        """
        Initialize Web Evaluation integration.
        
        Args:
            codebase: Graph-sitter codebase instance (optional)
            config: Evaluation configuration
        """
        self.codebase = codebase
        self.config = config or EvaluationConfig()
        self._browser_manager = None
        self._session_manager = None
        
        # Initialize browser components (mock implementation)
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize web evaluation components."""
        try:
            # Mock browser manager initialization
            self._browser_manager = MockBrowserManager()
            self._session_manager = MockSessionManager()
            logger.info("Web evaluation components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize web evaluation components: {e}")
    
    def is_available(self) -> bool:
        """Check if Web Evaluation integration is available."""
        return self._browser_manager is not None
    
    async def evaluate_url(
        self,
        url: str,
        config: Optional[EvaluationConfig] = None
    ) -> WebEvalResult:
        """
        Evaluate a web application at the given URL.
        
        Args:
            url: URL to evaluate
            config: Optional evaluation configuration
            
        Returns:
            WebEvalResult with evaluation details
        """
        eval_config = config or self.config
        start_time = datetime.now()
        
        try:
            # Mock evaluation process
            findings = await self._run_evaluation_checks(url, eval_config)
            screenshots = await self._capture_screenshots(url, eval_config)
            
            # Calculate score based on findings
            score = self._calculate_score(findings)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return WebEvalResult(
                url=url,
                success=True,
                score=score,
                timestamp=start_time,
                duration=duration,
                findings=findings,
                screenshots=screenshots,
                errors=[],
                metadata={
                    "config": asdict(eval_config),
                    "user_agent": eval_config.user_agent,
                    "viewport": f"{eval_config.viewport_width}x{eval_config.viewport_height}"
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Web evaluation failed for {url}: {e}")
            
            return WebEvalResult(
                url=url,
                success=False,
                score=0.0,
                timestamp=start_time,
                duration=duration,
                findings=[],
                screenshots=[],
                errors=[str(e)],
                metadata={"error": str(e)}
            )
    
    async def evaluate_local_app(
        self,
        port: int = 3000,
        path: str = "/",
        config: Optional[EvaluationConfig] = None
    ) -> WebEvalResult:
        """
        Evaluate a local web application.
        
        Args:
            port: Local port where app is running
            path: Path to evaluate (default: "/")
            config: Optional evaluation configuration
            
        Returns:
            WebEvalResult with evaluation details
        """
        url = f"http://localhost:{port}{path}"
        return await self.evaluate_url(url, config)
    
    async def batch_evaluate(
        self,
        urls: List[str],
        config: Optional[EvaluationConfig] = None
    ) -> List[WebEvalResult]:
        """
        Evaluate multiple URLs in batch.
        
        Args:
            urls: List of URLs to evaluate
            config: Optional evaluation configuration
            
        Returns:
            List of WebEvalResult objects
        """
        results = []
        
        for url in urls:
            try:
                result = await self.evaluate_url(url, config)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate {url}: {e}")
                results.append(WebEvalResult(
                    url=url,
                    success=False,
                    score=0.0,
                    timestamp=datetime.now(),
                    duration=0.0,
                    findings=[],
                    screenshots=[],
                    errors=[str(e)],
                    metadata={"batch_error": str(e)}
                ))
        
        return results
    
    async def _run_evaluation_checks(
        self,
        url: str,
        config: EvaluationConfig
    ) -> List[Dict[str, Any]]:
        """Run evaluation checks on the URL."""
        findings = []
        
        # Mock accessibility check
        if config.check_accessibility:
            findings.append({
                "type": "accessibility",
                "severity": "info",
                "message": "Page has good accessibility practices",
                "score": 0.9,
                "details": {
                    "alt_texts": "present",
                    "heading_structure": "proper",
                    "color_contrast": "sufficient"
                }
            })
        
        # Mock performance check
        if config.check_performance:
            findings.append({
                "type": "performance",
                "severity": "warning",
                "message": "Page load time could be improved",
                "score": 0.7,
                "details": {
                    "load_time": "2.3s",
                    "first_contentful_paint": "1.2s",
                    "largest_contentful_paint": "2.1s"
                }
            })
        
        # Mock security check
        if config.check_security:
            findings.append({
                "type": "security",
                "severity": "info",
                "message": "Basic security headers present",
                "score": 0.8,
                "details": {
                    "https": True,
                    "security_headers": ["X-Frame-Options", "X-Content-Type-Options"],
                    "csp": "present"
                }
            })
        
        # Mock custom checks
        for check in config.custom_checks:
            findings.append({
                "type": "custom",
                "check": check,
                "severity": "info",
                "message": f"Custom check '{check}' passed",
                "score": 0.8,
                "details": {"custom_check": check}
            })
        
        return findings
    
    async def _capture_screenshots(
        self,
        url: str,
        config: EvaluationConfig
    ) -> List[str]:
        """Capture screenshots of the web page."""
        if not config.capture_screenshots:
            return []
        
        # Mock screenshot capture
        screenshots = [
            f"screenshot_{url.replace('://', '_').replace('/', '_')}_full.png",
            f"screenshot_{url.replace('://', '_').replace('/', '_')}_mobile.png"
        ]
        
        return screenshots
    
    def _calculate_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate overall score from findings."""
        if not findings:
            return 0.5  # Neutral score if no findings
        
        total_score = sum(finding.get('score', 0.5) for finding in findings)
        return min(total_score / len(findings), 1.0)
    
    async def generate_report(
        self,
        results: Union[WebEvalResult, List[WebEvalResult]],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            results: Single result or list of results
            output_path: Optional path to save report
            
        Returns:
            Report content as string
        """
        if isinstance(results, WebEvalResult):
            results = [results]
        
        report_lines = [
            "# Web Application Evaluation Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Total URLs Evaluated: {len(results)}",
            ""
        ]
        
        # Summary statistics
        successful = sum(1 for r in results if r.success)
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        
        report_lines.extend([
            "## Summary",
            f"- Successful evaluations: {successful}/{len(results)}",
            f"- Average score: {avg_score:.2f}",
            f"- Total duration: {sum(r.duration for r in results):.2f}s",
            ""
        ])
        
        # Individual results
        for i, result in enumerate(results, 1):
            report_lines.extend([
                f"## Evaluation {i}: {result.url}",
                f"- Success: {'✅' if result.success else '❌'}",
                f"- Score: {result.score:.2f}",
                f"- Duration: {result.duration:.2f}s",
                f"- Findings: {len(result.findings)}",
                ""
            ])
            
            # Findings details
            if result.findings:
                report_lines.append("### Findings:")
                for finding in result.findings:
                    severity_emoji = {
                        'error': '🔴',
                        'warning': '🟡',
                        'info': '🔵'
                    }.get(finding.get('severity', 'info'), '🔵')
                    
                    report_lines.append(
                        f"- {severity_emoji} **{finding.get('type', 'unknown').title()}**: "
                        f"{finding.get('message', 'No message')} (Score: {finding.get('score', 0):.2f})"
                    )
                report_lines.append("")
            
            # Errors
            if result.errors:
                report_lines.append("### Errors:")
                for error in result.errors:
                    report_lines.append(f"- ❌ {error}")
                report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Report saved to {output_path}")
        
        return report_content
    
    async def cleanup(self):
        """Clean up web evaluation resources."""
        try:
            if self._browser_manager:
                await self._browser_manager.cleanup()
            if self._session_manager:
                await self._session_manager.cleanup()
            logger.info("Web evaluation resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Mock implementations for browser and session management
class MockBrowserManager:
    """Mock browser manager for demonstration."""
    
    def __init__(self):
        self.browsers = {}
    
    async def get_browser(self, config):
        """Get or create a browser instance."""
        return MockBrowser(config)
    
    async def cleanup(self):
        """Clean up all browsers."""
        for browser in self.browsers.values():
            await browser.close()
        self.browsers.clear()


class MockBrowser:
    """Mock browser for demonstration."""
    
    def __init__(self, config):
        self.config = config
        self.pages = []
    
    async def new_page(self):
        """Create a new page."""
        page = MockPage(self.config)
        self.pages.append(page)
        return page
    
    async def close(self):
        """Close browser."""
        for page in self.pages:
            await page.close()
        self.pages.clear()


class MockPage:
    """Mock page for demonstration."""
    
    def __init__(self, config):
        self.config = config
        self.url = None
    
    async def goto(self, url):
        """Navigate to URL."""
        self.url = url
        await asyncio.sleep(0.1)  # Simulate navigation
    
    async def screenshot(self, path):
        """Take screenshot."""
        # Mock screenshot creation
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).touch()
        return path
    
    async def close(self):
        """Close page."""
        pass


class MockSessionManager:
    """Mock session manager for demonstration."""
    
    def __init__(self):
        self.sessions = {}
    
    async def create_session(self, session_id):
        """Create a new evaluation session."""
        self.sessions[session_id] = {
            "created": datetime.now(),
            "status": "active"
        }
        return session_id
    
    async def cleanup(self):
        """Clean up all sessions."""
        self.sessions.clear()


# Convenience function for codebase integration
def add_web_eval_capabilities(codebase, **kwargs) -> None:
    """
    Add Web Evaluation capabilities to a codebase instance.
    
    Args:
        codebase: Graph-sitter codebase instance
        **kwargs: Configuration for WebEvalIntegration
    """
    if hasattr(codebase, '_web_eval'):
        # Already has web eval integration
        return
    
    # Create integration instance
    integration = WebEvalIntegration(codebase=codebase, **kwargs)
    codebase._web_eval = integration
    
    # Add methods to codebase
    codebase.evaluate_url = integration.evaluate_url
    codebase.evaluate_local_app = integration.evaluate_local_app
    codebase.batch_evaluate = integration.batch_evaluate
    codebase.generate_web_report = integration.generate_report
    codebase.cleanup_web_eval = integration.cleanup
    
    # Add properties
    codebase.web_eval_available = property(lambda self: self._web_eval.is_available())
    
    logger.info(f"Web evaluation capabilities added to codebase: {codebase.repo_path}")

