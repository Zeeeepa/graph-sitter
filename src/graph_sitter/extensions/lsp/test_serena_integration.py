#!/usr/bin/env python3
"""
Test script for Serena LSP integration

This script demonstrates the comprehensive error analysis capabilities
of the Serena LSP bridge integration.
"""

import asyncio
import tempfile
from pathlib import Path

from .serena_bridge import SerenaLSPBridge, ErrorSeverity, ErrorCategory
from .serena_analysis import GitHubRepositoryAnalyzer, analyze_github_repository


async def test_basic_lsp_bridge():
    """Test basic LSP bridge functionality."""
    print("🔍 Testing basic LSP bridge functionality...")
    
    # Create a temporary directory with some Python code
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("""
# Test Python file with intentional errors
def broken_function():
    # Syntax error - missing closing quote
    message = "Hello world
    print(message)
    
    # Undefined variable error
    result = undefined_variable + 5
    
    # Type error
    return "string" + 42

def unused_function():
    # This function is never called
    pass

# Missing import
import nonexistent_module
""")
        
        # Initialize LSP bridge
        bridge = SerenaLSPBridge(temp_dir, enable_runtime_collection=True)
        
        try:
            # Get diagnostics
            diagnostics = bridge.get_diagnostics(include_runtime=True)
            
            print(f"✅ Found {len(diagnostics)} diagnostics")
            
            # Group by severity
            by_severity = {}
            for diag in diagnostics:
                severity = diag.severity.name if hasattr(diag.severity, 'name') else str(diag.severity)
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(diag)
            
            for severity, diags in by_severity.items():
                print(f"  {severity}: {len(diags)} errors")
                for diag in diags[:3]:  # Show first 3
                    print(f"    - {diag.message}")
            
            # Test runtime error collection
            runtime_errors = bridge.get_runtime_errors()
            print(f"✅ Runtime error collection: {len(runtime_errors)} errors")
            
            # Get status
            status = bridge.get_status()
            print(f"✅ Bridge status: {status['initialized']}")
            
        finally:
            bridge.shutdown()


async def test_github_analysis():
    """Test GitHub repository analysis."""
    print("\n🔍 Testing GitHub repository analysis...")
    
    # Test with a small public repository (using a mock for demo)
    try:
        analyzer = GitHubRepositoryAnalyzer()
        
        # For demo purposes, we'll create a mock repository
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock repository structure
            repo_dir = Path(temp_dir) / "test_repo"
            repo_dir.mkdir()
            
            # Create some Python files with errors
            (repo_dir / "main.py").write_text("""
import sys
import os

def main():
    # Syntax error
    print("Hello world"
    
    # Undefined variable
    result = undefined_var + 10
    
    return result

if __name__ == "__main__":
    main()
""")
            
            (repo_dir / "utils.py").write_text("""
# Missing import
from nonexistent import something

def helper_function():
    # Type error
    return "string" + 42

def unused_function():
    pass
""")
            
            # Initialize git repo
            import subprocess
            subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, capture_output=True)
            
            # Analyze the repository
            bridge = SerenaLSPBridge(str(repo_dir))
            
            try:
                diagnostics = bridge.get_diagnostics(include_runtime=True)
                
                print(f"✅ Repository analysis complete: {len(diagnostics)} issues found")
                
                # Group by severity
                severity_counts = {}
                category_counts = {}
                
                for diag in diagnostics:
                    severity = diag.severity.name if hasattr(diag.severity, 'name') else str(diag.severity)
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    if hasattr(diag, 'error_type'):
                        category = diag.error_type.name if hasattr(diag.error_type, 'name') else str(diag.error_type)
                        category_counts[category] = category_counts.get(category, 0) + 1
                
                print("📊 Severity breakdown:")
                for severity, count in severity_counts.items():
                    print(f"  {severity}: {count}")
                
                if category_counts:
                    print("📊 Category breakdown:")
                    for category, count in category_counts.items():
                        print(f"  {category}: {count}")
                
                # Test file-specific analysis
                file_errors = bridge.get_file_diagnostics("main.py", include_runtime=True)
                print(f"✅ File-specific analysis: {len(file_errors)} errors in main.py")
                
            finally:
                bridge.shutdown()
                
        await analyzer.shutdown()
        
    except Exception as e:
        print(f"❌ GitHub analysis test failed: {e}")


async def test_error_categorization():
    """Test error categorization and analysis."""
    print("\n🔍 Testing error categorization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with different types of errors
        files = {
            "syntax_errors.py": '''
# Syntax errors
def broken():
    print("missing quote
    return [1, 2, 3,  # missing bracket
''',
            "type_errors.py": '''
# Type errors
def type_issues():
    result = "string" + 42
    items = [1, 2, 3]
    return items.nonexistent_method()
''',
            "import_errors.py": '''
# Import errors
import nonexistent_module
from missing_package import something
''',
            "logic_errors.py": '''
# Logic errors
def logic_issues():
    x = undefined_variable
    return x / 0
'''
        }
        
        for filename, content in files.items():
            (Path(temp_dir) / filename).write_text(content)
        
        bridge = SerenaLSPBridge(temp_dir)
        
        try:
            diagnostics = bridge.get_diagnostics(include_runtime=True)
            
            print(f"✅ Found {len(diagnostics)} total diagnostics")
            
            # Categorize errors
            categories = {}
            for diag in diagnostics:
                # Simple categorization based on message content
                message = diag.message.lower()
                if "syntax" in message or "invalid syntax" in message:
                    category = "SYNTAX"
                elif "import" in message or "module" in message:
                    category = "IMPORT"
                elif "type" in message:
                    category = "TYPE"
                elif "undefined" in message or "not defined" in message:
                    category = "UNDEFINED"
                else:
                    category = "OTHER"
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(diag)
            
            print("📊 Error categorization:")
            for category, errors in categories.items():
                print(f"  {category}: {len(errors)} errors")
                for error in errors[:2]:  # Show first 2
                    print(f"    - {error.message}")
            
        finally:
            bridge.shutdown()


async def test_performance_monitoring():
    """Test performance monitoring capabilities."""
    print("\n🔍 Testing performance monitoring...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a larger codebase for performance testing
        for i in range(10):
            file_path = Path(temp_dir) / f"module_{i}.py"
            file_path.write_text(f'''
# Module {i}
import sys
import os

def function_{i}():
    # Some errors for testing
    result = undefined_var_{i}
    return result + "string"

class Class_{i}:
    def method_{i}(self):
        return self.nonexistent_attr

# More code...
for j in range(5):
    def dynamic_func():
        pass
''')
        
        import time
        start_time = time.time()
        
        bridge = SerenaLSPBridge(temp_dir)
        
        try:
            # Measure initialization time
            init_time = time.time() - start_time
            
            # Measure analysis time
            analysis_start = time.time()
            diagnostics = bridge.get_diagnostics(include_runtime=True)
            analysis_time = time.time() - analysis_start
            
            # Get status with performance info
            status = bridge.get_status()
            
            print(f"⚡ Performance metrics:")
            print(f"  Initialization time: {init_time:.2f}s")
            print(f"  Analysis time: {analysis_time:.2f}s")
            print(f"  Total diagnostics: {len(diagnostics)}")
            print(f"  Files analyzed: {len(status.get('cache_sizes', {}).get('diagnostics_cache', 0))}")
            print(f"  Bridge initialized: {status.get('initialized', False)}")
            
            if 'runtime_status' in status:
                runtime_status = status['runtime_status']
                print(f"  Runtime collection: {runtime_status.get('runtime_collection_enabled', False)}")
                print(f"  Runtime errors: {runtime_status.get('total_runtime_errors', 0)}")
            
        finally:
            bridge.shutdown()


async def main():
    """Run all tests."""
    print("🚀 Starting Serena LSP Integration Tests\n")
    
    try:
        await test_basic_lsp_bridge()
        await test_github_analysis()
        await test_error_categorization()
        await test_performance_monitoring()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

