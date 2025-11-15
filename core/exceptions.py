"""Custom exceptions for code review agents."""


class CodeReviewAgentError(Exception):
    """Base exception for all agent errors."""
    pass


class PlatformError(CodeReviewAgentError):
    """Exception for platform API errors."""
    pass


class LLMError(CodeReviewAgentError):
    """Exception for LLM provider errors."""
    pass


class ConfigurationError(CodeReviewAgentError):
    """Exception for configuration errors."""
    pass


class ValidationError(CodeReviewAgentError):
    """Exception for validation errors."""
    pass


class GitOperationError(CodeReviewAgentError):
    """Exception for git operation errors."""
    pass


class NetworkError(CodeReviewAgentError):
    """Exception for network-related errors."""
    pass


class AuthenticationError(CodeReviewAgentError):
    """Exception for authentication errors."""
    pass


class RateLimitError(CodeReviewAgentError):
    """Exception for rate limit errors."""
    pass
