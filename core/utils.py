"""Utility functions for code review agents."""

import time
import functools
from typing import Callable, Any, TypeVar, Optional
from .logger import get_logger
from .exceptions import NetworkError, RateLimitError

logger = get_logger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: int = 2,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed after {max_retries} attempts",
                            function=func.__name__,
                            error=str(e)
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s",
                        function=func.__name__,
                        error=str(e),
                        delay=delay
                    )
                    time.sleep(delay)

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_repository_name(repo_string: str) -> tuple[str, str]:
    """
    Parse repository string into owner and repo name.

    Args:
        repo_string: Repository string (e.g., "owner/repo")

    Returns:
        Tuple of (owner, repo)
    """
    parts = repo_string.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid repository format: {repo_string}")
    return parts[0], parts[1]


def should_exclude_file(file_path: str, exclude_patterns: list[str]) -> bool:
    """
    Check if a file should be excluded based on patterns.

    Args:
        file_path: Path to the file
        exclude_patterns: List of exclusion patterns

    Returns:
        True if file should be excluded
    """
    import fnmatch

    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    Rough estimation: 1 token ≈ 4 characters

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4


def format_file_path(file_path: str, line_number: Optional[int] = None) -> str:
    """
    Format file path with optional line number for display.

    Args:
        file_path: Path to the file
        line_number: Optional line number

    Returns:
        Formatted string
    """
    if line_number:
        return f"{file_path}:{line_number}"
    return file_path


def sanitize_branch_name(name: str) -> str:
    """
    Sanitize a string to be used as a git branch name.

    Args:
        name: String to sanitize

    Returns:
        Sanitized branch name
    """
    import re
    # Replace invalid characters with hyphens
    name = re.sub(r'[^\w\-\/]', '-', name)
    # Remove consecutive hyphens
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    return name.lower()


def calculate_diff_stats(diff_text: str) -> dict[str, int]:
    """
    Calculate statistics from a diff.

    Args:
        diff_text: Unified diff text

    Returns:
        Dictionary with stats (additions, deletions, files_changed)
    """
    additions = 0
    deletions = 0
    files_changed = 0

    for line in diff_text.split('\n'):
        if line.startswith('+++') or line.startswith('---'):
            if not line.endswith('/dev/null'):
                files_changed += 1
        elif line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1

    return {
        'additions': additions,
        'deletions': deletions,
        'files_changed': files_changed // 2  # Divide by 2 as each file has +++ and ---
    }
