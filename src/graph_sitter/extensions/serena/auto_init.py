"""
Auto-initialization for Serena Integration

This module automatically integrates Serena capabilities into the Codebase class
when imported. It should be imported after the Codebase class is defined.
"""

from graph_sitter.shared.logging.get_logger import get_logger
from .integration import add_serena_to_codebase

logger = get_logger(__name__)

def initialize_serena_integration():
    """Initialize Serena integration with the Codebase class."""
    try:
        # Import Codebase class
        from graph_sitter.core.codebase import Codebase
        
        # Add Serena methods to Codebase
        add_serena_to_codebase(Codebase)
        
        logger.info("✅ Serena LSP integration successfully added to Codebase class")
        logger.info("🚀 Available methods: get_completions, get_hover_info, rename_symbol, extract_method, semantic_search, and more!")
        
        return True
        
    except ImportError as e:
        logger.warning(f"Could not import Codebase class for Serena integration: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Serena integration: {e}")
        return False

# Auto-initialize when this module is imported
_initialized = initialize_serena_integration()

