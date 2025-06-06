"""
Dead Code Detection Module

Identifies unused functions, classes, variables, and imports in codebases.
Helps clean up codebases by finding code that can be safely removed.
"""

import ast
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class DeadCodeDetector:
    """Detects various types of dead code in codebases."""
    
    def __init__(self):
        self.usage_threshold = 0  # Minimum usage count to consider code as "alive"
        
        # Common entry points that should not be considered dead
        self.entry_points = {
            'main', '__main__', 'run', 'start', 'execute',
            'test_', 'setUp', 'tearDown', '__init__', '__new__',
            '__str__', '__repr__', '__len__', '__iter__'
        }
        
        # Magic methods that should not be considered dead
        self.magic_methods = {
            '__init__', '__new__', '__del__', '__str__', '__repr__',
            '__len__', '__iter__', '__next__', '__getitem__', '__setitem__',
            '__delitem__', '__contains__', '__call__', '__enter__', '__exit__',
            '__add__', '__sub__', '__mul__', '__div__', '__mod__', '__pow__',
            '__and__', '__or__', '__xor__', '__lshift__', '__rshift__',
            '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__',
            '__hash__', '__bool__', '__bytes__', '__format__'
        }
    
    def find_dead_code(self, codebase) -> List[Dict[str, Any]]:
        """Find all types of dead code in the codebase."""
        dead_code = []
        
        try:
            if hasattr(codebase, 'functions'):
                dead_code.extend(self._find_dead_code_graph_sitter(codebase))
            else:
                dead_code.extend(self._find_dead_code_ast(codebase))
        except Exception as e:
            logger.error(f"Dead code detection failed: {e}")
        
        return dead_code
    
    def _find_dead_code_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Find dead code using graph-sitter."""
        dead_code = []
        
        # Find unused functions
        dead_code.extend(self._find_unused_functions_graph_sitter(codebase))
        
        # Find unused classes
        dead_code.extend(self._find_unused_classes_graph_sitter(codebase))
        
        # Find unused imports
        dead_code.extend(self._find_unused_imports_graph_sitter(codebase))
        
        # Find unused variables (simplified)
        dead_code.extend(self._find_unused_variables_graph_sitter(codebase))
        
        return dead_code
    
    def _find_dead_code_ast(self, file_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find dead code using AST data."""
        dead_code = []
        
        # Build usage maps from AST data
        function_usage = defaultdict(int)
        class_usage = defaultdict(int)
        
        # Count usages (simplified analysis)
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                # This is a simplified approach - in reality we'd need call graph analysis
                function_usage[func['name']] += 1
            
            for cls in analysis.get('classes', []):
                class_usage[cls['name']] += 1
        
        # Find unused functions
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                if (function_usage[func['name']] <= 1 and  # Only defined, not used
                    not self._is_entry_point(func['name']) and
                    not func['name'].startswith('test_')):
                    
                    dead_code.append({
                        'type': 'unused_function',
                        'name': func['name'],
                        'file': filepath,
                        'line': func.get('line_start', 0),
                        'severity': 'minor',
                        'message': f"Function '{func['name']}' appears to be unused",
                        'confidence': 0.6  # Lower confidence for AST-only analysis
                    })
        
        return dead_code
    
    def _find_unused_functions_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Find unused functions using graph-sitter."""
        unused_functions = []
        
        for function in codebase.functions:
            # Check if function has any usages
            usages = getattr(function, 'usages', [])
            
            if (len(usages) <= self.usage_threshold and
                not self._is_entry_point(function.name) and
                not self._is_test_function(function.name) and
                not self._is_magic_method(function.name)):
                
                unused_functions.append({
                    'type': 'unused_function',
                    'name': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'severity': self._calculate_severity('function', function),
                    'message': f"Function '{function.name}' appears to be unused",
                    'confidence': 0.8,
                    'details': {
                        'usage_count': len(usages),
                        'is_public': not function.name.startswith('_'),
                        'has_decorators': len(getattr(function, 'decorators', [])) > 0,
                        'lines_of_code': len(function.source.splitlines()) if hasattr(function, 'source') else 0
                    }
                })
        
        return unused_functions
    
    def _find_unused_classes_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Find unused classes using graph-sitter."""
        unused_classes = []
        
        for cls in codebase.classes:
            # Check if class has any usages
            usages = getattr(cls, 'usages', [])
            
            if (len(usages) <= self.usage_threshold and
                not self._is_entry_point(cls.name) and
                not self._is_exception_class(cls) and
                not self._is_test_class(cls.name)):
                
                unused_classes.append({
                    'type': 'unused_class',
                    'name': cls.name,
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'severity': self._calculate_severity('class', cls),
                    'message': f"Class '{cls.name}' appears to be unused",
                    'confidence': 0.8,
                    'details': {
                        'usage_count': len(usages),
                        'is_public': not cls.name.startswith('_'),
                        'method_count': len(getattr(cls, 'methods', [])),
                        'has_subclasses': len(getattr(cls, 'subclasses', [])) > 0,
                        'inheritance_depth': len(getattr(cls, 'superclasses', []))
                    }
                })
        
        return unused_classes
    
    def _find_unused_imports_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Find unused imports using graph-sitter."""
        unused_imports = []
        
        for file in codebase.files:
            file_imports = getattr(file, 'imports', [])
            
            for import_stmt in file_imports:
                if self._is_import_unused(import_stmt, file):
                    unused_imports.append({
                        'type': 'unused_import',
                        'name': self._get_import_name(import_stmt),
                        'file': file.filepath,
                        'line': getattr(import_stmt, 'line_number', 0),
                        'severity': 'minor',
                        'message': f"Import '{self._get_import_name(import_stmt)}' appears to be unused",
                        'confidence': 0.7,
                        'details': {
                            'import_type': self._get_import_type(import_stmt),
                            'module': getattr(import_stmt, 'module_name', 'unknown')
                        }
                    })
        
        return unused_imports
    
    def _find_unused_variables_graph_sitter(self, codebase) -> List[Dict[str, Any]]:
        """Find unused variables using graph-sitter."""
        unused_variables = []
        
        # This is a simplified implementation
        # Full implementation would require detailed scope analysis
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                variables = self._extract_variables_from_source(function.source)
                for var_name, line_no in variables:
                    if (not var_name.startswith('_') and  # Skip private variables
                        not self._is_variable_used(var_name, function.source)):
                        
                        unused_variables.append({
                            'type': 'unused_variable',
                            'name': var_name,
                            'file': function.filepath,
                            'line': line_no,
                            'function': function.name,
                            'severity': 'minor',
                            'message': f"Variable '{var_name}' appears to be unused in function '{function.name}'",
                            'confidence': 0.6  # Lower confidence due to simplified analysis
                        })
        
        return unused_variables
    
    def _is_entry_point(self, name: str) -> bool:
        """Check if a function/class name is likely an entry point."""
        return any(entry in name.lower() for entry in self.entry_points)
    
    def _is_test_function(self, name: str) -> bool:
        """Check if a function is a test function."""
        return (name.startswith('test_') or 
                name.endswith('_test') or
                'test' in name.lower())
    
    def _is_test_class(self, name: str) -> bool:
        """Check if a class is a test class."""
        return (name.startswith('Test') or 
                name.endswith('Test') or
                'test' in name.lower())
    
    def _is_magic_method(self, name: str) -> bool:
        """Check if a function is a magic method."""
        return name in self.magic_methods
    
    def _is_exception_class(self, cls) -> bool:
        """Check if a class is an exception class."""
        class_name = cls.name.lower()
        superclasses = getattr(cls, 'superclasses', [])
        
        # Check if inherits from Exception or has 'error'/'exception' in name
        return ('error' in class_name or 
                'exception' in class_name or
                any('Exception' in str(base) for base in superclasses))
    
    def _calculate_severity(self, code_type: str, code_object) -> str:
        """Calculate severity of dead code."""
        if code_type == 'function':
            # Public functions are more severe to remove
            if not code_object.name.startswith('_'):
                return 'minor'
            else:
                return 'info'
        
        elif code_type == 'class':
            # Classes with many methods are more severe
            method_count = len(getattr(code_object, 'methods', []))
            if method_count > 5:
                return 'minor'
            else:
                return 'info'
        
        return 'info'
    
    def _is_import_unused(self, import_stmt, file) -> bool:
        """Check if an import is unused (simplified)."""
        # This is a simplified check - full implementation would require
        # detailed symbol usage analysis
        
        import_name = self._get_import_name(import_stmt)
        
        # Check if import name appears in file source
        if hasattr(file, 'source'):
            source = file.source
            # Simple text search (not perfect but reasonable heuristic)
            return import_name not in source.replace(f"import {import_name}", "")
        
        return False
    
    def _get_import_name(self, import_stmt) -> str:
        """Get the name of an import."""
        if hasattr(import_stmt, 'imported_symbol') and import_stmt.imported_symbol:
            return import_stmt.imported_symbol.name
        elif hasattr(import_stmt, 'module_name'):
            return import_stmt.module_name
        else:
            return 'unknown'
    
    def _get_import_type(self, import_stmt) -> str:
        """Get the type of import (from, import, etc.)."""
        if hasattr(import_stmt, 'is_from_import') and import_stmt.is_from_import:
            return 'from_import'
        else:
            return 'import'
    
    def _extract_variables_from_source(self, source: str) -> List[Tuple[str, int]]:
        """Extract variable assignments from source code."""
        variables = []
        
        try:
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append((target.id, node.lineno))
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    variables.append((node.target.id, node.lineno))
        
        except SyntaxError:
            pass
        
        return variables
    
    def _is_variable_used(self, var_name: str, source: str) -> bool:
        """Check if a variable is used in the source code (simplified)."""
        try:
            tree = ast.parse(source)
            
            # Count assignments vs usages
            assignments = 0
            usages = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == var_name:
                            assignments += 1
                elif isinstance(node, ast.Name) and node.id == var_name:
                    if isinstance(node.ctx, ast.Load):
                        usages += 1
            
            # Variable is used if it's loaded more than just assigned
            return usages > assignments
        
        except SyntaxError:
            # Fallback to simple text search
            return var_name in source.replace(f"{var_name} =", "")
    
    def generate_dead_code_report(self, dead_code: List[Dict[str, Any]]) -> str:
        """Generate a human-readable dead code report."""
        if not dead_code:
            return "✅ No dead code detected!"
        
        report = []
        report.append("🗑️  DEAD CODE ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Group by type
        by_type = defaultdict(list)
        for item in dead_code:
            by_type[item['type']].append(item)
        
        # Summary
        report.append(f"📊 Total Dead Code Items: {len(dead_code)}")
        for code_type, items in by_type.items():
            type_name = code_type.replace('_', ' ').title()
            report.append(f"  • {type_name}: {len(items)}")
        report.append("")
        
        # Details by type
        for code_type, items in by_type.items():
            if items:
                type_name = code_type.replace('_', ' ').title()
                report.append(f"🔍 {type_name.upper()}")
                report.append("-" * 30)
                
                for item in items[:10]:  # Limit to first 10 items
                    report.append(f"  • {item['name']} ({item['file']}:{item.get('line', '?')})")
                
                if len(items) > 10:
                    report.append(f"  ... and {len(items) - 10} more")
                
                report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 30)
        
        if by_type['unused_function']:
            report.append("• Review unused functions - they may be safe to remove")
        
        if by_type['unused_class']:
            report.append("• Consider removing unused classes to reduce codebase size")
        
        if by_type['unused_import']:
            report.append("• Remove unused imports to improve load times")
        
        if by_type['unused_variable']:
            report.append("• Clean up unused variables to improve code clarity")
        
        return "\n".join(report)
    
    def get_cleanup_suggestions(self, dead_code: List[Dict[str, Any]]) -> List[str]:
        """Get specific cleanup suggestions."""
        suggestions = []
        
        # Group by file for easier cleanup
        by_file = defaultdict(list)
        for item in dead_code:
            by_file[item['file']].append(item)
        
        for filepath, items in by_file.items():
            if len(items) > 1:
                suggestions.append(f"📁 {filepath}: {len(items)} dead code items to review")
        
        # High-impact suggestions
        high_impact = [item for item in dead_code if item.get('severity') in ['major', 'critical']]
        if high_impact:
            suggestions.append(f"🎯 {len(high_impact)} high-impact items should be prioritized")
        
        # Safe removals
        safe_removals = [item for item in dead_code if item.get('confidence', 0) > 0.8]
        if safe_removals:
            suggestions.append(f"✅ {len(safe_removals)} items are safe to remove with high confidence")
        
        return suggestions

