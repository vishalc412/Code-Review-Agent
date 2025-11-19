"""Parser for review comments."""

import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from core.logger import get_logger
from core.config import Severity

logger = get_logger(__name__)


class CommentCategory(str, Enum):
    """Categories of review comments."""
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    OTHER = "other"


@dataclass
class ReviewComment:
    """Represents a code review comment."""
    file: str
    line: Optional[int]
    severity: Severity
    category: CommentCategory
    message: str
    suggestion: Optional[str] = None
    comment_id: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    resolved: bool = False

    def is_actionable(self) -> bool:
        """Check if the comment is actionable (requires code changes)."""
        # Non-actionable keywords
        non_actionable_keywords = [
            "looks good",
            "lgtm",
            "approved",
            "question:",
            "why did you",
            "can you explain",
        ]

        message_lower = self.message.lower()
        for keyword in non_actionable_keywords:
            if keyword in message_lower:
                return False

        return True


class CommentParser:
    """Parser for review comments."""

    def __init__(self, comment_prefix: str = "[AI Review]"):
        self.comment_prefix = comment_prefix
        self.logger = get_logger(__name__)

    def parse_json_comments(self, json_data: List[dict]) -> List[ReviewComment]:
        """
        Parse comments from JSON format (output from LLM).

        Args:
            json_data: List of comment dictionaries

        Returns:
            List of ReviewComment objects
        """
        comments = []

        for item in json_data:
            try:
                comment = ReviewComment(
                    file=item.get('file', ''),
                    line=item.get('line'),
                    severity=Severity(item.get('severity', 'minor')),
                    category=CommentCategory(item.get('category', 'other')),
                    message=item.get('message', ''),
                    suggestion=item.get('suggestion'),
                )
                comments.append(comment)
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Failed to parse comment: {e}", item=item)
                continue

        self.logger.info(f"Parsed {len(comments)} comments from JSON")
        return comments

    def parse_platform_comments(
        self,
        platform_comments: List[dict],
        platform: str
    ) -> List[ReviewComment]:
        """
        Parse comments from platform-specific format.

        Args:
            platform_comments: List of platform comment objects
            platform: Platform name (github, gitlab, azure_devops)

        Returns:
            List of ReviewComment objects
        """
        if platform == "github":
            return self._parse_github_comments(platform_comments)
        elif platform == "gitlab":
            return self._parse_gitlab_comments(platform_comments)
        elif platform == "azure_devops":
            return self._parse_azure_devops_comments(platform_comments)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _parse_github_comments(self, comments: List[dict]) -> List[ReviewComment]:
        """Parse GitHub PR review comments."""
        parsed_comments = []

        for comment in comments:
            # Skip bot comments unless they're from our AI
            if comment.get('user', {}).get('type') == 'Bot':
                if self.comment_prefix not in comment.get('body', ''):
                    continue

            parsed_comment = ReviewComment(
                file=comment.get('path', ''),
                line=comment.get('line') or comment.get('original_line'),
                severity=self._extract_severity(comment.get('body', '')),
                category=self._extract_category(comment.get('body', '')),
                message=self._clean_message(comment.get('body', '')),
                comment_id=str(comment.get('id')),
                author=comment.get('user', {}).get('login'),
                created_at=comment.get('created_at'),
                resolved=False  # GitHub doesn't have a resolved field directly
            )

            if parsed_comment.is_actionable():
                parsed_comments.append(parsed_comment)

        self.logger.info(f"Parsed {len(parsed_comments)} actionable comments from GitHub")
        return parsed_comments

    def _parse_gitlab_comments(self, comments: List[dict]) -> List[ReviewComment]:
        """Parse GitLab MR comments."""
        parsed_comments = []

        for comment in comments:
            notes = comment.get('notes', [])
            for note in notes:
                # Skip system notes
                if note.get('system', False):
                    continue

                # Get position information
                position = note.get('position', {})

                parsed_comment = ReviewComment(
                    file=position.get('new_path', ''),
                    line=position.get('new_line'),
                    severity=self._extract_severity(note.get('body', '')),
                    category=self._extract_category(note.get('body', '')),
                    message=self._clean_message(note.get('body', '')),
                    comment_id=str(note.get('id')),
                    author=note.get('author', {}).get('username'),
                    created_at=note.get('created_at'),
                    resolved=note.get('resolved', False)
                )

                if parsed_comment.is_actionable():
                    parsed_comments.append(parsed_comment)

        self.logger.info(f"Parsed {len(parsed_comments)} actionable comments from GitLab")
        return parsed_comments

    def _parse_azure_devops_comments(self, comments: List[dict]) -> List[ReviewComment]:
        """Parse Azure DevOps PR comments."""
        parsed_comments = []

        for thread in comments:
            # Skip threads without comments
            if not thread.get('comments'):
                continue

            # Get the first comment in the thread
            comment = thread['comments'][0]

            # Get position information
            thread_context = thread.get('threadContext', {})
            right_file_end = thread_context.get('rightFileEnd', {})

            parsed_comment = ReviewComment(
                file=thread_context.get('filePath', ''),
                line=right_file_end.get('line'),
                severity=self._extract_severity(comment.get('content', '')),
                category=self._extract_category(comment.get('content', '')),
                message=self._clean_message(comment.get('content', '')),
                comment_id=str(thread.get('id')),
                author=comment.get('author', {}).get('displayName'),
                created_at=comment.get('publishedDate'),
                resolved=thread.get('status') == 'closed'
            )

            if parsed_comment.is_actionable():
                parsed_comments.append(parsed_comment)

        self.logger.info(f"Parsed {len(parsed_comments)} actionable comments from Azure DevOps")
        return parsed_comments

    def _extract_severity(self, text: str) -> Severity:
        """Extract severity from comment text."""
        text_lower = text.lower()

        if any(word in text_lower for word in ['critical', 'blocker', 'security']):
            return Severity.CRITICAL
        elif any(word in text_lower for word in ['major', 'important', 'bug']):
            return Severity.MAJOR
        elif any(word in text_lower for word in ['minor', 'small']):
            return Severity.MINOR
        else:
            return Severity.SUGGESTION

    def _extract_category(self, text: str) -> CommentCategory:
        """Extract category from comment text."""
        text_lower = text.lower()

        if 'security' in text_lower or 'vulnerability' in text_lower:
            return CommentCategory.SECURITY
        elif 'performance' in text_lower or 'slow' in text_lower or 'optimize' in text_lower:
            return CommentCategory.PERFORMANCE
        elif 'test' in text_lower or 'coverage' in text_lower:
            return CommentCategory.TESTING
        elif 'style' in text_lower or 'format' in text_lower or 'lint' in text_lower:
            return CommentCategory.STYLE
        elif 'documentation' in text_lower or 'comment' in text_lower or 'docstring' in text_lower:
            return CommentCategory.DOCUMENTATION
        elif 'bug' in text_lower or 'error' in text_lower or 'fix' in text_lower:
            return CommentCategory.BUG
        else:
            return CommentCategory.OTHER

    def _clean_message(self, message: str) -> str:
        """Clean and normalize message text."""
        # Remove AI prefix if present
        if self.comment_prefix in message:
            message = message.replace(self.comment_prefix, '').strip()

        # Remove extra whitespace
        message = re.sub(r'\s+', ' ', message).strip()

        return message

    def filter_by_severity(
        self,
        comments: List[ReviewComment],
        min_severity: Severity
    ) -> List[ReviewComment]:
        """
        Filter comments by minimum severity.

        Args:
            comments: List of comments
            min_severity: Minimum severity level

        Returns:
            Filtered list of comments
        """
        severity_order = {
            Severity.CRITICAL: 4,
            Severity.MAJOR: 3,
            Severity.MINOR: 2,
            Severity.SUGGESTION: 1
        }

        min_level = severity_order[min_severity]
        filtered = [
            c for c in comments
            if severity_order[c.severity] >= min_level
        ]

        self.logger.info(
            f"Filtered {len(filtered)} comments with severity >= {min_severity}",
            original=len(comments),
            filtered=len(filtered)
        )
        return filtered

    def group_by_file(
        self,
        comments: List[ReviewComment]
    ) -> dict[str, List[ReviewComment]]:
        """
        Group comments by file.

        Args:
            comments: List of comments

        Returns:
            Dictionary mapping file paths to comments
        """
        grouped = {}
        for comment in comments:
            if comment.file not in grouped:
                grouped[comment.file] = []
            grouped[comment.file].append(comment)

        return grouped
