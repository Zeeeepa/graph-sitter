"""
Tests for the GitHub comment formatter.
"""
import unittest

from graph_sitter.extensions.github.pr_analysis.comment_formatter import GitHubCommentFormatter


class TestGitHubCommentFormatter(unittest.TestCase):
    """Tests for the GitHub comment formatter."""

    def setUp(self):
        """Set up the test case."""
        self.formatter = GitHubCommentFormatter()
        self.pr_context = {
            'number': 123,
            'title': 'Test PR',
            'html_url': 'https://github.com/owner/repo/pull/123'
        }

    def test_format_results_empty(self):
        """Test formatting empty results."""
        results = []
        comment = self.formatter.format_results(results, self.pr_context)
        
        self.assertIn('# PR Analysis Results for #123', comment)
        self.assertIn('No issues found! :white_check_mark:', comment)

    def test_format_results_with_issues(self):
        """Test formatting results with issues."""
        results = [
            {
                'rule_id': 'UNUSED_IMPORT',
                'message': 'Unused import detected',
                'severity': 'warning',
                'file': 'src/example.py',
                'line': 10,
                'code_snippet': 'import os  # This import is not used',
                'suggestion': 'Remove the unused import'
            },
            {
                'rule_id': 'SYNTAX_ERROR',
                'message': 'Syntax error detected',
                'severity': 'error',
                'file': 'src/example.py',
                'line': 15,
                'code_snippet': 'def function(:\n    pass',
                'suggestion': 'Fix the syntax error in the function definition'
            }
        ]
        
        comment = self.formatter.format_results(results, self.pr_context)
        
        # Check header
        self.assertIn('# PR Analysis Results for #123', comment)
        
        # Check summary table
        self.assertIn('| Severity | Count |', comment)
        self.assertIn('| :warning: Warning | 1 |', comment)
        self.assertIn('| :x: Error | 1 |', comment)
        
        # Check warning section
        self.assertIn('## :warning: Warning Issues', comment)
        self.assertIn('### UNUSED_IMPORT: Unused import detected', comment)
        self.assertIn('**File:** `src/example.py`', comment)
        self.assertIn('**Line:** 10', comment)
        self.assertIn('```\nimport os  # This import is not used\n```', comment)
        self.assertIn('**Suggestion:** Remove the unused import', comment)
        
        # Check error section
        self.assertIn('## :x: Error Issues', comment)
        self.assertIn('### SYNTAX_ERROR: Syntax error detected', comment)
        self.assertIn('**File:** `src/example.py`', comment)
        self.assertIn('**Line:** 15', comment)
        self.assertIn('```\ndef function(:\n    pass\n```', comment)
        self.assertIn('**Suggestion:** Fix the syntax error in the function definition', comment)


if __name__ == '__main__':
    unittest.main()

