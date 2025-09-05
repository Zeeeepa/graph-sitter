"""
Completion Provider

Provides context-aware code completions using LSP and semantic analysis.
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import threading

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from ..mcp_bridge import SerenaMCPBridge
from graph_sitter.core.symbol import Symbol

logger = get_logger(__name__)


@dataclass
class CompletionItem:
    """Represents a code completion item."""
    label: str
    kind: str
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None
    score: float = 0.0
    source: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'label': self.label,
            'kind': self.kind,
            'detail': self.detail,
            'documentation': self.documentation,
            'insertText': self.insert_text or self.label,
            'sortText': self.sort_text,
            'filterText': self.filter_text,
            'score': self.score,
            'source': self.source
        }


class CompletionProvider:
    """
    Provides intelligent code completions.
    
    Combines LSP completions with semantic analysis and AI-powered suggestions.
    """
    
    def __init__(self, codebase: Codebase, mcp_bridge: SerenaMCPBridge, config):
        self.codebase = codebase
        self.mcp_bridge = mcp_bridge
        self.config = config
        
        # Completion cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._cache_max_age = 30.0  # seconds
        
        # Symbol index for fast lookups
        self._symbol_index: Dict[str, List[Symbol]] = defaultdict(list)
        self._build_symbol_index()
        
        logger.debug("Completion provider initialized")
    
    def get_completions(self, file_path: str, line: int, character: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get code completions at the specified position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
            **kwargs: Additional options (trigger_character, context, etc.)
        
        Returns:
            List of completion items
        """
        # Check cache first
        cache_key = f"{file_path}:{line}:{character}"
        cached_result = self._get_cached_completions(cache_key)
        if cached_result:
            return cached_result
        
        # Get context information
        context = self._get_completion_context(file_path, line, character)
        
        # Collect completions from multiple sources
        completions = []
        
        # 1. LSP completions (if available)
        lsp_completions = self._get_lsp_completions(file_path, line, character, context)
        completions.extend(lsp_completions)
        
        # 2. Symbol-based completions
        symbol_completions = self._get_symbol_completions(file_path, line, character, context)
        completions.extend(symbol_completions)
        
        # 3. Keyword completions
        keyword_completions = self._get_keyword_completions(file_path, context)
        completions.extend(keyword_completions)
        
        # 4. Snippet completions
        snippet_completions = self._get_snippet_completions(file_path, context)
        completions.extend(snippet_completions)
        
        # 5. AI-powered completions (if enabled)
        if self.config.enable_ai_completions:
            ai_completions = self._get_ai_completions(file_path, line, character, context)
            completions.extend(ai_completions)
        
        # Deduplicate and rank completions
        final_completions = self._process_completions(completions, context)
        
        # Cache result
        self._cache_completions(cache_key, final_completions)
        
        return [comp.to_dict() for comp in final_completions[:self.config.max_completions]]
    
    def _get_completion_context(self, file_path: str, line: int, character: int) -> Dict[str, Any]:
        """Get context information for completions."""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return {}
            
            # Get file content
            content = file_obj.content
            lines = content.split('\n')
            
            if line >= len(lines):
                return {}
            
            current_line = lines[line]
            prefix = current_line[:character]
            suffix = current_line[character:]
            
            # Analyze context
            context = {
                'file_path': file_path,
                'line': line,
                'character': character,
                'current_line': current_line,
                'prefix': prefix,
                'suffix': suffix,
                'language': self._detect_language(file_path),
                'in_string': self._is_in_string(prefix),
                'in_comment': self._is_in_comment(prefix),
                'trigger_character': prefix[-1] if prefix else None,
                'word_prefix': self._extract_word_prefix(prefix),
                'scope': self._get_scope_context(file_obj, line),
                'imports': self._get_imports_context(file_obj),
                'surrounding_lines': lines[max(0, line-2):line+3]
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting completion context: {e}")
            return {}
    
    def _get_lsp_completions(self, file_path: str, line: int, character: int, context: Dict[str, Any]) -> List[CompletionItem]:
        """Get completions from LSP servers."""
        completions: List[CompletionItem] = []
        
        try:
            # This would integrate with actual LSP servers
            # For now, return empty list as LSP integration is handled elsewhere
            pass
            
        except Exception as e:
            logger.debug(f"Error getting LSP completions: {e}")
        
        return completions
    
    def _get_symbol_completions(self, file_path: str, line: int, character: int, context: Dict[str, Any]) -> List[CompletionItem]:
        """Get completions based on symbols in the codebase."""
        completions: List[CompletionItem] = []
        word_prefix = context.get('word_prefix', '').lower()
        
        if len(word_prefix) < 2:  # Only complete for 2+ characters
            return completions
        
        try:
            # Get symbols from current file
            file_obj = self.codebase.get_file(file_path)
            if file_obj:
                for symbol in file_obj.symbols:
                    if symbol.name.lower().startswith(word_prefix):
                        completion = CompletionItem(
                            label=symbol.name,
                            kind=self._symbol_to_completion_kind(symbol),
                            detail=self._get_symbol_detail(symbol),
                            documentation=self._get_symbol_documentation(symbol),
                            score=self._calculate_symbol_score(symbol, context),
                            source="local_symbols"
                        )
                        completions.append(completion)
            
            # Get symbols from imported modules
            imports_context = context.get('imports', [])
            for import_info in imports_context:
                # Add imported symbols
                imported_symbols = self._get_imported_symbols(import_info)
                for symbol in imported_symbols:
                    if symbol.name.lower().startswith(word_prefix):
                        completion = CompletionItem(
                            label=symbol.name,
                            kind=self._symbol_to_completion_kind(symbol),
                            detail=f"from {import_info.get('module', 'unknown')}",
                            score=self._calculate_symbol_score(symbol, context) * 0.8,  # Lower score for imports
                            source="imported_symbols"
                        )
                        completions.append(completion)
            
            # Get symbols from global index
            for symbol_name, symbols in self._symbol_index.items():
                if symbol_name.lower().startswith(word_prefix):
                    for symbol in symbols[:3]:  # Limit to top 3 matches
                        completion = CompletionItem(
                            label=symbol.name,
                            kind=self._symbol_to_completion_kind(symbol),
                            detail=f"from {symbol.file.path if hasattr(symbol, 'file') else 'unknown'}",
                            score=self._calculate_symbol_score(symbol, context) * 0.6,  # Lower score for global
                            source="global_symbols"
                        )
                        completions.append(completion)
            
        except Exception as e:
            logger.error(f"Error getting symbol completions: {e}")
        
        return completions
    
    def _get_keyword_completions(self, file_path: str, context: Dict[str, Any]) -> List[CompletionItem]:
        """Get keyword completions based on language."""
        completions: List[CompletionItem] = []
        language = context.get('language', '')
        word_prefix = context.get('word_prefix', '').lower()
        
        if len(word_prefix) < 2:
            return completions
        
        try:
            keywords = self._get_language_keywords(language)
            
            for keyword in keywords:
                if keyword.lower().startswith(word_prefix):
                    completion = CompletionItem(
                        label=keyword,
                        kind="Keyword",
                        detail=f"{language} keyword",
                        score=0.5,  # Medium priority
                        source="keywords"
                    )
                    completions.append(completion)
                    
        except Exception as e:
            logger.error(f"Error getting keyword completions: {e}")
        
        return completions
    
    def _get_snippet_completions(self, file_path: str, context: Dict[str, Any]) -> List[CompletionItem]:
        """Get snippet completions."""
        completions = []
        language = context.get('language', '')
        word_prefix = context.get('word_prefix', '').lower()
        
        try:
            snippets = self._get_language_snippets(language)
            
            for snippet_name, snippet_data in snippets.items():
                if snippet_name.lower().startswith(word_prefix):
                    completion = CompletionItem(
                        label=snippet_name,
                        kind="Snippet",
                        detail=snippet_data.get('description', 'Code snippet'),
                        insert_text=snippet_data.get('body', snippet_name),
                        score=0.7,  # Higher priority for snippets
                        source="snippets"
                    )
                    completions.append(completion)
                    
        except Exception as e:
            logger.error(f"Error getting snippet completions: {e}")
        
        return completions
    
    def _get_ai_completions(self, file_path: str, line: int, character: int, context: Dict[str, Any]) -> List[CompletionItem]:
        """Get AI-powered completions."""
        completions = []
        
        try:
            # This would integrate with AI completion services
            # For now, return contextual suggestions based on patterns
            
            word_prefix = context.get('word_prefix', '')
            if len(word_prefix) >= 3:
                # Generate contextual completions based on common patterns
                ai_suggestions = self._generate_contextual_suggestions(context)
                
                for suggestion in ai_suggestions:
                    completion = CompletionItem(
                        label=suggestion['label'],
                        kind=suggestion.get('kind', 'Text'),
                        detail=suggestion.get('detail', 'AI suggestion'),
                        insert_text=suggestion.get('insert_text'),
                        score=suggestion.get('score', 0.6),
                        source="ai_powered"
                    )
                    completions.append(completion)
                    
        except Exception as e:
            logger.error(f"Error getting AI completions: {e}")
        
        return completions
    
    def _process_completions(self, completions: List[CompletionItem], context: Dict[str, Any]) -> List[CompletionItem]:
        """Process and rank completions."""
        # Remove duplicates
        seen = set()
        unique_completions = []
        
        for comp in completions:
            key = (comp.label, comp.kind)
            if key not in seen:
                seen.add(key)
                unique_completions.append(comp)
        
        # Sort by score (descending)
        unique_completions.sort(key=lambda x: x.score, reverse=True)
        
        # Apply additional ranking based on context
        for i, comp in enumerate(unique_completions):
            # Boost score for exact prefix matches
            word_prefix = context.get('word_prefix', '').lower()
            if comp.label.lower().startswith(word_prefix):
                comp.score += 0.2
            
            # Boost score for local symbols
            if comp.source == "local_symbols":
                comp.score += 0.1
            
            # Set sort text for stable ordering
            comp.sort_text = f"{1000 - int(comp.score * 100):04d}_{i:04d}"
        
        # Re-sort after score adjustments
        unique_completions.sort(key=lambda x: x.score, reverse=True)
        
        return unique_completions
    
    def _build_symbol_index(self) -> None:
        """Build index of all symbols in the codebase."""
        try:
            self._symbol_index.clear()
            
            for file in self.codebase.files:
                for symbol in file.symbols:
                    self._symbol_index[symbol.name].append(symbol)
            
            logger.debug(f"Built symbol index with {len(self._symbol_index)} entries")
            
        except Exception as e:
            logger.error(f"Error building symbol index: {e}")
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.java': 'java',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php'
        }
        return language_map.get(ext, 'unknown')
    
    def _is_in_string(self, prefix: str) -> bool:
        """Check if position is inside a string literal."""
        # Simple heuristic - count quotes
        single_quotes = prefix.count("'") - prefix.count("\\'")
        double_quotes = prefix.count('"') - prefix.count('\\"')
        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)
    
    def _is_in_comment(self, prefix: str) -> bool:
        """Check if position is inside a comment."""
        # Simple heuristic for common comment patterns
        return '//' in prefix or '/*' in prefix or '#' in prefix
    
    def _extract_word_prefix(self, prefix: str) -> str:
        """Extract the word prefix for completion."""
        # Find the last word boundary
        match = re.search(r'(\w+)$', prefix)
        return match.group(1) if match else ''
    
    def _get_scope_context(self, file_obj, line: int) -> Dict[str, Any]:
        """Get scope context (function, class, etc.)."""
        # This would analyze the AST to determine current scope
        return {'type': 'global', 'name': None}
    
    def _get_imports_context(self, file_obj) -> List[Dict[str, Any]]:
        """Get imports context from the file."""
        imports = []
        try:
            for import_stmt in file_obj.imports:
                imports.append({
                    'module': import_stmt.module_name if hasattr(import_stmt, 'module_name') else 'unknown',
                    'names': import_stmt.imported_names if hasattr(import_stmt, 'imported_names') else [],
                    'alias': import_stmt.alias if hasattr(import_stmt, 'alias') else None
                })
        except Exception as e:
            logger.debug(f"Error getting imports context: {e}")
        
        return imports
    
    def _get_imported_symbols(self, import_info: Dict[str, Any]) -> List[Symbol]:
        """Get symbols from an import."""
        # This would resolve imported symbols
        return []
    
    def _symbol_to_completion_kind(self, symbol: Symbol) -> str:
        """Convert symbol type to completion kind."""
        symbol_type = getattr(symbol, 'symbol_type', 'unknown')
        kind_map = {
            'function': 'Function',
            'class': 'Class',
            'variable': 'Variable',
            'constant': 'Constant',
            'property': 'Property',
            'method': 'Method',
            'field': 'Field',
            'enum': 'Enum',
            'interface': 'Interface',
            'module': 'Module'
        }
        return kind_map.get(symbol_type, 'Text')
    
    def _get_symbol_detail(self, symbol: Symbol) -> Optional[str]:
        """Get detail information for a symbol."""
        try:
            if hasattr(symbol, 'signature'):
                return symbol.signature
            elif hasattr(symbol, 'type_annotation'):
                return symbol.type_annotation
            else:
                return None
        except Exception:
            return None
    
    def _get_symbol_documentation(self, symbol: Symbol) -> Optional[str]:
        """Get documentation for a symbol."""
        try:
            if hasattr(symbol, 'docstring'):
                return symbol.docstring
            else:
                return None
        except Exception:
            return None
    
    def _calculate_symbol_score(self, symbol: Symbol, context: Dict[str, Any]) -> float:
        """Calculate relevance score for a symbol."""
        score = 0.5  # Base score
        
        # Boost score based on symbol type
        symbol_type = getattr(symbol, 'symbol_type', 'unknown')
        type_scores = {
            'function': 0.8,
            'method': 0.8,
            'class': 0.7,
            'variable': 0.6,
            'constant': 0.5
        }
        score = type_scores.get(symbol_type, score)
        
        # Boost score for exact matches
        word_prefix = context.get('word_prefix', '').lower()
        if symbol.name and symbol.name.lower() == word_prefix:
            score += 0.3
        elif symbol.name and symbol.name.lower().startswith(word_prefix):
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_language_keywords(self, language: str) -> List[str]:
        """Get keywords for a programming language."""
        keywords_map = {
            'python': [
                'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
                'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
                'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
                'async', 'await'
            ],
            'typescript': [
                'abstract', 'any', 'as', 'boolean', 'break', 'case', 'catch', 'class', 'const',
                'continue', 'debugger', 'declare', 'default', 'delete', 'do', 'else', 'enum',
                'export', 'extends', 'false', 'finally', 'for', 'from', 'function', 'if',
                'implements', 'import', 'in', 'instanceof', 'interface', 'let', 'new', 'null',
                'number', 'package', 'private', 'protected', 'public', 'return', 'static',
                'string', 'super', 'switch', 'this', 'throw', 'true', 'try', 'type', 'typeof',
                'var', 'void', 'while', 'with', 'yield'
            ],
            'java': [
                'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
                'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
                'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
                'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package',
                'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp',
                'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient',
                'try', 'void', 'volatile', 'while'
            ]
        }
        return keywords_map.get(language, [])
    
    def _get_language_snippets(self, language: str) -> Dict[str, Dict[str, str]]:
        """Get code snippets for a programming language."""
        snippets_map = {
            'python': {
                'if': {
                    'description': 'if statement',
                    'body': 'if ${1:condition}:\n    ${2:pass}'
                },
                'for': {
                    'description': 'for loop',
                    'body': 'for ${1:item} in ${2:iterable}:\n    ${3:pass}'
                },
                'def': {
                    'description': 'function definition',
                    'body': 'def ${1:function_name}(${2:parameters}):\n    """${3:docstring}"""\n    ${4:pass}'
                },
                'class': {
                    'description': 'class definition',
                    'body': 'class ${1:ClassName}:\n    """${2:docstring}"""\n    \n    def __init__(self${3:, parameters}):\n        ${4:pass}'
                }
            },
            'typescript': {
                'if': {
                    'description': 'if statement',
                    'body': 'if (${1:condition}) {\n    ${2:// code}\n}'
                },
                'for': {
                    'description': 'for loop',
                    'body': 'for (${1:let i = 0}; ${2:i < length}; ${3:i++}) {\n    ${4:// code}\n}'
                },
                'function': {
                    'description': 'function declaration',
                    'body': 'function ${1:functionName}(${2:parameters}): ${3:returnType} {\n    ${4:// code}\n}'
                },
                'class': {
                    'description': 'class declaration',
                    'body': 'class ${1:ClassName} {\n    constructor(${2:parameters}) {\n        ${3:// code}\n    }\n}'
                }
            }
        }
        return snippets_map.get(language, {})
    
    def _generate_contextual_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate contextual AI suggestions."""
        suggestions = []
        
        # This would use AI to generate contextual suggestions
        # For now, return some basic pattern-based suggestions
        
        word_prefix = context.get('word_prefix', '')
        language = context.get('language', '')
        
        # Common patterns
        if word_prefix.startswith('get_'):
            suggestions.append({
                'label': f'{word_prefix}result',
                'kind': 'Function',
                'detail': 'Getter method pattern',
                'score': 0.7
            })
        
        if word_prefix.startswith('set_'):
            suggestions.append({
                'label': f'{word_prefix}value',
                'kind': 'Function', 
                'detail': 'Setter method pattern',
                'score': 0.7
            })
        
        return suggestions
    
    def _get_cached_completions(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached completions if still valid."""
        with self._cache_lock:
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                if time.time() - cached_data['timestamp'] < self._cache_max_age:
                    return cached_data['completions']
                else:
                    del self._cache[cache_key]
        return None
    
    def _cache_completions(self, cache_key: str, completions: List[CompletionItem]) -> None:
        """Cache completions result."""
        with self._cache_lock:
            # Limit cache size
            if len(self._cache) >= self.config.cache_size:
                # Remove oldest entries
                oldest_keys = sorted(self._cache.keys(), 
                                   key=lambda k: self._cache[k]['timestamp'])[:10]
                for key in oldest_keys:
                    del self._cache[key]
            
            self._cache[cache_key] = {
                'completions': [comp.to_dict() for comp in completions],
                'timestamp': time.time()
            }
    
    def invalidate_cache(self, file_path: Optional[str] = None) -> None:
        """Invalidate completion cache."""
        with self._cache_lock:
            if file_path:
                # Remove entries for specific file
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(file_path)]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                # Clear entire cache
                self._cache.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        with self._cache_lock:
            cache_size = len(self._cache)
        
        return {
            'initialized': True,
            'cache_size': cache_size,
            'cache_max_size': self.config.cache_size,
            'symbol_index_size': len(self._symbol_index),
            'ai_completions_enabled': self.config.enable_ai_completions
        }
    
    def shutdown(self) -> None:
        """Shutdown the completion provider."""
        with self._cache_lock:
            self._cache.clear()
        self._symbol_index.clear()
        logger.debug("Completion provider shutdown")
