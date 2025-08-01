"""
Unified Error Context Engine

This module provides comprehensive error context analysis by consolidating
functionality from advanced_context.py, advanced_error_viewer.py, and 
error_analysis.py into a single, efficient engine.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger
from .unified_error_models import (
    UnifiedError, ErrorContext, RelatedSymbol, ErrorFix, FixConfidence
)

logger = get_logger(__name__)


class SymbolAnalyzer:
    """Analyzes symbols and their relationships for error context."""
    
    def __init__(self, codebase):
        self.codebase = codebase
        self._symbol_cache: Dict[str, Dict[str, Any]] = {}
    
    def analyze_symbol_at_location(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Analyze symbol at a specific location."""
        try:
            # Try to get symbol information from codebase
            if hasattr(self.codebase, 'get_symbol_at_position'):
                return self.codebase.get_symbol_at_position(file_path, line, character)
            
            # Fallback to AST analysis
            return self._analyze_symbol_with_ast(file_path, line, character)
            
        except Exception as e:
            logger.error(f"Error analyzing symbol at {file_path}:{line}:{character}: {e}")
            return None
    
    def _analyze_symbol_with_ast(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Analyze symbol using AST parsing."""
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                return None
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find the node at the given position
            target_node = self._find_node_at_position(tree, line, character)
            if not target_node:
                return None
            
            # Analyze the node
            return self._analyze_ast_node(target_node, source)
            
        except Exception as e:
            logger.error(f"Error in AST analysis for {file_path}: {e}")
            return None
    
    def _find_node_at_position(self, tree: ast.AST, line: int, character: int) -> Optional[ast.AST]:
        """Find AST node at specific position."""
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
                if node.lineno == line and node.col_offset <= character:
                    # Check if this is the most specific node
                    if hasattr(node, 'end_col_offset') and node.end_col_offset:
                        if character <= node.end_col_offset:
                            return node
                    else:
                        return node
        return None
    
    def _analyze_ast_node(self, node: ast.AST, source: str) -> Dict[str, Any]:
        """Analyze an AST node to extract symbol information."""
        info = {
            'type': type(node).__name__,
            'line': getattr(node, 'lineno', 0),
            'column': getattr(node, 'col_offset', 0)
        }
        
        if isinstance(node, ast.Name):
            info['name'] = node.id
            info['context'] = type(node.ctx).__name__
            
        elif isinstance(node, ast.FunctionDef):
            info['name'] = node.name
            info['args'] = [arg.arg for arg in node.args.args]
            info['returns'] = ast.unparse(node.returns) if node.returns else None
            
        elif isinstance(node, ast.ClassDef):
            info['name'] = node.name
            info['bases'] = [ast.unparse(base) for base in node.bases]
            
        elif isinstance(node, ast.Attribute):
            info['attr'] = node.attr
            info['value'] = ast.unparse(node.value)
            
        elif isinstance(node, ast.Call):
            info['func'] = ast.unparse(node.func)
            info['args'] = [ast.unparse(arg) for arg in node.args]
        
        return info
    
    def find_symbol_definitions(self, symbol_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Find all definitions of a symbol."""
        definitions = []
        
        try:
            # Try codebase symbol search first
            if hasattr(self.codebase, 'find_symbol_definitions'):
                return self.codebase.find_symbol_definitions(symbol_name, file_path)
            
            # Fallback to file-based search
            definitions.extend(self._find_definitions_in_file(symbol_name, file_path))
            
            # Search in imported modules
            imports = self._get_file_imports(file_path)
            for import_info in imports:
                if symbol_name in import_info.get('symbols', []):
                    definitions.extend(self._find_definitions_in_module(symbol_name, import_info))
            
        except Exception as e:
            logger.error(f"Error finding definitions for {symbol_name}: {e}")
        
        return definitions
    
    def find_symbol_usages(self, symbol_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Find all usages of a symbol."""
        usages = []
        
        try:
            # Try codebase symbol search first
            if hasattr(self.codebase, 'find_symbol_usages'):
                return self.codebase.find_symbol_usages(symbol_name, file_path)
            
            # Fallback to grep-like search
            usages.extend(self._find_usages_in_codebase(symbol_name))
            
        except Exception as e:
            logger.error(f"Error finding usages for {symbol_name}: {e}")
        
        return usages
    
    def _find_definitions_in_file(self, symbol_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Find symbol definitions in a specific file."""
        definitions = []
        
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                return definitions
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Look for function definitions
                if f"def {symbol_name}(" in line:
                    definitions.append({
                        'type': 'function',
                        'name': symbol_name,
                        'file': file_path,
                        'line': i,
                        'definition': line.strip()
                    })
                
                # Look for class definitions
                elif f"class {symbol_name}" in line:
                    definitions.append({
                        'type': 'class',
                        'name': symbol_name,
                        'file': file_path,
                        'line': i,
                        'definition': line.strip()
                    })
                
                # Look for variable assignments
                elif f"{symbol_name} =" in line:
                    definitions.append({
                        'type': 'variable',
                        'name': symbol_name,
                        'file': file_path,
                        'line': i,
                        'definition': line.strip()
                    })
        
        except Exception as e:
            logger.error(f"Error searching definitions in {file_path}: {e}")
        
        return definitions
    
    def _find_usages_in_codebase(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find symbol usages across the codebase."""
        usages = []
        
        try:
            # Get all Python files
            if hasattr(self.codebase, 'files'):
                python_files = [f for f in self.codebase.files if f.file_path.endswith('.py')]
            else:
                # Fallback to directory traversal
                python_files = list(Path(self.codebase.repo_path).rglob("*.py"))
                python_files = [{'file_path': str(f)} for f in python_files]
            
            for file_info in python_files:
                file_path = file_info.get('file_path', str(file_info))
                usages.extend(self._find_usages_in_file(symbol_name, file_path))
        
        except Exception as e:
            logger.error(f"Error searching usages in codebase: {e}")
        
        return usages
    
    def _find_usages_in_file(self, symbol_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Find symbol usages in a specific file."""
        usages = []
        
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                return usages
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if symbol_name in line:
                    # More sophisticated check to avoid false positives
                    if re.search(r'\b' + re.escape(symbol_name) + r'\b', line):
                        usages.append({
                            'file': file_path,
                            'line': i,
                            'context': line.strip(),
                            'type': 'usage'
                        })
        
        except Exception as e:
            logger.error(f"Error searching usages in {file_path}: {e}")
        
        return usages
    
    def _get_file_imports(self, file_path: str) -> List[Dict[str, Any]]:
        """Get import information from a file."""
        imports = []
        
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                return imports
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'symbols': [alias.asname or alias.name]
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    symbols = [alias.asname or alias.name for alias in node.names]
                    imports.append({
                        'type': 'from_import',
                        'module': node.module,
                        'symbols': symbols
                    })
        
        except Exception as e:
            logger.error(f"Error parsing imports from {file_path}: {e}")
        
        return imports


class ErrorContextEngine:
    """
    Unified engine for providing comprehensive error context.
    
    This consolidates functionality from multiple context analysis modules
    into a single, efficient system.
    """
    
    def __init__(self, codebase):
        self.codebase = codebase
        self.symbol_analyzer = SymbolAnalyzer(codebase)
        self._context_cache: Dict[str, ErrorContext] = {}
    
    def get_full_error_context(self, error: UnifiedError) -> ErrorContext:
        """
        Get comprehensive context for an error.
        
        Args:
            error: The error to analyze
            
        Returns:
            Complete error context information
        """
        # Check cache first
        if error.id in self._context_cache:
            return self._context_cache[error.id]
        
        context = ErrorContext(error=error)
        
        try:
            # Get surrounding code
            context.surrounding_code = self._get_surrounding_code(error)
            
            # Analyze function/class context
            context.function_context = self._get_function_context(error)
            context.class_context = self._get_class_context(error)
            
            # Analyze symbols
            context.symbol_definitions = self._get_symbol_definitions(error)
            context.symbol_usages = self._get_symbol_usages(error)
            
            # Find related errors
            context.related_errors = self._find_related_errors(error)
            context.similar_errors = self._find_similar_errors(error)
            
            # Analyze impact
            context.affected_functions = self._get_affected_functions(error)
            context.affected_classes = self._get_affected_classes(error)
            context.affected_files = self._get_affected_files(error)
            
            # Generate fix recommendations
            context.recommended_fixes = self._generate_enhanced_fixes(error, context)
            context.fix_priority = self._determine_fix_priority(error, context)
            
            # Cache the result
            self._context_cache[error.id] = context
            
        except Exception as e:
            logger.error(f"Error generating context for {error.id}: {e}")
        
        return context
    
    def _get_surrounding_code(self, error: UnifiedError, context_lines: int = 10) -> str:
        """Get surrounding code context."""
        try:
            file_path = Path(error.location.file_path)
            if not file_path.exists():
                return ""
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start_line = max(0, error.location.line - context_lines - 1)
            end_line = min(len(lines), error.location.line + context_lines)
            
            context_lines_list = []
            for i in range(start_line, end_line):
                line_num = i + 1
                prefix = ">>> " if line_num == error.location.line else "    "
                context_lines_list.append(f"{prefix}{line_num:4d}: {lines[i].rstrip()}")
            
            return "\n".join(context_lines_list)
            
        except Exception as e:
            logger.error(f"Error getting surrounding code: {e}")
            return ""
    
    def _get_function_context(self, error: UnifiedError) -> Optional[Dict[str, Any]]:
        """Get context of the function containing the error."""
        try:
            # Try to get function information from codebase
            if hasattr(self.codebase, 'get_function_at_line'):
                return self.codebase.get_function_at_line(
                    error.location.file_path, 
                    error.location.line
                )
            
            # Fallback to AST analysis
            return self._get_function_context_ast(error)
            
        except Exception as e:
            logger.error(f"Error getting function context: {e}")
            return None
    
    def _get_function_context_ast(self, error: UnifiedError) -> Optional[Dict[str, Any]]:
        """Get function context using AST analysis."""
        try:
            file_path = Path(error.location.file_path)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find the function containing the error line
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if (hasattr(node, 'lineno') and 
                        node.lineno <= error.location.line <= 
                        getattr(node, 'end_lineno', node.lineno + 100)):
                        
                        return {
                            'name': node.name,
                            'args': [arg.arg for arg in node.args.args],
                            'returns': ast.unparse(node.returns) if node.returns else None,
                            'line_start': node.lineno,
                            'line_end': getattr(node, 'end_lineno', None),
                            'docstring': ast.get_docstring(node)
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in AST function analysis: {e}")
            return None
    
    def _get_class_context(self, error: UnifiedError) -> Optional[Dict[str, Any]]:
        """Get context of the class containing the error."""
        try:
            # Similar to function context but for classes
            file_path = Path(error.location.file_path)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find the class containing the error line
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if (hasattr(node, 'lineno') and 
                        node.lineno <= error.location.line <= 
                        getattr(node, 'end_lineno', node.lineno + 1000)):
                        
                        return {
                            'name': node.name,
                            'bases': [ast.unparse(base) for base in node.bases],
                            'line_start': node.lineno,
                            'line_end': getattr(node, 'end_lineno', None),
                            'docstring': ast.get_docstring(node),
                            'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting class context: {e}")
            return None
    
    def _get_symbol_definitions(self, error: UnifiedError) -> List[Dict[str, Any]]:
        """Get symbol definitions related to the error."""
        definitions = []
        
        try:
            # Extract potential symbol names from error message
            symbol_names = self._extract_symbol_names(error.message)
            
            for symbol_name in symbol_names:
                symbol_defs = self.symbol_analyzer.find_symbol_definitions(
                    symbol_name, error.location.file_path
                )
                definitions.extend(symbol_defs)
        
        except Exception as e:
            logger.error(f"Error getting symbol definitions: {e}")
        
        return definitions
    
    def _get_symbol_usages(self, error: UnifiedError) -> List[Dict[str, Any]]:
        """Get symbol usages related to the error."""
        usages = []
        
        try:
            # Extract potential symbol names from error message
            symbol_names = self._extract_symbol_names(error.message)
            
            for symbol_name in symbol_names:
                symbol_usages = self.symbol_analyzer.find_symbol_usages(
                    symbol_name, error.location.file_path
                )
                usages.extend(symbol_usages)
        
        except Exception as e:
            logger.error(f"Error getting symbol usages: {e}")
        
        return usages
    
    def _extract_symbol_names(self, message: str) -> List[str]:
        """Extract potential symbol names from error message."""
        symbols = []
        
        # Look for quoted names
        quoted_matches = re.findall(r"'([^']+)'", message)
        symbols.extend(quoted_matches)
        
        # Look for specific patterns
        patterns = [
            r"undefined name '([^']+)'",
            r"name '([^']+)' is not defined",
            r"cannot import name '([^']+)'",
            r"module '([^']+)' has no attribute",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            symbols.extend(matches)
        
        return list(set(symbols))  # Remove duplicates
    
    def _find_related_errors(self, error: UnifiedError) -> List[UnifiedError]:
        """Find errors related to this one."""
        # This would typically use the error manager to find related errors
        # For now, return empty list
        return []
    
    def _find_similar_errors(self, error: UnifiedError) -> List[UnifiedError]:
        """Find similar errors in the codebase."""
        # This would typically use the error manager to find similar errors
        # For now, return empty list
        return []
    
    def _get_affected_functions(self, error: UnifiedError) -> List[str]:
        """Get functions that might be affected by this error."""
        affected = []
        
        try:
            # If error is in a function, that function is affected
            func_context = self._get_function_context(error)
            if func_context:
                affected.append(func_context['name'])
            
            # Find functions that call the affected function
            # This would require more sophisticated analysis
            
        except Exception as e:
            logger.error(f"Error finding affected functions: {e}")
        
        return affected
    
    def _get_affected_classes(self, error: UnifiedError) -> List[str]:
        """Get classes that might be affected by this error."""
        affected = []
        
        try:
            # If error is in a class, that class is affected
            class_context = self._get_class_context(error)
            if class_context:
                affected.append(class_context['name'])
        
        except Exception as e:
            logger.error(f"Error finding affected classes: {e}")
        
        return affected
    
    def _get_affected_files(self, error: UnifiedError) -> List[str]:
        """Get files that might be affected by this error."""
        affected = [error.location.file_path]
        
        try:
            # Find files that import from the error file
            # This would require import analysis across the codebase
            pass
        
        except Exception as e:
            logger.error(f"Error finding affected files: {e}")
        
        return affected
    
    def _generate_enhanced_fixes(self, error: UnifiedError, context: ErrorContext) -> List[ErrorFix]:
        """Generate enhanced fixes based on full context."""
        fixes = list(error.fixes)  # Start with existing fixes
        
        try:
            # Generate context-aware fixes
            if context.function_context:
                fixes.extend(self._generate_function_fixes(error, context.function_context))
            
            if context.class_context:
                fixes.extend(self._generate_class_fixes(error, context.class_context))
            
            if context.symbol_definitions:
                fixes.extend(self._generate_symbol_fixes(error, context.symbol_definitions))
        
        except Exception as e:
            logger.error(f"Error generating enhanced fixes: {e}")
        
        return fixes
    
    def _generate_function_fixes(self, error: UnifiedError, func_context: Dict[str, Any]) -> List[ErrorFix]:
        """Generate fixes specific to function context."""
        fixes = []
        
        # Example: If error is about missing return statement
        if "missing return" in error.message.lower():
            fixes.append(ErrorFix(
                id=f"add_return_{error.id}",
                title="Add return statement",
                description=f"Add return statement to function '{func_context['name']}'",
                confidence=FixConfidence.MEDIUM,
                changes=[{
                    'type': 'add_return',
                    'file': error.location.file_path,
                    'function': func_context['name']
                }]
            ))
        
        return fixes
    
    def _generate_class_fixes(self, error: UnifiedError, class_context: Dict[str, Any]) -> List[ErrorFix]:
        """Generate fixes specific to class context."""
        fixes = []
        
        # Example: If error is about missing __init__ method
        if "__init__" in error.message and "missing" in error.message.lower():
            fixes.append(ErrorFix(
                id=f"add_init_{error.id}",
                title="Add __init__ method",
                description=f"Add __init__ method to class '{class_context['name']}'",
                confidence=FixConfidence.MEDIUM,
                changes=[{
                    'type': 'add_method',
                    'file': error.location.file_path,
                    'class': class_context['name'],
                    'method': '__init__'
                }]
            ))
        
        return fixes
    
    def _generate_symbol_fixes(self, error: UnifiedError, symbol_defs: List[Dict[str, Any]]) -> List[ErrorFix]:
        """Generate fixes based on symbol definitions."""
        fixes = []
        
        # Example: If we have symbol definitions, we can suggest more specific fixes
        for symbol_def in symbol_defs:
            if symbol_def['type'] == 'function' and "argument" in error.message.lower():
                fixes.append(ErrorFix(
                    id=f"fix_args_{error.id}",
                    title=f"Fix arguments for {symbol_def['name']}",
                    description=f"Fix function call arguments based on definition",
                    confidence=FixConfidence.MEDIUM,
                    changes=[{
                        'type': 'fix_arguments',
                        'file': error.location.file_path,
                        'line': error.location.line,
                        'function': symbol_def['name']
                    }]
                ))
        
        return fixes
    
    def _determine_fix_priority(self, error: UnifiedError, context: ErrorContext) -> str:
        """Determine the priority for fixing this error."""
        if error.severity == error.severity.ERROR:
            if context.affected_functions or context.affected_classes:
                return "high"
            else:
                return "medium"
        elif error.severity == error.severity.WARNING:
            return "medium"
        else:
            return "low"
    
    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._context_cache.clear()

