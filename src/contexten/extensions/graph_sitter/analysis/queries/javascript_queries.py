"""
JavaScript/TypeScript-specific Tree-sitter Query Patterns

Official tree-sitter query patterns for JavaScript and TypeScript code analysis.
"""

from typing import Dict, List
from ..core.tree_sitter_core import TreeSitterCore, QueryMatch


class JavaScriptQueries:
    """JavaScript/TypeScript-specific query patterns using official tree-sitter syntax."""
    
    # Function definition queries
    FUNCTION_DEFINITIONS = """
    [
      (function_declaration
        name: (identifier) @function.name
        parameters: (formal_parameters) @function.params
        body: (statement_block) @function.body) @function.def
      (arrow_function
        parameters: (formal_parameters) @function.params
        body: (_) @function.body) @function.arrow
      (method_definition
        name: (property_identifier) @method.name
        parameters: (formal_parameters) @method.params
        body: (statement_block) @method.body) @method.def
    ]
    """
    
    # Class definition queries
    CLASS_DEFINITIONS = """
    (class_declaration
      name: (identifier) @class.name
      superclass: (identifier)? @class.super
      body: (class_body) @class.body) @class.def
    """
    
    # Variable declarations
    VARIABLE_DECLARATIONS = """
    [
      (variable_declaration
        (variable_declarator
          name: (identifier) @var.name
          value: (_)? @var.value) @var.declarator) @var.declaration
      (lexical_declaration
        (variable_declarator
          name: (identifier) @var.name
          value: (_)? @var.value) @var.declarator) @var.lexical
    ]
    """
    
    # Import/Export statements
    IMPORT_EXPORT = """
    [
      (import_statement
        source: (string) @import.source) @import.stmt
      (export_statement
        declaration: (_) @export.declaration) @export.stmt
      (import_clause
        (identifier) @import.default) @import.default_clause
      (named_imports
        (import_specifier
          name: (identifier) @import.named) @import.specifier) @import.named_clause
    ]
    """
    
    # Function calls
    FUNCTION_CALLS = """
    (call_expression
      function: (_) @call.function
      arguments: (arguments) @call.args) @call.expr
    """
    
    # Control flow statements
    CONTROL_FLOW = """
    [
      (if_statement
        condition: (parenthesized_expression) @if.condition
        consequence: (_) @if.body
        alternative: (_)? @if.else) @if.stmt
      (for_statement
        initializer: (_)? @for.init
        condition: (_)? @for.condition
        increment: (_)? @for.increment
        body: (_) @for.body) @for.stmt
      (for_in_statement
        left: (_) @for_in.var
        right: (_) @for_in.object
        body: (_) @for_in.body) @for_in.stmt
      (while_statement
        condition: (parenthesized_expression) @while.condition
        body: (_) @while.body) @while.stmt
      (try_statement
        body: (statement_block) @try.body
        handler: (catch_clause
          parameter: (identifier)? @catch.param
          body: (statement_block) @catch.body)? @catch.clause
        finalizer: (finally_clause
          body: (statement_block) @finally.body)? @finally.clause) @try.stmt
    ]
    """
    
    # Object and array patterns
    OBJECT_ARRAY_PATTERNS = """
    [
      (object_expression
        (pair
          key: (_) @object.key
          value: (_) @object.value) @object.pair) @object.expr
      (array_expression
        (_) @array.element) @array.expr
    ]
    """
    
    # Async/await patterns
    ASYNC_PATTERNS = """
    [
      (function_declaration
        (async) @async.keyword
        name: (identifier) @async.function.name) @async.function
      (arrow_function
        (async) @async.keyword) @async.arrow
      (await_expression
        (_) @await.expr) @await.stmt
    ]
    """
    
    # Complexity patterns
    COMPLEXITY_PATTERNS = """
    [
      (if_statement) @complexity.if
      (for_statement) @complexity.for
      (for_in_statement) @complexity.for_in
      (while_statement) @complexity.while
      (do_statement) @complexity.do_while
      (switch_statement) @complexity.switch
      (case_clause) @complexity.case
      (try_statement) @complexity.try
      (catch_clause) @complexity.catch
      (conditional_expression) @complexity.ternary
      (binary_expression
        operator: ["&&" "||"] @complexity.logical_op)
    ]
    """
    
    # Error patterns and code smells
    ERROR_PATTERNS = """
    [
      ; Empty catch blocks
      (try_statement
        handler: (catch_clause
          body: (statement_block) @error.empty_catch))
      
      ; Console.log statements (potential debugging code)
      (call_expression
        function: (member_expression
          object: (identifier) @console
          property: (property_identifier) @log)
        (#eq? @console "console")
        (#eq? @log "log")) @error.console_log
      
      ; Eval usage (security risk)
      (call_expression
        function: (identifier) @eval
        (#eq? @eval "eval")) @error.eval_usage
      
      ; Long parameter lists
      (formal_parameters
        (identifier) (identifier) (identifier) (identifier) (identifier) (identifier)+) @error.long_params
    ]
    """
    
    def __init__(self, core: TreeSitterCore):
        """Initialize JavaScript queries with tree-sitter core."""
        self.core = core
        self.language = 'javascript'  # Also works for TypeScript
        self._compiled_queries = {}
        self._compile_queries()
    
    def _compile_queries(self):
        """Compile all query patterns."""
        queries = {
            'functions': self.FUNCTION_DEFINITIONS,
            'classes': self.CLASS_DEFINITIONS,
            'variables': self.VARIABLE_DECLARATIONS,
            'imports': self.IMPORT_EXPORT,
            'calls': self.FUNCTION_CALLS,
            'control_flow': self.CONTROL_FLOW,
            'objects': self.OBJECT_ARRAY_PATTERNS,
            'async': self.ASYNC_PATTERNS,
            'complexity': self.COMPLEXITY_PATTERNS,
            'errors': self.ERROR_PATTERNS,
        }
        
        for name, pattern in queries.items():
            query = self.core.create_query(self.language, pattern, f"js_{name}")
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
    
    def find_async_patterns(self, parse_result) -> List[QueryMatch]:
        """Find async/await patterns."""
        if 'async' not in self._compiled_queries:
            return []
        
        return self.core.execute_query(
            self._compiled_queries['async'],
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

