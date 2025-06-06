"""
CircleCI Extension Test Runner

Comprehensive test runner for the CircleCI extension that validates:
- Unit tests for all components
- Integration tests for workflows
- Configuration validation
- Performance benchmarks
- Example code validation
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pytest
    import coverage
except ImportError:
    print("❌ Required test dependencies not found. Install with:")
    print("   pip install pytest pytest-asyncio coverage")
    sys.exit(1)


class TestRunner:
    """Comprehensive test runner for CircleCI extension"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.src_path = self.base_path / "src"
        self.test_path = self.base_path / "tests"
        self.examples_path = self.base_path / "examples"
        
        self.results = {
            "unit_tests": {"passed": 0, "failed": 0, "errors": []},
            "integration_tests": {"passed": 0, "failed": 0, "errors": []},
            "config_validation": {"passed": 0, "failed": 0, "errors": []},
            "example_validation": {"passed": 0, "failed": 0, "errors": []},
            "coverage": {"percentage": 0.0, "missing_lines": []},
            "performance": {"benchmarks": {}, "issues": []}
        }
    
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title: str):
        """Print formatted section"""
        print(f"\n{'─'*40}")
        print(f"📋 {title}")
        print(f"{'─'*40}")
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Run command and return result"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.base_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.print_section("Checking Dependencies")
        
        required_packages = [
            "pytest",
            "pytest-asyncio", 
            "coverage",
            "aiohttp",
            "pydantic"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"❌ {package}")
        
        if missing:
            print(f"\n⚠️ Missing packages: {', '.join(missing)}")
            print("Install with: pip install " + " ".join(missing))
            return False
        
        return True
    
    def validate_structure(self) -> bool:
        """Validate project structure"""
        self.print_section("Validating Project Structure")
        
        required_paths = [
            "src/contexten/extensions/circleci/__init__.py",
            "src/contexten/extensions/circleci/config.py",
            "src/contexten/extensions/circleci/types.py",
            "src/contexten/extensions/circleci/client.py",
            "src/contexten/extensions/circleci/webhook_processor.py",
            "src/contexten/extensions/circleci/failure_analyzer.py",
            "src/contexten/extensions/circleci/workflow_automation.py",
            "src/contexten/extensions/circleci/integration_agent.py",
            "src/contexten/extensions/circleci/auto_fix_generator.py",
            "tests/unit/extensions/circleci/test_config.py",
            "tests/unit/extensions/circleci/test_webhook_processor.py",
            "tests/integration/circleci/test_e2e_workflow.py",
            "examples/circleci_integration/basic_usage.py",
            "examples/circleci_integration/advanced_usage.py"
        ]
        
        missing = []
        for path in required_paths:
            full_path = self.base_path / path
            if full_path.exists():
                print(f"✅ {path}")
            else:
                missing.append(path)
                print(f"❌ {path}")
        
        if missing:
            print(f"\n⚠️ Missing files: {len(missing)}")
            return False
        
        print(f"\n✅ All required files present")
        return True
    
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        self.print_section("Running Unit Tests")
        
        unit_test_path = self.test_path / "unit" / "extensions" / "circleci"
        
        if not unit_test_path.exists():
            print(f"❌ Unit test directory not found: {unit_test_path}")
            return False
        
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            str(unit_test_path),
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            f"--cov={self.src_path / 'contexten' / 'extensions' / 'circleci'}",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json"
        ]
        
        result = self.run_command(cmd)
        
        if result["success"]:
            print("✅ Unit tests passed")
            self.results["unit_tests"]["passed"] = 1
            
            # Parse coverage
            try:
                with open(self.base_path / "coverage.json") as f:
                    coverage_data = json.load(f)
                    self.results["coverage"]["percentage"] = coverage_data["totals"]["percent_covered"]
                    print(f"📊 Coverage: {self.results['coverage']['percentage']:.1f}%")
            except Exception as e:
                print(f"⚠️ Could not parse coverage: {e}")
            
        else:
            print("❌ Unit tests failed")
            print(result["stderr"])
            self.results["unit_tests"]["failed"] = 1
            self.results["unit_tests"]["errors"].append(result["stderr"])
        
        return result["success"]
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        self.print_section("Running Integration Tests")
        
        integration_test_path = self.test_path / "integration" / "circleci"
        
        if not integration_test_path.exists():
            print(f"❌ Integration test directory not found: {integration_test_path}")
            return False
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(integration_test_path),
            "-v",
            "--tb=short",
            "--asyncio-mode=auto"
        ]
        
        result = self.run_command(cmd)
        
        if result["success"]:
            print("✅ Integration tests passed")
            self.results["integration_tests"]["passed"] = 1
        else:
            print("❌ Integration tests failed")
            print(result["stderr"])
            self.results["integration_tests"]["failed"] = 1
            self.results["integration_tests"]["errors"].append(result["stderr"])
        
        return result["success"]
    
    def validate_configuration(self) -> bool:
        """Validate configuration classes"""
        self.print_section("Validating Configuration")
        
        try:
            from src.contexten.extensions.circleci.config import (
                CircleCIIntegrationConfig, APIConfig, WebhookConfig
            )
            
            # Test basic configuration creation
            api_config = APIConfig(api_token="test-token")
            config = CircleCIIntegrationConfig(api=api_config)
            
            print("✅ Configuration classes import successfully")
            
            # Test validation
            issues = config.validate_configuration()
            print(f"📋 Configuration validation found {len(issues)} issues")
            
            # Test serialization
            config_dict = config.dict()
            print("✅ Configuration serialization works")
            
            # Test environment loading (should fail gracefully)
            try:
                CircleCIIntegrationConfig.from_env()
                print("⚠️ Environment config loaded (unexpected)")
            except ValueError:
                print("✅ Environment config validation works")
            
            self.results["config_validation"]["passed"] = 1
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            self.results["config_validation"]["failed"] = 1
            self.results["config_validation"]["errors"].append(str(e))
            return False
    
    def validate_examples(self) -> bool:
        """Validate example code"""
        self.print_section("Validating Examples")
        
        example_files = [
            self.examples_path / "circleci_integration" / "basic_usage.py",
            self.examples_path / "circleci_integration" / "advanced_usage.py"
        ]
        
        success = True
        
        for example_file in example_files:
            if not example_file.exists():
                print(f"❌ Example file not found: {example_file}")
                success = False
                continue
            
            # Check syntax
            try:
                with open(example_file) as f:
                    compile(f.read(), str(example_file), 'exec')
                print(f"✅ {example_file.name} - syntax valid")
            except SyntaxError as e:
                print(f"❌ {example_file.name} - syntax error: {e}")
                success = False
                self.results["example_validation"]["errors"].append(f"{example_file.name}: {e}")
            
            # Check imports (basic validation)
            try:
                with open(example_file) as f:
                    content = f.read()
                    if "from src.contexten.extensions.circleci" in content:
                        print(f"✅ {example_file.name} - imports look correct")
                    else:
                        print(f"⚠️ {example_file.name} - no CircleCI imports found")
            except Exception as e:
                print(f"❌ {example_file.name} - import check failed: {e}")
        
        if success:
            self.results["example_validation"]["passed"] = 1
        else:
            self.results["example_validation"]["failed"] = 1
        
        return success
    
    def run_performance_benchmarks(self) -> bool:
        """Run basic performance benchmarks"""
        self.print_section("Running Performance Benchmarks")
        
        try:
            from src.contexten.extensions.circleci.webhook_processor import WebhookProcessor
            from src.contexten.extensions.circleci.config import CircleCIIntegrationConfig, APIConfig
            
            # Create test config
            config = CircleCIIntegrationConfig(
                api=APIConfig(api_token="test-token"),
                debug_mode=True
            )
            config.webhook.validate_signatures = False
            
            async def benchmark_webhook_processing():
                """Benchmark webhook processing"""
                processor = WebhookProcessor(config)
                
                # Test payload
                import json
                payload = {
                    "type": "ping",
                    "id": "benchmark-test",
                    "happened_at": "2024-01-01T12:00:00Z"
                }
                
                headers = {"content-type": "application/json"}
                body = json.dumps(payload)
                
                # Benchmark processing time
                start_time = time.time()
                iterations = 100
                
                for _ in range(iterations):
                    result = await processor.process_webhook(headers, body)
                    if not result.success:
                        raise Exception(f"Webhook processing failed: {result.error}")
                
                end_time = time.time()
                total_time = end_time - start_time
                avg_time = total_time / iterations
                
                return {
                    "total_time": total_time,
                    "average_time": avg_time,
                    "iterations": iterations,
                    "throughput": iterations / total_time
                }
            
            # Run benchmark
            benchmark_result = asyncio.run(benchmark_webhook_processing())
            
            print(f"📊 Webhook Processing Benchmark:")
            print(f"   - Iterations: {benchmark_result['iterations']}")
            print(f"   - Total Time: {benchmark_result['total_time']:.3f}s")
            print(f"   - Average Time: {benchmark_result['average_time']*1000:.2f}ms")
            print(f"   - Throughput: {benchmark_result['throughput']:.1f} req/s")
            
            self.results["performance"]["benchmarks"]["webhook_processing"] = benchmark_result
            
            # Performance thresholds
            if benchmark_result['average_time'] > 0.1:  # 100ms threshold
                issue = f"Webhook processing too slow: {benchmark_result['average_time']*1000:.2f}ms"
                self.results["performance"]["issues"].append(issue)
                print(f"⚠️ {issue}")
            else:
                print("✅ Webhook processing performance acceptable")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance benchmarks failed: {e}")
            self.results["performance"]["issues"].append(str(e))
            return False
    
    def check_code_quality(self) -> bool:
        """Check code quality with basic linting"""
        self.print_section("Checking Code Quality")
        
        circleci_path = self.src_path / "contexten" / "extensions" / "circleci"
        
        # Check for basic code quality issues
        issues = []
        
        for py_file in circleci_path.glob("*.py"):
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                    # Basic checks
                    if len(content.split('\n')) > 1000:
                        issues.append(f"{py_file.name}: Very long file ({len(content.split())} lines)")
                    
                    if "TODO" in content:
                        todo_count = content.count("TODO")
                        issues.append(f"{py_file.name}: {todo_count} TODO items")
                    
                    if "print(" in content and "logger" not in content:
                        issues.append(f"{py_file.name}: Uses print() instead of logging")
                    
                    # Check for docstrings
                    if not content.strip().startswith('"""'):
                        issues.append(f"{py_file.name}: Missing module docstring")
                
            except Exception as e:
                issues.append(f"{py_file.name}: Could not analyze - {e}")
        
        if issues:
            print(f"⚠️ Code quality issues found:")
            for issue in issues[:10]:  # Show first 10
                print(f"   - {issue}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more")
        else:
            print("✅ No major code quality issues found")
        
        return len(issues) == 0
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("Test Report Summary")
        
        total_passed = sum(r["passed"] for r in self.results.values() if "passed" in r)
        total_failed = sum(r["failed"] for r in self.results.values() if "failed" in r)
        total_tests = total_passed + total_failed
        
        print(f"📊 Overall Results:")
        print(f"   - Total Tests: {total_tests}")
        print(f"   - Passed: {total_passed} ✅")
        print(f"   - Failed: {total_failed} ❌")
        print(f"   - Success Rate: {(total_passed/total_tests*100) if total_tests > 0 else 0:.1f}%")
        
        if self.results["coverage"]["percentage"] > 0:
            print(f"   - Code Coverage: {self.results['coverage']['percentage']:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        
        sections = [
            ("Unit Tests", self.results["unit_tests"]),
            ("Integration Tests", self.results["integration_tests"]),
            ("Config Validation", self.results["config_validation"]),
            ("Example Validation", self.results["example_validation"])
        ]
        
        for name, result in sections:
            status = "✅" if result["passed"] > 0 else "❌" if result["failed"] > 0 else "⏭️"
            print(f"   {status} {name}: {result['passed']} passed, {result['failed']} failed")
        
        # Performance results
        if self.results["performance"]["benchmarks"]:
            print(f"\n⚡ Performance:")
            for name, benchmark in self.results["performance"]["benchmarks"].items():
                print(f"   - {name}: {benchmark.get('average_time', 0)*1000:.2f}ms avg")
        
        # Issues summary
        all_errors = []
        for result in self.results.values():
            if "errors" in result:
                all_errors.extend(result["errors"])
        
        if self.results["performance"]["issues"]:
            all_errors.extend(self.results["performance"]["issues"])
        
        if all_errors:
            print(f"\n⚠️ Issues Found ({len(all_errors)}):")
            for error in all_errors[:5]:  # Show first 5
                print(f"   - {error}")
            if len(all_errors) > 5:
                print(f"   ... and {len(all_errors) - 5} more")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if self.results["coverage"]["percentage"] < 80:
            print("   - Increase test coverage (target: 80%+)")
        
        if self.results["performance"]["issues"]:
            print("   - Address performance issues")
        
        if total_failed > 0:
            print("   - Fix failing tests before deployment")
        
        if all_errors:
            print("   - Review and resolve identified issues")
        
        print("   - Run tests regularly during development")
        print("   - Consider adding more integration tests")
        print("   - Set up continuous integration")
        
        return total_failed == 0 and len(self.results["performance"]["issues"]) == 0
    
    def run_all_tests(self) -> bool:
        """Run all tests and validations"""
        self.print_header("CircleCI Extension Test Suite")
        
        print("🚀 Starting comprehensive test suite...")
        print(f"📁 Base Path: {self.base_path}")
        print(f"📁 Source Path: {self.src_path}")
        print(f"📁 Test Path: {self.test_path}")
        
        # Check dependencies first
        if not self.check_dependencies():
            print("❌ Dependencies check failed")
            return False
        
        # Validate project structure
        if not self.validate_structure():
            print("❌ Project structure validation failed")
            return False
        
        # Run all test categories
        test_functions = [
            ("Configuration Validation", self.validate_configuration),
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Example Validation", self.validate_examples),
            ("Performance Benchmarks", self.run_performance_benchmarks),
            ("Code Quality Check", self.check_code_quality)
        ]
        
        overall_success = True
        
        for name, test_func in test_functions:
            try:
                print(f"\n🔄 Running {name}...")
                success = test_func()
                if not success:
                    overall_success = False
                    print(f"❌ {name} failed")
                else:
                    print(f"✅ {name} passed")
            except Exception as e:
                print(f"❌ {name} crashed: {e}")
                overall_success = False
        
        # Generate final report
        report_success = self.generate_report()
        
        return overall_success and report_success


def main():
    """Main test runner entry point"""
    runner = TestRunner()
    
    try:
        success = runner.run_all_tests()
        
        if success:
            print(f"\n🎉 All tests passed! CircleCI extension is ready for deployment.")
            sys.exit(0)
        else:
            print(f"\n❌ Some tests failed. Please review and fix issues before deployment.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

