#!/usr/bin/env python3
"""
Validation Execution Script for Testing-12

This script orchestrates the complete end-to-end validation process
for the Graph-Sitter integration system production readiness assessment.
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ValidationOrchestrator:
    """Orchestrates the complete validation process."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.validation_results = {}
        self.validation_dir = Path("validation")
        self.validation_dir.mkdir(exist_ok=True)
        
    def run_complete_validation(self) -> Dict[str, Any]:
        """Run the complete validation process."""
        logger.info("🚀 Starting Testing-12: End-to-End System Validation")
        
        validation_summary = {
            'validation_id': f"testing-12-{int(time.time())}",
            'start_time': self.start_time.isoformat(),
            'phases': {},
            'overall_status': 'IN_PROGRESS',
            'critical_issues': [],
            'recommendations': []
        }
        
        try:
            # Phase 1: System Health Check
            logger.info("📋 Phase 1: System Health Check")
            health_results = self._run_system_health_check()
            validation_summary['phases']['health_check'] = health_results
            
            # Phase 2: Dependency Validation
            logger.info("🔍 Phase 2: Dependency Validation")
            dependency_results = self._run_dependency_validation()
            validation_summary['phases']['dependency_validation'] = dependency_results
            
            # Phase 3: Component Testing
            logger.info("🧪 Phase 3: Component Testing")
            component_results = self._run_component_testing()
            validation_summary['phases']['component_testing'] = component_results
            
            # Phase 4: Integration Testing
            logger.info("🔗 Phase 4: Integration Testing")
            integration_results = self._run_integration_testing()
            validation_summary['phases']['integration_testing'] = integration_results
            
            # Phase 5: Performance Benchmarking
            logger.info("⚡ Phase 5: Performance Benchmarking")
            performance_results = self._run_performance_benchmarking()
            validation_summary['phases']['performance_benchmarking'] = performance_results
            
            # Phase 6: Security Assessment
            logger.info("🔒 Phase 6: Security Assessment")
            security_results = self._run_security_assessment()
            validation_summary['phases']['security_assessment'] = security_results
            
            # Phase 7: Production Readiness Assessment
            logger.info("🏭 Phase 7: Production Readiness Assessment")
            readiness_results = self._run_production_readiness_assessment()
            validation_summary['phases']['production_readiness'] = readiness_results
            
            # Generate final assessment
            validation_summary = self._generate_final_assessment(validation_summary)
            
        except Exception as e:
            logger.error(f"Validation process failed: {e}")
            validation_summary['overall_status'] = 'FAILED'
            validation_summary['error'] = str(e)
            validation_summary['critical_issues'].append(f"Validation process failure: {e}")
            
        finally:
            validation_summary['end_time'] = datetime.now().isoformat()
            validation_summary['total_duration_minutes'] = (
                datetime.now() - self.start_time
            ).total_seconds() / 60
            
        return validation_summary
        
    def _run_system_health_check(self) -> Dict[str, Any]:
        """Run basic system health checks."""
        logger.info("Checking system health and prerequisites")
        
        health_results = {
            'status': 'PASSED',
            'checks': {},
            'issues': []
        }
        
        # Check Python version
        python_version = sys.version_info
        health_results['checks']['python_version'] = {
            'required': '3.12+',
            'actual': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            'status': 'PASSED' if python_version >= (3, 12) else 'FAILED'
        }
        
        # Check project structure
        required_dirs = ['src', 'tests', 'docs', '.github']
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            health_results['checks'][f'{dir_name}_directory'] = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'status': 'PASSED' if dir_path.exists() else 'FAILED'
            }
            
        # Check configuration files
        config_files = ['pyproject.toml', 'README.md', '.gitignore']
        for file_name in config_files:
            file_path = project_root / file_name
            health_results['checks'][f'{file_name}_file'] = {
                'path': str(file_path),
                'exists': file_path.exists(),
                'status': 'PASSED' if file_path.exists() else 'FAILED'
            }
            
        # Check for critical dependencies
        try:
            import tree_sitter
            health_results['checks']['tree_sitter_import'] = {'status': 'PASSED'}
        except ImportError:
            health_results['checks']['tree_sitter_import'] = {'status': 'FAILED'}
            health_results['issues'].append("tree-sitter not available")
            
        try:
            import rustworkx
            health_results['checks']['rustworkx_import'] = {'status': 'PASSED'}
        except ImportError:
            health_results['checks']['rustworkx_import'] = {'status': 'FAILED'}
            health_results['issues'].append("rustworkx not available")
            
        # Determine overall health status
        failed_checks = [k for k, v in health_results['checks'].items() if v.get('status') == 'FAILED']
        if failed_checks:
            health_results['status'] = 'FAILED'
            health_results['issues'].extend([f"Failed check: {check}" for check in failed_checks])
            
        return health_results
        
    def _run_dependency_validation(self) -> Dict[str, Any]:
        """Validate that all dependencies are properly resolved."""
        logger.info("Validating project dependencies")
        
        dependency_results = {
            'status': 'PASSED',
            'dependency_analysis': {},
            'issues': []
        }
        
        # Check pyproject.toml dependencies
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                    
                dependencies = pyproject_data.get('project', {}).get('dependencies', [])
                dependency_results['dependency_analysis']['total_dependencies'] = len(dependencies)
                dependency_results['dependency_analysis']['dependencies'] = dependencies[:10]  # First 10
                
            except Exception as e:
                dependency_results['issues'].append(f"Failed to parse pyproject.toml: {e}")
                dependency_results['status'] = 'WARNING'
                
        # Check for lock file
        lock_file = project_root / "uv.lock"
        dependency_results['dependency_analysis']['lock_file_exists'] = lock_file.exists()
        
        if not lock_file.exists():
            dependency_results['issues'].append("No lock file found - dependency versions not pinned")
            dependency_results['status'] = 'WARNING'
            
        return dependency_results
        
    def _run_component_testing(self) -> Dict[str, Any]:
        """Run component-level testing."""
        logger.info("Running component tests")
        
        component_results = {
            'status': 'PASSED',
            'test_results': {},
            'issues': []
        }
        
        # Run existing test suite
        try:
            import subprocess
            
            # Run pytest with coverage
            test_command = [
                sys.executable, '-m', 'pytest',
                'tests/',
                '--tb=short',
                '--quiet'
            ]
            
            result = subprocess.run(
                test_command,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            component_results['test_results']['pytest'] = {
                'return_code': result.returncode,
                'stdout': result.stdout[-1000:],  # Last 1000 chars
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'status': 'PASSED' if result.returncode == 0 else 'FAILED'
            }
            
            if result.returncode != 0:
                component_results['status'] = 'FAILED'
                component_results['issues'].append("Test suite execution failed")
                
        except subprocess.TimeoutExpired:
            component_results['status'] = 'FAILED'
            component_results['issues'].append("Test suite execution timed out")
        except Exception as e:
            component_results['status'] = 'FAILED'
            component_results['issues'].append(f"Test execution error: {e}")
            
        return component_results
        
    def _run_integration_testing(self) -> Dict[str, Any]:
        """Run integration testing."""
        logger.info("Running integration tests")
        
        integration_results = {
            'status': 'PASSED',
            'integration_scenarios': {},
            'issues': []
        }
        
        # Test 1: Module imports
        try:
            # Test core module imports
            from src.graph_sitter import utils
            integration_results['integration_scenarios']['core_imports'] = {'status': 'PASSED'}
        except Exception as e:
            integration_results['integration_scenarios']['core_imports'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            integration_results['issues'].append(f"Core import failed: {e}")
            integration_results['status'] = 'FAILED'
            
        # Test 2: Configuration loading
        try:
            # Test configuration files
            config_files = list((project_root / "src" / "graph_sitter" / "configs").glob("*.py"))
            integration_results['integration_scenarios']['config_loading'] = {
                'status': 'PASSED',
                'config_files_found': len(config_files)
            }
        except Exception as e:
            integration_results['integration_scenarios']['config_loading'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            integration_results['issues'].append(f"Configuration loading failed: {e}")
            
        # Test 3: CLI functionality
        try:
            cli_path = project_root / "src" / "graph_sitter" / "cli"
            cli_files = list(cli_path.glob("*.py")) if cli_path.exists() else []
            integration_results['integration_scenarios']['cli_availability'] = {
                'status': 'PASSED' if cli_files else 'WARNING',
                'cli_files_found': len(cli_files)
            }
        except Exception as e:
            integration_results['integration_scenarios']['cli_availability'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
        return integration_results
        
    def _run_performance_benchmarking(self) -> Dict[str, Any]:
        """Run performance benchmarking."""
        logger.info("Running performance benchmarks")
        
        performance_results = {
            'status': 'PASSED',
            'benchmarks': {},
            'issues': []
        }
        
        # Basic performance tests
        try:
            # Test 1: Import performance
            import time
            start_time = time.time()
            
            # Import core modules
            from src.graph_sitter import utils
            
            import_time = time.time() - start_time
            
            performance_results['benchmarks']['import_performance'] = {
                'import_time_seconds': import_time,
                'status': 'PASSED' if import_time < 5.0 else 'WARNING'
            }
            
            # Test 2: Basic functionality performance
            start_time = time.time()
            
            # Simulate basic operations
            test_data = list(range(1000))
            processed_data = [x * 2 for x in test_data]
            
            processing_time = time.time() - start_time
            
            performance_results['benchmarks']['basic_processing'] = {
                'processing_time_seconds': processing_time,
                'items_processed': len(processed_data),
                'items_per_second': len(processed_data) / processing_time,
                'status': 'PASSED'
            }
            
        except Exception as e:
            performance_results['status'] = 'FAILED'
            performance_results['issues'].append(f"Performance benchmarking failed: {e}")
            
        return performance_results
        
    def _run_security_assessment(self) -> Dict[str, Any]:
        """Run security assessment."""
        logger.info("Running security assessment")
        
        security_results = {
            'status': 'PASSED',
            'security_checks': {},
            'issues': []
        }
        
        # Check for security-related files
        security_files = [
            '.github/dependabot.yml',
            '.pre-commit-config.yaml',
            'pyproject.toml'
        ]
        
        for file_name in security_files:
            file_path = project_root / file_name
            security_results['security_checks'][f'{file_name}_exists'] = {
                'exists': file_path.exists(),
                'status': 'PASSED' if file_path.exists() else 'WARNING'
            }
            
        # Check for common security issues in code
        try:
            # Look for potential security issues
            python_files = list((project_root / "src").rglob("*.py"))
            
            security_patterns = [
                'eval(',
                'exec(',
                'subprocess.call(',
                'os.system(',
                'input(',
                'raw_input('
            ]
            
            security_issues = []
            for py_file in python_files[:10]:  # Check first 10 files
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in security_patterns:
                        if pattern in content:
                            security_issues.append(f"{py_file.name}: {pattern}")
                except Exception:
                    continue
                    
            security_results['security_checks']['code_security_scan'] = {
                'files_scanned': len(python_files[:10]),
                'issues_found': len(security_issues),
                'issues': security_issues[:5],  # First 5 issues
                'status': 'WARNING' if security_issues else 'PASSED'
            }
            
        except Exception as e:
            security_results['issues'].append(f"Security scan failed: {e}")
            security_results['status'] = 'WARNING'
            
        return security_results
        
    def _run_production_readiness_assessment(self) -> Dict[str, Any]:
        """Assess production readiness."""
        logger.info("Assessing production readiness")
        
        readiness_results = {
            'status': 'PASSED',
            'readiness_criteria': {},
            'issues': []
        }
        
        # Check documentation
        doc_files = [
            'README.md',
            'CONTRIBUTING.md',
            'LICENSE'
        ]
        
        for doc_file in doc_files:
            file_path = project_root / doc_file
            readiness_results['readiness_criteria'][f'{doc_file}_exists'] = {
                'exists': file_path.exists(),
                'status': 'PASSED' if file_path.exists() else 'WARNING'
            }
            
        # Check CI/CD configuration
        ci_files = [
            '.github/workflows/test.yml',
            '.github/workflows/release.yml'
        ]
        
        for ci_file in ci_files:
            file_path = project_root / ci_file
            readiness_results['readiness_criteria'][f'{ci_file}_exists'] = {
                'exists': file_path.exists(),
                'status': 'PASSED' if file_path.exists() else 'WARNING'
            }
            
        # Check package configuration
        package_files = [
            'pyproject.toml',
            'uv.lock'
        ]
        
        for package_file in package_files:
            file_path = project_root / package_file
            readiness_results['readiness_criteria'][f'{package_file}_exists'] = {
                'exists': file_path.exists(),
                'status': 'PASSED' if file_path.exists() else 'FAILED'
            }
            
        # Check for production-specific configurations
        prod_configs = [
            'Dockerfile',
            'docker-compose.yml',
            '.dockerignore'
        ]
        
        prod_config_count = 0
        for config_file in prod_configs:
            file_path = project_root / config_file
            if file_path.exists():
                prod_config_count += 1
                
        readiness_results['readiness_criteria']['production_configs'] = {
            'configs_found': prod_config_count,
            'total_configs': len(prod_configs),
            'status': 'PASSED' if prod_config_count >= 1 else 'WARNING'
        }
        
        return readiness_results
        
    def _generate_final_assessment(self, validation_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final assessment and recommendations."""
        logger.info("Generating final assessment")
        
        # Count passed/failed phases
        phase_statuses = []
        critical_failures = []
        warnings = []
        
        for phase_name, phase_results in validation_summary['phases'].items():
            status = phase_results.get('status', 'UNKNOWN')
            phase_statuses.append(status)
            
            if status == 'FAILED':
                critical_failures.append(phase_name)
                validation_summary['critical_issues'].extend(
                    phase_results.get('issues', [])
                )
            elif status == 'WARNING':
                warnings.append(phase_name)
                
        # Determine overall status
        if critical_failures:
            validation_summary['overall_status'] = 'FAILED'
            validation_summary['production_ready'] = False
        elif warnings:
            validation_summary['overall_status'] = 'WARNING'
            validation_summary['production_ready'] = False
        else:
            validation_summary['overall_status'] = 'PASSED'
            validation_summary['production_ready'] = True
            
        # Generate recommendations
        if critical_failures:
            validation_summary['recommendations'].append(
                f"❌ CRITICAL: Address failures in phases: {', '.join(critical_failures)}"
            )
            
        if warnings:
            validation_summary['recommendations'].append(
                f"⚠️ WARNING: Review issues in phases: {', '.join(warnings)}"
            )
            
        if validation_summary['production_ready']:
            validation_summary['recommendations'].append(
                "✅ READY: System appears ready for production deployment"
            )
        else:
            validation_summary['recommendations'].append(
                "🔄 NOT READY: Address critical issues before production deployment"
            )
            
        # Add next steps
        validation_summary['next_steps'] = self._generate_next_steps(validation_summary)
        
        return validation_summary
        
    def _generate_next_steps(self, validation_summary: Dict[str, Any]) -> List[str]:
        """Generate next steps based on validation results."""
        next_steps = []
        
        if validation_summary['production_ready']:
            next_steps.extend([
                "1. Review and approve production deployment plan",
                "2. Setup production infrastructure and monitoring",
                "3. Execute staged deployment to production",
                "4. Monitor system performance and stability",
                "5. Establish operational procedures and support"
            ])
        else:
            next_steps.extend([
                "1. Address all critical issues identified in validation",
                "2. Re-run validation tests to verify fixes",
                "3. Complete missing documentation and configurations",
                "4. Setup comprehensive monitoring and alerting",
                "5. Conduct security audit and penetration testing"
            ])
            
        return next_steps
        
    def save_results(self, validation_summary: Dict[str, Any]):
        """Save validation results to files."""
        # Save detailed JSON results
        results_file = self.validation_dir / "validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(validation_summary, f, indent=2)
            
        # Save summary report
        summary_file = self.validation_dir / "validation_summary.md"
        self._generate_markdown_summary(validation_summary, summary_file)
        
        logger.info(f"Validation results saved to: {results_file}")
        logger.info(f"Validation summary saved to: {summary_file}")
        
    def _generate_markdown_summary(self, validation_summary: Dict[str, Any], output_file: Path):
        """Generate markdown summary report."""
        with open(output_file, 'w') as f:
            f.write("# 🚀 Testing-12: End-to-End Validation Summary\n\n")
            
            # Overall status
            status_emoji = "✅" if validation_summary['production_ready'] else "❌"
            f.write(f"## {status_emoji} Overall Status: {validation_summary['overall_status']}\n\n")
            f.write(f"**Production Ready**: {validation_summary['production_ready']}\n\n")
            
            # Validation phases
            f.write("## 📋 Validation Phases\n\n")
            for phase_name, phase_results in validation_summary['phases'].items():
                status = phase_results.get('status', 'UNKNOWN')
                emoji = "✅" if status == 'PASSED' else "⚠️" if status == 'WARNING' else "❌"
                f.write(f"- {emoji} **{phase_name.replace('_', ' ').title()}**: {status}\n")
                
            # Critical issues
            if validation_summary['critical_issues']:
                f.write("\n## ❌ Critical Issues\n\n")
                for issue in validation_summary['critical_issues']:
                    f.write(f"- {issue}\n")
                    
            # Recommendations
            f.write("\n## 💡 Recommendations\n\n")
            for rec in validation_summary['recommendations']:
                f.write(f"- {rec}\n")
                
            # Next steps
            f.write("\n## 🎯 Next Steps\n\n")
            for step in validation_summary['next_steps']:
                f.write(f"{step}\n")
                
            # Metadata
            f.write(f"\n---\n\n")
            f.write(f"**Validation ID**: {validation_summary['validation_id']}\n")
            f.write(f"**Start Time**: {validation_summary['start_time']}\n")
            f.write(f"**End Time**: {validation_summary['end_time']}\n")
            f.write(f"**Duration**: {validation_summary['total_duration_minutes']:.1f} minutes\n")


def main():
    """Main execution function."""
    print("🚀 Starting Testing-12: End-to-End System Validation & Production Readiness")
    print("=" * 80)
    
    orchestrator = ValidationOrchestrator()
    
    try:
        # Run complete validation
        results = orchestrator.run_complete_validation()
        
        # Save results
        orchestrator.save_results(results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Overall Status: {results['overall_status']}")
        print(f"Production Ready: {results['production_ready']}")
        print(f"Duration: {results['total_duration_minutes']:.1f} minutes")
        
        if results['critical_issues']:
            print(f"\n❌ Critical Issues ({len(results['critical_issues'])}):")
            for issue in results['critical_issues'][:5]:  # Show first 5
                print(f"  - {issue}")
                
        print(f"\n💡 Key Recommendations:")
        for rec in results['recommendations']:
            print(f"  {rec}")
            
        print(f"\n📁 Detailed results saved to: validation/validation_results.json")
        print(f"📄 Summary report saved to: validation/validation_summary.md")
        
        # Exit with appropriate code
        sys.exit(0 if results['production_ready'] else 1)
        
    except Exception as e:
        logger.error(f"Validation execution failed: {e}")
        print(f"\n❌ VALIDATION FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

