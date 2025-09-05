#!/usr/bin/env python3
"""
Comprehensive Example: Graph-Sitter LSP Extension with Runtime Error Collection

This example demonstrates all features of the enhanced LSP extension including:
- Runtime error collection and analysis
- Serena LSP integration with graceful fallback
- Comprehensive error context analysis
- Intelligent fix suggestion generation
- Real-time diagnostics processing

Usage:
    python comprehensive_example.py [repo_path]
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from serena_bridge import SerenaLSPBridge, ErrorInfo, create_serena_bridge, create_error_info, ErrorType
from serena_protocol import SerenaProtocolExtension, create_serena_protocol_extension
from runtime_collector import RuntimeErrorCollector, create_runtime_collector

# Import DiagnosticSeverity with fallback
try:
    from solidlsp.ls_types import DiagnosticSeverity
except ImportError:
    from enum import IntEnum
    class DiagnosticSeverity(IntEnum):
        ERROR = 1
        WARNING = 2
        INFORMATION = 3
        HINT = 4


def demonstrate_basic_usage():
    """Demonstrate basic usage of the LSP extension."""
    print("=== Basic Usage Demonstration ===")
    
    # Get repository path
    repo_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Using repository path: {repo_path}")
    
    # Create Serena LSP bridge
    print("\n1. Creating Serena LSP Bridge...")
    bridge = create_serena_bridge(repo_path, enable_runtime_collection=True)
    
    # Check initialization status
    print(f"   Bridge initialized: {bridge.is_initialized}")
    print(f"   Runtime collection active: {bridge.runtime_collector.is_active if bridge.runtime_collector else False}")
    
    # Add some static errors for demonstration
    print("\n2. Adding static analysis errors...")
    static_error = create_error_info(
        file_path="example.py",
        line=10,
        character=5,
        message="Undefined variable 'undefined_var'",
        severity=DiagnosticSeverity.ERROR,
        error_type=ErrorType.STATIC_ANALYSIS
    )
    static_error.fix_suggestions = ["Define the variable before use", "Check for typos in variable name"]
    bridge.add_static_error(static_error)
    
    warning = create_error_info(
        file_path="example.py",
        line=15,
        character=0,
        message="Unused import 'unused_module'",
        severity=DiagnosticSeverity.WARNING,
        error_type=ErrorType.LINTING
    )
    warning.fix_suggestions = ["Remove unused import", "Use the imported module"]
    bridge.add_static_error(warning)
    
    print(f"   Added {len(bridge.get_static_errors())} static errors")
    
    # Get error summary
    print("\n3. Error Summary:")
    summary = bridge.get_error_summary()
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    return bridge


def demonstrate_runtime_error_collection(bridge: SerenaLSPBridge):
    """Demonstrate runtime error collection."""
    print("\n=== Runtime Error Collection Demonstration ===")
    
    if not bridge.runtime_collector:
        print("Runtime collection not available")
        return
    
    print("1. Triggering runtime errors for demonstration...")
    
    # Create some runtime errors
    def trigger_name_error():
        """Function that will trigger a NameError."""
        return undefined_variable  # This will cause a NameError
    
    def trigger_type_error():
        """Function that will trigger a TypeError."""
        return "string" + 42  # This will cause a TypeError
    
    def trigger_index_error():
        """Function that will trigger an IndexError."""
        empty_list = []
        return empty_list[0]  # This will cause an IndexError
    
    # Trigger errors and catch them (they'll be collected by the runtime collector)
    errors_to_trigger = [
        ("NameError", trigger_name_error),
        ("TypeError", trigger_type_error),
        ("IndexError", trigger_index_error)
    ]
    
    for error_name, error_func in errors_to_trigger:
        try:
            print(f"   Triggering {error_name}...")
            error_func()
        except Exception as e:
            print(f"   Caught {error_name}: {e}")
            time.sleep(0.1)  # Give collector time to process
    
    # Wait a moment for collection to complete
    time.sleep(0.5)
    
    # Show collected runtime errors
    runtime_errors = bridge.get_runtime_errors()
    print(f"\n2. Collected {len(runtime_errors)} runtime errors:")
    
    for i, error in enumerate(runtime_errors, 1):
        print(f"\n   Error {i}:")
        print(f"     File: {error.file_path}")
        print(f"     Line: {error.line}")
        print(f"     Message: {error.message}")
        print(f"     Severity: {error.severity.name}")
        print(f"     Type: {error.error_type.name}")
        
        if error.runtime_context:
            context = error.runtime_context
            print(f"     Exception Type: {context.exception_type}")
            print(f"     Stack Frames: {len(context.stack_trace)}")
            print(f"     Local Variables: {len(context.local_variables)}")
            print(f"     Execution Path: {' -> '.join(context.execution_path[-3:])}")  # Last 3 steps
        
        if error.fix_suggestions:
            print(f"     Fix Suggestions:")
            for suggestion in error.fix_suggestions:
                print(f"       - {suggestion}")


def demonstrate_protocol_extension(bridge: SerenaLSPBridge):
    """Demonstrate protocol extension functionality."""
    print("\n=== Protocol Extension Demonstration ===")
    
    # Create protocol extension
    print("1. Creating protocol extension...")
    extension = SerenaProtocolExtension(bridge.repo_path, enable_runtime_collection=True)
    
    # Add notification callback
    notifications_received = []
    
    def notification_callback(notification: Dict[str, Any]):
        notifications_received.append(notification)
        print(f"   Received notification: {notification['method']}")
    
    extension.add_notification_callback(notification_callback)
    
    # Test various protocol methods
    print("\n2. Testing protocol methods...")
    
    methods_to_test = [
        ('serena/getAllErrors', {}),
        ('serena/getErrorSummary', {}),
        ('serena/getPerformanceStats', {}),
        ('serena/getFileErrors', {'filePath': 'example.py'}),
    ]
    
    for method, params in methods_to_test:
        print(f"   Testing {method}...")
        response = extension.handle_request(method, params)
        
        if response['error']:
            print(f"     Error: {response['error']['message']}")
        else:
            result = response['result']
            if isinstance(result, dict):
                # Show key information from the result
                if 'count' in result:
                    print(f"     Count: {result['count']}")
                if 'total_errors' in result:
                    print(f"     Total Errors: {result['total_errors']}")
                if 'errors' in result:
                    print(f"     Errors: {len(result['errors'])}")
            else:
                print(f"     Result type: {type(result)}")
    
    # Test configuration
    print("\n3. Testing configuration...")
    config_response = extension.handle_request('serena/configureCollection', {
        'maxErrors': 500,
        'collectVariables': True,
        'variableMaxLength': 100
    })
    
    if config_response['error']:
        print(f"   Configuration error: {config_response['error']['message']}")
    else:
        print(f"   Configuration successful: {config_response['result']['success']}")
    
    # Show notifications received
    print(f"\n4. Notifications received: {len(notifications_received)}")
    for notification in notifications_received:
        print(f"   - {notification['method']}")
    
    extension.shutdown()


def demonstrate_error_analysis():
    """Demonstrate advanced error analysis features."""
    print("\n=== Advanced Error Analysis Demonstration ===")
    
    # Create a bridge for analysis
    repo_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    bridge = create_serena_bridge(repo_path, enable_runtime_collection=True)
    
    # Create errors with different characteristics
    print("1. Creating errors with various characteristics...")
    
    errors = [
        create_error_info(
            file_path="module1.py",
            line=25,
            character=10,
            message="ImportError: No module named 'missing_module'",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR
        ),
        create_error_info(
            file_path="module2.py",
            line=50,
            character=5,
            message="AttributeError: 'NoneType' object has no attribute 'method'",
            severity=DiagnosticSeverity.ERROR,
            error_type=ErrorType.RUNTIME_ERROR
        ),
        create_error_info(
            file_path="module3.py",
            line=100,
            character=15,
            message="Line too long (120 > 88 characters)",
            severity=DiagnosticSeverity.WARNING,
            error_type=ErrorType.LINTING
        ),
    ]
    
    for error in errors:
        bridge.add_static_error(error)
    
    # Analyze errors
    print("\n2. Error Analysis:")
    all_errors = bridge.get_all_errors()
    
    # Group by severity
    by_severity = {}
    for error in all_errors:
        severity = error.severity.name
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(error)
    
    print("   By Severity:")
    for severity, error_list in by_severity.items():
        print(f"     {severity}: {len(error_list)} errors")
    
    # Group by type
    by_type = {}
    for error in all_errors:
        error_type = error.error_type.name
        if error_type not in by_type:
            by_type[error_type] = []
        by_type[error_type].append(error)
    
    print("   By Type:")
    for error_type, error_list in by_type.items():
        print(f"     {error_type}: {len(error_list)} errors")
    
    # Show errors with suggestions
    errors_with_suggestions = [e for e in all_errors if e.has_fix_suggestions]
    print(f"   Errors with fix suggestions: {len(errors_with_suggestions)}")
    
    # Show errors with runtime context
    errors_with_context = [e for e in all_errors if e.has_runtime_context]
    print(f"   Errors with runtime context: {len(errors_with_context)}")
    
    bridge.shutdown()


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("\n=== Performance Monitoring Demonstration ===")
    
    repo_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    bridge = create_serena_bridge(repo_path, enable_runtime_collection=True)
    
    # Get initial stats
    print("1. Initial performance stats:")
    initial_stats = bridge.get_performance_stats()
    for key, value in initial_stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Perform some operations
    print("\n2. Performing operations...")
    
    # Add multiple errors
    for i in range(10):
        error = create_error_info(
            file_path=f"test_file_{i}.py",
            line=i * 10,
            character=0,
            message=f"Test error {i}",
            severity=DiagnosticSeverity.WARNING,
            error_type=ErrorType.LINTING
        )
        bridge.add_static_error(error)
    
    # Trigger some runtime errors
    if bridge.runtime_collector:
        for i in range(5):
            try:
                # This will trigger a NameError
                eval(f"undefined_var_{i}")
            except:
                pass
        
        time.sleep(0.2)  # Allow collection to complete
    
    # Get updated stats
    print("\n3. Updated performance stats:")
    updated_stats = bridge.get_performance_stats()
    for key, value in updated_stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Show collection efficiency
    if bridge.runtime_collector:
        collection_stats = bridge.runtime_collector.get_collection_stats()
        print("\n4. Runtime collection efficiency:")
        for key, value in collection_stats.items():
            print(f"   {key}: {value}")
    
    bridge.shutdown()


async def demonstrate_async_usage():
    """Demonstrate asynchronous usage patterns."""
    print("\n=== Asynchronous Usage Demonstration ===")
    
    repo_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    bridge = create_serena_bridge(repo_path, enable_runtime_collection=True)
    
    # Create an async error handler
    async def async_error_handler(error: ErrorInfo):
        print(f"   Async handler received: {error.message}")
        # Simulate async processing
        await asyncio.sleep(0.01)
    
    # Add the handler (note: this is a simplified example)
    # In a real implementation, you'd need proper async handling
    bridge.add_error_handler(lambda error: asyncio.create_task(async_error_handler(error)))
    
    print("1. Adding errors with async handling...")
    
    # Add errors
    for i in range(3):
        error = create_error_info(
            file_path=f"async_test_{i}.py",
            line=i,
            character=0,
            message=f"Async test error {i}",
            severity=DiagnosticSeverity.INFO,
            error_type=ErrorType.STATIC_ANALYSIS
        )
        bridge.add_static_error(error)
        await asyncio.sleep(0.1)  # Simulate async processing time
    
    print("2. Async processing completed")
    
    bridge.shutdown()


def main():
    """Main demonstration function."""
    print("Graph-Sitter LSP Extension - Comprehensive Example")
    print("=" * 60)
    
    try:
        # Basic usage
        bridge = demonstrate_basic_usage()
        
        # Runtime error collection
        demonstrate_runtime_error_collection(bridge)
        
        # Protocol extension
        demonstrate_protocol_extension(bridge)
        
        # Advanced error analysis
        demonstrate_error_analysis()
        
        # Performance monitoring
        demonstrate_performance_monitoring()
        
        # Async usage
        asyncio.run(demonstrate_async_usage())
        
        # Cleanup
        bridge.shutdown()
        
        print("\n" + "=" * 60)
        print("Demonstration completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✓ Runtime error collection with full context")
        print("✓ Static error management and analysis")
        print("✓ Serena LSP integration with graceful fallback")
        print("✓ Protocol extensions for LSP communication")
        print("✓ Intelligent fix suggestion generation")
        print("✓ Performance monitoring and statistics")
        print("✓ Asynchronous processing support")
        print("✓ Comprehensive error analysis and reporting")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
