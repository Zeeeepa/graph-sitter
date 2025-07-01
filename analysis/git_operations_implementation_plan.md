# 🛠️ Git Operations Implementation Plan

**Component**: `src/graph_sitter/git`  
**Issue**: ZAM-1086  
**Priority**: High (Critical for CI/CD system)

## 🎯 Implementation Strategy

This plan addresses the critical issues identified in the component analysis and provides a phased approach to refactoring the git operations module for the autonomous CI/CD system.

## 📋 Phase 1: Security & Critical Fixes (Week 1)

### 1.1 Credential Security
**Priority**: Critical  
**Files**: `src/graph_sitter/git/configs/constants.py`

#### Current Issue:
```python
# Hardcoded credentials - SECURITY RISK
CODEGEN_BOT_NAME = "codegen-sh[bot]"
CODEGEN_BOT_EMAIL = "131295404+codegen-sh[bot]@users.noreply.github.com"
```

#### Fix Implementation:
```python
import os
from typing import Optional

def get_bot_credentials() -> tuple[str, str]:
    """Get bot credentials from environment variables with fallbacks."""
    name = os.getenv("CODEGEN_BOT_NAME", "codegen-sh[bot]")
    email = os.getenv("CODEGEN_BOT_EMAIL", "131295404+codegen-sh[bot]@users.noreply.github.com")
    return name, email

# Usage in repo_operator.py
CODEGEN_BOT_NAME, CODEGEN_BOT_EMAIL = get_bot_credentials()
```

### 1.2 Shell Command Security
**Priority**: Critical  
**Files**: `src/graph_sitter/git/utils/clone.py`

#### Current Issue:
```python
# Shell injection vulnerability
delete_command = f"rm -rf {repo_path}"
subprocess.run(delete_command, shell=True, capture_output=True)
```

#### Fix Implementation:
```python
import shutil
from pathlib import Path

def safe_remove_directory(repo_path: str) -> None:
    """Safely remove directory without shell injection risk."""
    path = Path(repo_path)
    if path.exists() and path.is_dir():
        # Change to parent directory if currently in target
        if os.getcwd() == str(path.resolve()):
            os.chdir(path.parent)
        shutil.rmtree(path)
        logger.info(f"Safely removed directory: {repo_path}")
```

### 1.3 Input Validation
**Priority**: High  
**Files**: All utility functions

#### Implementation:
```python
from pathlib import Path
from urllib.parse import urlparse

def validate_repo_path(repo_path: str) -> Path:
    """Validate and sanitize repository path."""
    if not repo_path or not isinstance(repo_path, str):
        raise ValueError("Repository path must be a non-empty string")
    
    path = Path(repo_path).resolve()
    
    # Prevent directory traversal
    if ".." in str(path):
        raise ValueError("Directory traversal not allowed in repo path")
    
    return path

def validate_clone_url(url: str) -> str:
    """Validate clone URL format and security."""
    if not url or not isinstance(url, str):
        raise ValueError("Clone URL must be a non-empty string")
    
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "git", "ssh"):
        raise ValueError("Only https, git, and ssh URLs are allowed")
    
    return url
```

## 📋 Phase 2: Architectural Refactoring (Weeks 2-3)

### 2.1 Break Down Monolithic RepoOperator
**Priority**: High  
**Files**: `src/graph_sitter/git/repo_operator/`

#### Current Issue:
- Single 1000+ line class handling everything
- High coupling and low cohesion
- Difficult to test and maintain

#### Proposed Architecture:
```python
# src/graph_sitter/git/operations/
├── base.py              # Base operation classes
├── git_operations.py    # Local git operations
├── github_operations.py # GitHub API operations
├── branch_manager.py    # Branch management
├── pr_manager.py        # Pull request operations
└── coordinator.py       # Main orchestrator

# base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class GitOperation(ABC, Generic[T]):
    """Base class for all git operations."""
    
    def __init__(self, repo_config: RepoConfig, logger: Logger):
        self.repo_config = repo_config
        self.logger = logger
    
    @abstractmethod
    def execute(self) -> T:
        """Execute the operation."""
        pass
    
    def validate_preconditions(self) -> None:
        """Validate operation preconditions."""
        pass

# git_operations.py
class LocalGitOperations(GitOperation[None]):
    """Handles local git repository operations."""
    
    def __init__(self, repo_config: RepoConfig, git_cli: GitCLI):
        super().__init__(repo_config, get_logger(__name__))
        self.git_cli = git_cli
    
    def clone_repository(self, url: str, shallow: bool = True) -> Path:
        """Clone repository safely."""
        validated_url = validate_clone_url(url)
        repo_path = validate_repo_path(self.repo_config.repo_path)
        
        if repo_path.exists():
            safe_remove_directory(str(repo_path))
        
        GitRepo.clone_from(
            url=validated_url,
            to_path=str(repo_path),
            depth=1 if shallow else None,
            progress=CustomRemoteProgress()
        )
        return repo_path
    
    def create_branch(self, branch_name: str, base_branch: str = None) -> None:
        """Create a new branch safely."""
        # Implementation with validation
        pass
    
    def commit_changes(self, message: str, files: list[str] = None) -> str:
        """Commit changes with proper validation."""
        # Implementation
        pass

# github_operations.py
class GitHubOperations(GitOperation[None]):
    """Handles GitHub API operations with rate limiting."""
    
    def __init__(self, repo_config: RepoConfig, client: GitRepoClient):
        super().__init__(repo_config, get_logger(__name__))
        self.client = client
        self.rate_limiter = RateLimiter(max_calls=5000, period=3600)
    
    async def create_pull_request(self, pr_options: PROptions) -> PullRequest:
        """Create PR with rate limiting."""
        await self.rate_limiter.acquire()
        # Implementation
        pass
    
    async def get_pull_request(self, pr_number: int) -> PullRequest:
        """Get PR with caching and rate limiting."""
        await self.rate_limiter.acquire()
        # Implementation
        pass

# coordinator.py
class RepoCoordinator:
    """Coordinates all repository operations."""
    
    def __init__(self, repo_config: RepoConfig, access_token: str = None):
        self.repo_config = repo_config
        self.git_ops = LocalGitOperations(repo_config, self._get_git_cli())
        self.github_ops = GitHubOperations(repo_config, self._get_github_client())
        self.branch_mgr = BranchManager(self.git_ops, self.github_ops)
        self.pr_mgr = PRManager(self.github_ops)
    
    def setup_repository(self, setup_option: SetupOption) -> None:
        """Setup repository with proper error handling."""
        try:
            if setup_option == SetupOption.CLONE:
                self.git_ops.clone_repository(self.repo_config.clone_url)
            elif setup_option == SetupOption.PULL_OR_CLONE:
                self._clone_or_pull()
        except Exception as e:
            self.logger.error(f"Repository setup failed: {e}")
            raise
```

### 2.2 Standardize Technology Stack
**Priority**: Medium  
**Files**: All git operation files

#### Current Issue:
- Mixed use of GitPython and subprocess
- Inconsistent error handling

#### Implementation:
```python
# Standardize on GitPython with fallback to subprocess only when necessary
class GitOperationMixin:
    """Mixin providing standardized git operations."""
    
    def _execute_git_command(self, command: list[str], cwd: str = None) -> str:
        """Execute git command with proper error handling."""
        try:
            # Prefer GitPython methods
            return self._execute_with_gitpython(command)
        except GitCommandError as e:
            # Fallback to subprocess only if GitPython fails
            self.logger.warning(f"GitPython failed, falling back to subprocess: {e}")
            return self._execute_with_subprocess(command, cwd)
    
    def _execute_with_gitpython(self, command: list[str]) -> str:
        """Execute using GitPython."""
        # Implementation using GitPython
        pass
    
    def _execute_with_subprocess(self, command: list[str], cwd: str) -> str:
        """Safe subprocess execution as fallback."""
        # Use subprocess.run with proper validation
        result = subprocess.run(
            command,  # No shell=True
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
```

## 📋 Phase 3: Performance & Quality (Week 4)

### 3.1 Rate Limiting Implementation
**Priority**: High  
**Files**: `src/graph_sitter/git/clients/`

#### Implementation:
```python
import asyncio
import time
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter for GitHub API."""
    
    def __init__(self, max_calls: int, period: int = 3600):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make an API call."""
        async with self._lock:
            now = time.time()
            # Remove old calls outside the period
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.period]
            
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = min(self.calls)
                wait_time = self.period - (now - oldest_call)
                await asyncio.sleep(wait_time)
            
            self.calls.append(now)

class RateLimitedGitHubClient(GitRepoClient):
    """GitHub client with built-in rate limiting."""
    
    def __init__(self, repo_config: RepoConfig, access_token: str = None):
        super().__init__(repo_config, access_token)
        self.rate_limiter = RateLimiter(max_calls=5000, period=3600)
    
    async def _make_api_call(self, operation):
        """Make API call with rate limiting."""
        await self.rate_limiter.acquire()
        return operation()
```

### 3.2 Async Support
**Priority**: Medium  
**Files**: All operation classes

#### Implementation:
```python
import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar('T')

class AsyncGitOperations:
    """Async wrapper for git operations."""
    
    async def clone_repository_async(self, url: str, shallow: bool = True) -> Path:
        """Async repository cloning."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._clone_repository_sync, 
            url, 
            shallow
        )
    
    async def batch_operations(self, operations: list[Callable[[], Awaitable[T]]]) -> list[T]:
        """Execute multiple operations concurrently."""
        return await asyncio.gather(*[op() for op in operations])
```

### 3.3 Comprehensive Error Handling
**Priority**: High  
**Files**: All modules

#### Implementation:
```python
# src/graph_sitter/git/exceptions.py
class GitOperationError(Exception):
    """Base exception for git operations."""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}

class CloneError(GitOperationError):
    """Repository cloning failed."""
    pass

class PushError(GitOperationError):
    """Push operation failed."""
    pass

class GitHubAPIError(GitOperationError):
    """GitHub API operation failed."""
    
    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code

# Error handling decorator
def handle_git_errors(operation_name: str):
    """Decorator for consistent error handling."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except GitCommandError as e:
                raise GitOperationError(
                    f"{operation_name} failed: {e.stderr}",
                    operation=operation_name,
                    details={"command": e.command, "status": e.status}
                ) from e
            except GithubException as e:
                raise GitHubAPIError(
                    f"{operation_name} failed: {e.data.get('message', str(e))}",
                    operation=operation_name,
                    status_code=e.status
                ) from e
        return wrapper
    return decorator
```

## 📋 Phase 4: Advanced Features (Week 5)

### 4.1 Enhanced Webhook Validation
**Priority**: Medium  
**Files**: `src/graph_sitter/git/models/`

#### Implementation:
```python
import hmac
import hashlib
from typing import Optional

class WebhookValidator:
    """Validates GitHub webhook payloads."""
    
    def __init__(self, secret: str):
        self.secret = secret.encode('utf-8')
    
    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature."""
        if not signature.startswith('sha256='):
            return False
        
        expected = hmac.new(
            self.secret,
            payload,
            hashlib.sha256
        ).hexdigest()
        
        received = signature[7:]  # Remove 'sha256=' prefix
        return hmac.compare_digest(expected, received)
    
    def validate_payload(self, payload: dict) -> bool:
        """Validate payload structure."""
        required_fields = ['action', 'repository', 'sender']
        return all(field in payload for field in required_fields)

# Enhanced PR context with validation
class ValidatedPullRequestContext(PullRequestContext):
    """PR context with enhanced validation."""
    
    @classmethod
    def from_webhook(cls, payload: dict, validator: WebhookValidator) -> "ValidatedPullRequestContext":
        """Create from validated webhook payload."""
        if not validator.validate_payload(payload):
            raise ValueError("Invalid webhook payload structure")
        
        return cls.from_payload(payload)
```

### 4.2 Monitoring & Metrics
**Priority**: Low  
**Files**: New monitoring module

#### Implementation:
```python
# src/graph_sitter/git/monitoring/metrics.py
import time
from typing import Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class OperationMetrics:
    """Metrics for git operations."""
    operation_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Operation duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

class MetricsCollector:
    """Collects and aggregates operation metrics."""
    
    def __init__(self):
        self.metrics: list[OperationMetrics] = []
        self.counters = defaultdict(int)
    
    def start_operation(self, operation_name: str, **metadata) -> OperationMetrics:
        """Start tracking an operation."""
        metric = OperationMetrics(
            operation_name=operation_name,
            metadata=metadata
        )
        self.metrics.append(metric)
        return metric
    
    def finish_operation(self, metric: OperationMetrics, success: bool, error: str = None):
        """Finish tracking an operation."""
        metric.end_time = time.time()
        metric.success = success
        metric.error_message = error
        
        # Update counters
        self.counters[f"{metric.operation_name}_total"] += 1
        if success:
            self.counters[f"{metric.operation_name}_success"] += 1
        else:
            self.counters[f"{metric.operation_name}_error"] += 1
    
    def get_summary(self) -> dict:
        """Get metrics summary."""
        return {
            "total_operations": len(self.metrics),
            "counters": dict(self.counters),
            "average_durations": self._calculate_average_durations(),
            "error_rate": self._calculate_error_rate()
        }
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/git/operations/test_git_operations.py
import pytest
from unittest.mock import Mock, patch
from graph_sitter.git.operations.git_operations import LocalGitOperations

class TestLocalGitOperations:
    
    @pytest.fixture
    def git_ops(self, mock_repo_config, mock_git_cli):
        return LocalGitOperations(mock_repo_config, mock_git_cli)
    
    def test_clone_repository_success(self, git_ops, tmp_path):
        """Test successful repository cloning."""
        url = "https://github.com/test/repo.git"
        
        with patch('graph_sitter.git.operations.git_operations.GitRepo.clone_from') as mock_clone:
            result = git_ops.clone_repository(url)
            
            mock_clone.assert_called_once()
            assert result.exists()
    
    def test_clone_repository_invalid_url(self, git_ops):
        """Test cloning with invalid URL."""
        with pytest.raises(ValueError, match="Only https, git, and ssh URLs are allowed"):
            git_ops.clone_repository("ftp://invalid.com/repo.git")
    
    def test_safe_remove_directory(self, tmp_path):
        """Test safe directory removal."""
        test_dir = tmp_path / "test_repo"
        test_dir.mkdir()
        
        safe_remove_directory(str(test_dir))
        assert not test_dir.exists()
```

### Integration Tests
```python
# tests/integration/git/test_repo_coordinator.py
import pytest
from graph_sitter.git.operations.coordinator import RepoCoordinator

class TestRepoCoordinator:
    
    @pytest.mark.integration
    def test_full_pr_workflow(self, test_repo_config, github_token):
        """Test complete PR creation workflow."""
        coordinator = RepoCoordinator(test_repo_config, github_token)
        
        # Setup repository
        coordinator.setup_repository(SetupOption.CLONE)
        
        # Create branch
        branch_name = "test-feature-branch"
        coordinator.branch_mgr.create_branch(branch_name)
        
        # Make changes and commit
        coordinator.git_ops.commit_changes("Test commit")
        
        # Create PR
        pr = coordinator.pr_mgr.create_pull_request(
            PROptions(title="Test PR", body="Test description")
        )
        
        assert pr is not None
        assert pr.title == "Test PR"
```

## 📊 Success Metrics

### Code Quality Metrics
- **Cyclomatic Complexity**: <10 per method
- **Class Size**: <200 lines per class
- **Method Size**: <50 lines per method
- **Test Coverage**: >90%

### Performance Metrics
- **Clone Time**: <30s for typical repositories
- **API Response Time**: <2s for GitHub operations
- **Memory Usage**: <100MB for large repository operations
- **Error Rate**: <1% for all operations

### Security Metrics
- **Zero** hardcoded credentials
- **100%** input validation coverage
- **Zero** shell injection vulnerabilities
- **Secure** token handling throughout

## 🚀 Deployment Strategy

### Phase 1 Deployment
1. Deploy security fixes to staging environment
2. Run comprehensive security audit
3. Deploy to production with monitoring

### Phase 2 Deployment
1. Deploy refactored components incrementally
2. A/B test new architecture vs old
3. Monitor performance metrics
4. Gradual rollout to all users

### Phase 3 Deployment
1. Deploy performance optimizations
2. Monitor system performance
3. Optimize based on real-world usage

### Phase 4 Deployment
1. Deploy advanced features
2. Enable monitoring and metrics collection
3. Continuous improvement based on metrics

## 🔄 Maintenance Plan

### Daily
- Monitor error rates and performance metrics
- Review security alerts
- Check rate limiting effectiveness

### Weekly
- Review and update dependencies
- Analyze performance trends
- Update documentation

### Monthly
- Security audit and penetration testing
- Performance optimization review
- Architecture review and improvements

---

*This implementation plan provides a comprehensive roadmap for transforming the git operations component into a secure, performant, and maintainable foundation for the autonomous CI/CD system.*

