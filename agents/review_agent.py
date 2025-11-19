"""Code Review Agent - Agent 1."""

import click
from typing import Optional
from .base_agent import BaseAgent
from parsers.diff_parser import DiffParser
from core.utils import should_exclude_file, calculate_diff_stats
from core.exceptions import CodeReviewAgentError
from core.config import get_settings


class ReviewAgent(BaseAgent):
    """
    Agent that reviews code changes and posts comments on pull requests.
    """

    def __init__(self, settings=None):
        super().__init__(settings)
        self.diff_parser = DiffParser()

    def run(self, pr_id: str) -> dict:
        """
        Run code review on a pull request.

        Args:
            pr_id: Pull request ID or number

        Returns:
            Dictionary with review results
        """
        try:
            self.logger.info(f"Starting code review for PR {pr_id}", pr_id=pr_id)

            # Step 1: Get PR details
            pr = self.platform.get_pull_request(pr_id)
            self.logger.info(
                f"Retrieved PR: {pr.title}",
                pr_id=pr_id,
                title=pr.title,
                author=pr.author
            )

            # Step 2: Get PR diff
            diff = self.platform.get_pull_request_diff(pr_id)
            diff_stats = calculate_diff_stats(diff)
            self.logger.info(
                "Retrieved PR diff",
                stats=diff_stats
            )

            # Step 3: Parse diff
            file_diffs = self.diff_parser.parse(diff)
            self.logger.info(f"Parsed {len(file_diffs)} files from diff")

            # Step 4: Filter files based on exclude patterns
            exclude_patterns = self.settings.exclude_patterns
            if isinstance(exclude_patterns, str):
                exclude_patterns = [p.strip() for p in exclude_patterns.split(',')]

            filtered_diffs = [
                fd for fd in file_diffs
                if not should_exclude_file(fd.file_path, exclude_patterns)
                   and not fd.is_binary
                   and not fd.is_deleted_file
            ]

            self.logger.info(
                f"Filtered to {len(filtered_diffs)} files for review",
                original=len(file_diffs),
                filtered=len(filtered_diffs)
            )

            # Check if we exceed max files limit
            if len(filtered_diffs) > self.settings.max_files_to_review:
                self.logger.warning(
                    f"Too many files ({len(filtered_diffs)}), limiting to {self.settings.max_files_to_review}",
                    total=len(filtered_diffs),
                    limit=self.settings.max_files_to_review
                )
                filtered_diffs = filtered_diffs[:self.settings.max_files_to_review]

            if not filtered_diffs:
                self.logger.info("No files to review after filtering")
                return {
                    'status': 'success',
                    'pr_id': pr_id,
                    'comments_posted': 0,
                    'message': 'No files to review'
                }

            # Step 5: Review code with LLM
            context = {
                'title': pr.title,
                'description': pr.description,
                'author': pr.author,
                'files_changed': len(file_diffs)
            }

            # Reconstruct diff for filtered files
            filtered_diff = self._reconstruct_diff(filtered_diffs)

            review_result = self.llm_client.review_code(
                diff=filtered_diff,
                context=context,
                focus=self.settings.review_focus,
                depth=self.settings.review_depth
            )

            self.logger.info(
                f"LLM review completed with {len(review_result.comments)} comments",
                comments=len(review_result.comments),
                tokens_used=review_result.tokens_used
            )

            # Step 6: Filter comments by severity threshold
            from parsers.comment_parser import CommentParser
            comment_parser = CommentParser(self.settings.review_comment_prefix)

            filtered_comments = comment_parser.filter_by_severity(
                review_result.comments,
                self.settings.severity_threshold
            )

            self.logger.info(
                f"Filtered to {len(filtered_comments)} comments above threshold",
                original=len(review_result.comments),
                filtered=len(filtered_comments),
                threshold=self.settings.severity_threshold
            )

            # Step 7: Post comments on PR
            comments_posted = 0

            # Post PR-level summary if enabled
            if self.settings.include_pr_summary and review_result.summary:
                summary_text = f"{self.settings.review_comment_prefix}\n\n{review_result.summary}"
                self.platform.post_review_comment(pr_id, summary_text)
                comments_posted += 1
                self.logger.info("Posted PR summary comment")

            # Post inline comments if enabled
            if self.settings.include_line_comments:
                for comment in filtered_comments:
                    if comment.line:
                        comment_text = self._format_comment(comment)
                        try:
                            self.platform.post_review_comment(
                                pr_id,
                                comment_text,
                                file_path=comment.file,
                                line_number=comment.line
                            )
                            comments_posted += 1
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to post inline comment: {e}",
                                file=comment.file,
                                line=comment.line
                            )
                            # Fall back to general comment
                            general_text = f"{comment_text}\n\n**File:** {comment.file}:{comment.line}"
                            self.platform.post_review_comment(pr_id, general_text)
                            comments_posted += 1

            # Post file-level comments if enabled
            if self.settings.include_file_comments:
                file_comments = [c for c in filtered_comments if not c.line]
                for comment in file_comments:
                    comment_text = self._format_comment(comment)
                    self.platform.post_review_comment(pr_id, comment_text)
                    comments_posted += 1

            self.logger.info(
                f"Review completed successfully",
                pr_id=pr_id,
                comments_posted=comments_posted,
                issues_found=len(filtered_comments)
            )

            return {
                'status': 'success',
                'pr_id': pr_id,
                'pr_title': pr.title,
                'files_reviewed': len(filtered_diffs),
                'issues_found': len(filtered_comments),
                'comments_posted': comments_posted,
                'tokens_used': review_result.tokens_used
            }

        except Exception as e:
            self.logger.error(f"Review failed: {e}", pr_id=pr_id, error=str(e))
            raise CodeReviewAgentError(f"Review failed: {e}")

    def _reconstruct_diff(self, file_diffs) -> str:
        """Reconstruct unified diff from file diffs."""
        diff_parts = []

        for file_diff in file_diffs:
            diff_parts.append(f"diff --git a/{file_diff.file_path} b/{file_diff.file_path}")

            if file_diff.is_new_file:
                diff_parts.append(f"--- /dev/null")
                diff_parts.append(f"+++ b/{file_diff.file_path}")
            else:
                diff_parts.append(f"--- a/{file_diff.file_path}")
                diff_parts.append(f"+++ b/{file_diff.file_path}")

            for hunk in file_diff.hunks:
                diff_parts.append(
                    f"@@ -{hunk.source_start},{hunk.source_length} "
                    f"+{hunk.target_start},{hunk.target_length} @@"
                )

                # Add context and changes
                all_lines = []
                for line_no, content in hunk.removed_lines:
                    all_lines.append((line_no, f"-{content}"))
                for line_no, content in hunk.added_lines:
                    all_lines.append((line_no, f"+{content}"))
                for line_no, content in hunk.context_lines:
                    all_lines.append((line_no, f" {content}"))

                # Sort by line number
                all_lines.sort(key=lambda x: x[0])

                for _, line in all_lines:
                    diff_parts.append(line.rstrip())

        return "\n".join(diff_parts)

    def _format_comment(self, comment) -> str:
        """Format a review comment for posting."""
        severity_emoji = {
            'critical': '🔴',
            'major': '🟠',
            'minor': '🟡',
            'suggestion': '🔵'
        }

        emoji = severity_emoji.get(comment.severity.value, '⚪')

        parts = [
            f"{self.settings.review_comment_prefix} {emoji} **{comment.severity.value.upper()}** - {comment.category.value}",
            "",
            comment.message
        ]

        if comment.suggestion:
            parts.extend(["", "**Suggested fix:**", "```", comment.suggestion, "```"])

        return "\n".join(parts)


@click.command()
@click.option('--pr-id', '--pr-number', required=True, help='Pull request ID or number')
@click.option('--config', help='Path to config file (optional)')
def main(pr_id: str, config: Optional[str]):
    """
    Run code review agent on a pull request.
    """
    try:
        if config:
            import os
            os.environ['ENV_FILE'] = config

        agent = ReviewAgent()
        result = agent.run(pr_id)

        click.echo(f"✅ Review completed successfully!")
        click.echo(f"PR: {result.get('pr_title', pr_id)}")
        click.echo(f"Files reviewed: {result.get('files_reviewed', 0)}")
        click.echo(f"Issues found: {result.get('issues_found', 0)}")
        click.echo(f"Comments posted: {result.get('comments_posted', 0)}")

    except Exception as e:
        click.echo(f"❌ Review failed: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()
