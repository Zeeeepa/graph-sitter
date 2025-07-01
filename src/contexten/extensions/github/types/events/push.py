
from ..base import GitHubRepository, GitHubUser
from ..commit import GitHubCommit
from ..enterprise import GitHubEnterprise
from ..installation import GitHubInstallation
from ..organization import GitHubOrganization
from ..pusher import GitHubPusher
from pydantic import BaseModel

class PushEvent(BaseModel):
    ref: str
    before: str
    after: str
    repository: GitHubRepository
    pusher: GitHubPusher
    organization: GitHubOrganization
    enterprise: GitHubEnterprise
    sender: GitHubUser
    installation: GitHubInstallation
    created: bool
    deleted: bool
    forced: bool
    base_ref: str | None = None
    compare: str
    commits: list[GitHubCommit]
    head_commit: GitHubCommit | None = None
