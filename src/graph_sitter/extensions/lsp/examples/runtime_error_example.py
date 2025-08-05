"""
Example usage of the Enhanced Serena LSP Bridge with Runtime Error Collection

This example demonstrates how to use the enhanced LSP bridge to collect
both static analysis errors and runtime errors with comprehensive context.
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import the LSP modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from serena_bridge import SerenaLSPBridge, ErrorInfo


def example_function_with_errors():
    """Function that will generate various types of runtime errors."""
    
    # This will cause a NameError
    try:
        print(undefined_variable)
    except NameError as e:
        print(f"Caught NameError: {e}")
    
    # This will cause an AttributeError
    try:
        none_value = None
        none_value.some_attribute
    except AttributeError as e:
        print(f"Caught AttributeError: {e}")
    
    # This will cause a TypeError
    try:
        result = "string" + 42
    except TypeError as e:
        print(f"Caught TypeError: {e}")
    
    # This will cause an IndexError
    try:
        my_list = [1, 2, 3]
        print(my_list[10])
    except IndexError as e:
        print(f"Caught IndexError: {e}")
    
    # This will cause a KeyError
    try:
        my_dict = {"key1": "value1"}
        print(my_dict["nonexistent_key"])
    except KeyError as e:
        print(f"Caught KeyError: {e}")
    
    # This will cause a ZeroDivisionError
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        print(f"Caught ZeroDivisionError: {e}")


def demonstrate_lsp_bridge():
    """Demonstrate the enhanced LSP bridge capabilities."""
    
    # Get the repository path (assuming we're in a git repo)
    repo_path = Path(__file__).parent.parent.parent.parent.parent
    
    print(f"Initializing LSP Bridge for repository: {repo_path}")
    
    # Initialize the LSP bridge with runtime error collection enabled
    lsp_bridge = SerenaLSPBridge(
        repo_path=str(repo_path),
        enable_runtime_collection=True
    )
    
    try:
        # Get initial status
        status = lsp_bridge.get_status()
        print("\n=== LSP Bridge Status ===")
        print(f"Initialized: {status['initialized']}")
        print(f"Language Servers: {status['language_servers']}")
        print(f"Runtime Collection Available: {status['runtime_collection']['available']}")
        print(f"Runtime Collection Active: {status['runtime_collection']['active']}")
        print(f"Serena Integration: {status['serena_components']['solidlsp_available']}")
        
        # Get static analysis errors
        print("\n=== Static Analysis Errors ===")
        static_errors = lsp_bridge.get_static_errors()
        print(f"Found {len(static_errors)} static analysis errors")
        for error in static_errors[:5]:  # Show first 5
            print(f"  {error}")
        
        # Generate some runtime errors
        print("\n=== Generating Runtime Errors ===")
        example_function_with_errors()
        
        # Wait a moment for errors to be collected
        time.sleep(1)
        
        # Get runtime errors
        print("\n=== Runtime Errors ===")
        runtime_errors = lsp_bridge.get_runtime_errors()
        print(f"Found {len(runtime_errors)} runtime errors")
        for error in runtime_errors:
            print(f"  {error}")
            if error.runtime_context:
                print(f"    Exception Type: {error.runtime_context.exception_type}")
                print(f"    Stack Trace Lines: {len(error.runtime_context.stack_trace)}")
                print(f"    Local Variables: {len(error.runtime_context.local_variables)}")
                print(f"    Fix Suggestions: {len(error.fix_suggestions)}")
                if error.fix_suggestions:
                    for suggestion in error.fix_suggestions[:2]:  # Show first 2
                        print(f"      - {suggestion}")
        
        # Get comprehensive error summary
        print("\n=== Runtime Error Summary ===")
        summary = lsp_bridge.get_runtime_error_summary()
        print(f"Total Runtime Errors: {summary['total_errors']}")
        print(f"Collection Active: {summary['collection_active']}")
        print(f"Errors by Type: {summary['errors_by_type']}")
        print(f"Errors by File: {summary['errors_by_file']}")
        
        # Get all errors with full context
        print("\n=== All Errors with Context ===")
        all_errors_with_context = lsp_bridge.get_all_errors_with_context()
        print(f"Total errors with context: {len(all_errors_with_context)}")
        
        # Show detailed context for first runtime error
        runtime_errors_with_context = [
            error for error in all_errors_with_context 
            if error.get('runtime') is not None
        ]
        
        if runtime_errors_with_context:
            print("\n=== Detailed Runtime Error Context ===")
            first_runtime_error = runtime_errors_with_context[0]
            print(f"File: {first_runtime_error['basic_info']['file_path']}")
            print(f"Line: {first_runtime_error['basic_info']['line']}")
            print(f"Message: {first_runtime_error['basic_info']['message']}")
            print(f"Exception Type: {first_runtime_error['runtime']['exception_type']}")
            print(f"Execution Path: {first_runtime_error['runtime']['execution_path']}")
            print("Local Variables:")
            for var_name, var_value in list(first_runtime_error['runtime']['local_variables'].items())[:3]:
                print(f"  {var_name}: {var_value}")
        
        # Test file-specific diagnostics
        current_file = str(Path(__file__).absolute())
        print(f"\n=== File-Specific Diagnostics for {Path(current_file).name} ===")
        file_diagnostics = lsp_bridge.get_file_diagnostics(current_file, include_runtime=True)
        print(f"Found {len(file_diagnostics)} diagnostics for this file")
        for diag in file_diagnostics:
            print(f"  {diag}")
            if diag.is_runtime_error:
                print(f"    Runtime Error with {len(diag.fix_suggestions)} suggestions")
        
        # Clear runtime errors
        print("\n=== Clearing Runtime Errors ===")
        lsp_bridge.clear_runtime_errors()
        runtime_errors_after_clear = lsp_bridge.get_runtime_errors()
        print(f"Runtime errors after clear: {len(runtime_errors_after_clear)}")
        
    finally:
        # Always shutdown properly
        print("\n=== Shutting Down LSP Bridge ===")
        lsp_bridge.shutdown()
        print("LSP Bridge shutdown complete")


def demonstrate_error_context():
    """Demonstrate detailed error context extraction."""
    
    print("\n" + "="*50)
    print("DETAILED ERROR CONTEXT DEMONSTRATION")
    print("="*50)
    
    repo_path = Path(__file__).parent.parent.parent.parent.parent
    lsp_bridge = SerenaLSPBridge(str(repo_path), enable_runtime_collection=True)
    
    try:
        # Create a more complex error scenario
        def nested_function_level_3():
            local_var_3 = "level 3 variable"
            # This will cause an error
            return undefined_variable_level_3
        
        def nested_function_level_2():
            local_var_2 = {"key": "level 2 data"}
            return nested_function_level_3()
        
        def nested_function_level_1():
            local_var_1 = [1, 2, 3, 4, 5]
            return nested_function_level_2()
        
        try:
            nested_function_level_1()
        except NameError:
            pass  # Error will be collected by runtime collector
        
        # Wait for error collection
        time.sleep(1)
        
        # Get the collected error with full context
        runtime_errors = lsp_bridge.get_runtime_errors()
        if runtime_errors:
            error = runtime_errors[-1]  # Get the most recent error
            context = error.get_full_context()
            
            print("COMPREHENSIVE ERROR CONTEXT:")
            print(f"File: {context['basic_info']['file_path']}")
            print(f"Line: {context['basic_info']['line']}")
            print(f"Error Type: {context['basic_info']['error_type']}")
            print(f"Message: {context['basic_info']['message']}")
            
            if 'runtime' in context:
                runtime = context['runtime']
                print(f"\nException Type: {runtime['exception_type']}")
                print(f"Thread ID: {runtime['thread_id']}")
                print(f"Process ID: {runtime['process_id']}")
                print(f"Timestamp: {runtime['timestamp']}")
                
                print(f"\nExecution Path ({len(runtime['execution_path'])} levels):")
                for i, func_name in enumerate(runtime['execution_path']):
                    print(f"  {i+1}. {func_name}")
                
                print(f"\nLocal Variables ({len(runtime['local_variables'])}):")
                for var_name, var_value in runtime['local_variables'].items():
                    print(f"  {var_name}: {var_value}")
                
                print(f"\nStack Trace ({len(runtime['stack_trace'])} lines):")
                for line in runtime['stack_trace'][:5]:  # Show first 5 lines
                    print(f"  {line.strip()}")
            
            print(f"\nFix Suggestions ({len(context['fix_suggestions'])}):")
            for suggestion in context['fix_suggestions']:
                print(f"  - {suggestion}")
    
    finally:
        lsp_bridge.shutdown()


if __name__ == "__main__":
    print("Enhanced Serena LSP Bridge Runtime Error Collection Demo")
    print("="*60)
    
    try:
        demonstrate_lsp_bridge()
        demonstrate_error_context()
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nDemo completed!")

