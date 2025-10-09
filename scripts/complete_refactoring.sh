#!/bin/bash
# Script to complete the graph-sitter refactoring
# This script guides through steps 4-30 of the refactoring plan

set -e

echo "🚀 Graph-Sitter Refactoring Completion Script"
echo "=============================================="
echo ""
echo "This script will guide you through completing the refactoring."
echo "Please review docs/IMPLEMENTATION_GUIDE.md before proceeding."
echo ""

# Check if we're in the right directory
if [ ! -f "src/analysis_utils.py" ] || [ ! -f "src/protocols.py" ]; then
    echo "❌ Error: Foundation files not found."
    echo "Please run this script from the repository root."
    exit 1
fi

echo "✅ Foundation files found (analysis_utils.py, protocols.py)"
echo ""

# Step 4-7: Create graph_sitter_adapter.py
echo "📝 Step 4-7: Creating graph_sitter_adapter.py"
echo "   This will consolidate:"
echo "   - graph_sitter_analysis.py (1,675 lines)"
echo "   - graph_sitter_backend.py (3,954 lines)"
echo ""
echo "   Target: ~3,500 lines (30% reduction)"
echo ""
read -p "   Create skeleton? (y/n): " create_gs_adapter

if [ "$create_gs_adapter" = "y" ]; then
    cat > src/graph_sitter_adapter.py << 'ADAPTER_EOF'
"""Unified Graph-Sitter Adapter for code analysis.

This module consolidates graph_sitter_analysis.py and graph_sitter_backend.py
into a single, coherent adapter implementing GraphSitterAnalyzerProtocol.
"""

import logging
from typing import Any

from graph_sitter import Codebase
from protocols import GraphSitterAnalyzerProtocol
from analysis_utils import AnalysisError

logger = logging.getLogger(__name__)


class GraphSitterAdapter:
    """Unified adapter for graph-sitter based code analysis.
    
    This class consolidates functionality from:
    - GraphSitterAnalyzer (high-level analysis)
    - AnalysisEngine (backend processing)
    
    Implements GraphSitterAnalyzerProtocol for type safety.
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize adapter with codebase.
        
        Args:
            codebase: Graph-sitter Codebase instance
        """
        self.codebase = codebase
        self._graph = None  # NetworkX graph cache
        self._file_cache = {}
        self._symbol_cache = {}
        logger.info(f"Initialized GraphSitterAdapter for: {codebase.path}")
    
    # Protocol Implementation - Core Analysis Methods
    
    def get_codebase_overview(self) -> dict[str, Any]:
        """Get comprehensive overview of codebase structure.
        
        Returns:
            Dictionary containing:
                - total_files: int
                - total_lines: int
                - total_functions: int
                - total_classes: int
                - languages: list[str]
                - entry_points: list[dict]
        """
        # TODO: Implement from graph_sitter_analysis.py
        raise NotImplementedError("Migrate from GraphSitterAnalyzer")
    
    def get_file_details(self, file_path: str) -> dict[str, Any]:
        """Get detailed analysis of specific file.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            Dictionary with file metrics, symbols, dependencies
        """
        # TODO: Implement with caching
        raise NotImplementedError("Migrate from GraphSitterAnalyzer")
    
    def get_function_details(self, function_name: str, file_path: str) -> dict[str, Any]:
        """Get detailed analysis of specific function."""
        # TODO: Implement
        raise NotImplementedError("Migrate from GraphSitterAnalyzer")
    
    def get_class_details(self, class_name: str, file_path: str) -> dict[str, Any]:
        """Get detailed analysis of specific class."""
        # TODO: Implement
        raise NotImplementedError("Migrate from GraphSitterAnalyzer")
    
    def get_symbol_details(self, symbol_name: str) -> dict[str, Any]:
        """Get detailed analysis of symbol (function/class/variable)."""
        # TODO: Implement
        raise NotImplementedError("Migrate from GraphSitterAnalyzer")
    
    # Visualization Methods
    
    def create_blast_radius_visualization(self, symbol_name: str) -> dict[str, Any]:
        """Create visualization showing impact of changing a symbol."""
        # TODO: Migrate from graph_sitter_analysis.py
        raise NotImplementedError("Migrate visualization logic")
    
    def create_call_trace_visualization(self, function_name: str) -> dict[str, Any]:
        """Create visualization showing function call relationships."""
        # TODO: Migrate
        raise NotImplementedError("Migrate visualization logic")
    
    def create_dependency_trace_visualization(self, module_name: str) -> dict[str, Any]:
        """Create visualization showing module dependencies."""
        # TODO: Migrate
        raise NotImplementedError("Migrate visualization logic")
    
    def find_dead_code(self) -> list[dict[str, Any]]:
        """Identify unused code that can be removed."""
        # TODO: Migrate from graph_sitter_analysis.py
        raise NotImplementedError("Migrate dead code detection")
    
    # Private helper methods (from backend)
    
    def _build_dependency_graph(self):
        """Build NetworkX graph of code dependencies."""
        # TODO: Migrate from graph_sitter_backend.py AnalysisEngine
        pass
    
    def _analyze_complexity(self, node):
        """Calculate complexity metrics."""
        # TODO: Migrate complexity calculation
        pass


# For backward compatibility
GraphSitterAnalyzer = GraphSitterAdapter  # Alias

ADAPTER_EOF
    echo "✅ Created src/graph_sitter_adapter.py skeleton"
else
    echo "⏭️  Skipped graph_sitter_adapter.py"
fi

# Step 8-11: Create autogenlib_adapter.py
echo ""
echo "📝 Step 8-11: Creating autogenlib_adapter.py"
read -p "   Create skeleton? (y/n): " create_ai_adapter

if [ "$create_ai_adapter" = "y" ]; then
    cat > src/autogenlib_adapter.py << 'AI_ADAPTER_EOF'
"""Unified AutoGenLib Adapter for AI-powered error resolution.

This module consolidates autogenlib_context.py and autogenlib_ai_resolve.py
into a single adapter for AI-assisted code fixing.
"""

import logging
from typing import Any

from graph_sitter import Codebase
from protocols import AutoGenLibResolverProtocol
from analysis_utils import AnalysisError

logger = logging.getLogger(__name__)


class AutoGenLibAdapter:
    """Unified adapter for AI-powered error resolution.
    
    Consolidates:
    - Context generation (from autogenlib_context.py)
    - AI resolution (from autogenlib_ai_resolve.py)
    
    Implements AutoGenLibResolverProtocol.
    """
    
    def __init__(
        self,
        codebase: Codebase,
        graph_sitter_adapter=None,
        lsp_manager=None,
        ai_config: dict | None = None
    ):
        """Initialize AI resolution adapter.
        
        Args:
            codebase: Graph-sitter Codebase instance
            graph_sitter_adapter: GraphSitterAdapter for code analysis
            lsp_manager: LSPDiagnosticsManager for diagnostics
            ai_config: AI configuration (provider, model, etc.)
        """
        self.codebase = codebase
        self.gs_adapter = graph_sitter_adapter
        self.lsp_manager = lsp_manager
        self.ai_config = ai_config or {}
        self._client = None
        logger.info("Initialized AutoGenLibAdapter")
    
    # Protocol Implementation
    
    def resolve_error(
        self,
        error: AnalysisError,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Resolve single error using AI assistance.
        
        Args:
            error: AnalysisError to resolve
            context: Additional context
            
        Returns:
            Dictionary with fix_code, explanation, confidence
        """
        # TODO: Implement from autogenlib_ai_resolve.py
        raise NotImplementedError("Migrate from resolve_diagnostic_with_ai")
    
    def resolve_multiple_errors(
        self,
        errors: list[AnalysisError],
        max_fixes: int = 10
    ) -> list[dict[str, Any]]:
        """Resolve multiple errors in batch."""
        # TODO: Implement
        raise NotImplementedError("Migrate from resolve_multiple_errors_with_ai")
    
    def get_error_context(
        self,
        error: AnalysisError,
        include_related_symbols: bool = True
    ) -> dict[str, Any]:
        """Get comprehensive context for error."""
        # TODO: Implement from autogenlib_context.py
        raise NotImplementedError("Migrate from get_ai_fix_context")
    
    def generate_fix_strategy(
        self,
        errors: list[AnalysisError]
    ) -> dict[str, Any]:
        """Generate comprehensive fix strategy."""
        # TODO: Implement
        raise NotImplementedError("Migrate from generate_comprehensive_fix_strategy")
    
    # Private helper methods
    
    def _get_llm_codebase_overview(self) -> str:
        """Get LLM-friendly codebase overview."""
        # TODO: Migrate from autogenlib_context.py
        pass
    
    def _construct_fix_prompt(self, error, context) -> str:
        """Construct AI prompt for fix generation."""
        # TODO: Implement prompt engineering
        pass


AI_ADAPTER_EOF
    echo "✅ Created src/autogenlib_adapter.py skeleton"
else
    echo "⏭️  Skipped autogenlib_adapter.py"
fi

# Summary
echo ""
echo "=============================================="
echo "📊 Refactoring Progress Summary"
echo "=============================================="
echo ""
echo "✅ Completed (Steps 1-3):"
echo "   - Architecture analysis"
echo "   - analysis_utils.py (159 lines)"
echo "   - protocols.py (229 lines)"
echo ""
echo "🔄 Created Skeletons (Steps 4-11):"
if [ "$create_gs_adapter" = "y" ]; then
    echo "   - graph_sitter_adapter.py (skeleton)"
fi
if [ "$create_ai_adapter" = "y" ]; then
    echo "   - autogenlib_adapter.py (skeleton)"
fi
echo ""
echo "⏳ Remaining:"
echo "   - Implement adapter methods (migrate code from old files)"
echo "   - Create lib_analysis.py (tool integrations)"
echo "   - Create main_analysis.py (CLI)"
echo "   - Add tests"
echo "   - Write documentation"
echo ""
echo "📚 Next Steps:"
echo "   1. Review docs/IMPLEMENTATION_GUIDE.md"
echo "   2. Implement methods marked with TODO"
echo "   3. Run tests to validate"
echo "   4. Update documentation"
echo ""
echo "✨ See docs/REFACTORING_PROGRESS.md for detailed tracking"
echo ""
AI_ADAPTER_EOF

chmod +x scripts/complete_refactoring.sh
echo "✅ Created executable completion script"

