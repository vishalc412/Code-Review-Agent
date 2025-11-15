"""Factory for creating LLM clients."""

from .base import BaseLLMClient
from .anthropic_client import AnthropicClient
from .azure_ai_client import AzureAIClient
from core.config import Settings, LLMProvider
from core.exceptions import ConfigurationError


def create_llm_client(settings: Settings) -> BaseLLMClient:
    """
    Create an LLM client based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured LLM client instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    if settings.llm_provider == LLMProvider.ANTHROPIC:
        if not settings.anthropic_api_key:
            raise ConfigurationError("Anthropic API key is required")

        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model
        )

    elif settings.llm_provider == LLMProvider.AZURE_AI:
        if not all([
            settings.azure_ai_api_key,
            settings.azure_ai_endpoint,
            settings.azure_ai_deployment_name
        ]):
            raise ConfigurationError(
                "Azure AI requires api_key, endpoint, and deployment_name"
            )

        return AzureAIClient(
            api_key=settings.azure_ai_api_key,
            endpoint=settings.azure_ai_endpoint,
            deployment_name=settings.azure_ai_deployment_name,
            api_version=settings.azure_ai_api_version
        )

    else:
        raise ConfigurationError(f"Unsupported LLM provider: {settings.llm_provider}")
