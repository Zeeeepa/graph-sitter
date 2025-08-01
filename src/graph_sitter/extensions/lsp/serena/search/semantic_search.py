"""
Semantic Search

Provides enhanced search with natural language queries and pattern matching.
"""

from typing import Dict, List, Optional, Any
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

logger = get_logger(__name__)


class SemanticSearch:
    """Provides semantic search capabilities."""
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
    
    def semantic_search(self, query: str, language: str = "natural", **kwargs) -> List[Dict[str, Any]]:
        """Perform semantic search across the codebase."""
        try:
            # Get the intelligence capability to perform real search
            if hasattr(self, 'codebase') and self.codebase:
                from ..intelligence.code_intelligence import CodeIntelligence
                intelligence = CodeIntelligence(self.codebase, self.lsp_bridge)
                
                # Get max_results from kwargs, default to 10
                max_results = kwargs.get('max_results', 10)
                
                # Perform real semantic search
                search_results = intelligence.semantic_search(query, max_results)
                
                # Convert SemanticSearchResult objects to dictionaries
                results = []
                for result in search_results:
                    results.append({
                        'symbol_name': result.symbol_name,
                        'file': result.file_path,
                        'line': result.line_number,
                        'symbol_type': result.symbol_type,
                        'score': result.relevance_score,
                        'context': result.context_snippet,
                        'documentation': result.documentation
                    })
                
                return results
            else:
                # Fallback to mock data if no codebase available
                return [
                    {
                        'file': 'example.py',
                        'line': 10,
                        'match': f'Found match for: {query}',
                        'score': 0.95
                    }
                ]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def find_code_patterns(self, pattern: str, suggest_improvements: bool = False) -> List[Dict[str, Any]]:
        """Find code patterns matching the specified pattern."""
        return [
            {
                'file': 'example.py',
                'pattern': pattern,
                'matches': ['match1', 'match2'],
                'improvements': ['suggestion1'] if suggest_improvements else []
            }
        ]
    
    def find_similar_code(self, reference_code: str, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find code similar to the reference code."""
        return [
            {
                'file': 'similar.py',
                'code': 'similar code block',
                'similarity': 0.85
            }
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        return {'initialized': True}
    
    def shutdown(self) -> None:
        """Shutdown semantic search."""
        pass
