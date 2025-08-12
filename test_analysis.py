#!/usr/bin/env python3
"""
Test script for the graph-sitter_analysis.py tool.
"""

import unittest
from unittest.mock import patch, MagicMock

from graph_sitter_analysis import (
    CodebaseAnalyzer, 
    CodebaseAnalysisResult,
    CodeIssue,
    EntryPoint,
    DeadCode,
    IssueSeverity
)

class TestCodebaseAnalyzer(unittest.TestCase):
    """Test cases for the CodebaseAnalyzer class."""
    
    @patch('graph_sitter_analysis.Codebase')
    def test_initialization(self, mock_codebase):
        """Test that the analyzer initializes correctly."""
        # Arrange
        repo_path = "test/repo"
        language = "python"
        
        # Act
        analyzer = CodebaseAnalyzer(repo_path, language)
        
        # Assert
        self.assertEqual(analyzer.repo_path, repo_path)
        self.assertEqual(analyzer.language, language)
        self.assertIsNone(analyzer.codebase)
        self.assertIsInstance(analyzer.result, CodebaseAnalysisResult)
    
    @patch('graph_sitter_analysis.Codebase')
    @patch('graph_sitter_analysis.get_codebase_summary')
    def test_load_codebase_local(self, mock_get_summary, mock_codebase):
        """Test loading a local codebase."""
        # Arrange
        repo_path = "./local/repo"
        mock_codebase_instance = MagicMock()
        mock_codebase.return_value = mock_codebase_instance
        mock_get_summary.return_value = "Codebase summary"
        
        # Act
        analyzer = CodebaseAnalyzer(repo_path)
        with patch('graph_sitter_analysis.console'):  # Suppress console output
            analyzer.load_codebase()
        
        # Assert
        mock_codebase.assert_called_once()
        self.assertEqual(analyzer.codebase, mock_codebase_instance)
    
    @patch('graph_sitter_analysis.Codebase')
    def test_analyze(self, mock_codebase):
        """Test the analyze method."""
        # Arrange
        repo_path = "test/repo"
        analyzer = CodebaseAnalyzer(repo_path)
        
        # Mock the internal methods
        analyzer._build_file_tree = MagicMock()
        analyzer._identify_entry_points = MagicMock()
        analyzer._detect_dead_code = MagicMock()
        analyzer._find_issues = MagicMock()
        analyzer.load_codebase = MagicMock()
        
        # Act
        with patch('graph_sitter_analysis.Progress'):  # Suppress progress bar
            result = analyzer.analyze()
        
        # Assert
        analyzer.load_codebase.assert_called_once()
        analyzer._build_file_tree.assert_called_once()
        analyzer._identify_entry_points.assert_called_once()
        analyzer._detect_dead_code.assert_called_once()
        analyzer._find_issues.assert_called_once()
        self.assertEqual(result, analyzer.result)

class TestCodeIssue(unittest.TestCase):
    """Test cases for the CodeIssue class."""
    
    def test_code_issue_str(self):
        """Test the string representation of a CodeIssue."""
        # Arrange
        issue = CodeIssue(
            filepath="test/file.py",
            line_number=42,
            issue_type="Test Issue",
            message="This is a test issue",
            severity=IssueSeverity.CRITICAL
        )
        
        # Act
        result = str(issue)
        
        # Assert
        self.assertIn("test/file.py:42", result)
        self.assertIn("Test Issue", result)
        self.assertIn("This is a test issue", result)
        self.assertIn(IssueSeverity.CRITICAL.value, result)

class TestEntryPoint(unittest.TestCase):
    """Test cases for the EntryPoint class."""
    
    def test_entry_point_str(self):
        """Test the string representation of an EntryPoint."""
        # Arrange
        entry_point = EntryPoint(
            name="main",
            filepath="test/file.py",
            type="function",
            reason="Main function"
        )
        
        # Act
        result = str(entry_point)
        
        # Assert
        self.assertIn("main", result)
        self.assertIn("test/file.py", result)
        self.assertIn("function", result)
        self.assertIn("Main function", result)

class TestDeadCode(unittest.TestCase):
    """Test cases for the DeadCode class."""
    
    def test_dead_code_str(self):
        """Test the string representation of a DeadCode."""
        # Arrange
        dead_code = DeadCode(
            name="unused_function",
            filepath="test/file.py",
            type="function",
            reason="Not used by any other code"
        )
        
        # Act
        result = str(dead_code)
        
        # Assert
        self.assertIn("unused_function", result)
        self.assertIn("test/file.py", result)
        self.assertIn("function", result)
        self.assertIn("Not used by any other code", result)

if __name__ == "__main__":
    unittest.main()

