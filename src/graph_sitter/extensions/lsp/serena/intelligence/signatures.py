"""
Signature Provider

Provides function signature help during function calls.
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
class ParameterInfo:
    """Information about a function parameter."""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    documentation: Optional[str] = None
    is_optional: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'typeAnnotation': self.type_annotation,
            'defaultValue': self.default_value,
            'documentation': self.documentation,
            'isOptional': self.is_optional
        }


@dataclass
class SignatureInfo:
    """Information about a function signature."""
    function_name: str
    parameters: List[ParameterInfo]
    return_type: Optional[str] = None
    documentation: Optional[str] = None
    active_parameter: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'functionName': self.function_name,
            'parameters': [param.to_dict() for param in self.parameters],
            'returnType': self.return_type,
            'documentation': self.documentation,
            'activeParameter': self.active_parameter
        }


class SignatureProvider:
    """
    Provides function signature help.
    
    Analyzes function calls and provides parameter information and documentation.
    """
    
    def __init__(self, codebase: Codebase, mcp_bridge: SerenaMCPBridge, config):
        self.codebase = codebase
        self.mcp_bridge = mcp_bridge
        self.config = config
        
        # Signature cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._cache_max_age = 30.0  # seconds
        
        logger.debug("Signature provider initialized")
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get signature help for function call at position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Signature help information or None if not available
        """
        # Check cache first
        cache_key = f"{file_path}:{line}:{character}"
        cached_result = self._get_cached_signature(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Analyze function call context
            call_context = self._analyze_function_call(file_path, line, character)
            if not call_context:
                return None
            
            # Find function definition
            function_symbol = self._find_function_definition(call_context['function_name'], file_path)
            if not function_symbol:
                return None
            
            # Build signature information
            signature_info = self._build_signature_info(function_symbol, call_context)
            
            # Cache result
            if signature_info:
                result = signature_info.to_dict()
                self._cache_signature(cache_key, result)
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting signature help: {e}")
            return None
    
    def _analyze_function_call(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Analyze the function call context at the given position."""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return None
            
            content = file_obj.content
            lines = content.split('\n')
            
            if line >= len(lines):
                return None
            
            # Get current line and analyze backwards to find function call
            current_line = lines[line]
            
            # Find the function call by looking for opening parenthesis
            call_info = self._find_function_call_info(current_line, character, lines, line)
            
            return call_info
            
        except Exception as e:
            logger.error(f"Error analyzing function call: {e}")
            return None
    
    def _find_function_call_info(self, current_line: str, character: int, all_lines: List[str], line_num: int) -> Optional[Dict[str, Any]]:
        """Find function call information from the current position."""
        try:
            # Look backwards from current position to find opening parenthesis
            paren_count = 0
            bracket_count = 0
            in_string = False
            string_char = None
            
            # Start from current character and work backwards
            for i in range(character - 1, -1, -1):
                char = current_line[i]
                
                # Handle string literals
                if char in ['"', "'"] and (i == 0 or current_line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                    continue
                
                if in_string:
                    continue
                
                # Count parentheses and brackets
                if char == ')':
                    paren_count += 1
                elif char == '(':
                    if paren_count == 0:
                        # Found the opening parenthesis of our function call
                        function_name = self._extract_function_name(current_line, i)
                        if function_name:
                            # Count current parameter position
                            active_param = self._count_parameters(current_line, i + 1, character)
                            
                            return {
                                'function_name': function_name,
                                'call_start': i,
                                'active_parameter': active_param,
                                'line': line_num,
                                'character': character
                            }
                    else:
                        paren_count -= 1
                elif char == ']':
                    bracket_count += 1
                elif char == '[':
                    bracket_count -= 1
            
            # If we didn't find it on current line, check previous lines
            # (for multi-line function calls)
            if line_num > 0:
                return self._find_multiline_function_call(all_lines, line_num, character)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding function call info: {e}")
            return None
    
    def _extract_function_name(self, line: str, paren_pos: int) -> Optional[str]:
        """Extract function name before the opening parenthesis."""
        try:
            # Work backwards from parenthesis to find function name
            end_pos = paren_pos
            start_pos = paren_pos - 1
            
            # Skip whitespace
            while start_pos >= 0 and line[start_pos].isspace():
                start_pos -= 1
                end_pos = start_pos + 1
            
            # Find start of identifier
            while start_pos >= 0 and (line[start_pos].isalnum() or line[start_pos] in ['_', '.']):
                start_pos -= 1
            
            start_pos += 1
            
            if start_pos < end_pos:
                function_name = line[start_pos:end_pos]
                # Handle method calls (obj.method)
                if '.' in function_name:
                    return function_name.split('.')[-1]
                return function_name
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting function name: {e}")
            return None
    
    def _count_parameters(self, line: str, start_pos: int, end_pos: int) -> int:
        """Count the current parameter position in the function call."""
        try:
            param_count = 0
            paren_count = 0
            bracket_count = 0
            in_string = False
            string_char = None
            
            for i in range(start_pos, min(end_pos, len(line))):
                char = line[i]
                
                # Handle string literals
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                    continue
                
                if in_string:
                    continue
                
                # Count nested structures
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                elif char == ',' and paren_count == 0 and bracket_count == 0:
                    param_count += 1
            
            return param_count
            
        except Exception as e:
            logger.debug(f"Error counting parameters: {e}")
            return 0
    
    def _find_multiline_function_call(self, lines: List[str], current_line: int, character: int) -> Optional[Dict[str, Any]]:
        """Find function call that spans multiple lines."""
        try:
            # This is a simplified implementation
            # A full implementation would need to handle complex multi-line scenarios
            
            # Look at previous lines for unclosed parentheses
            for line_idx in range(current_line - 1, max(0, current_line - 5), -1):
                line = lines[line_idx]
                
                # Look for function calls in this line
                for i, char in enumerate(line):
                    if char == '(':
                        function_name = self._extract_function_name(line, i)
                        if function_name:
                            # Count parameters across multiple lines
                            active_param = self._count_multiline_parameters(lines, line_idx, i + 1, current_line, character)
                            
                            return {
                                'function_name': function_name,
                                'call_start': i,
                                'active_parameter': active_param,
                                'line': line_idx,
                                'character': i
                            }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding multiline function call: {e}")
            return None
    
    def _count_multiline_parameters(self, lines: List[str], start_line: int, start_char: int, end_line: int, end_char: int) -> int:
        """Count parameters across multiple lines."""
        try:
            param_count = 0
            paren_count = 0
            bracket_count = 0
            in_string = False
            string_char = None
            
            # Process from start position to end position
            for line_idx in range(start_line, end_line + 1):
                line = lines[line_idx]
                
                # Determine start and end positions for this line
                if line_idx == start_line:
                    start_pos = start_char
                else:
                    start_pos = 0
                
                if line_idx == end_line:
                    end_pos = min(end_char, len(line))
                else:
                    end_pos = len(line)
                
                # Count parameters in this line segment
                for i in range(start_pos, end_pos):
                    char = line[i]
                    
                    # Handle string literals
                    if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                        continue
                    
                    if in_string:
                        continue
                    
                    # Count nested structures
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                    elif char == ',' and paren_count == 0 and bracket_count == 0:
                        param_count += 1
            
            return param_count
            
        except Exception as e:
            logger.debug(f"Error counting multiline parameters: {e}")
            return 0
    
    def _find_function_definition(self, function_name: str, file_path: str) -> Optional[Symbol]:
        """Find the definition of the function."""
        try:
            # First, look in the current file
            file_obj = self.codebase.get_file(file_path)
            if file_obj:
                for symbol in file_obj.symbols:
                    if symbol.name == function_name and hasattr(symbol, 'parameters'):
                        return symbol
            
            # Then look in imported modules
            if file_obj:
                imported_symbol = self._find_imported_function(file_obj, function_name)
                if imported_symbol:
                    return imported_symbol
            
            # Finally, search globally
            for file in self.codebase.files:
                for symbol in file.symbols:
                    if symbol.name == function_name and hasattr(symbol, 'parameters'):
                        return symbol
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding function definition: {e}")
            return None
    
    def _find_imported_function(self, file_obj, function_name: str) -> Optional[Symbol]:
        """Find function in imported modules."""
        try:
            # This would resolve imported functions
            # For now, return None as this requires complex import resolution
            return None
            
        except Exception as e:
            logger.debug(f"Error finding imported function: {e}")
            return None
    
    def _build_signature_info(self, function_symbol: Symbol, call_context: Dict[str, Any]) -> Optional[SignatureInfo]:
        """Build signature information from function symbol."""
        try:
            function_name = function_symbol.name
            
            # Extract parameters
            parameters = []
            if hasattr(function_symbol, 'parameters'):
                for param in function_symbol.parameters:
                    param_info = ParameterInfo(
                        name=param.name if hasattr(param, 'name') else str(param),
                        type_annotation=getattr(param, 'type_annotation', None),
                        default_value=getattr(param, 'default_value', None),
                        documentation=self._get_parameter_documentation(param, function_symbol),
                        is_optional=getattr(param, 'default_value', None) is not None
                    )
                    parameters.append(param_info)
            
            # Get return type
            return_type = getattr(function_symbol, 'return_type', None)
            
            # Get function documentation
            documentation = self._get_function_documentation(function_symbol)
            
            # Get active parameter
            active_parameter = call_context.get('active_parameter', 0)
            
            return SignatureInfo(
                function_name=function_name,
                parameters=parameters,
                return_type=return_type,
                documentation=documentation,
                active_parameter=min(active_parameter, len(parameters) - 1) if parameters else 0
            )
            
        except Exception as e:
            logger.error(f"Error building signature info: {e}")
            return None
    
    def _get_parameter_documentation(self, param, function_symbol: Symbol) -> Optional[str]:
        """Get documentation for a specific parameter."""
        try:
            # Extract parameter documentation from function docstring
            if hasattr(function_symbol, 'docstring') and function_symbol.docstring:
                docstring = function_symbol.docstring
                param_name = param.name if hasattr(param, 'name') else str(param)
                
                # Look for parameter documentation patterns
                patterns = [
                    rf'{param_name}\s*:\s*(.+?)(?:\n|$)',  # param: description
                    rf'@param\s+{param_name}\s+(.+?)(?:\n|$)',  # @param name description
                    rf':param\s+{param_name}:\s*(.+?)(?:\n|$)',  # :param name: description
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, docstring, re.IGNORECASE | re.MULTILINE)
                    if match:
                        return match.group(1).strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting parameter documentation: {e}")
            return None
    
    def _get_function_documentation(self, function_symbol: Symbol) -> Optional[str]:
        """Get documentation for the function."""
        try:
            if hasattr(function_symbol, 'docstring') and function_symbol.docstring:
                # Extract the main description (before parameter documentation)
                docstring = function_symbol.docstring
                
                # Split on common parameter section markers
                sections = re.split(r'\n\s*(?:Args?|Arguments?|Parameters?|Param|Returns?|Return):', docstring, flags=re.IGNORECASE)
                
                if sections:
                    main_doc = sections[0].strip()
                    # Limit length
                    if len(main_doc) > 300:
                        main_doc = main_doc[:297] + "..."
                    return main_doc
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting function documentation: {e}")
            return None
    
    def _get_cached_signature(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached signature information if still valid."""
        with self._cache_lock:
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                if time.time() - cached_data['timestamp'] < self._cache_max_age:
                    return cached_data['signature_info']
                else:
                    del self._cache[cache_key]
        return None
    
    def _cache_signature(self, cache_key: str, signature_info: Dict[str, Any]) -> None:
        """Cache signature information."""
        with self._cache_lock:
            # Limit cache size
            if len(self._cache) >= self.config.cache_size:
                # Remove oldest entries
                oldest_keys = sorted(self._cache.keys(), 
                                   key=lambda k: self._cache[k]['timestamp'])[:10]
                for key in oldest_keys:
                    del self._cache[key]
            
            self._cache[cache_key] = {
                'signature_info': signature_info,
                'timestamp': time.time()
            }
    
    def invalidate_cache(self, file_path: str = None) -> None:
        """Invalidate signature cache."""
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
            'context_signatures_enabled': self.config.enable_context_signatures
        }
    
    def shutdown(self) -> None:
        """Shutdown the signature provider."""
        with self._cache_lock:
            self._cache.clear()
        logger.debug("Signature provider shutdown")
