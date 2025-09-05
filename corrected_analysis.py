#!/usr/bin/env python3
"""
Corrected Comprehensive Analysis
Fixes: 1) Project tree generation, 2) Proper entry point detection, 3) Full error list display
"""

import os
import json
from pathlib import Path
from collections import defaultdict, Counter

def load_error_analysis() -> dict:
    """Load the actual error analysis results"""
    if os.path.exists("analysis_results.json"):
        with open("analysis_results.json", "r") as f:
            return json.load(f)
    return {}

def load_detailed_errors() -> list:
    """Load detailed error list from error_list.txt"""
    errors = []
    if os.path.exists("error_list.txt"):
        with open("error_list.txt", "r") as f:
            content = f.read()
            
        # Parse the error list format
        lines = content.split('\n')
        current_error = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('📁 File:'):
                current_error['file'] = line.replace('📁 File:', '').strip()
            elif line.startswith('📍 Line:'):
                current_error['line'] = line.replace('📍 Line:', '').strip()
            elif line.startswith('🔧 Function:'):
                current_error['function'] = line.replace('🔧 Function:', '').strip()
            elif line.startswith('💡 Fix:'):
                current_error['fix'] = line.replace('💡 Fix:', '').strip()
                # End of error entry
                if current_error:
                    errors.append(current_error.copy())
                    current_error = {}
    
    return errors

def generate_project_tree_with_issues() -> str:
    """Generate proper project tree with issue counts"""
    
    # Load error data from JSON (has file counts)
    error_data = load_error_analysis()
    file_errors = error_data.get("statistics", {}).get("by_file", {})
    
    # Build directory structure
    tree_structure = {}
    
    for file_path, error_count in file_errors.items():
        parts = file_path.split("/")
        current = tree_structure
        
        # Build nested structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # It's a file
                current[part] = {"type": "file", "errors": error_count}
            else:  # It's a directory
                if part not in current:
                    current[part] = {"type": "dir", "children": {}, "total_errors": 0}
                current[part]["total_errors"] = current[part].get("total_errors", 0) + error_count
                current = current[part]["children"]
    
    def format_tree(structure, prefix="", is_last=True):
        """Format the tree structure"""
        lines = []
        items = list(structure.items())
        
        for i, (name, data) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            connector = "└── " if is_last_item else "├── "
            
            if data["type"] == "dir":
                total_errors = data.get("total_errors", 0)
                if total_errors >= 10:
                    error_badge = f" [⚠️ Critical: {total_errors}]"
                elif total_errors >= 5:
                    error_badge = f" [👉 Major: {total_errors}]"
                elif total_errors > 0:
                    error_badge = f" [🔍 Minor: {total_errors}]"
                else:
                    error_badge = ""
                
                lines.append(f"{prefix}{connector}📁 {name}/{error_badge}")
                
                # Add children
                extension = "    " if is_last_item else "│   "
                lines.extend(format_tree(data["children"], prefix + extension, True))
                
            else:  # file
                error_count = data.get("errors", 0)
                if error_count >= 5:
                    error_badge = f" [⚠️ Critical: {error_count}]"
                elif error_count >= 3:
                    error_badge = f" [👉 Major: {error_count}]"
                elif error_count > 0:
                    error_badge = f" [🔍 Minor: {error_count}]"
                else:
                    error_badge = ""
                
                icon = "🐍" if name.endswith('.py') else "📄"
                lines.append(f"{prefix}{connector}{icon} {name}{error_badge}")
        
        return lines
    
    # Generate tree
    tree_lines = ["graph-sitter/"]
    tree_lines.extend(format_tree(tree_structure))
    
    return "\n".join(tree_lines)

def identify_real_entry_points() -> list:
    """Identify real entry points based on usage patterns, not complexity"""
    
    # Load comprehensive analysis
    if os.path.exists("comprehensive_analysis_results.json"):
        with open("comprehensive_analysis_results.json", "r") as f:
            data = json.load(f)
    else:
        return []
    
    components = data.get("components", [])
    
    # Real entry points are components that:
    # 1. Are used by many other components (high dependents count)
    # 2. Have names suggesting they're main interfaces
    # 3. Are in core/main directories
    
    entry_points = []
    
    for comp in components:
        name = comp.get("name", "")
        file_path = comp.get("file_path", "")
        dependents = comp.get("dependents", [])
        comp_type = comp.get("component_type", "")
        
        # Check if it's a real entry point
        is_entry = False
        reason = ""
        
        # High usage indicates entry point
        if len(dependents) > 10:
            is_entry = True
            reason = f"Used by {len(dependents)} components"
        
        # Core classes that are likely entry points
        entry_names = ["Codebase", "Parser", "SourceFile", "CodebaseContext", "Editable"]
        if name in entry_names:
            is_entry = True
            reason = "Core framework class"
        
        # Main/CLI files
        if "main" in file_path.lower() or "cli" in file_path.lower() or "__main__" in file_path:
            is_entry = True
            reason = "Main/CLI entry point"
        
        # Files in core directories
        if "core/" in file_path and comp_type == "Class":
            if len(dependents) > 5:  # Lower threshold for core classes
                is_entry = True
                reason = "Core class with dependencies"
        
        if is_entry:
            entry_points.append({
                "name": name,
                "type": comp_type,
                "file": file_path,
                "dependents": len(dependents),
                "reason": reason
            })
    
    # Sort by dependents count (most used first)
    entry_points.sort(key=lambda x: x["dependents"], reverse=True)
    
    return entry_points[:15]  # Top 15 real entry points

def get_full_error_list() -> dict:
    """Get the complete list of missing function errors"""
    
    # Load detailed errors from the text file
    errors = load_detailed_errors()
    
    # Group errors by function name for better analysis
    error_groups = defaultdict(list)
    
    for error in errors:
        func_name = error.get("function", "unknown")
        error_groups[func_name].append(error)
    
    return error_groups

def generate_corrected_report():
    """Generate the corrected comprehensive report"""
    
    # Load data
    error_data = load_error_analysis()
    detailed_errors = load_detailed_errors()
    
    # Generate components
    project_tree = generate_project_tree_with_issues()
    entry_points = identify_real_entry_points()
    error_groups = get_full_error_list()
    
    # Count totals
    total_errors = error_data.get("statistics", {}).get("total_errors", 0)
    file_errors = error_data.get("statistics", {}).get("by_file", {})
    total_files_with_errors = len(file_errors)
    
    report = []
    
    # Header
    report.append("=" * 80)
    report.append("🎯 CORRECTED COMPREHENSIVE ARCHITECTURAL ANALYSIS")
    report.append("Graph-Sitter Codebase - Fixed Analysis")
    report.append("=" * 80)
    
    # Summary
    report.append(f"\n📊 CORRECTED SUMMARY")
    report.append("-" * 30)
    report.append(f"🚨 Total Missing Function Errors: {total_errors}")
    report.append(f"📁 Files with Errors: {total_files_with_errors}")
    report.append(f"🔧 Unique Missing Functions: {len(error_groups)}")
    
    # Project Tree
    report.append(f"\n🌳 PROJECT TREE WITH ACTUAL ISSUES")
    report.append("-" * 40)
    report.append(project_tree)
    
    # Real Entry Points
    report.append(f"\n🎯 REAL ENTRY POINTS (Based on Usage, Not Complexity)")
    report.append("-" * 55)
    for i, ep in enumerate(entry_points, 1):
        report.append(f"{i:2d}. 🟩 {ep['name']} ({ep['type']})")
        report.append(f"     📁 {ep['file']}")
        report.append(f"     👥 Used by {ep['dependents']} components - {ep['reason']}")
    
    # Complete Error Analysis
    report.append(f"\n🔴 COMPLETE MISSING FUNCTION ANALYSIS")
    report.append("-" * 45)
    
    # Sort error groups by frequency
    sorted_errors = sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    error_counter = 1
    for func_name, func_errors in sorted_errors:
        report.append(f"\n{error_counter}. 🔴 MISSING FUNCTION: '{func_name}' ({len(func_errors)} occurrences)")
        
        # Show all locations where this function is missing
        for error in func_errors[:10]:  # Show first 10 occurrences
            file_path = error.get("file", "unknown")
            line = error.get("line", "unknown")
            report.append(f"   📁 {file_path}:{line}")
        
        if len(func_errors) > 10:
            report.append(f"   ... and {len(func_errors) - 10} more occurrences")
        
        # Suggest fix
        report.append(f"   💡 Fix: Define function '{func_name}' or import it from appropriate module")
        
        error_counter += 1
    
    # Top problematic files
    report.append(f"\n📊 MOST PROBLEMATIC FILES")
    report.append("-" * 30)
    sorted_files = sorted(file_errors.items(), key=lambda x: x[1], reverse=True)
    
    for i, (file_path, error_count) in enumerate(sorted_files[:10], 1):
        report.append(f"{i:2d}. 📁 {file_path}: {error_count} errors")
    
    # Action Plan
    report.append(f"\n🎯 PRIORITIZED ACTION PLAN")
    report.append("-" * 30)
    report.append("1. 🔥 IMMEDIATE - Fix most frequent missing functions:")
    
    for func_name, func_errors in sorted_errors[:5]:
        report.append(f"   • Define '{func_name}' ({len(func_errors)} occurrences)")
    
    report.append("\n2. 📁 HIGH PRIORITY - Fix most problematic files:")
    for file_path, error_count in sorted_files[:5]:
        report.append(f"   • Fix {file_path} ({error_count} errors)")
    
    report.append("\n3. 🔍 SYSTEMATIC - Review and fix remaining functions:")
    report.append("   • Review import statements")
    report.append("   • Check for typos in function names")
    report.append("   • Verify module dependencies")
    
    report.append("\n" + "=" * 80)
    report.append("✨ Corrected Analysis Complete! ✨")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Main execution"""
    print("🔧 GENERATING CORRECTED ANALYSIS...")
    
    # Check if we have the required data
    if not os.path.exists("analysis_results.json"):
        print("❌ analysis_results.json not found. Run error_analysis.py first.")
        return
    
    # Generate corrected report
    report = generate_corrected_report()
    
    # Display and save
    print(report)
    
    with open("corrected_analysis_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📁 Corrected report saved to: corrected_analysis_report.txt")

if __name__ == "__main__":
    main()
