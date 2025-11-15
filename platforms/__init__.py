"""Platform integrations for code review agents."""

from .base import BasePlatform, PullRequest, PlatformComment
from .github import GitHubPlatform
from .gitlab import GitLabPlatform
from .azure_devops import AzureDevOpsPlatform
from .factory import create_platform

__all__ = [
    "BasePlatform",
    "PullRequest",
    "PlatformComment",
    "GitHubPlatform",
    "GitLabPlatform",
    "AzureDevOpsPlatform",
    "create_platform",
]
