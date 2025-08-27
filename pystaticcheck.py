#!/usr/bin/env python3
"""
PyStaticCheck - Comprehensive Python Static Code Checker

This script combines multiple Python static analysis tools into a single interface.
It leverages UV for package management and provides a unified output format.

Tools integrated:
- ruff (includes pyflakes, pycodestyle, mccabe, isort functionality)
- mypy (type checking)
- pylint (comprehensive linting)
- bandit (security analysis)
- pyright (Microsoft's static type checker)
- vulture (dead code detection)
- dodgy (suspicious code patterns)
- pydocstyle (docstring style checking)
- pyroma (packaging best practices)
- codespell (spell checking)
- graph_sitter (code structure analysis)
- biome (formatting and linting)

Usage:
    python pystaticcheck.py [options] [path]

Options:
    --install         Install all required tools using UV
    --parallel        Run tools in parallel (default: sequential)
    --format FORMAT   Output format (text, json, html, default: text)
    --exclude PATTERN Exclude files/directories matching pattern
    --only TOOLS      Run only specified tools (comma-separated)
    --config FILE     Use custom config file
    --verbose         Show verbose output
    --summary         Show only summary of issues
    --fix             Apply automatic fixes where possible
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

# Version
__version__ = "0.1.0"

# Tool definitions with their installation and execution commands
TOOLS = {
    "ruff": {
        "install": ["uv", "add", "--dev", "ruff"],
        "run": ["uv", "run", "ruff", "check", "{path}"],
        "fix": ["uv", "run", "ruff", "check", "--fix", "{path}"],
        "config": "ruff.toml",
        "description": "Fast Python linter, includes pyflakes, pycodestyle, mccabe, isort",
        "category": "linting",
        "weight": 10,  # Priority weight (higher = more important)
    },
    "mypy": {
        "install": ["uv", "add", "--dev", "mypy"],
        "run": ["uv", "run", "mypy", "{path}"],
        "config": "mypy.ini",
        "description": "Static type checker for Python",
        "category": "typing",
        "weight": 9,
    },
    "pylint": {
        "install": ["uv", "add", "--dev", "pylint"],
        "run": ["uv", "run", "pylint", "{path}"],
        "config": ".pylintrc",
        "description": "Comprehensive Python linter",
        "category": "linting",
        "weight": 8,
    },
    "bandit": {
        "install": ["uv", "add", "--dev", "bandit"],
        "run": ["uv", "run", "bandit", "-r", "{path}"],
        "config": ".bandit",
        "description": "Security-focused linter",
        "category": "security",
        "weight": 7,
    },
    "pyright": {
        "install": ["uv", "add", "--dev", "pyright"],
        "run": ["uv", "run", "pyright", "{path}"],
        "config": "pyrightconfig.json",
        "description": "Microsoft's static type checker",
        "category": "typing",
        "weight": 6,
    },
    "vulture": {
        "install": ["uv", "add", "--dev", "vulture"],
        "run": ["uv", "run", "vulture", "{path}"],
        "config": ".vulture",
        "description": "Dead code detector",
        "category": "code_quality",
        "weight": 5,
    },
    "dodgy": {
        "install": ["uv", "add", "--dev", "dodgy"],
        "run": ["uv", "run", "dodgy", "--ignore-paths", ".venv,venv,env,node_modules", "{path}"],
        "description": "Suspicious code pattern detector",
        "category": "security",
        "weight": 4,
    },
    "pydocstyle": {
        "install": ["uv", "add", "--dev", "pydocstyle"],
        "run": ["uv", "run", "pydocstyle", "{path}"],
        "config": ".pydocstyle",
        "description": "Docstring style checker",
        "category": "documentation",
        "weight": 3,
    },
    "pyroma": {
        "install": ["uv", "add", "--dev", "pyroma"],
        "run": ["uv", "run", "pyroma", "."],
        "description": "Packaging best practices checker",
        "category": "packaging",
        "weight": 2,
    },
    "codespell": {
        "install": ["uv", "add", "--dev", "codespell"],
        "run": ["uv", "run", "codespell", "{path}"],
        "config": ".codespellrc",
        "description": "Spell checker for code",
        "category": "spelling",
        "weight": 1,
    },
    "biome": {
        "install": ["npm", "install", "-g", "@biomejs/biome"],
        "run": ["biome", "check", "{path}"],
        "fix": ["biome", "check", "--apply", "{path}"],
        "config": "biome.json",
        "description": "Fast formatter and linter",
        "category": "formatting",
        "weight": 0,
    },
}

# Define color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class PyStaticCheck:
    """Main class for the comprehensive Python static code checker."""

    def __init__(self, args):
        """Initialize the checker with command line arguments."""
        self.args = args
        self.path = args.path
        self.results = {}
        self.start_time = time.time()
        self.tools_to_run = self._get_tools_to_run()
        
    def _get_tools_to_run(self) -> Dict[str, Dict]:
        """Determine which tools to run based on user input."""
        if not self.args.only:
            return TOOLS
        
        selected_tools = {}
        requested_tools = [t.strip() for t in self.args.only.split(",")]
        
        for tool_name in requested_tools:
            if tool_name in TOOLS:
                selected_tools[tool_name] = TOOLS[tool_name]
            else:
                print(f"{Colors.YELLOW}Warning: Unknown tool '{tool_name}'{Colors.ENDC}")
        
        if not selected_tools:
            print(f"{Colors.RED}Error: No valid tools specified{Colors.ENDC}")
            sys.exit(1)
            
        return selected_tools

    def install_tools(self):
        """Install all required tools using UV."""
        print(f"{Colors.HEADER}Installing required tools...{Colors.ENDC}")
        
        for tool_name, tool_info in self.tools_to_run.items():
            print(f"Installing {tool_name}...")
            try:
                subprocess.run(
                    tool_info["install"],
                    check=True,
                    stdout=subprocess.PIPE if not self.args.verbose else None,
                    stderr=subprocess.PIPE if not self.args.verbose else None,
                )
                print(f"{Colors.GREEN}✓ {tool_name} installed successfully{Colors.ENDC}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}✗ Failed to install {tool_name}: {e}{Colors.ENDC}")
                if self.args.verbose:
                    print(f"Error details: {e.stderr.decode() if e.stderr else ''}")

    def _run_tool(self, tool_name: str, tool_info: Dict) -> Tuple[str, Dict]:
        """Run a single tool and return its results."""
        if self.args.verbose:
            print(f"{Colors.BLUE}Running {tool_name}...{Colors.ENDC}")
            
        cmd = tool_info["fix" if self.args.fix and "fix" in tool_info else "run"]
        cmd = [part.format(path=self.path) for part in cmd]
        
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            duration = time.time() - start
            
            return tool_name, {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "duration": duration,
                "returncode": result.returncode
            }
        except Exception as e:
            duration = time.time() - start
            return tool_name, {
                "success": False,
                "output": "",
                "error": str(e),
                "duration": duration,
                "returncode": -1
            }

    def run_tools(self):
        """Run all selected tools either in parallel or sequentially."""
        print(f"{Colors.HEADER}Running static analysis tools on {self.path}...{Colors.ENDC}")
        
        if self.args.parallel:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(self._run_tool, tool_name, tool_info): tool_name
                    for tool_name, tool_info in self.tools_to_run.items()
                }
                
                for future in concurrent.futures.as_completed(futures):
                    tool_name, result = future.result()
                    self.results[tool_name] = result
                    self._print_tool_result(tool_name, result)
        else:
            for tool_name, tool_info in self.tools_to_run.items():
                tool_name, result = self._run_tool(tool_name, tool_info)
                self.results[tool_name] = result
                self._print_tool_result(tool_name, result)

    def _print_tool_result(self, tool_name: str, result: Dict):
        """Print the result of a tool run."""
        if self.args.summary:
            status = f"{Colors.GREEN}✓{Colors.ENDC}" if result["success"] else f"{Colors.RED}✗{Colors.ENDC}"
            print(f"{status} {tool_name} ({result['duration']:.2f}s)")
            return
            
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== {tool_name} ==={Colors.ENDC}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Status: {'Success' if result['success'] else 'Failed'}")
        
        if not result["success"] or self.args.verbose:
            if result["output"]:
                print(f"\n{Colors.YELLOW}Output:{Colors.ENDC}")
                print(result["output"])
            
            if result["error"]:
                print(f"\n{Colors.RED}Errors:{Colors.ENDC}")
                print(result["error"])

    def generate_report(self):
        """Generate a comprehensive report of all tool results."""
        total_duration = time.time() - self.start_time
        success_count = sum(1 for result in self.results.values() if result["success"])
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Summary ==={Colors.ENDC}")
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Tools run: {len(self.results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(self.results) - success_count}")
        
        if self.args.format == "json":
            self._generate_json_report()
        elif self.args.format == "html":
            self._generate_html_report()

    def _generate_json_report(self):
        """Generate a JSON report of all tool results."""
        report = {
            "summary": {
                "total_duration": time.time() - self.start_time,
                "tools_run": len(self.results),
                "successful": sum(1 for result in self.results.values() if result["success"]),
                "failed": sum(1 for result in self.results.values() if not result["success"]),
            },
            "results": self.results
        }
        
        report_path = Path("pystaticcheck_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\nJSON report saved to {report_path}")

    def _generate_html_report(self):
        """Generate an HTML report of all tool results."""
        # Simple HTML report template
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyStaticCheck Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .summary { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
                .tool { margin: 20px 0; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                .tool-header { display: flex; justify-content: space-between; }
                .success { color: green; }
                .failure { color: red; }
                .output { background-color: #f9f9f9; padding: 10px; border-radius: 5px; white-space: pre-wrap; }
            </style>
        </head>
        <body>
            <h1>PyStaticCheck Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total duration: {total_duration:.2f}s</p>
                <p>Tools run: {tools_run}</p>
                <p>Successful: {successful}</p>
                <p>Failed: {failed}</p>
            </div>
            
            <h2>Tool Results</h2>
            {tool_results}
        </body>
        </html>
        """
        
        tool_results = ""
        for tool_name, result in self.results.items():
            status_class = "success" if result["success"] else "failure"
            status_text = "Success" if result["success"] else "Failed"
            
            tool_results += f"""
            <div class="tool">
                <div class="tool-header">
                    <h3>{tool_name}</h3>
                    <span class="{status_class}">{status_text}</span>
                </div>
                <p>Duration: {result['duration']:.2f}s</p>
            """
            
            if result["output"]:
                tool_results += f"""
                <h4>Output:</h4>
                <div class="output">{result['output']}</div>
                """
                
            if result["error"]:
                tool_results += f"""
                <h4>Errors:</h4>
                <div class="output">{result['error']}</div>
                """
                
            tool_results += "</div>"
            
        report_html = html.format(
            total_duration=time.time() - self.start_time,
            tools_run=len(self.results),
            successful=sum(1 for result in self.results.values() if result["success"]),
            failed=sum(1 for result in self.results.values() if not result["success"]),
            tool_results=tool_results
        )
        
        report_path = Path("pystaticcheck_report.html")
        with open(report_path, "w") as f:
            f.write(report_html)
            
        print(f"\nHTML report saved to {report_path}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Python Static Code Checker"
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Path to the Python code to check"
    )
    parser.add_argument(
        "--install", action="store_true", help="Install all required tools using UV"
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Run tools in parallel"
    )
    parser.add_argument(
        "--format", choices=["text", "json", "html"], default="text",
        help="Output format (text, json, html)"
    )
    parser.add_argument(
        "--exclude", help="Exclude files/directories matching pattern"
    )
    parser.add_argument(
        "--only", help="Run only specified tools (comma-separated)"
    )
    parser.add_argument(
        "--config", help="Use custom config file"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show verbose output"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show only summary of issues"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Apply automatic fixes where possible"
    )
    parser.add_argument(
        "--version", action="version", version=f"PyStaticCheck {__version__}"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    checker = PyStaticCheck(args)
    
    if args.install:
        checker.install_tools()
        
    checker.run_tools()
    checker.generate_report()
    
    # Return non-zero exit code if any tool failed
    if any(not result["success"] for result in checker.results.values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
