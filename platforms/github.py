"""GitHub platform integration."""

import base64
from typing import List, Optional
from github import Github, GithubException
from .base import BasePlatform, PullRequest, PlatformComment
from core.logger import get_logger
from core.exceptions import PlatformError
from core.utils import retry_with_backoff, parse_repository_name

logger = get_logger(__name__)


class GitHubPlatform(BasePlatform):
    """GitHub platform integration."""

    def __init__(self, token: str, repository: str):
        """
        Initialize GitHub platform.

        Args:
            token: GitHub personal access token
            repository: Repository in format "owner/repo"
        """
        self.client = Github(token)
        self.owner, self.repo_name = parse_repository_name(repository)
        self.repo = self.client.get_repo(f"{self.owner}/{self.repo_name}")
        self.logger = get_logger(__name__)

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def get_pull_request(self, pr_id: str) -> PullRequest:
        """Get GitHub pull request details."""
        try:
            pr_number = int(pr_id)
            pr = self.repo.get_pull(pr_number)

            return PullRequest(
                id=str(pr.id),
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                source_branch=pr.head.ref,
                target_branch=pr.base.ref,
                state=pr.state,
                web_url=pr.html_url,
                created_at=pr.created_at.isoformat(),
                updated_at=pr.updated_at.isoformat()
            )

        except GithubException as e:
            self.logger.error(f"Failed to get PR {pr_id}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def get_pull_request_diff(self, pr_id: str) -> str:
        """Get unified diff for GitHub pull request."""
        try:
            pr_number = int(pr_id)
            pr = self.repo.get_pull(pr_number)

            # Get files and construct diff
            files = pr.get_files()
            diff_parts = []

            for file in files:
                if file.patch:
                    diff_parts.append(f"diff --git a/{file.filename} b/{file.filename}")
                    diff_parts.append(f"--- a/{file.filename}")
                    diff_parts.append(f"+++ b/{file.filename}")
                    diff_parts.append(file.patch)

            return "\n".join(diff_parts)

        except GithubException as e:
            self.logger.error(f"Failed to get diff for PR {pr_id}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def get_pull_request_files(self, pr_id: str) -> List[dict]:
        """Get files changed in GitHub pull request."""
        try:
            pr_number = int(pr_id)
            pr = self.repo.get_pull(pr_number)
            files = pr.get_files()

            return [
                {
                    'filename': f.filename,
                    'status': f.status,
                    'additions': f.additions,
                    'deletions': f.deletions,
                    'changes': f.changes,
                    'patch': f.patch
                }
                for f in files
            ]

        except GithubException as e:
            self.logger.error(f"Failed to get files for PR {pr_id}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def post_review_comment(
        self,
        pr_id: str,
        body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> PlatformComment:
        """Post review comment on GitHub pull request."""
        try:
            pr_number = int(pr_id)
            pr = self.repo.get_pull(pr_number)

            if file_path and line_number:
                # Post inline comment
                commit = pr.get_commits().reversed[0]
                comment = pr.create_review_comment(
                    body=body,
                    commit=commit,
                    path=file_path,
                    line=line_number
                )
            else:
                # Post general comment
                comment = pr.create_issue_comment(body)

            return PlatformComment(
                id=str(comment.id),
                body=comment.body,
                author=comment.user.login,
                file_path=file_path,
                line_number=line_number,
                created_at=comment.created_at.isoformat(),
                updated_at=comment.updated_at.isoformat()
            )

        except GithubException as e:
            self.logger.error(f"Failed to post comment on PR {pr_id}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def get_review_comments(self, pr_id: str) -> List[PlatformComment]:
        """Get all review comments for GitHub pull request."""
        try:
            pr_number = int(pr_id)
            pr = self.repo.get_pull(pr_number)

            comments = []

            # Get review comments (inline)
            for comment in pr.get_review_comments():
                comments.append(PlatformComment(
                    id=str(comment.id),
                    body=comment.body,
                    author=comment.user.login,
                    file_path=comment.path,
                    line_number=comment.line or comment.original_line,
                    created_at=comment.created_at.isoformat(),
                    updated_at=comment.updated_at.isoformat()
                ))

            # Get issue comments (general)
            for comment in pr.get_issue_comments():
                comments.append(PlatformComment(
                    id=str(comment.id),
                    body=comment.body,
                    author=comment.user.login,
                    created_at=comment.created_at.isoformat(),
                    updated_at=comment.updated_at.isoformat()
                ))

            return comments

        except GithubException as e:
            self.logger.error(f"Failed to get comments for PR {pr_id}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def create_pull_request(
        self,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str
    ) -> PullRequest:
        """Create new GitHub pull request."""
        try:
            pr = self.repo.create_pull(
                title=title,
                body=description,
                head=source_branch,
                base=target_branch
            )

            self.logger.info(
                f"Created PR #{pr.number}",
                pr_number=pr.number,
                url=pr.html_url
            )

            return PullRequest(
                id=str(pr.id),
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                source_branch=pr.head.ref,
                target_branch=pr.base.ref,
                state=pr.state,
                web_url=pr.html_url,
                created_at=pr.created_at.isoformat(),
                updated_at=pr.updated_at.isoformat()
            )

        except GithubException as e:
            self.logger.error(f"Failed to create PR: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def get_file_content(
        self,
        file_path: str,
        ref: Optional[str] = None
    ) -> str:
        """Get file content from GitHub repository."""
        try:
            content = self.repo.get_contents(file_path, ref=ref)

            if isinstance(content, list):
                raise PlatformError(f"{file_path} is a directory, not a file")

            # Decode base64 content
            return base64.b64decode(content.content).decode('utf-8')

        except GithubException as e:
            self.logger.error(f"Failed to get content for {file_path}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GithubException,))
    def update_file(
        self,
        file_path: str,
        content: str,
        branch: str,
        commit_message: str
    ) -> None:
        """Update file in GitHub repository."""
        try:
            # Get current file to get its SHA
            try:
                file_content = self.repo.get_contents(file_path, ref=branch)
                sha = file_content.sha
            except GithubException:
                # File doesn't exist, create it
                sha = None

            if sha:
                # Update existing file
                self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=sha,
                    branch=branch
                )
            else:
                # Create new file
                self.repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    branch=branch
                )

            self.logger.info(
                f"Updated file {file_path} on branch {branch}",
                file=file_path,
                branch=branch
            )

        except GithubException as e:
            self.logger.error(f"Failed to update file {file_path}: {e}")
            raise PlatformError(f"GitHub API error: {e}")

    def create_branch(self, branch_name: str, from_branch: str = "main") -> None:
        """Create a new branch in GitHub repository."""
        try:
            # Get the source branch
            source = self.repo.get_branch(from_branch)

            # Create new branch
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source.commit.sha
            )

            self.logger.info(
                f"Created branch {branch_name} from {from_branch}",
                branch=branch_name,
                source=from_branch
            )

        except GithubException as e:
            self.logger.error(f"Failed to create branch {branch_name}: {e}")
            raise PlatformError(f"GitHub API error: {e}")
