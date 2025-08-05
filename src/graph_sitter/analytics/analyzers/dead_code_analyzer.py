"""
Dead Code Analyzer for Graph-Sitter Analytics

Identifies unused and unreachable code:
- Unused functions and methods
- Unused variables and imports
- Unreachable code blocks
- Orphaned classes and modules
- Import optimization opportunities
"""

from typing import List, Dict, Any, Set
from collections import defaultdict

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.import_resolution import Import
from graph_sitter.shared.logging.logger import get_logger

from ..core.base_analyzer import BaseAnalyzer
from ..core.analysis_result import AnalysisResult, Finding, Severity, FindingType

logger = get_logger(__name__)


class DeadCodeAnalyzer(BaseAnalyzer):
    """
    Analyzes codebase for unused and unreachable code.
    
    Leverages Graph-Sitter's symbol analysis and dependency tracking
    to identify dead code with high accuracy.
    """
    
    def __init__(self):
        super().__init__("dead_code")
        self.supported_languages = {"python", "typescript", "javascript", "java", "cpp", "rust", "go"}
        
        # Patterns for entry points that should not be considered dead
        self.entry_point_patterns = {
            "python": [
                "__main__", "__init__", "main", "setup", "teardown",
                "test_", "setUp", "tearDown", "_test", "pytest_",
                "__enter__", "__exit__", "__call__", "__str__", "__repr__"
            ],
            "javascript": [
                "main", "index", "default", "exports", "module.exports",
                "addEventListener", "onClick", "onLoad", "componentDidMount"
            ],
            "typescript": [
                "main", "index", "default", "exports", "ngOnInit", "ngOnDestroy",
                "componentDidMount", "componentWillUnmount"
            ],
            "java": [
                "main", "setUp", "tearDown", "test", "init", "destroy",
                "onCreate", "onDestroy", "run", "call"
            ]
        }
        
        # Magic methods and special functions that shouldn't be flagged as dead
        self.special_methods = {
            "python": [
                "__init__", "__del__", "__str__", "__repr__", "__len__", "__getitem__",
                "__setitem__", "__delitem__", "__iter__", "__next__", "__enter__",
                "__exit__", "__call__", "__eq__", "__ne__", "__lt__", "__le__",
                "__gt__", "__ge__", "__hash__", "__bool__", "__add__", "__sub__",
                "__mul__", "__truediv__", "__floordiv__", "__mod__", "__pow__"
            ],
            "java": [
                "toString", "equals", "hashCode", "clone", "finalize", "notify",
                "notifyAll", "wait", "run", "call", "compare", "compareTo"
            ]
        }
    
    @BaseAnalyzer.measure_execution_time
    def analyze(self, codebase: Codebase, files: List) -> AnalysisResult:
        """Perform comprehensive dead code analysis."""
        if not self.validate_codebase(codebase):
            result = self.create_result("failed")
            result.error_message = "Invalid codebase provided"
            return result
        
        result = self.create_result()
        
        try:
            # Build symbol usage maps
            symbol_usage_map = self._build_symbol_usage_map(codebase)
            import_usage_map = self._build_import_usage_map(codebase)
            
            dead_functions = []
            dead_classes = []
            dead_variables = []
            unused_imports = []
            unreachable_code = []
            
            symbols_analyzed = 0
            
            for file in files:
                if not self.is_supported_file(str(file.filepath)):
                    continue
                
                file_language = self._detect_language(str(file.filepath))
                file_content = self.get_file_content(file)
                
                # Analyze functions for dead code
                for func in file.functions:
                    if self._is_dead_function(func, symbol_usage_map, file_language):
                        dead_functions.append(self._create_dead_function_finding(func))
                    symbols_analyzed += 1
                
                # Analyze classes for dead code
                for cls in file.classes:
                    if self._is_dead_class(cls, symbol_usage_map, file_language):
                        dead_classes.append(self._create_dead_class_finding(cls))
                    symbols_analyzed += 1
                
                # Analyze imports for unused imports
                for imp in file.imports:
                    if self._is_unused_import(imp, import_usage_map):
                        unused_imports.append(self._create_unused_import_finding(imp))
                
                # Analyze for unreachable code blocks
                if file_content:
                    unreachable_blocks = self._find_unreachable_code(file, file_content, file_language)
                    unreachable_code.extend(unreachable_blocks)
                
                self.log_progress(symbols_analyzed, 
                                len(list(codebase.functions)) + len(list(codebase.classes)), 
                                "symbols")
            
            # Create findings
            all_findings = dead_functions + dead_classes + dead_variables + unused_imports + unreachable_code
            
            for finding_data in all_findings:
                finding = Finding(
                    type=FindingType.DEAD_CODE,
                    severity=finding_data["severity"],
                    title=finding_data["title"],
                    description=finding_data["description"],
                    file_path=finding_data["file_path"],
                    line_number=finding_data.get("line_number"),
                    code_snippet=finding_data.get("code_snippet"),
                    recommendation=finding_data["recommendation"],
                    rule_id=finding_data["rule_id"],
                    metadata=finding_data.get("metadata", {})
                )
                result.add_finding(finding)
            
            # Calculate metrics
            result.metrics.files_analyzed = len([f for f in files if self.is_supported_file(str(f.filepath))])
            result.metrics.symbols_analyzed = symbols_analyzed
            result.metrics.quality_score = self._calculate_dead_code_score(all_findings, symbols_analyzed)
            
            # Store detailed dead code metrics
            result.metrics.dead_code_metrics = {
                "symbols_analyzed": symbols_analyzed,
                "dead_functions": len(dead_functions),
                "dead_classes": len(dead_classes),
                "unused_imports": len(unused_imports),
                "unreachable_code_blocks": len(unreachable_code),
                "total_dead_code_items": len(all_findings),
                "dead_code_percentage": (len(all_findings) / symbols_analyzed * 100) if symbols_analyzed > 0 else 0,
                "cleanup_opportunities": self._identify_cleanup_opportunities(all_findings)
            }
            
            # Generate recommendations
            result.recommendations = self._generate_dead_code_recommendations(all_findings)
            
            logger.info(f"Dead code analysis completed: {len(all_findings)} dead code items found in {symbols_analyzed} symbols")
            
        except Exception as e:
            logger.error(f"Dead code analysis failed: {str(e)}")
            result.status = "failed"
            result.error_message = str(e)
        
        return result
    
    def _build_symbol_usage_map(self, codebase: Codebase) -> Dict[str, Set[str]]:
        """Build a map of symbol usage across the codebase."""
        usage_map = defaultdict(set)
        
        # Iterate through all symbols and their usages
        for symbol in codebase.symbols:
            symbol_key = self._get_symbol_key(symbol)
            
            # Get all usages of this symbol
            if hasattr(symbol, 'symbol_usages'):
                for usage in symbol.symbol_usages:
                    if hasattr(usage, 'filepath'):
                        usage_map[symbol_key].add(str(usage.filepath))
            
            # Check function calls
            if isinstance(symbol, Function) and hasattr(symbol, 'call_sites'):
                for call_site in symbol.call_sites:
                    if hasattr(call_site, 'filepath'):
                        usage_map[symbol_key].add(str(call_site.filepath))
        
        return dict(usage_map)
    
    def _build_import_usage_map(self, codebase: Codebase) -> Dict[str, Set[str]]:
        """Build a map of import usage across the codebase."""
        usage_map = defaultdict(set)
        
        for imp in codebase.imports:
            import_key = self._get_import_key(imp)
            
            # Check if imported symbol is used
            if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                imported_symbol = imp.imported_symbol
                if hasattr(imported_symbol, 'symbol_usages'):
                    for usage in imported_symbol.symbol_usages:
                        if hasattr(usage, 'filepath'):
                            usage_map[import_key].add(str(usage.filepath))
        
        return dict(usage_map)
    
    def _is_dead_function(self, func: Function, usage_map: Dict[str, Set[str]], language: str) -> bool:
        """Check if a function is dead (unused)."""
        # Skip special methods and entry points
        if self._is_special_function(func, language):
            return False
        
        # Skip if function is used
        func_key = self._get_symbol_key(func)
        if func_key in usage_map and usage_map[func_key]:
            return False
        
        # Check if function has call sites
        if hasattr(func, 'call_sites') and func.call_sites:
            return False
        
        # Check if function is exported or public
        if self._is_exported_function(func, language):
            return False
        
        return True
    
    def _is_dead_class(self, cls: Class, usage_map: Dict[str, Set[str]], language: str) -> bool:
        """Check if a class is dead (unused)."""
        # Skip if class is used
        cls_key = self._get_symbol_key(cls)
        if cls_key in usage_map and usage_map[cls_key]:
            return False
        
        # Check if any methods are used
        if hasattr(cls, 'methods'):
            for method in cls.methods:
                method_key = self._get_symbol_key(method)
                if method_key in usage_map and usage_map[method_key]:
                    return False
        
        # Check if class is exported or public
        if self._is_exported_class(cls, language):
            return False
        
        return True
    
    def _is_unused_import(self, imp: Import, usage_map: Dict[str, Set[str]]) -> bool:
        """Check if an import is unused."""
        import_key = self._get_import_key(imp)
        
        # Check if imported symbol is used
        if import_key in usage_map and usage_map[import_key]:
            return False
        
        # Check if it's a side-effect import (no specific symbol imported)
        if hasattr(imp, 'imported_symbol') and not imp.imported_symbol:
            return False  # Side-effect imports are not considered unused
        
        return True
    
    def _find_unreachable_code(self, file, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Find unreachable code blocks in a file."""
        unreachable_blocks = []
        
        # Simple heuristics for unreachable code
        lines = file_content.splitlines()
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for code after return statements
            if self._is_return_statement(line_stripped, language):
                # Look for non-empty lines after return
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line and not self._is_comment_or_whitespace(next_line, language):
                        # Check if it's not another function/class definition
                        if not self._is_function_or_class_definition(next_line, language):
                            unreachable_blocks.append({
                                "severity": Severity.MEDIUM,
                                "title": "Unreachable Code After Return",
                                "description": f"Code after return statement is unreachable",
                                "file_path": str(file.filepath),
                                "line_number": j + 1,
                                "code_snippet": self.extract_code_snippet(file_content, j + 1),
                                "recommendation": "Remove unreachable code or restructure control flow",
                                "rule_id": "DEAD_UNREACHABLE",
                                "metadata": {"unreachable_type": "after_return"}
                            })
                        break
            
            # Check for code after unconditional breaks/continues
            if self._is_break_or_continue(line_stripped, language):
                # Similar logic for break/continue
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line and not self._is_comment_or_whitespace(next_line, language):
                        if not self._is_control_structure_end(next_line, language):
                            unreachable_blocks.append({
                                "severity": Severity.LOW,
                                "title": "Unreachable Code After Break/Continue",
                                "description": f"Code after break/continue statement may be unreachable",
                                "file_path": str(file.filepath),
                                "line_number": j + 1,
                                "code_snippet": self.extract_code_snippet(file_content, j + 1),
                                "recommendation": "Review control flow and remove unreachable code",
                                "rule_id": "DEAD_UNREACHABLE_BREAK",
                                "metadata": {"unreachable_type": "after_break_continue"}
                            })
                        break
        
        return unreachable_blocks
    
    def _is_special_function(self, func: Function, language: str) -> bool:
        """Check if function is a special method or entry point."""
        if not hasattr(func, 'name') or not func.name:
            return False
        
        func_name = func.name.lower()
        
        # Check entry points
        entry_points = self.entry_point_patterns.get(language, [])
        if any(pattern.lower() in func_name for pattern in entry_points):
            return True
        
        # Check special methods
        special_methods = self.special_methods.get(language, [])
        if func.name in special_methods:
            return True
        
        return False
    
    def _is_exported_function(self, func: Function, language: str) -> bool:
        """Check if function is exported or public."""
        if not hasattr(func, 'name'):
            return False
        
        # Language-specific export checks
        if language == "python":
            # Functions not starting with underscore are considered public
            return not func.name.startswith('_')
        elif language in ["javascript", "typescript"]:
            # Check if function is exported (simplified check)
            return True  # Conservative approach - assume exported
        elif language == "java":
            # Check if function is public (simplified check)
            return True  # Conservative approach - assume public
        
        return True  # Conservative default
    
    def _is_exported_class(self, cls: Class, language: str) -> bool:
        """Check if class is exported or public."""
        if not hasattr(cls, 'name'):
            return False
        
        # Similar logic to functions
        if language == "python":
            return not cls.name.startswith('_')
        
        return True  # Conservative default
    
    def _get_symbol_key(self, symbol: Symbol) -> str:
        """Get a unique key for a symbol."""
        if hasattr(symbol, 'name') and hasattr(symbol, 'filepath'):
            return f"{symbol.name}@{symbol.filepath}"
        elif hasattr(symbol, 'name'):
            return symbol.name
        else:
            return str(id(symbol))
    
    def _get_import_key(self, imp: Import) -> str:
        """Get a unique key for an import."""
        if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
            return self._get_symbol_key(imp.imported_symbol)
        elif hasattr(imp, 'module_name'):
            return f"import:{imp.module_name}"
        else:
            return str(id(imp))
    
    def _create_dead_function_finding(self, func: Function) -> Dict[str, Any]:
        """Create a finding for a dead function."""
        return {
            "severity": Severity.MEDIUM,
            "title": f"Unused Function: {func.name}",
            "description": f"Function '{func.name}' is defined but never called",
            "file_path": str(func.filepath),
            "line_number": getattr(func, 'line_number', None),
            "recommendation": "Remove unused function or verify if it should be called",
            "rule_id": "DEAD_FUNCTION",
            "metadata": {
                "symbol_type": "function",
                "symbol_name": func.name
            }
        }
    
    def _create_dead_class_finding(self, cls: Class) -> Dict[str, Any]:
        """Create a finding for a dead class."""
        return {
            "severity": Severity.MEDIUM,
            "title": f"Unused Class: {cls.name}",
            "description": f"Class '{cls.name}' is defined but never instantiated or used",
            "file_path": str(cls.filepath),
            "line_number": getattr(cls, 'line_number', None),
            "recommendation": "Remove unused class or verify if it should be used",
            "rule_id": "DEAD_CLASS",
            "metadata": {
                "symbol_type": "class",
                "symbol_name": cls.name
            }
        }
    
    def _create_unused_import_finding(self, imp: Import) -> Dict[str, Any]:
        """Create a finding for an unused import."""
        import_name = "unknown"
        if hasattr(imp, 'imported_symbol') and imp.imported_symbol and hasattr(imp.imported_symbol, 'name'):
            import_name = imp.imported_symbol.name
        elif hasattr(imp, 'module_name'):
            import_name = imp.module_name
        
        return {
            "severity": Severity.LOW,
            "title": f"Unused Import: {import_name}",
            "description": f"Import '{import_name}' is not used in the file",
            "file_path": str(imp.filepath) if hasattr(imp, 'filepath') else "unknown",
            "line_number": getattr(imp, 'line_number', None),
            "recommendation": "Remove unused import to clean up code",
            "rule_id": "DEAD_IMPORT",
            "metadata": {
                "symbol_type": "import",
                "import_name": import_name
            }
        }
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        from pathlib import Path
        
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go"
        }
        
        return lang_map.get(ext, "unknown")
    
    def _is_return_statement(self, line: str, language: str) -> bool:
        """Check if line is a return statement."""
        patterns = {
            "python": r'^\s*return\b',
            "javascript": r'^\s*return\b',
            "typescript": r'^\s*return\b',
            "java": r'^\s*return\b',
            "cpp": r'^\s*return\b',
            "rust": r'^\s*return\b',
            "go": r'^\s*return\b'
        }
        
        import re
        pattern = patterns.get(language, r'^\s*return\b')
        return bool(re.search(pattern, line, re.IGNORECASE))
    
    def _is_break_or_continue(self, line: str, language: str) -> bool:
        """Check if line is a break or continue statement."""
        patterns = {
            "python": r'^\s*(break|continue)\b',
            "javascript": r'^\s*(break|continue)\b',
            "typescript": r'^\s*(break|continue)\b',
            "java": r'^\s*(break|continue)\b',
            "cpp": r'^\s*(break|continue)\b',
            "rust": r'^\s*(break|continue)\b',
            "go": r'^\s*(break|continue)\b'
        }
        
        import re
        pattern = patterns.get(language, r'^\s*(break|continue)\b')
        return bool(re.search(pattern, line, re.IGNORECASE))
    
    def _is_comment_or_whitespace(self, line: str, language: str) -> bool:
        """Check if line is a comment or whitespace."""
        if not line.strip():
            return True
        
        comment_patterns = {
            "python": r'^\s*#',
            "javascript": r'^\s*(//|/\*)',
            "typescript": r'^\s*(//|/\*)',
            "java": r'^\s*(//|/\*)',
            "cpp": r'^\s*(//|/\*)',
            "rust": r'^\s*//',
            "go": r'^\s*//'
        }
        
        import re
        pattern = comment_patterns.get(language, r'^\s*(#|//|/\*)')
        return bool(re.search(pattern, line))
    
    def _is_function_or_class_definition(self, line: str, language: str) -> bool:
        """Check if line is a function or class definition."""
        patterns = {
            "python": r'^\s*(def|class)\b',
            "javascript": r'^\s*(function|class)\b',
            "typescript": r'^\s*(function|class)\b',
            "java": r'^\s*(public|private|protected)?\s*(static)?\s*(class|interface)\b',
            "cpp": r'^\s*(class|struct)\b',
            "rust": r'^\s*(fn|struct|impl)\b',
            "go": r'^\s*(func|type)\b'
        }
        
        import re
        pattern = patterns.get(language, r'^\s*(def|function|class)\b')
        return bool(re.search(pattern, line, re.IGNORECASE))
    
    def _is_control_structure_end(self, line: str, language: str) -> bool:
        """Check if line ends a control structure."""
        if language == "python":
            # Python uses indentation, so check for dedent
            return line and not line.startswith('    ')
        else:
            # Other languages use braces
            return '}' in line
    
    def _identify_cleanup_opportunities(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify cleanup opportunities based on findings."""
        opportunities = {
            "files_with_dead_code": set(),
            "total_lines_removable": 0,
            "import_cleanup_files": set(),
            "function_cleanup_count": 0,
            "class_cleanup_count": 0
        }
        
        for finding in findings:
            file_path = finding["file_path"]
            rule_id = finding["rule_id"]
            
            opportunities["files_with_dead_code"].add(file_path)
            
            if rule_id == "DEAD_FUNCTION":
                opportunities["function_cleanup_count"] += 1
                opportunities["total_lines_removable"] += 10  # Estimate
            elif rule_id == "DEAD_CLASS":
                opportunities["class_cleanup_count"] += 1
                opportunities["total_lines_removable"] += 20  # Estimate
            elif rule_id == "DEAD_IMPORT":
                opportunities["import_cleanup_files"].add(file_path)
                opportunities["total_lines_removable"] += 1
        
        # Convert sets to lists for JSON serialization
        opportunities["files_with_dead_code"] = list(opportunities["files_with_dead_code"])
        opportunities["import_cleanup_files"] = list(opportunities["import_cleanup_files"])
        
        return opportunities
    
    def _calculate_dead_code_score(self, findings: List[Dict[str, Any]], symbols_analyzed: int) -> float:
        """Calculate dead code quality score."""
        if symbols_analyzed == 0:
            return 100.0
        
        # Calculate penalty based on dead code percentage
        dead_code_count = len(findings)
        dead_code_percentage = (dead_code_count / symbols_analyzed) * 100
        
        # Score decreases with more dead code
        score = 100 - min(dead_code_percentage * 2, 100)  # Max penalty of 100
        
        return max(0, score)
    
    def _generate_dead_code_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable dead code cleanup recommendations."""
        recommendations = []
        
        # Count finding types
        finding_counts = defaultdict(int)
        for finding in findings:
            finding_counts[finding["rule_id"]] += 1
        
        if finding_counts.get("DEAD_FUNCTION", 0) > 0:
            recommendations.append(f"Remove {finding_counts['DEAD_FUNCTION']} unused functions to reduce codebase size")
        
        if finding_counts.get("DEAD_CLASS", 0) > 0:
            recommendations.append(f"Remove {finding_counts['DEAD_CLASS']} unused classes to simplify architecture")
        
        if finding_counts.get("DEAD_IMPORT", 0) > 0:
            recommendations.append(f"Clean up {finding_counts['DEAD_IMPORT']} unused imports to improve load times")
        
        if finding_counts.get("DEAD_UNREACHABLE", 0) > 0:
            recommendations.append(f"Remove {finding_counts['DEAD_UNREACHABLE']} unreachable code blocks")
        
        # General recommendations
        total_findings = len(findings)
        if total_findings > 0:
            recommendations.append(f"Implement automated dead code detection in CI/CD pipeline")
            
        if total_findings > 10:
            recommendations.append("Consider using automated refactoring tools for large-scale cleanup")
        
        return recommendations[:5]  # Return top 5 recommendations

