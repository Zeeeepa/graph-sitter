#!/usr/bin/env python3
"""
Simple script to run comprehensive integration tests.

This script provides an easy way to run the comprehensive integration testing
framework without needing to remember complex command line arguments.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from tests.integration.test_comprehensive_integration import run_comprehensive_integration_tests
    from tests.integration.framework.config import get_config
    from rich.console import Console
    from rich.panel import Panel
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have installed the project dependencies:")
    print("  pip install -e .")
    print("  pip install psutil click pytest-asyncio")
    sys.exit(1)

console = Console()


async def main():
    """Run comprehensive integration tests."""
    console.print(Panel.fit(
        "🧪 Comprehensive Integration Testing Framework\n"
        "Testing-11: Comprehensive Integration Testing & Validation",
        style="bold blue"
    ))
    
    try:
        # Load configuration
        config = get_config()
        console.print(f"📋 Configuration loaded")
        console.print(f"   Debug Mode: {'✅' if config.debug_mode else '❌'}")
        console.print(f"   Log Level: {config.log_level}")
        console.print(f"   Output Directory: {config.get_output_directory()}")
        
        # Validate configuration
        issues = config.validate_config()
        if issues:
            console.print("⚠️ Configuration issues found:")
            for issue in issues:
                console.print(f"   • {issue}")
            console.print("Continuing with default values...")
        
        console.print("\n🚀 Starting comprehensive integration tests...")
        
        # Run all tests
        summary, reports = await run_comprehensive_integration_tests()
        
        # Display final results
        console.print("\n" + "="*60)
        console.print("🎯 FINAL RESULTS")
        console.print("="*60)
        
        status_colors = {
            "success": "green",
            "partial_success": "yellow",
            "performance_degradation": "orange", 
            "validation_issues": "orange",
            "failure": "red",
            "critical_failure": "bright_red"
        }
        
        status_emojis = {
            "success": "✅",
            "partial_success": "⚠️",
            "performance_degradation": "📉",
            "validation_issues": "🔍", 
            "failure": "❌",
            "critical_failure": "🚨"
        }
        
        status_color = status_colors.get(summary.overall_status, "white")
        status_emoji = status_emojis.get(summary.overall_status, "❓")
        
        console.print(f"{status_emoji} Overall Status: [{status_color}]{summary.overall_status.upper()}[/{status_color}]")
        console.print(f"📊 Total Tests: {summary.total_tests}")
        console.print(f"📈 Success Rate: {summary.overall_success_rate:.1%}")
        console.print(f"⏱️ Duration: {summary.total_duration_ms:.1f}ms")
        
        # Show report locations
        console.print(f"\n📄 Reports generated:")
        for format_name, file_path in reports.items():
            console.print(f"   {format_name.upper()}: {file_path}")
        
        # Determine exit code
        if summary.overall_status in ["critical_failure", "failure"]:
            console.print("\n❌ Tests failed with critical issues", style="red")
            return 1
        elif summary.overall_status in ["performance_degradation", "validation_issues"]:
            console.print("\n⚠️ Tests completed with warnings", style="yellow")
            if config.fail_on_regression:
                return 1
            return 0
        else:
            console.print("\n✅ All tests passed successfully!", style="green")
            return 0
            
    except KeyboardInterrupt:
        console.print("\n⏹️ Tests interrupted by user")
        return 130
    except Exception as e:
        console.print(f"\n❌ Test execution failed: {e}", style="red")
        if config.debug_mode:
            import traceback
            console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

