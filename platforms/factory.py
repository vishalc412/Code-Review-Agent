"""Factory for creating platform clients."""

from .base import BasePlatform
from .github import GitHubPlatform
from .gitlab import GitLabPlatform
from .azure_devops import AzureDevOpsPlatform
from core.config import Settings, Platform
from core.exceptions import ConfigurationError


def create_platform(settings: Settings) -> BasePlatform:
    """
    Create a platform client based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured platform client instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    if settings.platform == Platform.GITHUB:
        if not settings.github_token or not settings.github_repository:
            raise ConfigurationError("GitHub requires token and repository")

        return GitHubPlatform(
            token=settings.github_token,
            repository=settings.github_repository
        )

    elif settings.platform == Platform.GITLAB:
        if not settings.gitlab_token or not settings.gitlab_project_id:
            raise ConfigurationError("GitLab requires token and project_id")

        return GitLabPlatform(
            token=settings.gitlab_token,
            project_id=settings.gitlab_project_id,
            url=settings.gitlab_url
        )

    elif settings.platform == Platform.AZURE_DEVOPS:
        if not all([
            settings.azure_devops_pat,
            settings.azure_devops_organization,
            settings.azure_devops_project,
            settings.azure_devops_repository_id
        ]):
            raise ConfigurationError(
                "Azure DevOps requires PAT, organization, project, and repository_id"
            )

        return AzureDevOpsPlatform(
            pat=settings.azure_devops_pat,
            organization=settings.azure_devops_organization,
            project=settings.azure_devops_project,
            repository_id=settings.azure_devops_repository_id
        )

    else:
        raise ConfigurationError(f"Unsupported platform: {settings.platform}")
