"""
Graph Builder: Constructs dependency graphs and symbol relationships

This module handles:
- Symbol extraction from source code
- Dependency relationship mapping
- Graph construction and analysis
- Cross-file reference resolution
"""

import ast
import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import networkx as nx

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("Tree-sitter not available, falling back to AST parsing")


@dataclass
class Symbol:
    """Represents a code symbol (function, class, variable, etc.)"""
    name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    visibility: str = 'public'
    is_exported: bool = False
    is_deprecated: bool = False
    complexity_score: int = 0
    parameter_count: int = 0
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    annotations: Dict[str, Any] = None
    decorators: List[str] = None
    modifiers: List[str] = None


@dataclass
class Dependency:
    """Represents a dependency relationship between files or symbols"""
    source_file: str
    target_file: str
    source_symbol: Optional[str] = None
    target_symbol: Optional[str] = None
    dependency_type: str = 'import'
    import_statement: Optional[str] = None
    line_number: int = 0
    is_external: bool = False
    is_circular: bool = False


class GraphBuilder:
    """
    Builds dependency graphs and extracts symbols from source code
    """
    
    def __init__(self, config):
        """
        Initialize the graph builder
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.dependency_graph = nx.DiGraph()
        self.symbol_graph = nx.DiGraph()
        
        # Language-specific parsers
        self.parsers = {}
        if TREE_SITTER_AVAILABLE:
            self._initialize_tree_sitter_parsers()
    
    def _initialize_tree_sitter_parsers(self):
        """Initialize Tree-sitter parsers for supported languages"""
        # This would initialize actual Tree-sitter parsers
        # For now, we'll use a placeholder implementation
        pass
    
    def extract_symbols(self, file_path: str, content: str, language: str) -> List[Dict[str, Any]]:
        """
        Extract symbols from source code
        
        Args:
            file_path: Path to the source file
            content: File content
            language: Programming language
            
        Returns:
            List of symbol dictionaries
        """
        self.logger.debug(f"Extracting symbols from {file_path} ({language})")
        
        try:
            if language == 'python':
                return self._extract_python_symbols(file_path, content)
            elif language in ['typescript', 'javascript']:
                return self._extract_js_ts_symbols(file_path, content)
            elif language == 'java':
                return self._extract_java_symbols(file_path, content)
            else:
                return self._extract_generic_symbols(file_path, content, language)
        except Exception as e:
            self.logger.error(f"Symbol extraction failed for {file_path}: {str(e)}")
            return []
    
    def _extract_python_symbols(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract symbols from Python code using AST"""
        symbols = []
        
        try:
            tree = ast.parse(content)
            
            class SymbolVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.symbols = []
                    self.current_class = None
                    self.current_function = None
                
                def visit_ClassDef(self, node):
                    symbol = {
                        'name': node.name,
                        'symbol_type': 'class',
                        'file_path': file_path,
                        'start_line': node.lineno,
                        'end_line': getattr(node, 'end_lineno', node.lineno),
                        'start_column': node.col_offset,
                        'end_column': getattr(node, 'end_col_offset', 0),
                        'docstring': ast.get_docstring(node),
                        'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                        'is_exported': not node.name.startswith('_'),
                        'visibility': 'private' if node.name.startswith('_') else 'public'
                    }
                    
                    # Calculate inheritance depth
                    symbol['base_classes'] = [self._get_name(base) for base in node.bases]
                    
                    self.symbols.append(symbol)
                    
                    old_class = self.current_class
                    self.current_class = node.name
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    symbol_type = 'method' if self.current_class else 'function'
                    
                    symbol = {
                        'name': node.name,
                        'symbol_type': symbol_type,
                        'file_path': file_path,
                        'start_line': node.lineno,
                        'end_line': getattr(node, 'end_lineno', node.lineno),
                        'start_column': node.col_offset,
                        'end_column': getattr(node, 'end_col_offset', 0),
                        'docstring': ast.get_docstring(node),
                        'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                        'parameter_count': len(node.args.args),
                        'is_async': isinstance(node, ast.AsyncFunctionDef),
                        'is_exported': not node.name.startswith('_'),
                        'visibility': 'private' if node.name.startswith('_') else 'public',
                        'complexity_score': self._calculate_complexity(node)
                    }
                    
                    # Extract return type annotation
                    if node.returns:
                        symbol['return_type'] = self._get_annotation(node.returns)
                    
                    # Extract parameter information
                    symbol['parameters'] = self._extract_parameters(node.args)
                    
                    if self.current_class:
                        symbol['class_name'] = self.current_class
                    
                    self.symbols.append(symbol)
                    
                    old_function = self.current_function
                    self.current_function = node.name
                    self.generic_visit(node)
                    self.current_function = old_function
                
                def visit_Assign(self, node):
                    # Extract variable assignments
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbol = {
                                'name': target.id,
                                'symbol_type': 'variable',
                                'file_path': file_path,
                                'start_line': node.lineno,
                                'end_line': node.lineno,
                                'start_column': node.col_offset,
                                'end_column': getattr(node, 'end_col_offset', 0),
                                'is_exported': not target.id.startswith('_'),
                                'visibility': 'private' if target.id.startswith('_') else 'public'
                            }
                            
                            if self.current_class:
                                symbol['class_name'] = self.current_class
                            if self.current_function:
                                symbol['function_name'] = self.current_function
                            
                            self.symbols.append(symbol)
                    
                    self.generic_visit(node)
                
                def _get_decorator_name(self, decorator):
                    if isinstance(decorator, ast.Name):
                        return decorator.id
                    elif isinstance(decorator, ast.Attribute):
                        return f"{self._get_name(decorator.value)}.{decorator.attr}"
                    return str(decorator)
                
                def _get_name(self, node):
                    if isinstance(node, ast.Name):
                        return node.id
                    elif isinstance(node, ast.Attribute):
                        return f"{self._get_name(node.value)}.{node.attr}"
                    return str(node)
                
                def _get_annotation(self, annotation):
                    if isinstance(annotation, ast.Name):
                        return annotation.id
                    elif isinstance(annotation, ast.Attribute):
                        return f"{self._get_name(annotation.value)}.{annotation.attr}"
                    return str(annotation)
                
                def _extract_parameters(self, args):
                    params = []
                    for arg in args.args:
                        param = {'name': arg.arg}
                        if arg.annotation:
                            param['type'] = self._get_annotation(arg.annotation)
                        params.append(param)
                    return params
                
                def _calculate_complexity(self, node):
                    """Calculate cyclomatic complexity"""
                    complexity = 1  # Base complexity
                    
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                            complexity += 1
                        elif isinstance(child, ast.ExceptHandler):
                            complexity += 1
                        elif isinstance(child, (ast.And, ast.Or)):
                            complexity += 1
                    
                    return complexity
            
            visitor = SymbolVisitor()
            visitor.visit(tree)
            symbols = visitor.symbols
            
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error parsing Python file {file_path}: {str(e)}")
        
        return symbols
    
    def _extract_js_ts_symbols(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract symbols from JavaScript/TypeScript code"""
        symbols = []
        
        # Simple regex-based extraction for now
        # In a real implementation, this would use Tree-sitter or a proper JS/TS parser
        
        # Function declarations
        function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            symbols.append({
                'name': match.group(1),
                'symbol_type': 'function',
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num,
                'is_exported': 'export' in match.group(0),
                'is_async': 'async' in match.group(0)
            })
        
        # Class declarations
        class_pattern = r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            symbol = {
                'name': match.group(1),
                'symbol_type': 'class',
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num,
                'is_exported': 'export' in match.group(0)
            }
            if match.group(2):
                symbol['base_classes'] = [match.group(2)]
            symbols.append(symbol)
        
        # Variable declarations
        var_pattern = r'(?:export\s+)?(?:const|let|var)\s+(\w+)'
        for match in re.finditer(var_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            symbols.append({
                'name': match.group(1),
                'symbol_type': 'variable',
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num,
                'is_exported': 'export' in match.group(0)
            })
        
        return symbols
    
    def _extract_java_symbols(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract symbols from Java code"""
        symbols = []
        
        # Class declarations
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            symbol = {
                'name': match.group(1),
                'symbol_type': 'class',
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num,
                'visibility': self._extract_java_visibility(match.group(0))
            }
            if match.group(2):
                symbol['base_classes'] = [match.group(2)]
            symbols.append(symbol)
        
        # Method declarations
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)'
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            symbols.append({
                'name': match.group(1),
                'symbol_type': 'method',
                'file_path': file_path,
                'start_line': line_num,
                'end_line': line_num,
                'visibility': self._extract_java_visibility(match.group(0)),
                'is_static': 'static' in match.group(0)
            })
        
        return symbols
    
    def _extract_generic_symbols(self, file_path: str, content: str, language: str) -> List[Dict[str, Any]]:
        """Generic symbol extraction for unsupported languages"""
        symbols = []
        
        # Very basic pattern matching for function-like constructs
        patterns = {
            'function': r'(?:function|def|fn)\s+(\w+)',
            'class': r'(?:class|struct|interface)\s+(\w+)',
            'variable': r'(?:var|let|const|int|string|bool)\s+(\w+)'
        }
        
        for symbol_type, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                symbols.append({
                    'name': match.group(1),
                    'symbol_type': symbol_type,
                    'file_path': file_path,
                    'start_line': line_num,
                    'end_line': line_num,
                    'language': language
                })
        
        return symbols
    
    def _extract_java_visibility(self, declaration: str) -> str:
        """Extract visibility modifier from Java declaration"""
        if 'private' in declaration:
            return 'private'
        elif 'protected' in declaration:
            return 'protected'
        elif 'public' in declaration:
            return 'public'
        else:
            return 'package'
    
    def extract_dependencies(self, file_path: str, content: str, language: str, symbols: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract dependencies from source code
        
        Args:
            file_path: Path to the source file
            content: File content
            language: Programming language
            symbols: Previously extracted symbols
            
        Returns:
            List of dependency dictionaries
        """
        self.logger.debug(f"Extracting dependencies from {file_path} ({language})")
        
        try:
            if language == 'python':
                return self._extract_python_dependencies(file_path, content)
            elif language in ['typescript', 'javascript']:
                return self._extract_js_ts_dependencies(file_path, content)
            elif language == 'java':
                return self._extract_java_dependencies(file_path, content)
            else:
                return self._extract_generic_dependencies(file_path, content, language)
        except Exception as e:
            self.logger.error(f"Dependency extraction failed for {file_path}: {str(e)}")
            return []
    
    def _extract_python_dependencies(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract dependencies from Python code"""
        dependencies = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append({
                            'source_file': file_path,
                            'target_module': alias.name,
                            'dependency_type': 'import',
                            'import_statement': f"import {alias.name}",
                            'line_number': node.lineno,
                            'is_external': not self._is_local_module(alias.name, file_path)
                        })
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        dependencies.append({
                            'source_file': file_path,
                            'target_module': module,
                            'imported_name': alias.name,
                            'dependency_type': 'from_import',
                            'import_statement': f"from {module} import {alias.name}",
                            'line_number': node.lineno,
                            'is_external': not self._is_local_module(module, file_path),
                            'is_relative': node.level > 0
                        })
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error extracting Python dependencies from {file_path}: {str(e)}")
        
        return dependencies
    
    def _extract_js_ts_dependencies(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract dependencies from JavaScript/TypeScript code"""
        dependencies = []
        
        # ES6 imports
        import_pattern = r'import\s+(?:{[^}]+}|\w+|\*\s+as\s+\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            module_path = match.group(1)
            dependencies.append({
                'source_file': file_path,
                'target_module': module_path,
                'dependency_type': 'import',
                'import_statement': match.group(0),
                'line_number': line_num,
                'is_external': not module_path.startswith('.'),
                'is_relative': module_path.startswith('.')
            })
        
        # CommonJS requires
        require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.finditer(require_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            module_path = match.group(1)
            dependencies.append({
                'source_file': file_path,
                'target_module': module_path,
                'dependency_type': 'require',
                'import_statement': match.group(0),
                'line_number': line_num,
                'is_external': not module_path.startswith('.'),
                'is_relative': module_path.startswith('.')
            })
        
        return dependencies
    
    def _extract_java_dependencies(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract dependencies from Java code"""
        dependencies = []
        
        # Import statements
        import_pattern = r'import\s+(?:static\s+)?([^;]+);'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            imported_class = match.group(1).strip()
            dependencies.append({
                'source_file': file_path,
                'target_module': imported_class,
                'dependency_type': 'import',
                'import_statement': match.group(0),
                'line_number': line_num,
                'is_external': not imported_class.startswith('com.yourcompany'),  # Adjust as needed
                'is_static': 'static' in match.group(0)
            })
        
        return dependencies
    
    def _extract_generic_dependencies(self, file_path: str, content: str, language: str) -> List[Dict[str, Any]]:
        """Generic dependency extraction"""
        dependencies = []
        
        # Basic include/import patterns
        patterns = [
            r'#include\s*[<"]([^>"]+)[>"]',  # C/C++
            r'use\s+([^;]+);',  # Rust
            r'import\s+"([^"]+)"',  # Go
            r'require\s+[\'"]([^\'"]+)[\'"]'  # Various languages
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                dependencies.append({
                    'source_file': file_path,
                    'target_module': match.group(1),
                    'dependency_type': 'include',
                    'import_statement': match.group(0),
                    'line_number': line_num,
                    'language': language
                })
        
        return dependencies
    
    def _is_local_module(self, module_name: str, file_path: str) -> bool:
        """Check if a module is local to the project"""
        # Simple heuristic: if it starts with a dot or matches project structure
        if module_name.startswith('.'):
            return True
        
        # Check if module exists in project directory
        project_root = self._find_project_root(file_path)
        if project_root:
            module_path = Path(project_root) / module_name.replace('.', '/')
            return module_path.exists() or (module_path.with_suffix('.py')).exists()
        
        return False
    
    def _find_project_root(self, file_path: str) -> Optional[str]:
        """Find the project root directory"""
        path = Path(file_path).parent
        while path.parent != path:
            if (path / '.git').exists() or (path / 'setup.py').exists() or (path / 'pyproject.toml').exists():
                return str(path)
            path = path.parent
        return None
    
    def build_dependency_graph(self, file_results, repo_id: str, commit_id: str) -> int:
        """
        Build dependency graph from file analysis results
        
        Args:
            file_results: List of FileAnalysis objects
            repo_id: Repository identifier
            commit_id: Commit identifier
            
        Returns:
            Number of dependencies mapped
        """
        self.logger.info("Building dependency graph")
        
        # Clear existing graph
        self.dependency_graph.clear()
        
        dependency_count = 0
        
        # Add nodes for all files
        for file_result in file_results:
            self.dependency_graph.add_node(file_result.file_path, **{
                'language': file_result.language,
                'metrics': file_result.metrics,
                'symbol_count': len(file_result.symbols)
            })
        
        # Add dependency edges
        for file_result in file_results:
            for dep in file_result.dependencies:
                target_file = self._resolve_dependency_target(dep, file_result.file_path)
                if target_file and target_file in self.dependency_graph:
                    self.dependency_graph.add_edge(
                        file_result.file_path,
                        target_file,
                        **dep
                    )
                    dependency_count += 1
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        return dependency_count
    
    def _resolve_dependency_target(self, dependency: Dict, source_file: str) -> Optional[str]:
        """Resolve dependency target to actual file path"""
        target_module = dependency.get('target_module', '')
        
        if dependency.get('is_external', False):
            return None  # External dependencies not in our graph
        
        # Handle relative imports
        if dependency.get('is_relative', False):
            source_dir = Path(source_file).parent
            if target_module.startswith('.'):
                # Python relative import
                levels = len(target_module) - len(target_module.lstrip('.'))
                module_name = target_module.lstrip('.')
                target_dir = source_dir
                for _ in range(levels - 1):
                    target_dir = target_dir.parent
                target_path = target_dir / module_name.replace('.', '/') / '__init__.py'
                if target_path.exists():
                    return str(target_path)
                target_path = target_dir / f"{module_name.replace('.', '/')}.py"
                if target_path.exists():
                    return str(target_path)
            else:
                # JavaScript/TypeScript relative import
                target_path = source_dir / target_module
                if target_path.with_suffix('.js').exists():
                    return str(target_path.with_suffix('.js'))
                if target_path.with_suffix('.ts').exists():
                    return str(target_path.with_suffix('.ts'))
                if (target_path / 'index.js').exists():
                    return str(target_path / 'index.js')
                if (target_path / 'index.ts').exists():
                    return str(target_path / 'index.ts')
        
        return None
    
    def _detect_circular_dependencies(self):
        """Detect and mark circular dependencies"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            for cycle in cycles:
                for i in range(len(cycle)):
                    source = cycle[i]
                    target = cycle[(i + 1) % len(cycle)]
                    if self.dependency_graph.has_edge(source, target):
                        self.dependency_graph[source][target]['is_circular'] = True
                        self.logger.warning(f"Circular dependency detected: {' -> '.join(cycle)}")
        except Exception as e:
            self.logger.error(f"Error detecting circular dependencies: {str(e)}")
    
    def get_dependency_metrics(self) -> Dict[str, Any]:
        """Calculate dependency graph metrics"""
        if not self.dependency_graph.nodes():
            return {}
        
        return {
            'total_files': self.dependency_graph.number_of_nodes(),
            'total_dependencies': self.dependency_graph.number_of_edges(),
            'avg_dependencies_per_file': self.dependency_graph.number_of_edges() / self.dependency_graph.number_of_nodes(),
            'max_dependencies': max(dict(self.dependency_graph.out_degree()).values()) if self.dependency_graph.nodes() else 0,
            'circular_dependencies': sum(1 for _, _, data in self.dependency_graph.edges(data=True) if data.get('is_circular', False)),
            'strongly_connected_components': len(list(nx.strongly_connected_components(self.dependency_graph)))
        }

