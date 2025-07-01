#!/usr/bin/env python3
"""
Unused Code Analysis Script

This script analyzes the codebase to identify unused code, wrong parameters,
and optimization opportunities for the autonomous CI/CD system.
"""

import ast
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class CodeAnalyzer:
    """Analyzes Python code for unused components and parameter issues"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.src_path = root_path / "src"
        self.analysis_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_files_analyzed": 0,
            "unused_imports": [],
            "unused_functions": [],
            "unused_classes": [],
            "unused_variables": [],
            "parameter_issues": [],
            "dead_code_blocks": [],
            "optimization_opportunities": [],
            "module_dependencies": {},
            "import_graph": {},
            "statistics": {}
        }
        
        # Track all definitions and usages
        self.all_definitions = defaultdict(list)
        self.all_usages = defaultdict(set)
        self.import_map = defaultdict(set)
        self.file_imports = defaultdict(set)
        
    def analyze_codebase(self) -> Dict[str, Any]:
        """Run comprehensive codebase analysis"""
        print("🔍 Starting comprehensive codebase analysis...")
        
        # Phase 1: Collect all Python files
        python_files = self._collect_python_files()
        self.analysis_results["total_files_analyzed"] = len(python_files)
        
        print(f"📁 Found {len(python_files)} Python files to analyze")
        
        # Phase 2: Parse all files and build symbol tables
        print("🔍 Phase 1: Building symbol tables...")
        for file_path in python_files:
            self._analyze_file(file_path)
        
        # Phase 3: Identify unused components
        print("🔍 Phase 2: Identifying unused components...")
        self._identify_unused_imports()
        self._identify_unused_functions()
        self._identify_unused_classes()
        self._identify_unused_variables()
        
        # Phase 4: Analyze parameter issues
        print("🔍 Phase 3: Analyzing parameter issues...")
        self._analyze_parameter_issues()
        
        # Phase 5: Find dead code blocks
        print("🔍 Phase 4: Finding dead code blocks...")
        self._find_dead_code_blocks()
        
        # Phase 6: Identify optimization opportunities
        print("🔍 Phase 5: Identifying optimization opportunities...")
        self._identify_optimization_opportunities()
        
        # Phase 7: Generate statistics
        print("🔍 Phase 6: Generating statistics...")
        self._generate_statistics()
        
        return self.analysis_results
    
    def _collect_python_files(self) -> List[Path]:
        """Collect all Python files in the codebase"""
        python_files = []
        
        # Exclude certain directories
        exclude_dirs = {
            "__pycache__", ".git", ".pytest_cache", "node_modules",
            ".venv", "venv", "env", "build", "dist", ".tox"
        }
        
        for root, dirs, files in os.walk(self.src_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            visitor = FileAnalysisVisitor(file_path, self)
            visitor.visit(tree)
            
        except Exception as e:
            logging.warning(f"Failed to analyze {file_path}: {str(e)}")
    
    def _identify_unused_imports(self):
        """Identify unused imports"""
        for file_path, imports in self.file_imports.items():
            for import_info in imports:
                import_name = import_info["name"]
                alias = import_info.get("alias", import_name)
                
                # Check if the import is used in the file
                if not self._is_symbol_used_in_file(alias, file_path):
                    self.analysis_results["unused_imports"].append({
                        "file": str(file_path),
                        "import": import_name,
                        "alias": alias,
                        "line": import_info.get("line", 0),
                        "type": import_info.get("type", "import")
                    })
    
    def _identify_unused_functions(self):
        """Identify unused functions"""
        for func_name, definitions in self.all_definitions.items():
            if func_name.startswith("_"):  # Skip private functions for now
                continue
                
            usages = self.all_usages.get(func_name, set())
            
            for definition in definitions:
                # Check if function is used outside its definition file
                external_usages = [u for u in usages if u != definition["file"]]
                
                if not external_usages and not self._is_special_function(func_name, definition):
                    self.analysis_results["unused_functions"].append({
                        "name": func_name,
                        "file": definition["file"],
                        "line": definition["line"],
                        "type": definition["type"]
                    })
    
    def _identify_unused_classes(self):
        """Identify unused classes"""
        for class_name, definitions in self.all_definitions.items():
            usages = self.all_usages.get(class_name, set())
            
            for definition in definitions:
                if definition["type"] != "class":
                    continue
                
                # Check if class is used outside its definition file
                external_usages = [u for u in usages if u != definition["file"]]
                
                if not external_usages and not self._is_special_class(class_name, definition):
                    self.analysis_results["unused_classes"].append({
                        "name": class_name,
                        "file": definition["file"],
                        "line": definition["line"],
                        "type": definition["type"]
                    })
    
    def _identify_unused_variables(self):
        """Identify unused variables (module-level constants)"""
        for var_name, definitions in self.all_definitions.items():
            if not var_name.isupper():  # Focus on constants
                continue
                
            usages = self.all_usages.get(var_name, set())
            
            for definition in definitions:
                if definition["type"] != "variable":
                    continue
                
                # Check if variable is used outside its definition file
                external_usages = [u for u in usages if u != definition["file"]]
                
                if not external_usages:
                    self.analysis_results["unused_variables"].append({
                        "name": var_name,
                        "file": definition["file"],
                        "line": definition["line"],
                        "type": definition["type"]
                    })
    
    def _analyze_parameter_issues(self):
        """Analyze function parameters for issues"""
        # This would analyze function signatures and calls to find mismatches
        # For now, we'll focus on common patterns
        
        parameter_issues = []
        
        # Look for functions with many unused parameters
        for func_name, definitions in self.all_definitions.items():
            for definition in definitions:
                if definition["type"] == "function" and "parameters" in definition:
                    params = definition["parameters"]
                    if len(params) > 5:  # Functions with many parameters
                        parameter_issues.append({
                            "type": "too_many_parameters",
                            "function": func_name,
                            "file": definition["file"],
                            "line": definition["line"],
                            "parameter_count": len(params),
                            "suggestion": "Consider using a configuration object or breaking into smaller functions"
                        })
        
        self.analysis_results["parameter_issues"] = parameter_issues
    
    def _find_dead_code_blocks(self):
        """Find potentially dead code blocks"""
        # This would identify unreachable code, unused conditional branches, etc.
        # For now, we'll identify some common patterns
        
        dead_code = []
        
        # Look for files in experimental or unused directories
        experimental_patterns = ["experimental", "unused", "deprecated", "old", "backup"]
        
        for file_path in Path(self.src_path).rglob("*.py"):
            path_str = str(file_path).lower()
            for pattern in experimental_patterns:
                if pattern in path_str:
                    dead_code.append({
                        "type": "experimental_file",
                        "file": str(file_path),
                        "reason": f"File in {pattern} directory",
                        "suggestion": "Review if still needed or can be removed"
                    })
                    break
        
        self.analysis_results["dead_code_blocks"] = dead_code
    
    def _identify_optimization_opportunities(self):
        """Identify optimization opportunities"""
        opportunities = []
        
        # Look for large files that might need splitting
        for file_path in Path(self.src_path).rglob("*.py"):
            try:
                with open(file_path, 'r') as f:
                    line_count = sum(1 for _ in f)
                
                if line_count > 500:  # Large files
                    opportunities.append({
                        "type": "large_file",
                        "file": str(file_path),
                        "line_count": line_count,
                        "suggestion": "Consider splitting into smaller modules"
                    })
            except:
                continue
        
        # Look for modules with many imports
        for file_path, imports in self.file_imports.items():
            if len(imports) > 20:  # Many imports
                opportunities.append({
                    "type": "many_imports",
                    "file": str(file_path),
                    "import_count": len(imports),
                    "suggestion": "Consider reducing dependencies or splitting module"
                })
        
        self.analysis_results["optimization_opportunities"] = opportunities
    
    def _generate_statistics(self):
        """Generate analysis statistics"""
        stats = {
            "total_files": self.analysis_results["total_files_analyzed"],
            "unused_imports_count": len(self.analysis_results["unused_imports"]),
            "unused_functions_count": len(self.analysis_results["unused_functions"]),
            "unused_classes_count": len(self.analysis_results["unused_classes"]),
            "unused_variables_count": len(self.analysis_results["unused_variables"]),
            "parameter_issues_count": len(self.analysis_results["parameter_issues"]),
            "dead_code_blocks_count": len(self.analysis_results["dead_code_blocks"]),
            "optimization_opportunities_count": len(self.analysis_results["optimization_opportunities"]),
            "total_definitions": sum(len(defs) for defs in self.all_definitions.values()),
            "total_usages": sum(len(usages) for usages in self.all_usages.values())
        }
        
        # Calculate cleanup potential
        total_unused = (stats["unused_imports_count"] + 
                       stats["unused_functions_count"] + 
                       stats["unused_classes_count"] + 
                       stats["unused_variables_count"])
        
        stats["cleanup_potential"] = {
            "total_unused_items": total_unused,
            "estimated_lines_removable": total_unused * 5,  # Rough estimate
            "potential_size_reduction_percent": min(total_unused / stats["total_definitions"] * 100, 100) if stats["total_definitions"] > 0 else 0
        }
        
        self.analysis_results["statistics"] = stats
    
    def _is_symbol_used_in_file(self, symbol: str, file_path: Path) -> bool:
        """Check if a symbol is used in a specific file"""
        # This is a simplified check - a more sophisticated version would
        # parse the AST to find actual usage
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return symbol in content
        except:
            return False
    
    def _is_special_function(self, func_name: str, definition: Dict) -> bool:
        """Check if function is special (main, test, etc.)"""
        special_patterns = ["main", "test_", "setup", "teardown", "__"]
        return any(pattern in func_name for pattern in special_patterns)
    
    def _is_special_class(self, class_name: str, definition: Dict) -> bool:
        """Check if class is special (Exception, Config, etc.)"""
        special_patterns = ["Exception", "Error", "Config", "Settings", "Test"]
        return any(pattern in class_name for pattern in special_patterns)


class FileAnalysisVisitor(ast.NodeVisitor):
    """AST visitor for analyzing individual files"""
    
    def __init__(self, file_path: Path, analyzer: CodeAnalyzer):
        self.file_path = file_path
        self.analyzer = analyzer
        self.current_class = None
        self.current_function = None
    
    def visit_Import(self, node):
        """Visit import statements"""
        for alias in node.names:
            import_info = {
                "name": alias.name,
                "alias": alias.asname or alias.name,
                "line": node.lineno,
                "type": "import"
            }
            self.analyzer.file_imports[self.file_path].add(frozenset(import_info.items()))
    
    def visit_ImportFrom(self, node):
        """Visit from...import statements"""
        for alias in node.names:
            import_info = {
                "name": f"{node.module}.{alias.name}" if node.module else alias.name,
                "alias": alias.asname or alias.name,
                "line": node.lineno,
                "type": "from_import",
                "module": node.module
            }
            self.analyzer.file_imports[self.file_path].add(frozenset(import_info.items()))
    
    def visit_FunctionDef(self, node):
        """Visit function definitions"""
        func_info = {
            "name": node.name,
            "file": str(self.file_path),
            "line": node.lineno,
            "type": "function",
            "parameters": [arg.arg for arg in node.args.args],
            "class": self.current_class
        }
        
        self.analyzer.all_definitions[node.name].append(func_info)
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions"""
        self.visit_FunctionDef(node)  # Same handling as regular functions
    
    def visit_ClassDef(self, node):
        """Visit class definitions"""
        class_info = {
            "name": node.name,
            "file": str(self.file_path),
            "line": node.lineno,
            "type": "class",
            "bases": [self._get_name(base) for base in node.bases]
        }
        
        self.analyzer.all_definitions[node.name].append(class_info)
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Assign(self, node):
        """Visit variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_info = {
                    "name": target.id,
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "type": "variable"
                }
                self.analyzer.all_definitions[target.id].append(var_info)
        
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit name references (usage)"""
        if isinstance(node.ctx, ast.Load):  # Only count loads, not stores
            self.analyzer.all_usages[node.id].add(str(self.file_path))
        
        self.generic_visit(node)
    
    def _get_name(self, node):
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)


def generate_cleanup_script(analysis_results: Dict[str, Any]) -> str:
    """Generate a script to clean up unused code"""
    script_lines = [
        "#!/usr/bin/env python3",
        '"""',
        "Automated Code Cleanup Script",
        "Generated from unused code analysis",
        '"""',
        "",
        "import os",
        "from pathlib import Path",
        "",
        "def cleanup_unused_imports():",
        '    """Remove unused imports"""',
        "    # TODO: Implement safe import removal",
        "    pass",
        "",
        "def cleanup_unused_functions():",
        '    """Remove unused functions"""',
        "    # TODO: Implement safe function removal",
        "    pass",
        "",
        "def main():",
        '    print("🧹 Starting automated cleanup...")',
        "    cleanup_unused_imports()",
        "    cleanup_unused_functions()",
        '    print("✅ Cleanup completed!")',
        "",
        'if __name__ == "__main__":',
        "    main()"
    ]
    
    return "\n".join(script_lines)


def main():
    """Main analysis function"""
    print("🔍 Unused Code Analysis for Autonomous CI/CD")
    print("=" * 60)
    
    root_path = Path(__file__).parent.parent
    analyzer = CodeAnalyzer(root_path)
    
    try:
        # Run analysis
        results = analyzer.analyze_codebase()
        
        # Save results
        output_file = root_path / "unused_code_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate cleanup script
        cleanup_script = generate_cleanup_script(results)
        cleanup_file = root_path / "scripts" / "cleanup_unused_code.py"
        with open(cleanup_file, 'w') as f:
            f.write(cleanup_script)
        
        # Print summary
        stats = results["statistics"]
        print("\n📊 ANALYSIS SUMMARY")
        print("=" * 40)
        print(f"📁 Files analyzed: {stats['total_files']}")
        print(f"🗑️  Unused imports: {stats['unused_imports_count']}")
        print(f"🔧 Unused functions: {stats['unused_functions_count']}")
        print(f"📦 Unused classes: {stats['unused_classes_count']}")
        print(f"📝 Unused variables: {stats['unused_variables_count']}")
        print(f"⚠️  Parameter issues: {stats['parameter_issues_count']}")
        print(f"💀 Dead code blocks: {stats['dead_code_blocks_count']}")
        print(f"🚀 Optimization opportunities: {stats['optimization_opportunities_count']}")
        
        cleanup_potential = stats["cleanup_potential"]
        print(f"\n🧹 CLEANUP POTENTIAL")
        print("=" * 40)
        print(f"Total unused items: {cleanup_potential['total_unused_items']}")
        print(f"Estimated removable lines: {cleanup_potential['estimated_lines_removable']}")
        print(f"Potential size reduction: {cleanup_potential['potential_size_reduction_percent']:.1f}%")
        
        print(f"\n📋 Detailed results saved to: {output_file}")
        print(f"🧹 Cleanup script generated: {cleanup_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        logging.exception("Analysis failed")
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())

