"""
Common Tree-sitter Query Patterns

Language-agnostic query patterns that work across multiple programming languages.
"""

from typing import Dict, List, Optional
from ..core.tree_sitter_core import TreeSitterCore, QueryMatch


class CommonQueries:
    """Common query patterns that work across multiple languages."""
    
    def __init__(self, core: TreeSitterCore):
        """Initialize common queries with tree-sitter core."""
        self.core = core
        self._compiled_queries = {}
    
    def create_generic_query(self, language: str, pattern: str, name: str) -> Optional:
        """Create a generic query for any language."""
        return self.core.create_query(language, pattern, f"common_{name}_{language}")
    
    def find_comments(self, parse_result, language: str) -> List[QueryMatch]:
        """Find comments in any language (language-specific implementation needed)."""
        comment_patterns = {
            'python': '(comment) @comment',
            'javascript': '(comment) @comment',
            'typescript': '(comment) @comment',
            'java': '(line_comment) @comment (block_comment) @comment',
            'cpp': '(comment) @comment',
            'c': '(comment) @comment',
            'rust': '(line_comment) @comment (block_comment) @comment',
            'go': '(comment) @comment',
        }
        
        pattern = comment_patterns.get(language)
        if not pattern:
            return []
        
        query = self.core.create_query(language, pattern)
        if not query:
            return []
        
        return self.core.execute_query(
            query,
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_string_literals(self, parse_result, language: str) -> List[QueryMatch]:
        """Find string literals in any language."""
        string_patterns = {
            'python': '(string) @string',
            'javascript': '(string) @string (template_string) @string',
            'typescript': '(string) @string (template_string) @string',
            'java': '(string_literal) @string',
            'cpp': '(string_literal) @string',
            'c': '(string_literal) @string',
            'rust': '(string_literal) @string',
            'go': '(interpreted_string_literal) @string (raw_string_literal) @string',
        }
        
        pattern = string_patterns.get(language)
        if not pattern:
            return []
        
        query = self.core.create_query(language, pattern)
        if not query:
            return []
        
        return self.core.execute_query(
            query,
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def count_lines_of_code(self, parse_result) -> Dict[str, int]:
        """
        Count lines of code using tree-sitter.
        
        Returns:
            Dictionary with line counts
        """
        source_lines = parse_result.source_code.decode('utf-8', errors='ignore').split('\n')
        
        total_lines = len(source_lines)
        blank_lines = sum(1 for line in source_lines if not line.strip())
        
        # Find comments to calculate comment lines
        language = parse_result.language
        comments = self.find_comments(parse_result, language)
        
        comment_lines = set()
        for comment in comments:
            start_row = comment.start_point[0]
            end_row = comment.end_point[0]
            for row in range(start_row, end_row + 1):
                comment_lines.add(row)
        
        code_lines = total_lines - blank_lines - len(comment_lines)
        
        return {
            'total_lines': total_lines,
            'code_lines': max(0, code_lines),
            'comment_lines': len(comment_lines),
            'blank_lines': blank_lines
        }
    
    def analyze_nesting_depth(self, parse_result) -> Dict[str, int]:
        """
        Analyze maximum nesting depth in the code.
        
        Returns:
            Dictionary with nesting depth metrics
        """
        max_depth = 0
        current_depth = 0
        
        def walk_node(node, depth=0):
            nonlocal max_depth, current_depth
            current_depth = depth
            max_depth = max(max_depth, depth)
            
            # Increment depth for nesting constructs
            nesting_types = {
                'if_statement', 'for_statement', 'while_statement', 'try_statement',
                'function_definition', 'class_definition', 'method_definition',
                'block', 'statement_block', 'compound_statement'
            }
            
            if node.type in nesting_types:
                depth += 1
            
            for child in node.children:
                walk_node(child, depth)
        
        walk_node(parse_result.tree.root_node)
        
        return {
            'max_nesting_depth': max_depth,
            'average_nesting_depth': max_depth // 2 if max_depth > 0 else 0
        }
    
    def find_large_functions(self, parse_result, language: str, line_threshold: int = 50) -> List[QueryMatch]:
        """
        Find functions that exceed a certain line count threshold.
        
        Args:
            parse_result: Parsed code result
            language: Programming language
            line_threshold: Maximum acceptable lines for a function
            
        Returns:
            List of large functions
        """
        # Get language-specific function patterns
        function_patterns = {
            'python': '(function_definition) @function',
            'javascript': '[' +
                         '(function_declaration) @function ' +
                         '(arrow_function) @function ' +
                         '(method_definition) @function' +
                         ']',
            'typescript': '[' +
                         '(function_declaration) @function ' +
                         '(arrow_function) @function ' +
                         '(method_definition) @function' +
                         ']',
            'java': '(method_declaration) @function',
            'cpp': '(function_definition) @function',
            'c': '(function_definition) @function',
        }
        
        pattern = function_patterns.get(language)
        if not pattern:
            return []
        
        query = self.core.create_query(language, pattern)
        if not query:
            return []
        
        all_functions = self.core.execute_query(
            query,
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
        
        large_functions = []
        for func in all_functions:
            start_line = func.start_point[0]
            end_line = func.end_point[0]
            line_count = end_line - start_line + 1
            
            if line_count > line_threshold:
                large_functions.append(func)
        
        return large_functions
    
    def calculate_file_metrics(self, parse_result) -> Dict[str, any]:
        """
        Calculate comprehensive file-level metrics.
        
        Returns:
            Dictionary with various file metrics
        """
        language = parse_result.language
        
        # Basic line counts
        line_metrics = self.count_lines_of_code(parse_result)
        
        # Nesting depth
        nesting_metrics = self.analyze_nesting_depth(parse_result)
        
        # Find large functions
        large_functions = self.find_large_functions(parse_result, language)
        
        # Count different node types
        node_counts = {}
        
        def count_nodes(node):
            node_type = node.type
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
            for child in node.children:
                count_nodes(child)
        
        count_nodes(parse_result.tree.root_node)
        
        return {
            **line_metrics,
            **nesting_metrics,
            'large_functions_count': len(large_functions),
            'node_type_counts': node_counts,
            'parse_errors': parse_result.has_errors,
            'parse_time': parse_result.parse_time,
            'file_size_bytes': len(parse_result.source_code)
        }

