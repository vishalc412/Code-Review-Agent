"""GitLab platform integration."""

import base64
from typing import List, Optional
import gitlab
from gitlab.exceptions import GitlabError
from .base import BasePlatform, PullRequest, PlatformComment
from core.logger import get_logger
from core.exceptions import PlatformError
from core.utils import retry_with_backoff

logger = get_logger(__name__)


class GitLabPlatform(BasePlatform):
    """GitLab platform integration."""

    def __init__(self, token: str, project_id: str, url: str = "https://gitlab.com"):
        """
        Initialize GitLab platform.

        Args:
            token: GitLab personal access token
            project_id: Project ID
            url: GitLab instance URL
        """
        self.client = gitlab.Gitlab(url, private_token=token)
        self.client.auth()
        self.project = self.client.projects.get(project_id)
        self.logger = get_logger(__name__)

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def get_pull_request(self, pr_id: str) -> PullRequest:
        """Get GitLab merge request details."""
        try:
            mr_iid = int(pr_id)
            mr = self.project.mergerequests.get(mr_iid)

            return PullRequest(
                id=str(mr.id),
                number=mr.iid,
                title=mr.title,
                description=mr.description or "",
                author=mr.author.get('username', ''),
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                state=mr.state,
                web_url=mr.web_url,
                created_at=mr.created_at,
                updated_at=mr.updated_at
            )

        except GitlabError as e:
            self.logger.error(f"Failed to get MR {pr_id}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def get_pull_request_diff(self, pr_id: str) -> str:
        """Get unified diff for GitLab merge request."""
        try:
            mr_iid = int(pr_id)
            mr = self.project.mergerequests.get(mr_iid)

            # Get changes/diffs
            changes = mr.changes()
            diff_parts = []

            for change in changes.get('changes', []):
                diff_parts.append(change.get('diff', ''))

            return "\n".join(diff_parts)

        except GitlabError as e:
            self.logger.error(f"Failed to get diff for MR {pr_id}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def get_pull_request_files(self, pr_id: str) -> List[dict]:
        """Get files changed in GitLab merge request."""
        try:
            mr_iid = int(pr_id)
            mr = self.project.mergerequests.get(mr_iid)

            changes = mr.changes()

            return [
                {
                    'filename': change.get('new_path') or change.get('old_path'),
                    'status': 'modified' if change.get('new_file') else 'deleted' if change.get('deleted_file') else 'modified',
                    'old_path': change.get('old_path'),
                    'new_path': change.get('new_path'),
                    'patch': change.get('diff')
                }
                for change in changes.get('changes', [])
            ]

        except GitlabError as e:
            self.logger.error(f"Failed to get files for MR {pr_id}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def post_review_comment(
        self,
        pr_id: str,
        body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> PlatformComment:
        """Post review comment on GitLab merge request."""
        try:
            mr_iid = int(pr_id)
            mr = self.project.mergerequests.get(mr_iid)

            if file_path and line_number:
                # Create a discussion with position
                # Get the latest commit
                commits = mr.commits()
                if not commits:
                    raise PlatformError("No commits found in MR")

                latest_commit = commits[0]

                # Create discussion with position
                discussion = mr.discussions.create({
                    'body': body,
                    'position': {
                        'base_sha': mr.diff_refs.get('base_sha'),
                        'start_sha': mr.diff_refs.get('start_sha'),
                        'head_sha': mr.diff_refs.get('head_sha'),
                        'position_type': 'text',
                        'new_path': file_path,
                        'new_line': line_number,
                    }
                })

                note = discussion.attributes.get('notes', [{}])[0]

                return PlatformComment(
                    id=str(discussion.id),
                    body=body,
                    author=note.get('author', {}).get('username', ''),
                    file_path=file_path,
                    line_number=line_number,
                    created_at=note.get('created_at'),
                    updated_at=note.get('updated_at')
                )
            else:
                # Post general comment
                note = mr.notes.create({'body': body})

                return PlatformComment(
                    id=str(note.id),
                    body=note.body,
                    author=note.author.get('username', ''),
                    created_at=note.created_at,
                    updated_at=note.updated_at
                )

        except GitlabError as e:
            self.logger.error(f"Failed to post comment on MR {pr_id}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def get_review_comments(self, pr_id: str) -> List[PlatformComment]:
        """Get all review comments for GitLab merge request."""
        try:
            mr_iid = int(pr_id)
            mr = self.project.mergerequests.get(mr_iid)

            comments = []

            # Get discussions
            discussions = mr.discussions.list(get_all=True)

            for discussion in discussions:
                notes = discussion.attributes.get('notes', [])
                for note in notes:
                    # Skip system notes
                    if note.get('system', False):
                        continue

                    # Get position if available
                    position = note.get('position', {})
                    file_path = position.get('new_path')
                    line_number = position.get('new_line')

                    comments.append(PlatformComment(
                        id=str(note.get('id')),
                        body=note.get('body', ''),
                        author=note.get('author', {}).get('username', ''),
                        file_path=file_path,
                        line_number=line_number,
                        created_at=note.get('created_at'),
                        updated_at=note.get('updated_at')
                    ))

            return comments

        except GitlabError as e:
            self.logger.error(f"Failed to get comments for MR {pr_id}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def create_pull_request(
        self,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str
    ) -> PullRequest:
        """Create new GitLab merge request."""
        try:
            mr = self.project.mergerequests.create({
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description
            })

            self.logger.info(
                f"Created MR !{mr.iid}",
                mr_iid=mr.iid,
                url=mr.web_url
            )

            return PullRequest(
                id=str(mr.id),
                number=mr.iid,
                title=mr.title,
                description=mr.description or "",
                author=mr.author.get('username', ''),
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                state=mr.state,
                web_url=mr.web_url,
                created_at=mr.created_at,
                updated_at=mr.updated_at
            )

        except GitlabError as e:
            self.logger.error(f"Failed to create MR: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def get_file_content(
        self,
        file_path: str,
        ref: Optional[str] = None
    ) -> str:
        """Get file content from GitLab repository."""
        try:
            file_obj = self.project.files.get(
                file_path=file_path,
                ref=ref or self.project.default_branch
            )

            # Decode base64 content
            return base64.b64decode(file_obj.content).decode('utf-8')

        except GitlabError as e:
            self.logger.error(f"Failed to get content for {file_path}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(GitlabError,))
    def update_file(
        self,
        file_path: str,
        content: str,
        branch: str,
        commit_message: str
    ) -> None:
        """Update file in GitLab repository."""
        try:
            # Try to get existing file
            try:
                file_obj = self.project.files.get(file_path=file_path, ref=branch)
                # Update existing file
                file_obj.content = content
                file_obj.save(branch=branch, commit_message=commit_message)
            except GitlabError:
                # File doesn't exist, create it
                self.project.files.create({
                    'file_path': file_path,
                    'branch': branch,
                    'content': content,
                    'commit_message': commit_message
                })

            self.logger.info(
                f"Updated file {file_path} on branch {branch}",
                file=file_path,
                branch=branch
            )

        except GitlabError as e:
            self.logger.error(f"Failed to update file {file_path}: {e}")
            raise PlatformError(f"GitLab API error: {e}")

    def create_branch(self, branch_name: str, from_branch: str = "main") -> None:
        """Create a new branch in GitLab repository."""
        try:
            self.project.branches.create({
                'branch': branch_name,
                'ref': from_branch
            })

            self.logger.info(
                f"Created branch {branch_name} from {from_branch}",
                branch=branch_name,
                source=from_branch
            )

        except GitlabError as e:
            self.logger.error(f"Failed to create branch {branch_name}: {e}")
            raise PlatformError(f"GitLab API error: {e}")
