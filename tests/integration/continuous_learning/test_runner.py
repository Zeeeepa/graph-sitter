"""
Comprehensive Integration Test Runner

This module provides a unified test runner for all continuous learning
integration tests as specified in ZAM-1053.
"""

import asyncio
import pytest
import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from pathlib import Path
import argparse
import sys

from .test_config import TestConfig
from .test_integration_framework import IntegrationTestSuite
from .test_performance_benchmark import PerformanceBenchmark
from .test_workflow_suite import WorkflowTestSuite
from .test_production_readiness import ProductionReadinessTest

logger = logging.getLogger(__name__)


class ContinuousLearningTestRunner:
    """
    Comprehensive test runner for all continuous learning integration tests.
    
    This class orchestrates the execution of all test suites and provides
    comprehensive reporting and validation against success criteria.
    """
    
    def __init__(self, test_config: TestConfig):
        """Initialize the test runner."""
        self.config = test_config
        self.results = {
            "integration_tests": {},
            "performance_benchmarks": {},
            "workflow_tests": {},
            "production_readiness": {},
            "overall_summary": {}
        }
        
        # Test suite instances
        self.integration_suite = IntegrationTestSuite(test_config)
        self.performance_benchmark = PerformanceBenchmark(test_config)
        self.workflow_suite = WorkflowTestSuite(test_config)
        self.production_readiness = ProductionReadinessTest(test_config)
        
        logger.info("Initialized ContinuousLearningTestRunner")
    
    def setup_test_environment(self, integration_test_environment: Dict[str, Any]):
        """Setup test environment for all test suites."""
        self.integration_suite.setup_test_environment(integration_test_environment)
        self.performance_benchmark.setup_test_environment(integration_test_environment)
        self.workflow_suite.setup_test_environment(integration_test_environment)
        self.production_readiness.setup_test_environment(integration_test_environment)
        
        logger.info("Test environment setup completed for all suites")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all continuous learning integration tests.
        
        Returns comprehensive results including success criteria validation.
        """
        start_time = time.time()
        
        logger.info("Starting comprehensive continuous learning integration tests")
        
        try:
            # Phase 1: Integration Tests
            logger.info("Phase 1: Running Integration Tests")
            await self._run_integration_tests()
            
            # Phase 2: Performance Benchmarks
            logger.info("Phase 2: Running Performance Benchmarks")
            await self._run_performance_benchmarks()
            
            # Phase 3: Workflow Tests
            logger.info("Phase 3: Running Workflow Tests")
            await self._run_workflow_tests()
            
            # Phase 4: Production Readiness Tests
            logger.info("Phase 4: Running Production Readiness Tests")
            await self._run_production_readiness_tests()
            
            # Generate comprehensive summary
            total_duration = time.time() - start_time
            self.results["overall_summary"] = self._generate_overall_summary(total_duration)
            
            # Validate success criteria
            success_validation = self._validate_success_criteria()
            self.results["success_criteria_validation"] = success_validation
            
            logger.info(f"All tests completed in {total_duration:.2f}s")
            
            return self.results
            
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            raise
    
    async def _run_integration_tests(self):
        """Run integration test suite."""
        try:
            # Run all integration tests
            openevolve_result = await self.integration_suite.test_openevolve_integration()
            self_healing_result = await self.integration_suite.test_self_healing_workflow()
            pattern_analysis_result = await self.integration_suite.test_pattern_analysis_pipeline()
            cross_component_result = await self.integration_suite.test_cross_component_integration()
            
            # Get comprehensive summary
            integration_summary = self.integration_suite.get_test_summary()
            
            self.results["integration_tests"] = {
                "openevolve_integration": asdict(openevolve_result),
                "self_healing_workflow": asdict(self_healing_result),
                "pattern_analysis_pipeline": asdict(pattern_analysis_result),
                "cross_component_integration": asdict(cross_component_result),
                "summary": integration_summary
            }
            
            logger.info(f"Integration tests completed: {integration_summary['success_rate']:.2%} success rate")
            
        except Exception as e:
            logger.error(f"Integration tests failed: {str(e)}")
            self.results["integration_tests"] = {"error": str(e)}
    
    async def _run_performance_benchmarks(self):
        """Run performance benchmark suite."""
        try:
            # Run comprehensive performance benchmarks
            system_benchmark = await self.performance_benchmark.benchmark_system_performance()
            
            self.results["performance_benchmarks"] = {
                "system_benchmark": system_benchmark,
                "load_test_results": [asdict(r) for r in self.performance_benchmark.load_test_results],
                "stress_test_results": [asdict(r) for r in self.performance_benchmark.stress_test_results]
            }
            
            logger.info("Performance benchmarks completed")
            
        except Exception as e:
            logger.error(f"Performance benchmarks failed: {str(e)}")
            self.results["performance_benchmarks"] = {"error": str(e)}
    
    async def _run_workflow_tests(self):
        """Run workflow test suite."""
        try:
            # Run all workflow tests
            error_to_improvement = await self.workflow_suite.test_error_to_improvement_workflow()
            pattern_to_optimization = await self.workflow_suite.test_pattern_to_optimization_workflow()
            learning_effectiveness = await self.workflow_suite.test_learning_effectiveness()
            full_system_cycle = await self.workflow_suite.test_full_system_cycle()
            
            # Get workflow summary
            workflow_summary = self.workflow_suite.get_workflow_summary()
            
            self.results["workflow_tests"] = {
                "error_to_improvement": asdict(error_to_improvement),
                "pattern_to_optimization": asdict(pattern_to_optimization),
                "learning_effectiveness": asdict(learning_effectiveness),
                "full_system_cycle": asdict(full_system_cycle),
                "summary": workflow_summary
            }
            
            logger.info(f"Workflow tests completed: {workflow_summary['overall_success_rate']:.2%} success rate")
            
        except Exception as e:
            logger.error(f"Workflow tests failed: {str(e)}")
            self.results["workflow_tests"] = {"error": str(e)}
    
    async def _run_production_readiness_tests(self):
        """Run production readiness test suite."""
        try:
            # Run all production readiness tests
            deployment_results = await self.production_readiness.test_deployment_procedures()
            monitoring_results = await self.production_readiness.test_monitoring_and_alerting()
            backup_results = await self.production_readiness.test_disaster_recovery()
            security_results = await self.production_readiness.test_security_compliance()
            scalability_results = await self.production_readiness.test_scalability_limits()
            
            # Get production readiness summary
            readiness_summary = self.production_readiness.get_production_readiness_summary()
            
            self.results["production_readiness"] = {
                "deployment_procedures": [asdict(r) for r in deployment_results],
                "monitoring_and_alerting": [asdict(r) for r in monitoring_results],
                "disaster_recovery": [asdict(r) for r in backup_results],
                "security_compliance": [asdict(r) for r in security_results],
                "scalability_limits": scalability_results,
                "summary": readiness_summary
            }
            
            logger.info(f"Production readiness tests completed: {readiness_summary['overall_readiness_score']:.2%} readiness score")
            
        except Exception as e:
            logger.error(f"Production readiness tests failed: {str(e)}")
            self.results["production_readiness"] = {"error": str(e)}
    
    def _generate_overall_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate overall test summary."""
        summary = {
            "total_duration": total_duration,
            "timestamp": str(int(time.time())),
            "test_phases_completed": 0,
            "test_phases_failed": 0,
            "overall_success": False
        }
        
        # Count completed and failed phases
        phases = ["integration_tests", "performance_benchmarks", "workflow_tests", "production_readiness"]
        
        for phase in phases:
            if phase in self.results and "error" not in self.results[phase]:
                summary["test_phases_completed"] += 1
            else:
                summary["test_phases_failed"] += 1
        
        # Calculate overall success
        summary["overall_success"] = summary["test_phases_failed"] == 0
        
        # Add detailed metrics
        if "integration_tests" in self.results and "summary" in self.results["integration_tests"]:
            summary["integration_success_rate"] = self.results["integration_tests"]["summary"].get("success_rate", 0)
        
        if "workflow_tests" in self.results and "summary" in self.results["workflow_tests"]:
            summary["workflow_success_rate"] = self.results["workflow_tests"]["summary"].get("overall_success_rate", 0)
        
        if "production_readiness" in self.results and "summary" in self.results["production_readiness"]:
            summary["production_readiness_score"] = self.results["production_readiness"]["summary"].get("overall_readiness_score", 0)
        
        return summary
    
    def _validate_success_criteria(self) -> Dict[str, bool]:
        """
        Validate against success criteria from ZAM-1053.
        
        Success Criteria:
        - All integration tests pass with >95% success rate
        - System performance meets or exceeds baseline requirements
        - Continuous learning demonstrates measurable improvements over 30-day period
        - Error detection and recovery achieves <5 minute MTTR for common issues
        - Pattern analysis provides actionable recommendations with >80% accuracy
        - System handles 1000+ concurrent users with <2 second response times
        """
        validation = {}
        
        # Integration tests success rate >95%
        integration_success_rate = 0
        if "integration_tests" in self.results and "summary" in self.results["integration_tests"]:
            integration_success_rate = self.results["integration_tests"]["summary"].get("success_rate", 0)
        validation["integration_tests_95_percent"] = integration_success_rate >= 0.95
        
        # System performance meets baseline requirements
        performance_meets_baseline = False
        if "performance_benchmarks" in self.results and "system_benchmark" in self.results["performance_benchmarks"]:
            # Check if performance validation passed
            perf_validation = self.results["performance_benchmarks"]["system_benchmark"].get("performance_validation", {})
            performance_meets_baseline = all(perf_validation.values()) if perf_validation else False
        validation["performance_meets_baseline"] = performance_meets_baseline
        
        # Error detection and recovery MTTR <5 minutes (300 seconds)
        mttr_under_5_minutes = False
        if "workflow_tests" in self.results and "error_to_improvement" in self.results["workflow_tests"]:
            error_workflow = self.results["workflow_tests"]["error_to_improvement"]
            mttr = error_workflow.get("performance_metrics", {}).get("total_mttr", 999)
            mttr_under_5_minutes = mttr <= 300
        validation["mttr_under_5_minutes"] = mttr_under_5_minutes
        
        # Pattern analysis accuracy >80%
        pattern_analysis_accuracy = False
        if "integration_tests" in self.results and "pattern_analysis_pipeline" in self.results["integration_tests"]:
            pattern_result = self.results["integration_tests"]["pattern_analysis_pipeline"]
            accuracy = pattern_result.get("metrics", {}).get("prediction_accuracy", 0)
            pattern_analysis_accuracy = accuracy >= 0.80
        validation["pattern_analysis_80_percent_accuracy"] = pattern_analysis_accuracy
        
        # System handles 1000+ concurrent users with <2s response times
        handles_1000_users = False
        if "performance_benchmarks" in self.results and "load_test_results" in self.results["performance_benchmarks"]:
            load_results = self.results["performance_benchmarks"]["load_test_results"]
            for result in load_results:
                if result.get("concurrent_users", 0) >= 1000:
                    if result.get("p95_response_time", 9999) <= 2000:  # 2 seconds in milliseconds
                        handles_1000_users = True
                        break
        validation["handles_1000_users_2s_response"] = handles_1000_users
        
        # Production readiness
        production_ready = False
        if "production_readiness" in self.results and "summary" in self.results["production_readiness"]:
            readiness_score = self.results["production_readiness"]["summary"].get("overall_readiness_score", 0)
            production_ready = readiness_score >= 0.90
        validation["production_ready"] = production_ready
        
        # Overall success (all criteria met)
        validation["all_criteria_met"] = all(validation.values())
        
        return validation
    
    def save_results(self, output_file: Optional[str] = None):
        """Save test results to file."""
        if output_file is None:
            output_file = f"continuous_learning_test_results_{int(time.time())}.json"
        
        output_path = Path(output_file)
        
        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Test results saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
    
    def print_summary(self):
        """Print test summary to console."""
        print("\n" + "="*80)
        print("CONTINUOUS LEARNING INTEGRATION TEST SUMMARY")
        print("="*80)
        
        overall = self.results.get("overall_summary", {})
        
        print(f"Total Duration: {overall.get('total_duration', 0):.2f} seconds")
        print(f"Test Phases Completed: {overall.get('test_phases_completed', 0)}/4")
        print(f"Overall Success: {'✅ PASS' if overall.get('overall_success', False) else '❌ FAIL'}")
        
        print("\n" + "-"*40)
        print("SUCCESS CRITERIA VALIDATION")
        print("-"*40)
        
        validation = self.results.get("success_criteria_validation", {})
        
        criteria = [
            ("Integration tests >95% success rate", "integration_tests_95_percent"),
            ("Performance meets baseline", "performance_meets_baseline"),
            ("MTTR <5 minutes", "mttr_under_5_minutes"),
            ("Pattern analysis >80% accuracy", "pattern_analysis_80_percent_accuracy"),
            ("Handles 1000+ users <2s response", "handles_1000_users_2s_response"),
            ("Production ready", "production_ready")
        ]
        
        for description, key in criteria:
            status = "✅ PASS" if validation.get(key, False) else "❌ FAIL"
            print(f"{description}: {status}")
        
        print(f"\nAll Criteria Met: {'✅ PASS' if validation.get('all_criteria_met', False) else '❌ FAIL'}")
        
        print("\n" + "="*80)


async def main():
    """Main function for running tests from command line."""
    parser = argparse.ArgumentParser(description="Run Continuous Learning Integration Tests")
    parser.add_argument("--config", help="Path to test configuration file")
    parser.add_argument("--output", help="Output file for test results")
    parser.add_argument("--concurrent-users", type=int, default=100, help="Number of concurrent users for load testing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create test configuration
    config = TestConfig(concurrent_users=args.concurrent_users)
    
    # Create test runner
    test_runner = ContinuousLearningTestRunner(config)
    
    # Setup mock test environment (in real implementation, this would be actual services)
    from .conftest import (
        mock_database, mock_openevolve_client, mock_self_healing_system,
        mock_pattern_analysis_engine, test_data_directory
    )
    
    # Note: In a real implementation, you would setup actual test environment
    # For now, we'll use a simplified mock environment
    mock_env = {
        "config": config,
        "database": None,  # Would be actual database connection
        "openevolve_client": None,  # Would be actual OpenEvolve client
        "self_healing_system": None,  # Would be actual self-healing system
        "pattern_analysis_engine": None,  # Would be actual pattern analysis engine
        "test_data_dir": Path("/tmp/test_data")  # Would be actual test data directory
    }
    
    test_runner.setup_test_environment(mock_env)
    
    try:
        # Run all tests
        results = await test_runner.run_all_tests()
        
        # Print summary
        test_runner.print_summary()
        
        # Save results
        test_runner.save_results(args.output)
        
        # Exit with appropriate code
        success = results.get("success_criteria_validation", {}).get("all_criteria_met", False)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

