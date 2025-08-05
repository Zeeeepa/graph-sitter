"""Example usage of AutoGenLib integration with Codegen SDK and Graph-sitter."""

import os
from graph_sitter.core.codebase import Codebase
from .core import init_autogenlib


def example_basic_usage():
    """Basic example of using AutoGenLib with Codegen SDK."""
    
    # Initialize with Codegen SDK credentials
    integration = init_autogenlib(
        description="Utility library for data processing and analysis",
        codegen_org_id=os.environ.get("CODEGEN_ORG_ID"),
        codegen_token=os.environ.get("CODEGEN_TOKEN"),
        enable_caching=True
    )
    
    # Now you can import modules that don't exist yet
    from autogenlib.data_processing import clean_data, validate_input
    from autogenlib.analysis import calculate_statistics, generate_report
    
    # Use the generated functions
    sample_data = [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 82}]
    cleaned = clean_data(sample_data)
    stats = calculate_statistics(cleaned)
    report = generate_report(stats)
    
    print(f"Generated report: {report}")


def example_with_codebase_context():
    """Example using graph-sitter codebase context for better generation."""
    
    # Load a codebase for context
    codebase = Codebase.from_repo("fastapi/fastapi")
    
    # Initialize with codebase context
    integration = init_autogenlib(
        description="FastAPI utility extensions",
        codebase=codebase,
        codegen_org_id=os.environ.get("CODEGEN_ORG_ID"),
        codegen_token=os.environ.get("CODEGEN_TOKEN"),
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),  # Fallback
        enable_caching=True
    )
    
    # Import FastAPI-related utilities that will be generated with context
    from autogenlib.fastapi_utils import create_router, add_middleware
    from autogenlib.validation import validate_request, sanitize_input
    
    # The generated code will be informed by the FastAPI codebase patterns
    router = create_router("/api/v1")
    middleware = add_middleware(router, "cors")
    
    print(f"Generated router: {router}")


def example_with_existing_code():
    """Example of extending existing modules with new functionality."""
    
    integration = init_autogenlib(
        description="Mathematical utilities library",
        codegen_org_id=os.environ.get("CODEGEN_ORG_ID"),
        codegen_token=os.environ.get("CODEGEN_TOKEN")
    )
    
    # First import creates the base module
    from autogenlib.math_utils import basic_operations
    
    # Later imports extend the module with new functions
    from autogenlib.math_utils import advanced_operations, statistical_functions
    
    # All functions are available in the same module
    result1 = basic_operations([1, 2, 3, 4, 5])
    result2 = advanced_operations(result1)
    stats = statistical_functions(result2)
    
    print(f"Mathematical analysis result: {stats}")


def example_error_handling():
    """Example demonstrating error handling and fallback providers."""
    
    # Initialize with multiple providers for redundancy
    integration = init_autogenlib(
        description="Robust utility library with error handling",
        codegen_org_id="invalid_org_id",  # This will fail
        codegen_token="invalid_token",
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),  # Fallback
        enable_caching=False
    )
    
    try:
        # This will use Claude as fallback when Codegen SDK fails
        from autogenlib.error_handling import safe_execute, retry_operation
        
        result = safe_execute(lambda: 1 / 0)  # This should handle the error
        print(f"Safe execution result: {result}")
        
    except ImportError as e:
        print(f"Failed to generate module: {e}")


def example_integration_with_contexten():
    """Example of integrating with the broader contexten ecosystem."""
    
    from graph_sitter.core.codebase import Codebase
    from codegen.extensions.events.codegen_app import CodegenApp
    
    # Create a CodegenApp instance
    app = CodegenApp("AutoGenLib Demo", repo="fastapi/fastapi")
    app.parse_repo()
    
    # Get the codebase from the app
    codebase = app.get_codebase()
    
    # Initialize AutoGenLib with the codebase context
    integration = init_autogenlib(
        description="Context-aware utility library",
        codebase=codebase,
        codegen_org_id=os.environ.get("CODEGEN_ORG_ID"),
        codegen_token=os.environ.get("CODEGEN_TOKEN"),
        enable_caching=True
    )
    
    # Generate code that's informed by the FastAPI codebase
    from autogenlib.web_utils import create_endpoint, handle_request
    from autogenlib.middleware import auth_middleware, logging_middleware
    
    # The generated code will follow FastAPI patterns
    endpoint = create_endpoint("/users", methods=["GET", "POST"])
    auth = auth_middleware(endpoint)
    
    print(f"Generated web utilities with FastAPI context")


if __name__ == "__main__":
    # Run examples (uncomment as needed)
    
    print("=== Basic Usage Example ===")
    try:
        example_basic_usage()
    except Exception as e:
        print(f"Basic usage failed: {e}")
    
    print("\n=== Codebase Context Example ===")
    try:
        example_with_codebase_context()
    except Exception as e:
        print(f"Codebase context example failed: {e}")
    
    print("\n=== Existing Code Extension Example ===")
    try:
        example_with_existing_code()
    except Exception as e:
        print(f"Existing code extension failed: {e}")
    
    print("\n=== Error Handling Example ===")
    try:
        example_error_handling()
    except Exception as e:
        print(f"Error handling example failed: {e}")
    
    print("\n=== Contexten Integration Example ===")
    try:
        example_integration_with_contexten()
    except Exception as e:
        print(f"Contexten integration failed: {e}")

