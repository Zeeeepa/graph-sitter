#!/usr/bin/env python3
"""
Interactive CLI Demo of the Graph-Sitter Reflex Dashboard
This demonstrates all the key features that would be available in the web UI.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any
import os


class DashboardDemo:
    """Interactive demo of the dashboard functionality."""
    
    def __init__(self):
        self.available_codebases = []
        self.selected_codebase = ""
        self.selected_codebase_path = ""
        self.codebase_loaded = False
        self.analysis_results = {}
        
        # Stats
        self.total_files = 0
        self.total_errors = 0
        self.total_warnings = 0
        self.total_symbols = 0
        
        self.detect_codebases()
    
    def detect_codebases(self):
        """Detect available codebases."""
        print("🔍 Detecting available codebases...")
        
        current_dir = Path.cwd()
        codebases = []
        
        # Current directory
        codebases.append(("Current Directory", str(current_dir), current_dir.name))
        
        # Graph-sitter core (if we're in the dashboard)
        if current_dir.parent.name == "reflex_dashboard":
            graph_sitter_root = current_dir.parent.parent
            if (graph_sitter_root / "src" / "graph_sitter").exists():
                codebases.append(("Graph-Sitter Core", str(graph_sitter_root), graph_sitter_root.name))
        
        # Source directories
        for src_dir in ["src", "lib", "app"]:
            if (current_dir / src_dir).exists():
                codebases.append((f"{src_dir.title()} Directory", str(current_dir / src_dir), src_dir))
        
        self.available_codebases = codebases
        print(f"✅ Found {len(codebases)} available codebases")
    
    def show_codebases(self):
        """Show available codebases."""
        print("\n📁 Available Codebases:")
        for i, (name, path, display) in enumerate(self.available_codebases, 1):
            print(f"   {i}. {name} ({display})")
            print(f"      Path: {path}")
    
    def select_codebase(self, index: int):
        """Select a codebase by index."""
        if 1 <= index <= len(self.available_codebases):
            name, path, display = self.available_codebases[index - 1]
            self.selected_codebase = name
            self.selected_codebase_path = path
            self.codebase_loaded = False
            print(f"✅ Selected: {name}")
            return True
        else:
            print("❌ Invalid selection")
            return False
    
    def load_codebase(self):
        """Load the selected codebase."""
        if not self.selected_codebase:
            print("❌ No codebase selected")
            return False
        
        print(f"📂 Loading codebase: {self.selected_codebase}")
        print(f"📍 Path: {self.selected_codebase_path}")
        
        try:
            path = Path(self.selected_codebase_path)
            
            # Count files
            print("🔍 Scanning files...")
            python_files = list(path.rglob("*.py"))
            js_files = list(path.rglob("*.js")) + list(path.rglob("*.ts"))
            all_files = python_files + js_files
            
            self.total_files = len(python_files)
            
            print(f"📊 File Statistics:")
            print(f"   🐍 Python files: {len(python_files)}")
            print(f"   📜 JS/TS files: {len(js_files)}")
            print(f"   📁 Total relevant files: {len(all_files)}")
            
            self.codebase_loaded = True
            print("✅ Codebase loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load codebase: {e}")
            return False
    
    async def run_analysis(self):
        """Run comprehensive analysis."""
        if not self.codebase_loaded:
            print("❌ No codebase loaded")
            return False
        
        print("\n🚀 Starting comprehensive analysis...")
        print("=" * 50)
        
        # Analysis steps with progress
        steps = [
            ("Initializing analysis engine", 10),
            ("Scanning file structure", 20),
            ("Collecting LSP diagnostics", 40),
            ("Analyzing symbols and functions", 60),
            ("Calculating complexity metrics", 80),
            ("Generating health report", 90),
            ("Finalizing results", 100)
        ]
        
        for step_name, progress in steps:
            print(f"📊 {step_name}... ({progress}%)")
            await asyncio.sleep(0.8)  # Simulate work
        
        # Generate mock analysis results
        path = Path(self.selected_codebase_path)
        python_files = list(path.rglob("*.py"))
        
        self.total_files = len(python_files)
        self.total_errors = max(0, len(python_files) // 10)  # 10% error rate
        self.total_warnings = max(0, len(python_files) // 5)  # 20% warning rate
        self.total_symbols = len(python_files) * 15  # ~15 symbols per file
        
        # Calculate health metrics
        maintainability_index = max(0, 100 - (self.total_errors * 10) - (self.total_warnings * 2))
        technical_debt_score = (self.total_errors * 3) + (self.total_warnings * 1)
        
        self.analysis_results = {
            "files": self.total_files,
            "errors": self.total_errors,
            "warnings": self.total_warnings,
            "symbols": self.total_symbols,
            "maintainability_index": maintainability_index,
            "technical_debt_score": technical_debt_score,
            "health_status": "Good" if maintainability_index > 70 else "Fair" if maintainability_index > 40 else "Poor"
        }
        
        print("\n✅ Analysis completed!")
        return True
    
    def show_analysis_results(self):
        """Show detailed analysis results."""
        if not self.analysis_results:
            print("❌ No analysis results available")
            return
        
        print("\n📊 ANALYSIS RESULTS")
        print("=" * 50)
        
        # Overview stats
        print(f"📁 Total Files: {self.analysis_results['files']}")
        print(f"🔴 Errors: {self.analysis_results['errors']}")
        print(f"🟡 Warnings: {self.analysis_results['warnings']}")
        print(f"🟢 Symbols: {self.analysis_results['symbols']}")
        
        print(f"\n🏥 Health Metrics:")
        print(f"   📈 Maintainability Index: {self.analysis_results['maintainability_index']:.1f}/100")
        print(f"   💳 Technical Debt Score: {self.analysis_results['technical_debt_score']}")
        print(f"   🎯 Overall Health: {self.analysis_results['health_status']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if self.analysis_results['errors'] > 0:
            print(f"   🔴 Fix {self.analysis_results['errors']} critical errors")
        if self.analysis_results['warnings'] > 50:
            print(f"   🟡 Address {self.analysis_results['warnings']} warnings")
        if self.analysis_results['maintainability_index'] < 70:
            print(f"   🔵 Improve maintainability (currently {self.analysis_results['maintainability_index']:.1f}/100)")
        
        print(f"\n🎉 This represents what the Reflex dashboard would show in:")
        print(f"   • Interactive charts and graphs")
        print(f"   • Clickable file tree with error indicators")
        print(f"   • Symbol hierarchy visualization")
        print(f"   • LSP diagnostics with navigation")
        print(f"   • Real-time progress tracking")
    
    def show_file_tree_demo(self):
        """Demonstrate file tree functionality."""
        if not self.codebase_loaded:
            print("❌ No codebase loaded")
            return
        
        print("\n🌳 FILE TREE DEMO")
        print("=" * 50)
        
        path = Path(self.selected_codebase_path)
        
        # Show directory structure (limited depth)
        print("📁 Directory Structure (sample):")
        
        dirs_shown = 0
        for item in sorted(path.iterdir()):
            if dirs_shown >= 10:  # Limit output
                print("   ... (more directories)")
                break
                
            if item.is_dir() and not item.name.startswith('.'):
                py_files = list(item.rglob("*.py"))
                error_count = len(py_files) // 10  # Mock errors
                
                status = "🔴" if error_count > 5 else "🟡" if error_count > 0 else "🟢"
                print(f"   📁 {item.name}/ {status} ({len(py_files)} files, ~{error_count} issues)")
                
                # Show some files in the directory
                files_shown = 0
                for py_file in sorted(item.rglob("*.py")):
                    if files_shown >= 3:
                        if len(py_files) > 3:
                            print(f"      ... ({len(py_files) - 3} more files)")
                        break
                    
                    rel_path = py_file.relative_to(item)
                    file_errors = 1 if files_shown == 0 and error_count > 0 else 0
                    file_status = "🔴" if file_errors > 0 else "🟢"
                    print(f"      📄 {rel_path} {file_status}")
                    files_shown += 1
                
                dirs_shown += 1
        
        print(f"\n🎯 In the Reflex dashboard, this would be:")
        print(f"   • Expandable/collapsible tree nodes")
        print(f"   • Search and filtering by file type")
        print(f"   • Click to view file contents")
        print(f"   • Error badges and indicators")
        print(f"   • File size and line count info")
    
    def show_symbols_demo(self):
        """Demonstrate symbol analysis."""
        print("\n🧩 SYMBOL ANALYSIS DEMO")
        print("=" * 50)
        
        if not self.analysis_results:
            print("❌ Run analysis first")
            return
        
        # Mock symbol data
        mock_symbols = [
            ("Codebase", "class", "src/graph_sitter/core/codebase.py", 45, 8.5),
            ("Function", "class", "src/graph_sitter/core/function.py", 123, 7.2),
            ("analyze_symbols", "function", "src/graph_sitter/analysis/analyzer.py", 67, 6.8),
            ("get_completions", "function", "src/graph_sitter/lsp/server.py", 234, 5.9),
            ("parse_tree", "function", "src/graph_sitter/parsing/parser.py", 89, 5.4),
        ]
        
        print("🔝 Top Complex Symbols:")
        for name, symbol_type, file_path, line, complexity in mock_symbols:
            complexity_color = "🔴" if complexity > 7 else "🟡" if complexity > 5 else "🟢"
            print(f"   {complexity_color} {name} ({symbol_type})")
            print(f"      📍 {file_path}:{line}")
            print(f"      📊 Complexity: {complexity}/10")
        
        print(f"\n📈 Symbol Statistics:")
        print(f"   🏛️ Total Symbols: {self.analysis_results['symbols']}")
        print(f"   🔧 Functions: ~{self.analysis_results['symbols'] * 0.7:.0f}")
        print(f"   🏗️ Classes: ~{self.analysis_results['symbols'] * 0.3:.0f}")
        
        print(f"\n🎯 In the Reflex dashboard, this would show:")
        print(f"   • Interactive symbol tree with hierarchy")
        print(f"   • Click to navigate to symbol definition")
        print(f"   • Complexity heatmaps and charts")
        print(f"   • Symbol relationships and dependencies")
        print(f"   • Documentation and signature info")
    
    def show_diagnostics_demo(self):
        """Demonstrate LSP diagnostics."""
        print("\n🩺 LSP DIAGNOSTICS DEMO")
        print("=" * 50)
        
        if not self.analysis_results:
            print("❌ Run analysis first")
            return
        
        # Mock diagnostic data
        mock_diagnostics = [
            ("error", "Undefined variable 'undefined_var'", "src/graph_sitter/core/codebase.py", 45, "E0602"),
            ("warning", "Unused import 'os'", "src/graph_sitter/core/function.py", 123, "W0611"),
            ("info", "Consider using f-string", "src/graph_sitter/core/class_definition.py", 67, "C0209"),
            ("error", "Missing return statement", "src/graph_sitter/analysis/analyzer.py", 234, "E1128"),
            ("warning", "Line too long (85 > 80 characters)", "src/graph_sitter/lsp/server.py", 156, "C0301"),
        ]
        
        print("🚨 Recent Diagnostics:")
        for severity, message, file_path, line, code in mock_diagnostics:
            severity_icon = "🔴" if severity == "error" else "🟡" if severity == "warning" else "🔵"
            print(f"   {severity_icon} {severity.upper()}: {message}")
            print(f"      📍 {file_path}:{line}")
            print(f"      🏷️ Code: {code}")
        
        print(f"\n📊 Diagnostic Summary:")
        print(f"   🔴 Errors: {self.analysis_results['errors']}")
        print(f"   🟡 Warnings: {self.analysis_results['warnings']}")
        print(f"   🔵 Info: ~{self.analysis_results['warnings'] // 2}")
        
        print(f"\n🎯 In the Reflex dashboard, this would provide:")
        print(f"   • Filterable diagnostic list by severity")
        print(f"   • Click to jump to error location")
        print(f"   • Error grouping by file and type")
        print(f"   • Quick fix suggestions")
        print(f"   • Integration with LSP servers")


async def main():
    """Main interactive demo."""
    print("🚀 GRAPH-SITTER REFLEX DASHBOARD DEMO")
    print("=" * 60)
    print("This demonstrates all the features that would be available")
    print("in the interactive web dashboard built with Reflex!")
    print("=" * 60)
    
    demo = DashboardDemo()
    
    while True:
        print("\n🎛️ DASHBOARD MENU:")
        print("1. 📁 Show Available Codebases")
        print("2. 🎯 Select Codebase")
        print("3. 📂 Load Selected Codebase")
        print("4. 🚀 Run Comprehensive Analysis")
        print("5. 📊 Show Analysis Results")
        print("6. 🌳 Demo File Tree Navigation")
        print("7. 🧩 Demo Symbol Analysis")
        print("8. 🩺 Demo LSP Diagnostics")
        print("9. ❌ Exit")
        
        try:
            choice = input("\n👉 Select option (1-9): ").strip()
            
            if choice == "1":
                demo.show_codebases()
            
            elif choice == "2":
                demo.show_codebases()
                try:
                    index = int(input("👉 Select codebase number: "))
                    demo.select_codebase(index)
                except ValueError:
                    print("❌ Please enter a valid number")
            
            elif choice == "3":
                demo.load_codebase()
            
            elif choice == "4":
                await demo.run_analysis()
            
            elif choice == "5":
                demo.show_analysis_results()
            
            elif choice == "6":
                demo.show_file_tree_demo()
            
            elif choice == "7":
                demo.show_symbols_demo()
            
            elif choice == "8":
                demo.show_diagnostics_demo()
            
            elif choice == "9":
                print("\n👋 Thanks for trying the Graph-Sitter Dashboard demo!")
                print("🎉 The full Reflex web interface provides all these features")
                print("   with beautiful interactive UI, real-time updates, and more!")
                break
            
            else:
                print("❌ Invalid choice. Please select 1-9.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
