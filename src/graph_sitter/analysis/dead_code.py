"""Dead code detection and cleanup analysis following graph-sitter.com patterns."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol

logger = logging.getLogger(__name__)


@dataclass
class DeadCodeItem:
    """Represents a piece of dead code."""
    symbol: Symbol
    type: str  # 'function', 'class', 'variable', 'import'
    filepath: str
    line_start: Optional[int]
    line_end: Optional[int]
    reason: str
    confidence: float  # 0.0 to 1.0
    impact_score: float
    safe_to_remove: bool
    dependencies: List[str]


@dataclass
class CleanupPlan:
    """Plan for removing dead code safely."""
    items: List[DeadCodeItem]
    removal_order: List[str]  # Order to remove items
    estimated_lines_saved: int
    estimated_files_affected: int
    risk_assessment: str  # 'low', 'medium', 'high'
    warnings: List[str]


class DeadCodeDetector:
    """Comprehensive dead code detection and analysis."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.dead_code_items: List[DeadCodeItem] = []
        self.usage_graph: Dict[str, Set[str]] = {}
        self._build_usage_graph()
    
    def _build_usage_graph(self):
        """Build usage graph for dead code detection."""
        try:
            # Build symbol usage relationships
            for symbol in self.codebase.symbols:
                symbol_id = f"{symbol.__class__.__name__}:{symbol.name}"
                self.usage_graph[symbol_id] = set()
                
                # Add usages
                usages = getattr(symbol, 'usages', [])
                for usage in usages:
                    usage_id = f"{usage.__class__.__name__}:{getattr(usage, 'name', str(usage))}"
                    self.usage_graph[symbol_id].add(usage_id)
                
                # Add call sites for functions
                if isinstance(symbol, Function):
                    call_sites = getattr(symbol, 'call_sites', [])
                    for call_site in call_sites:
                        caller = getattr(call_site, 'parent_function', None)
                        if caller:
                            caller_id = f"Function:{caller.name}"
                            self.usage_graph[symbol_id].add(caller_id)
        except Exception as e:
            logger.error(f"Error building usage graph: {e}")
    
    def find_dead_code(self) -> List[DeadCodeItem]:
        """Find all dead code in the codebase."""
        try:
            self.dead_code_items = []
            
            # Find unused functions
            self.dead_code_items.extend(self._find_unused_functions())
            
            # Find unused classes
            self.dead_code_items.extend(self._find_unused_classes())
            
            # Find unused imports
            self.dead_code_items.extend(self._find_unused_imports())
            
            # Find unused variables
            self.dead_code_items.extend(self._find_unused_variables())
            
            # Find unreachable code
            self.dead_code_items.extend(self._find_unreachable_code())
            
            return self.dead_code_items
        except Exception as e:
            logger.error(f"Error finding dead code: {e}")
            return []
    
    def _find_unused_functions(self) -> List[DeadCodeItem]:
        """Find functions with no call sites or usages."""
        try:
            unused_functions = []
            
            for function in self.codebase.functions:
                # Check if function has any usages
                usages = getattr(function, 'usages', [])
                call_sites = getattr(function, 'call_sites', [])
                
                if not usages and not call_sites:
                    # Check if it's a potential entry point
                    if not self._is_entry_point(function):
                        confidence = self._calculate_confidence(function, 'function')
                        impact_score = self._calculate_impact_score(function)
                        
                        unused_functions.append(DeadCodeItem(
                            symbol=function,
                            type='function',
                            filepath=getattr(function, 'filepath', 'unknown'),
                            line_start=getattr(function, 'line_start', None),
                            line_end=getattr(function, 'line_end', None),
                            reason='No call sites or usages found',
                            confidence=confidence,
                            impact_score=impact_score,
                            safe_to_remove=confidence > 0.8,
                            dependencies=self._get_symbol_dependencies(function)
                        ))
            
            return unused_functions
        except Exception as e:
            logger.error(f"Error finding unused functions: {e}")
            return []
    
    def _find_unused_classes(self) -> List[DeadCodeItem]:
        """Find classes with no instantiations or usages."""
        try:
            unused_classes = []
            
            for class_def in self.codebase.classes:
                # Check if class has any usages
                usages = getattr(class_def, 'usages', [])
                
                # Check if any methods are used
                methods = getattr(class_def, 'methods', [])
                method_usages = []
                for method in methods:
                    method_usages.extend(getattr(method, 'usages', []))
                    method_usages.extend(getattr(method, 'call_sites', []))
                
                if not usages and not method_usages:
                    # Check if it's a base class or has special significance
                    if not self._is_base_class(class_def):
                        confidence = self._calculate_confidence(class_def, 'class')
                        impact_score = self._calculate_impact_score(class_def)
                        
                        unused_classes.append(DeadCodeItem(
                            symbol=class_def,
                            type='class',
                            filepath=getattr(class_def, 'filepath', 'unknown'),
                            line_start=getattr(class_def, 'line_start', None),
                            line_end=getattr(class_def, 'line_end', None),
                            reason='No instantiations or method usages found',
                            confidence=confidence,
                            impact_score=impact_score,
                            safe_to_remove=confidence > 0.7,
                            dependencies=self._get_symbol_dependencies(class_def)
                        ))
            
            return unused_classes
        except Exception as e:
            logger.error(f"Error finding unused classes: {e}")
            return []
    
    def _find_unused_imports(self) -> List[DeadCodeItem]:
        """Find imports that are not used."""
        try:
            unused_imports = []
            
            for import_stmt in self.codebase.imports:
                imported_symbol = getattr(import_stmt, 'imported_symbol', None)
                
                if imported_symbol:
                    # Check if the imported symbol is used
                    usages = getattr(imported_symbol, 'usages', [])
                    
                    if not usages:
                        # Additional check: look for string references in source
                        symbol_name = getattr(imported_symbol, 'name', '')
                        if symbol_name and not self._has_string_references(symbol_name, import_stmt):
                            confidence = 0.9  # High confidence for unused imports
                            
                            unused_imports.append(DeadCodeItem(
                                symbol=import_stmt,
                                type='import',
                                filepath=getattr(import_stmt, 'filepath', 'unknown'),
                                line_start=getattr(import_stmt, 'line_start', None),
                                line_end=getattr(import_stmt, 'line_end', None),
                                reason='Imported symbol is not used',
                                confidence=confidence,
                                impact_score=0.1,  # Low impact
                                safe_to_remove=True,
                                dependencies=[]
                            ))
            
            return unused_imports
        except Exception as e:
            logger.error(f"Error finding unused imports: {e}")
            return []
    
    def _find_unused_variables(self) -> List[DeadCodeItem]:
        """Find global variables that are not used."""
        try:
            unused_variables = []
            
            for var in self.codebase.global_vars:
                # Check if variable has any usages
                usages = getattr(var, 'usages', [])
                
                if not usages:
                    # Check if it's a configuration variable or constant
                    if not self._is_configuration_variable(var):
                        confidence = self._calculate_confidence(var, 'variable')
                        impact_score = self._calculate_impact_score(var)
                        
                        unused_variables.append(DeadCodeItem(
                            symbol=var,
                            type='variable',
                            filepath=getattr(var, 'filepath', 'unknown'),
                            line_start=getattr(var, 'line_start', None),
                            line_end=getattr(var, 'line_end', None),
                            reason='Global variable is not used',
                            confidence=confidence,
                            impact_score=impact_score,
                            safe_to_remove=confidence > 0.8,
                            dependencies=[]
                        ))
            
            return unused_variables
        except Exception as e:
            logger.error(f"Error finding unused variables: {e}")
            return []
    
    def _find_unreachable_code(self) -> List[DeadCodeItem]:
        """Find unreachable code blocks."""
        try:
            # This is a simplified implementation
            # In practice, you'd need more sophisticated control flow analysis
            unreachable_code = []
            
            for function in self.codebase.functions:
                source = getattr(function, 'source', '')
                lines = source.split('\n')
                
                # Look for code after return statements
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('return ') and i < len(lines) - 1:
                        # Check if there's non-comment code after return
                        remaining_lines = lines[i+1:]
                        non_comment_lines = [
                            l for l in remaining_lines
                            if l.strip() and not l.strip().startswith('#')
                        ]
                        
                        if non_comment_lines:
                            # Found unreachable code
                            unreachable_code.append(DeadCodeItem(
                                symbol=function,
                                type='unreachable_code',
                                filepath=getattr(function, 'filepath', 'unknown'),
                                line_start=getattr(function, 'line_start', 0) + i + 1,
                                line_end=getattr(function, 'line_end', 0),
                                reason='Code after return statement',
                                confidence=0.9,
                                impact_score=0.2,
                                safe_to_remove=True,
                                dependencies=[]
                            ))
                            break
            
            return unreachable_code
        except Exception as e:
            logger.error(f"Error finding unreachable code: {e}")
            return []
    
    def estimate_cleanup_impact(self, items: List[DeadCodeItem]) -> Dict[str, Any]:
        """Estimate the impact of removing dead code."""
        try:
            total_lines = 0
            files_affected = set()
            risk_factors = []
            
            for item in items:
                # Estimate lines of code
                if item.line_start and item.line_end:
                    total_lines += item.line_end - item.line_start + 1
                else:
                    # Estimate based on symbol type
                    if item.type == 'function':
                        total_lines += 10  # Average function size
                    elif item.type == 'class':
                        total_lines += 20  # Average class size
                    elif item.type == 'import':
                        total_lines += 1
                    else:
                        total_lines += 5
                
                files_affected.add(item.filepath)
                
                # Assess risk factors
                if item.confidence < 0.7:
                    risk_factors.append(f"Low confidence for {item.symbol.name}")
                
                if item.impact_score > 0.5:
                    risk_factors.append(f"High impact for {item.symbol.name}")
            
            # Calculate risk level
            if len(risk_factors) > len(items) * 0.3:
                risk_level = 'high'
            elif len(risk_factors) > len(items) * 0.1:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'estimated_lines_saved': total_lines,
                'files_affected': len(files_affected),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'items_by_type': {
                    'functions': len([i for i in items if i.type == 'function']),
                    'classes': len([i for i in items if i.type == 'class']),
                    'imports': len([i for i in items if i.type == 'import']),
                    'variables': len([i for i in items if i.type == 'variable']),
                    'unreachable': len([i for i in items if i.type == 'unreachable_code'])
                }
            }
        except Exception as e:
            logger.error(f"Error estimating cleanup impact: {e}")
            return {}
    
    def get_removal_plan(self, items: List[DeadCodeItem]) -> CleanupPlan:
        """Generate a safe removal plan for dead code."""
        try:
            # Sort items by safety and impact
            safe_items = [item for item in items if item.safe_to_remove]
            unsafe_items = [item for item in items if not item.safe_to_remove]
            
            # Sort safe items by impact (remove low impact first)
            safe_items.sort(key=lambda x: (x.impact_score, -x.confidence))
            
            # Create removal order
            removal_order = []
            
            # First: Remove imports (lowest risk)
            imports = [item for item in safe_items if item.type == 'import']
            removal_order.extend([item.symbol.name for item in imports])
            
            # Second: Remove unused variables
            variables = [item for item in safe_items if item.type == 'variable']
            removal_order.extend([item.symbol.name for item in variables])
            
            # Third: Remove unreachable code
            unreachable = [item for item in safe_items if item.type == 'unreachable_code']
            removal_order.extend([item.symbol.name for item in unreachable])
            
            # Fourth: Remove unused functions
            functions = [item for item in safe_items if item.type == 'function']
            removal_order.extend([item.symbol.name for item in functions])
            
            # Last: Remove unused classes (highest risk)
            classes = [item for item in safe_items if item.type == 'class']
            removal_order.extend([item.symbol.name for item in classes])
            
            # Estimate impact
            impact = self.estimate_cleanup_impact(safe_items)
            
            # Generate warnings
            warnings = []
            if unsafe_items:
                warnings.append(f"{len(unsafe_items)} items require manual review")
            
            if impact.get('risk_level') == 'high':
                warnings.append("High risk cleanup - proceed with caution")
            
            for risk_factor in impact.get('risk_factors', []):
                warnings.append(risk_factor)
            
            return CleanupPlan(
                items=safe_items,
                removal_order=removal_order,
                estimated_lines_saved=impact.get('estimated_lines_saved', 0),
                estimated_files_affected=impact.get('files_affected', 0),
                risk_assessment=impact.get('risk_level', 'unknown'),
                warnings=warnings
            )
        except Exception as e:
            logger.error(f"Error creating removal plan: {e}")
            return CleanupPlan(
                items=[], removal_order=[], estimated_lines_saved=0,
                estimated_files_affected=0, risk_assessment='unknown',
                warnings=[f"Error creating plan: {e}"]
            )
    
    def _is_entry_point(self, function: Function) -> bool:
        """Check if function is a potential entry point."""
        try:
            entry_patterns = [
                'main', '__main__', 'run', 'start', 'execute',
                'test_', 'setup', 'teardown', '__init__',
                'handle', 'process', 'serve'
            ]
            
            func_name = function.name.lower()
            
            # Check name patterns
            if any(pattern in func_name for pattern in entry_patterns):
                return True
            
            # Check decorators for entry points
            decorators = getattr(function, 'decorators', [])
            for decorator in decorators:
                decorator_str = str(decorator).lower()
                if any(pattern in decorator_str for pattern in ['app.route', 'click.command', 'pytest']):
                    return True
            
            return False
        except Exception:
            return False
    
    def _is_base_class(self, class_def: Class) -> bool:
        """Check if class is a base class or has special significance."""
        try:
            # Check if it has subclasses
            subclasses = getattr(class_def, 'subclasses', [])
            if subclasses:
                return True
            
            # Check for abstract methods or special patterns
            methods = getattr(class_def, 'methods', [])
            for method in methods:
                decorators = getattr(method, 'decorators', [])
                for decorator in decorators:
                    if 'abstractmethod' in str(decorator):
                        return True
            
            # Check class name patterns
            class_name = class_def.name
            base_patterns = ['Base', 'Abstract', 'Interface', 'Mixin', 'Protocol']
            if any(pattern in class_name for pattern in base_patterns):
                return True
            
            return False
        except Exception:
            return False
    
    def _is_configuration_variable(self, variable: Symbol) -> bool:
        """Check if variable is a configuration variable."""
        try:
            var_name = variable.name.upper()
            config_patterns = [
                'CONFIG', 'SETTING', 'CONSTANT', 'DEFAULT',
                'URL', 'PATH', 'KEY', 'SECRET', 'TOKEN',
                'DEBUG', 'VERSION', 'API_'
            ]
            
            return any(pattern in var_name for pattern in config_patterns)
        except Exception:
            return False
    
    def _calculate_confidence(self, symbol: Symbol, symbol_type: str) -> float:
        """Calculate confidence that symbol is truly dead."""
        try:
            confidence = 0.5  # Base confidence
            
            # Increase confidence based on symbol type
            if symbol_type == 'import':
                confidence += 0.3  # Imports are easier to detect
            elif symbol_type == 'variable':
                confidence += 0.2
            elif symbol_type == 'function':
                confidence += 0.1
            else:  # class
                confidence += 0.0  # Classes are harder to detect
            
            # Decrease confidence for public symbols
            if not symbol.name.startswith('_'):
                confidence -= 0.2
            
            # Increase confidence if symbol is private
            if symbol.name.startswith('__'):
                confidence += 0.2
            elif symbol.name.startswith('_'):
                confidence += 0.1
            
            # Check for test-related symbols
            if 'test' in symbol.name.lower():
                confidence += 0.1
            
            return max(0.0, min(1.0, confidence))
        except Exception:
            return 0.5
    
    def _calculate_impact_score(self, symbol: Symbol) -> float:
        """Calculate the impact of removing this symbol."""
        try:
            # Base impact
            impact = 0.1
            
            # Increase impact based on dependencies
            dependencies = getattr(symbol, 'dependencies', [])
            impact += len(dependencies) * 0.1
            
            # Increase impact for public symbols
            if not symbol.name.startswith('_'):
                impact += 0.3
            
            # Increase impact for classes (they might be used dynamically)
            if isinstance(symbol, Class):
                impact += 0.2
            
            # Decrease impact for test symbols
            if 'test' in symbol.name.lower():
                impact -= 0.2
            
            return max(0.0, min(1.0, impact))
        except Exception:
            return 0.1
    
    def _get_symbol_dependencies(self, symbol: Symbol) -> List[str]:
        """Get list of symbol dependencies."""
        try:
            dependencies = getattr(symbol, 'dependencies', [])
            return [getattr(dep, 'name', str(dep)) for dep in dependencies]
        except Exception:
            return []
    
    def _has_string_references(self, symbol_name: str, import_stmt: Import) -> bool:
        """Check if symbol is referenced as a string (dynamic usage)."""
        try:
            # Get the file containing the import
            source_file = getattr(import_stmt, 'file', None)
            if not source_file:
                return False
            
            source = getattr(source_file, 'source', '')
            
            # Look for string references
            string_patterns = [
                f'"{symbol_name}"',
                f"'{symbol_name}'",
                f'getattr({symbol_name}',
                f'hasattr({symbol_name}',
                f'setattr({symbol_name}'
            ]
            
            return any(pattern in source for pattern in string_patterns)
        except Exception:
            return False


# Convenience functions
def find_dead_code(codebase: Codebase) -> List[DeadCodeItem]:
    """Find unused functions and classes."""
    detector = DeadCodeDetector(codebase)
    return detector.find_dead_code()


def find_unused_imports(codebase: Codebase) -> List[DeadCodeItem]:
    """Find unused imports."""
    detector = DeadCodeDetector(codebase)
    return detector._find_unused_imports()


def find_unused_variables(codebase: Codebase) -> List[DeadCodeItem]:
    """Find unused variables."""
    detector = DeadCodeDetector(codebase)
    return detector._find_unused_variables()


def estimate_cleanup_impact(codebase: Codebase, items: List[DeadCodeItem]) -> Dict[str, Any]:
    """Estimate removal impact."""
    detector = DeadCodeDetector(codebase)
    return detector.estimate_cleanup_impact(items)


def get_removal_plan(codebase: Codebase, items: List[DeadCodeItem]) -> CleanupPlan:
    """Generate safe removal plan."""
    detector = DeadCodeDetector(codebase)
    return detector.get_removal_plan(items)

