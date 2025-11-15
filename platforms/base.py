"""Base class for platform integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PullRequest:
    """Represents a pull request/merge request."""
    id: str
    number: int
    title: str
    description: str
    author: str
    source_branch: str
    target_branch: str
    state: str
    web_url: str
    created_at: str
    updated_at: str


@dataclass
class PlatformComment:
    """Represents a comment on a platform."""
    id: str
    body: str
    author: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BasePlatform(ABC):
    """Abstract base class for platform integrations."""

    @abstractmethod
    def get_pull_request(self, pr_id: str) -> PullRequest:
        """
        Get pull request details.

        Args:
            pr_id: Pull request ID or number

        Returns:
            PullRequest object
        """
        pass

    @abstractmethod
    def get_pull_request_diff(self, pr_id: str) -> str:
        """
        Get unified diff for pull request.

        Args:
            pr_id: Pull request ID or number

        Returns:
            Unified diff string
        """
        pass

    @abstractmethod
    def get_pull_request_files(self, pr_id: str) -> List[dict]:
        """
        Get list of files changed in pull request.

        Args:
            pr_id: Pull request ID or number

        Returns:
            List of file information dictionaries
        """
        pass

    @abstractmethod
    def post_review_comment(
        self,
        pr_id: str,
        body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> PlatformComment:
        """
        Post a review comment on pull request.

        Args:
            pr_id: Pull request ID or number
            body: Comment text
            file_path: Optional file path for inline comment
            line_number: Optional line number for inline comment

        Returns:
            Created PlatformComment
        """
        pass

    @abstractmethod
    def get_review_comments(self, pr_id: str) -> List[PlatformComment]:
        """
        Get all review comments for a pull request.

        Args:
            pr_id: Pull request ID or number

        Returns:
            List of PlatformComment objects
        """
        pass

    @abstractmethod
    def create_pull_request(
        self,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str
    ) -> PullRequest:
        """
        Create a new pull request.

        Args:
            title: PR title
            description: PR description
            source_branch: Source branch name
            target_branch: Target branch name

        Returns:
            Created PullRequest object
        """
        pass

    @abstractmethod
    def get_file_content(
        self,
        file_path: str,
        ref: Optional[str] = None
    ) -> str:
        """
        Get content of a file from repository.

        Args:
            file_path: Path to file
            ref: Optional git reference (branch, commit, tag)

        Returns:
            File content as string
        """
        pass

    @abstractmethod
    def update_file(
        self,
        file_path: str,
        content: str,
        branch: str,
        commit_message: str
    ) -> None:
        """
        Update a file in the repository.

        Args:
            file_path: Path to file
            content: New file content
            branch: Branch name
            commit_message: Commit message
        """
        pass
