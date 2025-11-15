"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from parsers.comment_parser import ReviewComment


@dataclass
class ReviewResult:
    """Result from LLM code review."""
    comments: List[ReviewComment]
    summary: str
    raw_response: str
    tokens_used: Optional[int] = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def review_code(
        self,
        diff: str,
        context: dict,
        focus: str = "all",
        depth: str = "standard"
    ) -> ReviewResult:
        """
        Review code changes using LLM.

        Args:
            diff: Unified diff of code changes
            context: Additional context (PR title, description, etc.)
            focus: Focus area (all, security, performance, style, bugs)
            depth: Review depth (quick, standard, deep)

        Returns:
            ReviewResult object
        """
        pass

    @abstractmethod
    def generate_fix(
        self,
        file_content: str,
        comment: ReviewComment,
        file_path: str
    ) -> str:
        """
        Generate code fix based on review comment.

        Args:
            file_content: Current file content
            comment: Review comment to address
            file_path: Path to the file

        Returns:
            Fixed code content
        """
        pass

    @abstractmethod
    def analyze_comments(
        self,
        comments: List[ReviewComment],
        file_contents: dict[str, str]
    ) -> dict:
        """
        Analyze review comments and determine fixability.

        Args:
            comments: List of review comments
            file_contents: Dictionary mapping file paths to contents

        Returns:
            Analysis result with fixable comments categorized
        """
        pass
