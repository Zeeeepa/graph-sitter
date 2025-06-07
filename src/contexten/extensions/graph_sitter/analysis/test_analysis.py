"""
Test Analysis Module

Analyzes test coverage, organization, and provides utilities for
test file management and splitting.
"""

from typing import Dict, List, Any, Optional, Set
from collections import Counter, defaultdict
import os

try:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.file import SourceFile
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    # Fallback types
    Codebase = Any
    Function = Any
    Class = Any
    SourceFile = Any


def analyze_test_coverage(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze test coverage and organization in the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with test coverage analysis
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        analysis = {
            "test_functions": [],
            "test_classes": [],
            "test_files": [],
            "coverage_metrics": {
                "total_functions": 0,
                "tested_functions": 0,
                "total_classes": 0,
                "tested_classes": 0,
                "coverage_percentage": 0.0
            },
            "test_patterns": {},
            "test_organization": {}
        }
        
        # Collect all functions and classes
        all_functions = list(codebase.functions)
        all_classes = list(codebase.classes)
        
        analysis["coverage_metrics"]["total_functions"] = len(all_functions)
        analysis["coverage_metrics"]["total_classes"] = len(all_classes)
        
        # Find test functions
        test_functions = [f for f in all_functions if is_test_function(f)]
        analysis["test_functions"] = [
            {
                "name": func.name,
                "file": func.file.filepath if hasattr(func, 'file') else "unknown",
                "line_number": getattr(func, 'line_number', None),
                "test_type": classify_test_type(func)
            }
            for func in test_functions
        ]
        
        # Find test classes
        test_classes = [c for c in all_classes if is_test_class(c)]
        analysis["test_classes"] = [
            {
                "name": cls.name,
                "file": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                "method_count": len(cls.methods) if hasattr(cls, 'methods') else 0,
                "test_methods": [m.name for m in cls.methods if is_test_function(m)] if hasattr(cls, 'methods') else []
            }
            for cls in test_classes
        ]
        
        # Find test files
        test_files = find_test_files(codebase)
        analysis["test_files"] = test_files
        
        # Analyze test patterns
        analysis["test_patterns"] = analyze_test_patterns(test_functions, test_classes)
        
        # Analyze test organization
        analysis["test_organization"] = analyze_test_organization(test_files, test_functions, test_classes)
        
        # Calculate coverage (simplified)
        tested_functions = find_tested_functions(all_functions, test_functions)
        tested_classes = find_tested_classes(all_classes, test_classes)
        
        analysis["coverage_metrics"]["tested_functions"] = len(tested_functions)
        analysis["coverage_metrics"]["tested_classes"] = len(tested_classes)
        
        if analysis["coverage_metrics"]["total_functions"] > 0:
            analysis["coverage_metrics"]["coverage_percentage"] = (
                len(tested_functions) / analysis["coverage_metrics"]["total_functions"] * 100
            )
        
        return analysis
        
    except Exception as e:
        return {"error": f"Error analyzing test coverage: {str(e)}"}


def is_test_function(func: Function) -> bool:
    """Check if a function is a test function."""
    if not hasattr(func, 'name'):
        return False
    
    name = func.name.lower()
    return (
        name.startswith('test_') or
        name.endswith('_test') or
        'test' in name and any(keyword in name for keyword in ['should', 'when', 'given'])
    )


def is_test_class(cls: Class) -> bool:
    """Check if a class is a test class."""
    if not hasattr(cls, 'name'):
        return False
    
    name = cls.name
    return (
        name.startswith('Test') or
        name.endswith('Test') or
        name.endswith('Tests') or
        'Test' in name
    )


def classify_test_type(func: Function) -> str:
    """Classify the type of test based on function name and content."""
    if not hasattr(func, 'name'):
        return "unknown"
    
    name = func.name.lower()
    
    if 'unit' in name:
        return "unit"
    elif 'integration' in name or 'e2e' in name:
        return "integration"
    elif 'performance' in name or 'perf' in name:
        return "performance"
    elif 'smoke' in name:
        return "smoke"
    elif 'regression' in name:
        return "regression"
    else:
        return "unit"  # Default assumption


def find_test_files(codebase: Codebase) -> List[Dict[str, Any]]:
    """Find all test files in the codebase."""
    test_files = []
    
    try:
        for file in codebase.files:
            if is_test_file(file):
                test_info = {
                    "filepath": file.filepath,
                    "filename": os.path.basename(file.filepath),
                    "test_function_count": 0,
                    "test_class_count": 0,
                    "file_size": len(file.source) if hasattr(file, 'source') else 0
                }
                
                # Count test functions and classes in this file
                if hasattr(file, 'functions'):
                    test_info["test_function_count"] = len([f for f in file.functions if is_test_function(f)])
                
                if hasattr(file, 'classes'):
                    test_info["test_class_count"] = len([c for c in file.classes if is_test_class(c)])
                
                test_files.append(test_info)
        
        return test_files
        
    except Exception as e:
        return [{"error": f"Error finding test files: {str(e)}"}]


def is_test_file(file: SourceFile) -> bool:
    """Check if a file is a test file."""
    if not hasattr(file, 'filepath'):
        return False
    
    filepath = file.filepath.lower()
    filename = os.path.basename(filepath)
    
    return (
        filename.startswith('test_') or
        filename.endswith('_test.py') or
        filename.endswith('_tests.py') or
        '/test/' in filepath or
        '/tests/' in filepath or
        'test' in filename
    )


def analyze_test_patterns(test_functions: List[Function], test_classes: List[Class]) -> Dict[str, Any]:
    """Analyze patterns in test naming and organization."""
    patterns = {
        "naming_patterns": defaultdict(int),
        "test_types": defaultdict(int),
        "common_prefixes": [],
        "common_suffixes": []
    }
    
    try:
        # Analyze function naming patterns
        function_names = [f.name for f in test_functions if hasattr(f, 'name')]
        
        for name in function_names:
            # Count naming patterns
            if name.startswith('test_'):
                patterns["naming_patterns"]["test_prefix"] += 1
            if name.endswith('_test'):
                patterns["naming_patterns"]["test_suffix"] += 1
            if 'should' in name:
                patterns["naming_patterns"]["should_pattern"] += 1
            if 'when' in name:
                patterns["naming_patterns"]["when_pattern"] += 1
            
            # Classify test types
            test_type = classify_test_type(type('MockFunc', (), {'name': name})())
            patterns["test_types"][test_type] += 1
        
        # Find common prefixes and suffixes
        if function_names:
            # Simple prefix/suffix analysis
            prefixes = Counter([name.split('_')[0] for name in function_names if '_' in name])
            suffixes = Counter([name.split('_')[-1] for name in function_names if '_' in name])
            
            patterns["common_prefixes"] = [
                {"prefix": prefix, "count": count}
                for prefix, count in prefixes.most_common(5)
            ]
            patterns["common_suffixes"] = [
                {"suffix": suffix, "count": count}
                for suffix, count in suffixes.most_common(5)
            ]
        
        # Convert defaultdicts to regular dicts
        patterns["naming_patterns"] = dict(patterns["naming_patterns"])
        patterns["test_types"] = dict(patterns["test_types"])
        
        return patterns
        
    except Exception as e:
        return {"error": f"Error analyzing test patterns: {str(e)}"}


def analyze_test_organization(test_files: List[Dict[str, Any]], 
                            test_functions: List[Function], 
                            test_classes: List[Class]) -> Dict[str, Any]:
    """Analyze how tests are organized in the codebase."""
    organization = {
        "file_distribution": {},
        "size_analysis": {},
        "structure_analysis": {}
    }
    
    try:
        # File distribution analysis
        total_test_functions = len(test_functions)
        total_test_classes = len(test_classes)
        
        organization["file_distribution"] = {
            "total_test_files": len(test_files),
            "avg_functions_per_file": total_test_functions / len(test_files) if test_files else 0,
            "avg_classes_per_file": total_test_classes / len(test_files) if test_files else 0
        }
        
        # Size analysis
        if test_files:
            file_sizes = [f.get("file_size", 0) for f in test_files if isinstance(f, dict)]
            if file_sizes:
                organization["size_analysis"] = {
                    "avg_file_size": sum(file_sizes) / len(file_sizes),
                    "largest_file": max(file_sizes),
                    "smallest_file": min(file_sizes)
                }
        
        # Structure analysis
        file_function_counts = [f.get("test_function_count", 0) for f in test_files if isinstance(f, dict)]
        if file_function_counts:
            organization["structure_analysis"] = {
                "files_with_many_tests": len([c for c in file_function_counts if c > 20]),
                "files_with_few_tests": len([c for c in file_function_counts if c < 5]),
                "max_tests_per_file": max(file_function_counts),
                "min_tests_per_file": min(file_function_counts)
            }
        
        return organization
        
    except Exception as e:
        return {"error": f"Error analyzing test organization: {str(e)}"}


def find_tested_functions(all_functions: List[Function], test_functions: List[Function]) -> List[str]:
    """Find functions that appear to be tested (simplified heuristic)."""
    tested = []
    
    try:
        # Create a set of test function names for faster lookup
        test_names = {f.name.lower() for f in test_functions if hasattr(f, 'name')}
        
        for func in all_functions:
            if not hasattr(func, 'name') or is_test_function(func):
                continue
            
            func_name = func.name.lower()
            
            # Check if there's a test function that might test this function
            potential_test_names = [
                f"test_{func_name}",
                f"test_{func_name}_",
                f"{func_name}_test",
                f"should_{func_name}",
                f"when_{func_name}"
            ]
            
            if any(test_name in test_names or any(test_name in tn for tn in test_names) 
                   for test_name in potential_test_names):
                tested.append(func.name)
        
        return tested
        
    except Exception as e:
        return []


def find_tested_classes(all_classes: List[Class], test_classes: List[Class]) -> List[str]:
    """Find classes that appear to be tested (simplified heuristic)."""
    tested = []
    
    try:
        # Create a set of test class names for faster lookup
        test_names = {c.name.lower() for c in test_classes if hasattr(c, 'name')}
        
        for cls in all_classes:
            if not hasattr(cls, 'name') or is_test_class(cls):
                continue
            
            class_name = cls.name.lower()
            
            # Check if there's a test class that might test this class
            potential_test_names = [
                f"test{cls.name}",
                f"{cls.name}test",
                f"{cls.name}tests"
            ]
            
            if any(test_name.lower() in test_names for test_name in potential_test_names):
                tested.append(cls.name)
        
        return tested
        
    except Exception as e:
        return []


def split_test_files(codebase: Codebase, target_file: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Split a large test file into smaller, more focused test files.
    Based on the test splitting example from README4.md.
    
    Args:
        codebase: The codebase to modify
        target_file: Path to the test file to split
        dry_run: If True, only show what would be done
        
    Returns:
        Dictionary with splitting results
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        results = {
            "target_file": target_file,
            "groups_created": {},
            "functions_moved": 0,
            "dry_run": dry_run,
            "errors": []
        }
        
        # Get the target file
        try:
            file = codebase.get_file(target_file)
        except:
            return {"error": f"File {target_file} not found"}
        
        if not hasattr(file, 'functions'):
            return {"error": f"File {target_file} has no functions"}
        
        base_name = target_file.replace('.py', '')
        
        # Group tests by subpath (based on README4.md example)
        test_groups = {}
        for test_function in file.functions:
            if test_function.name.startswith('test_'):
                # Extract subpath from function name (first 3 parts)
                test_subpath = '_'.join(test_function.name.split('_')[:3])
                if test_subpath not in test_groups:
                    test_groups[test_subpath] = []
                test_groups[test_subpath].append(test_function)
        
        # Process each group
        for subpath, tests in test_groups.items():
            new_filename = f"{base_name}/{subpath}.py"
            
            group_info = {
                "new_file": new_filename,
                "test_count": len(tests),
                "functions": [test.name for test in tests]
            }
            
            if not dry_run:
                try:
                    # Create file if it doesn't exist
                    if not codebase.has_file(new_filename):
                        new_file = codebase.create_file(new_filename)
                    else:
                        new_file = codebase.get_file(new_filename)
                    
                    # Move each test in the group
                    for test_function in tests:
                        if hasattr(test_function, 'move_to_file'):
                            test_function.move_to_file(new_file, strategy="add_back_edge")
                            results["functions_moved"] += 1
                        
                except Exception as e:
                    results["errors"].append(f"Error moving {subpath}: {str(e)}")
            
            results["groups_created"][subpath] = group_info
        
        return results
        
    except Exception as e:
        return {"error": f"Error splitting test file: {str(e)}"}


def get_test_statistics(codebase: Codebase) -> Dict[str, Any]:
    """
    Get comprehensive test statistics for the codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Dictionary with test statistics
    """
    if not GRAPH_SITTER_AVAILABLE:
        return {"error": "Graph-sitter not available"}
    
    try:
        analysis = analyze_test_coverage(codebase)
        
        if "error" in analysis:
            return analysis
        
        stats = {
            "summary": {
                "total_test_functions": len(analysis["test_functions"]),
                "total_test_classes": len(analysis["test_classes"]),
                "total_test_files": len(analysis["test_files"]),
                "coverage_percentage": analysis["coverage_metrics"]["coverage_percentage"]
            },
            "file_analysis": {},
            "top_test_files": [],
            "recommendations": []
        }
        
        # Analyze test files
        if analysis["test_files"]:
            file_test_counts = Counter()
            for file_info in analysis["test_files"]:
                if isinstance(file_info, dict):
                    filepath = file_info.get("filepath", "unknown")
                    test_count = file_info.get("test_function_count", 0) + file_info.get("test_class_count", 0)
                    file_test_counts[filepath] = test_count
            
            stats["top_test_files"] = [
                {"file": filepath, "test_count": count}
                for filepath, count in file_test_counts.most_common(5)
            ]
        
        # Generate recommendations
        recommendations = []
        
        if stats["summary"]["coverage_percentage"] < 50:
            recommendations.append("Consider increasing test coverage - currently below 50%")
        
        if stats["summary"]["total_test_files"] > 0:
            avg_tests_per_file = stats["summary"]["total_test_functions"] / stats["summary"]["total_test_files"]
            if avg_tests_per_file > 50:
                recommendations.append("Some test files may be too large - consider splitting them")
            elif avg_tests_per_file < 5:
                recommendations.append("Test files seem small - consider consolidating related tests")
        
        if analysis["test_patterns"].get("naming_patterns", {}).get("test_prefix", 0) < stats["summary"]["total_test_functions"] * 0.8:
            recommendations.append("Consider standardizing test function naming with 'test_' prefix")
        
        stats["recommendations"] = recommendations
        
        return stats
        
    except Exception as e:
        return {"error": f"Error getting test statistics: {str(e)}"}


def generate_test_report(codebase: Codebase) -> str:
    """
    Generate a formatted test analysis report.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        Formatted string report
    """
    if not GRAPH_SITTER_AVAILABLE:
        return "❌ Graph-sitter not available for test analysis"
    
    try:
        stats = get_test_statistics(codebase)
        
        if "error" in stats:
            return f"❌ Error: {stats['error']}"
        
        report = []
        report.append("🧪 Test Analysis Report")
        report.append("=" * 50)
        
        # Summary
        summary = stats["summary"]
        report.append(f"📊 Test Summary:")
        report.append(f"  • Test Functions: {summary['total_test_functions']}")
        report.append(f"  • Test Classes: {summary['total_test_classes']}")
        report.append(f"  • Test Files: {summary['total_test_files']}")
        report.append(f"  • Coverage: {summary['coverage_percentage']:.1f}%")
        report.append("")
        
        # Top test files
        if stats["top_test_files"]:
            report.append("📁 Top Test Files by Test Count:")
            report.append("-" * 30)
            for file_info in stats["top_test_files"]:
                report.append(f"  • {file_info['file']} ({file_info['test_count']} tests)")
            report.append("")
        
        # Recommendations
        if stats["recommendations"]:
            report.append("💡 Recommendations:")
            report.append("-" * 30)
            for rec in stats["recommendations"]:
                report.append(f"  • {rec}")
            report.append("")
        
        # Coverage assessment
        coverage = summary['coverage_percentage']
        if coverage >= 80:
            report.append("✅ Excellent test coverage!")
        elif coverage >= 60:
            report.append("👍 Good test coverage")
        elif coverage >= 40:
            report.append("⚠️ Moderate test coverage - room for improvement")
        else:
            report.append("❌ Low test coverage - consider adding more tests")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"❌ Error generating test report: {str(e)}"

