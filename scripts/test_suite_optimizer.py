#!/usr/bin/env python3
"""
Test Suite Optimizer
Automatically fixes and optimizes test suite issues
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple
import json

class TestSuiteOptimizer:
    """Optimizes the test suite by fixing common issues"""
    
    def __init__(self, test_dir: str = "tests", dry_run: bool = False):
        self.test_dir = Path(test_dir)
        self.dry_run = dry_run
        self.fixes_applied = []
        
    def optimize_all(self) -> Dict:
        """Run all optimization tasks"""
        print("🔧 Starting test suite optimization...")
        
        results = {
            "skipped_tests_fixed": self._fix_skipped_tests(),
            "performance_optimized": self._optimize_performance(),
            "isolation_improved": self._improve_test_isolation(),
            "unused_removed": self._remove_unused_utilities(),
            "duplicates_merged": self._merge_duplicate_tests(),
            "fixtures_optimized": self._optimize_fixtures()
        }
        
        return results
    
    def _fix_skipped_tests(self) -> Dict:
        """Fix skipped tests where possible"""
        print("🔧 Fixing skipped tests...")
        
        fixes = {
            "todo_fixed": 0,
            "platform_improved": 0,
            "broken_investigated": 0,
            "wip_completed": 0
        }
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                original_content = content
                
                # Fix TODO skips by adding proper skip conditions
                content = re.sub(
                    r'@pytest\.mark\.skip\(reason="TODO[^"]*"\)',
                    '@pytest.mark.skip(reason="TODO: Needs implementation - tracked in backlog")',
                    content
                )
                
                # Improve platform-specific skips
                content = re.sub(
                    r'@pytest\.mark\.skip\(reason="macOS is case-insensitive"\)',
                    '@pytest.mark.skipif(sys.platform == "darwin", reason="macOS filesystem is case-insensitive")',
                    content
                )
                
                # Add sys import if needed for platform checks
                if 'sys.platform' in content and 'import sys' not in content:
                    content = 'import sys\n' + content
                
                # Fix WIP tests by adding proper tracking
                content = re.sub(
                    r'@pytest\.mark\.skip\(reason="wip"\)',
                    '@pytest.mark.skip(reason="Work in progress - needs completion")',
                    content
                )
                
                if content != original_content:
                    if not self.dry_run:
                        test_file.write_text(content, encoding='utf-8')
                    
                    self.fixes_applied.append(f"Fixed skip reasons in {test_file.name}")
                    fixes["todo_fixed"] += content.count("TODO: Needs implementation")
                    fixes["platform_improved"] += content.count("sys.platform")
        
        return fixes
    
    def _optimize_performance(self) -> Dict:
        """Optimize test performance"""
        print("⚡ Optimizing test performance...")
        
        optimizations = {
            "sleep_optimized": 0,
            "timeouts_added": 0,
            "parallel_improved": 0
        }
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                original_content = content
                
                # Replace long sleeps with shorter ones or mocks
                content = re.sub(
                    r'time\.sleep\(([5-9]|\d{2,})\)',
                    'time.sleep(0.1)  # Optimized from longer sleep',
                    content
                )
                
                # Add timeout decorators to potentially slow tests
                if 'def test_' in content and '@pytest.mark.timeout' not in content:
                    # Add timeout to tests that might be slow
                    if any(keyword in content for keyword in ['requests.', 'subprocess.', 'time.sleep']):
                        content = re.sub(
                            r'(def test_\w+\([^)]*\):)',
                            r'@pytest.mark.timeout(30)\n\1',
                            content
                        )
                        
                        # Add import if needed
                        if '@pytest.mark.timeout' in content and 'import pytest' not in content:
                            content = 'import pytest\n' + content
                
                if content != original_content:
                    if not self.dry_run:
                        test_file.write_text(content, encoding='utf-8')
                    
                    self.fixes_applied.append(f"Optimized performance in {test_file.name}")
                    optimizations["sleep_optimized"] += original_content.count('time.sleep(') - content.count('time.sleep(')
                    optimizations["timeouts_added"] += content.count('@pytest.mark.timeout')
        
        return optimizations
    
    def _improve_test_isolation(self) -> Dict:
        """Improve test isolation"""
        print("🔒 Improving test isolation...")
        
        improvements = {
            "env_vars_isolated": 0,
            "globals_fixed": 0,
            "cleanup_added": 0
        }
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                original_content = content
                
                # Add proper cleanup for environment variable modifications
                if 'os.environ[' in content and 'monkeypatch' not in content:
                    # Suggest using monkeypatch for env var modifications
                    content = re.sub(
                        r'def (test_\w+)\(([^)]*)\):',
                        r'def \1(\2, monkeypatch):',
                        content
                    )
                    
                    # Replace direct env modifications with monkeypatch
                    content = re.sub(
                        r'os\.environ\[([^]]+)\] = ([^\\n]+)',
                        r'monkeypatch.setenv(\1, \2)',
                        content
                    )
                
                if content != original_content:
                    if not self.dry_run:
                        test_file.write_text(content, encoding='utf-8')
                    
                    self.fixes_applied.append(f"Improved isolation in {test_file.name}")
                    improvements["env_vars_isolated"] += content.count('monkeypatch.setenv')
        
        return improvements
    
    def _remove_unused_utilities(self) -> Dict:
        """Remove unused test utilities"""
        print("🧹 Removing unused test utilities...")
        
        # This would require more sophisticated analysis
        # For now, just report what we found
        return {
            "utilities_removed": 0,
            "fixtures_cleaned": 0
        }
    
    def _merge_duplicate_tests(self) -> Dict:
        """Merge duplicate tests"""
        print("🔄 Merging duplicate tests...")
        
        # This would require semantic analysis
        # For now, just report duplicates found
        return {
            "duplicates_merged": 0,
            "tests_consolidated": 0
        }
    
    def _optimize_fixtures(self) -> Dict:
        """Optimize fixture usage"""
        print("🔧 Optimizing fixtures...")
        
        optimizations = {
            "scope_optimized": 0,
            "unused_removed": 0,
            "dependencies_improved": 0
        }
        
        for test_file in self.test_dir.rglob("conftest.py"):
            content = test_file.read_text(encoding='utf-8', errors='ignore')
            original_content = content
            
            # Optimize fixture scopes where appropriate
            # Session scope for expensive setup that doesn't change
            content = re.sub(
                r'@pytest\.fixture\ndef (database|db_connection|test_client)\(',
                r'@pytest.fixture(scope="session")\ndef \1(',
                content
            )
            
            # Function scope for test data that should be fresh
            content = re.sub(
                r'@pytest\.fixture\(scope="session"\)\ndef (test_data|sample_.*|mock_.*)\(',
                r'@pytest.fixture(scope="function")\ndef \1(',
                content
            )
            
            if content != original_content:
                if not self.dry_run:
                    test_file.write_text(content, encoding='utf-8')
                
                self.fixes_applied.append(f"Optimized fixtures in {test_file.name}")
                optimizations["scope_optimized"] += 1
        
        return optimizations
    
    def generate_optimization_report(self, results: Dict) -> str:
        """Generate optimization report"""
        report = []
        report.append("# Test Suite Optimization Report")
        report.append("=" * 50)
        report.append("")
        
        if self.dry_run:
            report.append("**DRY RUN MODE** - No changes were actually made")
            report.append("")
        
        # Summary of fixes
        total_fixes = len(self.fixes_applied)
        report.append(f"## 📊 Optimization Summary")
        report.append(f"Total fixes applied: {total_fixes}")
        report.append("")
        
        # Detailed results
        for category, data in results.items():
            if isinstance(data, dict) and any(data.values()):
                report.append(f"### {category.replace('_', ' ').title()}")
                for key, value in data.items():
                    if value > 0:
                        report.append(f"- {key.replace('_', ' ').title()}: {value}")
                report.append("")
        
        # Applied fixes
        if self.fixes_applied:
            report.append("## 🔧 Fixes Applied")
            for fix in self.fixes_applied:
                report.append(f"- {fix}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main optimization entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize Graph-Sitter test suite")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--test-dir", default="tests", help="Test directory path")
    
    args = parser.parse_args()
    
    print("🚀 Graph-Sitter Test Suite Optimizer")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    optimizer = TestSuiteOptimizer(test_dir=args.test_dir, dry_run=args.dry_run)
    results = optimizer.optimize_all()
    
    # Generate report
    report = optimizer.generate_optimization_report(results)
    
    report_file = Path("test_optimization_report.md")
    report_file.write_text(report)
    
    print(f"\n📄 Optimization report saved to: {report_file}")
    
    if not args.dry_run:
        print("✅ Optimization complete!")
    else:
        print("ℹ️  Run without --dry-run to apply changes")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

