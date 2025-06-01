#!/usr/bin/env python3
"""
Code Analysis Helper for Autonomous CI/CD

This script provides standardized code analysis functions using the proper
graph_sitter import format for autonomous CI/CD operations.
"""

import os
import sys
from typing import Dict, List, Optional, Any

# Standardized import format as requested
from graph_sitter import codebase


class CodeAnalysisHelper:
    """Helper class for code analysis operations in autonomous CI/CD"""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = codebase_path
        self.codebase_instance = None
    
    def load_codebase(self) -> bool:
        """Load the codebase for analysis"""
        try:
            # Use the standardized codebase import
            self.codebase_instance = codebase.load_codebase(self.codebase_path)
            return True
        except Exception as e:
            print(f"Failed to load codebase: {e}")
            return False
    
    def analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality using graph_sitter codebase"""
        if not self.codebase_instance:
            if not self.load_codebase():
                return {"error": "Failed to load codebase"}
        
        try:
            # Use standardized codebase analysis functions
            analysis_result = {
                "summary": codebase.get_codebase_summary(self.codebase_instance),
                "metrics": codebase.calculate_metrics(self.codebase_instance),
                "issues": codebase.find_issues(self.codebase_instance),
                "suggestions": codebase.get_improvement_suggestions(self.codebase_instance)
            }
            
            return analysis_result
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    def detect_dead_code(self) -> Dict[str, Any]:
        """Detect dead code using standardized imports"""
        if not self.codebase_instance:
            if not self.load_codebase():
                return {"error": "Failed to load codebase"}
        
        try:
            # Use standardized dead code detection
            dead_code_result = {
                "unused_functions": codebase.find_unused_functions(self.codebase_instance),
                "unused_imports": codebase.find_unused_imports(self.codebase_instance),
                "unreachable_code": codebase.find_unreachable_code(self.codebase_instance),
                "cleanup_suggestions": codebase.get_cleanup_suggestions(self.codebase_instance)
            }
            
            return dead_code_result
        except Exception as e:
            return {"error": f"Dead code detection failed: {e}"}
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependencies using standardized imports"""
        if not self.codebase_instance:
            if not self.load_codebase():
                return {"error": "Failed to load codebase"}
        
        try:
            # Use standardized dependency analysis
            dependency_result = {
                "dependency_graph": codebase.build_dependency_graph(self.codebase_instance),
                "circular_dependencies": codebase.find_circular_dependencies(self.codebase_instance),
                "external_dependencies": codebase.analyze_external_dependencies(self.codebase_instance),
                "dependency_health": codebase.assess_dependency_health(self.codebase_instance)
            }
            
            return dependency_result
        except Exception as e:
            return {"error": f"Dependency analysis failed: {e}"}
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report"""
        
        report = {
            "timestamp": codebase.get_current_timestamp(),
            "codebase_path": self.codebase_path,
            "analysis_results": {}
        }
        
        # Run all analyses
        analyses = {
            "code_quality": self.analyze_code_quality,
            "dead_code": self.detect_dead_code,
            "dependencies": self.analyze_dependencies
        }
        
        for analysis_name, analysis_func in analyses.items():
            try:
                result = analysis_func()
                report["analysis_results"][analysis_name] = result
            except Exception as e:
                report["analysis_results"][analysis_name] = {"error": str(e)}
        
        return report


def main():
    """Main function for command-line usage"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Analysis Helper for Autonomous CI/CD")
    parser.add_argument("--path", default=".", help="Path to codebase (default: current directory)")
    parser.add_argument("--analysis", choices=["quality", "dead-code", "dependencies", "all"], 
                       default="all", help="Type of analysis to run")
    parser.add_argument("--output", help="Output file for results (default: stdout)")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = CodeAnalysisHelper(args.path)
    
    # Run requested analysis
    if args.analysis == "quality":
        result = analyzer.analyze_code_quality()
    elif args.analysis == "dead-code":
        result = analyzer.detect_dead_code()
    elif args.analysis == "dependencies":
        result = analyzer.analyze_dependencies()
    else:  # all
        result = analyzer.generate_comprehensive_report()
    
    # Output results
    import json
    output_json = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Analysis results written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()

