"""
Tests for PR static analysis.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from graph_sitter.git.auth.github_auth import GitHubAuth
from graph_sitter.git.clients.github_api_client import GitHubAPIClient
from graph_sitter.git.pr_analysis.pr_analyzer import PRAnalyzer
from graph_sitter.git.utils.comment_formatter import CommentFormatter
from graph_sitter.git.webhook.webhook_handler import WebhookHandler


class TestCommentFormatter(unittest.TestCase):
    """Tests for the CommentFormatter class."""
    
    def setUp(self):
        self.formatter = CommentFormatter()
    
    def test_format_general_comment(self):
        """Test formatting a general comment."""
        comment = self.formatter.format_general_comment(
            title="Test Analysis",
            summary="Found 2 issues",
            details=[
                {
                    "type": "warning",
                    "title": "Unused variable",
                    "message": "Variable 'foo' is defined but never used",
                    "location": {"file": "test.py", "line_start": 10}
                }
            ],
            conclusion="Please fix the issues"
        )
        
        self.assertIn("Test Analysis", comment)
        self.assertIn("Found 2 issues", comment)
        self.assertIn("Unused variable", comment)
        self.assertIn("Please fix the issues", comment)
    
    def test_format_inline_comment(self):
        """Test formatting an inline comment."""
        comment = self.formatter.format_inline_comment(
            issue="Variable 'foo' is defined but never used",
            suggestion="Remove the variable or use it",
            code_snippet="# Remove this line\nfoo = 42",
            severity="warning"
        )
        
        self.assertIn("Variable 'foo' is defined but never used", comment)
        self.assertIn("Remove the variable or use it", comment)
        self.assertIn("# Remove this line", comment)
        self.assertIn("foo = 42", comment)
    
    def test_format_summary_comment(self):
        """Test formatting a summary comment."""
        comment = self.formatter.format_summary_comment(
            issues_by_type={"warning": 2, "error": 1},
            files_analyzed=5,
            total_issues=3
        )
        
        self.assertIn("Analyzed **5** files", comment)
        self.assertIn("found **3** issues", comment)
        self.assertIn("Warning", comment)
        self.assertIn("Error", comment)


class TestWebhookHandler(unittest.TestCase):
    """Tests for the WebhookHandler class."""
    
    def setUp(self):
        self.github_client = MagicMock(spec=GitHubAPIClient)
        self.webhook_secret = "test_secret"
        self.handler = WebhookHandler(
            github_client=self.github_client,
            webhook_secret=self.webhook_secret
        )
    
    @patch("hmac.compare_digest", return_value=True)
    def test_validate_signature(self, mock_compare):
        """Test validating webhook signatures."""
        payload = b'{"action":"opened"}'
        signature = "sha256=test_signature"
        
        result = self.handler.validate_signature(payload, signature)
        self.assertTrue(result)
    
    @patch("hmac.compare_digest", return_value=False)
    def test_validate_signature_invalid(self, mock_compare):
        """Test validating invalid webhook signatures."""
        payload = b'{"action":"opened"}'
        signature = "sha256=invalid_signature"
        
        result = self.handler.validate_signature(payload, signature)
        self.assertFalse(result)
    
    def test_register_handler(self):
        """Test registering event handlers."""
        mock_handler = MagicMock()
        self.handler.register_handler("pull_request", mock_handler)
        
        self.assertIn("pull_request", self.handler._event_handlers)
        self.assertEqual(self.handler._event_handlers["pull_request"], [mock_handler])


class TestPRAnalyzer(unittest.TestCase):
    """Tests for the PRAnalyzer class."""
    
    def setUp(self):
        self.github_client = MagicMock(spec=GitHubAPIClient)
        self.comment_formatter = MagicMock(spec=CommentFormatter)
        self.analyzer = PRAnalyzer(
            github_client=self.github_client,
            comment_formatter=self.comment_formatter
        )
    
    def test_analyze_file(self):
        """Test analyzing a file."""
        file = MagicMock()
        file.filename = "test.py"
        file.status = "modified"
        
        issues = self.analyzer._analyze_file(file)
        self.assertIsInstance(issues, list)


if __name__ == "__main__":
    unittest.main()

