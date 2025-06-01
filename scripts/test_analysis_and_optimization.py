#!/usr/bin/env python3
"""
Test Analysis and Optimization Script
Comprehensive analysis and optimization of the Graph-Sitter test suite
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
import json

@dataclass
class TestIssue:
    """Represents a test issue found during analysis"""
    file_path: str
    line_number: int
    issue_type: str
    reason: str
    severity: str
    fix_suggestion: str

@dataclass
class TestMetrics:
    """Test suite metrics"""
    total_test_files: int
    total_tests: int
    skipped_tests: int
    xfail_tests: int
    platform_specific_skips: int
    performance_issues: int
    unused_fixtures: int
    duplicate_tests: int

class TestSuiteAnalyzer:
    """Analyzes the test suite for issues and optimization opportunities"""
    
    def __init__(self, test_dir: str = "tests"):
        self.test_dir = Path(test_dir)
        self.issues: List[TestIssue] = []
        self.metrics = TestMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
    def analyze_all(self) -> Tuple[bool, Dict]:
        """Run comprehensive test analysis"""
        print("🔍 Starting comprehensive test suite analysis...")
        
        results = {
            "skipped_tests": self._analyze_skipped_tests(),
            "unused_utilities": self._find_unused_test_utilities(),
            "performance_issues": self._analyze_performance_issues(),
            "test_isolation": self._check_test_isolation(),
            "coverage_gaps": self._analyze_coverage_gaps(),
            "flaky_tests": self._identify_flaky_tests(),
            "duplicate_tests": self._find_duplicate_tests(),
            "fixture_usage": self._analyze_fixture_usage()
        }
        
        self._calculate_metrics()
        return len(self.issues) == 0, results
    
    def _analyze_skipped_tests(self) -> Dict:
        """Analyze all skipped and xfail tests"""
        print("📊 Analyzing skipped and xfail tests...")
        
        skipped_patterns = {
            r'@pytest\.mark\.skip\(reason="([^"]+)"\)': 'skip',
            r'@pytest\.mark\.skip\("([^"]+)"\)': 'skip',
            r'@pytest\.mark\.skip': 'skip_no_reason',
            r'@pytest\.mark\.xfail\(reason="([^"]+)"\)': 'xfail',
            r'@pytest\.mark\.xfail': 'xfail_no_reason',
            r'@pytest\.mark\.skipif\([^,]+,\s*reason="([^"]+)"\)': 'skipif'
        }
        
        skip_analysis = defaultdict(list)
        reason_counts = Counter()
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, skip_type in skipped_patterns.items():
                        match = re.search(pattern, line)
                        if match:
                            reason = match.group(1) if match.groups() else "No reason provided"
                            
                            skip_analysis[skip_type].append({
                                'file': str(test_file.relative_to(self.test_dir)),
                                'line': i,
                                'reason': reason,
                                'content': line.strip()
                            })
                            
                            reason_counts[reason] += 1
                            
                            # Categorize issues
                            severity = self._categorize_skip_severity(reason, skip_type)
                            fix_suggestion = self._suggest_skip_fix(reason, skip_type)
                            
                            self.issues.append(TestIssue(
                                file_path=str(test_file),
                                line_number=i,
                                issue_type=skip_type,
                                reason=reason,
                                severity=severity,
                                fix_suggestion=fix_suggestion
                            ))
        
        return {
            'skip_analysis': dict(skip_analysis),
            'reason_counts': dict(reason_counts),
            'total_skipped': sum(len(v) for v in skip_analysis.values())
        }
    
    def _categorize_skip_severity(self, reason: str, skip_type: str) -> str:
        """Categorize the severity of a skipped test"""
        high_priority = [
            "broken", "timing out", "needs investigation", "wip",
            "not yet implemented", "todo"
        ]
        
        medium_priority = [
            "macos is case-insensitive", "case-sensitive", "platform"
        ]
        
        low_priority = [
            "performance reasons", "not implementing", "much better ways"
        ]
        
        reason_lower = reason.lower()
        
        if any(keyword in reason_lower for keyword in high_priority):
            return "HIGH"
        elif any(keyword in reason_lower for keyword in medium_priority):
            return "MEDIUM"
        elif any(keyword in reason_lower for keyword in low_priority):
            return "LOW"
        else:
            return "MEDIUM"
    
    def _suggest_skip_fix(self, reason: str, skip_type: str) -> str:
        """Suggest fixes for skipped tests"""
        reason_lower = reason.lower()
        
        if "macos is case-insensitive" in reason_lower:
            return "Use pytest.mark.skipif with proper platform detection or mock filesystem"
        elif "wip" in reason_lower or "todo" in reason_lower:
            return "Complete implementation or remove test if no longer needed"
        elif "timing out" in reason_lower:
            return "Investigate timeout cause, add proper timeouts, or optimize test"
        elif "not yet implemented" in reason_lower:
            return "Implement feature or remove test if feature cancelled"
        elif "performance reasons" in reason_lower:
            return "Optimize test or move to performance test suite"
        elif "broken" in reason_lower:
            return "Fix test implementation or underlying code"
        else:
            return "Review test necessity and fix underlying issue"
    
    def _find_unused_test_utilities(self) -> Dict:
        """Find unused test utilities and fixtures"""
        print("🔍 Finding unused test utilities...")
        
        # Find all utility functions and fixtures
        utilities = set()
        fixtures = set()
        used_items = set()
        
        for test_file in self.test_dir.rglob("*.py"):
            content = test_file.read_text(encoding='utf-8', errors='ignore')
            
            # Find fixture definitions
            fixture_matches = re.findall(r'@pytest\.fixture[^\n]*\ndef\s+(\w+)', content)
            fixtures.update(fixture_matches)
            
            # Find utility function definitions in shared/
            if "shared" in str(test_file):
                func_matches = re.findall(r'def\s+(\w+)\s*\(', content)
                utilities.update(func_matches)
            
            # Find usage of utilities and fixtures
            for line in content.split('\n'):
                # Simple heuristic for function calls
                calls = re.findall(r'(\w+)\s*\(', line)
                used_items.update(calls)
        
        unused_utilities = utilities - used_items
        unused_fixtures = fixtures - used_items
        
        return {
            'unused_utilities': list(unused_utilities),
            'unused_fixtures': list(unused_fixtures),
            'total_utilities': len(utilities),
            'total_fixtures': len(fixtures)
        }
    
    def _analyze_performance_issues(self) -> Dict:
        """Analyze test performance issues"""
        print("⚡ Analyzing test performance...")
        
        performance_issues = []
        
        # Look for potential performance issues
        performance_patterns = [
            (r'time\.sleep\(\d+\)', 'Long sleep detected'),
            (r'\.join\(\)\s*$', 'Blocking join without timeout'),
            (r'while\s+True:', 'Infinite loop potential'),
            (r'for\s+\w+\s+in\s+range\(\d{4,}\)', 'Large range iteration'),
            (r'@pytest\.mark\.slow', 'Marked as slow test')
        ]
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, issue_desc in performance_patterns:
                        if re.search(pattern, line):
                            performance_issues.append({
                                'file': str(test_file.relative_to(self.test_dir)),
                                'line': i,
                                'issue': issue_desc,
                                'content': line.strip()
                            })
        
        return {
            'performance_issues': performance_issues,
            'total_issues': len(performance_issues)
        }
    
    def _check_test_isolation(self) -> Dict:
        """Check for test isolation issues"""
        print("🔒 Checking test isolation...")
        
        isolation_issues = []
        
        # Patterns that might indicate isolation issues
        isolation_patterns = [
            (r'global\s+\w+', 'Global variable modification'),
            (r'os\.environ\[', 'Environment variable modification'),
            (r'sys\.path\.', 'sys.path modification'),
            (r'monkeypatch\.setattr\([^)]*\)', 'Monkeypatch without proper cleanup'),
            (r'@pytest\.fixture\([^)]*scope=["\']session["\']', 'Session-scoped fixture')
        ]
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, issue_desc in isolation_patterns:
                        if re.search(pattern, line):
                            isolation_issues.append({
                                'file': str(test_file.relative_to(self.test_dir)),
                                'line': i,
                                'issue': issue_desc,
                                'content': line.strip()
                            })
        
        return {
            'isolation_issues': isolation_issues,
            'total_issues': len(isolation_issues)
        }
    
    def _analyze_coverage_gaps(self) -> Dict:
        """Analyze test coverage gaps"""
        print("📈 Analyzing coverage gaps...")
        
        # This would ideally integrate with coverage.py
        # For now, we'll do a basic analysis
        
        src_files = list(Path("src").rglob("*.py")) if Path("src").exists() else []
        test_files = list(self.test_dir.rglob("test_*.py"))
        
        # Simple heuristic: check if each source file has corresponding tests
        coverage_analysis = {
            'total_source_files': len(src_files),
            'total_test_files': len(test_files),
            'potentially_untested': []
        }
        
        for src_file in src_files:
            # Look for corresponding test file
            relative_path = src_file.relative_to("src")
            potential_test_names = [
                f"test_{relative_path.stem}.py",
                f"test_{relative_path.stem}_test.py",
                f"{relative_path.stem}_test.py"
            ]
            
            has_test = any(
                test_file.name in potential_test_names
                for test_file in test_files
            )
            
            if not has_test and not src_file.name.startswith("__"):
                coverage_analysis['potentially_untested'].append(str(relative_path))
        
        return coverage_analysis
    
    def _identify_flaky_tests(self) -> Dict:
        """Identify potentially flaky tests"""
        print("🎲 Identifying potentially flaky tests...")
        
        flaky_indicators = []
        
        # Patterns that might indicate flaky tests
        flaky_patterns = [
            (r'time\.sleep\(', 'Uses sleep (timing dependent)'),
            (r'random\.', 'Uses random values'),
            (r'datetime\.now\(\)', 'Uses current time'),
            (r'threading\.', 'Uses threading'),
            (r'multiprocessing\.', 'Uses multiprocessing'),
            (r'@pytest\.mark\.flaky', 'Marked as flaky'),
            (r'retry|attempt', 'Has retry logic')
        ]
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, indicator in flaky_patterns:
                        if re.search(pattern, line):
                            flaky_indicators.append({
                                'file': str(test_file.relative_to(self.test_dir)),
                                'line': i,
                                'indicator': indicator,
                                'content': line.strip()
                            })
        
        return {
            'flaky_indicators': flaky_indicators,
            'total_indicators': len(flaky_indicators)
        }
    
    def _find_duplicate_tests(self) -> Dict:
        """Find potentially duplicate tests"""
        print("🔍 Finding duplicate tests...")
        
        test_signatures = defaultdict(list)
        
        for test_file in self.test_dir.rglob("*.py"):
            if test_file.name.startswith("test_"):
                content = test_file.read_text(encoding='utf-8', errors='ignore')
                
                # Extract test function signatures
                test_functions = re.findall(r'def\s+(test_\w+)\s*\([^)]*\):', content)
                
                for func_name in test_functions:
                    test_signatures[func_name].append(str(test_file.relative_to(self.test_dir)))
        
        # Find duplicates
        duplicates = {
            name: files for name, files in test_signatures.items()
            if len(files) > 1
        }
        
        return {
            'duplicate_tests': duplicates,
            'total_duplicates': len(duplicates)
        }
    
    def _analyze_fixture_usage(self) -> Dict:
        """Analyze fixture usage patterns"""
        print("🔧 Analyzing fixture usage...")
        
        fixture_definitions = {}
        fixture_usage = defaultdict(int)
        
        for test_file in self.test_dir.rglob("*.py"):
            content = test_file.read_text(encoding='utf-8', errors='ignore')
            
            # Find fixture definitions
            fixture_matches = re.findall(
                r'@pytest\.fixture[^\n]*\ndef\s+(\w+)', content
            )
            
            for fixture_name in fixture_matches:
                fixture_definitions[fixture_name] = str(test_file.relative_to(self.test_dir))
            
            # Count fixture usage
            for fixture_name in fixture_definitions:
                usage_count = len(re.findall(rf'\b{fixture_name}\b', content))
                fixture_usage[fixture_name] += usage_count
        
        return {
            'fixture_definitions': fixture_definitions,
            'fixture_usage': dict(fixture_usage),
            'unused_fixtures': [
                name for name, count in fixture_usage.items() if count <= 1
            ]
        }
    
    def _calculate_metrics(self):
        """Calculate overall test metrics"""
        test_files = list(self.test_dir.rglob("test_*.py"))
        self.metrics.total_test_files = len(test_files)
        
        # Count different types of issues
        for issue in self.issues:
            if issue.issue_type in ['skip', 'skip_no_reason']:
                self.metrics.skipped_tests += 1
            elif issue.issue_type in ['xfail', 'xfail_no_reason']:
                self.metrics.xfail_tests += 1
            elif 'platform' in issue.reason.lower() or 'macos' in issue.reason.lower():
                self.metrics.platform_specific_skips += 1
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive analysis report"""
        report = []
        report.append("# Test Suite Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        # Metrics summary
        report.append("## 📊 Test Suite Metrics")
        report.append(f"- Total test files: {self.metrics.total_test_files}")
        report.append(f"- Skipped tests: {self.metrics.skipped_tests}")
        report.append(f"- XFail tests: {self.metrics.xfail_tests}")
        report.append(f"- Platform-specific skips: {self.metrics.platform_specific_skips}")
        report.append("")
        
        # Skipped tests analysis
        if results['skipped_tests']['total_skipped'] > 0:
            report.append("## ⚠️ Skipped Tests Analysis")
            report.append(f"Total skipped: {results['skipped_tests']['total_skipped']}")
            report.append("")
            
            report.append("### Top skip reasons:")
            for reason, count in sorted(
                results['skipped_tests']['reason_counts'].items(),
                key=lambda x: x[1], reverse=True
            )[:10]:
                report.append(f"- {reason}: {count}")
            report.append("")
        
        # Performance issues
        if results['performance_issues']['total_issues'] > 0:
            report.append("## ⚡ Performance Issues")
            report.append(f"Total issues found: {results['performance_issues']['total_issues']}")
            report.append("")
        
        # Coverage gaps
        untested_count = len(results['coverage_gaps']['potentially_untested'])
        if untested_count > 0:
            report.append("## 📈 Coverage Gaps")
            report.append(f"Potentially untested files: {untested_count}")
            report.append("")
        
        # Recommendations
        report.append("## 🎯 Recommendations")
        report.append("")
        
        if self.metrics.skipped_tests > 10:
            report.append("1. **High Priority**: Address skipped tests - over 10 tests are currently skipped")
        
        if results['performance_issues']['total_issues'] > 5:
            report.append("2. **Medium Priority**: Optimize test performance - multiple performance issues detected")
        
        if untested_count > 20:
            report.append("3. **Medium Priority**: Improve test coverage - many source files lack corresponding tests")
        
        if results['duplicate_tests']['total_duplicates'] > 0:
            report.append("4. **Low Priority**: Remove duplicate tests to reduce maintenance overhead")
        
        return "\n".join(report)
    
    def print_results(self):
        """Print analysis results"""
        print("\n" + "=" * 60)
        print("📊 TEST SUITE ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"\n📈 Metrics:")
        print(f"  Total test files: {self.metrics.total_test_files}")
        print(f"  Skipped tests: {self.metrics.skipped_tests}")
        print(f"  XFail tests: {self.metrics.xfail_tests}")
        print(f"  Platform-specific skips: {self.metrics.platform_specific_skips}")
        
        # Print high-priority issues
        high_priority_issues = [i for i in self.issues if i.severity == "HIGH"]
        if high_priority_issues:
            print(f"\n🚨 High Priority Issues ({len(high_priority_issues)}):")
            for issue in high_priority_issues[:5]:  # Show first 5
                print(f"  - {Path(issue.file_path).name}:{issue.line_number} - {issue.reason}")
        
        print(f"\n✅ Analysis complete. Found {len(self.issues)} total issues.")


def main():
    """Main analysis entry point"""
    print("🚀 Graph-Sitter Test Suite Analysis & Optimization")
    print("=" * 60)
    
    analyzer = TestSuiteAnalyzer()
    success, results = analyzer.analyze_all()
    
    # Generate and save report
    report = analyzer.generate_report(results)
    
    report_file = Path("test_analysis_report.md")
    report_file.write_text(report)
    
    # Print results
    analyzer.print_results()
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Save detailed results as JSON
    results_file = Path("test_analysis_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📊 Detailed results saved to: {results_file}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

