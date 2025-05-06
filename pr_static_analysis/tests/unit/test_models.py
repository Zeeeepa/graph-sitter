import unittest
from pr_static_analysis.git.models import GitHubNamedUserContext, PRPartContext, PullRequestContext

class TestGitHubModels(unittest.TestCase):
    def test_github_named_user_context_from_payload(self):
        # Test creating a GitHubNamedUserContext from a payload
        payload = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "avatar_url": "https://github.com/testuser.png"
        }
        
        user = GitHubNamedUserContext.from_payload(payload)
        
        self.assertEqual(user.login, "testuser")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.avatar_url, "https://github.com/testuser.png")
    
    def test_pr_part_context_from_payload(self):
        # Test creating a PRPartContext from a payload
        payload = {
            "ref": "feature-branch",
            "sha": "abcdef1234567890",
            "repo": {
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "html_url": "https://github.com/testuser/test-repo"
            }
        }
        
        pr_part = PRPartContext.from_payload(payload)
        
        self.assertEqual(pr_part.ref, "feature-branch")
        self.assertEqual(pr_part.sha, "abcdef1234567890")
        self.assertEqual(pr_part.repo_name, "test-repo")
        self.assertEqual(pr_part.repo_full_name, "testuser/test-repo")
        self.assertEqual(pr_part.repo_url, "https://github.com/testuser/test-repo")
    
    def test_pull_request_context_from_payload(self):
        # Test creating a PullRequestContext from a payload
        payload = {
            "pull_request": {
                "id": 12345,
                "url": "https://api.github.com/repos/testuser/test-repo/pulls/1",
                "html_url": "https://github.com/testuser/test-repo/pull/1",
                "number": 1,
                "state": "open",
                "title": "Test PR",
                "user": {
                    "login": "testuser",
                    "name": "Test User",
                    "email": "test@example.com",
                    "avatar_url": "https://github.com/testuser.png"
                },
                "body": "This is a test PR",
                "draft": False,
                "head": {
                    "ref": "feature-branch",
                    "sha": "abcdef1234567890",
                    "repo": {
                        "name": "test-repo",
                        "full_name": "testuser/test-repo",
                        "html_url": "https://github.com/testuser/test-repo"
                    }
                },
                "base": {
                    "ref": "main",
                    "sha": "0987654321fedcba",
                    "repo": {
                        "name": "test-repo",
                        "full_name": "testuser/test-repo",
                        "html_url": "https://github.com/testuser/test-repo"
                    }
                },
                "merged": False,
                "additions": 10,
                "deletions": 5,
                "changed_files": 2
            }
        }
        
        pr = PullRequestContext.from_payload(payload)
        
        self.assertEqual(pr.id, 12345)
        self.assertEqual(pr.url, "https://api.github.com/repos/testuser/test-repo/pulls/1")
        self.assertEqual(pr.html_url, "https://github.com/testuser/test-repo/pull/1")
        self.assertEqual(pr.number, 1)
        self.assertEqual(pr.state, "open")
        self.assertEqual(pr.title, "Test PR")
        self.assertEqual(pr.user.login, "testuser")
        self.assertEqual(pr.body, "This is a test PR")
        self.assertEqual(pr.draft, False)
        self.assertEqual(pr.head.ref, "feature-branch")
        self.assertEqual(pr.base.ref, "main")
        self.assertEqual(pr.merged, False)
        self.assertEqual(pr.additions, 10)
        self.assertEqual(pr.deletions, 5)
        self.assertEqual(pr.changed_files, 2)

if __name__ == "__main__":
    unittest.main()

