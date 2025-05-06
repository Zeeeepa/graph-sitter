import unittest
import os
import tempfile
import shutil
from pr_static_analysis.git import RepoOperator

class TestRepoOperator(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize a RepoOperator
        self.repo_operator = RepoOperator(repo_path=self.test_dir)
    
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_clone_repo(self):
        # Test cloning a repository
        # Use a public repository for testing
        result = self.repo_operator.clone_repo("https://github.com/octocat/Hello-World.git")
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, ".git")))
    
    def test_get_file_content(self):
        # Test getting file content
        # First, clone a repository
        self.repo_operator.clone_repo("https://github.com/octocat/Hello-World.git")
        
        # Get content of a file
        content = self.repo_operator.get_file_content("README")
        
        self.assertIsNotNone(content)
        self.assertIn("Hello World", content)
    
    def test_find_files(self):
        # Test finding files
        # First, clone a repository
        self.repo_operator.clone_repo("https://github.com/octocat/Hello-World.git")
        
        # Find files matching a pattern
        files = self.repo_operator.find_files("*.md")
        
        self.assertIsInstance(files, list)
        self.assertTrue(any(file.endswith(".md") for file in files))

if __name__ == "__main__":
    unittest.main()

