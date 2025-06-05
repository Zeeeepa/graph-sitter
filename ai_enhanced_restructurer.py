#!/usr/bin/env python3
"""
AI-Enhanced Codebase Restructurer using Graph-Sitter + codebase.ai

This enhanced version uses AI to make smarter restructuring decisions:
1. AI-driven module naming and organization
2. Intelligent dead code analysis with type resolution
3. Context-aware refactoring decisions
4. Safe dependency resolution before code removal

Usage:
    from graph_sitter import Codebase
    ai_restructure_codebase(codebase, target_directory="ai_restructured")
"""

import os
import re
import shutil
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import networkx as nx

def ai_restructure_codebase(
    codebase, 
    target_directory: str = "ai_restructured",
    backup_original: bool = True,
    min_shared_usage: int = 3,
    use_ai_naming: bool = True,
    safe_dead_code_removal: bool = True,
    ai_request_limit: int = 100,
    verbose: bool = True
) -> Dict:
    """
    🤖 AI-ENHANCED CODEBASE RESTRUCTURER
    
    Uses codebase.ai for intelligent restructuring decisions and type resolution
    for safe dead code removal.
    
    Args:
        codebase: Graph-sitter Codebase object
        target_directory: Directory to create restructured codebase
        backup_original: Whether to backup original files
        min_shared_usage: Minimum usages to consider code as "shared"
        use_ai_naming: Whether to use AI for module naming
        safe_dead_code_removal: Whether to use type resolution for safe removal
        ai_request_limit: Maximum AI requests to make
        verbose: Whether to print progress messages
        
    Returns:
        Dict with restructuring results and statistics
    """
    
    def log(message: str, emoji: str = "🤖"):
        if verbose:
            print(f"{emoji} {message}")
    
    # Set AI request limits
    if hasattr(codebase, 'set_session_options'):
        codebase.set_session_options(max_ai_requests=ai_request_limit)
    
    # Initialize results tracking
    results = {
        "original_stats": {},
        "final_stats": {},
        "operations": [],
        "errors": [],
        "warnings": [],
        "ai_decisions": [],
        "dead_code_removed": [],
        "type_resolutions": []
    }
    
    try:
        # ==================== PHASE 0: ANALYSIS & BACKUP ====================
        log("Starting AI-enhanced codebase restructuring...", "🚀")
        
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
        
        # ==================== PHASE 1: AI-DRIVEN DEAD CODE ANALYSIS ====================
        if safe_dead_code_removal:
            log("Phase 1: AI-driven dead code analysis with type resolution...", "🔍")
            dead_code_candidates = []
            type_resolutions = 0
            
            for function in original_functions:
                try:
                    # Skip test files and decorated functions
                    if "test" in function.file.filepath.lower() or function.decorators:
                        continue
                    
                    # Analyze function usage with type resolution
                    usage_context = {
                        "call_sites": list(function.call_sites),
                        "usages": list(function.usages),
                        "dependencies": list(function.dependencies) if hasattr(function, 'dependencies') else [],
                        "parent": function.parent if hasattr(function, 'parent') else None,
                        "file_path": function.file.filepath
                    }
                    
                    # Resolve return type if available
                    if hasattr(function, 'return_type') and function.return_type:
                        try:
                            return_type = function.return_type
                            if hasattr(return_type, 'resolved_value'):
                                resolved_types = return_type.resolved_value
                                usage_context["return_type_resolved"] = str(resolved_types)
                                type_resolutions += 1
                            elif hasattr(return_type, 'resolved_types'):
                                resolved_symbols = return_type.resolved_types
                                usage_context["return_type_symbols"] = [str(s) for s in resolved_symbols] if resolved_symbols else []
                                type_resolutions += 1
                        except Exception as e:
                            results["warnings"].append(f"Type resolution failed for {function.name}: {e}")
                    
                    # Use AI to determine if function is truly dead code
                    if not function.usages and not function.call_sites:
                        ai_analysis = codebase.ai(
                            prompt="""Analyze this function to determine if it's safe to remove as dead code.
                            Consider:
                            1. Is it truly unused or might it be called dynamically?
                            2. Is it part of a public API that external code might use?
                            3. Is it a utility function that might be needed later?
                            4. Does it have side effects or register itself somehow?
                            
                            Answer with: SAFE_TO_REMOVE, KEEP_UTILITY, KEEP_API, or KEEP_DYNAMIC
                            Then explain your reasoning.""",
                            target=function,
                            context=usage_context
                        )
                        
                        if "SAFE_TO_REMOVE" in ai_analysis:
                            dead_code_candidates.append({
                                "function": function,
                                "reason": ai_analysis,
                                "context": usage_context
                            })
                            results["ai_decisions"].append(f"AI marked {function.name} for removal: {ai_analysis}")
                        else:
                            results["ai_decisions"].append(f"AI kept {function.name}: {ai_analysis}")
                
                except Exception as e:
                    results["errors"].append(f"Dead code analysis failed for {function.name}: {e}")
            
            # Remove AI-approved dead code
            removed_count = 0
            for candidate in dead_code_candidates:
                try:
                    function = candidate["function"]
                    function.remove()
                    removed_count += 1
                    results["dead_code_removed"].append({
                        "name": function.name,
                        "reason": candidate["reason"],
                        "file": function.file.filepath
                    })
                except Exception as e:
                    results["errors"].append(f"Failed to remove dead function {function.name}: {e}")
            
            results["operations"].append(f"AI-analyzed and removed {removed_count} dead functions with {type_resolutions} type resolutions")
            log(f"Removed {removed_count} dead functions after AI analysis", "✅")
        
        # ==================== PHASE 2: AI-DRIVEN MODULE ORGANIZATION ====================
        if use_ai_naming:
            log("Phase 2: AI-driven module organization...", "🧠")
            
            # Group functions by similarity for AI analysis
            function_groups = defaultdict(list)
            
            # First, group functions by basic patterns
            for function in codebase.functions:
                if "test" in function.file.filepath.lower():
                    continue
                
                # Get function context for AI analysis
                func_context = {
                    "name": function.name,
                    "docstring": function.docstring if hasattr(function, 'docstring') else "",
                    "file_path": function.file.filepath,
                    "dependencies": [str(d) for d in function.dependencies] if hasattr(function, 'dependencies') else [],
                    "call_sites_count": len(list(function.call_sites)),
                    "usages_count": len(list(function.usages))
                }
                
                # Use AI to categorize function
                try:
                    ai_category = codebase.ai(
                        prompt="""Analyze this function and categorize it into one of these modules:
                        - UTILS: Helper functions, utilities, common tools
                        - API: Web endpoints, request handlers, API-related
                        - DATA: Database operations, data models, schemas
                        - ANALYSIS: Analytics, metrics, measurements, calculations
                        - VISUALIZATION: Plotting, charting, rendering, UI
                        - IO: File operations, reading, writing, import/export
                        - CORE: Core business logic, main functionality
                        - VALIDATION: Input validation, data checking
                        - CONFIGURATION: Settings, config management
                        - TESTING: Test utilities, mocks, fixtures
                        
                        Respond with just the category name and a brief reason.
                        Format: CATEGORY: reason""",
                        target=function,
                        context=func_context
                    )
                    
                    # Extract category from AI response
                    category = "CORE"  # default
                    if ":" in ai_category:
                        category_part = ai_category.split(":")[0].strip()
                        if category_part in ["UTILS", "API", "DATA", "ANALYSIS", "VISUALIZATION", "IO", "CORE", "VALIDATION", "CONFIGURATION", "TESTING"]:
                            category = category_part
                    
                    function_groups[category.lower()].append({
                        "function": function,
                        "ai_reason": ai_category,
                        "context": func_context
                    })
                    
                    results["ai_decisions"].append(f"AI categorized {function.name} as {category}: {ai_category}")
                
                except Exception as e:
                    # Fallback to rule-based categorization
                    function_groups["core"].append({
                        "function": function,
                        "ai_reason": f"Fallback categorization due to error: {e}",
                        "context": func_context
                    })
                    results["warnings"].append(f"AI categorization failed for {function.name}, using fallback: {e}")
            
            # Create AI-suggested module structure
            modules_created = 0
            functions_organized = 0
            
            for category, func_list in function_groups.items():
                if not func_list:
                    continue
                
                # Create module directory
                module_dir = target_path / category
                module_dir.mkdir(exist_ok=True)
                modules_created += 1
                
                # Use AI to suggest better module names for each category
                try:
                    if len(func_list) > 1:
                        sample_functions = func_list[:3]  # Sample for AI analysis
                        ai_module_name = codebase.ai(
                            prompt=f"""Given these functions that were categorized as '{category}', suggest a better, more specific module name.
                            Consider the actual functionality and provide a concise, descriptive name.
                            Respond with just the module name (lowercase, underscore_separated).""",
                            context={
                                "category": category,
                                "functions": [f["function"].name for f in sample_functions],
                                "sample_code": [str(f["function"]) for f in sample_functions[:1]]
                            }
                        )
                        
                        # Clean AI suggestion
                        suggested_name = re.sub(r'[^a-z0-9_]', '', ai_module_name.lower().strip())
                        if suggested_name and len(suggested_name) > 2:
                            # Rename directory if AI suggests better name
                            new_module_dir = target_path / suggested_name
                            if not new_module_dir.exists():
                                module_dir.rename(new_module_dir)
                                module_dir = new_module_dir
                                results["ai_decisions"].append(f"AI renamed module '{category}' to '{suggested_name}'")
                
                except Exception as e:
                    results["warnings"].append(f"AI module naming failed for {category}: {e}")
                
                # Organize functions into the module
                for func_data in func_list:
                    try:
                        function = func_data["function"]
                        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', function.name)
                        module_file_path = module_dir / f"{safe_name}.py"
                        
                        # Avoid conflicts
                        counter = 1
                        while module_file_path.exists():
                            module_file_path = module_dir / f"{safe_name}_{counter}.py"
                            counter += 1
                        
                        # Create file and move function
                        module_file = codebase.create_file(str(module_file_path), content="")
                        function.move_to_file(module_file, include_dependencies=True)
                        functions_organized += 1
                        
                    except Exception as e:
                        results["errors"].append(f"Failed to organize function {function.name}: {e}")
            
            results["operations"].append(f"AI-organized {functions_organized} functions into {modules_created} intelligent modules")
            log(f"AI-organized {functions_organized} functions into {modules_created} modules", "✅")
        
        # ==================== PHASE 3: INTELLIGENT SHARED CODE EXTRACTION ====================
        log("Phase 3: AI-driven shared code extraction...", "🔗")
        
        # Create shared directory
        shared_dir = target_path / "shared"
        shared_dir.mkdir(exist_ok=True)
        
        # Analyze function usage patterns with AI
        shared_candidates = []
        
        for function in codebase.functions:
            try:
                # Count unique files using this function
                using_files = set()
                for usage in function.usages:
                    if hasattr(usage, 'file') and usage.file != function.file:
                        using_files.add(usage.file.filepath)
                
                if len(using_files) >= min_shared_usage:
                    # Use AI to determine if function should be shared
                    usage_context = {
                        "function_name": function.name,
                        "usage_count": len(using_files),
                        "using_files": list(using_files),
                        "dependencies": [str(d) for d in function.dependencies] if hasattr(function, 'dependencies') else []
                    }
                    
                    ai_shared_analysis = codebase.ai(
                        prompt="""Analyze this function to determine if it should be extracted to a shared module.
                        Consider:
                        1. Is it a true utility that multiple modules need?
                        2. Is it stable and unlikely to change frequently?
                        3. Does it have minimal dependencies?
                        4. Would sharing it improve code organization?
                        
                        Suggest the best shared module type:
                        - UTILS: General utilities and helpers
                        - CONSTANTS: Configuration and constant values
                        - TYPES: Type definitions and schemas
                        - COMMON: Common business logic
                        - SKIP: Don't share this function
                        
                        Format: MODULE_TYPE: reason""",
                        target=function,
                        context=usage_context
                    )
                    
                    if "SKIP" not in ai_shared_analysis:
                        shared_candidates.append({
                            "function": function,
                            "ai_analysis": ai_shared_analysis,
                            "usage_context": usage_context
                        })
                        results["ai_decisions"].append(f"AI marked {function.name} for sharing: {ai_shared_analysis}")
            
            except Exception as e:
                results["errors"].append(f"Shared code analysis failed for {function.name}: {e}")
        
        # Extract AI-approved shared functions
        shared_extracted = 0
        for candidate in shared_candidates:
            try:
                function = candidate["function"]
                ai_analysis = candidate["ai_analysis"]
                
                # Determine shared module from AI analysis
                shared_module = "common"  # default
                if "UTILS:" in ai_analysis:
                    shared_module = "utils"
                elif "CONSTANTS:" in ai_analysis:
                    shared_module = "constants"
                elif "TYPES:" in ai_analysis:
                    shared_module = "types"
                elif "COMMON:" in ai_analysis:
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
                shared_extracted += 1
                
            except Exception as e:
                results["errors"].append(f"Failed to extract shared function {function.name}: {e}")
        
        results["operations"].append(f"AI-extracted {shared_extracted} functions to shared modules")
        log(f"AI-extracted {shared_extracted} shared functions", "✅")
        
        # ==================== PHASE 4: FINAL VALIDATION & AI REVIEW ====================
        log("Phase 4: AI validation of restructured codebase...", "🔍")
        
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
            "target_directory": str(target_path),
            "ai_decisions_made": len(results["ai_decisions"]),
            "dead_code_removed": len(results["dead_code_removed"]),
            "type_resolutions": len(results["type_resolutions"])
        }
        
        # AI-powered final assessment
        try:
            final_assessment = codebase.ai(
                prompt="""Review this codebase restructuring and provide a quality assessment.
                Consider:
                1. Module organization and naming
                2. Code separation and cohesion
                3. Potential issues or improvements
                4. Overall structure quality (1-10 scale)
                
                Provide a brief assessment and quality score.""",
                context={
                    "original_stats": results["original_stats"],
                    "final_stats": results["final_stats"],
                    "operations": results["operations"],
                    "modules": [d.name for d in target_path.iterdir() if d.is_dir()]
                }
            )
            results["ai_assessment"] = final_assessment
            log(f"AI Assessment: {final_assessment}", "🎯")
        except Exception as e:
            results["warnings"].append(f"AI final assessment failed: {e}")
        
        # ==================== FINAL REPORT ====================
        log("🎉 AI-enhanced restructuring complete!", "🎉")
        log(f"📊 Final stats: {results['final_stats']['files']} files, {results['final_stats']['modules_created']} modules", "📊")
        log(f"🤖 AI decisions: {results['final_stats']['ai_decisions_made']}, Dead code removed: {results['final_stats']['dead_code_removed']}", "🤖")
        log(f"📁 Restructured codebase saved to: {target_path}", "📁")
        
        if results["errors"]:
            log(f"⚠️  {len(results['errors'])} errors occurred during restructuring", "⚠️")
        
        if results["warnings"]:
            log(f"⚠️  {len(results['warnings'])} warnings generated", "⚠️")
        
        return results
        
    except Exception as e:
        results["errors"].append(f"Critical error during AI restructuring: {e}")
        log(f"❌ Critical error: {e}", "❌")
        return results


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    """
    Example usage of the AI-enhanced codebase restructurer
    """
    from graph_sitter import Codebase
    
    print("🤖 AI-Enhanced Codebase Restructurer Example")
    print("=" * 60)
    
    # Load a codebase
    print("📂 Loading codebase...")
    codebase = Codebase.from_repo(".", language="python")
    
    # Run AI-enhanced restructuring
    print("\n🤖 Starting AI-enhanced restructuring...")
    results = ai_restructure_codebase(
        codebase=codebase,
        target_directory="ai_restructured_codebase",
        backup_original=True,
        min_shared_usage=2,
        use_ai_naming=True,
        safe_dead_code_removal=True,
        ai_request_limit=50,  # Limit for demo
        verbose=True
    )
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("🤖 AI-ENHANCED RESTRUCTURING RESULTS")
    print("=" * 60)
    
    print(f"📊 Original: {results['original_stats']['files']} files, {results['original_stats']['functions']} functions")
    print(f"📊 Final: {results['final_stats']['files']} files, {results['final_stats']['functions']} functions")
    print(f"🤖 AI Decisions: {results['final_stats']['ai_decisions_made']}")
    print(f"🗑️  Dead Code Removed: {results['final_stats']['dead_code_removed']}")
    print(f"📁 Modules: {results['final_stats']['modules_created']}")
    print(f"📁 Target: {results['final_stats']['target_directory']}")
    
    print(f"\n🔧 Operations performed:")
    for operation in results['operations']:
        print(f"   ✅ {operation}")
    
    if "ai_assessment" in results:
        print(f"\n🎯 AI Quality Assessment:")
        print(f"   {results['ai_assessment']}")
    
    print(f"\n🤖 Sample AI Decisions:")
    for decision in results['ai_decisions'][:5]:
        print(f"   • {decision}")
    
    if results['dead_code_removed']:
        print(f"\n🗑️  Dead Code Removed:")
        for removed in results['dead_code_removed'][:3]:
            print(f"   • {removed['name']} from {removed['file']}")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors'][:3]:
            print(f"   • {error}")
    
    print(f"\n🎉 AI-enhanced restructuring complete! Check '{results['final_stats']['target_directory']}'")

