"""
Self-Analysis Extension for Graph-Sitter

This module enables the codebase to analyze itself and provide insights
about its own structure, issues, and potential improvements.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """Result of a self-analysis operation."""
    category: str
    severity: str  # 'info', 'warning', 'error'
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class CodebaseAnalyzer:
    """Analyzes the codebase for various issues and patterns."""
    
    def __init__(self, codebase):
        self.codebase = codebase
        self.results: List[AnalysisResult] = []
    
    def analyze_all(self) -> List[AnalysisResult]:
        """Run all analysis checks."""
        self.results.clear()
        
        # Run different analysis categories
        self._analyze_code_quality()
        self._analyze_architecture()
        self._analyze_dependencies()
        self._analyze_test_coverage()
        self._analyze_documentation()
        self._analyze_performance_patterns()
        self._analyze_security_patterns()
        
        return self.results
    
    def _analyze_code_quality(self) -> None:
        """Analyze code quality issues."""
        logger.info("Analyzing code quality...")
        
        # Check for common code smells
        self._check_function_complexity()
        self._check_duplicate_code()
        self._check_naming_conventions()
        self._check_import_organization()
    
    def _check_function_complexity(self) -> None:
        """Check for overly complex functions."""
        complex_functions = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_cyclomatic_complexity(node)
                        if complexity > 10:  # Threshold for high complexity
                            complex_functions.append({
                                'file': str(file.path),
                                'function': node.name,
                                'line': node.lineno,
                                'complexity': complexity
                            })
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        if complex_functions:
            for func in complex_functions:
                self.results.append(AnalysisResult(
                    category="Code Quality",
                    severity="warning",
                    message=f"Function '{func['function']}' has high cyclomatic complexity ({func['complexity']})",
                    file_path=func['file'],
                    line_number=func['line'],
                    suggestions=[
                        "Consider breaking this function into smaller functions",
                        "Extract complex logic into separate methods",
                        "Use early returns to reduce nesting"
                    ]
                ))
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_duplicate_code(self) -> None:
        """Check for potential code duplication."""
        # Simple duplicate detection based on similar function signatures
        function_signatures = defaultdict(list)
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Create a simple signature
                        args = [arg.arg for arg in node.args.args]
                        signature = f"{node.name}({', '.join(args)})"
                        function_signatures[signature].append({
                            'file': str(file.path),
                            'line': node.lineno
                        })
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        # Report potential duplicates
        for signature, locations in function_signatures.items():
            if len(locations) > 1:
                self.results.append(AnalysisResult(
                    category="Code Quality",
                    severity="info",
                    message=f"Potential duplicate function signature: {signature}",
                    suggestions=[
                        "Review these functions for potential consolidation",
                        "Consider extracting common logic to a shared utility"
                    ]
                ))
    
    def _check_naming_conventions(self) -> None:
        """Check naming conventions."""
        naming_issues = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                            naming_issues.append({
                                'file': str(file.path),
                                'line': node.lineno,
                                'type': 'function',
                                'name': node.name
                            })
                    elif isinstance(node, ast.ClassDef):
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            naming_issues.append({
                                'file': str(file.path),
                                'line': node.lineno,
                                'type': 'class',
                                'name': node.name
                            })
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        for issue in naming_issues:
            self.results.append(AnalysisResult(
                category="Code Quality",
                severity="info",
                message=f"{issue['type'].title()} '{issue['name']}' doesn't follow naming conventions",
                file_path=issue['file'],
                line_number=issue['line'],
                suggestions=[
                    "Use snake_case for functions and variables",
                    "Use PascalCase for classes",
                    "Use UPPER_CASE for constants"
                ]
            ))
    
    def _check_import_organization(self) -> None:
        """Check import organization."""
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            lines = file.content.split('\n')
            import_lines = []
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')):
                    import_lines.append((i + 1, stripped))
            
            if len(import_lines) > 5:  # Only check files with multiple imports
                # Check if imports are grouped properly
                stdlib_imports = []
                third_party_imports = []
                local_imports = []
                
                for line_num, import_line in import_lines:
                    if 'graph_sitter' in import_line:
                        local_imports.append(line_num)
                    elif any(lib in import_line for lib in ['os', 'sys', 'json', 'pathlib', 'typing']):
                        stdlib_imports.append(line_num)
                    else:
                        third_party_imports.append(line_num)
                
                # Check if imports are properly ordered
                all_import_lines = stdlib_imports + third_party_imports + local_imports
                if all_import_lines != sorted(all_import_lines):
                    self.results.append(AnalysisResult(
                        category="Code Quality",
                        severity="info",
                        message="Imports are not properly organized",
                        file_path=str(file.path),
                        suggestions=[
                            "Group imports: stdlib, third-party, local",
                            "Sort imports within each group",
                            "Use tools like isort for automatic organization"
                        ]
                    ))
    
    def _analyze_architecture(self) -> None:
        """Analyze architectural patterns and issues."""
        logger.info("Analyzing architecture...")
        
        # Check for circular dependencies
        self._check_circular_dependencies()
        
        # Check module coupling
        self._check_module_coupling()
        
        # Check for architectural violations
        self._check_architectural_violations()
    
    def _check_circular_dependencies(self) -> None:
        """Check for circular import dependencies."""
        # This is a simplified check - in practice, you'd want more sophisticated analysis
        import_graph = defaultdict(set)
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            file_module = str(file.path.relative_to(self.codebase.repo_path)).replace('/', '.').replace('.py', '')
            
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('graph_sitter'):
                            import_graph[file_module].add(node.module)
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        # Simple cycle detection (this could be more sophisticated)
        for module, imports in import_graph.items():
            for imported in imports:
                if imported in import_graph and module in import_graph[imported]:
                    self.results.append(AnalysisResult(
                        category="Architecture",
                        severity="warning",
                        message=f"Potential circular dependency between {module} and {imported}",
                        suggestions=[
                            "Refactor to remove circular dependencies",
                            "Consider dependency inversion",
                            "Extract common interfaces"
                        ]
                    ))
    
    def _check_module_coupling(self) -> None:
        """Check for high coupling between modules."""
        # Count imports between modules
        module_imports = defaultdict(Counter)
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            file_module = str(file.path.relative_to(self.codebase.repo_path)).replace('/', '.').replace('.py', '')
            
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('graph_sitter'):
                            module_imports[file_module][node.module] += 1
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        # Report high coupling
        for module, imports in module_imports.items():
            total_imports = sum(imports.values())
            if total_imports > 10:  # Threshold for high coupling
                self.results.append(AnalysisResult(
                    category="Architecture",
                    severity="info",
                    message=f"Module {module} has high coupling ({total_imports} imports)",
                    suggestions=[
                        "Consider reducing dependencies",
                        "Use dependency injection",
                        "Extract interfaces to reduce coupling"
                    ]
                ))
    
    def _check_architectural_violations(self) -> None:
        """Check for architectural layer violations."""
        # Define architectural layers
        layers = {
            'core': ['core'],
            'extensions': ['extensions'],
            'cli': ['cli'],
            'shared': ['shared']
        }
        
        violations = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            file_parts = file.path.parts
            if 'src' in file_parts and 'graph_sitter' in file_parts:
                # Determine which layer this file belongs to
                current_layer = None
                for layer, paths in layers.items():
                    if any(path in file_parts for path in paths):
                        current_layer = layer
                        break
                
                if current_layer:
                    # Check imports
                    try:
                        tree = ast.parse(file.content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                if node.module and 'graph_sitter' in node.module:
                                    # Check if this violates layer rules
                                    if current_layer == 'core' and 'extensions' in node.module:
                                        violations.append({
                                            'file': str(file.path),
                                            'violation': f"Core layer importing from extensions: {node.module}"
                                        })
                    except Exception as e:
                        logger.debug(f"Error analyzing {file.path}: {e}")
        
        for violation in violations:
            self.results.append(AnalysisResult(
                category="Architecture",
                severity="warning",
                message=violation['violation'],
                file_path=violation['file'],
                suggestions=[
                    "Respect architectural layer boundaries",
                    "Move shared code to appropriate layer",
                    "Use dependency inversion if needed"
                ]
            ))
    
    def _analyze_dependencies(self) -> None:
        """Analyze dependency usage and issues."""
        logger.info("Analyzing dependencies...")
        
        # Check for unused imports
        self._check_unused_imports()
        
        # Check for missing dependencies
        self._check_missing_dependencies()
    
    def _check_unused_imports(self) -> None:
        """Check for unused imports."""
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                
                # Collect all imports
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.add(alias.name)
                
                # Collect all names used
                used_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        if isinstance(node.value, ast.Name):
                            used_names.add(node.value.id)
                
                # Find unused imports
                unused = imports - used_names
                if unused:
                    self.results.append(AnalysisResult(
                        category="Dependencies",
                        severity="info",
                        message=f"Unused imports: {', '.join(sorted(unused))}",
                        file_path=str(file.path),
                        suggestions=[
                            "Remove unused imports",
                            "Use tools like autoflake for automatic cleanup"
                        ]
                    ))
                    
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
    
    def _check_missing_dependencies(self) -> None:
        """Check for potentially missing dependencies."""
        # This is a simplified check - would need more sophisticated analysis
        common_imports = {
            'requests': 'requests',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'plotly': 'plotly'
        }
        
        used_packages = set()
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            package = alias.name.split('.')[0]
                            if package in common_imports:
                                used_packages.add(package)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            package = node.module.split('.')[0]
                            if package in common_imports:
                                used_packages.add(package)
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        # Check if packages are in requirements (simplified)
        requirements_files = [
            self.codebase.repo_path / 'requirements.txt',
            self.codebase.repo_path / 'pyproject.toml',
            self.codebase.repo_path / 'setup.py'
        ]
        
        declared_deps = set()
        for req_file in requirements_files:
            if req_file.exists():
                try:
                    content = req_file.read_text()
                    for package in used_packages:
                        if package in content:
                            declared_deps.add(package)
                except Exception as e:
                    logger.debug(f"Error reading {req_file}: {e}")
        
        missing_deps = used_packages - declared_deps
        if missing_deps:
            self.results.append(AnalysisResult(
                category="Dependencies",
                severity="warning",
                message=f"Potentially missing dependencies: {', '.join(sorted(missing_deps))}",
                suggestions=[
                    "Add missing dependencies to requirements.txt or pyproject.toml",
                    "Verify all dependencies are properly declared"
                ]
            ))
    
    def _analyze_test_coverage(self) -> None:
        """Analyze test coverage and quality."""
        logger.info("Analyzing test coverage...")
        
        # Count test files vs source files
        test_files = []
        source_files = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            if 'test' in str(file.path).lower():
                test_files.append(file)
            elif not any(skip in str(file.path) for skip in ['__pycache__', '.git', 'build']):
                source_files.append(file)
        
        if source_files:
            test_ratio = len(test_files) / len(source_files)
            if test_ratio < 0.3:  # Less than 30% test coverage
                self.results.append(AnalysisResult(
                    category="Testing",
                    severity="warning",
                    message=f"Low test coverage ratio: {test_ratio:.2%} ({len(test_files)} test files for {len(source_files)} source files)",
                    suggestions=[
                        "Add more unit tests",
                        "Consider test-driven development",
                        "Use coverage tools to identify untested code"
                    ]
                ))
    
    def _analyze_documentation(self) -> None:
        """Analyze documentation coverage and quality."""
        logger.info("Analyzing documentation...")
        
        undocumented_functions = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check if function has docstring
                        has_docstring = (
                            node.body and
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)
                        )
                        
                        if not has_docstring and not node.name.startswith('_'):
                            undocumented_functions.append({
                                'file': str(file.path),
                                'function': node.name,
                                'line': node.lineno
                            })
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        if undocumented_functions:
            self.results.append(AnalysisResult(
                category="Documentation",
                severity="info",
                message=f"Found {len(undocumented_functions)} undocumented public functions",
                suggestions=[
                    "Add docstrings to public functions",
                    "Follow PEP 257 docstring conventions",
                    "Include parameter and return type documentation"
                ]
            ))
    
    def _analyze_performance_patterns(self) -> None:
        """Analyze for performance anti-patterns."""
        logger.info("Analyzing performance patterns...")
        
        performance_issues = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            try:
                tree = ast.parse(file.content)
                for node in ast.walk(tree):
                    # Check for string concatenation in loops
                    if isinstance(node, (ast.For, ast.While)):
                        for child in ast.walk(node):
                            if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                                if isinstance(child.target, ast.Name):
                                    performance_issues.append({
                                        'file': str(file.path),
                                        'line': node.lineno,
                                        'issue': 'String concatenation in loop',
                                        'suggestion': 'Use list.append() and join() instead'
                                    })
                    
                    # Check for inefficient list operations
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            if node.func.attr == 'append' and isinstance(node.func.value, ast.ListComp):
                                performance_issues.append({
                                    'file': str(file.path),
                                    'line': node.lineno,
                                    'issue': 'Inefficient list comprehension with append',
                                    'suggestion': 'Use list comprehension directly'
                                })
                                
            except Exception as e:
                logger.debug(f"Error analyzing {file.path}: {e}")
        
        for issue in performance_issues:
            self.results.append(AnalysisResult(
                category="Performance",
                severity="info",
                message=issue['issue'],
                file_path=issue['file'],
                line_number=issue['line'],
                suggestions=[issue['suggestion']]
            ))
    
    def _analyze_security_patterns(self) -> None:
        """Analyze for security issues."""
        logger.info("Analyzing security patterns...")
        
        security_issues = []
        
        for file in self.codebase.files:
            if not file.path.suffix == '.py':
                continue
                
            content = file.content
            
            # Check for hardcoded secrets (simple patterns)
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
                (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
                (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
                (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token')
            ]
            
            for pattern, message in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    security_issues.append({
                        'file': str(file.path),
                        'line': line_num,
                        'issue': message,
                        'suggestion': 'Use environment variables or secure configuration'
                    })
            
            # Check for eval/exec usage
            if 'eval(' in content or 'exec(' in content:
                security_issues.append({
                    'file': str(file.path),
                    'line': None,
                    'issue': 'Use of eval() or exec()',
                    'suggestion': 'Avoid eval/exec for security reasons'
                })
        
        for issue in security_issues:
            self.results.append(AnalysisResult(
                category="Security",
                severity="warning",
                message=issue['issue'],
                file_path=issue['file'],
                line_number=issue['line'],
                suggestions=[issue['suggestion']]
            ))


def add_self_analysis_capabilities(codebase) -> None:
    """Add self-analysis capabilities to a Codebase instance."""
    if hasattr(codebase, '_analyzer'):
        return  # Already has analyzer
    
    analyzer = CodebaseAnalyzer(codebase)
    codebase._analyzer = analyzer
    
    # Add methods to codebase
    def analyze_self():
        """Analyze the codebase for issues and patterns."""
        return codebase._analyzer.analyze_all()
    
    def get_analysis_summary():
        """Get a summary of analysis results."""
        results = codebase._analyzer.analyze_all()
        
        summary = {
            'total_issues': len(results),
            'by_category': Counter(r.category for r in results),
            'by_severity': Counter(r.severity for r in results),
            'top_issues': results[:10]  # Top 10 issues
        }
        
        return summary
    
    def get_health_score():
        """Calculate a health score for the codebase."""
        results = codebase._analyzer.analyze_all()
        
        if not results:
            return 100  # Perfect score if no issues
        
        # Weight different severities
        severity_weights = {'error': 10, 'warning': 5, 'info': 1}
        total_weight = sum(severity_weights[r.severity] for r in results)
        
        # Calculate score (0-100, where 100 is perfect)
        max_possible_weight = len(codebase.files) * 10  # Assume max 10 weight per file
        score = max(0, 100 - (total_weight / max_possible_weight * 100))
        
        return min(100, score)
    
    # Add methods to codebase instance
    codebase.analyze_self = analyze_self
    codebase.get_analysis_summary = get_analysis_summary
    codebase.get_health_score = get_health_score
    
    logger.info(f"Self-analysis capabilities added to codebase: {codebase.repo_path}")

