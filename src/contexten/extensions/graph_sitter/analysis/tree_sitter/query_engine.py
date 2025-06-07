"""
Tree-sitter Query Engine

Advanced query patterns for code analysis based on tree-sitter syntax trees.
"""

import logging
from typing import Dict, List, Any, Optional, Iterator, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    tree_sitter = None
    Language = None
    Parser = None
    Node = None


@dataclass
class QueryResult:
    """Result of a tree-sitter query."""
    
    node: Any  # tree_sitter.Node
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    text: str
    context: Dict[str, Any]


class QueryEngine:
    """
    Advanced tree-sitter query engine for pattern-based code analysis.
    
    Based on patterns from: https://graph-sitter.com/tutorials/at-a-glance
    """
    
    def __init__(self):
        """Initialize the query engine."""
        self.logger = logging.getLogger(__name__)
        self.parsers = {}
        self.languages = {}
        
        if not TREE_SITTER_AVAILABLE:
            self.logger.warning("tree-sitter not available. Query functionality will be limited.")
    
    def setup_language(self, language_name: str, language_path: Optional[str] = None) -> bool:
        """
        Setup a language for parsing.
        
        Args:
            language_name: Name of the language (e.g., 'python', 'javascript')
            language_path: Optional path to language library
            
        Returns:
            True if setup successful, False otherwise
        """
        if not TREE_SITTER_AVAILABLE:
            return False
        
        try:
            if language_path:
                language = Language(language_path, language_name)
            else:
                # Try to load from common locations
                language = self._load_default_language(language_name)
            
            if language:
                parser = Parser()
                parser.set_language(language)
                
                self.languages[language_name] = language
                self.parsers[language_name] = parser
                
                self.logger.info(f"Successfully setup {language_name} language")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to setup {language_name} language: {e}")
        
        return False
    
    def parse_file(self, file_path: str, language: str) -> Optional[Any]:
        """
        Parse a file using tree-sitter.
        
        Args:
            file_path: Path to the file to parse
            language: Language to use for parsing
            
        Returns:
            Parsed tree or None if parsing failed
        """
        if not TREE_SITTER_AVAILABLE or language not in self.parsers:
            return None
        
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            parser = self.parsers[language]
            tree = parser.parse(source_code)
            
            return tree
            
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def query_pattern(self, tree: Any, pattern: str, language: str) -> List[QueryResult]:
        """
        Execute a query pattern on a syntax tree.
        
        Args:
            tree: Parsed syntax tree
            pattern: Tree-sitter query pattern
            language: Language of the tree
            
        Returns:
            List of query results
        """
        if not TREE_SITTER_AVAILABLE or language not in self.languages:
            return []
        
        try:
            language_obj = self.languages[language]
            query = language_obj.query(pattern)
            
            results = []
            captures = query.captures(tree.root_node)
            
            for node, capture_name in captures:
                result = QueryResult(
                    node=node,
                    file_path="",  # Will be set by caller
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                    start_column=node.start_point[1],
                    end_column=node.end_point[1],
                    text=node.text.decode('utf-8') if node.text else "",
                    context={"capture_name": capture_name}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute query pattern: {e}")
            return []
    
    def find_functions(self, tree: Any, language: str) -> List[QueryResult]:
        """
        Find all function definitions in a syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language of the tree
            
        Returns:
            List of function definitions
        """
        patterns = {
            'python': '''
                (function_def
                  name: (identifier) @function.name
                ) @function.def
            ''',
            'javascript': '''
                (function_declaration
                  name: (identifier) @function.name
                ) @function.def
                
                (arrow_function) @function.def
            ''',
            'typescript': '''
                (function_declaration
                  name: (identifier) @function.name
                ) @function.def
                
                (arrow_function) @function.def
                
                (method_definition
                  name: (property_identifier) @function.name
                ) @function.def
            '''
        }
        
        pattern = patterns.get(language, '')
        if pattern:
            return self.query_pattern(tree, pattern, language)
        return []
    
    def find_classes(self, tree: Any, language: str) -> List[QueryResult]:
        """
        Find all class definitions in a syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language of the tree
            
        Returns:
            List of class definitions
        """
        patterns = {
            'python': '''
                (class_definition
                  name: (identifier) @class.name
                ) @class.def
            ''',
            'javascript': '''
                (class_declaration
                  name: (identifier) @class.name
                ) @class.def
            ''',
            'typescript': '''
                (class_declaration
                  name: (type_identifier) @class.name
                ) @class.def
            '''
        }
        
        pattern = patterns.get(language, '')
        if pattern:
            return self.query_pattern(tree, pattern, language)
        return []
    
    def find_imports(self, tree: Any, language: str) -> List[QueryResult]:
        """
        Find all import statements in a syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language of the tree
            
        Returns:
            List of import statements
        """
        patterns = {
            'python': '''
                (import_statement) @import
                (import_from_statement) @import
            ''',
            'javascript': '''
                (import_statement) @import
            ''',
            'typescript': '''
                (import_statement) @import
            '''
        }
        
        pattern = patterns.get(language, '')
        if pattern:
            return self.query_pattern(tree, pattern, language)
        return []
    
    def find_function_calls(self, tree: Any, language: str) -> List[QueryResult]:
        """
        Find all function calls in a syntax tree.
        
        Args:
            tree: Parsed syntax tree
            language: Language of the tree
            
        Returns:
            List of function calls
        """
        patterns = {
            'python': '''
                (call
                  function: (identifier) @call.function
                ) @call
                
                (call
                  function: (attribute
                    attribute: (identifier) @call.method
                  )
                ) @call
            ''',
            'javascript': '''
                (call_expression
                  function: (identifier) @call.function
                ) @call
                
                (call_expression
                  function: (member_expression
                    property: (property_identifier) @call.method
                  )
                ) @call
            ''',
            'typescript': '''
                (call_expression
                  function: (identifier) @call.function
                ) @call
                
                (call_expression
                  function: (member_expression
                    property: (property_identifier) @call.method
                  )
                ) @call
            '''
        }
        
        pattern = patterns.get(language, '')
        if pattern:
            return self.query_pattern(tree, pattern, language)
        return []
    
    def find_complex_patterns(self, tree: Any, language: str) -> Dict[str, List[QueryResult]]:
        """
        Find complex code patterns that might indicate issues.
        
        Args:
            tree: Parsed syntax tree
            language: Language of the tree
            
        Returns:
            Dictionary of pattern types to results
        """
        results = {}
        
        # Find deeply nested code
        if language == 'python':
            nested_pattern = '''
                (if_statement
                  (if_statement
                    (if_statement) @deep.nested
                  )
                ) @nested
            '''
            results['deep_nesting'] = self.query_pattern(tree, nested_pattern, language)
        
        # Find long parameter lists
        if language in ['python', 'javascript', 'typescript']:
            # This is a simplified pattern - real implementation would be more complex
            results['long_parameters'] = []
        
        # Find TODO/FIXME comments
        comment_patterns = {
            'python': '(comment) @comment',
            'javascript': '(comment) @comment',
            'typescript': '(comment) @comment'
        }
        
        if language in comment_patterns:
            comments = self.query_pattern(tree, comment_patterns[language], language)
            todo_comments = [c for c in comments if 'TODO' in c.text or 'FIXME' in c.text]
            results['todo_comments'] = todo_comments
        
        return results
    
    def analyze_complexity(self, tree: Any, language: str) -> Dict[str, Any]:
        """
        Analyze code complexity using tree-sitter patterns.
        
        Args:
            tree: Parsed syntax tree
            language: Language of the tree
            
        Returns:
            Complexity analysis results
        """
        complexity = {
            'cyclomatic_complexity': 0,
            'nesting_depth': 0,
            'function_count': 0,
            'class_count': 0,
            'branch_count': 0
        }
        
        try:
            # Count functions and classes
            functions = self.find_functions(tree, language)
            classes = self.find_classes(tree, language)
            
            complexity['function_count'] = len(functions)
            complexity['class_count'] = len(classes)
            
            # Count branching statements for cyclomatic complexity
            branch_patterns = {
                'python': '''
                    (if_statement) @branch
                    (while_statement) @branch
                    (for_statement) @branch
                    (try_statement) @branch
                ''',
                'javascript': '''
                    (if_statement) @branch
                    (while_statement) @branch
                    (for_statement) @branch
                    (switch_statement) @branch
                ''',
                'typescript': '''
                    (if_statement) @branch
                    (while_statement) @branch
                    (for_statement) @branch
                    (switch_statement) @branch
                '''
            }
            
            if language in branch_patterns:
                branches = self.query_pattern(tree, branch_patterns[language], language)
                complexity['branch_count'] = len(branches)
                complexity['cyclomatic_complexity'] = len(branches) + 1
            
        except Exception as e:
            self.logger.error(f"Failed to analyze complexity: {e}")
        
        return complexity
    
    def _load_default_language(self, language_name: str) -> Optional[Any]:
        """
        Try to load a language from default locations.
        
        Args:
            language_name: Name of the language
            
        Returns:
            Language object or None
        """
        # This would need to be implemented based on the specific
        # tree-sitter language installation on the system
        self.logger.warning(f"Default language loading not implemented for {language_name}")
        return None
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages.
        
        Returns:
            List of supported language names
        """
        return list(self.languages.keys())
    
    def is_available(self) -> bool:
        """
        Check if tree-sitter is available.
        
        Returns:
            True if tree-sitter is available, False otherwise
        """
        return TREE_SITTER_AVAILABLE

