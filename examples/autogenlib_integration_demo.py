#!/usr/bin/env python3
"""
Comprehensive demo of AutoGenLib integration with Codegen SDK and Graph-sitter.

This example demonstrates:
1. Basic AutoGenLib usage with Codegen SDK
2. Enhanced context from graph-sitter codebase analysis
3. Integration with the contexten ecosystem
4. Multiple AI provider fallback
5. Caching and performance optimization
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter.core.codebase import Codebase
from codegen.extensions.autogenlib import init_autogenlib
from codegen.extensions.autogenlib.config import AutoGenLibConfig
from codegen.extensions.autogenlib.integration import (
    init_contexten_autogenlib,
    setup_autogenlib_for_codegen_app
)
from contexten.extensions.events.codegen_app import CodegenApp


def demo_basic_usage():
    """Demonstrate basic AutoGenLib usage."""
    print("=== Basic AutoGenLib Usage ===")
    
    # Initialize with environment variables
    integration = init_autogenlib(
        description="Data processing and analysis utilities",
        enable_caching=True
    )
    
    print(f"Initialized AutoGenLib with {len(integration.generator.providers)} providers")
    
    # Example 1: Data processing utilities
    print("\n1. Generating data processing utilities...")
    try:
        from autogenlib.data_processing import clean_csv_data, validate_json_schema
        
        # Test the generated functions
        sample_csv_data = "name,age,city\nAlice,25,NYC\nBob,,LA\nCharlie,30,"
        cleaned_data = clean_csv_data(sample_csv_data)
        print(f"Cleaned CSV data: {cleaned_data}")
        
        sample_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        sample_data = {"name": "Alice", "age": 25}
        is_valid = validate_json_schema(sample_data, sample_schema)
        print(f"JSON validation result: {is_valid}")
        
    except ImportError as e:
        print(f"Failed to import data processing utilities: {e}")
    
    # Example 2: Mathematical utilities
    print("\n2. Generating mathematical utilities...")
    try:
        from autogenlib.math_utils import calculate_statistics, generate_fibonacci
        
        numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stats = calculate_statistics(numbers)
        print(f"Statistics for {numbers}: {stats}")
        
        fib_sequence = generate_fibonacci(10)
        print(f"Fibonacci sequence (10 terms): {fib_sequence}")
        
    except ImportError as e:
        print(f"Failed to import math utilities: {e}")


def demo_codebase_context():
    """Demonstrate AutoGenLib with codebase context."""
    print("\n=== AutoGenLib with Codebase Context ===")
    
    try:
        # Load a well-known repository for context
        print("Loading FastAPI codebase for context...")
        codebase = Codebase.from_repo("fastapi/fastapi")
        print(f"Loaded codebase with {len(codebase.functions)} functions")
        
        # Initialize with codebase context
        integration = init_autogenlib(
            description="FastAPI extension utilities",
            codebase=codebase,
            enable_caching=True
        )
        
        # Generate FastAPI-aware utilities
        print("\nGenerating FastAPI-aware utilities...")
        from autogenlib.fastapi_extensions import create_crud_router, add_auth_middleware
        
        # The generated code should be informed by FastAPI patterns
        router = create_crud_router("/api/users", model_name="User")
        print(f"Generated CRUD router: {type(router)}")
        
        middleware = add_auth_middleware(router, auth_type="bearer")
        print(f"Added auth middleware: {type(middleware)}")
        
    except Exception as e:
        print(f"Codebase context demo failed: {e}")


def demo_contexten_integration():
    """Demonstrate integration with the contexten ecosystem."""
    print("\n=== Contexten Ecosystem Integration ===")
    
    try:
        # Create a CodegenApp instance
        app = CodegenApp("AutoGenLib Demo", repo="fastapi/fastapi")
        print("Created CodegenApp instance")
        
        # Parse the repository
        app.parse_repo()
        print("Parsed repository")
        
        # Set up AutoGenLib integration
        success = setup_autogenlib_for_codegen_app(app)
        print(f"AutoGenLib setup: {'Success' if success else 'Failed'}")
        
        if success:
            # Get integration status
            status = app.get_autogenlib_status()
            print(f"Integration status: {status}")
            
            # Generate code with full context
            from autogenlib.web_framework import create_api_endpoint, handle_websocket
            
            endpoint = create_api_endpoint("/api/data", methods=["GET", "POST"])
            print(f"Generated API endpoint: {type(endpoint)}")
            
            websocket_handler = handle_websocket("/ws/updates")
            print(f"Generated WebSocket handler: {type(websocket_handler)}")
        
    except Exception as e:
        print(f"Contexten integration demo failed: {e}")


def demo_provider_fallback():
    """Demonstrate multiple provider fallback."""
    print("\n=== Provider Fallback Demo ===")
    
    # Create configuration with multiple providers
    config = AutoGenLibConfig(
        description="Multi-provider test library",
        codegen_org_id=os.environ.get("CODEGEN_ORG_ID", "invalid"),
        codegen_token=os.environ.get("CODEGEN_TOKEN", "invalid"),
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        provider_order=["codegen", "claude", "openai"],
        enable_caching=False  # Disable caching to test fallback
    )
    
    print(f"Available providers: {config.get_available_providers()}")
    
    # Initialize integration
    integration = init_contexten_autogenlib(config=config)
    status = integration.get_status()
    
    print(f"Integration available: {integration.is_available()}")
    print(f"Configured providers: {status.get('available_providers', [])}")
    
    if integration.is_available():
        try:
            # Test generation with fallback
            from autogenlib.fallback_test import robust_function, error_handler
            
            result = robust_function("test input")
            print(f"Robust function result: {result}")
            
            error_result = error_handler(Exception("test error"))
            print(f"Error handler result: {error_result}")
            
        except ImportError as e:
            print(f"Fallback test failed: {e}")


def demo_advanced_features():
    """Demonstrate advanced features."""
    print("\n=== Advanced Features Demo ===")
    
    # Custom configuration
    config = AutoGenLibConfig(
        description="Advanced utility library with custom settings",
        enable_caching=True,
        max_context_functions=20,
        max_context_dependencies=25,
        generation_timeout=45,
        temperature=0.2
    )
    
    integration = init_autogenlib(
        description=config.description,
        enable_caching=config.enable_caching
    )
    
    # Cache management
    print("Testing cache management...")
    cache_info = integration.cache.get_cache_info()
    print(f"Cache info: {cache_info}")
    
    # Generate some modules to populate cache
    try:
        from autogenlib.cache_test import function_a, function_b
        
        result_a = function_a("test")
        result_b = function_b(42)
        
        print(f"Generated functions: {result_a}, {result_b}")
        
        # Check cache again
        cache_info = integration.cache.get_cache_info()
        print(f"Cache after generation: {cache_info}")
        
        # List cached modules
        cached_modules = integration.cache.list_cached()
        print(f"Cached modules: {cached_modules}")
        
    except ImportError as e:
        print(f"Cache test failed: {e}")


async def demo_async_integration():
    """Demonstrate async integration patterns."""
    print("\n=== Async Integration Demo ===")
    
    integration = init_autogenlib(
        description="Async utility library",
        enable_caching=True
    )
    
    # Simulate async code generation
    async def generate_async_module(module_name):
        """Generate a module asynchronously."""
        loop = asyncio.get_event_loop()
        
        # Run generation in thread pool to avoid blocking
        code = await loop.run_in_executor(
            None,
            integration.generate_module,
            module_name
        )
        return code
    
    try:
        # Generate multiple modules concurrently
        tasks = [
            generate_async_module("autogenlib.async_utils.task_manager"),
            generate_async_module("autogenlib.async_utils.queue_handler"),
            generate_async_module("autogenlib.async_utils.event_processor")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i} failed: {result}")
            else:
                print(f"Task {i} generated {len(result) if result else 0} characters of code")
        
        # Now import and use the generated modules
        from autogenlib.async_utils import task_manager, queue_handler, event_processor
        
        # Test the async utilities
        manager = task_manager.create_manager()
        queue = queue_handler.create_queue(maxsize=100)
        processor = event_processor.create_processor()
        
        print(f"Created async utilities: {type(manager)}, {type(queue)}, {type(processor)}")
        
    except Exception as e:
        print(f"Async demo failed: {e}")


def main():
    """Run all demos."""
    print("AutoGenLib Integration Comprehensive Demo")
    print("=" * 50)
    
    # Check environment
    print("Environment check:")
    print(f"CODEGEN_ORG_ID: {'Set' if os.environ.get('CODEGEN_ORG_ID') else 'Not set'}")
    print(f"CODEGEN_TOKEN: {'Set' if os.environ.get('CODEGEN_TOKEN') else 'Not set'}")
    print(f"CLAUDE_API_KEY: {'Set' if os.environ.get('CLAUDE_API_KEY') else 'Not set'}")
    print(f"OPENAI_API_KEY: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not set'}")
    print()
    
    # Run demos
    try:
        demo_basic_usage()
    except Exception as e:
        print(f"Basic usage demo failed: {e}")
    
    try:
        demo_codebase_context()
    except Exception as e:
        print(f"Codebase context demo failed: {e}")
    
    try:
        demo_contexten_integration()
    except Exception as e:
        print(f"Contexten integration demo failed: {e}")
    
    try:
        demo_provider_fallback()
    except Exception as e:
        print(f"Provider fallback demo failed: {e}")
    
    try:
        demo_advanced_features()
    except Exception as e:
        print(f"Advanced features demo failed: {e}")
    
    # Run async demo
    try:
        asyncio.run(demo_async_integration())
    except Exception as e:
        print(f"Async integration demo failed: {e}")
    
    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    main()
