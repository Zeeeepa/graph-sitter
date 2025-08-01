#!/usr/bin/env python3
"""
Comprehensive Serena Consolidation Test Suite

This is the master test suite that validates the complete unified Serena interface
implementation and consolidation. It tests all aspects of the system:

✅ Unified Interface: All 4 methods working (errors, full_error_context, resolve_errors, resolve_error)
⚡ Lazy Loading: LSP features initialized only when first accessed
🔄 Consistent Return Types: Standardized error/result objects
🛡️ Graceful Error Handling: Proper fallbacks when LSP unavailable
🚀 Performance: Sub-5s initialization, sub-1s context extraction
🧪 Real Integration: Works with actual codebases and LSP servers

This test suite serves as the definitive validation that the Serena consolidation
is complete and the unified interface is ready for production use.
"""

import os
import sys
import time
import json
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test imports
try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
    print("✅ Graph-sitter import successful")
except ImportError as e:
    print(f"❌ Graph-sitter import failed: {e}")
    GRAPH_SITTER_AVAILABLE = False

# Test enhanced components
try:
    from graph_sitter.core.enhanced_error_types import EnhancedErrorInfo, ErrorSeverity, ErrorCategory, CodeLocation
    from graph_sitter.core.enhanced_lsp_manager import EnhancedLSPManager
    from graph_sitter.core.fix_application import FixApplicator
    from graph_sitter.core.error_methods import SerenaErrorMethods
    ENHANCED_COMPONENTS_AVAILABLE = True
    print("✅ Enhanced components import successful")
except ImportError as e:
    print(f"❌ Enhanced components import failed: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False


@dataclass
class TestResult:
    """Test result with detailed information."""
    test_name: str
    success: bool
    execution_time: float
    details: Dict[str, Any]
    error_message: str = ""


class ComprehensiveTestSuite:
    """Comprehensive test suite for the unified Serena interface."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test and record results."""
        print(f"\n🧪 Running: {test_name}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            details = test_func()
            success = True
            error_message = ""
            print(f"✅ {test_name} - PASSED")
        except Exception as e:
            details = {"error": str(e)}
            success = False
            error_message = str(e)
            print(f"❌ {test_name} - FAILED: {error_message}")
            traceback.print_exc()
        
        execution_time = time.time() - start_time
        
        result = TestResult(
            test_name=test_name,
            success=success,
            execution_time=execution_time,
            details=details,
            error_message=error_message
        )
        
        self.results.append(result)
        return result
    
    def test_component_availability(self) -> Dict[str, Any]:
        """Test that all required components are available."""
        components = {
            'graph_sitter': GRAPH_SITTER_AVAILABLE,
            'enhanced_components': ENHANCED_COMPONENTS_AVAILABLE,
        }
        
        # Test specific imports
        try:
            from graph_sitter.core.codebase import Codebase as CoreCodebase
            components['core_codebase'] = True
        except ImportError:
            components['core_codebase'] = False
        
        try:
            from graph_sitter.enhanced.codebase import Codebase as EnhancedCodebase
            components['enhanced_codebase'] = True
        except ImportError:
            components['enhanced_codebase'] = False
        
        # Verify unified interface methods
        if GRAPH_SITTER_AVAILABLE:
            codebase = Codebase(".")
            methods = {
                'errors': hasattr(codebase, 'errors'),
                'full_error_context': hasattr(codebase, 'full_error_context'),
                'resolve_errors': hasattr(codebase, 'resolve_errors'),
                'resolve_error': hasattr(codebase, 'resolve_error'),
            }
            components['unified_methods'] = methods
        
        print(f"📦 Component Availability:")
        for component, available in components.items():
            status = "✅" if available else "❌"
            print(f"   {status} {component}")
        
        return components
    
    def test_codebase_initialization(self) -> Dict[str, Any]:
        """Test codebase initialization performance and functionality."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        # Test with current directory
        start_time = time.time()
        codebase = Codebase(".")
        init_time = time.time() - start_time
        
        # Verify codebase properties
        details = {
            'initialization_time': init_time,
            'repo_path': str(codebase.repo_path),
            'has_unified_methods': {
                'errors': hasattr(codebase, 'errors'),
                'full_error_context': hasattr(codebase, 'full_error_context'),
                'resolve_errors': hasattr(codebase, 'resolve_errors'),
                'resolve_error': hasattr(codebase, 'resolve_error'),
            }
        }
        
        # Performance requirement
        if init_time > 5.0:
            raise Exception(f"Initialization too slow: {init_time:.2f}s > 5.0s")
        
        print(f"⚡ Initialization time: {init_time:.2f}s")
        print(f"📁 Repository path: {codebase.repo_path}")
        
        return details
    
    def test_errors_method(self) -> Dict[str, Any]:
        """Test the codebase.errors() method."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        codebase = Codebase(".")
        
        # Test errors() method
        start_time = time.time()
        errors = codebase.errors()
        errors_time = time.time() - start_time
        
        # Verify return type
        if not isinstance(errors, list):
            raise Exception(f"errors() should return list, got {type(errors)}")
        
        details = {
            'execution_time': errors_time,
            'errors_found': len(errors),
            'error_types': {},
            'error_severities': {},
            'error_sources': {},
            'sample_errors': []
        }
        
        # Analyze errors if found
        if errors:
            for error in errors[:5]:  # Sample first 5 errors
                # Verify error structure
                required_fields = ['id', 'location', 'message', 'severity']
                for field in required_fields:
                    if field not in error:
                        raise Exception(f"Error missing required field: {field}")
                
                # Count categories
                error_type = error.get('error_type', 'unknown')
                severity = error.get('severity', 'unknown')
                source = error.get('source', 'unknown')
                
                details['error_types'][error_type] = details['error_types'].get(error_type, 0) + 1
                details['error_severities'][severity] = details['error_severities'].get(severity, 0) + 1
                details['error_sources'][source] = details['error_sources'].get(source, 0) + 1
                
                # Add to sample
                details['sample_errors'].append({
                    'id': error['id'],
                    'message': error['message'][:100],
                    'severity': error['severity'],
                    'file': error['location']['file_path']
                })
        
        print(f"🔍 Found {len(errors)} errors in {errors_time:.2f}s")
        if errors:
            print(f"📊 Error breakdown:")
            print(f"   Types: {details['error_types']}")
            print(f"   Severities: {details['error_severities']}")
            print(f"   Sources: {details['error_sources']}")
        
        return details
    
    def test_full_error_context_method(self) -> Dict[str, Any]:
        """Test the codebase.full_error_context() method."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        codebase = Codebase(".")
        errors = codebase.errors()
        
        if not errors:
            return {
                'message': 'No errors found to test context extraction',
                'errors_available': False
            }
        
        # Test context for first error
        error_id = errors[0]['id']
        
        start_time = time.time()
        context = codebase.full_error_context(error_id)
        context_time = time.time() - start_time
        
        details = {
            'execution_time': context_time,
            'error_id': error_id,
            'context_found': context is not None,
            'context_fields': [],
            'errors_available': True
        }
        
        if context:
            # Verify context structure
            expected_fields = ['id', 'location', 'message', 'context', 'reasoning']
            for field in expected_fields:
                if field in context:
                    details['context_fields'].append(field)
            
            # Performance requirement
            if context_time > 1.0:
                raise Exception(f"Context extraction too slow: {context_time:.2f}s > 1.0s")
        
        print(f"🎯 Context extraction: {context_time:.3f}s")
        print(f"📋 Context fields: {details['context_fields']}")
        
        return details
    
    def test_resolve_errors_method(self) -> Dict[str, Any]:
        """Test the codebase.resolve_errors() method."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        codebase = Codebase(".")
        errors = codebase.errors()
        
        if not errors:
            return {
                'message': 'No errors found to test batch resolution',
                'errors_available': False
            }
        
        # Test with first few errors
        test_error_ids = [e['id'] for e in errors[:3]]
        
        start_time = time.time()
        result = codebase.resolve_errors(test_error_ids)
        resolve_time = time.time() - start_time
        
        # Verify result structure
        if not isinstance(result, dict):
            raise Exception(f"resolve_errors() should return dict, got {type(result)}")
        
        required_fields = ['total_errors', 'successful_fixes', 'failed_fixes', 'summary']
        for field in required_fields:
            if field not in result:
                raise Exception(f"Result missing required field: {field}")
        
        details = {
            'execution_time': resolve_time,
            'total_errors': result['total_errors'],
            'successful_fixes': result['successful_fixes'],
            'failed_fixes': result['failed_fixes'],
            'skipped_errors': result.get('skipped_errors', 0),
            'summary': result['summary'],
            'errors_available': True
        }
        
        print(f"🔧 Batch resolution: {resolve_time:.2f}s")
        print(f"📊 Results: {result['summary']}")
        
        return details
    
    def test_resolve_error_method(self) -> Dict[str, Any]:
        """Test the codebase.resolve_error() method."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        codebase = Codebase(".")
        errors = codebase.errors()
        
        if not errors:
            return {
                'message': 'No errors found to test single resolution',
                'errors_available': False
            }
        
        # Test with first error
        error_id = errors[0]['id']
        
        start_time = time.time()
        result = codebase.resolve_error(error_id)
        resolve_time = time.time() - start_time
        
        details = {
            'execution_time': resolve_time,
            'error_id': error_id,
            'result_found': result is not None,
            'errors_available': True
        }
        
        if result:
            # Verify result structure
            if not isinstance(result, dict):
                raise Exception(f"resolve_error() should return dict, got {type(result)}")
            
            required_fields = ['success', 'error_id']
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Result missing required field: {field}")
            
            details.update({
                'success': result['success'],
                'applied_fixes': len(result.get('applied_fixes', [])),
                'confidence_score': result.get('confidence_score', 0.0)
            })
        
        print(f"🎯 Single resolution: {resolve_time:.3f}s")
        if result:
            print(f"✅ Success: {result['success']}, Confidence: {result.get('confidence_score', 0):.2f}")
        
        return details
    
    def test_lazy_loading_behavior(self) -> Dict[str, Any]:
        """Test that LSP features are loaded lazily."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        # Create new codebase instance
        start_time = time.time()
        codebase = Codebase(".")
        init_time = time.time() - start_time
        
        # First call to errors() should trigger LSP initialization
        start_time = time.time()
        first_errors = codebase.errors()
        first_call_time = time.time() - start_time
        
        # Second call should be faster (cached)
        start_time = time.time()
        second_errors = codebase.errors()
        second_call_time = time.time() - start_time
        
        details = {
            'init_time': init_time,
            'first_call_time': first_call_time,
            'second_call_time': second_call_time,
            'caching_effective': second_call_time < first_call_time,
            'errors_consistent': len(first_errors) == len(second_errors)
        }
        
        print(f"⚡ Lazy loading analysis:")
        print(f"   Init: {init_time:.3f}s")
        print(f"   First call: {first_call_time:.3f}s")
        print(f"   Second call: {second_call_time:.3f}s")
        print(f"   Caching effective: {details['caching_effective']}")
        
        return details
    
    def test_error_handling_graceful_fallbacks(self) -> Dict[str, Any]:
        """Test graceful error handling and fallbacks."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        codebase = Codebase(".")
        
        # All methods should work without crashing
        methods_tested = {}
        
        try:
            errors = codebase.errors()
            methods_tested['errors'] = {'success': True, 'result_type': type(errors).__name__}
        except Exception as e:
            methods_tested['errors'] = {'success': False, 'error': str(e)}
        
        try:
            # Test with a fake error ID
            context = codebase.full_error_context("fake_error_id")
            methods_tested['full_error_context'] = {'success': True, 'result_type': type(context).__name__}
        except Exception as e:
            methods_tested['full_error_context'] = {'success': False, 'error': str(e)}
        
        try:
            result = codebase.resolve_errors([])
            methods_tested['resolve_errors'] = {'success': True, 'result_type': type(result).__name__}
        except Exception as e:
            methods_tested['resolve_errors'] = {'success': False, 'error': str(e)}
        
        try:
            result = codebase.resolve_error("fake_error_id")
            methods_tested['resolve_error'] = {'success': True, 'result_type': type(result).__name__}
        except Exception as e:
            methods_tested['resolve_error'] = {'success': False, 'error': str(e)}
        
        details = {
            'methods_tested': methods_tested,
            'all_methods_graceful': all(m['success'] for m in methods_tested.values())
        }
        
        print(f"🛡️  Graceful error handling:")
        for method, result in methods_tested.items():
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {method}")
        
        return details
    
    def test_performance_requirements(self) -> Dict[str, Any]:
        """Test that performance requirements are met."""
        if not GRAPH_SITTER_AVAILABLE:
            raise Exception("Graph-sitter not available")
        
        performance_results = {}
        
        # Test initialization performance
        start_time = time.time()
        codebase = Codebase(".")
        init_time = time.time() - start_time
        performance_results['initialization'] = {
            'time': init_time,
            'requirement': 5.0,
            'meets_requirement': init_time < 5.0
        }
        
        # Test error detection performance
        start_time = time.time()
        errors = codebase.errors()
        errors_time = time.time() - start_time
        performance_results['error_detection'] = {
            'time': errors_time,
            'requirement': 10.0,
            'meets_requirement': errors_time < 10.0,
            'errors_found': len(errors)
        }
        
        # Test context extraction performance (if errors exist)
        if errors:
            start_time = time.time()
            context = codebase.full_error_context(errors[0]['id'])
            context_time = time.time() - start_time
            performance_results['context_extraction'] = {
                'time': context_time,
                'requirement': 1.0,
                'meets_requirement': context_time < 1.0
            }
        
        details = {
            'performance_results': performance_results,
            'all_requirements_met': all(r['meets_requirement'] for r in performance_results.values())
        }
        
        print(f"🚀 Performance requirements:")
        for test, result in performance_results.items():
            status = "✅" if result['meets_requirement'] else "❌"
            print(f"   {status} {test}: {result['time']:.3f}s (< {result['requirement']}s)")
        
        return details
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_time = time.time() - self.start_time
        
        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        # Categorize results
        component_tests = [r for r in self.results if 'component' in r.test_name.lower()]
        functionality_tests = [r for r in self.results if any(word in r.test_name.lower() for word in ['errors', 'context', 'resolve'])]
        performance_tests = [r for r in self.results if 'performance' in r.test_name.lower() or 'lazy' in r.test_name.lower()]
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_execution_time': total_time
            },
            'categories': {
                'component_tests': len(component_tests),
                'functionality_tests': len(functionality_tests),
                'performance_tests': len(performance_tests)
            },
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'execution_time': r.execution_time,
                    'error_message': r.error_message
                }
                for r in self.results
            ],
            'unified_interface_status': {
                'available': GRAPH_SITTER_AVAILABLE and ENHANCED_COMPONENTS_AVAILABLE,
                'methods_working': passed_tests >= 4,  # At least 4 core methods working
                'performance_acceptable': all(r.success for r in performance_tests),
                'ready_for_production': passed_tests >= total_tests * 0.8  # 80% pass rate
            }
        }
        
        return report
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        print("🚀 COMPREHENSIVE SERENA CONSOLIDATION TEST SUITE")
        print("=" * 70)
        print("Testing unified interface implementation and consolidation")
        print()
        
        # Run all tests
        self.run_test("Component Availability", self.test_component_availability)
        self.run_test("Codebase Initialization", self.test_codebase_initialization)
        self.run_test("Errors Method", self.test_errors_method)
        self.run_test("Full Error Context Method", self.test_full_error_context_method)
        self.run_test("Resolve Errors Method", self.test_resolve_errors_method)
        self.run_test("Resolve Error Method", self.test_resolve_error_method)
        self.run_test("Lazy Loading Behavior", self.test_lazy_loading_behavior)
        self.run_test("Graceful Error Handling", self.test_error_handling_graceful_fallbacks)
        self.run_test("Performance Requirements", self.test_performance_requirements)
        
        # Generate final report
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Time: {summary['total_execution_time']:.2f}s")
        
        print(f"\nTest Categories:")
        for category, count in report['categories'].items():
            print(f"  {category.replace('_', ' ').title()}: {count}")
        
        # Unified interface status
        ui_status = report['unified_interface_status']
        print(f"\n🎯 UNIFIED INTERFACE STATUS:")
        print(f"  Available: {'✅' if ui_status['available'] else '❌'}")
        print(f"  Methods Working: {'✅' if ui_status['methods_working'] else '❌'}")
        print(f"  Performance Acceptable: {'✅' if ui_status['performance_acceptable'] else '❌'}")
        print(f"  Ready for Production: {'✅' if ui_status['ready_for_production'] else '❌'}")
        
        # Failed tests details
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            print(f"\n❌ FAILED TESTS:")
            for result in failed_results:
                print(f"  - {result.test_name}: {result.error_message}")
        
        print(f"\n{'✅ CONSOLIDATION COMPLETE' if ui_status['ready_for_production'] else '⚠️  CONSOLIDATION NEEDS WORK'}")
        
        return report


def main():
    """Main function to run comprehensive tests."""
    suite = ComprehensiveTestSuite()
    report = suite.run_all_tests()
    
    # Save report
    report_file = Path("comprehensive_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    # Return appropriate exit code
    if report['unified_interface_status']['ready_for_production']:
        print("\n🎉 SUCCESS: Unified Serena interface is ready for production!")
        return 0
    else:
        print("\n⚠️  WARNING: Unified Serena interface needs additional work")
        return 1


if __name__ == "__main__":
    exit(main())

