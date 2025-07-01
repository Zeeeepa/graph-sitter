# 🚨 Immediate Fixes Summary - Git Operations Component

**Component**: `src/graph_sitter/git`  
**Issue**: ZAM-1086  
**Priority**: Critical Security & Stability Fixes

## 🔥 Critical Security Fixes (Implement Immediately)

### 1. Remove Hardcoded Credentials
**File**: `src/graph_sitter/git/configs/constants.py`

**Current (VULNERABLE):**
```python
CODEGEN_BOT_NAME = "codegen-sh[bot]"
CODEGEN_BOT_EMAIL = "131295404+codegen-sh[bot]@users.noreply.github.com"
```

**Fix:**
```python
import os

def get_bot_credentials() -> tuple[str, str]:
    """Get bot credentials from environment variables."""
    name = os.getenv("CODEGEN_BOT_NAME", "codegen-sh[bot]")
    email = os.getenv("CODEGEN_BOT_EMAIL", "131295404+codegen-sh[bot]@users.noreply.github.com")
    return name, email

CODEGEN_BOT_NAME, CODEGEN_BOT_EMAIL = get_bot_credentials()
```

### 2. Fix Shell Injection Vulnerability
**File**: `src/graph_sitter/git/utils/clone.py`

**Current (VULNERABLE):**
```python
delete_command = f"rm -rf {repo_path}"
subprocess.run(delete_command, shell=True, capture_output=True)
```

**Fix:**
```python
import shutil
from pathlib import Path

def safe_remove_directory(repo_path: str) -> None:
    """Safely remove directory without shell injection risk."""
    path = Path(repo_path)
    if path.exists() and path.is_dir():
        if os.getcwd() == str(path.resolve()):
            os.chdir(path.parent)
        shutil.rmtree(path)
        logger.info(f"Safely removed directory: {repo_path}")

# Replace the vulnerable code with:
if os.path.exists(repo_path) and os.listdir(repo_path):
    if os.getcwd() == os.path.realpath(repo_path):
        repo_parent_dir = os.path.dirname(repo_path)
        os.chdir(repo_parent_dir)
    safe_remove_directory(repo_path)
```

### 3. Add Input Validation
**File**: `src/graph_sitter/git/utils/validation.py` (NEW)

```python
from pathlib import Path
from urllib.parse import urlparse
import re

class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass

def validate_repo_path(repo_path: str) -> Path:
    """Validate and sanitize repository path."""
    if not repo_path or not isinstance(repo_path, str):
        raise ValidationError("Repository path must be a non-empty string")
    
    # Remove any null bytes
    repo_path = repo_path.replace('\x00', '')
    
    path = Path(repo_path).resolve()
    
    # Prevent directory traversal
    if ".." in str(path) or str(path).startswith("/"):
        raise ValidationError("Invalid repository path")
    
    return path

def validate_clone_url(url: str) -> str:
    """Validate clone URL format and security."""
    if not url or not isinstance(url, str):
        raise ValidationError("Clone URL must be a non-empty string")
    
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "git", "ssh"):
        raise ValidationError("Only https, git, and ssh URLs are allowed")
    
    # Basic domain validation
    if not parsed.netloc:
        raise ValidationError("Invalid URL format")
    
    return url

def validate_branch_name(branch_name: str) -> str:
    """Validate git branch name."""
    if not branch_name or not isinstance(branch_name, str):
        raise ValidationError("Branch name must be a non-empty string")
    
    # Git branch name rules
    if not re.match(r'^[a-zA-Z0-9/_-]+$', branch_name):
        raise ValidationError("Invalid branch name format")
    
    if branch_name.startswith('-') or branch_name.endswith('.'):
        raise ValidationError("Invalid branch name format")
    
    return branch_name
```

## ⚡ High-Priority Stability Fixes

### 4. Fix Mixed Technology Usage
**File**: `src/graph_sitter/git/utils/clone.py`

**Current (INCONSISTENT):**
```python
# Mixed GitPython and subprocess
GitRepo.clone_from(url=clone_url, to_path=repo_path, depth=1 if shallow else None, progress=CustomRemoteProgress())
subprocess_with_stopwatch(command=pull_command, command_desc=f"pull {repo_path}", shell=True, capture_output=True)
```

**Fix:**
```python
from git import Repo as GitRepo, GitCommandError
from graph_sitter.git.utils.validation import validate_clone_url, validate_repo_path

def clone_repo(repo_path: str, clone_url: str, shallow: bool = True) -> str:
    """Clone repository using GitPython consistently."""
    validated_url = validate_clone_url(clone_url)
    validated_path = validate_repo_path(repo_path)
    
    if validated_path.exists() and any(validated_path.iterdir()):
        if os.getcwd() == str(validated_path):
            os.chdir(validated_path.parent)
        safe_remove_directory(str(validated_path))
    
    try:
        GitRepo.clone_from(
            url=validated_url,
            to_path=str(validated_path),
            depth=1 if shallow else None,
            progress=CustomRemoteProgress()
        )
        logger.info(f"Successfully cloned {validated_url} to {validated_path}")
        return str(validated_path)
    except GitCommandError as e:
        logger.error(f"Clone failed: {e}")
        raise

def pull_repo(repo_path: str, clone_url: str) -> None:
    """Pull repository updates using GitPython."""
    validated_path = validate_repo_path(repo_path)
    validated_url = validate_clone_url(clone_url)
    
    if not validated_path.exists():
        logger.warning(f"{validated_path} directory does not exist. Cannot pull.")
        return
    
    try:
        repo = GitRepo(str(validated_path))
        origin = repo.remotes.origin
        origin.set_url(validated_url)  # Refresh token
        origin.pull(progress=CustomRemoteProgress())
        logger.info(f"Successfully pulled updates for {validated_path}")
    except GitCommandError as e:
        logger.error(f"Pull failed: {e}")
        raise
```

### 5. Improve Error Handling
**File**: `src/graph_sitter/git/exceptions.py` (NEW)

```python
class GitOperationError(Exception):
    """Base exception for git operations."""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}

class CloneError(GitOperationError):
    """Repository cloning failed."""
    pass

class PullError(GitOperationError):
    """Repository pull failed."""
    pass

class ValidationError(GitOperationError):
    """Input validation failed."""
    pass

class GitHubAPIError(GitOperationError):
    """GitHub API operation failed."""
    
    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
```

### 6. Add Basic Rate Limiting
**File**: `src/graph_sitter/git/clients/rate_limiter.py` (NEW)

```python
import time
from typing import Optional
from threading import Lock

class SimpleRateLimiter:
    """Simple rate limiter for GitHub API calls."""
    
    def __init__(self, max_calls: int = 5000, period: int = 3600):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self._lock = Lock()
    
    def acquire(self) -> None:
        """Acquire permission to make an API call."""
        with self._lock:
            now = time.time()
            # Remove old calls outside the period
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.period]
            
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = min(self.calls)
                wait_time = self.period - (now - oldest_call) + 1
                time.sleep(wait_time)
                # Clean up again after waiting
                now = time.time()
                self.calls = [call_time for call_time in self.calls 
                             if now - call_time < self.period]
            
            self.calls.append(now)
```

**Update**: `src/graph_sitter/git/clients/github_client.py`

```python
from graph_sitter.git.clients.rate_limiter import SimpleRateLimiter

class GithubClient:
    def __init__(self, token: str | None = None, base_url: str = Consts.DEFAULT_BASE_URL):
        self.base_url = base_url
        self._client = Github(token, base_url=base_url)
        self.rate_limiter = SimpleRateLimiter()
    
    def _make_api_call(self, operation):
        """Make API call with rate limiting."""
        self.rate_limiter.acquire()
        return operation()
    
    def get_repo_by_full_name(self, full_name: str) -> Repository | None:
        try:
            return self._make_api_call(lambda: self._client.get_repo(full_name))
        except UnknownObjectException:
            return None
        except Exception as e:
            logger.warning(f"Error getting repo {full_name}: {e}")
            return None
```

## 🛡️ Security Hardening

### 7. Secure Token Handling
**File**: `src/graph_sitter/git/utils/clone_url.py`

**Current (POTENTIAL EXPOSURE):**
```python
def add_access_token_to_url(url: str, token: str | None) -> str:
    # Token might be logged or exposed
```

**Fix:**
```python
import logging
from urllib.parse import urlparse, urlunparse

def add_access_token_to_url(url: str, token: str | None) -> str:
    """Add access token to URL securely."""
    if not token:
        return url
    
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme or "https"
    
    # Mask token in logs
    masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
    logger.debug(f"Adding token {masked_token} to URL")
    
    token_prefix = f"x-access-token:{token}@"
    secure_url = f"{scheme}://{token_prefix}{parsed_url.netloc}{parsed_url.path}"
    
    return secure_url

def mask_sensitive_url(url: str) -> str:
    """Mask sensitive information in URLs for logging."""
    if "@" in url:
        parts = url.split("@")
        if len(parts) == 2:
            auth_part = parts[0]
            if ":" in auth_part:
                user, token = auth_part.rsplit(":", 1)
                masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
                return f"{user}:{masked_token}@{parts[1]}"
    return url
```

### 8. Environment Variable Validation
**File**: `src/graph_sitter/git/configs/env_config.py` (NEW)

```python
import os
from typing import Optional

class EnvironmentConfig:
    """Secure environment configuration management."""
    
    @staticmethod
    def get_required_env(key: str) -> str:
        """Get required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    @staticmethod
    def get_optional_env(key: str, default: str = None) -> Optional[str]:
        """Get optional environment variable."""
        return os.getenv(key, default)
    
    @staticmethod
    def validate_github_token(token: str) -> bool:
        """Validate GitHub token format."""
        if not token:
            return False
        
        # GitHub tokens start with specific prefixes
        valid_prefixes = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_']
        return any(token.startswith(prefix) for prefix in valid_prefixes)
    
    @classmethod
    def get_github_token(cls) -> str:
        """Get and validate GitHub token."""
        token = cls.get_required_env("GITHUB_TOKEN")
        if not cls.validate_github_token(token):
            raise ValueError("Invalid GitHub token format")
        return token
```

## 📋 Implementation Checklist

### Immediate Actions (Day 1)
- [ ] Create `validation.py` with input validation functions
- [ ] Create `exceptions.py` with proper exception hierarchy
- [ ] Update `constants.py` to use environment variables
- [ ] Fix shell injection in `clone.py`
- [ ] Add basic rate limiting to GitHub client

### Short-term Actions (Week 1)
- [ ] Update all clone operations to use validation
- [ ] Implement secure token handling
- [ ] Add environment variable validation
- [ ] Update error handling throughout the module
- [ ] Add comprehensive logging with sensitive data masking

### Testing Requirements
- [ ] Unit tests for all validation functions
- [ ] Security tests for shell injection prevention
- [ ] Integration tests for rate limiting
- [ ] Performance tests for large repository operations

### Documentation Updates
- [ ] Update README with security requirements
- [ ] Document environment variable requirements
- [ ] Add security best practices guide
- [ ] Update API documentation

## 🚀 Deployment Strategy

### Phase 1: Security Fixes
1. Deploy validation and security fixes to staging
2. Run security audit and penetration testing
3. Deploy to production with monitoring

### Phase 2: Stability Improvements
1. Deploy error handling and rate limiting improvements
2. Monitor error rates and performance
3. Gradual rollout with feature flags

### Monitoring Requirements
- Monitor error rates for all git operations
- Track rate limiting effectiveness
- Alert on security validation failures
- Performance monitoring for large operations

---

**⚠️ CRITICAL**: These fixes address immediate security vulnerabilities and should be implemented as soon as possible. The shell injection vulnerability and hardcoded credentials pose significant security risks to the autonomous CI/CD system.

