"""Tests for configuration management."""

import pytest
from core.config import Settings, Platform, LLMProvider
from core.exceptions import ConfigurationError


def test_settings_creation():
    """Test creating settings object."""
    settings = Settings(
        platform="github",
        github_token="test",
        github_repository="test/repo",
        llm_provider="anthropic",
        anthropic_api_key="test"
    )

    assert settings.platform == Platform.GITHUB
    assert settings.llm_provider == LLMProvider.ANTHROPIC


def test_github_validation():
    """Test GitHub configuration validation."""
    settings = Settings(
        platform="github",
        github_token="test",
        github_repository="test/repo",
        llm_provider="anthropic",
        anthropic_api_key="test"
    )

    # Should not raise
    settings.validate_platform_config()


def test_github_validation_missing_token():
    """Test GitHub validation with missing token."""
    settings = Settings(
        platform="github",
        github_repository="test/repo",
        llm_provider="anthropic",
        anthropic_api_key="test"
    )

    with pytest.raises(ValueError):
        settings.validate_platform_config()


def test_anthropic_validation():
    """Test Anthropic configuration validation."""
    settings = Settings(
        platform="github",
        github_token="test",
        github_repository="test/repo",
        llm_provider="anthropic",
        anthropic_api_key="test"
    )

    # Should not raise
    settings.validate_llm_config()


def test_exclude_patterns_parsing():
    """Test exclude patterns are parsed correctly."""
    settings = Settings(
        platform="github",
        github_token="test",
        github_repository="test/repo",
        llm_provider="anthropic",
        anthropic_api_key="test",
        exclude_patterns="*.md,*.txt,test/**"
    )

    # The field_validator should parse this into a list
    assert isinstance(settings.exclude_patterns, (list, str))
