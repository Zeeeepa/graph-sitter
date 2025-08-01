#!/usr/bin/env python3
"""
Comprehensive Error Detection Validation Suite

This test suite validates EVERY type of error that can be detected via LSP,
including full context, reasoning, and false positive detection.

Error Types Tested:
1. Syntax Errors (all variants)
2. Import Errors (missing modules, circular imports, etc.)
3. Type Errors (all type mismatches)
4. Name Errors (undefined variables, functions, classes)
5. Attribute Errors (missing attributes, methods)
6. Index Errors (list/dict access issues)
7. Key Errors (dictionary key issues)
8. Value Errors (invalid values)
9. Runtime Logic Errors
10. Code Quality Issues (unused variables, etc.)
11. False Positives (valid code that might be flagged)
"""

import sys
import os
import tempfile
import shutil
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@dataclass
class ErrorTestCase:
    """Test case for a specific error type."""
    name: str
    description: str
    code: str
    expected_error_types: List[str]
    expected_keywords: List[str]  # Keywords that should appear in error message/context
    should_have_fix: bool
    category: str

@dataclass
class ErrorValidationResult:
    """Result of error validation."""
    test_case: ErrorTestCase
    detected_errors: List[Dict[str, Any]]
    validation_passed: bool
    issues: List[str]
    context_quality: int  # 1-10 rating
    reasoning_quality: int  # 1-10 rating

class ComprehensiveErrorValidator:
    """Comprehensive error detection validator."""
    
    def __init__(self):
        self.test_cases = self._create_comprehensive_test_cases()
        self.results: List[ErrorValidationResult] = []
        
    def _create_comprehensive_test_cases(self) -> List[ErrorTestCase]:
        """Create comprehensive test cases for all error types."""
        
        test_cases = []
        
        # 1. SYNTAX ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="missing_parenthesis",
                description="Function definition missing closing parenthesis",
                code='''
def broken_function(param1, param2
    print("Missing closing parenthesis")
    return param1 + param2
''',
                expected_error_types=["SyntaxError", "syntax"],
                expected_keywords=["parenthesis", "missing", "syntax"],
                should_have_fix=True,
                category="syntax"
            ),
            
            ErrorTestCase(
                name="missing_colon",
                description="If statement missing colon",
                code='''
def test_function():
    x = 5
    if x > 3
        print("Missing colon")
    return x
''',
                expected_error_types=["SyntaxError", "syntax"],
                expected_keywords=["colon", "missing", "if"],
                should_have_fix=True,
                category="syntax"
            ),
            
            ErrorTestCase(
                name="invalid_indentation",
                description="Inconsistent indentation",
                code='''
def test_function():
    x = 5
        y = 10  # Wrong indentation
    return x + y
''',
                expected_error_types=["IndentationError", "syntax"],
                expected_keywords=["indentation", "indent", "spaces"],
                should_have_fix=True,
                category="syntax"
            ),
            
            ErrorTestCase(
                name="unclosed_string",
                description="String literal not closed",
                code='''
def test_function():
    message = "This string is not closed
    print(message)
    return message
''',
                expected_error_types=["SyntaxError", "syntax"],
                expected_keywords=["string", "quote", "unclosed"],
                should_have_fix=True,
                category="syntax"
            ),
        ])
        
        # 2. IMPORT ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="missing_module",
                description="Import of non-existent module",
                code='''
import nonexistent_module_12345
from another_fake_module import something

def test_function():
    return nonexistent_module_12345.some_function()
''',
                expected_error_types=["ImportError", "ModuleNotFoundError", "import"],
                expected_keywords=["module", "import", "not found", "nonexistent"],
                should_have_fix=False,
                category="import"
            ),
            
            ErrorTestCase(
                name="missing_import_item",
                description="Import of non-existent item from valid module",
                code='''
from os import nonexistent_function_xyz
from sys import fake_attribute_abc

def test_function():
    return nonexistent_function_xyz()
''',
                expected_error_types=["ImportError", "import"],
                expected_keywords=["import", "cannot", "nonexistent"],
                should_have_fix=False,
                category="import"
            ),
            
            ErrorTestCase(
                name="circular_import_simulation",
                description="Potential circular import issue",
                code='''
# This simulates a circular import scenario
import sys
sys.path.append('.')
try:
    from . import circular_module_that_imports_this
except ImportError:
    pass

def test_function():
    return "circular import test"
''',
                expected_error_types=["ImportError", "import"],
                expected_keywords=["import", "circular", "relative"],
                should_have_fix=False,
                category="import"
            ),
        ])
        
        # 3. TYPE ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="type_mismatch_operation",
                description="Operation between incompatible types",
                code='''
def test_function():
    x = "string"
    y = 42
    result = x + y  # String + int
    return result
''',
                expected_error_types=["TypeError", "type"],
                expected_keywords=["type", "string", "int", "unsupported"],
                should_have_fix=True,
                category="type"
            ),
            
            ErrorTestCase(
                name="wrong_argument_type",
                description="Function called with wrong argument type",
                code='''
def numeric_function(x: int, y: int) -> int:
    return x + y

def test_function():
    result = numeric_function("string", 42)  # Wrong type
    return result
''',
                expected_error_types=["TypeError", "type"],
                expected_keywords=["argument", "type", "expected", "int"],
                should_have_fix=True,
                category="type"
            ),
            
            ErrorTestCase(
                name="none_type_operation",
                description="Operation on None type",
                code='''
def test_function():
    x = None
    result = x.upper()  # None has no upper method
    return result
''',
                expected_error_types=["AttributeError", "type"],
                expected_keywords=["None", "attribute", "upper"],
                should_have_fix=True,
                category="type"
            ),
        ])
        
        # 4. NAME ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="undefined_variable",
                description="Use of undefined variable",
                code='''
def test_function():
    print(undefined_variable_xyz)  # Not defined
    return undefined_variable_xyz
''',
                expected_error_types=["NameError", "undefined"],
                expected_keywords=["undefined", "name", "not defined"],
                should_have_fix=True,
                category="name"
            ),
            
            ErrorTestCase(
                name="undefined_function",
                description="Call to undefined function",
                code='''
def test_function():
    result = nonexistent_function_abc()  # Not defined
    return result
''',
                expected_error_types=["NameError", "undefined"],
                expected_keywords=["undefined", "function", "not defined"],
                should_have_fix=True,
                category="name"
            ),
            
            ErrorTestCase(
                name="undefined_class",
                description="Use of undefined class",
                code='''
def test_function():
    obj = UndefinedClass()  # Not defined
    return obj
''',
                expected_error_types=["NameError", "undefined"],
                expected_keywords=["undefined", "class", "not defined"],
                should_have_fix=True,
                category="name"
            ),
        ])
        
        # 5. ATTRIBUTE ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="missing_method",
                description="Call to non-existent method",
                code='''
def test_function():
    x = "hello"
    result = x.nonexistent_method()  # String has no such method
    return result
''',
                expected_error_types=["AttributeError", "attribute"],
                expected_keywords=["attribute", "method", "nonexistent"],
                should_have_fix=False,
                category="attribute"
            ),
            
            ErrorTestCase(
                name="missing_attribute",
                description="Access to non-existent attribute",
                code='''
class TestClass:
    def __init__(self):
        self.existing_attr = "exists"

def test_function():
    obj = TestClass()
    return obj.nonexistent_attr  # Attribute doesn't exist
''',
                expected_error_types=["AttributeError", "attribute"],
                expected_keywords=["attribute", "nonexistent", "object"],
                should_have_fix=True,
                category="attribute"
            ),
        ])
        
        # 6. INDEX/KEY ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="list_index_error",
                description="List index out of range",
                code='''
def test_function():
    my_list = [1, 2, 3]
    return my_list[10]  # Index out of range
''',
                expected_error_types=["IndexError", "index"],
                expected_keywords=["index", "range", "list"],
                should_have_fix=True,
                category="index"
            ),
            
            ErrorTestCase(
                name="dict_key_error",
                description="Dictionary key not found",
                code='''
def test_function():
    my_dict = {"a": 1, "b": 2}
    return my_dict["nonexistent_key"]  # Key doesn't exist
''',
                expected_error_types=["KeyError", "key"],
                expected_keywords=["key", "nonexistent", "dict"],
                should_have_fix=True,
                category="key"
            ),
        ])
        
        # 7. VALUE ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="invalid_conversion",
                description="Invalid type conversion",
                code='''
def test_function():
    result = int("not_a_number")  # Can't convert to int
    return result
''',
                expected_error_types=["ValueError", "value"],
                expected_keywords=["value", "invalid", "conversion", "int"],
                should_have_fix=True,
                category="value"
            ),
        ])
        
        # 8. LOGIC ERRORS
        test_cases.extend([
            ErrorTestCase(
                name="division_by_zero",
                description="Division by zero",
                code='''
def test_function():
    x = 10
    y = 0
    result = x / y  # Division by zero
    return result
''',
                expected_error_types=["ZeroDivisionError", "division"],
                expected_keywords=["division", "zero", "divide"],
                should_have_fix=True,
                category="logic"
            ),
        ])
        
        # 9. CODE QUALITY ISSUES
        test_cases.extend([
            ErrorTestCase(
                name="unused_variable",
                description="Variable defined but never used",
                code='''
def test_function():
    unused_var = "This variable is never used"
    x = 5
    return x
''',
                expected_error_types=["unused", "warning"],
                expected_keywords=["unused", "variable", "defined"],
                should_have_fix=True,
                category="quality"
            ),
            
            ErrorTestCase(
                name="unused_import",
                description="Import that is never used",
                code='''
import json  # This import is never used
import os

def test_function():
    return os.getcwd()
''',
                expected_error_types=["unused", "import", "warning"],
                expected_keywords=["unused", "import", "json"],
                should_have_fix=True,
                category="quality"
            ),
        ])
        
        # 10. FALSE POSITIVES (Valid code that might be incorrectly flagged)
        test_cases.extend([
            ErrorTestCase(
                name="valid_dynamic_attribute",
                description="Valid dynamic attribute access",
                code='''
class DynamicClass:
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
    
    def __getattr__(self, name):
        return f"dynamic_{name}"

def test_function():
    obj = DynamicClass()
    return obj.some_dynamic_attr  # This is valid!
''',
                expected_error_types=[],  # Should NOT be flagged
                expected_keywords=[],
                should_have_fix=False,
                category="false_positive"
            ),
            
            ErrorTestCase(
                name="valid_monkey_patching",
                description="Valid monkey patching",
                code='''
import types

def test_function():
    def new_method(self):
        return "patched"
    
    # This is valid monkey patching
    str.custom_method = new_method
    return "hello".custom_method()
''',
                expected_error_types=[],  # Should NOT be flagged
                expected_keywords=[],
                should_have_fix=False,
                category="false_positive"
            ),
            
            ErrorTestCase(
                name="valid_conditional_import",
                description="Valid conditional import",
                code='''
def test_function():
    try:
        import optional_module
        return optional_module.some_function()
    except ImportError:
        return "fallback"  # This is valid!
''',
                expected_error_types=[],  # Should NOT be flagged as error
                expected_keywords=[],
                should_have_fix=False,
                category="false_positive"
            ),
        ])
        
        return test_cases
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all error types."""
        print("🔍 COMPREHENSIVE ERROR DETECTION VALIDATION")
        print("=" * 80)
        print(f"Testing {len(self.test_cases)} error scenarios across all categories")
        print()
        
        # Create temporary directory with git repo
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize git repository
            import subprocess
            subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, capture_output=True)
            
            # Create test files for each category
            category_results = {}
            
            for i, test_case in enumerate(self.test_cases):
                print(f"📋 Testing {i+1}/{len(self.test_cases)}: {test_case.name} ({test_case.category})")
                
                # Create test file
                test_file = Path(temp_dir) / f"test_{test_case.name}.py"
                test_file.write_text(test_case.code)
                
                # Add to git
                subprocess.run(['git', 'add', str(test_file)], cwd=temp_dir, capture_output=True)
                
                # Test error detection
                result = self._validate_error_detection(test_case, temp_dir)
                self.results.append(result)
                
                # Track by category
                if test_case.category not in category_results:
                    category_results[test_case.category] = []
                category_results[test_case.category].append(result)
                
                print(f"   {'✅' if result.validation_passed else '❌'} {test_case.description}")
                if not result.validation_passed:
                    for issue in result.issues:
                        print(f"      ⚠️  {issue}")
                print()
            
            # Commit all test files
            subprocess.run(['git', 'commit', '-m', 'Test files'], cwd=temp_dir, capture_output=True)
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(category_results)
            
            return report
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _validate_error_detection(self, test_case: ErrorTestCase, temp_dir: str) -> ErrorValidationResult:
        """Validate error detection for a specific test case."""
        try:
            from graph_sitter.enhanced.codebase import Codebase
            
            # Create codebase for this test
            codebase = Codebase(temp_dir)
            
            # Get errors
            detected_errors = codebase.errors()
            
            # Validate the detection
            validation_passed = True
            issues = []
            
            # Check if expected errors were detected
            if test_case.expected_error_types:
                found_expected = False
                for error in detected_errors:
                    error_type = error.get('severity', '').lower()
                    error_message = error.get('message', '').lower()
                    error_source = error.get('source', '').lower()
                    
                    # Check if this error matches expected types
                    for expected_type in test_case.expected_error_types:
                        if (expected_type.lower() in error_type or 
                            expected_type.lower() in error_message or
                            expected_type.lower() in error_source):
                            found_expected = True
                            break
                    
                    if found_expected:
                        break
                
                if not found_expected:
                    validation_passed = False
                    issues.append(f"Expected error types {test_case.expected_error_types} not detected")
            
            # For false positives, ensure NO errors were detected
            if test_case.category == "false_positive" and detected_errors:
                validation_passed = False
                issues.append(f"False positive: {len(detected_errors)} errors detected in valid code")
            
            # Validate error context and reasoning
            context_quality = 0
            reasoning_quality = 0
            
            for error in detected_errors:
                # Check for context information
                if 'file_path' in error and 'line' in error and 'message' in error:
                    context_quality += 2
                
                # Check for detailed context
                error_id = error.get('id', 'test_id')
                try:
                    context = codebase.full_error_context(error_id)
                    if context and isinstance(context, dict):
                        if 'context' in context:
                            context_quality += 3
                        if 'suggestions' in context:
                            reasoning_quality += 3
                        if 'fix_available' in context:
                            reasoning_quality += 2
                except Exception:
                    pass
            
            # Normalize quality scores
            context_quality = min(10, context_quality)
            reasoning_quality = min(10, reasoning_quality)
            
            return ErrorValidationResult(
                test_case=test_case,
                detected_errors=detected_errors,
                validation_passed=validation_passed,
                issues=issues,
                context_quality=context_quality,
                reasoning_quality=reasoning_quality
            )
            
        except Exception as e:
            return ErrorValidationResult(
                test_case=test_case,
                detected_errors=[],
                validation_passed=False,
                issues=[f"Validation failed: {e}"],
                context_quality=0,
                reasoning_quality=0
            )
    
    def _generate_comprehensive_report(self, category_results: Dict[str, List[ErrorValidationResult]]) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.validation_passed)
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'categories_tested': len(category_results)
            },
            'category_breakdown': {},
            'error_detection_coverage': {},
            'context_quality_analysis': {},
            'false_positive_analysis': {},
            'recommendations': []
        }
        
        # Analyze by category
        for category, results in category_results.items():
            category_passed = sum(1 for r in results if r.validation_passed)
            category_total = len(results)
            
            avg_context_quality = sum(r.context_quality for r in results) / len(results)
            avg_reasoning_quality = sum(r.reasoning_quality for r in results) / len(results)
            
            report['category_breakdown'][category] = {
                'total_tests': category_total,
                'passed_tests': category_passed,
                'pass_rate': (category_passed / category_total * 100) if category_total > 0 else 0,
                'avg_context_quality': round(avg_context_quality, 2),
                'avg_reasoning_quality': round(avg_reasoning_quality, 2),
                'failed_tests': [r.test_case.name for r in results if not r.validation_passed]
            }
        
        # Error detection coverage
        detected_error_types = set()
        for result in self.results:
            for error in result.detected_errors:
                error_type = error.get('severity', 'unknown')
                detected_error_types.add(error_type)
        
        report['error_detection_coverage'] = {
            'detected_types': list(detected_error_types),
            'coverage_count': len(detected_error_types)
        }
        
        # Context quality analysis
        context_scores = [r.context_quality for r in self.results]
        reasoning_scores = [r.reasoning_quality for r in self.results]
        
        report['context_quality_analysis'] = {
            'avg_context_quality': round(sum(context_scores) / len(context_scores), 2) if context_scores else 0,
            'avg_reasoning_quality': round(sum(reasoning_scores) / len(reasoning_scores), 2) if reasoning_scores else 0,
            'high_quality_context': sum(1 for s in context_scores if s >= 7),
            'low_quality_context': sum(1 for s in context_scores if s <= 3)
        }
        
        # False positive analysis
        false_positive_results = [r for r in self.results if r.test_case.category == "false_positive"]
        false_positives_detected = sum(1 for r in false_positive_results if not r.validation_passed)
        
        report['false_positive_analysis'] = {
            'total_false_positive_tests': len(false_positive_results),
            'false_positives_detected': false_positives_detected,
            'false_positive_rate': (false_positives_detected / len(false_positive_results) * 100) if false_positive_results else 0
        }
        
        # Generate recommendations
        recommendations = []
        
        if report['summary']['pass_rate'] < 80:
            recommendations.append("Overall error detection needs improvement - less than 80% pass rate")
        
        if report['context_quality_analysis']['avg_context_quality'] < 5:
            recommendations.append("Error context quality is low - need richer contextual information")
        
        if report['context_quality_analysis']['avg_reasoning_quality'] < 5:
            recommendations.append("Error reasoning quality is low - need better fix suggestions")
        
        if report['false_positive_analysis']['false_positive_rate'] > 20:
            recommendations.append("High false positive rate - need better error filtering")
        
        for category, data in report['category_breakdown'].items():
            if data['pass_rate'] < 70:
                recommendations.append(f"Poor detection for {category} errors - {data['pass_rate']:.1f}% pass rate")
        
        report['recommendations'] = recommendations
        
        return report
    
    def print_detailed_report(self, report: Dict[str, Any]):
        """Print detailed validation report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE ERROR DETECTION VALIDATION REPORT")
        print("=" * 80)
        
        # Summary
        summary = report['summary']
        print(f"\n🎯 OVERALL SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"   Categories Tested: {summary['categories_tested']}")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, data in report['category_breakdown'].items():
            status = "✅" if data['pass_rate'] >= 80 else "⚠️" if data['pass_rate'] >= 60 else "❌"
            print(f"   {status} {category.upper()}: {data['passed_tests']}/{data['total_tests']} ({data['pass_rate']:.1f}%)")
            print(f"      Context Quality: {data['avg_context_quality']}/10")
            print(f"      Reasoning Quality: {data['avg_reasoning_quality']}/10")
            if data['failed_tests']:
                print(f"      Failed: {', '.join(data['failed_tests'])}")
        
        # Error detection coverage
        coverage = report['error_detection_coverage']
        print(f"\n🔍 ERROR DETECTION COVERAGE:")
        print(f"   Detected Error Types: {coverage['coverage_count']}")
        print(f"   Types: {', '.join(coverage['detected_types'])}")
        
        # Context quality
        context = report['context_quality_analysis']
        print(f"\n📝 CONTEXT & REASONING QUALITY:")
        print(f"   Average Context Quality: {context['avg_context_quality']}/10")
        print(f"   Average Reasoning Quality: {context['avg_reasoning_quality']}/10")
        print(f"   High Quality Context: {context['high_quality_context']} tests")
        print(f"   Low Quality Context: {context['low_quality_context']} tests")
        
        # False positives
        fp = report['false_positive_analysis']
        print(f"\n🚫 FALSE POSITIVE ANALYSIS:")
        print(f"   False Positive Tests: {fp['total_false_positive_tests']}")
        print(f"   False Positives Detected: {fp['false_positives_detected']}")
        print(f"   False Positive Rate: {fp['false_positive_rate']:.1f}%")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Overall assessment
        overall_score = (
            summary['pass_rate'] * 0.4 +
            context['avg_context_quality'] * 10 * 0.3 +
            context['avg_reasoning_quality'] * 10 * 0.2 +
            (100 - fp['false_positive_rate']) * 0.1
        )
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if overall_score >= 85:
            print(f"   🎉 EXCELLENT ({overall_score:.1f}/100) - Production ready!")
        elif overall_score >= 70:
            print(f"   ✅ GOOD ({overall_score:.1f}/100) - Minor improvements needed")
        elif overall_score >= 50:
            print(f"   ⚠️  FAIR ({overall_score:.1f}/100) - Significant improvements needed")
        else:
            print(f"   ❌ POOR ({overall_score:.1f}/100) - Major overhaul required")


def main():
    """Main function to run comprehensive error validation."""
    print("🚀 COMPREHENSIVE ERROR DETECTION VALIDATION SUITE")
    print("=" * 80)
    print("This suite validates EVERY type of error detection with full context and reasoning")
    print("Including false positive detection and comprehensive error coverage")
    print()
    
    validator = ComprehensiveErrorValidator()
    
    print(f"📋 Test Cases Created:")
    categories = {}
    for test_case in validator.test_cases:
        if test_case.category not in categories:
            categories[test_case.category] = 0
        categories[test_case.category] += 1
    
    for category, count in categories.items():
        print(f"   {category.upper()}: {count} tests")
    
    print(f"\nTotal: {len(validator.test_cases)} comprehensive test cases")
    print()
    
    # Run validation
    start_time = time.time()
    report = validator.run_comprehensive_validation()
    end_time = time.time()
    
    # Print detailed report
    validator.print_detailed_report(report)
    
    print(f"\n⏱️  Validation completed in {end_time - start_time:.2f} seconds")
    
    # Save detailed report
    report_file = Path("comprehensive_error_validation_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"💾 Detailed report saved to: {report_file}")
    
    # Return exit code based on results
    if report['summary']['pass_rate'] >= 80 and report['false_positive_analysis']['false_positive_rate'] <= 20:
        print("\n🎉 VALIDATION PASSED - Error detection system is working correctly!")
        return 0
    else:
        print("\n⚠️  VALIDATION ISSUES FOUND - See recommendations above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

