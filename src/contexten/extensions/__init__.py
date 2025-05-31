"""Contexten extensions package."""

# Import autogenlib integration for easy access
try:
    from .autogenlib import (
        AutoGenLibIntegration,
        init_autogenlib,
        CodeGenerator,
        CodegenSDKProvider,
        ClaudeProvider,
        GraphSitterContextProvider
    )
    from .autogenlib.integration import (
        ContextenAutoGenLibIntegration,
        init_contexten_autogenlib,
        setup_autogenlib_for_codegen_app
    )
    
    __all__ = [
        "AutoGenLibIntegration",
        "init_autogenlib",
        "CodeGenerator", 
        "CodegenSDKProvider",
        "ClaudeProvider",
        "GraphSitterContextProvider",
        "ContextenAutoGenLibIntegration",
        "init_contexten_autogenlib",
        "setup_autogenlib_for_codegen_app"
    ]
    
except ImportError as e:
    # AutoGenLib integration not available
    __all__ = []

