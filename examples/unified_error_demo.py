#!/usr/bin/env python3
"""
Unified Error Interface Demo

This demo showcases the new unified error interface for Serena LSP integration.
It demonstrates all the key features:

- codebase.errors() - Get all errors with filtering
- codebase.full_error_context(error_id) - Get comprehensive error context
- codebase.resolve_errors() - Auto-fix multiple errors
- codebase.resolve_error(error_id) - Fix specific error

The demo creates a test project with various error types and shows how
the unified interface can detect, analyze, and fix them automatically.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import json

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    print("Please install graph-sitter: pip install -e .")
    GRAPH_SITTER_AVAILABLE = False


def create_test_project(project_path: Path) -> None:
    """Create a test project with various error types."""
    print(f"📁 Creating test project at: {project_path}")
    
    # Create project structure
    (project_path / "src").mkdir(parents=True, exist_ok=True)
    (project_path / "tests").mkdir(parents=True, exist_ok=True)
    
    # File 1: Unused imports and variables
    unused_code = '''import os
import sys
import json  # Unused import
from typing import List, Dict, Optional  # Mixed usage

def process_data(data: List[str]) -> None:
    """Process some data."""
    unused_variable = "never used"
    result = []  # Unused variable
    
    for item in data:
        print(item)
    
    sys.exit(0)  # Uses sys, so import is needed
'''
    
    with open(project_path / "src" / "unused_code.py", "w") as f:
        f.write(unused_code)
    
    # File 2: Missing imports
    missing_imports = '''def get_current_directory():
    """Get the current working directory."""
    return os.getcwd()  # Missing import for os

def serialize_data(data):
    """Serialize data to JSON."""
    return json.dumps(data)  # Missing import for json

def get_file_path(filename):
    """Get full file path."""
    return Path(filename).absolute()  # Missing import for Path
'''
    
    with open(project_path / "src" / "missing_imports.py", "w") as f:
        f.write(missing_imports)
    
    # File 3: Style issues
    style_issues = '''def bad_style(x,y,z):
    result=x+y+z
    very_long_line_that_exceeds_the_recommended_line_length_limit_and_should_be_broken_into_multiple_lines = True
    return result

class BadClass:
    def method1(self):pass
    def method2(self):pass


def another_function():
    pass
'''
    
    with open(project_path / "src" / "style_issues.py", "w") as f:
        f.write(style_issues)
    
    # File 4: Type errors (if mypy is available)
    type_errors = '''def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def main():
    # Type error: passing strings to function expecting ints
    result = add_numbers("hello", "world")
    
    # Type error: incompatible assignment
    number: int = "not a number"
    
    return result
'''
    
    with open(project_path / "src" / "type_errors.py", "w") as f:
        f.write(type_errors)
    
    # File 5: Correct code (should have no errors)
    correct_code = '''from typing import List, Optional

def well_written_function(numbers: List[int]) -> Optional[int]:
    """
    Calculate the sum of positive numbers in a list.
    
    Args:
        numbers: List of integers to process
        
    Returns:
        Sum of positive numbers, or None if no positive numbers found
    """
    positive_numbers = [n for n in numbers if n > 0]
    
    if not positive_numbers:
        return None
    
    return sum(positive_numbers)

class WellWrittenClass:
    """Example of a well-written class."""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    def greet(self) -> str:
        """Return a greeting message."""
        return f"Hello, {self.name}!"
'''
    
    with open(project_path / "src" / "correct_code.py", "w") as f:
        f.write(correct_code)
    
    # Create a simple test file
    test_code = '''import unittest
from src.correct_code import well_written_function

class TestWellWrittenFunction(unittest.TestCase):
    def test_positive_numbers(self):
        result = well_written_function([1, 2, 3, -1, -2])
        self.assertEqual(result, 6)
    
    def test_no_positive_numbers(self):
        result = well_written_function([-1, -2, -3])
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
'''
    
    with open(project_path / "tests" / "test_correct_code.py", "w") as f:
        f.write(test_code)
    
    print("✅ Test project created successfully")


def demonstrate_error_detection(codebase: Codebase) -> List[Any]:
    """Demonstrate error detection capabilities."""
    print("\n" + "=" * 60)
    print("🔍 STEP 1: ERROR DETECTION")
    print("=" * 60)
    
    # Get all errors
    print("📊 Getting all errors in the codebase...")
    all_errors = codebase.errors()
    
    print(f"✅ Found {len(all_errors)} total issues")
    
    # Get error summary
    summary = codebase.error_summary()
    print(f"\n📈 ERROR SUMMARY:")
    print(f"   ❌ Errors: {summary.total_errors}")
    print(f"   ⚠️  Warnings: {summary.total_warnings}")
    print(f"   ℹ️  Info: {summary.total_info}")
    print(f"   💡 Hints: {summary.total_hints}")
    print(f"   🔧 Auto-fixable: {summary.auto_fixable}")
    print(f"   🛠️  Manually fixable: {summary.manually_fixable}")
    
    # Show errors by category
    if summary.by_category:
        print(f"\n📂 ERRORS BY CATEGORY:")
        for category, count in summary.by_category.items():
            print(f"   {category}: {count}")
    
    # Show error hotspots
    if summary.error_hotspots:
        print(f"\n🔥 ERROR HOTSPOTS:")
        for hotspot in summary.error_hotspots[:5]:
            print(f"   {hotspot['file']}: {hotspot['error_count']} errors")
    
    # Show some example errors
    if all_errors:
        print(f"\n📝 EXAMPLE ERRORS:")
        for i, error in enumerate(all_errors[:5]):
            severity_emoji = {
                1: "❌",  # ERROR
                2: "⚠️",   # WARNING
                3: "ℹ️",   # INFO
                4: "💡"   # HINT
            }.get(error.severity.value, "❓")
            
            print(f"   {i+1}. {severity_emoji} {error.location.file_path}:{error.location.line}")
            print(f"      {error.message}")
            print(f"      Source: {error.source}, Category: {error.category.value}")
            if error.auto_fixable:
                print(f"      🔧 Auto-fixable")
            print()
    
    return all_errors


def demonstrate_error_context(codebase: Codebase, errors: List[Any]) -> None:
    """Demonstrate comprehensive error context analysis."""
    print("\n" + "=" * 60)
    print("🔍 STEP 2: ERROR CONTEXT ANALYSIS")
    print("=" * 60)
    
    if not errors:
        print("⚠️  No errors found for context analysis")
        return
    
    # Analyze the first few errors in detail
    for i, error in enumerate(errors[:3]):
        print(f"\n📋 ANALYZING ERROR {i+1}: {error.id}")
        print(f"   Location: {error.location}")
        print(f"   Message: {error.message}")
        
        # Get full context
        print("   🔍 Getting comprehensive context...")
        context = codebase.full_error_context(error.id)
        
        if context:
            print("   ✅ Context retrieved successfully")
            
            # Show surrounding code
            if context.surrounding_code:
                print(f"\n   📄 SURROUNDING CODE:")
                lines = context.surrounding_code.split('\n')
                for line in lines[:10]:  # Show first 10 lines
                    print(f"   {line}")
                if len(lines) > 10:
                    print(f"   ... ({len(lines) - 10} more lines)")
            
            # Show function context
            if context.function_context:
                func = context.function_context
                print(f"\n   🔧 FUNCTION CONTEXT:")
                print(f"      Function: {func.get('name', 'unknown')}")
                if func.get('args'):
                    print(f"      Arguments: {', '.join(func['args'])}")
                if func.get('returns'):
                    print(f"      Returns: {func['returns']}")
            
            # Show class context
            if context.class_context:
                cls = context.class_context
                print(f"\n   📦 CLASS CONTEXT:")
                print(f"      Class: {cls.get('name', 'unknown')}")
                if cls.get('bases'):
                    print(f"      Inherits from: {', '.join(cls['bases'])}")
                if cls.get('methods'):
                    print(f"      Methods: {', '.join(cls['methods'])}")
            
            # Show symbol information
            if context.symbol_definitions:
                print(f"\n   🎯 SYMBOL DEFINITIONS:")
                for sym_def in context.symbol_definitions[:3]:
                    print(f"      {sym_def.get('type', 'unknown')} {sym_def.get('name', 'unknown')} "
                          f"at {sym_def.get('file', 'unknown')}:{sym_def.get('line', 0)}")
            
            # Show related errors
            if context.related_errors:
                print(f"\n   🔗 RELATED ERRORS: {len(context.related_errors)}")
                for rel_error in context.related_errors[:2]:
                    print(f"      {rel_error.location}: {rel_error.message[:50]}...")
            
            # Show fix recommendations
            if context.recommended_fixes:
                print(f"\n   🔧 RECOMMENDED FIXES:")
                for fix in context.recommended_fixes[:3]:
                    confidence_emoji = {
                        "high": "🟢",
                        "medium": "🟡", 
                        "low": "🔴",
                        "none": "⚫"
                    }.get(fix.confidence.value, "❓")
                    
                    print(f"      {confidence_emoji} {fix.title}")
                    print(f"         {fix.description}")
                    if fix.requires_user_input:
                        print(f"         ⚠️  Requires user input")
            
            print(f"   📊 Fix Priority: {context.fix_priority}")
        else:
            print("   ❌ Could not retrieve context (LSP may not be available)")


def demonstrate_error_resolution(codebase: Codebase) -> None:
    """Demonstrate automatic error resolution."""
    print("\n" + "=" * 60)
    print("🔧 STEP 3: AUTOMATIC ERROR RESOLUTION")
    print("=" * 60)
    
    # Get fixable errors
    print("🔍 Finding auto-fixable errors...")
    fixable_errors = codebase.get_fixable_errors(auto_fixable_only=True)
    
    print(f"✅ Found {len(fixable_errors)} auto-fixable errors")
    
    if not fixable_errors:
        print("⚠️  No auto-fixable errors found")
        return
    
    # Show what we can fix
    print(f"\n🔧 AUTO-FIXABLE ERRORS:")
    for i, error in enumerate(fixable_errors[:5]):
        print(f"   {i+1}. {error.location.file_path}:{error.location.line}")
        print(f"      {error.message}")
        print(f"      Available fixes: {len(error.fixes)}")
        
        # Show fix preview
        preview = codebase.preview_fix(error.id)
        if preview.get('can_resolve'):
            print(f"      🔧 Can auto-fix: {preview['fix_title']}")
            print(f"      📊 Confidence: {preview['confidence']}")
            print(f"      💥 Impact: {preview['estimated_impact']}")
        print()
    
    # Ask user for confirmation
    print("🤔 Would you like to auto-fix these errors? (y/n): ", end="")
    try:
        response = input().lower().strip()
    except (EOFError, KeyboardInterrupt):
        response = "n"
    
    if response == "y":
        print("\n🚀 Applying automatic fixes...")
        
        # Apply fixes with safety limits
        results = codebase.resolve_errors(
            auto_fixable_only=True,
            max_fixes=10  # Safety limit
        )
        
        print(f"✅ Fix application complete!")
        print(f"📊 RESOLUTION RESULTS:")
        
        successful_fixes = [r for r in results if r.success]
        failed_fixes = [r for r in results if not r.success]
        
        print(f"   ✅ Successful: {len(successful_fixes)}")
        print(f"   ❌ Failed: {len(failed_fixes)}")
        
        # Show successful fixes
        if successful_fixes:
            print(f"\n✅ SUCCESSFUL FIXES:")
            for result in successful_fixes:
                print(f"   {result.error_id}: {result.message}")
                if result.files_modified:
                    print(f"      Modified: {', '.join(result.files_modified)}")
        
        # Show failed fixes
        if failed_fixes:
            print(f"\n❌ FAILED FIXES:")
            for result in failed_fixes:
                print(f"   {result.error_id}: {result.message}")
                if result.remaining_issues:
                    print(f"      Issues: {', '.join(result.remaining_issues)}")
        
        # Show updated error count
        print(f"\n🔄 Refreshing error count...")
        codebase.refresh_errors()
        
        updated_errors = codebase.errors()
        print(f"📊 Errors after fixes: {len(updated_errors)} (was {len(fixable_errors)})")
        
    else:
        print("⏭️  Skipping automatic fixes")


def demonstrate_specific_error_resolution(codebase: Codebase) -> None:
    """Demonstrate resolving a specific error."""
    print("\n" + "=" * 60)
    print("🎯 STEP 4: SPECIFIC ERROR RESOLUTION")
    print("=" * 60)
    
    # Get all errors
    all_errors = codebase.errors()
    
    if not all_errors:
        print("⚠️  No errors found for specific resolution")
        return
    
    # Find a good example error to resolve
    target_error = None
    for error in all_errors:
        if error.auto_fixable and "unused" in error.message.lower():
            target_error = error
            break
    
    if not target_error:
        # Just pick the first auto-fixable error
        for error in all_errors:
            if error.auto_fixable:
                target_error = error
                break
    
    if not target_error:
        print("⚠️  No suitable error found for specific resolution demo")
        return
    
    print(f"🎯 Selected error for resolution:")
    print(f"   ID: {target_error.id}")
    print(f"   Location: {target_error.location}")
    print(f"   Message: {target_error.message}")
    print(f"   Auto-fixable: {target_error.auto_fixable}")
    
    # Preview the fix
    print(f"\n🔍 Previewing fix...")
    preview = codebase.preview_fix(target_error.id)
    
    if preview.get('can_resolve'):
        print(f"✅ Fix available:")
        print(f"   Title: {preview['fix_title']}")
        print(f"   Description: {preview.get('fix_description', 'N/A')}")
        print(f"   Confidence: {preview['confidence']}")
        print(f"   Requires input: {preview['requires_user_input']}")
        print(f"   Impact: {preview['estimated_impact']}")
        
        # Apply the specific fix
        print(f"\n🔧 Applying fix to error {target_error.id}...")
        result = codebase.resolve_error(target_error.id)
        
        if result.success:
            print(f"✅ Fix applied successfully!")
            print(f"   Message: {result.message}")
            if result.applied_fixes:
                print(f"   Applied fixes: {', '.join(result.applied_fixes)}")
            if result.files_modified:
                print(f"   Modified files: {', '.join(result.files_modified)}")
        else:
            print(f"❌ Fix failed:")
            print(f"   Message: {result.message}")
            if result.remaining_issues:
                print(f"   Issues: {', '.join(result.remaining_issues)}")
    else:
        print(f"❌ Cannot resolve this error:")
        print(f"   Reason: {preview.get('reason', 'Unknown')}")


def demonstrate_filtering_and_querying(codebase: Codebase) -> None:
    """Demonstrate error filtering and querying capabilities."""
    print("\n" + "=" * 60)
    print("🔍 STEP 5: ERROR FILTERING AND QUERYING")
    print("=" * 60)
    
    # Get errors with different filters
    print("📊 Testing different error filters...")
    
    # All errors
    all_errors = codebase.errors()
    print(f"   All errors: {len(all_errors)}")
    
    # Only errors (no warnings)
    only_errors = codebase.errors(include_warnings=False, include_hints=False)
    print(f"   Only errors: {len(only_errors)}")
    
    # Include everything
    everything = codebase.errors(include_warnings=True, include_hints=True)
    print(f"   All issues: {len(everything)}")
    
    # Filter by category
    categories = ["syntax", "type", "import", "undefined", "unused", "style"]
    for category in categories:
        cat_errors = codebase.errors(category=category)
        if cat_errors:
            print(f"   {category.title()} errors: {len(cat_errors)}")
    
    # Filter by source
    sources = set(error.source for error in all_errors)
    for source in sources:
        source_errors = codebase.errors(source=source)
        print(f"   From {source}: {len(source_errors)}")
    
    # Filter by file
    files_with_errors = set(error.location.file_path for error in all_errors)
    for file_path in list(files_with_errors)[:3]:  # Show first 3 files
        file_errors = codebase.errors(file_path=file_path)
        print(f"   In {file_path}: {len(file_errors)}")


def save_results_to_file(codebase: Codebase, output_file: str) -> None:
    """Save analysis results to a JSON file."""
    print(f"\n💾 Saving results to {output_file}...")
    
    try:
        # Collect all data
        all_errors = codebase.errors(include_warnings=True, include_hints=True)
        summary = codebase.error_summary()
        fixable_errors = codebase.get_fixable_errors()
        
        # Create comprehensive report
        report = {
            "timestamp": "2024-01-01T00:00:00Z",  # Would use real timestamp
            "total_errors": len(all_errors),
            "summary": summary.to_dict() if hasattr(summary, 'to_dict') else {},
            "fixable_errors": len(fixable_errors),
            "errors": [
                error.to_dict() if hasattr(error, 'to_dict') else {
                    "id": getattr(error, 'id', 'unknown'),
                    "message": getattr(error, 'message', 'unknown'),
                    "severity": getattr(error, 'severity', {}).name if hasattr(getattr(error, 'severity', {}), 'name') else 'unknown',
                    "location": str(getattr(error, 'location', 'unknown')),
                    "source": getattr(error, 'source', 'unknown'),
                    "auto_fixable": getattr(error, 'auto_fixable', False)
                }
                for error in all_errors[:50]  # Limit to first 50 for demo
            ]
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Results saved to {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main demo function."""
    print("🚀 UNIFIED SERENA ERROR INTERFACE DEMO")
    print("=" * 80)
    print("This demo showcases the new unified error interface that provides:")
    print("• Comprehensive error detection from all LSP servers")
    print("• Detailed error context and analysis")
    print("• Automatic error resolution with safety checks")
    print("• Flexible filtering and querying capabilities")
    print("=" * 80)
    
    if not GRAPH_SITTER_AVAILABLE:
        print("❌ Cannot run demo without graph-sitter")
        return
    
    # Create temporary project
    temp_dir = tempfile.mkdtemp(prefix="serena_demo_")
    project_path = Path(temp_dir)
    
    try:
        # Set up test project
        create_test_project(project_path)
        
        # Initialize codebase with Serena
        print(f"\n🔧 Initializing Codebase with Serena integration...")
        codebase = Codebase(str(project_path))
        
        # Check if unified error interface is available
        if not hasattr(codebase, 'errors'):
            print("❌ Unified error interface not available")
            print("   This might be because:")
            print("   1. Serena integration is not properly installed")
            print("   2. LSP servers are not available")
            print("   3. The unified interface is not yet integrated")
            return
        
        print("✅ Unified error interface is available!")
        
        # Run the demo steps
        errors = demonstrate_error_detection(codebase)
        demonstrate_error_context(codebase, errors)
        demonstrate_error_resolution(codebase)
        demonstrate_specific_error_resolution(codebase)
        demonstrate_filtering_and_querying(codebase)
        
        # Save results
        output_file = "serena_demo_results.json"
        save_results_to_file(codebase, output_file)
        
        print("\n" + "=" * 80)
        print("🎉 DEMO COMPLETE!")
        print("=" * 80)
        print("The unified Serena error interface provides a powerful,")
        print("consistent way to detect, analyze, and fix code errors")
        print("automatically. This makes code quality maintenance much")
        print("easier and more efficient!")
        print()
        print("Key benefits demonstrated:")
        print("✅ Unified API for all error operations")
        print("✅ Comprehensive error context and analysis")
        print("✅ Safe automatic error resolution")
        print("✅ Flexible filtering and querying")
        print("✅ Real-time error detection and updates")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"⚠️  Could not clean up {temp_dir}: {e}")


if __name__ == "__main__":
    main()

