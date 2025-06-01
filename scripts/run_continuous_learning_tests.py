#!/usr/bin/env python3
"""
Script to run continuous learning integration tests.

This script provides a convenient way to run the comprehensive integration
testing framework for the continuous learning system.
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.continuous_learning.test_runner import ContinuousLearningTestRunner
from tests.integration.continuous_learning.test_config import TestConfig


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('continuous_learning_tests.log')
        ]
    )


async def run_tests(args):
    """Run the continuous learning integration tests."""
    # Create test configuration
    config = TestConfig(
        concurrent_users=args.concurrent_users,
        test_duration=args.test_duration,
        response_time_p95=args.response_time_target
    )
    
    # Create test runner
    test_runner = ContinuousLearningTestRunner(config)
    
    # Setup mock test environment
    # Note: In a real implementation, this would connect to actual services
    mock_env = {
        "config": config,
        "database": None,
        "openevolve_client": None,
        "self_healing_system": None,
        "pattern_analysis_engine": None,
        "test_data_dir": Path("/tmp/continuous_learning_test_data")
    }
    
    test_runner.setup_test_environment(mock_env)
    
    try:
        print("🚀 Starting Continuous Learning Integration Tests")
        print(f"   Concurrent Users: {config.concurrent_users}")
        print(f"   Test Duration: {config.test_duration}")
        print(f"   Response Time Target: {config.response_time_p95}ms")
        print("-" * 60)
        
        # Run all tests
        results = await test_runner.run_all_tests()
        
        # Print summary
        test_runner.print_summary()
        
        # Save results if requested
        if args.output:
            test_runner.save_results(args.output)
            print(f"\n📄 Results saved to: {args.output}")
        
        # Check if all success criteria were met
        success = results.get("success_criteria_validation", {}).get("all_criteria_met", False)
        
        if success:
            print("\n🎉 All tests passed! System is ready for production.")
            return 0
        else:
            print("\n❌ Some tests failed. Review the results and address issues.")
            return 1
            
    except Exception as e:
        logging.error(f"Test execution failed: {str(e)}")
        print(f"\n💥 Test execution failed: {str(e)}")
        return 1


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run Continuous Learning Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python scripts/run_continuous_learning_tests.py
  
  # Run with custom load testing parameters
  python scripts/run_continuous_learning_tests.py --concurrent-users 500 --test-duration 1800
  
  # Run with verbose logging and save results
  python scripts/run_continuous_learning_tests.py --verbose --output results.json
  
  # Run quick test for development
  python scripts/run_continuous_learning_tests.py --concurrent-users 10 --test-duration 300
        """
    )
    
    parser.add_argument(
        "--concurrent-users",
        type=int,
        default=100,
        help="Number of concurrent users for load testing (default: 100)"
    )
    
    parser.add_argument(
        "--test-duration",
        type=int,
        default=300,
        help="Test duration in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--response-time-target",
        type=int,
        default=2000,
        help="Response time target in milliseconds (default: 2000)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for test results (JSON format)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with reduced parameters for development"
    )
    
    args = parser.parse_args()
    
    # Apply quick test settings
    if args.quick:
        args.concurrent_users = 10
        args.test_duration = 60
        args.response_time_target = 5000
        print("🏃 Running quick test mode (reduced parameters for development)")
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Run tests
    exit_code = asyncio.run(run_tests(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

