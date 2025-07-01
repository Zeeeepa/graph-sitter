#!/usr/bin/env python3
"""
Autonomous Test Optimizer
Automatically optimizes test suite performance and reliability for CI/CD
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from codegen import Agent
except ImportError:
    print("⚠️  Codegen SDK not available - running in standalone mode")
    Agent = None

class AutonomousTestOptimizer:
    """Autonomous test suite optimizer for CI/CD"""
    
    def __init__(self):
        self.org_id = os.getenv("CODEGEN_ORG_ID")
        self.token = os.getenv("CODEGEN_TOKEN")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.agent = None
        
        if Agent and self.org_id and self.token:
            try:
                self.agent = Agent(org_id=self.org_id, token=self.token)
                print("✅ Codegen SDK initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize Codegen SDK: {e}")
    
    def optimize_test_suite(self, analyze_flaky: bool = True, 
                          optimize_parallelization: bool = True,
                          suggest_new_tests: bool = True) -> Dict:
        """Run comprehensive test suite optimization"""
        print("🚀 Starting autonomous test optimization...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "flaky_tests": [],
            "performance_improvements": [],
            "parallelization_suggestions": [],
            "new_test_suggestions": [],
            "actions_taken": []
        }
        
        if analyze_flaky:
            results["flaky_tests"] = self._analyze_flaky_tests()
        
        if optimize_parallelization:
            results["parallelization_suggestions"] = self._optimize_parallelization()
        
        if suggest_new_tests:
            results["new_test_suggestions"] = self._suggest_new_tests()
        
        # Apply optimizations using Codegen SDK if available
        if self.agent:
            results["actions_taken"] = self._apply_optimizations_with_codegen(results)
        else:
            results["actions_taken"] = self._apply_optimizations_standalone(results)
        
        return results
    
    def _analyze_flaky_tests(self) -> List[Dict]:
        """Analyze test history to identify flaky tests"""
        print("🎲 Analyzing flaky tests...")
        
        flaky_tests = []
        
        # Get recent workflow runs
        workflow_runs = self._get_recent_workflow_runs()
        
        # Analyze test failures across runs
        test_failures = {}
        total_runs = len(workflow_runs)
        
        for run in workflow_runs:
            failed_tests = self._extract_failed_tests_from_run(run)
            for test_name in failed_tests:
                if test_name not in test_failures:
                    test_failures[test_name] = 0
                test_failures[test_name] += 1
        
        # Identify flaky tests (fail sometimes but not always)
        for test_name, failure_count in test_failures.items():
            failure_rate = failure_count / total_runs
            if 0.1 < failure_rate < 0.9:  # Flaky if fails 10-90% of the time
                flaky_tests.append({
                    "test_name": test_name,
                    "failure_rate": failure_rate,
                    "failure_count": failure_count,
                    "total_runs": total_runs,
                    "severity": "high" if failure_rate > 0.5 else "medium"
                })
        
        # Sort by failure rate
        flaky_tests.sort(key=lambda x: x["failure_rate"], reverse=True)
        
        print(f"📊 Found {len(flaky_tests)} potentially flaky tests")
        return flaky_tests
    
    def _optimize_parallelization(self) -> List[Dict]:
        """Suggest parallelization improvements"""
        print("⚡ Optimizing test parallelization...")
        
        suggestions = []
        
        # Analyze test execution times
        test_times = self._get_test_execution_times()
        
        # Identify slow tests that could benefit from parallelization
        slow_tests = [t for t in test_times if t["duration"] > 30]  # > 30 seconds
        
        if slow_tests:
            suggestions.append({
                "type": "parallel_execution",
                "description": "Run slow tests in parallel",
                "tests": [t["name"] for t in slow_tests],
                "estimated_improvement": f"{sum(t['duration'] for t in slow_tests) / 4:.1f}s saved"
            })
        
        # Suggest test grouping
        test_groups = self._analyze_test_dependencies()
        if test_groups:
            suggestions.append({
                "type": "test_grouping",
                "description": "Group independent tests for parallel execution",
                "groups": test_groups,
                "estimated_improvement": "30-50% faster execution"
            })
        
        # Suggest fixture optimization
        fixture_suggestions = self._analyze_fixture_usage()
        if fixture_suggestions:
            suggestions.extend(fixture_suggestions)
        
        return suggestions
    
    def _suggest_new_tests(self) -> List[Dict]:
        """Suggest new tests based on code coverage analysis"""
        print("🧪 Suggesting new tests...")
        
        suggestions = []
        
        # Analyze code coverage
        coverage_data = self._get_coverage_data()
        
        if coverage_data:
            # Find uncovered code
            uncovered_files = [
                f for f in coverage_data.get("files", [])
                if f.get("coverage", 100) < 80
            ]
            
            for file_info in uncovered_files[:10]:  # Top 10 files needing tests
                suggestions.append({
                    "type": "coverage_improvement",
                    "file": file_info["filename"],
                    "current_coverage": file_info.get("coverage", 0),
                    "missing_lines": file_info.get("missing_lines", []),
                    "priority": "high" if file_info.get("coverage", 0) < 50 else "medium"
                })
        
        # Suggest integration tests
        integration_suggestions = self._suggest_integration_tests()
        suggestions.extend(integration_suggestions)
        
        return suggestions
    
    def _apply_optimizations_with_codegen(self, results: Dict) -> List[str]:
        """Apply optimizations using Codegen SDK"""
        print("🤖 Applying optimizations with Codegen SDK...")
        
        actions = []
        
        # Create tasks for high-priority issues
        high_priority_flaky = [
            t for t in results["flaky_tests"] 
            if t["severity"] == "high"
        ]
        
        if high_priority_flaky:
            prompt = f"""
            Fix the following flaky tests in the Graph-Sitter test suite:
            
            {json.dumps(high_priority_flaky, indent=2)}
            
            For each flaky test:
            1. Investigate the root cause of flakiness
            2. Implement fixes (add timeouts, improve isolation, use mocks)
            3. Add retry mechanisms if appropriate
            4. Update test documentation
            
            Focus on the highest failure rate tests first.
            """
            
            try:
                task = self.agent.run(prompt=prompt)
                actions.append(f"Created Codegen task for flaky test fixes: {task.id}")
            except Exception as e:
                actions.append(f"Failed to create Codegen task: {e}")
        
        # Create task for performance optimizations
        if results["parallelization_suggestions"]:
            prompt = f"""
            Optimize the Graph-Sitter test suite performance based on these suggestions:
            
            {json.dumps(results["parallelization_suggestions"], indent=2)}
            
            Implement:
            1. Parallel test execution improvements
            2. Fixture scope optimizations
            3. Test grouping for better parallelization
            4. Performance monitoring
            """
            
            try:
                task = self.agent.run(prompt=prompt)
                actions.append(f"Created Codegen task for performance optimization: {task.id}")
            except Exception as e:
                actions.append(f"Failed to create performance optimization task: {e}")
        
        return actions
    
    def _apply_optimizations_standalone(self, results: Dict) -> List[str]:
        """Apply optimizations without Codegen SDK"""
        print("🔧 Applying optimizations in standalone mode...")
        
        actions = []
        
        # Create GitHub issues for high-priority items
        if self.github_token and results["flaky_tests"]:
            high_priority_flaky = [
                t for t in results["flaky_tests"] 
                if t["severity"] == "high"
            ]
            
            if high_priority_flaky:
                issue_created = self._create_github_issue(
                    title="🎲 Fix Flaky Tests Identified by Autonomous Analysis",
                    body=self._format_flaky_tests_issue(high_priority_flaky)
                )
                if issue_created:
                    actions.append("Created GitHub issue for flaky test fixes")
        
        # Apply simple optimizations directly
        optimizations_applied = self._apply_simple_optimizations(results)
        actions.extend(optimizations_applied)
        
        return actions
    
    def _get_recent_workflow_runs(self, limit: int = 50) -> List[Dict]:
        """Get recent workflow runs from GitHub API"""
        if not self.github_token:
            return []
        
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get repository info from environment or git
            repo = os.getenv("GITHUB_REPOSITORY", "Zeeeepa/graph-sitter")
            
            url = f"https://api.github.com/repos/{repo}/actions/runs"
            params = {"per_page": limit, "status": "completed"}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json().get("workflow_runs", [])
        
        except Exception as e:
            print(f"⚠️  Failed to get workflow runs: {e}")
            return []
    
    def _extract_failed_tests_from_run(self, run: Dict) -> List[str]:
        """Extract failed test names from a workflow run"""
        # This would require parsing job logs or artifacts
        # For now, return empty list as placeholder
        return []
    
    def _get_test_execution_times(self) -> List[Dict]:
        """Get test execution times from recent runs"""
        # Placeholder - would parse test reports or logs
        return []
    
    def _analyze_test_dependencies(self) -> List[Dict]:
        """Analyze test dependencies for grouping"""
        # Placeholder - would analyze test imports and fixtures
        return []
    
    def _analyze_fixture_usage(self) -> List[Dict]:
        """Analyze fixture usage for optimization suggestions"""
        suggestions = []
        
        # Look for expensive fixtures that could be session-scoped
        conftest_files = list(Path("tests").rglob("conftest.py"))
        
        for conftest_file in conftest_files:
            try:
                content = conftest_file.read_text()
                
                # Find fixtures without explicit scope
                if "@pytest.fixture\ndef" in content and "scope=" not in content:
                    suggestions.append({
                        "type": "fixture_scope_optimization",
                        "file": str(conftest_file),
                        "description": "Add explicit scopes to fixtures",
                        "priority": "medium"
                    })
            except Exception:
                continue
        
        return suggestions
    
    def _get_coverage_data(self) -> Dict:
        """Get test coverage data"""
        try:
            # Try to run coverage and get data
            result = subprocess.run(
                ["python", "-m", "coverage", "json", "--quiet"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        
        return {}
    
    def _suggest_integration_tests(self) -> List[Dict]:
        """Suggest integration tests based on code analysis"""
        suggestions = []
        
        # Look for API endpoints without integration tests
        api_files = list(Path("src").rglob("*api*.py")) if Path("src").exists() else []
        
        for api_file in api_files:
            # Check if corresponding integration test exists
            test_file = Path("tests/integration") / f"test_{api_file.stem}.py"
            if not test_file.exists():
                suggestions.append({
                    "type": "integration_test",
                    "file": str(api_file),
                    "suggested_test": str(test_file),
                    "description": f"Add integration tests for {api_file.name}",
                    "priority": "medium"
                })
        
        return suggestions
    
    def _create_github_issue(self, title: str, body: str) -> bool:
        """Create a GitHub issue"""
        if not self.github_token:
            return False
        
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            repo = os.getenv("GITHUB_REPOSITORY", "Zeeeepa/graph-sitter")
            url = f"https://api.github.com/repos/{repo}/issues"
            
            data = {
                "title": title,
                "body": body,
                "labels": ["testing", "automation", "performance"]
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return True
        
        except Exception as e:
            print(f"⚠️  Failed to create GitHub issue: {e}")
            return False
    
    def _format_flaky_tests_issue(self, flaky_tests: List[Dict]) -> str:
        """Format flaky tests for GitHub issue"""
        body = [
            "## 🎲 Flaky Tests Detected",
            "",
            "The autonomous test analyzer has identified the following flaky tests:",
            ""
        ]
        
        for test in flaky_tests:
            body.extend([
                f"### {test['test_name']}",
                f"- **Failure Rate**: {test['failure_rate']:.1%}",
                f"- **Failures**: {test['failure_count']}/{test['total_runs']} runs",
                f"- **Severity**: {test['severity']}",
                ""
            ])
        
        body.extend([
            "## 🔧 Recommended Actions",
            "",
            "1. Investigate root causes of flakiness",
            "2. Add proper timeouts and retries",
            "3. Improve test isolation",
            "4. Use mocks for external dependencies",
            "5. Add debugging information for failures",
            "",
            "---",
            "*This issue was created automatically by the autonomous test optimizer.*"
        ])
        
        return "\n".join(body)
    
    def _apply_simple_optimizations(self, results: Dict) -> List[str]:
        """Apply simple optimizations that don't require complex changes"""
        actions = []
        
        # Update pytest configuration for better parallelization
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text()
                
                # Add parallel execution if not present
                if "--dist=loadgroup" not in content:
                    # This would require more sophisticated TOML parsing
                    actions.append("Suggested adding parallel execution to pytest config")
                
            except Exception:
                pass
        
        return actions


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous test suite optimizer")
    parser.add_argument("--analyze-flaky-tests", action="store_true", default=True,
                       help="Analyze flaky tests")
    parser.add_argument("--optimize-parallelization", action="store_true", default=True,
                       help="Optimize test parallelization")
    parser.add_argument("--suggest-new-tests", action="store_true", default=True,
                       help="Suggest new tests")
    parser.add_argument("--output", default="test_optimization_results.json",
                       help="Output file for results")
    
    args = parser.parse_args()
    
    print("🚀 Autonomous Test Suite Optimizer")
    print("=" * 50)
    
    optimizer = AutonomousTestOptimizer()
    
    results = optimizer.optimize_test_suite(
        analyze_flaky=args.analyze_flaky_tests,
        optimize_parallelization=args.optimize_parallelization,
        suggest_new_tests=args.suggest_new_tests
    )
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to: {args.output}")
    
    # Print summary
    print("\n📈 Optimization Summary:")
    print(f"  - Flaky tests found: {len(results['flaky_tests'])}")
    print(f"  - Performance suggestions: {len(results['parallelization_suggestions'])}")
    print(f"  - New test suggestions: {len(results['new_test_suggestions'])}")
    print(f"  - Actions taken: {len(results['actions_taken'])}")
    
    if results['actions_taken']:
        print("\n🔧 Actions taken:")
        for action in results['actions_taken']:
            print(f"  - {action}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

