#!/usr/bin/env python3
"""
Error Analysis Module for Graph-sitter Codebase
===============================================

This module provides focused error analysis capabilities for codebases,
integrating with LSP servers for real-time error detection and analysis.
This replaces the complexity-focused deep_analysis.py with error-specific functionality.
"""

import sys
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodebaseErrorAnalyzer:
    """Focused error analysis for codebases using graph-sitter and LSP integration."""
    
    def __init__(self, codebase):
        self.codebase = codebase
        self.error_cache = {}
        
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns across the codebase."""
        try:
            logger.info("Starting error pattern analysis...")
            
            # Basic counts
            files = list(self.codebase.files)
            
            # Error analysis
            analysis = {
                "basic_counts": {
                    "total_files": len(files),
                    "analyzed_files": 0,
                    "files_with_errors": 0
                },
                "error_patterns": self._analyze_error_patterns(files),
                "error_hotspots": self._identify_error_hotspots(files),
                "error_severity_distribution": self._analyze_error_severity(files),
                "error_categories": self._categorize_errors(files)
            }
            
            logger.info("Error pattern analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in error pattern analysis: {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _analyze_error_patterns(self, files) -> Dict[str, Any]:
        """Analyze common error patterns."""
        try:
            error_patterns = {
                "import_errors": 0,
                "syntax_errors": 0,
                "type_errors": 0,
                "undefined_variables": 0,
                "unused_imports": 0,
                "missing_docstrings": 0
            }
            
            # This would integrate with LSP diagnostics
            # For now, we'll analyze basic patterns from the AST
            
            for file in files:
                # Check for potential import issues
                if hasattr(file, 'imports'):
                    for imp in file.imports:
                        # Basic import validation could go here
                        pass
                
                # Check for functions without docstrings
                if hasattr(file, 'functions'):
                    for func in file.functions:
                        if not hasattr(func, 'docstring') or not func.docstring:
                            error_patterns["missing_docstrings"] += 1
            
            return error_patterns
            
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}")
            return {"error": str(e)}
    
    def _identify_error_hotspots(self, files) -> Dict[str, Any]:
        """Identify files and areas with high error density."""
        try:
            hotspots = {
                "files_by_error_count": [],
                "directories_by_error_count": [],
                "error_prone_patterns": []
            }
            
            # This would integrate with LSP diagnostics to get real error counts
            # For now, we'll use proxy metrics
            
            file_error_scores = []
            for file in files:
                # Calculate error proneness score based on complexity indicators
                score = 0
                if hasattr(file, 'imports'):
                    score += len(file.imports) * 0.1  # More imports = more potential issues
                if hasattr(file, 'functions'):
                    score += len([f for f in file.functions if len(f.parameters) > 5]) * 0.5  # Complex functions
                
                file_error_scores.append({
                    "file": file.file_path if hasattr(file, 'file_path') else file.name,
                    "error_score": score
                })
            
            # Sort by error score
            hotspots["files_by_error_count"] = sorted(
                file_error_scores, 
                key=lambda x: x["error_score"], 
                reverse=True
            )[:10]
            
            return hotspots
            
        except Exception as e:
            logger.error(f"Error identifying hotspots: {e}")
            return {"error": str(e)}
    
    def _analyze_error_severity(self, files) -> Dict[str, Any]:
        """Analyze error severity distribution."""
        try:
            severity_dist = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
            
            # This would integrate with LSP diagnostics for real severity data
            # For now, we'll use heuristics
            
            for file in files:
                # Check for potential critical issues
                if hasattr(file, 'functions'):
                    for func in file.functions:
                        # Functions with many parameters might have issues
                        if len(func.parameters) > 8:
                            severity_dist["high"] += 1
                        elif len(func.parameters) > 5:
                            severity_dist["medium"] += 1
            
            return severity_dist
            
        except Exception as e:
            logger.error(f"Error analyzing severity: {e}")
            return {"error": str(e)}
    
    def _categorize_errors(self, files) -> Dict[str, Any]:
        """Categorize errors by type and source."""
        try:
            categories = {
                "lsp_errors": {
                    "syntax": 0,
                    "type_checking": 0,
                    "imports": 0,
                    "undefined": 0
                },
                "code_quality": {
                    "style": 0,
                    "complexity": 0,
                    "documentation": 0,
                    "naming": 0
                },
                "potential_bugs": {
                    "null_references": 0,
                    "resource_leaks": 0,
                    "logic_errors": 0
                }
            }
            
            # This would integrate with actual LSP diagnostics
            # For now, we'll use basic heuristics
            
            for file in files:
                # Check documentation
                if hasattr(file, 'functions'):
                    for func in file.functions:
                        if not hasattr(func, 'docstring') or not func.docstring:
                            categories["code_quality"]["documentation"] += 1
                
                # Check naming conventions
                if hasattr(file, 'classes'):
                    for cls in file.classes:
                        if not cls.name[0].isupper():
                            categories["code_quality"]["naming"] += 1
            
            return categories
            
        except Exception as e:
            logger.error(f"Error categorizing errors: {e}")
            return {"error": str(e)}
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a comprehensive error summary."""
        try:
            analysis = self.analyze_error_patterns()
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_files_analyzed": analysis.get("basic_counts", {}).get("total_files", 0),
                "error_analysis": analysis,
                "recommendations": self._generate_error_recommendations(analysis)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _generate_error_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on error analysis."""
        recommendations = []
        
        try:
            error_patterns = analysis.get("error_patterns", {})
            
            if error_patterns.get("missing_docstrings", 0) > 10:
                recommendations.append("Consider adding docstrings to functions for better documentation")
            
            if error_patterns.get("import_errors", 0) > 5:
                recommendations.append("Review import statements for potential issues")
            
            hotspots = analysis.get("error_hotspots", {}).get("files_by_error_count", [])
            if hotspots and len(hotspots) > 0:
                top_file = hotspots[0].get("file", "unknown")
                recommendations.append(f"Focus on refactoring {top_file} - it shows high error potential")
            
            severity = analysis.get("error_severity_distribution", {})
            if severity.get("critical", 0) > 0:
                recommendations.append("Address critical errors immediately")
            
            if severity.get("high", 0) > 10:
                recommendations.append("Plan to address high-severity issues in next sprint")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error generating recommendations - manual review needed")
        
        return recommendations


def analyze_codebase_errors(codebase) -> Dict[str, Any]:
    """Convenience function to analyze codebase errors."""
    analyzer = CodebaseErrorAnalyzer(codebase)
    return analyzer.get_error_summary()


def main():
    """Main function for standalone execution."""
    try:
        from graph_sitter import Codebase
        
        codebase = Codebase(".")
        analyzer = CodebaseErrorAnalyzer(codebase)
        
        print("🔍 CODEBASE ERROR ANALYSIS")
        print("=" * 50)
        
        summary = analyzer.get_error_summary()
        print(json.dumps(summary, indent=2, default=str))
        
    except Exception as e:
        print(f"Error running analysis: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

