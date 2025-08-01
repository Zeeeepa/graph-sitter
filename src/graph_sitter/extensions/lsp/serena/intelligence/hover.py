"""
Hover Provider

Provides rich hover information for symbols including documentation,
type information, and contextual details.
"""

import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import threading

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from ..mcp_bridge import SerenaMCPBridge
from graph_sitter.core.symbol import Symbol

logger = get_logger(__name__)


@dataclass
class HoverInfo:
    """Represents hover information for a symbol."""
    symbol_name: str
    symbol_type: str
    signature: Optional[str] = None
    documentation: Optional[str] = None
    type_info: Optional[str] = None
    definition_location: Optional[Dict[str, Any]] = None
    examples: Optional[List[str]] = None
    related_symbols: Optional[List[str]] = None
    source: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'symbolName': self.symbol_name,
            'symbolType': self.symbol_type,
            'signature': self.signature,
            'documentation': self.documentation,
            'typeInfo': self.type_info,
            'definitionLocation': self.definition_location,
            'examples': self.examples or [],
            'relatedSymbols': self.related_symbols or [],
            'source': self.source
        }


class HoverProvider:
    """
    Provides rich hover information for symbols.
    
    Combines LSP hover data with semantic analysis and documentation extraction.
    """
    
    def __init__(self, codebase: Codebase, mcp_bridge: SerenaMCPBridge, config):
        self.codebase = codebase
        self.mcp_bridge = mcp_bridge
        self.config = config
        
        # Hover cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._cache_max_age = 60.0  # seconds (longer than completions)
        
        # Symbol documentation cache
        self._doc_cache: Dict[str, str] = {}
        
        logger.debug("Hover provider initialized")
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get hover information for symbol at position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Hover information or None if not available
        """
        # Check cache first
        cache_key = f"{file_path}:{line}:{character}"
        cached_result = self._get_cached_hover(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Find symbol at position
            symbol = self._find_symbol_at_position(file_path, line, character)
            if not symbol:
                return None
            
            # Build hover information
            hover_info = self._build_hover_info(symbol, file_path, line, character)
            
            # Cache result
            if hover_info:
                result = hover_info.to_dict()
                self._cache_hover(cache_key, result)
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting hover info: {e}")
            return None
    
    def _find_symbol_at_position(self, file_path: str, line: int, character: int) -> Optional[Symbol]:
        """Find symbol at the specified position."""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return None
            
            # Get the word at position
            word = self._get_word_at_position(file_obj.content, line, character)
            if not word:
                return None
            
            # Find matching symbol in file
            for symbol in file_obj.symbols:
                if symbol.name == word:
                    # Check if position is within symbol's range
                    if self._is_position_in_symbol(symbol, line, character):
                        return symbol
            
            # If not found in current file, search in imports
            imported_symbol = self._find_imported_symbol(file_obj, word)
            if imported_symbol:
                return imported_symbol
            
            # Search in global scope
            return self._find_global_symbol(word)
            
        except Exception as e:
            logger.error(f"Error finding symbol at position: {e}")
            return None
    
    def _get_word_at_position(self, content: str, line: int, character: int) -> Optional[str]:
        """Extract word at the specified position."""
        try:
            lines = content.split('\n')
            if line >= len(lines):
                return None
            
            current_line = lines[line]
            if character >= len(current_line):
                return None
            
            # Find word boundaries
            start = character
            end = character
            
            # Expand backwards
            while start > 0 and (current_line[start - 1].isalnum() or current_line[start - 1] == '_'):
                start -= 1
            
            # Expand forwards
            while end < len(current_line) and (current_line[end].isalnum() or current_line[end] == '_'):
                end += 1
            
            word = current_line[start:end]
            return word if word and word.replace('_', '').isalnum() else None
            
        except Exception as e:
            logger.error(f"Error getting word at position: {e}")
            return None
    
    def _is_position_in_symbol(self, symbol: Symbol, line: int, character: int) -> bool:
        """Check if position is within symbol's definition range."""
        try:
            # This would check if the position is within the symbol's span
            # For now, just check if it's the symbol name
            if hasattr(symbol, 'start_line') and hasattr(symbol, 'end_line'):
                return symbol.start_line <= line <= symbol.end_line
            return True  # Assume it matches if no range info
            
        except Exception:
            return True
    
    def _find_imported_symbol(self, file_obj, symbol_name: str) -> Optional[Symbol]:
        """Find symbol in imported modules."""
        try:
            for import_stmt in file_obj.imports:
                # This would resolve imported symbols
                # For now, return None as this requires more complex resolution
                pass
            return None
            
        except Exception as e:
            logger.debug(f"Error finding imported symbol: {e}")
            return None
    
    def _find_global_symbol(self, symbol_name: str) -> Optional[Symbol]:
        """Find symbol in global codebase."""
        try:
            # Search all files for the symbol
            for file in self.codebase.files:
                for symbol in file.symbols:
                    if symbol.name == symbol_name:
                        return symbol
            return None
            
        except Exception as e:
            logger.debug(f"Error finding global symbol: {e}")
            return None
    
    def _build_hover_info(self, symbol: Symbol, file_path: str, line: int, character: int) -> Optional[HoverInfo]:
        """Build comprehensive hover information for a symbol."""
        try:
            # Get basic symbol information
            symbol_name = symbol.name
            symbol_type = self._get_symbol_type(symbol)
            
            # Get signature information
            signature = self._get_symbol_signature(symbol)
            
            # Get documentation
            documentation = self._get_symbol_documentation(symbol)
            
            # Get type information
            type_info = self._get_symbol_type_info(symbol)
            
            # Get definition location
            definition_location = self._get_definition_location(symbol)
            
            # Get examples
            examples = self._get_symbol_examples(symbol)
            
            # Get related symbols
            related_symbols = self._get_related_symbols(symbol)
            
            # Determine source
            source = self._determine_hover_source(symbol, file_path)
            
            return HoverInfo(
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                signature=signature,
                documentation=documentation,
                type_info=type_info,
                definition_location=definition_location,
                examples=examples,
                related_symbols=related_symbols,
                source=source
            )
            
        except Exception as e:
            logger.error(f"Error building hover info: {e}")
            return None
    
    def _get_symbol_type(self, symbol: Symbol) -> str:
        """Get the type of symbol (function, class, variable, etc.)."""
        try:
            if hasattr(symbol, 'symbol_type'):
                return symbol.symbol_type
            elif hasattr(symbol, 'node_type'):
                return symbol.node_type
            else:
                # Infer from symbol properties
                if hasattr(symbol, 'parameters'):
                    return 'function'
                elif hasattr(symbol, 'methods'):
                    return 'class'
                else:
                    return 'variable'
                    
        except Exception:
            return 'unknown'
    
    def _get_symbol_signature(self, symbol: Symbol) -> Optional[str]:
        """Get the signature of a symbol."""
        try:
            if hasattr(symbol, 'signature'):
                return symbol.signature
            
            # Build signature for functions
            if hasattr(symbol, 'parameters'):
                params = []
                for param in symbol.parameters:
                    param_str = param.name if hasattr(param, 'name') else str(param)
                    if hasattr(param, 'type_annotation') and param.type_annotation:
                        param_str += f": {param.type_annotation}"
                    if hasattr(param, 'default_value') and param.default_value:
                        param_str += f" = {param.default_value}"
                    params.append(param_str)
                
                signature = f"{symbol.name}({', '.join(params)})"
                
                # Add return type if available
                if hasattr(symbol, 'return_type') and symbol.return_type:
                    signature += f" -> {symbol.return_type}"
                
                return signature
            
            # For classes, show class definition
            if hasattr(symbol, 'base_classes'):
                bases = symbol.base_classes if symbol.base_classes else []
                if bases:
                    return f"class {symbol.name}({', '.join(bases)})"
                else:
                    return f"class {symbol.name}"
            
            # For variables, show type if available
            if hasattr(symbol, 'type_annotation') and symbol.type_annotation:
                return f"{symbol.name}: {symbol.type_annotation}"
            
            return symbol.name
            
        except Exception as e:
            logger.debug(f"Error getting symbol signature: {e}")
            return symbol.name
    
    def _get_symbol_documentation(self, symbol: Symbol) -> Optional[str]:
        """Get documentation for a symbol."""
        try:
            # Check cache first
            cache_key = f"{symbol.name}_{id(symbol)}"
            if cache_key in self._doc_cache:
                return self._doc_cache[cache_key]
            
            documentation = None
            
            # Get docstring if available
            if hasattr(symbol, 'docstring') and symbol.docstring:
                documentation = symbol.docstring
            
            # For functions/methods, extract docstring from body
            elif hasattr(symbol, 'body') and symbol.body:
                documentation = self._extract_docstring_from_body(symbol.body)
            
            # For classes, get class docstring
            elif hasattr(symbol, 'class_docstring') and symbol.class_docstring:
                documentation = symbol.class_docstring
            
            # Clean up documentation
            if documentation:
                documentation = self._clean_documentation(documentation)
            
            # Cache result
            self._doc_cache[cache_key] = documentation
            
            return documentation
            
        except Exception as e:
            logger.debug(f"Error getting symbol documentation: {e}")
            return None
    
    def _get_symbol_type_info(self, symbol: Symbol) -> Optional[str]:
        """Get type information for a symbol."""
        try:
            type_info = []
            
            # Add type annotation
            if hasattr(symbol, 'type_annotation') and symbol.type_annotation:
                type_info.append(f"Type: {symbol.type_annotation}")
            
            # Add return type for functions
            if hasattr(symbol, 'return_type') and symbol.return_type:
                type_info.append(f"Returns: {symbol.return_type}")
            
            # Add base classes for classes
            if hasattr(symbol, 'base_classes') and symbol.base_classes:
                type_info.append(f"Inherits from: {', '.join(symbol.base_classes)}")
            
            # Add scope information
            if hasattr(symbol, 'scope'):
                type_info.append(f"Scope: {symbol.scope}")
            
            return '\n'.join(type_info) if type_info else None
            
        except Exception as e:
            logger.debug(f"Error getting symbol type info: {e}")
            return None
    
    def _get_definition_location(self, symbol: Symbol) -> Optional[Dict[str, Any]]:
        """Get the definition location of a symbol."""
        try:
            location = {}
            
            if hasattr(symbol, 'file') and symbol.file:
                location['file'] = symbol.file.path
            
            if hasattr(symbol, 'start_line'):
                location['line'] = symbol.start_line
            
            if hasattr(symbol, 'start_character'):
                location['character'] = symbol.start_character
            
            return location if location else None
            
        except Exception as e:
            logger.debug(f"Error getting definition location: {e}")
            return None
    
    def _get_symbol_examples(self, symbol: Symbol) -> Optional[List[str]]:
        """Get usage examples for a symbol."""
        try:
            examples = []
            
            # For functions, create basic usage example
            if hasattr(symbol, 'parameters'):
                if symbol.parameters:
                    param_names = [p.name if hasattr(p, 'name') else 'arg' for p in symbol.parameters[:3]]
                    example = f"{symbol.name}({', '.join(param_names)})"
                else:
                    example = f"{symbol.name}()"
                examples.append(example)
            
            # For classes, create instantiation example
            elif hasattr(symbol, 'methods'):
                examples.append(f"instance = {symbol.name}()")
            
            return examples if examples else None
            
        except Exception as e:
            logger.debug(f"Error getting symbol examples: {e}")
            return None
    
    def _get_related_symbols(self, symbol: Symbol) -> Optional[List[str]]:
        """Get symbols related to this symbol."""
        try:
            related = []
            
            # For methods, add the class
            if hasattr(symbol, 'parent_class') and symbol.parent_class:
                related.append(symbol.parent_class.name)
            
            # For classes, add methods
            if hasattr(symbol, 'methods'):
                related.extend([method.name for method in symbol.methods[:5]])
            
            # For functions, add parameters as related
            if hasattr(symbol, 'parameters'):
                related.extend([p.name for p in symbol.parameters if hasattr(p, 'name')])
            
            return related[:10] if related else None  # Limit to 10 items
            
        except Exception as e:
            logger.debug(f"Error getting related symbols: {e}")
            return None
    
    def _determine_hover_source(self, symbol: Symbol, file_path: str) -> str:
        """Determine the source of hover information."""
        try:
            if hasattr(symbol, 'file') and symbol.file:
                if symbol.file.path == file_path:
                    return "local_file"
                else:
                    return "external_file"
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def _extract_docstring_from_body(self, body: str) -> Optional[str]:
        """Extract docstring from function/class body."""
        try:
            # Look for docstring patterns
            lines = body.strip().split('\n')
            
            # Check for triple-quoted strings at the beginning
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    quote_type = stripped[:3]
                    
                    # Single line docstring
                    if stripped.endswith(quote_type) and len(stripped) > 6:
                        return stripped[3:-3].strip()
                    
                    # Multi-line docstring
                    docstring_lines = [stripped[3:]]
                    for j in range(i + 1, len(lines)):
                        if quote_type in lines[j]:
                            # Found end of docstring
                            end_line = lines[j]
                            end_index = end_line.find(quote_type)
                            docstring_lines.append(end_line[:end_index])
                            break
                        else:
                            docstring_lines.append(lines[j])
                    
                    return '\n'.join(docstring_lines).strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting docstring: {e}")
            return None
    
    def _clean_documentation(self, doc: str) -> str:
        """Clean and format documentation text."""
        try:
            # Remove excessive whitespace
            doc = re.sub(r'\n\s*\n\s*\n', '\n\n', doc)
            
            # Remove leading/trailing whitespace
            doc = doc.strip()
            
            # Limit length
            if len(doc) > 1000:
                doc = doc[:997] + "..."
            
            return doc
            
        except Exception:
            return doc
    
    def _get_cached_hover(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached hover information if still valid."""
        with self._cache_lock:
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                if time.time() - cached_data['timestamp'] < self._cache_max_age:
                    return cached_data['hover_info']
                else:
                    del self._cache[cache_key]
        return None
    
    def _cache_hover(self, cache_key: str, hover_info: Dict[str, Any]) -> None:
        """Cache hover information."""
        with self._cache_lock:
            # Limit cache size
            if len(self._cache) >= self.config.cache_size:
                # Remove oldest entries
                oldest_keys = sorted(self._cache.keys(), 
                                   key=lambda k: self._cache[k]['timestamp'])[:10]
                for key in oldest_keys:
                    del self._cache[key]
            
            self._cache[cache_key] = {
                'hover_info': hover_info,
                'timestamp': time.time()
            }
    
    def invalidate_cache(self, file_path: str = None) -> None:
        """Invalidate hover cache."""
        with self._cache_lock:
            if file_path:
                # Remove entries for specific file
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(file_path)]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                # Clear entire cache
                self._cache.clear()
        
        # Also clear documentation cache
        if not file_path:
            self._doc_cache.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        with self._cache_lock:
            cache_size = len(self._cache)
        
        return {
            'initialized': True,
            'cache_size': cache_size,
            'cache_max_size': self.config.cache_size,
            'doc_cache_size': len(self._doc_cache),
            'semantic_hover_enabled': self.config.enable_semantic_hover
        }
    
    def shutdown(self) -> None:
        """Shutdown the hover provider."""
        with self._cache_lock:
            self._cache.clear()
        self._doc_cache.clear()
        logger.debug("Hover provider shutdown")
