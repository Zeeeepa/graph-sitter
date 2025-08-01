#!/usr/bin/env python3
"""
Test Runner for Unified Error Interface

This script provides a convenient way to run all tests for the unified error interface
with different configurations and reporting options.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time


def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False, text=True)
    end_time = time.time()
    
    print(f"\nCompleted in {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run unified error interface tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML test report")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (number of workers)")
    parser.add_argument("--markers", "-m", help="Run tests matching given mark expression")
    parser.add_argument("--keyword", "-k", help="Run tests matching given keyword expression")
    parser.add_argument("--file", help="Run specific test file")
    
    args = parser.parse_args()
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add test directories/files
    test_paths = []
    
    if args.file:
        test_paths.append(args.file)
    elif args.unit:
        test_paths.append("tests/unit/")
    elif args.integration:
        test_paths.append("tests/integration/")
    elif args.performance:
        test_paths.append("tests/performance/")
    elif args.all:
        test_paths.extend(["tests/unit/", "tests/integration/", "tests/performance/"])
    else:
        # Default: run unit and integration tests
        test_paths.extend(["tests/unit/", "tests/integration/"])
    
    pytest_cmd.extend(test_paths)
    
    # Add options
    if args.verbose:
        pytest_cmd.extend(["-v", "-s"])
    
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src/graph_sitter/extensions/lsp/serena",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    if args.html_report:
        pytest_cmd.extend(["--html=test_report.html", "--self-contained-html"])
    
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    if args.markers:
        pytest_cmd.extend(["-m", args.markers])
    
    if args.keyword:
        pytest_cmd.extend(["-k", args.keyword])
    
    # Performance tests need special handling
    if args.performance:
        pytest_cmd.append("--run-performance")
    
    # Add common options
    pytest_cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print("Unified Error Interface Test Runner")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Test paths: {', '.join(test_paths)}")
    print(f"Command: {' '.join(pytest_cmd)}")
    
    # Run the tests
    success = run_command(pytest_cmd, "Running tests")
    
    if success:
        print("\n✅ All tests passed!")
        
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/")
        
        if args.html_report:
            print("\n📄 HTML test report generated: test_report.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


def run_quick_tests():
    """Run a quick subset of tests for development."""
    print("Running quick development tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/unit/extensions/lsp/test_serena_integration.py::TestUnifiedErrorInterfaceUnit::test_unified_error_interface_initialization",
        "tests/integration/test_unified_error_interface.py::TestUnifiedErrorInterface::test_errors_method_basic_functionality",
        "-v", "-s", "--tb=short"
    ]
    
    return run_command(cmd, "Quick development tests")


def run_smoke_tests():
    """Run smoke tests to verify basic functionality."""
    print("Running smoke tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "-k", "test_unified_error_interface_initialization or test_errors_method_basic_functionality or test_add_unified_error_interface_to_codebase",
        "-v", "--tb=short"
    ]
    
    return run_command(cmd, "Smoke tests")


def run_comprehensive_tests():
    """Run comprehensive test suite with coverage."""
    print("Running comprehensive test suite...")
    
    commands = [
        # Unit tests with coverage
        [
            "python", "-m", "pytest",
            "tests/unit/",
            "--cov=src/graph_sitter/extensions/lsp/serena",
            "--cov-report=term-missing",
            "-v"
        ],
        
        # Integration tests
        [
            "python", "-m", "pytest",
            "tests/integration/",
            "-v", "--tb=short"
        ],
        
        # Performance tests (if requested)
        [
            "python", "-m", "pytest",
            "tests/performance/",
            "--run-performance",
            "-v", "--tb=short"
        ]
    ]
    
    all_passed = True
    for i, cmd in enumerate(commands, 1):
        if i == 3:  # Performance tests
            print("\nSkipping performance tests (use --performance to run)")
            continue
            
        success = run_command(cmd, f"Test suite {i}/{len(commands)-1}")
        if not success:
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    # Check if running with special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            success = run_quick_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "smoke":
            success = run_smoke_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "comprehensive":
            success = run_comprehensive_tests()
            sys.exit(0 if success else 1)
    
    # Run main argument parser
    main()

