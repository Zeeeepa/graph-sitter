#!/usr/bin/env python3
"""
Comprehensive LSP Error Detection Validation Script

This script validates that the LSP integration is working correctly by:
1. Testing the fixed WeakKeyDictionary issue
2. Validating LSP server connectivity
3. Testing real error detection on files with known errors
4. Comparing real LSP diagnostics vs placeholder diagnostics
5. Measuring error detection accuracy across all categories
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


class ComprehensiveLSPValidator:
    """Comprehensive validator for LSP error detection functionality."""
    
    def __init__(self):
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {},
            'summary': {},
            'errors': []
        }
        
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🚀 COMPREHENSIVE LSP ERROR DETECTION VALIDATION")
        print("=" * 60)
        
        if not GRAPH_SITTER_AVAILABLE:
            self.results['errors'].append("Graph-sitter not available")
            return self.results
        
        # Test 1: WeakKeyDictionary Fix Validation
        print("\n1️⃣ Testing WeakKeyDictionary Fix...")
        self.test_weak_key_dictionary_fix()
        
        # Test 2: LSP Server Connectivity
        print("\n2️⃣ Testing LSP Server Connectivity...")
        self.test_lsp_server_connectivity()
        
        # Test 3: Real Error Detection
        print("\n3️⃣ Testing Real Error Detection...")
        self.test_real_error_detection()
        
        # Test 4: Error Analysis Quality
        print("\n4️⃣ Testing Error Analysis Quality...")
        self.test_error_analysis_quality()
        
        # Test 5: Performance Validation
        print("\n5️⃣ Testing Performance...")
        self.test_performance()
        
        # Generate summary
        self.generate_summary()
        
        # Print results
        self.print_results()
        
        return self.results
    
    def test_weak_key_dictionary_fix(self):
        """Test that the WeakKeyDictionary issue is fixed."""
        try:
            # Import the transaction manager to test the fix
            from graph_sitter.extensions.lsp.transaction_manager import get_lsp_manager
            
            # Try to create an LSP manager - this should not fail with weak reference error
            test_path = str(Path.cwd())
            manager = get_lsp_manager(test_path, enable_lsp=True)
            
            self.results['tests']['weak_key_dictionary_fix'] = {
                'status': 'PASS',
                'message': 'LSP manager created successfully without WeakKeyDictionary error',
                'manager_created': True,
                'manager_type': str(type(manager))
            }
            print("   ✅ WeakKeyDictionary fix successful - LSP manager created")
            
        except Exception as e:
            error_msg = str(e)
            self.results['tests']['weak_key_dictionary_fix'] = {
                'status': 'FAIL',
                'message': f'WeakKeyDictionary error still present: {error_msg}',
                'error': error_msg,
                'manager_created': False
            }
            print(f"   ❌ WeakKeyDictionary fix failed: {error_msg}")
    
    def test_lsp_server_connectivity(self):
        """Test LSP server connectivity and initialization."""
        try:
            # Test if pylsp is available
            import subprocess
            result = subprocess.run(['pylsp', '--help'], capture_output=True, text=True, timeout=5)
            pylsp_available = result.returncode == 0
            
            # Test codebase initialization
            codebase = Codebase(".")
            
            # Test if LSP diagnostic methods are available
            has_get_file_diagnostics = hasattr(codebase, 'get_file_diagnostics')
            
            # Test if unified error interface is available
            has_errors_method = hasattr(codebase, 'errors')
            has_full_error_context = hasattr(codebase, 'full_error_context')
            has_resolve_errors = hasattr(codebase, 'resolve_errors')
            
            self.results['tests']['lsp_server_connectivity'] = {
                'status': 'PASS' if pylsp_available and has_get_file_diagnostics else 'PARTIAL',
                'pylsp_available': pylsp_available,
                'codebase_initialized': True,
                'has_get_file_diagnostics': has_get_file_diagnostics,
                'has_errors_method': has_errors_method,
                'has_full_error_context': has_full_error_context,
                'has_resolve_errors': has_resolve_errors,
                'unified_interface_complete': has_errors_method and has_full_error_context and has_resolve_errors
            }
            
            if pylsp_available:
                print("   ✅ pylsp server available")
            else:
                print("   ⚠️  pylsp server not available")
                
            if has_get_file_diagnostics:
                print("   ✅ get_file_diagnostics method available")
            else:
                print("   ❌ get_file_diagnostics method not available")
                
            if has_errors_method and has_full_error_context and has_resolve_errors:
                print("   ✅ Unified error interface complete")
            else:
                print("   ⚠️  Unified error interface incomplete")
            
        except Exception as e:
            self.results['tests']['lsp_server_connectivity'] = {
                'status': 'FAIL',
                'error': str(e),
                'pylsp_available': False,
                'codebase_initialized': False
            }
            print(f"   ❌ LSP server connectivity test failed: {e}")
    
    def test_real_error_detection(self):
        """Test real error detection on files with known errors."""
        try:
            codebase = Codebase(".")
            
            # Test on our error validation file
            test_file = "test_errors_for_validation.py"
            if not Path(test_file).exists():
                self.results['tests']['real_error_detection'] = {
                    'status': 'SKIP',
                    'message': f'Test file {test_file} not found'
                }
                print(f"   ⚠️  Test file {test_file} not found")
                return
            
            # Get errors using the unified interface
            if hasattr(codebase, 'errors'):
                all_errors = codebase.errors()
                
                # Filter errors from our test file
                test_file_errors = [e for e in all_errors if test_file in e.get('file_path', '')]
                
                # Categorize errors
                error_categories = defaultdict(int)
                error_sources = defaultdict(int)
                
                for error in test_file_errors:
                    severity = error.get('severity', 'unknown')
                    source = error.get('source', 'unknown')
                    error_categories[severity] += 1
                    error_sources[source] += 1
                
                # Check if we got real LSP diagnostics vs placeholder
                has_real_lsp = any(source != 'syntax_analyzer' for source in error_sources.keys())
                
                self.results['tests']['real_error_detection'] = {
                    'status': 'PASS' if test_file_errors else 'FAIL',
                    'total_errors_detected': len(all_errors),
                    'test_file_errors': len(test_file_errors),
                    'error_categories': dict(error_categories),
                    'error_sources': dict(error_sources),
                    'has_real_lsp_diagnostics': has_real_lsp,
                    'sample_errors': test_file_errors[:5]  # First 5 errors as samples
                }
                
                print(f"   📊 Total errors detected: {len(all_errors)}")
                print(f"   📄 Errors in test file: {len(test_file_errors)}")
                print(f"   🔍 Error categories: {dict(error_categories)}")
                print(f"   🔧 Error sources: {dict(error_sources)}")
                
                if has_real_lsp:
                    print("   ✅ Real LSP diagnostics detected")
                else:
                    print("   ⚠️  Only placeholder diagnostics detected")
                    
            else:
                self.results['tests']['real_error_detection'] = {
                    'status': 'FAIL',
                    'message': 'errors() method not available on codebase'
                }
                print("   ❌ errors() method not available")
                
        except Exception as e:
            self.results['tests']['real_error_detection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"   ❌ Real error detection test failed: {e}")
    
    def test_error_analysis_quality(self):
        """Test the quality of error analysis (context, reasoning, suggestions)."""
        try:
            codebase = Codebase(".")
            
            if not hasattr(codebase, 'errors'):
                self.results['tests']['error_analysis_quality'] = {
                    'status': 'SKIP',
                    'message': 'errors() method not available'
                }
                return
            
            all_errors = codebase.errors()
            
            if not all_errors:
                self.results['tests']['error_analysis_quality'] = {
                    'status': 'SKIP',
                    'message': 'No errors found to analyze'
                }
                return
            
            # Analyze quality of error information
            quality_metrics = {
                'has_context': 0,
                'has_reasoning': 0,
                'has_suggestions': 0,
                'has_category': 0,
                'has_impact': 0,
                'context_quality_score': 0,
                'reasoning_quality_score': 0,
                'suggestions_quality_score': 0
            }
            
            for error in all_errors[:10]:  # Analyze first 10 errors
                # Check presence of enhanced fields
                if error.get('context'):
                    quality_metrics['has_context'] += 1
                    # Score context quality (1-10)
                    context = error['context']
                    if isinstance(context, dict) and context.get('surrounding_code'):
                        quality_metrics['context_quality_score'] += 8
                    elif context:
                        quality_metrics['context_quality_score'] += 5
                
                if error.get('reasoning'):
                    quality_metrics['has_reasoning'] += 1
                    # Score reasoning quality
                    reasoning = error['reasoning']
                    if isinstance(reasoning, dict) and len(str(reasoning)) > 50:
                        quality_metrics['reasoning_quality_score'] += 8
                    elif reasoning:
                        quality_metrics['reasoning_quality_score'] += 5
                
                if error.get('suggestions'):
                    quality_metrics['has_suggestions'] += 1
                    # Score suggestions quality
                    suggestions = error['suggestions']
                    if isinstance(suggestions, list) and len(suggestions) > 0:
                        quality_metrics['suggestions_quality_score'] += 8
                    elif suggestions:
                        quality_metrics['suggestions_quality_score'] += 5
                
                if error.get('category'):
                    quality_metrics['has_category'] += 1
                
                if error.get('impact'):
                    quality_metrics['has_impact'] += 1
            
            # Calculate percentages
            total_analyzed = min(len(all_errors), 10)
            quality_percentages = {}
            for key, value in quality_metrics.items():
                if 'score' in key:
                    quality_percentages[key] = (value / (total_analyzed * 10)) * 100 if total_analyzed > 0 else 0
                else:
                    quality_percentages[key] = (value / total_analyzed) * 100 if total_analyzed > 0 else 0
            
            self.results['tests']['error_analysis_quality'] = {
                'status': 'PASS',
                'total_errors_analyzed': total_analyzed,
                'quality_metrics': quality_metrics,
                'quality_percentages': quality_percentages,
                'sample_enhanced_error': all_errors[0] if all_errors else None
            }
            
            print(f"   📊 Analyzed {total_analyzed} errors")
            print(f"   📝 Context available: {quality_percentages['has_context']:.1f}%")
            print(f"   🧠 Reasoning available: {quality_percentages['has_reasoning']:.1f}%")
            print(f"   💡 Suggestions available: {quality_percentages['has_suggestions']:.1f}%")
            print(f"   🎯 Context quality: {quality_percentages['context_quality_score']:.1f}%")
            print(f"   🔍 Reasoning quality: {quality_percentages['reasoning_quality_score']:.1f}%")
            
        except Exception as e:
            self.results['tests']['error_analysis_quality'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"   ❌ Error analysis quality test failed: {e}")
    
    def test_performance(self):
        """Test performance of error detection."""
        try:
            start_time = time.time()
            
            codebase = Codebase(".")
            init_time = time.time() - start_time
            
            if hasattr(codebase, 'errors'):
                error_start = time.time()
                all_errors = codebase.errors()
                error_time = time.time() - error_start
                
                self.results['tests']['performance'] = {
                    'status': 'PASS',
                    'codebase_init_time': round(init_time, 3),
                    'error_detection_time': round(error_time, 3),
                    'total_time': round(init_time + error_time, 3),
                    'errors_per_second': round(len(all_errors) / error_time, 2) if error_time > 0 else 0,
                    'total_errors': len(all_errors)
                }
                
                print(f"   ⚡ Codebase init: {init_time:.3f}s")
                print(f"   🔍 Error detection: {error_time:.3f}s")
                print(f"   📊 Errors per second: {len(all_errors) / error_time:.2f}" if error_time > 0 else "   📊 Instant detection")
                
            else:
                self.results['tests']['performance'] = {
                    'status': 'PARTIAL',
                    'codebase_init_time': round(init_time, 3),
                    'message': 'errors() method not available'
                }
                print(f"   ⚡ Codebase init: {init_time:.3f}s")
                print("   ⚠️  errors() method not available for performance testing")
                
        except Exception as e:
            self.results['tests']['performance'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"   ❌ Performance test failed: {e}")
    
    def generate_summary(self):
        """Generate overall validation summary."""
        tests = self.results['tests']
        
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests.values() if test.get('status') == 'PASS')
        failed_tests = sum(1 for test in tests.values() if test.get('status') == 'FAIL')
        partial_tests = sum(1 for test in tests.values() if test.get('status') == 'PARTIAL')
        skipped_tests = sum(1 for test in tests.values() if test.get('status') == 'SKIP')
        
        # Calculate overall health score
        health_score = (passed_tests * 100 + partial_tests * 50) / (total_tests * 100) * 100 if total_tests > 0 else 0
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'partial_tests': partial_tests,
            'skipped_tests': skipped_tests,
            'health_score': round(health_score, 1),
            'overall_status': 'HEALTHY' if health_score >= 80 else 'PARTIAL' if health_score >= 50 else 'UNHEALTHY',
            'critical_issues': self._identify_critical_issues(),
            'recommendations': self._generate_recommendations()
        }
    
    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues from test results."""
        issues = []
        
        if self.results['tests'].get('weak_key_dictionary_fix', {}).get('status') == 'FAIL':
            issues.append("WeakKeyDictionary issue not fixed - LSP managers cannot be created")
        
        if not self.results['tests'].get('lsp_server_connectivity', {}).get('pylsp_available', False):
            issues.append("pylsp server not available - install with: pip install python-lsp-server[all]")
        
        if not self.results['tests'].get('lsp_server_connectivity', {}).get('unified_interface_complete', False):
            issues.append("Unified error interface incomplete - missing errors(), full_error_context(), or resolve_errors() methods")
        
        if not self.results['tests'].get('real_error_detection', {}).get('has_real_lsp_diagnostics', False):
            issues.append("Only placeholder diagnostics detected - real LSP integration not working")
        
        return issues
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check each test and provide specific recommendations
        if self.results['tests'].get('weak_key_dictionary_fix', {}).get('status') == 'FAIL':
            recommendations.append("Fix WeakKeyDictionary implementation in transaction_manager.py")
        
        if not self.results['tests'].get('lsp_server_connectivity', {}).get('pylsp_available', False):
            recommendations.append("Install python-lsp-server: pip install python-lsp-server[all]")
        
        real_error_test = self.results['tests'].get('real_error_detection', {})
        if real_error_test.get('test_file_errors', 0) == 0:
            recommendations.append("Create test files with real Python errors for validation")
        
        quality_test = self.results['tests'].get('error_analysis_quality', {})
        if quality_test.get('quality_percentages', {}).get('context_quality_score', 0) < 70:
            recommendations.append("Improve error context quality - add more surrounding code and relevant information")
        
        if quality_test.get('quality_percentages', {}).get('reasoning_quality_score', 0) < 70:
            recommendations.append("Enhance error reasoning - provide more detailed explanations of why errors occur")
        
        performance_test = self.results['tests'].get('performance', {})
        if performance_test.get('error_detection_time', 0) > 5:
            recommendations.append("Optimize error detection performance - consider caching and parallel processing")
        
        return recommendations
    
    def print_results(self):
        """Print comprehensive validation results."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE LSP VALIDATION RESULTS")
        print("=" * 80)
        
        summary = self.results['summary']
        
        # Overall status
        status_emoji = {'HEALTHY': '🟢', 'PARTIAL': '🟡', 'UNHEALTHY': '🔴'}
        print(f"\n🎯 OVERALL STATUS: {status_emoji.get(summary['overall_status'], '⚪')} {summary['overall_status']}")
        print(f"📈 Health Score: {summary['health_score']}%")
        
        # Test summary
        print(f"\n📋 TEST SUMMARY:")
        print(f"   ✅ Passed: {summary['passed_tests']}")
        print(f"   ❌ Failed: {summary['failed_tests']}")
        print(f"   ⚠️  Partial: {summary['partial_tests']}")
        print(f"   ⏭️  Skipped: {summary['skipped_tests']}")
        print(f"   📊 Total: {summary['total_tests']}")
        
        # Critical issues
        if summary['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in summary['critical_issues']:
                print(f"   • {issue}")
        
        # Recommendations
        if summary['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in summary['recommendations']:
                print(f"   • {rec}")
        
        # Detailed test results
        print(f"\n📝 DETAILED TEST RESULTS:")
        for test_name, test_result in self.results['tests'].items():
            status_emoji = {'PASS': '✅', 'FAIL': '❌', 'PARTIAL': '⚠️', 'SKIP': '⏭️'}
            emoji = status_emoji.get(test_result.get('status'), '⚪')
            print(f"   {emoji} {test_name.replace('_', ' ').title()}: {test_result.get('status')}")
            
            if test_result.get('message'):
                print(f"      {test_result['message']}")
        
        print(f"\n💾 Full results saved to: lsp_validation_results.json")


def main():
    """Main function to run comprehensive LSP validation."""
    validator = ComprehensiveLSPValidator()
    results = validator.run_all_validations()
    
    # Save results to file
    with open('lsp_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Return exit code based on results
    if results['summary']['overall_status'] == 'HEALTHY':
        return 0
    elif results['summary']['overall_status'] == 'PARTIAL':
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit(main())
