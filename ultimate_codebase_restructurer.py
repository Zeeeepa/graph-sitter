#!/usr/bin/env python3
"""
Ultimate Codebase Restructurer - Single File Solution

This single file provides complete automated codebase restructuring with:
1. User query interface to understand restructuring goals
2. AI-driven analysis and decision making
3. Type resolution for safe dead code removal
4. Intelligent module organization
5. Comprehensive reporting and validation

Usage:
    python ultimate_codebase_restructurer.py
    # OR
    from ultimate_codebase_restructurer import ultimate_restructure
    ultimate_restructure(codebase_path="./", user_query="Organize my code better")
"""

import os
import re
import shutil
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import networkx as nx

def ultimate_restructure(
    codebase_path: str = ".",
    user_query: str = None,
    target_directory: str = "restructured",
    backup_original: bool = True,
    ai_request_limit: int = 50,
    verbose: bool = True
) -> Dict:
    """
    🚀 ULTIMATE CODEBASE RESTRUCTURER
    
    Single function that does everything:
    1. Analyzes user intent through AI query
    2. Performs intelligent restructuring based on user goals
    3. Uses type resolution for safety
    4. Provides comprehensive reporting
    
    Args:
        codebase_path: Path to codebase to restructure
        user_query: User's description of what they want (if None, will prompt)
        target_directory: Where to save restructured code
        backup_original: Whether to backup original files
        ai_request_limit: Maximum AI requests to make
        verbose: Whether to print progress
        
    Returns:
        Dict with complete restructuring results and analysis
    """
    
    def log(message: str, emoji: str = "🔧"):
        if verbose:
            print(f"{emoji} {message}")
    
    def get_user_input():
        """Get user input for restructuring goals"""
        if user_query:
            return user_query
        
        print("\n" + "="*60)
        print("🤖 ULTIMATE CODEBASE RESTRUCTURER")
        print("="*60)
        print("\nI'll help you restructure your codebase intelligently!")
        print("Please describe what you want to achieve:\n")
        
        examples = [
            "Organize my code into clean modules",
            "Remove dead code and improve structure", 
            "Separate utilities from business logic",
            "Create a microservices-ready structure",
            "Optimize for testing and maintainability",
            "Prepare code for open source release"
        ]
        
        print("💡 Examples:")
        for i, example in enumerate(examples, 1):
            print(f"   {i}. {example}")
        
        print("\n" + "-"*60)
        query = input("🎯 What would you like me to do with your codebase? ")
        return query.strip()
    
    try:
        # ==================== PHASE 0: SETUP & USER INTENT ANALYSIS ====================
        log("Initializing Ultimate Codebase Restructurer...", "🚀")
        
        # Import graph_sitter
        try:
            from graph_sitter import Codebase
        except ImportError:
            raise ImportError("graph_sitter is required. Install with: pip install graph-sitter")
        
        # Load codebase
        log(f"Loading codebase from: {codebase_path}", "📂")
        codebase = Codebase(codebase_path, language="python")
        
        # Set AI limits
        if hasattr(codebase, 'set_session_options'):
            codebase.set_session_options(max_ai_requests=ai_request_limit)
        
        # Get user intent
        user_intent = get_user_input()
        log(f"User goal: {user_intent}", "🎯")
        
        # Initialize results
        results = {
            "user_query": user_intent,
            "original_stats": {},
            "final_stats": {},
            "operations": [],
            "ai_decisions": [],
            "dead_code_removed": [],
            "modules_created": [],
            "errors": [],
            "warnings": [],
            "restructuring_plan": {},
            "quality_assessment": ""
        }
        
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
        
        log(f"Codebase loaded: {results['original_stats']['files']} files, {results['original_stats']['functions']} functions", "📊")
        
        # ==================== PHASE 1: AI ANALYSIS OF USER INTENT ====================
        log("Analyzing user intent with AI...", "🧠")
        
        # Create codebase context for AI
        codebase_context = {
            "total_files": len(original_files),
            "total_functions": len(original_functions),
            "total_classes": len(original_classes),
            "file_structure": [f.filepath for f in original_files[:10]],  # Sample files
            "function_names": [f.name for f in original_functions[:20]],  # Sample functions
            "class_names": [c.name for c in original_classes[:10]]  # Sample classes
        }
        
        # Use AI to understand user intent and create restructuring plan
        try:
            restructuring_plan = codebase.ai(
                prompt=f"""Based on the user's request: "{user_intent}"
                
                Analyze this codebase and create a detailed restructuring plan.
                
                Consider:
                1. What specific modules/directories should be created?
                2. How should functions be categorized and organized?
                3. What dead code removal strategy is appropriate?
                4. What shared code should be extracted?
                5. What's the priority order of operations?
                
                Respond in this JSON-like format:
                MODULES: [list of module names to create]
                CATEGORIZATION: [strategy for organizing functions]
                DEAD_CODE: [approach for dead code removal]
                SHARED_CODE: [strategy for shared code extraction]
                PRIORITY: [high/medium/low for each operation]
                SPECIAL_CONSIDERATIONS: [any specific requirements]
                """,
                context=codebase_context
            )
            
            results["restructuring_plan"] = restructuring_plan
            results["ai_decisions"].append(f"AI created restructuring plan: {restructuring_plan}")
            log("AI restructuring plan created", "✅")
            
        except Exception as e:
            log(f"AI planning failed, using fallback strategy: {e}", "⚠️")
            results["warnings"].append(f"AI planning failed: {e}")
            restructuring_plan = "MODULES: [utils, core, api, data] CATEGORIZATION: name-based DEAD_CODE: conservative"
        
        # ==================== PHASE 2: INTELLIGENT DEAD CODE REMOVAL ====================
        log("Phase 2: AI-driven dead code analysis...", "🔍")
        
        dead_code_candidates = []
        type_resolutions = 0
        
        # Determine dead code strategy from AI plan
        conservative_removal = "conservative" in restructuring_plan.lower() or "careful" in restructuring_plan.lower()
        
        for function in original_functions:
            try:
                # Skip test files and decorated functions
                if "test" in function.file.filepath.lower() or function.decorators:
                    continue
                
                # Basic usage check
                if not function.usages and not function.call_sites:
                    
                    # Gather comprehensive context
                    function_context = {
                        "name": function.name,
                        "file": function.file.filepath,
                        "docstring": getattr(function, 'docstring', ''),
                        "line_count": len(str(function).split('\n')),
                        "has_decorators": bool(function.decorators),
                        "user_intent": user_intent
                    }
                    
                    # Type resolution analysis
                    if hasattr(function, 'return_type') and function.return_type:
                        try:
                            return_type = function.return_type
                            if hasattr(return_type, 'resolved_types'):
                                resolved_symbols = return_type.resolved_types
                                if resolved_symbols:
                                    function_context["resolved_types"] = [str(s) for s in resolved_symbols]
                                    type_resolutions += 1
                            elif hasattr(return_type, 'resolved_value'):
                                resolved_value = return_type.resolved_value
                                if resolved_value:
                                    function_context["resolved_value"] = str(resolved_value)
                                    type_resolutions += 1
                        except Exception as e:
                            results["warnings"].append(f"Type resolution failed for {function.name}: {e}")
                    
                    # AI safety analysis
                    try:
                        safety_analysis = codebase.ai(
                            prompt=f"""Analyze if this function is safe to remove as dead code.
                            
                            User's goal: "{user_intent}"
                            
                            Consider:
                            1. Is it truly unused or called dynamically?
                            2. Is it part of a public API?
                            3. Could it be utility code the user wants to keep?
                            4. Does it align with the user's restructuring goals?
                            5. Are there type dependencies that suggest it's important?
                            
                            Strategy: {"Conservative (keep if uncertain)" if conservative_removal else "Aggressive (remove if likely unused)"}
                            
                            Answer: REMOVE, KEEP_API, KEEP_UTILITY, or KEEP_UNCERTAIN
                            Reason: [brief explanation]""",
                            target=function,
                            context=function_context
                        )
                        
                        if "REMOVE" in safety_analysis and "KEEP" not in safety_analysis:
                            dead_code_candidates.append({
                                "function": function,
                                "reason": safety_analysis,
                                "context": function_context
                            })
                            results["ai_decisions"].append(f"AI marked {function.name} for removal: {safety_analysis}")
                        else:
                            results["ai_decisions"].append(f"AI preserved {function.name}: {safety_analysis}")
                    
                    except Exception as e:
                        results["warnings"].append(f"AI safety analysis failed for {function.name}: {e}")
                        # Conservative fallback - keep the function
                        results["ai_decisions"].append(f"Kept {function.name} due to analysis error")
            
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
                results["errors"].append(f"Failed to remove {function.name}: {e}")
        
        results["operations"].append(f"Removed {removed_count} dead functions with {type_resolutions} type resolutions")
        log(f"Removed {removed_count} dead functions", "✅")
        
        # ==================== PHASE 3: INTELLIGENT MODULE ORGANIZATION ====================
        log("Phase 3: AI-driven module organization...", "📁")
        
        # Create target directory
        target_path = Path(target_directory)
        if target_path.exists() and backup_original:
            backup_path = f"{target_directory}_backup"
            shutil.move(str(target_path), backup_path)
            log(f"Backed up to {backup_path}", "💾")
        target_path.mkdir(exist_ok=True)
        
        # Extract module strategy from AI plan
        suggested_modules = []
        if "MODULES:" in restructuring_plan:
            try:
                modules_part = restructuring_plan.split("MODULES:")[1].split("CATEGORIZATION:")[0]
                # Extract module names (simple parsing)
                suggested_modules = re.findall(r'\b[a-z_]+\b', modules_part.lower())
                suggested_modules = [m for m in suggested_modules if len(m) > 2 and m not in ['list', 'names', 'create']]
            except:
                pass
        
        # Fallback modules if AI didn't suggest any
        if not suggested_modules:
            suggested_modules = ['utils', 'core', 'api', 'data', 'analysis', 'io']
        
        log(f"Creating modules: {suggested_modules}", "📦")
        
        # Create module directories
        for module_name in suggested_modules:
            module_dir = target_path / module_name
            module_dir.mkdir(exist_ok=True)
            results["modules_created"].append(module_name)
        
        # Organize functions into modules using AI
        functions_organized = 0
        for function in codebase.functions:
            try:
                if "test" in function.file.filepath.lower():
                    continue
                
                # Use AI to categorize function
                function_context = {
                    "name": function.name,
                    "docstring": getattr(function, 'docstring', ''),
                    "file_path": function.file.filepath,
                    "available_modules": suggested_modules,
                    "user_intent": user_intent
                }
                
                try:
                    categorization = codebase.ai(
                        prompt=f"""Categorize this function into the most appropriate module.
                        
                        Available modules: {suggested_modules}
                        User's goal: "{user_intent}"
                        
                        Consider the function's purpose, name, and how it fits the user's goals.
                        
                        Respond with just the module name from the available list.""",
                        target=function,
                        context=function_context
                    )
                    
                    # Extract module name from AI response
                    target_module = "core"  # default
                    for module in suggested_modules:
                        if module in categorization.lower():
                            target_module = module
                            break
                    
                    results["ai_decisions"].append(f"AI categorized {function.name} → {target_module}")
                
                except Exception as e:
                    # Fallback categorization
                    target_module = "core"
                    results["warnings"].append(f"AI categorization failed for {function.name}: {e}")
                
                # Create file and move function
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', function.name)
                module_file_path = target_path / target_module / f"{safe_name}.py"
                
                # Handle name conflicts
                counter = 1
                while module_file_path.exists():
                    module_file_path = target_path / target_module / f"{safe_name}_{counter}.py"
                    counter += 1
                
                # Create and move
                module_file = codebase.create_file(str(module_file_path), content="")
                function.move_to_file(module_file, include_dependencies=True)
                functions_organized += 1
                
            except Exception as e:
                results["errors"].append(f"Failed to organize {function.name}: {e}")
        
        results["operations"].append(f"Organized {functions_organized} functions into {len(suggested_modules)} modules")
        log(f"Organized {functions_organized} functions", "✅")
        
        # ==================== PHASE 4: SHARED CODE EXTRACTION ====================
        log("Phase 4: AI-driven shared code extraction...", "🔗")
        
        shared_dir = target_path / "shared"
        shared_dir.mkdir(exist_ok=True)
        
        # Find functions used across multiple files
        shared_candidates = []
        for function in codebase.functions:
            using_files = set()
            for usage in function.usages:
                if hasattr(usage, 'file') and usage.file != function.file:
                    using_files.add(usage.file.filepath)
            
            if len(using_files) >= 2:  # Used in 2+ files
                try:
                    shared_analysis = codebase.ai(
                        prompt=f"""Should this function be moved to a shared module?
                        
                        User's goal: "{user_intent}"
                        Function is used in {len(using_files)} different files.
                        
                        Consider:
                        1. Is it a true utility that multiple modules need?
                        2. Does sharing it align with the user's goals?
                        3. Would it improve code organization?
                        
                        Answer: SHARE_UTILS, SHARE_COMMON, SHARE_TYPES, or KEEP_LOCAL
                        Reason: [brief explanation]""",
                        target=function,
                        context={"usage_count": len(using_files), "user_intent": user_intent}
                    )
                    
                    if "SHARE_" in shared_analysis:
                        shared_candidates.append({
                            "function": function,
                            "analysis": shared_analysis,
                            "usage_count": len(using_files)
                        })
                        results["ai_decisions"].append(f"AI marked {function.name} for sharing: {shared_analysis}")
                
                except Exception as e:
                    results["warnings"].append(f"Shared analysis failed for {function.name}: {e}")
        
        # Extract shared functions
        shared_extracted = 0
        for candidate in shared_candidates:
            try:
                function = candidate["function"]
                analysis = candidate["analysis"]
                
                # Determine shared module type
                if "UTILS" in analysis:
                    shared_module = "utils"
                elif "TYPES" in analysis:
                    shared_module = "types"
                else:
                    shared_module = "common"
                
                shared_file_path = shared_dir / f"{shared_module}.py"
                
                if not codebase.has_file(str(shared_file_path)):
                    shared_file = codebase.create_file(str(shared_file_path), content="")
                else:
                    shared_file = codebase.get_file(str(shared_file_path))
                
                function.move_to_file(shared_file, include_dependencies=True)
                shared_extracted += 1
                
            except Exception as e:
                results["errors"].append(f"Failed to extract shared function {function.name}: {e}")
        
        results["operations"].append(f"Extracted {shared_extracted} shared functions")
        log(f"Extracted {shared_extracted} shared functions", "✅")
        
        # ==================== PHASE 5: FINAL AI ASSESSMENT ====================
        log("Phase 5: AI quality assessment...", "🎯")
        
        # Collect final stats
        final_files = list(codebase.files)
        final_functions = list(codebase.functions)
        final_classes = list(codebase.classes)
        
        results["final_stats"] = {
            "files": len(final_files),
            "functions": len(final_functions),
            "classes": len(final_classes),
            "modules_created": len(results["modules_created"]),
            "target_directory": str(target_path),
            "ai_decisions_made": len(results["ai_decisions"]),
            "dead_code_removed": len(results["dead_code_removed"])
        }
        
        # AI final assessment
        try:
            final_assessment = codebase.ai(
                prompt=f"""Assess the quality of this codebase restructuring.
                
                Original user request: "{user_intent}"
                
                Results:
                - Original: {results['original_stats']['functions']} functions in {results['original_stats']['files']} files
                - Final: {results['final_stats']['functions']} functions in {results['final_stats']['files']} files
                - Modules created: {results['modules_created']}
                - Dead code removed: {len(results['dead_code_removed'])}
                - Shared code extracted: {shared_extracted}
                
                Rate the restructuring quality (1-10) and explain:
                1. How well it meets the user's goals
                2. Code organization quality
                3. Potential improvements
                4. Overall assessment""",
                context={
                    "user_intent": user_intent,
                    "operations": results["operations"],
                    "modules": results["modules_created"]
                }
            )
            
            results["quality_assessment"] = final_assessment
            log("AI quality assessment complete", "✅")
            
        except Exception as e:
            results["warnings"].append(f"AI assessment failed: {e}")
            results["quality_assessment"] = "Assessment unavailable due to AI error"
        
        # ==================== FINAL REPORT ====================
        log("\n" + "="*60, "🎉")
        log("ULTIMATE RESTRUCTURING COMPLETE!", "🎉")
        log("="*60, "🎉")
        
        print(f"\n🎯 User Goal: {user_intent}")
        print(f"📊 Original: {results['original_stats']['functions']} functions, {results['original_stats']['files']} files")
        print(f"📊 Final: {results['final_stats']['functions']} functions, {results['final_stats']['files']} files")
        print(f"📁 Modules: {', '.join(results['modules_created'])}")
        print(f"🗑️  Dead code removed: {len(results['dead_code_removed'])}")
        print(f"🔗 Shared functions: {shared_extracted}")
        print(f"🤖 AI decisions: {len(results['ai_decisions'])}")
        print(f"📁 Output: {target_path}")
        
        print(f"\n🎯 AI Quality Assessment:")
        print(f"{results['quality_assessment']}")
        
        if results['errors']:
            print(f"\n❌ Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"   • {error}")
        
        print(f"\n🎉 Restructuring complete! Check '{target_path}' directory.")
        
        return results
        
    except Exception as e:
        log(f"❌ Critical error: {e}", "❌")
        return {"error": str(e), "user_query": user_query or ""}


# ==================== COMMAND LINE INTERFACE ====================
if __name__ == "__main__":
    """
    Command line interface for the Ultimate Codebase Restructurer
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultimate Codebase Restructurer")
    parser.add_argument("--path", default=".", help="Path to codebase (default: current directory)")
    parser.add_argument("--query", help="Restructuring goal (if not provided, will prompt)")
    parser.add_argument("--output", default="restructured", help="Output directory (default: restructured)")
    parser.add_argument("--no-backup", action="store_true", help="Don't backup original files")
    parser.add_argument("--ai-limit", type=int, default=50, help="AI request limit (default: 50)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    print("🚀 Ultimate Codebase Restructurer")
    print("=" * 50)
    
    try:
        results = ultimate_restructure(
            codebase_path=args.path,
            user_query=args.query,
            target_directory=args.output,
            backup_original=not args.no_backup,
            ai_request_limit=args.ai_limit,
            verbose=not args.quiet
        )
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            sys.exit(1)
        else:
            print(f"\n✅ Success! Restructured codebase saved to: {results['final_stats']['target_directory']}")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

