"""Configuration management for code review agents."""

import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class Platform(str, Enum):
    """Supported platforms."""
    AZURE_DEVOPS = "azure_devops"
    GITLAB = "gitlab"
    GITHUB = "github"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    AZURE_AI = "azure_ai"
    ANTHROPIC = "anthropic"


class ReviewDepth(str, Enum):
    """Review depth options."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ReviewFocus(str, Enum):
    """Review focus areas."""
    ALL = "all"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BUGS = "bugs"


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    SUGGESTION = "suggestion"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Platform Selection
    platform: Platform = Field(default=Platform.GITHUB)

    # Azure DevOps Configuration
    azure_devops_pat: Optional[str] = None
    azure_devops_organization: Optional[str] = None
    azure_devops_project: Optional[str] = None
    azure_devops_repository_id: Optional[str] = None

    # GitLab Configuration
    gitlab_token: Optional[str] = None
    gitlab_url: str = "https://gitlab.com"
    gitlab_project_id: Optional[str] = None

    # GitHub Configuration
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    github_app_id: Optional[str] = None
    github_app_private_key_path: Optional[str] = None

    # LLM Provider Configuration
    llm_provider: LLMProvider = Field(default=LLMProvider.ANTHROPIC)

    # Azure AI Configuration
    azure_ai_api_key: Optional[str] = None
    azure_ai_endpoint: Optional[str] = None
    azure_ai_deployment_name: str = "gpt-4"
    azure_ai_api_version: str = "2024-02-15-preview"

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Review Agent Settings
    review_enabled: bool = True
    review_depth: ReviewDepth = ReviewDepth.STANDARD
    review_focus: ReviewFocus = ReviewFocus.ALL
    max_files_to_review: int = 50
    exclude_patterns: str = "*.md,*.txt,package-lock.json,*.min.js"
    include_line_comments: bool = True
    include_file_comments: bool = True
    include_pr_summary: bool = True
    severity_threshold: Severity = Severity.MINOR

    # Fix Agent Settings
    fix_enabled: bool = True
    fix_auto_create_pr: bool = True
    fix_branch_prefix: str = "fix/ai-review-"
    fix_severity_filter: Severity = Severity.MAJOR
    fix_max_files: int = 20
    fix_validate_syntax: bool = True
    fix_run_tests: bool = False

    # General Settings
    log_level: str = "INFO"
    max_retries: int = 3
    timeout_seconds: int = 300
    enable_webhooks: bool = True
    webhook_secret: Optional[str] = None

    # Comment Templates
    review_comment_prefix: str = "[AI Review]"
    fix_pr_title_prefix: str = "[AI Fix]"
    fix_pr_description_template: str = "templates/pr_descriptions/fix_pr_template.md"

    @field_validator("exclude_patterns")
    @classmethod
    def parse_exclude_patterns(cls, v: str) -> List[str]:
        """Parse comma-separated exclude patterns."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    def validate_platform_config(self) -> None:
        """Validate platform-specific configuration."""
        if self.platform == Platform.AZURE_DEVOPS:
            if not all([
                self.azure_devops_pat,
                self.azure_devops_organization,
                self.azure_devops_project,
                self.azure_devops_repository_id
            ]):
                raise ValueError(
                    "Azure DevOps requires: PAT, organization, project, and repository_id"
                )
        elif self.platform == Platform.GITLAB:
            if not all([self.gitlab_token, self.gitlab_project_id]):
                raise ValueError("GitLab requires: token and project_id")
        elif self.platform == Platform.GITHUB:
            if not self.github_token and not (
                self.github_app_id and self.github_app_private_key_path
            ):
                raise ValueError(
                    "GitHub requires either: token OR (app_id and private_key_path)"
                )
            if not self.github_repository:
                raise ValueError("GitHub requires: repository")

    def validate_llm_config(self) -> None:
        """Validate LLM provider configuration."""
        if self.llm_provider == LLMProvider.AZURE_AI:
            if not all([
                self.azure_ai_api_key,
                self.azure_ai_endpoint,
                self.azure_ai_deployment_name
            ]):
                raise ValueError(
                    "Azure AI requires: api_key, endpoint, and deployment_name"
                )
        elif self.llm_provider == LLMProvider.ANTHROPIC:
            if not self.anthropic_api_key:
                raise ValueError("Anthropic requires: api_key")

    def validate_all(self) -> None:
        """Validate all configuration."""
        self.validate_platform_config()
        self.validate_llm_config()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_all()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    _settings.validate_all()
    return _settings
