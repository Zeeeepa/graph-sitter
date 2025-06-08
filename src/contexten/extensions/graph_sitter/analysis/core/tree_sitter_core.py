#!/usr/bin/env python3
"""
Unified Tree-sitter Core

Standardized tree-sitter integration following official API patterns.
This module provides a clean, efficient interface to tree-sitter functionality
that eliminates the need for try/catch patterns and custom workarounds.

Based on official tree-sitter documentation:
- https://tree-sitter.github.io/tree-sitter/using-parsers
- https://tree-sitter.github.io/py-tree-sitter/
"""

import logging
from typing import Dict, List, Any, Optional, Iterator, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser, Node, Query, Tree, TreeCursor

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of parsing a file with tree-sitter."""
    
    tree: Tree
    source_code: bytes
    file_path: str
    language: str
    parse_time: float
    has_errors: bool


@dataclass
class QueryMatch:
    """Result of a tree-sitter query match."""
    
    node: Node
    captures: Dict[str, Node]
    file_path: str
    start_byte: int
    end_byte: int
    start_point: Tuple[int, int]  # (row, column)
    end_point: Tuple[int, int]    # (row, column)
    text: str


class TreeSitterCore:
    """
    Unified tree-sitter core following official API patterns.
    
    This class provides a standardized interface to tree-sitter functionality,
    eliminating the need for try/catch patterns and custom workarounds.
    """
    
    def __init__(self):
        """Initialize the tree-sitter core."""
        self.logger = logging.getLogger(__name__)
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        self.queries: Dict[str, Dict[str, Query]] = {}  # language -> query_name -> Query
        
        # Initialize supported languages
        self._initialize_languages()
    
    def _initialize_languages(self) -> None:
        """Initialize supported programming languages."""
        language_configs = {
            'python': 'tree_sitter_python',
            'javascript': 'tree_sitter_javascript', 
            'typescript': 'tree_sitter_typescript',
            'java': 'tree_sitter_java',
            'cpp': 'tree_sitter_cpp',
            'c': 'tree_sitter_c',
            'rust': 'tree_sitter_rust',
            'go': 'tree_sitter_go',
        }
        
        for lang_name, module_name in language_configs.items():
            try:
                # Import the language module dynamically
                module = __import__(module_name, fromlist=['language'])
                language = module.language()
                
                # Create parser for this language
                parser = Parser()
                parser.set_language(language)
                
                self.languages[lang_name] = language
                self.parsers[lang_name] = parser
                self.queries[lang_name] = {}
                
                self.logger.debug(f"Successfully initialized {lang_name} language")
                
            except ImportError:
                self.logger.warning(f"Language {lang_name} not available (missing {module_name})")
            except Exception as e:
                self.logger.error(f"Failed to initialize {lang_name}: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.languages.keys())
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a programming language is supported."""
        return language in self.languages
    
    def detect_language(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name if detected, None otherwise
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.rs': 'rust',
            '.go': 'go',
        }
        
        return extension_map.get(extension)
    
    def parse_file(self, file_path: Union[str, Path], language: Optional[str] = None) -> Optional[ParseResult]:
        """
        Parse a file using tree-sitter.
        
        Args:
            file_path: Path to the file to parse
            language: Programming language (auto-detected if None)
            
        Returns:
            ParseResult if successful, None otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None
        
        # Detect language if not provided
        if language is None:
            language = self.detect_language(file_path)
            if language is None:
                self.logger.warning(f"Could not detect language for {file_path}")
                return None
        
        # Check if language is supported
        if not self.is_language_supported(language):
            self.logger.error(f"Language {language} not supported")
            return None
        
        try:
            # Read source code
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            # Parse with tree-sitter
            import time
            start_time = time.time()
            
            parser = self.parsers[language]
            tree = parser.parse(source_code)
            
            parse_time = time.time() - start_time
            
            # Check for parse errors
            has_errors = tree.root_node.has_error
            
            return ParseResult(
                tree=tree,
                source_code=source_code,
                file_path=str(file_path),
                language=language,
                parse_time=parse_time,
                has_errors=has_errors
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def parse_string(self, source_code: Union[str, bytes], language: str) -> Optional[ParseResult]:
        """
        Parse source code string using tree-sitter.
        
        Args:
            source_code: Source code to parse
            language: Programming language
            
        Returns:
            ParseResult if successful, None otherwise
        """
        if not self.is_language_supported(language):
            self.logger.error(f"Language {language} not supported")
            return None
        
        try:
            # Convert to bytes if needed
            if isinstance(source_code, str):
                source_bytes = source_code.encode('utf-8')
            else:
                source_bytes = source_code
            
            # Parse with tree-sitter
            import time
            start_time = time.time()
            
            parser = self.parsers[language]
            tree = parser.parse(source_bytes)
            
            parse_time = time.time() - start_time
            
            # Check for parse errors
            has_errors = tree.root_node.has_error
            
            return ParseResult(
                tree=tree,
                source_code=source_bytes,
                file_path="<string>",
                language=language,
                parse_time=parse_time,
                has_errors=has_errors
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse string: {e}")
            return None
    
    def create_query(self, language: str, query_string: str, query_name: Optional[str] = None) -> Optional[Query]:
        """
        Create a tree-sitter query for pattern matching.
        
        Args:
            language: Programming language
            query_string: Query pattern string
            query_name: Optional name for caching
            
        Returns:
            Query object if successful, None otherwise
        """
        if not self.is_language_supported(language):
            self.logger.error(f"Language {language} not supported")
            return None
        
        try:
            query = Query(self.languages[language], query_string)
            
            # Cache query if name provided
            if query_name:
                self.queries[language][query_name] = query
            
            return query
            
        except Exception as e:
            self.logger.error(f"Failed to create query for {language}: {e}")
            return None
    
    def get_cached_query(self, language: str, query_name: str) -> Optional[Query]:
        """Get a cached query by name."""
        return self.queries.get(language, {}).get(query_name)
    
    def execute_query(self, query: Query, tree: Tree, source_code: bytes, file_path: str = "<unknown>") -> List[QueryMatch]:
        """
        Execute a tree-sitter query on a syntax tree.
        
        Args:
            query: Query object
            tree: Parsed syntax tree
            source_code: Original source code
            file_path: File path for context
            
        Returns:
            List of query matches
        """
        matches = []
        
        try:
            for match in query.matches(tree.root_node):
                # Extract captures
                captures = {}
                for capture in match.captures:
                    capture_name = query.capture_names[capture[1]]
                    captures[capture_name] = capture[0]
                
                # Get primary node (first capture or match node)
                primary_node = match.captures[0][0] if match.captures else tree.root_node
                
                # Extract text
                text = source_code[primary_node.start_byte:primary_node.end_byte].decode('utf-8', errors='ignore')
                
                match_result = QueryMatch(
                    node=primary_node,
                    captures=captures,
                    file_path=file_path,
                    start_byte=primary_node.start_byte,
                    end_byte=primary_node.end_byte,
                    start_point=(primary_node.start_point.row, primary_node.start_point.column),
                    end_point=(primary_node.end_point.row, primary_node.end_point.column),
                    text=text
                )
                
                matches.append(match_result)
                
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
        
        return matches
    
    def walk_tree(self, tree: Tree) -> TreeCursor:
        """
        Create a tree cursor for efficient tree traversal.
        
        Args:
            tree: Parsed syntax tree
            
        Returns:
            TreeCursor for traversal
        """
        return tree.walk()
    
    def get_node_text(self, node: Node, source_code: bytes) -> str:
        """
        Extract text content of a node.
        
        Args:
            node: Tree-sitter node
            source_code: Original source code
            
        Returns:
            Text content of the node
        """
        return source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
    
    def find_nodes_by_type(self, tree: Tree, node_type: str) -> List[Node]:
        """
        Find all nodes of a specific type in the tree.
        
        Args:
            tree: Parsed syntax tree
            node_type: Node type to search for
            
        Returns:
            List of matching nodes
        """
        nodes = []
        
        def visit_node(node: Node):
            if node.type == node_type:
                nodes.append(node)
            for child in node.children:
                visit_node(child)
        
        visit_node(tree.root_node)
        return nodes
    
    def get_node_children_by_field(self, node: Node, field_name: str) -> List[Node]:
        """
        Get child nodes by field name using official API.
        
        Args:
            node: Parent node
            field_name: Field name to search for
            
        Returns:
            List of child nodes with the specified field name
        """
        return node.children_by_field_name(field_name)
    
    def get_node_child_by_field(self, node: Node, field_name: str) -> Optional[Node]:
        """
        Get first child node by field name using official API.
        
        Args:
            node: Parent node
            field_name: Field name to search for
            
        Returns:
            First child node with the specified field name, or None
        """
        return node.child_by_field_name(field_name)


# Global instance for easy access
_tree_sitter_core = None

def get_tree_sitter_core() -> TreeSitterCore:
    """Get the global tree-sitter core instance."""
    global _tree_sitter_core
    if _tree_sitter_core is None:
        _tree_sitter_core = TreeSitterCore()
    return _tree_sitter_core

