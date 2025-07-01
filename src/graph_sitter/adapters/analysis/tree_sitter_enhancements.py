"""
🌳 Tree-sitter Integration and Query Patterns

Advanced tree-sitter integration with:
- Query pattern execution and analysis
- Syntax tree visualization and exploration
- Pattern-based code search and matching
- Interactive syntax tree navigation
- Advanced code structure analysis

Based on patterns from: https://graph-sitter.com/tutorials/at-a-glance
"""

import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Iterator
from pathlib import Path

try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node, Tree
    TREE_SITTER_AVAILABLE = True
except ImportError:
    print("Warning: tree-sitter not available. Some functionality will be limited.")
    TREE_SITTER_AVAILABLE = False
    Language = object
    Parser = object
    Node = object
    Tree = object


@dataclass
class QueryResult:
    """Result of a tree-sitter query"""
    pattern: str
    matches: List[Dict[str, Any]] = field(default_factory=list)
    file_path: str = ""
    language: str = ""
    total_matches: int = 0


@dataclass
class SyntaxTreeNode:
    """Representation of a syntax tree node"""
    type: str
    text: str = ""
    start_point: Tuple[int, int] = (0, 0)
    end_point: Tuple[int, int] = (0, 0)
    children: List['SyntaxTreeNode'] = field(default_factory=list)
    parent: Optional['SyntaxTreeNode'] = None
    depth: int = 0


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    pattern: str
    node_type: str
    text: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    context: str = ""
    file_path: str = ""


class TreeSitterAnalyzer:
    """
    Advanced tree-sitter analyzer for code structure analysis
    """
    
    def __init__(self, language: str = "python"):
        self.language = language
        self.parser = None
        self.tree_sitter_language = None
        
        if TREE_SITTER_AVAILABLE:
            self._initialize_parser()
    
    def _initialize_parser(self):
        """Initialize tree-sitter parser for the specified language"""
        try:
            # This would need actual language binaries in a real implementation
            # For now, we'll create a mock implementation
            self.parser = Parser()
            # self.tree_sitter_language = Language(library_path, language_name)
            # self.parser.set_language(self.tree_sitter_language)
            print(f"Tree-sitter parser initialized for {self.language}")
        except Exception as e:
            print(f"Error initializing tree-sitter parser: {e}")
    
    def parse_code(self, source_code: str) -> Optional[Tree]:
        """Parse source code into a syntax tree"""
        if not TREE_SITTER_AVAILABLE or not self.parser:
            return None
        
        try:
            tree = self.parser.parse(bytes(source_code, "utf8"))
            return tree
        except Exception as e:
            print(f"Error parsing code: {e}")
            return None
    
    def analyze_structure(self, source_code: str, file_path: str = "") -> Dict[str, Any]:
        """Analyze code structure using tree-sitter"""
        tree = self.parse_code(source_code)
        if not tree:
            return self._fallback_analysis(source_code, file_path)
        
        try:
            root_node = tree.root_node
            
            # Extract structural information
            functions = self._extract_functions(root_node, source_code)
            classes = self._extract_classes(root_node, source_code)
            imports = self._extract_imports(root_node, source_code)
            variables = self._extract_variables(root_node, source_code)
            
            # Calculate metrics
            depth = self._calculate_tree_depth(root_node)
            node_count = self._count_nodes(root_node)
            
            return {
                'file_path': file_path,
                'language': self.language,
                'tree_depth': depth,
                'node_count': node_count,
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'variables': variables,
                'syntax_tree': self._convert_to_dict(root_node, source_code)
            }
            
        except Exception as e:
            print(f"Error analyzing structure: {e}")
            return self._fallback_analysis(source_code, file_path)
    
    def _fallback_analysis(self, source_code: str, file_path: str) -> Dict[str, Any]:
        """Fallback analysis when tree-sitter is not available"""
        lines = source_code.splitlines()
        
        # Simple regex-based analysis
        functions = []
        classes = []
        imports = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Find function definitions
            if stripped.startswith('def '):
                match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', stripped)
                if match:
                    functions.append({
                        'name': match.group(1),
                        'parameters': match.group(2),
                        'line': i + 1,
                        'text': line
                    })
            
            # Find class definitions
            elif stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)(?:\([^)]*\))?:', stripped)
                if match:
                    classes.append({
                        'name': match.group(1),
                        'line': i + 1,
                        'text': line
                    })
            
            # Find imports
            elif stripped.startswith(('import ', 'from ')):
                imports.append({
                    'text': stripped,
                    'line': i + 1
                })
        
        return {
            'file_path': file_path,
            'language': self.language,
            'tree_depth': 0,
            'node_count': len(lines),
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'variables': [],
            'fallback_mode': True
        }
    
    def _extract_functions(self, node: Node, source_code: str) -> List[Dict[str, Any]]:
        """Extract function definitions from syntax tree"""
        functions = []
        
        def visit_node(n):
            if n.type == 'function_definition':
                name_node = n.child_by_field_name('name')
                params_node = n.child_by_field_name('parameters')
                
                if name_node:
                    functions.append({
                        'name': self._get_node_text(name_node, source_code),
                        'parameters': self._get_node_text(params_node, source_code) if params_node else '',
                        'start_line': n.start_point[0] + 1,
                        'end_line': n.end_point[0] + 1,
                        'text': self._get_node_text(n, source_code)
                    })
            
            for child in n.children:
                visit_node(child)
        
        visit_node(node)
        return functions
    
    def _extract_classes(self, node: Node, source_code: str) -> List[Dict[str, Any]]:
        """Extract class definitions from syntax tree"""
        classes = []
        
        def visit_node(n):
            if n.type == 'class_definition':
                name_node = n.child_by_field_name('name')
                
                if name_node:
                    classes.append({
                        'name': self._get_node_text(name_node, source_code),
                        'start_line': n.start_point[0] + 1,
                        'end_line': n.end_point[0] + 1,
                        'text': self._get_node_text(n, source_code)
                    })
            
            for child in n.children:
                visit_node(child)
        
        visit_node(node)
        return classes
    
    def _extract_imports(self, node: Node, source_code: str) -> List[Dict[str, Any]]:
        """Extract import statements from syntax tree"""
        imports = []
        
        def visit_node(n):
            if n.type in ['import_statement', 'import_from_statement']:
                imports.append({
                    'type': n.type,
                    'text': self._get_node_text(n, source_code),
                    'line': n.start_point[0] + 1
                })
            
            for child in n.children:
                visit_node(child)
        
        visit_node(node)
        return imports
    
    def _extract_variables(self, node: Node, source_code: str) -> List[Dict[str, Any]]:
        """Extract variable assignments from syntax tree"""
        variables = []
        
        def visit_node(n):
            if n.type == 'assignment':
                left_node = n.child_by_field_name('left')
                right_node = n.child_by_field_name('right')
                
                if left_node:
                    variables.append({
                        'name': self._get_node_text(left_node, source_code),
                        'value': self._get_node_text(right_node, source_code) if right_node else '',
                        'line': n.start_point[0] + 1,
                        'text': self._get_node_text(n, source_code)
                    })
            
            for child in n.children:
                visit_node(child)
        
        visit_node(node)
        return variables
    
    def _get_node_text(self, node: Node, source_code: str) -> str:
        """Get text content of a node"""
        if not node:
            return ""
        
        start_byte = node.start_byte
        end_byte = node.end_byte
        return source_code[start_byte:end_byte]
    
    def _calculate_tree_depth(self, node: Node) -> int:
        """Calculate maximum depth of syntax tree"""
        if not node.children:
            return 1
        
        return 1 + max(self._calculate_tree_depth(child) for child in node.children)
    
    def _count_nodes(self, node: Node) -> int:
        """Count total number of nodes in syntax tree"""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def _convert_to_dict(self, node: Node, source_code: str, max_depth: int = 3) -> Dict[str, Any]:
        """Convert syntax tree node to dictionary representation"""
        if max_depth <= 0:
            return {'type': node.type, 'text': '...truncated...'}
        
        return {
            'type': node.type,
            'text': self._get_node_text(node, source_code)[:100] + ('...' if len(self._get_node_text(node, source_code)) > 100 else ''),
            'start_point': node.start_point,
            'end_point': node.end_point,
            'children': [
                self._convert_to_dict(child, source_code, max_depth - 1)
                for child in node.children[:10]  # Limit children to prevent huge output
            ]
        }


class QueryPatternEngine:
    """
    Engine for executing tree-sitter query patterns
    """
    
    def __init__(self, analyzer: TreeSitterAnalyzer):
        self.analyzer = analyzer
        self.predefined_patterns = self._load_predefined_patterns()
    
    def _load_predefined_patterns(self) -> Dict[str, str]:
        """Load predefined query patterns for common code analysis tasks"""
        return {
            'function_definitions': '''
                (function_definition
                  name: (identifier) @function.name
                  parameters: (parameters) @function.params
                  body: (block) @function.body)
            ''',
            
            'class_definitions': '''
                (class_definition
                  name: (identifier) @class.name
                  superclasses: (argument_list)? @class.superclasses
                  body: (block) @class.body)
            ''',
            
            'function_calls': '''
                (call
                  function: (identifier) @call.function
                  arguments: (argument_list) @call.arguments)
            ''',
            
            'variable_assignments': '''
                (assignment
                  left: (identifier) @var.name
                  right: (_) @var.value)
            ''',
            
            'import_statements': '''
                (import_statement
                  name: (dotted_name) @import.name)
            ''',
            
            'conditional_statements': '''
                (if_statement
                  condition: (_) @if.condition
                  consequence: (block) @if.body
                  alternative: (_)? @if.else)
            ''',
            
            'loop_statements': '''
                [(for_statement) (while_statement)] @loop
            ''',
            
            'try_except_blocks': '''
                (try_statement
                  body: (block) @try.body
                  handlers: (except_clause)* @try.handlers)
            ''',
            
            'decorators': '''
                (decorated_definition
                  decorator: (decorator) @decorator
                  definition: (_) @decorated.definition)
            ''',
            
            'string_literals': '''
                (string) @string.literal
            ''',
            
            'complex_expressions': '''
                (binary_operator
                  left: (_) @expr.left
                  operator: (_) @expr.operator
                  right: (_) @expr.right)
            ''',
            
            'nested_functions': '''
                (function_definition
                  body: (block
                    (function_definition) @nested.function))
            '''
        }
    
    def execute_pattern(self, pattern: str, source_code: str, file_path: str = "") -> QueryResult:
        """Execute a tree-sitter query pattern"""
        tree = self.analyzer.parse_code(source_code)
        if not tree:
            return QueryResult(pattern=pattern, file_path=file_path)
        
        try:
            # This would use actual tree-sitter query execution in a real implementation
            # For now, we'll simulate pattern matching
            matches = self._simulate_pattern_matching(pattern, source_code)
            
            return QueryResult(
                pattern=pattern,
                matches=matches,
                file_path=file_path,
                language=self.analyzer.language,
                total_matches=len(matches)
            )
            
        except Exception as e:
            print(f"Error executing pattern: {e}")
            return QueryResult(pattern=pattern, file_path=file_path)
    
    def execute_predefined_pattern(self, pattern_name: str, source_code: str, file_path: str = "") -> QueryResult:
        """Execute a predefined query pattern"""
        if pattern_name not in self.predefined_patterns:
            raise ValueError(f"Unknown predefined pattern: {pattern_name}")
        
        pattern = self.predefined_patterns[pattern_name]
        return self.execute_pattern(pattern, source_code, file_path)
    
    def _simulate_pattern_matching(self, pattern: str, source_code: str) -> List[Dict[str, Any]]:
        """Simulate pattern matching (fallback when tree-sitter queries aren't available)"""
        matches = []
        lines = source_code.splitlines()
        
        # Simple pattern matching based on pattern content
        if 'function_definition' in pattern:
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    matches.append({
                        'type': 'function_definition',
                        'line': i + 1,
                        'text': line.strip(),
                        'captures': {'function.name': self._extract_function_name(line)}
                    })
        
        elif 'class_definition' in pattern:
            for i, line in enumerate(lines):
                if line.strip().startswith('class '):
                    matches.append({
                        'type': 'class_definition',
                        'line': i + 1,
                        'text': line.strip(),
                        'captures': {'class.name': self._extract_class_name(line)}
                    })
        
        elif 'import_statement' in pattern:
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    matches.append({
                        'type': 'import_statement',
                        'line': i + 1,
                        'text': line.strip()
                    })
        
        return matches
    
    def _extract_function_name(self, line: str) -> str:
        """Extract function name from def line"""
        match = re.search(r'def\s+(\w+)', line)
        return match.group(1) if match else ""
    
    def _extract_class_name(self, line: str) -> str:
        """Extract class name from class line"""
        match = re.search(r'class\s+(\w+)', line)
        return match.group(1) if match else ""


class SyntaxTreeVisualizer:
    """
    Visualizer for syntax trees and code structure
    """
    
    def __init__(self, analyzer: TreeSitterAnalyzer):
        self.analyzer = analyzer
    
    def visualize_tree(self, source_code: str, output_format: str = "text") -> str:
        """Visualize syntax tree in various formats"""
        tree = self.analyzer.parse_code(source_code)
        if not tree:
            return self._fallback_visualization(source_code, output_format)
        
        if output_format == "text":
            return self._tree_to_text(tree.root_node, source_code)
        elif output_format == "json":
            return json.dumps(self.analyzer._convert_to_dict(tree.root_node, source_code), indent=2)
        elif output_format == "dot":
            return self._tree_to_dot(tree.root_node, source_code)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _tree_to_text(self, node: Node, source_code: str, indent: int = 0) -> str:
        """Convert syntax tree to text representation"""
        result = "  " * indent + f"{node.type}"
        
        if node.type in ['identifier', 'string', 'number']:
            text = self.analyzer._get_node_text(node, source_code)
            if text:
                result += f": {text[:50]}"
        
        result += "\n"
        
        for child in node.children[:10]:  # Limit children to prevent huge output
            result += self._tree_to_text(child, source_code, indent + 1)
        
        if len(node.children) > 10:
            result += "  " * (indent + 1) + "... (truncated)\n"
        
        return result
    
    def _tree_to_dot(self, node: Node, source_code: str) -> str:
        """Convert syntax tree to DOT format for Graphviz"""
        dot_lines = ["digraph SyntaxTree {"]
        node_id = 0
        
        def add_node(n, parent_id=None):
            nonlocal node_id
            current_id = node_id
            node_id += 1
            
            label = n.type
            if n.type in ['identifier', 'string', 'number']:
                text = self.analyzer._get_node_text(n, source_code)
                if text:
                    label += f"\\n{text[:20]}"
            
            dot_lines.append(f'  {current_id} [label="{label}"];')
            
            if parent_id is not None:
                dot_lines.append(f'  {parent_id} -> {current_id};')
            
            for child in n.children[:10]:  # Limit children
                add_node(child, current_id)
        
        add_node(node)
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def _fallback_visualization(self, source_code: str, output_format: str) -> str:
        """Fallback visualization when tree-sitter is not available"""
        lines = source_code.splitlines()
        
        if output_format == "text":
            result = "Code Structure (Fallback Mode):\n"
            for i, line in enumerate(lines[:20]):  # Show first 20 lines
                result += f"{i+1:3d}: {line}\n"
            if len(lines) > 20:
                result += "... (truncated)\n"
            return result
        
        elif output_format == "json":
            return json.dumps({
                "type": "module",
                "lines": len(lines),
                "fallback_mode": True,
                "preview": lines[:10]
            }, indent=2)
        
        else:
            return "Fallback visualization not available for this format"


class PatternBasedSearcher:
    """
    Pattern-based code search using tree-sitter queries
    """
    
    def __init__(self, analyzer: TreeSitterAnalyzer):
        self.analyzer = analyzer
        self.query_engine = QueryPatternEngine(analyzer)
    
    def search_patterns(self, directory_path: str, patterns: List[str]) -> Dict[str, List[PatternMatch]]:
        """Search for patterns across multiple files"""
        results = defaultdict(list)
        directory = Path(directory_path)
        
        # Find all Python files
        for py_file in directory.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                for pattern in patterns:
                    matches = self._search_pattern_in_code(pattern, source_code, str(py_file))
                    results[pattern].extend(matches)
                    
            except Exception as e:
                print(f"Error searching in {py_file}: {e}")
        
        return dict(results)
    
    def search_semantic_patterns(self, directory_path: str, semantic_queries: List[str]) -> Dict[str, Any]:
        """Search for semantic patterns (high-level code constructs)"""
        results = {}
        
        semantic_patterns = {
            'error_handling': ['try_except_blocks'],
            'async_functions': ['function_definitions'],  # Would filter for async
            'decorators': ['decorators'],
            'complex_conditions': ['conditional_statements'],
            'nested_loops': ['loop_statements'],
            'long_functions': ['function_definitions'],  # Would filter by length
        }
        
        for query in semantic_queries:
            if query in semantic_patterns:
                patterns = semantic_patterns[query]
                query_results = []
                
                for pattern in patterns:
                    pattern_results = self.search_patterns(directory_path, [pattern])
                    query_results.extend(pattern_results.get(pattern, []))
                
                results[query] = query_results
        
        return results
    
    def _search_pattern_in_code(self, pattern: str, source_code: str, file_path: str) -> List[PatternMatch]:
        """Search for a pattern in source code"""
        matches = []
        
        # Use query engine to find matches
        query_result = self.query_engine.execute_pattern(pattern, source_code, file_path)
        
        for match in query_result.matches:
            pattern_match = PatternMatch(
                pattern=pattern,
                node_type=match.get('type', ''),
                text=match.get('text', ''),
                start_line=match.get('line', 0),
                end_line=match.get('line', 0),
                start_column=0,
                end_column=0,
                file_path=file_path
            )
            matches.append(pattern_match)
        
        return matches


# Convenience functions for direct use

def execute_query_patterns(source_code: str, patterns: List[str], language: str = "python") -> Dict[str, QueryResult]:
    """Execute multiple query patterns on source code"""
    analyzer = TreeSitterAnalyzer(language)
    query_engine = QueryPatternEngine(analyzer)
    
    results = {}
    for pattern in patterns:
        results[pattern] = query_engine.execute_pattern(pattern, source_code)
    
    return results


def visualize_syntax_tree(source_code: str, output_format: str = "text", language: str = "python") -> str:
    """Visualize syntax tree for source code"""
    analyzer = TreeSitterAnalyzer(language)
    visualizer = SyntaxTreeVisualizer(analyzer)
    
    return visualizer.visualize_tree(source_code, output_format)


def search_code_patterns(directory_path: str, patterns: List[str], language: str = "python") -> Dict[str, List[PatternMatch]]:
    """Search for code patterns in a directory"""
    analyzer = TreeSitterAnalyzer(language)
    searcher = PatternBasedSearcher(analyzer)
    
    return searcher.search_patterns(directory_path, patterns)

