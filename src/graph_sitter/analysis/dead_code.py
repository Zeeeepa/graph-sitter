"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple

import networkx as nx

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol

Dead code detection implementation following graph-sitter.com patterns.

This module provides comprehensive dead code detection including:
- Unused functions and classes
- Unreferenced imports
- Unused variables
- Dead code elimination strategies
"""

@dataclass
class DeadCodeItem:
    """Represents a piece of dead code."""
    item_type: str  # 'function', 'class', 'import', 'variable'
    name: str
    qualified_name: str
    file_path: str
    line_number: int
    reason: str
    confidence: float  # 0.0 to 1.0
    safe_to_remove: bool
    dependencies: List[str]  # Other items that depend on this
    
    @property
    def location(self) -> str:
        """Get human-readable location."""
        return f"{self.file_path}:{self.line_number}"

@dataclass
class DeadCodeReport:
    """Comprehensive dead code analysis report."""
    total_items_analyzed: int
    dead_functions: List[DeadCodeItem]
    dead_classes: List[DeadCodeItem]
    unused_imports: List[DeadCodeItem]
    unused_variables: List[DeadCodeItem]
    potential_savings: Dict[str, int]  # Lines of code that could be removed
    
    @property
    def total_dead_items(self) -> int:
        """Get total number of dead code items."""
        return (len(self.dead_functions) + len(self.dead_classes) + 
                len(self.unused_imports) + len(self.unused_variables))
    
    @property
    def total_potential_loc_savings(self) -> int:
        """Get total lines of code that could be saved."""
        return sum(self.potential_savings.values())

class DeadCodeDetector:
    """
    Dead code detector following graph-sitter.com patterns.
    
    Provides comprehensive dead code analysis including:
    - Function and class usage analysis
    - Import dependency tracking
    - Variable usage detection
    - Safe removal recommendations
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize dead code detector with codebase."""
        self.codebase = codebase
        self._symbol_usage_cache: Dict[str, Set[str]] = {}
        self._entry_points: Set[str] = set()
        self._test_patterns: Set[str] = {'test_', '_test', 'Test', 'tests'}
        
    def analyze(self, include_tests: bool = False, 
                confidence_threshold: float = 0.7) -> DeadCodeReport:
        """
        Perform comprehensive dead code analysis.
        
        Args:
            include_tests: Whether to include test files in analysis
            confidence_threshold: Minimum confidence level for dead code detection
            
        Returns:
            DeadCodeReport with all detected dead code
        """
        # Build usage maps
        self._build_symbol_usage_map()
        self._identify_entry_points()
        
        # Analyze different types of dead code
        dead_functions = self._find_dead_functions(include_tests, confidence_threshold)
        dead_classes = self._find_dead_classes(include_tests, confidence_threshold)
        unused_imports = self._find_unused_imports(confidence_threshold)
        unused_variables = self._find_unused_variables(confidence_threshold)
        
        # Calculate potential savings
        potential_savings = self._calculate_potential_savings(
            dead_functions, dead_classes, unused_imports, unused_variables
        )
        
        total_analyzed = (len(list(self.codebase.functions)) + 
                         len(list(self.codebase.classes)) +
                         len(list(self.codebase.imports)))
        
        return DeadCodeReport(
            total_items_analyzed=total_analyzed,
            dead_functions=dead_functions,
            dead_classes=dead_classes,
            unused_imports=unused_imports,
            unused_variables=unused_variables,
            potential_savings=potential_savings
        )
    
    def find_unused_functions(self, include_tests: bool = False) -> List[Function]:
        """
        Find functions with no call sites (potential dead code).
        
        Based on graph-sitter.com call site analysis patterns.
        """
        unused_functions = []
        
        for function in self.codebase.functions:
            if self._is_function_unused(function, include_tests):
                unused_functions.append(function)
        
        return unused_functions
    
    def find_unused_classes(self, include_tests: bool = False) -> List[Class]:
        """Find classes with no usages."""
        unused_classes = []
        
        for class_def in self.codebase.classes:
            if self._is_class_unused(class_def, include_tests):
                unused_classes.append(class_def)
        
        return unused_classes
    
    def find_circular_imports(self) -> List[List[str]]:
        """Find circular import dependencies."""
        
        # Build import dependency graph
        import_graph = nx.DiGraph()
        
        for file in self.codebase.files:
            if hasattr(file, 'imports'):
                for import_stmt in file.imports:
                    if hasattr(import_stmt, 'imported_symbol'):
                        imported_symbol = import_stmt.imported_symbol
                        if hasattr(imported_symbol, 'filepath'):
                            import_graph.add_edge(file.filepath, imported_symbol.filepath)
        
        # Find cycles
        try:
            cycles = list(nx.simple_cycles(import_graph))
            return cycles
        except:
            return []
    
    def get_removal_plan(self, dead_code_report: DeadCodeReport) -> Dict[str, List[str]]:
        """
        Generate a safe removal plan for dead code.
        
        Returns:
            Dictionary mapping file paths to lists of items to remove
        """
        removal_plan = {}
        
        # Group by file for efficient removal
        all_items = (dead_code_report.dead_functions + 
                    dead_code_report.dead_classes +
                    dead_code_report.unused_imports +
                    dead_code_report.unused_variables)
        
        for item in all_items:
            if item.safe_to_remove and item.confidence >= 0.8:
                if item.file_path not in removal_plan:
                    removal_plan[item.file_path] = []
                removal_plan[item.file_path].append(
                    f"{item.item_type}: {item.name} (line {item.line_number})"
                )
        
        return removal_plan
    
    def estimate_cleanup_impact(self, dead_code_report: DeadCodeReport) -> Dict[str, Any]:
        """Estimate the impact of cleaning up dead code."""
        total_files_affected = len(set(item.file_path for item in 
                                     dead_code_report.dead_functions + 
                                     dead_code_report.dead_classes +
                                     dead_code_report.unused_imports +
                                     dead_code_report.unused_variables))
        
        return {
            'files_affected': total_files_affected,
            'total_items_removable': dead_code_report.total_dead_items,
            'loc_savings': dead_code_report.total_potential_loc_savings,
            'complexity_reduction': self._estimate_complexity_reduction(dead_code_report),
            'maintenance_burden_reduction': self._estimate_maintenance_reduction(dead_code_report)
        }
    
    # Private helper methods
    
    def _build_symbol_usage_map(self):
        """Build a map of symbol usage across the codebase."""
        self._symbol_usage_cache.clear()
        
        for symbol in self.codebase.symbols:
            if hasattr(symbol, 'symbol_usages'):
                usage_locations = set()
                for usage in symbol.symbol_usages:
                    if hasattr(usage, 'filepath'):
                        usage_locations.add(usage.filepath)
                    elif hasattr(usage, 'file') and hasattr(usage.file, 'filepath'):
                        usage_locations.add(usage.file.filepath)
                
                self._symbol_usage_cache[symbol.qualified_name] = usage_locations
    
    def _identify_entry_points(self):
        """Identify entry point functions that should not be considered dead."""
        self._entry_points.clear()
        
        for function in self.codebase.functions:
            if self._is_entry_point_function(function):
                self._entry_points.add(function.qualified_name)
    
    def _is_entry_point_function(self, function: Function) -> bool:
        """Check if a function is an entry point."""
        entry_point_names = {
            'main', '__main__', 'run', 'start', 'execute', 'init', '__init__',
            'setup', 'teardown', 'setUp', 'tearDown'
        }
        
        # Check function name
        if function.name in entry_point_names:
            return True
        
        # Check for decorators that indicate entry points
        if hasattr(function, 'decorators'):
            decorator_names = {str(d) for d in function.decorators}
            entry_decorators = {'@app.route', '@click.command', '@pytest.fixture'}
            if any(entry_dec in dec for dec in decorator_names for entry_dec in entry_decorators):
                return True
        
        # Check if it's in a main block
        if hasattr(function, 'source'):
            return 'if __name__ == "__main__"' in function.source
        
        return False
    
    def _is_function_unused(self, function: Function, include_tests: bool) -> bool:
        """Check if a function is unused."""
        # Skip entry points
        if function.qualified_name in self._entry_points:
            return False
        
        # Skip test functions unless specifically including them
        if not include_tests and self._is_test_function(function):
            return False
        
        # Check call sites
        if hasattr(function, 'call_sites'):
            call_sites = function.call_sites
            if len(call_sites) > 0:
                return False
        
        # Check symbol usage
        if function.qualified_name in self._symbol_usage_cache:
            usage_locations = self._symbol_usage_cache[function.qualified_name]
            if len(usage_locations) > 1:  # Used in more than just its definition file
                return False
        
        # Check for special methods
        if self._is_special_method(function):
            return False
        
        return True
    
    def _is_class_unused(self, class_def: Class, include_tests: bool) -> bool:
        """Check if a class is unused."""
        # Skip test classes unless specifically including them
        if not include_tests and self._is_test_class(class_def):
            return False
        
        # Check if class is instantiated or subclassed
        if hasattr(class_def, 'usages'):
            if len(class_def.usages) > 0:
                return False
        
        # Check if any methods are used
        if hasattr(class_def, 'methods'):
            for method in class_def.methods:
                if not self._is_function_unused(method, include_tests):
                    return False
        
        # Check symbol usage
        if class_def.qualified_name in self._symbol_usage_cache:
            usage_locations = self._symbol_usage_cache[class_def.qualified_name]
            if len(usage_locations) > 1:
                return False
        
        return True
    
    def _is_test_function(self, function: Function) -> bool:
        """Check if a function is a test function."""
        test_indicators = ['test_', '_test', 'Test']
        return any(indicator in function.name for indicator in test_indicators)
    
    def _is_test_class(self, class_def: Class) -> bool:
        """Check if a class is a test class."""
        test_indicators = ['Test', 'test_', '_test']
        return any(indicator in class_def.name for indicator in test_indicators)
    
    def _is_special_method(self, function: Function) -> bool:
        """Check if a function is a special method (dunder methods, etc.)."""
        special_patterns = ['__', 'setUp', 'tearDown', 'test_']
        return any(pattern in function.name for pattern in special_patterns)
    
    def _find_dead_functions(self, include_tests: bool, confidence_threshold: float) -> List[DeadCodeItem]:
        """Find dead functions with confidence scoring."""
        dead_functions = []
        
        for function in self.codebase.functions:
            if self._is_function_unused(function, include_tests):
                confidence = self._calculate_function_dead_confidence(function)
                
                if confidence >= confidence_threshold:
                    dead_functions.append(DeadCodeItem(
                        item_type='function',
                        name=function.name,
                        qualified_name=function.qualified_name,
                        file_path=getattr(function, 'filepath', ''),
                        line_number=getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                        reason='No call sites found',
                        confidence=confidence,
                        safe_to_remove=confidence > 0.8,
                        dependencies=[]
                    ))
        
        return dead_functions
    
    def _find_dead_classes(self, include_tests: bool, confidence_threshold: float) -> List[DeadCodeItem]:
        """Find dead classes with confidence scoring."""
        dead_classes = []
        
        for class_def in self.codebase.classes:
            if self._is_class_unused(class_def, include_tests):
                confidence = self._calculate_class_dead_confidence(class_def)
                
                if confidence >= confidence_threshold:
                    dead_classes.append(DeadCodeItem(
                        item_type='class',
                        name=class_def.name,
                        qualified_name=class_def.qualified_name,
                        file_path=getattr(class_def, 'filepath', ''),
                        line_number=getattr(class_def, 'start_point', [0])[0] if hasattr(class_def, 'start_point') else 0,
                        reason='No usages or instantiations found',
                        confidence=confidence,
                        safe_to_remove=confidence > 0.8,
                        dependencies=[]
                    ))
        
        return dead_classes
    
    def _find_unused_imports(self, confidence_threshold: float) -> List[DeadCodeItem]:
        """Find unused imports."""
        unused_imports = []
        
        for file in self.codebase.files:
            if hasattr(file, 'imports'):
                for import_stmt in file.imports:
                    if self._is_import_unused(import_stmt, file):
                        confidence = self._calculate_import_dead_confidence(import_stmt, file)
                        
                        if confidence >= confidence_threshold:
                            unused_imports.append(DeadCodeItem(
                                item_type='import',
                                name=str(import_stmt),
                                qualified_name=str(import_stmt),
                                file_path=file.filepath,
                                line_number=getattr(import_stmt, 'start_point', [0])[0] if hasattr(import_stmt, 'start_point') else 0,
                                reason='Import not used in file',
                                confidence=confidence,
                                safe_to_remove=confidence > 0.9,
                                dependencies=[]
                            ))
        
        return unused_imports
    
    def _find_unused_variables(self, confidence_threshold: float) -> List[DeadCodeItem]:
        """Find unused variables."""
        unused_variables = []
        
        # This would require more sophisticated analysis of variable usage
        # For now, return empty list as this requires AST-level analysis
        
        return unused_variables
    
    def _is_import_unused(self, import_stmt, file: SourceFile) -> bool:
        """Check if an import is unused in the file."""
        # Simple heuristic: check if imported name appears in file source
        if hasattr(file, 'source') and hasattr(import_stmt, 'imported_symbol'):
            imported_name = str(import_stmt.imported_symbol)
            if hasattr(import_stmt.imported_symbol, 'name'):
                imported_name = import_stmt.imported_symbol.name
            
            # Check if the imported name is used in the file
            return imported_name not in file.source
        
        return False
    
    def _calculate_function_dead_confidence(self, function: Function) -> float:
        """Calculate confidence that a function is dead code."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if no call sites
        if hasattr(function, 'call_sites') and len(function.call_sites) == 0:
            confidence += 0.3
        
        # Increase confidence if not in entry points
        if function.qualified_name not in self._entry_points:
            confidence += 0.2
        
        # Decrease confidence for special methods
        if self._is_special_method(function):
            confidence -= 0.3
        
        # Decrease confidence for test functions
        if self._is_test_function(function):
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_class_dead_confidence(self, class_def: Class) -> float:
        """Calculate confidence that a class is dead code."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if no usages
        if hasattr(class_def, 'usages') and len(class_def.usages) == 0:
            confidence += 0.3
        
        # Check if any methods are used
        if hasattr(class_def, 'methods'):
            used_methods = sum(1 for method in class_def.methods 
                             if not self._is_function_unused(method, False))
            if used_methods == 0:
                confidence += 0.2
            else:
                confidence -= 0.1 * used_methods
        
        # Decrease confidence for test classes
        if self._is_test_class(class_def):
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_import_dead_confidence(self, import_stmt, file: SourceFile) -> float:
        """Calculate confidence that an import is unused."""
        # High confidence for import analysis since it's more straightforward
        return 0.9 if self._is_import_unused(import_stmt, file) else 0.1
    
    def _calculate_potential_savings(self, dead_functions: List[DeadCodeItem],
                                   dead_classes: List[DeadCodeItem],
                                   unused_imports: List[DeadCodeItem],
                                   unused_variables: List[DeadCodeItem]) -> Dict[str, int]:
        """Calculate potential lines of code savings."""
        savings = {
            'functions': 0,
            'classes': 0,
            'imports': len(unused_imports),  # Each import is typically 1 line
            'variables': len(unused_variables)
        }
        
        # Estimate function LOC savings
        for func_item in dead_functions:
            # Rough estimate: average function is 10 lines
            savings['functions'] += 10
        
        # Estimate class LOC savings
        for class_item in dead_classes:
            # Rough estimate: average class is 20 lines
            savings['classes'] += 20
        
        return savings
    
    def _estimate_complexity_reduction(self, dead_code_report: DeadCodeReport) -> float:
        """Estimate complexity reduction from removing dead code."""
        # Simple heuristic: each function/class removal reduces complexity
        complexity_reduction = (len(dead_code_report.dead_functions) * 2 +
                               len(dead_code_report.dead_classes) * 3)
        return min(complexity_reduction, 100.0)  # Cap at 100%
    
    def _estimate_maintenance_reduction(self, dead_code_report: DeadCodeReport) -> float:
        """Estimate maintenance burden reduction."""
        # Maintenance reduction is proportional to code removed
        total_items = dead_code_report.total_dead_items
        return min(total_items * 0.5, 50.0)  # Cap at 50% reduction
