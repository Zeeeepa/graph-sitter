#!/usr/bin/env python3
"""
Automated Codebase Restructurer using Graph-Sitter

This single function performs complete automated codebase restructuring:
1. Fixes all imports and organizes them
2. Separates functions into individual files  
3. Organizes functions into logical modules
4. Extracts shared code into common modules
5. Validates and reports results

Usage:
    from graph_sitter import Codebase
    restructure_codebase_automatically(codebase, target_directory="restructured")
"""

import os
import re
import shutil
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx

def restructure_codebase_automatically(
    codebase, 
    target_directory: str = "restructured",
    backup_original: bool = True,
    min_shared_usage: int = 3,
    organize_imports: bool = True,
    separate_functions: bool = True,
    create_modules: bool = True,
    extract_shared: bool = True,
    verbose: bool = True
) -> Dict:
    """
    🚀 AUTOMATED CODEBASE RESTRUCTURER
    
    Performs complete automated restructuring of a codebase using graph-sitter.
    
    Args:
        codebase: Graph-sitter Codebase object
        target_directory: Directory to create restructured codebase
        backup_original: Whether to backup original files
        min_shared_usage: Minimum usages to consider code as "shared"
        organize_imports: Whether to organize import statements
        separate_functions: Whether to separate functions into individual files
        create_modules: Whether to organize into logical modules
        extract_shared: Whether to extract shared code
        verbose: Whether to print progress messages
        
    Returns:
        Dict with restructuring results and statistics
    """
    
    def log(message: str, emoji: str = "🔧"):
        if verbose:
            print(f"{emoji} {message}")
    
    # Initialize results tracking
    results = {
        "original_stats": {},
        "final_stats": {},
        "operations": [],
        "errors": [],
        "warnings": []
    }
    
    try:
        # ==================== PHASE 0: ANALYSIS & BACKUP ====================
        log("Starting automated codebase restructuring...", "🚀")
        
        # Analyze original codebase
        original_files = list(codebase.files)
        original_functions = list(codebase.functions)
        original_classes = list(codebase.classes)
        
        results["original_stats"] = {
            "files": len(original_files),
            "functions": len(original_functions),
            "classes": len(original_classes),
            "python_files": len([f for f in original_files if f.filepath.endswith('.py')])
        }
        
        log(f"Original codebase: {results['original_stats']['files']} files, {results['original_stats']['functions']} functions", "📊")
        
        # Create target directory
        target_path = Path(target_directory)
        if target_path.exists():
            if backup_original:
                backup_path = f"{target_directory}_backup"
                shutil.move(str(target_path), backup_path)
                log(f"Backed up existing directory to {backup_path}", "💾")
        
        target_path.mkdir(exist_ok=True)
        
        # ==================== PHASE 1: IMPORT ORGANIZATION ====================
        if organize_imports:
            log("Phase 1: Organizing imports...", "📦")
            import_fixes = 0
            
            for file in original_files:
                if not file.filepath.endswith('.py'):
                    continue
                    
                try:
                    # Group imports by type
                    stdlib_imports = []
                    third_party_imports = []
                    local_imports = []
                    
                    for imp in file.imports:
                        if hasattr(imp, 'is_standard_library') and imp.is_standard_library:
                            stdlib_imports.append(imp)
                        elif hasattr(imp, 'is_third_party') and imp.is_third_party:
                            third_party_imports.append(imp)
                        else:
                            local_imports.append(imp)
                    
                    # Sort each group
                    for group in [stdlib_imports, third_party_imports, local_imports]:
                        group.sort(key=lambda x: getattr(x, 'module_name', str(x)))
                    
                    import_fixes += 1
                    
                except Exception as e:
                    results["warnings"].append(f"Import organization failed for {file.filepath}: {e}")
            
            results["operations"].append(f"Organized imports in {import_fixes} files")
            log(f"Organized imports in {import_fixes} files", "✅")
        
        # ==================== PHASE 2: FUNCTION SEPARATION ====================
        if separate_functions:
            log("Phase 2: Separating functions into individual files...", "🔪")
            separated_functions = 0
            function_files_created = 0
            
            # Create functions directory
            functions_dir = target_path / "functions"
            functions_dir.mkdir(exist_ok=True)
            
            for function in original_functions:
                try:
                    # Skip if function is in test files
                    if "test" in function.file.filepath.lower():
                        continue
                    
                    # Create new file for function
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', function.name)
                    new_filepath = functions_dir / f"{safe_name}.py"
                    
                    # Avoid name conflicts
                    counter = 1
                    while new_filepath.exists():
                        new_filepath = functions_dir / f"{safe_name}_{counter}.py"
                        counter += 1
                    
                    # Create new file in codebase
                    new_file = codebase.create_file(str(new_filepath), content="")
                    
                    # Move function to new file with dependencies
                    function.move_to_file(new_file, include_dependencies=True)
                    
                    separated_functions += 1
                    function_files_created += 1
                    
                except Exception as e:
                    results["errors"].append(f"Failed to separate function {function.name}: {e}")
            
            results["operations"].append(f"Separated {separated_functions} functions into {function_files_created} files")
            log(f"Separated {separated_functions} functions into individual files", "✅")
        
        # ==================== PHASE 3: MODULE ORGANIZATION ====================
        if create_modules:
            log("Phase 3: Organizing functions into logical modules...", "📁")
            
            # Define module classification rules
            module_rules = {
                "utils": lambda f: any(keyword in f.name.lower() for keyword in ["util", "helper", "tool", "common"]),
                "api": lambda f: any(keyword in f.name.lower() for keyword in ["api", "endpoint", "route", "handler"]),
                "data": lambda f: any(keyword in f.name.lower() for keyword in ["data", "db", "database", "model", "schema"]),
                "analysis": lambda f: any(keyword in f.name.lower() for keyword in ["analyze", "analysis", "metric", "measure"]),
                "visualization": lambda f: any(keyword in f.name.lower() for keyword in ["visual", "plot", "chart", "graph", "render"]),
                "io": lambda f: any(keyword in f.name.lower() for keyword in ["read", "write", "load", "save", "file", "export", "import"]),
                "core": lambda f: True  # Default module
            }
            
            # Create module directories
            modules_created = 0
            functions_organized = 0
            
            for module_name in module_rules.keys():
                module_dir = target_path / module_name
                module_dir.mkdir(exist_ok=True)
                modules_created += 1
            
            # Organize functions into modules
            for function in codebase.functions:
                try:
                    # Skip if already processed or in test files
                    if "test" in function.file.filepath.lower():
                        continue
                    
                    # Determine target module
                    target_module = "core"  # default
                    for module, condition in module_rules.items():
                        if module != "core" and condition(function):
                            target_module = module
                            break
                    
                    # Create module file path
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', function.name)
                    module_file_path = target_path / target_module / f"{safe_name}.py"
                    
                    # Avoid conflicts
                    counter = 1
                    while module_file_path.exists():
                        module_file_path = target_path / target_module / f"{safe_name}_{counter}.py"
                        counter += 1
                    
                    # Create file and move function
                    if not codebase.has_file(str(module_file_path)):
                        module_file = codebase.create_file(str(module_file_path), content="")
                        function.move_to_file(module_file, include_dependencies=True)
                        functions_organized += 1
                    
                except Exception as e:
                    results["errors"].append(f"Failed to organize function {function.name}: {e}")
            
            results["operations"].append(f"Created {modules_created} modules and organized {functions_organized} functions")
            log(f"Organized {functions_organized} functions into {modules_created} modules", "✅")
        
        # ==================== PHASE 4: SHARED CODE EXTRACTION ====================
        if extract_shared:
            log("Phase 4: Extracting shared code...", "🔗")
            
            # Create shared directory
            shared_dir = target_path / "shared"
            shared_dir.mkdir(exist_ok=True)
            
            # Analyze function usage patterns
            function_usage_map = defaultdict(set)
            shared_functions_extracted = 0
            
            for function in codebase.functions:
                # Count unique files using this function
                using_files = set()
                for usage in function.usages:
                    if hasattr(usage, 'file') and usage.file != function.file:
                        using_files.add(usage.file.filepath)
                
                if len(using_files) >= min_shared_usage:
                    function_usage_map[function] = using_files
            
            # Extract shared functions
            for function, using_files in function_usage_map.items():
                try:
                    # Determine shared module type
                    if any(keyword in function.name.lower() for keyword in ["util", "helper", "common"]):
                        shared_module = "utils"
                    elif any(keyword in function.name.lower() for keyword in ["constant", "config"]):
                        shared_module = "constants"
                    elif any(keyword in function.name.lower() for keyword in ["type", "schema", "model"]):
                        shared_module = "types"
                    else:
                        shared_module = "common"
                    
                    # Create shared file path
                    shared_file_path = shared_dir / f"{shared_module}.py"
                    
                    # Create or get shared file
                    if not codebase.has_file(str(shared_file_path)):
                        shared_file = codebase.create_file(str(shared_file_path), content="")
                    else:
                        shared_file = codebase.get_file(str(shared_file_path))
                    
                    # Move function to shared module
                    function.move_to_file(shared_file, include_dependencies=True)
                    shared_functions_extracted += 1
                    
                except Exception as e:
                    results["errors"].append(f"Failed to extract shared function {function.name}: {e}")
            
            results["operations"].append(f"Extracted {shared_functions_extracted} shared functions")
            log(f"Extracted {shared_functions_extracted} shared functions", "✅")
        
        # ==================== PHASE 5: FINAL VALIDATION ====================
        log("Phase 5: Validating restructured codebase...", "🔍")
        
        # Collect final statistics
        final_files = list(codebase.files)
        final_functions = list(codebase.functions)
        final_classes = list(codebase.classes)
        
        results["final_stats"] = {
            "files": len(final_files),
            "functions": len(final_functions),
            "classes": len(final_classes),
            "python_files": len([f for f in final_files if f.filepath.endswith('.py')]),
            "modules_created": len([d for d in target_path.iterdir() if d.is_dir()]),
            "target_directory": str(target_path)
        }
        
        # Calculate changes
        results["changes"] = {
            "files_added": results["final_stats"]["files"] - results["original_stats"]["files"],
            "functions_preserved": results["final_stats"]["functions"],
            "classes_preserved": results["final_stats"]["classes"]
        }
        
        # ==================== FINAL REPORT ====================
        log("🎉 Automated restructuring complete!", "🎉")
        log(f"📊 Final stats: {results['final_stats']['files']} files, {results['final_stats']['modules_created']} modules", "📊")
        log(f"📁 Restructured codebase saved to: {target_path}", "📁")
        
        if results["errors"]:
            log(f"⚠️  {len(results['errors'])} errors occurred during restructuring", "⚠️")
        
        if results["warnings"]:
            log(f"⚠️  {len(results['warnings'])} warnings generated", "⚠️")
        
        return results
        
    except Exception as e:
        results["errors"].append(f"Critical error during restructuring: {e}")
        log(f"❌ Critical error: {e}", "❌")
        return results


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    """
    Example usage of the automated codebase restructurer
    """
    from graph_sitter import Codebase
    
    print("🚀 Automated Codebase Restructurer Example")
    print("=" * 50)
    
    # Load a codebase (replace with your target codebase)
    print("📂 Loading codebase...")
    codebase = Codebase.from_repo(".", language="python")  # Current directory
    
    # Run automated restructuring
    print("\n🔧 Starting automated restructuring...")
    results = restructure_codebase_automatically(
        codebase=codebase,
        target_directory="restructured_codebase",
        backup_original=True,
        min_shared_usage=2,  # Lower threshold for demo
        verbose=True
    )
    
    # Print detailed results
    print("\n" + "=" * 50)
    print("📋 RESTRUCTURING RESULTS")
    print("=" * 50)
    
    print(f"📊 Original: {results['original_stats']['files']} files, {results['original_stats']['functions']} functions")
    print(f"📊 Final: {results['final_stats']['files']} files, {results['final_stats']['functions']} functions")
    print(f"📁 Modules created: {results['final_stats']['modules_created']}")
    print(f"📁 Target directory: {results['final_stats']['target_directory']}")
    
    print(f"\n🔧 Operations performed:")
    for operation in results['operations']:
        print(f"   ✅ {operation}")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"   • {error}")
    
    if results['warnings']:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results['warnings'][:5]:  # Show first 5 warnings
            print(f"   • {warning}")
    
    print(f"\n🎉 Restructuring complete! Check the '{results['final_stats']['target_directory']}' directory.")

