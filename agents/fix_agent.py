"""Code Review Fix Agent - Agent 2."""

import click
from typing import Optional, List
from datetime import datetime
from git import Repo, GitCommandError
from .base_agent import BaseAgent
from parsers.comment_parser import ReviewComment, CommentParser
from core.utils import sanitize_branch_name
from core.exceptions import CodeReviewAgentError, GitOperationError
from core.config import get_settings
import tempfile
import os
import shutil


class FixAgent(BaseAgent):
    """
    Agent that reads review comments, generates fixes, and creates a new PR.
    """

    def __init__(self, settings=None):
        super().__init__(settings)
        self.comment_parser = CommentParser(self.settings.review_comment_prefix)

    def run(self, pr_id: str, output_dir: Optional[str] = None) -> dict:
        """
        Generate fixes for review comments and create a new PR.

        Args:
            pr_id: Original pull request ID or number
            output_dir: Optional output directory for cloned repo

        Returns:
            Dictionary with fix results
        """
        try:
            self.logger.info(f"Starting fix generation for PR {pr_id}", pr_id=pr_id)

            # Step 1: Get PR details
            pr = self.platform.get_pull_request(pr_id)
            self.logger.info(
                f"Retrieved PR: {pr.title}",
                pr_id=pr_id,
                title=pr.title
            )

            # Step 2: Get review comments
            platform_comments = self.platform.get_review_comments(pr_id)
            self.logger.info(f"Retrieved {len(platform_comments)} comments")

            # Parse comments
            comments = self.comment_parser.parse_platform_comments(
                platform_comments,
                platform=self.settings.platform.value
            )

            # Filter by severity
            comments = self.comment_parser.filter_by_severity(
                comments,
                self.settings.fix_severity_filter
            )

            self.logger.info(
                f"Filtered to {len(comments)} actionable comments",
                total_comments=len(platform_comments),
                actionable=len(comments)
            )

            if not comments:
                self.logger.info("No actionable comments found")
                return {
                    'status': 'success',
                    'pr_id': pr_id,
                    'message': 'No actionable comments to fix'
                }

            # Step 3: Group comments by file
            comments_by_file = self.comment_parser.group_by_file(comments)

            # Limit number of files
            if len(comments_by_file) > self.settings.fix_max_files:
                self.logger.warning(
                    f"Too many files ({len(comments_by_file)}), limiting to {self.settings.fix_max_files}"
                )
                comments_by_file = dict(list(comments_by_file.items())[:self.settings.fix_max_files])

            # Step 4: Get file contents
            file_contents = {}
            for file_path in comments_by_file.keys():
                try:
                    content = self.platform.get_file_content(
                        file_path,
                        ref=pr.source_branch
                    )
                    file_contents[file_path] = content
                except Exception as e:
                    self.logger.warning(f"Failed to get content for {file_path}: {e}")

            # Step 5: Analyze comments for fixability
            all_comments = [c for comments_list in comments_by_file.values() for c in comments_list]
            analysis = self.llm_client.analyze_comments(all_comments, file_contents)

            fixable_indices = set(analysis.get('fixable', []))
            self.logger.info(
                f"{len(fixable_indices)} comments are auto-fixable",
                fixable=len(fixable_indices),
                total=len(all_comments)
            )

            # Step 6: Generate fixes
            fixes_applied = []
            for idx, comment in enumerate(all_comments):
                if idx in fixable_indices and comment.file in file_contents:
                    try:
                        fixed_content = self.llm_client.generate_fix(
                            file_contents[comment.file],
                            comment,
                            comment.file
                        )

                        # Validate syntax if enabled
                        if self.settings.fix_validate_syntax:
                            if self._validate_syntax(comment.file, fixed_content):
                                file_contents[comment.file] = fixed_content
                                fixes_applied.append({
                                    'file': comment.file,
                                    'line': comment.line,
                                    'comment': comment.message,
                                    'severity': comment.severity.value
                                })
                                self.logger.info(f"Applied fix to {comment.file}:{comment.line}")
                            else:
                                self.logger.warning(
                                    f"Syntax validation failed for {comment.file}, skipping fix"
                                )
                        else:
                            file_contents[comment.file] = fixed_content
                            fixes_applied.append({
                                'file': comment.file,
                                'line': comment.line,
                                'comment': comment.message,
                                'severity': comment.severity.value
                            })

                    except Exception as e:
                        self.logger.warning(f"Failed to generate fix for {comment.file}:{comment.line}: {e}")

            if not fixes_applied:
                self.logger.info("No fixes could be applied")
                return {
                    'status': 'success',
                    'pr_id': pr_id,
                    'message': 'No fixes could be applied automatically'
                }

            self.logger.info(f"Generated {len(fixes_applied)} fixes")

            # Step 7: Create fix branch and PR if auto-create is enabled
            if self.settings.fix_auto_create_pr:
                fix_pr = self._create_fix_pr(
                    pr,
                    file_contents,
                    fixes_applied
                )

                return {
                    'status': 'success',
                    'original_pr_id': pr_id,
                    'fix_pr_id': fix_pr.number,
                    'fix_pr_url': fix_pr.web_url,
                    'fixes_applied': len(fixes_applied),
                    'files_modified': len(file_contents)
                }
            else:
                # Just return the fixes without creating PR
                return {
                    'status': 'success',
                    'pr_id': pr_id,
                    'fixes_applied': len(fixes_applied),
                    'files_modified': len(file_contents),
                    'fixes': fixes_applied
                }

        except Exception as e:
            self.logger.error(f"Fix generation failed: {e}", pr_id=pr_id, error=str(e))
            raise CodeReviewAgentError(f"Fix generation failed: {e}")

    def _create_fix_pr(self, original_pr, file_contents: dict, fixes_applied: List[dict]):
        """Create a new PR with fixes."""
        # Generate branch name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"{self.settings.fix_branch_prefix}{original_pr.number}-{timestamp}"
        branch_name = sanitize_branch_name(branch_name)

        self.logger.info(f"Creating fix branch: {branch_name}")

        try:
            # Create branch
            if hasattr(self.platform, 'create_branch'):
                self.platform.create_branch(branch_name, original_pr.source_branch)
            else:
                raise NotImplementedError("Platform does not support branch creation")

            # Update files
            for file_path, content in file_contents.items():
                commit_message = f"Fix issues in {file_path}"
                self.platform.update_file(
                    file_path,
                    content,
                    branch_name,
                    commit_message
                )
                self.logger.info(f"Updated {file_path} on {branch_name}")

            # Create PR description
            pr_description = self._generate_fix_pr_description(original_pr, fixes_applied)

            # Create PR
            fix_pr = self.platform.create_pull_request(
                title=f"{self.settings.fix_pr_title_prefix} Fixes for PR #{original_pr.number}",
                description=pr_description,
                source_branch=branch_name,
                target_branch=original_pr.source_branch
            )

            self.logger.info(
                f"Created fix PR: {fix_pr.web_url}",
                fix_pr_id=fix_pr.number,
                url=fix_pr.web_url
            )

            return fix_pr

        except Exception as e:
            self.logger.error(f"Failed to create fix PR: {e}")
            raise GitOperationError(f"Failed to create fix PR: {e}")

    def _generate_fix_pr_description(self, original_pr, fixes_applied: List[dict]) -> str:
        """Generate description for fix PR."""
        severity_counts = {}
        for fix in fixes_applied:
            severity = fix['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        description_parts = [
            "# 🤖 AI-Generated Fixes for Review Comments",
            "",
            f"This PR addresses the code review comments from PR #{original_pr.number}.",
            "",
            "## Summary of Changes",
            ""
        ]

        # Group fixes by file
        fixes_by_file = {}
        for fix in fixes_applied:
            file = fix['file']
            if file not in fixes_by_file:
                fixes_by_file[file] = []
            fixes_by_file[file].append(fix)

        for file, file_fixes in fixes_by_file.items():
            description_parts.append(f"- **{file}**: {len(file_fixes)} issue(s) fixed")

        description_parts.extend([
            "",
            "## Issues Addressed",
            ""
        ])

        # Add severity breakdown
        for severity in ['critical', 'major', 'minor', 'suggestion']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                emoji = {'critical': '🔴', 'major': '🟠', 'minor': '🟡', 'suggestion': '🔵'}
                description_parts.append(
                    f"- {emoji.get(severity, '⚪')} **{severity.upper()}**: {count} issue(s)"
                )

        description_parts.extend([
            "",
            "## Detailed Changes",
            ""
        ])

        for fix in fixes_applied:
            description_parts.append(
                f"- [{fix['severity'].upper()}] {fix['file']}:{fix['line']} - {fix['comment'][:100]}"
            )

        description_parts.extend([
            "",
            "## Related PR",
            f"Fixes issues from: #{original_pr.number}",
            "",
            "---",
            "*This PR was automatically generated by the Code Review Fix Agent*"
        ])

        return "\n".join(description_parts)

    def _validate_syntax(self, file_path: str, content: str) -> bool:
        """
        Validate syntax of fixed code.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            True if syntax is valid
        """
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.py':
                import ast
                ast.parse(content)
                return True
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                # Basic check - just ensure it's not empty and has balanced braces
                if not content.strip():
                    return False
                return content.count('{') == content.count('}')
            else:
                # For other files, just check if not empty
                return bool(content.strip())

        except SyntaxError:
            return False
        except Exception as e:
            self.logger.warning(f"Validation error for {file_path}: {e}")
            return False


@click.command()
@click.option('--pr-id', '--pr-number', required=True, help='Pull request ID or number')
@click.option('--config', help='Path to config file (optional)')
@click.option('--output-dir', help='Output directory for cloned repo (optional)')
def main(pr_id: str, config: Optional[str], output_dir: Optional[str]):
    """
    Run fix agent to generate fixes for review comments.
    """
    try:
        if config:
            import os
            os.environ['ENV_FILE'] = config

        agent = FixAgent()
        result = agent.run(pr_id, output_dir)

        click.echo(f"✅ Fix generation completed successfully!")

        if 'fix_pr_id' in result:
            click.echo(f"Fix PR created: #{result['fix_pr_id']}")
            click.echo(f"URL: {result['fix_pr_url']}")
            click.echo(f"Fixes applied: {result['fixes_applied']}")
            click.echo(f"Files modified: {result['files_modified']}")
        else:
            click.echo(f"Fixes analyzed: {result.get('fixes_applied', 0)}")
            click.echo(result.get('message', ''))

    except Exception as e:
        click.echo(f"❌ Fix generation failed: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()
