#!/usr/bin/env python3
"""
Simplified Analysis System - Using Graph-Sitter's Built-in Capabilities

This demonstrates how simple analysis actually is when using graph-sitter's
pre-computed graph and built-in properties instead of complex analyzers.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import the actual graph-sitter core
try:
    from graph_sitter.core.codebase import Codebase
except ImportError:
    print("⚠️  Graph-sitter not installed. This is a demonstration of the simplified API.")
    # Create a mock for demonstration
    class MockCodebase:
        def __init__(self, path):
            self.repo_path = path
            self.files = []
            self.functions = []
            self.classes = []
            self.imports = []
    
    Codebase = MockCodebase

@dataclass
class SimpleIssue:
    """Simple issue representation."""
    type: str
    severity: str
    location: str
    description: str
    line_number: Optional[int] = None


@dataclass
class SimpleStats:
    """Simple statistics representation."""
    total_files: int
    total_functions: int
    total_classes: int
    total_imports: int
    total_lines: int
    unused_functions: int
    missing_docstrings: int


class SimplifiedAnalysis:
    """
    Simplified analysis using graph-sitter's built-in capabilities.
    
    This replaces our overcomplicated ComprehensiveAnalyzer with simple
    property access and built-in graph traversal.
    """
    
    def __init__(self, repo_path: str):
        """Initialize with simple codebase loading."""
        self.codebase = Codebase(repo_path)
        self.issues: List[SimpleIssue] = []
        self.stats: Optional[SimpleStats] = None
    
    @classmethod
    def from_repo(cls, repo_name: str) -> "SimplifiedAnalysis":
        """Create from GitHub repository - uses graph-sitter's built-in."""
        codebase = Codebase.from_repo(repo_name)
        instance = cls.__new__(cls)
        instance.codebase = codebase
        instance.issues = []
        instance.stats = None
        return instance
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform simple analysis using graph-sitter's built-in properties.
        
        This is dramatically simpler than our previous approach because
        graph-sitter pre-computes all relationships.
        """
        print("🔍 Running simplified analysis using graph-sitter built-ins...")
        
        # Generate stats using simple property access
        self._generate_stats()
        
        # Find issues using simple property checks
        self._find_unused_functions()
        self._find_missing_docstrings()
        self._find_complex_functions()
        self._find_inheritance_issues()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'issues': [
                {
                    'type': issue.type,
                    'severity': issue.severity,
                    'location': issue.location,
                    'description': issue.description,
                    'line_number': issue.line_number
                }
                for issue in self.issues
            ],
            'summary': {
                'total_issues': len(self.issues),
                'high_severity': len([i for i in self.issues if i.severity == 'high']),
                'medium_severity': len([i for i in self.issues if i.severity == 'medium']),
                'low_severity': len([i for i in self.issues if i.severity == 'low'])
            }
        }
    
    def _generate_stats(self):
        """Generate statistics using graph-sitter's instant lookups."""
        # These are all instant property access - no computation needed!
        total_lines = sum(len(file.source.split('\n')) for file in self.codebase.files 
                         if hasattr(file, 'source') and file.source)
        
        unused_functions = len([f for f in self.codebase.functions if not f.usages])
        missing_docstrings = len([f for f in self.codebase.functions if not f.docstring])
        
        self.stats = SimpleStats(
            total_files=len(self.codebase.files),
            total_functions=len(self.codebase.functions),
            total_classes=len(self.codebase.classes),
            total_imports=len(self.codebase.imports),
            total_lines=total_lines,
            unused_functions=unused_functions,
            missing_docstrings=missing_docstrings
        )
    
    def _find_unused_functions(self):
        """Find unused functions using graph-sitter's pre-computed usages."""
        for function in self.codebase.functions:
            # Skip private functions and test functions
            if function.name.startswith('_') or function.name.startswith('test_'):
                continue
                
            # Graph-sitter pre-computes usages - instant lookup!
            if not function.usages:
                self.issues.append(SimpleIssue(
                    type='unused_function',
                    severity='high',
                    location=f"{function.file.filepath}:{function.line_number}",
                    description=f"Function '{function.name}' is defined but never used",
                    line_number=function.line_number
                ))
    
    def _find_missing_docstrings(self):
        """Find missing docstrings using graph-sitter's built-in docstring property."""
        for function in self.codebase.functions:
            # Skip private functions
            if function.name.startswith('_'):
                continue
                
            # Graph-sitter provides docstring property directly
            if not function.docstring:
                self.issues.append(SimpleIssue(
                    type='missing_docstring',
                    severity='low',
                    location=f"{function.file.filepath}:{function.line_number}",
                    description=f"Function '{function.name}' missing docstring",
                    line_number=function.line_number
                ))
    
    def _find_complex_functions(self):
        """Find complex functions using graph-sitter's built-in call analysis."""
        for function in self.codebase.functions:
            # Use graph-sitter's pre-computed function calls
            call_count = len(function.function_calls)
            
            # Simple heuristic for complexity
            if call_count > 10:
                self.issues.append(SimpleIssue(
                    type='high_complexity',
                    severity='medium',
                    location=f"{function.file.filepath}:{function.line_number}",
                    description=f"Function '{function.name}' has high complexity ({call_count} calls)",
                    line_number=function.line_number
                ))
    
    def _find_inheritance_issues(self):
        """Find inheritance issues using graph-sitter's built-in inheritance tracking."""
        for cls in self.codebase.classes:
            # Graph-sitter provides superclasses property directly
            if len(cls.superclasses) > 3:
                self.issues.append(SimpleIssue(
                    type='deep_inheritance',
                    severity='medium',
                    location=f"{cls.file.filepath}:{cls.line_number}",
                    description=f"Class '{cls.name}' has deep inheritance chain ({len(cls.superclasses)} levels)",
                    line_number=cls.line_number
                ))
    
    def visualize(self):
        """Use graph-sitter's built-in visualization."""
        try:
            import networkx as nx
            
            # Create simple call graph
            G = nx.DiGraph()
            
            # Add function nodes
            for function in self.codebase.functions[:20]:  # Limit for demo
                G.add_node(function.name)
                
                # Add edges for function calls (pre-computed by graph-sitter)
                for call in function.function_calls:
                    if hasattr(call, 'function_definition') and call.function_definition:
                        G.add_edge(function.name, call.function_definition.name)
            
            # Use graph-sitter's built-in visualization
            self.codebase.visualize(G)
            print("📊 Visualization generated using graph-sitter's built-in visualize()")
            
        except ImportError:
            print("📊 NetworkX not available for visualization")
        except Exception as e:
            print(f"📊 Visualization error: {e}")
    
    def get_dead_code(self) -> List[str]:
        """Get dead code using graph-sitter's simple pattern."""
        # This is the exact pattern from graph-sitter.com documentation
        dead_functions = []
        for function in self.codebase.functions:
            if not function.usages:
                dead_functions.append(function.name)
        return dead_functions
    
    def remove_dead_code(self):
        """Remove dead code using graph-sitter's built-in removal."""
        # This is the exact pattern from graph-sitter.com documentation
        for function in self.codebase.functions:
            if not function.usages:
                function.remove()  # Graph-sitter handles all the complexity
        
        # Commit changes
        self.codebase.commit()


def demonstrate_simplicity():
    """Demonstrate how simple analysis actually is."""
    print("🚀 Demonstrating Graph-Sitter's Actual Simplicity")
    print("=" * 60)
    
    # Simple initialization
    analysis = SimplifiedAnalysis(".")
    
    # Simple analysis
    results = analysis.analyze()
    
    # Simple output
    print(f"📊 Analysis Results:")
    print(f"  Total Files: {results['stats'].total_files}")
    print(f"  Total Functions: {results['stats'].total_functions}")
    print(f"  Total Classes: {results['stats'].total_classes}")
    print(f"  Total Issues: {results['summary']['total_issues']}")
    print(f"  High Severity: {results['summary']['high_severity']}")
    
    # Show some issues
    print(f"\n🚨 Sample Issues:")
    for issue in results['issues'][:5]:
        print(f"  {issue['severity'].upper()}: {issue['description']}")
    
    # Demonstrate dead code detection
    dead_code = analysis.get_dead_code()
    print(f"\n💀 Dead Functions Found: {len(dead_code)}")
    for func in dead_code[:5]:
        print(f"  - {func}")
    
    print(f"\n✅ Analysis complete - this is how simple it should be!")
    return results


if __name__ == "__main__":
    demonstrate_simplicity()
