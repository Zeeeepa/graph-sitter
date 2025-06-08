"""
Python-specific Tree-sitter Query Patterns

Official tree-sitter query patterns for Python code analysis.
Based on tree-sitter-python grammar and official query syntax.
"""

from typing import Dict, List
from ..core.tree_sitter_core import TreeSitterCore, QueryMatch


class PythonQueries:
    """Python-specific query patterns using official tree-sitter syntax."""
    
    # Function definition queries
    FUNCTION_DEFINITIONS = """
    (function_definition
      name: (identifier) @function.name
      parameters: (parameters) @function.params
      body: (block) @function.body) @function.def
    """
    
    # Class definition queries
    CLASS_DEFINITIONS = """
    (class_definition
      name: (identifier) @class.name
      superclasses: (argument_list)? @class.bases
      body: (block) @class.body) @class.def
    """
    
    # Method definition queries
    METHOD_DEFINITIONS = """
    (class_definition
      body: (block
        (function_definition
          name: (identifier) @method.name
          parameters: (parameters) @method.params
          body: (block) @method.body) @method.def))
    """
    
    # Import statements
    IMPORT_STATEMENTS = """
    [
      (import_statement
        name: (dotted_name) @import.module) @import.stmt
      (import_from_statement
        module_name: (dotted_name) @import.from_module
        name: (dotted_name) @import.name) @import.from_stmt
    ]
    """
    
    # Variable assignments
    VARIABLE_ASSIGNMENTS = """
    (assignment
      left: (identifier) @var.name
      right: (_) @var.value) @var.assignment
    """
    
    # Function calls
    FUNCTION_CALLS = """
    (call
      function: (identifier) @call.function
      arguments: (argument_list) @call.args) @call.expr
    """
    
    # Control flow statements
    CONTROL_FLOW = """
    [
      (if_statement
        condition: (_) @if.condition
        consequence: (block) @if.body
        alternative: (_)? @if.else) @if.stmt
      (for_statement
        left: (_) @for.var
        right: (_) @for.iter
        body: (block) @for.body) @for.stmt
      (while_statement
        condition: (_) @while.condition
        body: (block) @while.body) @while.stmt
      (try_statement
        body: (block) @try.body
        (except_clause
          type: (_)? @except.type
          name: (identifier)? @except.name
          body: (block) @except.body) @except.clause) @try.stmt
    ]
    """
    
    # Decorators
    DECORATORS = """
    (decorated_definition
      (decorator
        (identifier) @decorator.name) @decorator.def
      definition: (_) @decorator.target) @decorated.def
    """
    
    # String literals
    STRING_LITERALS = """
    (string) @string.literal
    """
    
    # Comments
    COMMENTS = """
    (comment) @comment
    """
    
    # Complex expressions for complexity analysis
    COMPLEXITY_PATTERNS = """
    [
      (if_statement) @complexity.if
      (for_statement) @complexity.for
      (while_statement) @complexity.while
      (try_statement) @complexity.try
      (except_clause) @complexity.except
      (boolean_operator) @complexity.bool_op
      (comparison_operator) @complexity.comparison
      (lambda) @complexity.lambda
      (list_comprehension) @complexity.list_comp
      (dictionary_comprehension) @complexity.dict_comp
      (set_comprehension) @complexity.set_comp
      (generator_expression) @complexity.gen_exp
    ]
    """
    
    # Error patterns and code smells
    ERROR_PATTERNS = """
    [
      ; Long parameter lists (>5 parameters)
      (function_definition
        parameters: (parameters
          (identifier) (identifier) (identifier) (identifier) (identifier) (identifier)+) @error.long_params)
      
      ; Nested functions (potential code smell)
      (function_definition
        body: (block
          (function_definition) @error.nested_function))
      
      ; Empty except clauses
      (try_statement
        (except_clause
          body: (block
            (pass_statement)) @error.empty_except))
      
      ; Bare except clauses
      (try_statement
        (except_clause
          !type) @error.bare_except)
    ]
    """
    
    def __init__(self, core: TreeSitterCore):
        """Initialize Python queries with tree-sitter core."""
        self.core = core
        self.language = 'python'
        self._compiled_queries = {}
        self._compile_queries()
    
    def _compile_queries(self):
        """Compile all query patterns."""
        queries = {
            'functions': self.FUNCTION_DEFINITIONS,
            'classes': self.CLASS_DEFINITIONS,
            'methods': self.METHOD_DEFINITIONS,
            'imports': self.IMPORT_STATEMENTS,
            'variables': self.VARIABLE_ASSIGNMENTS,
            'calls': self.FUNCTION_CALLS,
            'control_flow': self.CONTROL_FLOW,
            'decorators': self.DECORATORS,
            'strings': self.STRING_LITERALS,
            'comments': self.COMMENTS,
            'complexity': self.COMPLEXITY_PATTERNS,
            'errors': self.ERROR_PATTERNS,
        }
        
        for name, pattern in queries.items():
            query = self.core.create_query(self.language, pattern, f"python_{name}")
            if query:
                self._compiled_queries[name] = query
    
    def find_functions(self, parse_result) -> List[QueryMatch]:
        """Find all function definitions."""
        if 'functions' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['functions'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_classes(self, parse_result) -> List[QueryMatch]:
        """Find all class definitions."""
        if 'classes' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['classes'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_methods(self, parse_result) -> List[QueryMatch]:
        """Find all method definitions."""
        if 'methods' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['methods'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_imports(self, parse_result) -> List[QueryMatch]:
        """Find all import statements."""
        if 'imports' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['imports'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_control_flow(self, parse_result) -> List[QueryMatch]:
        """Find all control flow statements for complexity analysis."""
        if 'control_flow' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['control_flow'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_complexity_patterns(self, parse_result) -> List[QueryMatch]:
        """Find patterns that contribute to cyclomatic complexity."""
        if 'complexity' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['complexity'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def find_error_patterns(self, parse_result) -> List[QueryMatch]:
        """Find potential error patterns and code smells."""
        if 'errors' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['errors'],
            parse_result.tree,
            parse_result.source_code,
            parse_result.file_path
        )
    
    def analyze_function_complexity(self, function_node, source_code: bytes) -> Dict[str, int]:
        """
        Analyze complexity of a specific function using tree-sitter.
        
        Args:
            function_node: Function node from tree-sitter
            source_code: Original source code
            
        Returns:
            Dictionary with complexity metrics
        """
        # Create a temporary query for this function's body
        complexity_query = """
        [
          (if_statement) @complexity
          (for_statement) @complexity
          (while_statement) @complexity
          (try_statement) @complexity
          (except_clause) @complexity
          (boolean_operator) @complexity
          (lambda) @complexity
          (list_comprehension) @complexity
          (dictionary_comprehension) @complexity
          (set_comprehension) @complexity
          (generator_expression) @complexity
        ]
        """
        
        query = self.core.create_query(self.language, complexity_query)
        if not query:
            return {'cyclomatic_complexity': 1}
        
        # Count complexity patterns within the function
        complexity_count = 0
        
        def count_in_node(node):
            nonlocal complexity_count
            for match in query.matches(node):
                complexity_count += 1
        
        # Get function body
        body_node = function_node.child_by_field_name('body')
        if body_node:
            count_in_node(body_node)
        
        return {
            'cyclomatic_complexity': max(1, complexity_count + 1),  # Base complexity is 1
            'complexity_patterns': complexity_count
        }

