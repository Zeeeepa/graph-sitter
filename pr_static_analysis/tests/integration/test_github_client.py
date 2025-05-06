import os
import unittest
from pr_static_analysis.git import GitHubClient

# Skip these tests if no GitHub token is available
@unittest.skipIf(not os.environ.get("GITHUB_TOKEN"), "GITHUB_TOKEN not set")
class TestGitHubClient(unittest.TestCase):
    def setUp(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.client = GitHubClient(access_token=self.github_token)
        
        # Test repository and PR
        self.test_repo = "octocat/Hello-World"  # Public repo for testing
        self.test_pr_number = 1  # First PR in the repo
    
    def test_get_repo(self):
        # Test getting a repository
        repo = self.client.get_repo(self.test_repo)
        
        self.assertIsNotNone(repo)
        self.assertEqual(repo.full_name, self.test_repo)
    
    def test_get_pr(self):
        # Test getting a PR
        pr = self.client.get_pr(self.test_repo, self.test_pr_number)
        
        self.assertIsNotNone(pr)
        self.assertEqual(pr.number, self.test_pr_number)
    
    def test_get_pr_files(self):
        # Test getting files in a PR
        files = self.client.get_pr_files(self.test_repo, self.test_pr_number)
        
        self.assertIsNotNone(files)
        self.assertIsInstance(files, list)
    
    def test_get_pr_commits(self):
        # Test getting commits in a PR
        commits = self.client.get_pr_commits(self.test_repo, self.test_pr_number)
        
        self.assertIsNotNone(commits)
        self.assertIsInstance(commits, list)

if __name__ == "__main__":
    unittest.main()

