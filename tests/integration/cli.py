#!/usr/bin/env python3
"""
Command Line Interface for Comprehensive Integration Testing

Provides a CLI tool for running integration tests, performance benchmarks,
validation checks, and generating reports.
"""

import asyncio
import click
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from .framework import (
    IntegrationTestFramework,
    PerformanceBenchmark,
    CrossComponentValidator,
    EndToEndWorkflowTester,
    TestReporter
)
from .framework.config import get_config, IntegrationTestConfig, create_sample_config_file
from .test_comprehensive_integration import run_comprehensive_integration_tests

console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--log-level', default='INFO', help='Set log level')
@click.pass_context
def cli(ctx, config, debug, log_level):
    """Comprehensive Integration Testing Framework CLI."""
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        ctx.obj['config'] = IntegrationTestConfig.from_file(Path(config))
    else:
        ctx.obj['config'] = get_config()
    
    # Override config with CLI options
    if debug:
        ctx.obj['config'].debug_mode = True
    
    ctx.obj['config'].log_level = log_level
    
    # Display header
    console.print(Panel.fit(
        "🧪 Comprehensive Integration Testing Framework",
        style="bold blue"
    ))


@cli.command()
@click.option('--components', '-c', multiple=True, help='Specific components to test')
@click.option('--suite-name', default='cli_integration', help='Name for the test suite')
@click.pass_context
def integration(ctx, components, suite_name):
    """Run integration tests."""
    config = ctx.obj['config']
    
    if not config.run_integration_tests:
        console.print("❌ Integration tests disabled in configuration")
        return
    
    async def run_integration():
        console.print("🔧 Running integration tests...")
        
        framework = IntegrationTestFramework()
        
        # Use specified components or all available
        if components:
            component_list = list(components)
        else:
            component_list = list(framework.components.keys())
        
        suite = framework.create_test_suite(suite_name, component_list)
        result = await framework.run_integration_suite(suite)
        
        console.print(f"✅ Integration tests completed")
        console.print(f"   Success Rate: {result.success_rate:.1%}")
        console.print(f"   Duration: {result.duration:.2f}s")
        
        return result
    
    try:
        result = asyncio.run(run_integration())
        
        # Exit with error code if tests failed significantly
        if result.success_rate < 0.8:
            console.print("❌ Integration tests failed", style="red")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Integration tests failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--iterations', '-i', default=5, help='Number of benchmark iterations')
@click.option('--baseline-update', is_flag=True, help='Update performance baselines')
@click.option('--codebase-path', type=click.Path(exists=True), help='Path to codebase for testing')
@click.pass_context
def performance(ctx, iterations, baseline_update, codebase_path):
    """Run performance benchmarks."""
    config = ctx.obj['config']
    
    if not config.run_performance_tests:
        console.print("❌ Performance tests disabled in configuration")
        return
    
    async def run_performance():
        console.print("🏃 Running performance benchmarks...")
        
        baseline_file = config.get_baseline_file_path()
        benchmark = PerformanceBenchmark(baseline_file=baseline_file)
        
        # Run Graph-Sitter parsing benchmark
        if codebase_path:
            path = Path(codebase_path)
        else:
            path = Path(".")
        
        if path.exists():
            await benchmark.benchmark_graph_sitter_parsing(path)
        
        # Run Codegen agent benchmark
        await benchmark.benchmark_codegen_agent_creation()
        
        # Update baselines if requested
        if baseline_update:
            benchmark.save_baselines()
            console.print("💾 Performance baselines updated")
        
        # Check for regressions
        summary = benchmark.get_performance_summary()
        regressions = summary.get("regressions_detected", 0)
        
        console.print(f"✅ Performance benchmarks completed")
        console.print(f"   Benchmarks: {summary.get('total_benchmarks', 0)}")
        console.print(f"   Regressions: {regressions}")
        
        return summary
    
    try:
        summary = asyncio.run(run_performance())
        
        # Exit with error code if significant regressions detected
        if config.fail_on_regression and summary.get("regressions_detected", 0) > 2:
            console.print("❌ Significant performance regressions detected", style="red")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Performance benchmarks failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--component-pairs', multiple=True, help='Specific component pairs to validate (format: comp1,comp2)')
@click.pass_context
def validation(ctx, component_pairs):
    """Run cross-component validation."""
    config = ctx.obj['config']
    
    if not config.run_validation_tests:
        console.print("❌ Validation tests disabled in configuration")
        return
    
    async def run_validation():
        console.print("🔍 Running cross-component validation...")
        
        validator = CrossComponentValidator()
        
        if component_pairs:
            # Run specific component pair validations
            results = []
            for pair_str in component_pairs:
                comp1, comp2 = pair_str.split(',')
                result = await validator.validate_interface_compatibility(comp1.strip(), comp2.strip())
                results.append(result)
        else:
            # Run all validations
            results = await validator.run_all_validations()
        
        # Analyze results
        passed = len([r for r in results if r.passed])
        critical_issues = sum(len(r.critical_issues) for r in results)
        error_issues = sum(len(r.error_issues) for r in results)
        
        console.print(f"✅ Cross-component validation completed")
        console.print(f"   Validations: {len(results)}")
        console.print(f"   Passed: {passed}")
        console.print(f"   Critical Issues: {critical_issues}")
        console.print(f"   Error Issues: {error_issues}")
        
        return results
    
    try:
        results = asyncio.run(run_validation())
        
        # Check for critical issues
        critical_issues = sum(len(r.critical_issues) for r in results)
        
        if config.fail_on_critical_validation and critical_issues > config.validation.max_allowed_critical_issues:
            console.print(f"❌ Too many critical validation issues: {critical_issues}", style="red")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Validation tests failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--workflows', '-w', multiple=True, help='Specific workflows to run')
@click.option('--timeout', default=300, help='Workflow timeout in seconds')
@click.pass_context
def workflow(ctx, workflows, timeout):
    """Run end-to-end workflow tests."""
    config = ctx.obj['config']
    
    if not config.run_workflow_tests:
        console.print("❌ Workflow tests disabled in configuration")
        return
    
    async def run_workflows():
        console.print("🎯 Running end-to-end workflow tests...")
        
        test_data_path = config.get_test_data_path()
        tester = EndToEndWorkflowTester(test_data_path=test_data_path)
        
        if workflows:
            # Run specific workflows
            results = []
            for workflow_name in workflows:
                scenario = next((s for s in tester.scenarios if s.name == workflow_name), None)
                if scenario:
                    result = await tester.execute_workflow(scenario)
                    results.append(result)
                else:
                    console.print(f"⚠️ Workflow '{workflow_name}' not found")
        else:
            # Run all workflows
            results = await tester.run_all_workflows()
        
        # Analyze results
        completed = len([w for w in results if w.status.value == "completed"])
        avg_success_rate = sum(w.success_rate for w in results) / len(results) if results else 0
        
        console.print(f"✅ End-to-end workflow tests completed")
        console.print(f"   Workflows: {len(results)}")
        console.print(f"   Completed: {completed}")
        console.print(f"   Average Success Rate: {avg_success_rate:.1%}")
        
        return results
    
    try:
        results = asyncio.run(run_workflows())
        
        # Check completion rate
        completion_rate = len([w for w in results if w.status.value == "completed"]) / len(results) if results else 0
        
        if config.fail_on_workflow_failure and completion_rate < config.workflow.min_workflow_success_rate:
            console.print(f"❌ Workflow completion rate too low: {completion_rate:.1%}", style="red")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Workflow tests failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--output-dir', type=click.Path(), help='Output directory for reports')
@click.option('--format', 'formats', multiple=True, default=['html', 'json', 'markdown'], 
              help='Report formats to generate')
@click.pass_context
def report(ctx, output_dir, formats):
    """Generate test reports from previous runs."""
    config = ctx.obj['config']
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = config.get_output_directory()
    
    console.print(f"📄 Generating reports in: {output_path}")
    
    # Create a reporter and generate reports
    reporter = TestReporter(output_dir=output_path)
    
    # Note: This would typically load previous test results
    # For now, we'll generate a sample report
    summary = reporter.generate_summary()
    
    generated_reports = {}
    
    if 'html' in formats and config.reporting.generate_html:
        html_report = reporter.generate_html_report(summary)
        generated_reports['html'] = html_report
    
    if 'json' in formats and config.reporting.generate_json:
        json_report = reporter.generate_json_report(summary)
        generated_reports['json'] = json_report
    
    if 'markdown' in formats and config.reporting.generate_markdown:
        md_report = reporter.generate_markdown_report(summary)
        generated_reports['markdown'] = md_report
    
    console.print("✅ Reports generated:")
    for format_name, file_path in generated_reports.items():
        console.print(f"   {format_name.upper()}: {file_path}")


@cli.command()
@click.option('--quick', is_flag=True, help='Run quick test suite (reduced iterations)')
@click.option('--output-dir', type=click.Path(), help='Output directory for reports')
@click.pass_context
def all(ctx, quick, output_dir):
    """Run all integration tests and generate comprehensive report."""
    config = ctx.obj['config']
    
    console.print("🚀 Running comprehensive integration test suite...")
    
    async def run_all_tests():
        try:
            summary, reports = await run_comprehensive_integration_tests()
            
            console.print("✅ Comprehensive integration testing completed!")
            console.print(f"   Overall Status: {summary.overall_status.upper()}")
            console.print(f"   Total Tests: {summary.total_tests}")
            console.print(f"   Success Rate: {summary.overall_success_rate:.1%}")
            
            return summary
            
        except Exception as e:
            console.print(f"❌ Comprehensive testing failed: {e}", style="red")
            raise
    
    try:
        summary = asyncio.run(run_all_tests())
        
        # Determine exit code based on results
        if summary.overall_status in ["critical_failure", "failure"]:
            console.print("❌ Tests failed with critical issues", style="red")
            sys.exit(1)
        elif summary.overall_status in ["performance_degradation", "validation_issues"]:
            console.print("⚠️ Tests completed with warnings", style="yellow")
            if config.fail_on_regression:
                sys.exit(1)
        else:
            console.print("✅ All tests passed successfully", style="green")
            
    except Exception as e:
        console.print(f"❌ Test execution failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='integration_test_config.json',
              help='Output file path')
def config_sample(output):
    """Generate a sample configuration file."""
    output_path = Path(output)
    
    try:
        create_sample_config_file(output_path)
        console.print(f"✅ Sample configuration file created: {output_path}")
        console.print("Edit this file to customize your integration testing setup.")
        
    except Exception as e:
        console.print(f"❌ Failed to create configuration file: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
def validate_config(ctx):
    """Validate the current configuration."""
    config = ctx.obj['config']
    
    console.print("🔍 Validating configuration...")
    
    issues = config.validate_config()
    
    if issues:
        console.print("❌ Configuration validation failed:", style="red")
        for issue in issues:
            console.print(f"   • {issue}")
        sys.exit(1)
    else:
        console.print("✅ Configuration is valid")
        
        # Display key settings
        console.print("\n📋 Current Configuration:")
        console.print(f"   Integration Tests: {'✅' if config.run_integration_tests else '❌'}")
        console.print(f"   Performance Tests: {'✅' if config.run_performance_tests else '❌'}")
        console.print(f"   Validation Tests: {'✅' if config.run_validation_tests else '❌'}")
        console.print(f"   Workflow Tests: {'✅' if config.run_workflow_tests else '❌'}")
        console.print(f"   Output Directory: {config.get_output_directory()}")
        console.print(f"   Debug Mode: {'✅' if config.debug_mode else '❌'}")


@cli.command()
def list_components():
    """List all available components for testing."""
    framework = IntegrationTestFramework()
    
    console.print("📋 Available Components:")
    
    for name, component in framework.components.items():
        console.print(f"   • {name}")
        console.print(f"     Module: {component.module_path}")
        console.print(f"     Dependencies: {', '.join(component.dependencies) if component.dependencies else 'None'}")
        console.print(f"     Performance Critical: {'✅' if component.performance_critical else '❌'}")
        console.print()


@cli.command()
def list_workflows():
    """List all available workflow scenarios."""
    tester = EndToEndWorkflowTester()
    
    console.print("🎯 Available Workflow Scenarios:")
    
    for scenario in tester.scenarios:
        console.print(f"   • {scenario.name}")
        console.print(f"     Description: {scenario.description}")
        console.print(f"     Steps: {len(scenario.steps)}")
        console.print()


if __name__ == '__main__':
    cli()

