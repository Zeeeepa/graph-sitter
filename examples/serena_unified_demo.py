#!/usr/bin/env python3
"""
Unified Serena Error Handling Demo

This demo shows the new unified error handling interface that's now directly
available on the Codebase class. No more complex initialization - just import
and use!

Features demonstrated:
- codebase.errors(): Get all errors in the codebase
- codebase.full_error_context(error_id): Get comprehensive context for specific error
- codebase.resolve_errors(): Auto-fix all errors
- codebase.resolve_error(error_id): Auto-fix specific error
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from graph_sitter import Codebase
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


def main():
    """Demonstrate the unified Serena error handling interface."""
    print("🚀 UNIFIED SERENA ERROR HANDLING DEMO")
    print("=" * 60)
    print("This demo shows the new unified error handling interface")
    print("that's now directly available on the Codebase class.")
    print()
    
    if not GRAPH_SITTER_AVAILABLE:
        print("❌ Graph-sitter not available. Please install it first.")
        return
    
    # Initialize codebase - that's it! No complex setup needed
    print("📁 Initializing codebase...")
    codebase = Codebase(".")
    print("✅ Codebase initialized with unified error handling")
    print()
    
    # 1. Get all errors in the codebase
    print("🔍 STEP 1: Getting all errors in the codebase")
    print("-" * 50)
    
    start_time = time.time()
    all_errors = codebase.errors()
    end_time = time.time()
    
    print(f"✅ Found {len(all_errors)} errors in {end_time - start_time:.2f} seconds")
    
    if all_errors:
        print("\n📊 Error Summary:")
        
        # Count by severity
        severity_counts = {}
        for error in all_errors:
            severity = error.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in severity_counts.items():
            emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}.get(severity, '📝')
            print(f"   {emoji} {severity.title()}: {count}")
        
        # Show first few errors
        print(f"\n📋 First {min(5, len(all_errors))} errors:")
        for i, error in enumerate(all_errors[:5]):
            print(f"   {i+1}. {error['file_path']}:{error['line']} - {error['message'][:80]}...")
            print(f"      ID: {error['id']}")
            print(f"      Has Fix: {'✅' if error.get('has_fix', False) else '❌'}")
    else:
        print("🎉 No errors found in the codebase!")
    
    print()
    
    # 2. Get full context for a specific error
    if all_errors:
        print("🔍 STEP 2: Getting full context for a specific error")
        print("-" * 50)
        
        # Pick the first error for demonstration
        sample_error = all_errors[0]
        print(f"📍 Analyzing error: {sample_error['id']}")
        print(f"   File: {sample_error['file_path']}:{sample_error['line']}")
        print(f"   Message: {sample_error['message']}")
        
        start_time = time.time()
        context = codebase.full_error_context(sample_error['id'])
        end_time = time.time()
        
        if context:
            print(f"✅ Got full context in {end_time - start_time:.2f} seconds")
            print("\n📋 Context Details:")
            print(f"   🔧 Fix Suggestions: {len(context.get('fix_suggestions', []))}")
            print(f"   🔗 Related Symbols: {len(context.get('related_symbols', []))}")
            print(f"   📦 Dependency Chain: {len(context.get('dependency_chain', []))}")
            print(f"   🛠️  Has Automatic Fix: {'✅' if context.get('has_fix', False) else '❌'}")
            
            # Show fix suggestions
            if context.get('fix_suggestions'):
                print(f"\n💡 Fix Suggestions:")
                for i, suggestion in enumerate(context['fix_suggestions'][:3]):
                    print(f"   {i+1}. {suggestion}")
            
            # Show code context if available
            if context.get('code_context'):
                print(f"\n📄 Code Context:")
                lines = context['code_context'].split('\n')
                for i, line in enumerate(lines[:5]):  # Show first 5 lines
                    print(f"   {i+1:2d}: {line}")
                if len(lines) > 5:
                    print(f"   ... ({len(lines) - 5} more lines)")
        else:
            print(f"❌ Could not get context for error {sample_error['id']}")
        
        print()
    
    # 3. Try to resolve specific error
    if all_errors:
        print("🔧 STEP 3: Attempting to resolve a specific error")
        print("-" * 50)
        
        # Find an error that might have a fix
        fixable_error = None
        for error in all_errors:
            if error.get('has_fix', False):
                fixable_error = error
                break
        
        if fixable_error:
            print(f"🎯 Attempting to fix error: {fixable_error['id']}")
            print(f"   File: {fixable_error['file_path']}:{fixable_error['line']}")
            print(f"   Message: {fixable_error['message']}")
            
            start_time = time.time()
            fix_result = codebase.resolve_error(fixable_error['id'])
            end_time = time.time()
            
            if fix_result:
                print(f"✅ Fix attempt completed in {end_time - start_time:.2f} seconds")
                print(f"   Success: {'✅' if fix_result.get('success', False) else '❌'}")
                
                if fix_result.get('success', False):
                    print(f"   Fix Applied: {fix_result.get('fix_applied', 'Unknown')}")
                    changes = fix_result.get('changes_made', [])
                    if changes:
                        print(f"   Changes Made: {len(changes)} changes")
                        for change in changes[:3]:  # Show first 3 changes
                            print(f"     - {change}")
                else:
                    print(f"   Error: {fix_result.get('error', 'Unknown error')}")
            else:
                print("❌ Fix attempt failed - no result returned")
        else:
            print("⚠️  No fixable errors found in the current set")
        
        print()
    
    # 4. Try to resolve all errors
    print("🔧 STEP 4: Attempting to resolve all fixable errors")
    print("-" * 50)
    
    # Count fixable errors
    fixable_errors = [error for error in all_errors if error.get('has_fix', False)]
    print(f"🎯 Found {len(fixable_errors)} potentially fixable errors out of {len(all_errors)} total")
    
    if fixable_errors:
        print("🚀 Attempting to fix all fixable errors...")
        
        start_time = time.time()
        bulk_result = codebase.resolve_errors()
        end_time = time.time()
        
        if bulk_result:
            print(f"✅ Bulk fix attempt completed in {end_time - start_time:.2f} seconds")
            print(f"\n📊 Results Summary:")
            print(f"   Total Errors: {bulk_result.get('total_errors', 0)}")
            print(f"   Attempted Fixes: {bulk_result.get('attempted_fixes', 0)}")
            print(f"   Successful Fixes: {bulk_result.get('successful_fixes', 0)}")
            print(f"   Failed Fixes: {bulk_result.get('failed_fixes', 0)}")
            
            success_rate = 0
            if bulk_result.get('attempted_fixes', 0) > 0:
                success_rate = (bulk_result.get('successful_fixes', 0) / bulk_result.get('attempted_fixes', 1)) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
            
            # Show individual results
            results = bulk_result.get('results', [])
            if results:
                print(f"\n📋 Individual Fix Results:")
                for i, result in enumerate(results[:5]):  # Show first 5 results
                    status = "✅" if result.get('success', False) else "❌"
                    error_id = result.get('error_id', 'unknown')[:50]  # Truncate long IDs
                    print(f"   {i+1}. {status} {error_id}")
                    if result.get('success', False):
                        print(f"      Fix: {result.get('fix_applied', 'Unknown')[:60]}...")
                    else:
                        print(f"      Error: {result.get('error', 'Unknown')[:60]}...")
                
                if len(results) > 5:
                    print(f"   ... and {len(results) - 5} more results")
        else:
            print("❌ Bulk fix attempt failed - no result returned")
    else:
        print("ℹ️  No fixable errors found - nothing to fix!")
    
    print()
    
    # 5. Final summary
    print("📊 FINAL SUMMARY")
    print("-" * 50)
    print("✅ Unified Serena error handling demo completed!")
    print()
    print("🎯 Key Features Demonstrated:")
    print("   • codebase.errors() - Get all errors with one simple call")
    print("   • codebase.full_error_context() - Get comprehensive error context")
    print("   • codebase.resolve_error() - Auto-fix specific errors")
    print("   • codebase.resolve_errors() - Auto-fix all errors")
    print()
    print("🚀 Benefits:")
    print("   • ✅ Unified Interface: All methods directly on Codebase class")
    print("   • ⚡ Lazy Loading: LSP features initialized only when needed")
    print("   • 🔄 Consistent Return Types: Standardized error objects")
    print("   • 🛡️  Graceful Error Handling: Proper fallbacks")
    print("   • 🚀 Performance: Efficient caching and batching")
    print()
    print("🎉 The new unified interface makes error handling simple and powerful!")


if __name__ == "__main__":
    main()

