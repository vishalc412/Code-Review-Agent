"""Azure DevOps platform integration."""

import base64
from typing import List, Optional
from azure.devops.connection import Connection
from azure.devops.v7_0.git import GitClient
from msrest.authentication import BasicAuthentication
from .base import BasePlatform, PullRequest, PlatformComment
from core.logger import get_logger
from core.exceptions import PlatformError
from core.utils import retry_with_backoff

logger = get_logger(__name__)


class AzureDevOpsPlatform(BasePlatform):
    """Azure DevOps platform integration."""

    def __init__(
        self,
        pat: str,
        organization: str,
        project: str,
        repository_id: str
    ):
        """
        Initialize Azure DevOps platform.

        Args:
            pat: Personal Access Token
            organization: Organization name
            project: Project name
            repository_id: Repository ID or name
        """
        credentials = BasicAuthentication('', pat)
        self.organization_url = f"https://dev.azure.com/{organization}"
        self.connection = Connection(base_url=self.organization_url, creds=credentials)
        self.git_client: GitClient = self.connection.clients.get_git_client()
        self.project = project
        self.repository_id = repository_id
        self.logger = get_logger(__name__)

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def get_pull_request(self, pr_id: str) -> PullRequest:
        """Get Azure DevOps pull request details."""
        try:
            pr_number = int(pr_id)
            pr = self.git_client.get_pull_request(
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                project=self.project
            )

            return PullRequest(
                id=str(pr.pull_request_id),
                number=pr.pull_request_id,
                title=pr.title,
                description=pr.description or "",
                author=pr.created_by.display_name,
                source_branch=pr.source_ref_name.replace('refs/heads/', ''),
                target_branch=pr.target_ref_name.replace('refs/heads/', ''),
                state=pr.status,
                web_url=f"{self.organization_url}/{self.project}/_git/{self.repository_id}/pullrequest/{pr.pull_request_id}",
                created_at=pr.creation_date.isoformat(),
                updated_at=pr.creation_date.isoformat()
            )

        except Exception as e:
            self.logger.error(f"Failed to get PR {pr_id}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def get_pull_request_diff(self, pr_id: str) -> str:
        """Get unified diff for Azure DevOps pull request."""
        try:
            pr_number = int(pr_id)

            # Get PR iterations
            iterations = self.git_client.get_pull_request_iterations(
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                project=self.project
            )

            if not iterations:
                return ""

            # Get the latest iteration
            latest_iteration = iterations[-1]

            # Get changes for the iteration
            changes = self.git_client.get_pull_request_iteration_changes(
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                iteration_id=latest_iteration.id,
                project=self.project
            )

            diff_parts = []

            for change in changes.change_entries:
                if hasattr(change, 'item') and change.item:
                    # Construct a simple diff header
                    path = change.item.path
                    diff_parts.append(f"diff --git a{path} b{path}")

                    # Note: Azure DevOps API doesn't provide unified diff directly
                    # You would need to fetch file contents and generate diff
                    # For now, we'll add a placeholder
                    if change.change_type == 'edit':
                        diff_parts.append(f"--- a{path}")
                        diff_parts.append(f"+++ b{path}")

            return "\n".join(diff_parts)

        except Exception as e:
            self.logger.error(f"Failed to get diff for PR {pr_id}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def get_pull_request_files(self, pr_id: str) -> List[dict]:
        """Get files changed in Azure DevOps pull request."""
        try:
            pr_number = int(pr_id)

            iterations = self.git_client.get_pull_request_iterations(
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                project=self.project
            )

            if not iterations:
                return []

            latest_iteration = iterations[-1]

            changes = self.git_client.get_pull_request_iteration_changes(
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                iteration_id=latest_iteration.id,
                project=self.project
            )

            files = []
            for change in changes.change_entries:
                if hasattr(change, 'item') and change.item:
                    files.append({
                        'filename': change.item.path,
                        'status': change.change_type,
                        'change_type': change.change_type
                    })

            return files

        except Exception as e:
            self.logger.error(f"Failed to get files for PR {pr_id}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def post_review_comment(
        self,
        pr_id: str,
        body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> PlatformComment:
        """Post review comment on Azure DevOps pull request."""
        try:
            pr_number = int(pr_id)

            from azure.devops.v7_0.git.models import (
                GitPullRequestCommentThread,
                Comment,
                CommentThreadContext
            )

            comment_obj = Comment(content=body)

            if file_path and line_number:
                # Create thread with context for inline comment
                thread_context = CommentThreadContext(
                    file_path=file_path,
                    right_file_end={'line': line_number, 'offset': 1},
                    right_file_start={'line': line_number, 'offset': 1}
                )

                thread = GitPullRequestCommentThread(
                    comments=[comment_obj],
                    thread_context=thread_context
                )
            else:
                # Create general comment thread
                thread = GitPullRequestCommentThread(
                    comments=[comment_obj]
                )

            created_thread = self.git_client.create_thread(
                comment_thread=thread,
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                project=self.project
            )

            return PlatformComment(
                id=str(created_thread.id),
                body=body,
                author="",
                file_path=file_path,
                line_number=line_number,
                created_at=created_thread.published_date.isoformat() if created_thread.published_date else None
            )

        except Exception as e:
            self.logger.error(f"Failed to post comment on PR {pr_id}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def get_review_comments(self, pr_id: str) -> List[PlatformComment]:
        """Get all review comments for Azure DevOps pull request."""
        try:
            pr_number = int(pr_id)

            threads = self.git_client.get_threads(
                repository_id=self.repository_id,
                pull_request_id=pr_number,
                project=self.project
            )

            comments = []

            for thread in threads:
                if not thread.comments:
                    continue

                # Get thread context
                thread_context = thread.thread_context
                file_path = None
                line_number = None

                if thread_context:
                    file_path = thread_context.file_path
                    if hasattr(thread_context, 'right_file_end') and thread_context.right_file_end:
                        line_number = thread_context.right_file_end.get('line')

                # Get first comment in thread
                comment = thread.comments[0]

                comments.append(PlatformComment(
                    id=str(thread.id),
                    body=comment.content,
                    author=comment.author.display_name if comment.author else "",
                    file_path=file_path,
                    line_number=line_number,
                    created_at=comment.published_date.isoformat() if comment.published_date else None
                ))

            return comments

        except Exception as e:
            self.logger.error(f"Failed to get comments for PR {pr_id}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def create_pull_request(
        self,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str
    ) -> PullRequest:
        """Create new Azure DevOps pull request."""
        try:
            from azure.devops.v7_0.git.models import GitPullRequest

            pr_obj = GitPullRequest(
                source_ref_name=f"refs/heads/{source_branch}",
                target_ref_name=f"refs/heads/{target_branch}",
                title=title,
                description=description
            )

            pr = self.git_client.create_pull_request(
                git_pull_request_to_create=pr_obj,
                repository_id=self.repository_id,
                project=self.project
            )

            self.logger.info(
                f"Created PR #{pr.pull_request_id}",
                pr_id=pr.pull_request_id
            )

            return PullRequest(
                id=str(pr.pull_request_id),
                number=pr.pull_request_id,
                title=pr.title,
                description=pr.description or "",
                author=pr.created_by.display_name,
                source_branch=source_branch,
                target_branch=target_branch,
                state=pr.status,
                web_url=f"{self.organization_url}/{self.project}/_git/{self.repository_id}/pullrequest/{pr.pull_request_id}",
                created_at=pr.creation_date.isoformat(),
                updated_at=pr.creation_date.isoformat()
            )

        except Exception as e:
            self.logger.error(f"Failed to create PR: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def get_file_content(
        self,
        file_path: str,
        ref: Optional[str] = None
    ) -> str:
        """Get file content from Azure DevOps repository."""
        try:
            item = self.git_client.get_item(
                repository_id=self.repository_id,
                path=file_path,
                project=self.project,
                version_descriptor={'version': ref} if ref else None
            )

            # Download content
            content_stream = self.git_client.get_item_content(
                repository_id=self.repository_id,
                path=file_path,
                project=self.project,
                version_descriptor={'version': ref} if ref else None
            )

            return content_stream.decode('utf-8')

        except Exception as e:
            self.logger.error(f"Failed to get content for {file_path}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def update_file(
        self,
        file_path: str,
        content: str,
        branch: str,
        commit_message: str
    ) -> None:
        """Update file in Azure DevOps repository."""
        try:
            from azure.devops.v7_0.git.models import (
                GitRefUpdate,
                GitCommitRef,
                GitChange,
                ItemContent
            )

            # Get the current ref
            refs = self.git_client.get_refs(
                repository_id=self.repository_id,
                project=self.project,
                filter=f"heads/{branch}"
            )

            if not refs:
                raise PlatformError(f"Branch {branch} not found")

            old_object_id = refs[0].object_id

            # Create change
            change = GitChange(
                change_type='edit',
                item={'path': file_path},
                new_content=ItemContent(
                    content=content,
                    content_type='rawtext'
                )
            )

            # Create commit
            commit = GitCommitRef(
                comment=commit_message,
                changes=[change]
            )

            # Create push
            ref_update = GitRefUpdate(
                name=f"refs/heads/{branch}",
                old_object_id=old_object_id
            )

            push = {
                'refUpdates': [ref_update],
                'commits': [commit]
            }

            self.git_client.create_push(
                push=push,
                repository_id=self.repository_id,
                project=self.project
            )

            self.logger.info(
                f"Updated file {file_path} on branch {branch}",
                file=file_path,
                branch=branch
            )

        except Exception as e:
            self.logger.error(f"Failed to update file {file_path}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")

    def create_branch(self, branch_name: str, from_branch: str = "main") -> None:
        """Create a new branch in Azure DevOps repository."""
        try:
            from azure.devops.v7_0.git.models import GitRefUpdate

            # Get the source branch ref
            refs = self.git_client.get_refs(
                repository_id=self.repository_id,
                project=self.project,
                filter=f"heads/{from_branch}"
            )

            if not refs:
                raise PlatformError(f"Source branch {from_branch} not found")

            source_sha = refs[0].object_id

            # Create new branch ref
            ref_update = GitRefUpdate(
                name=f"refs/heads/{branch_name}",
                old_object_id="0000000000000000000000000000000000000000",
                new_object_id=source_sha
            )

            self.git_client.update_refs(
                ref_updates=[ref_update],
                repository_id=self.repository_id,
                project=self.project
            )

            self.logger.info(
                f"Created branch {branch_name} from {from_branch}",
                branch=branch_name,
                source=from_branch
            )

        except Exception as e:
            self.logger.error(f"Failed to create branch {branch_name}: {e}")
            raise PlatformError(f"Azure DevOps API error: {e}")
