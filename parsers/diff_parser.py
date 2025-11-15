"""Parser for git diff output."""

from dataclasses import dataclass
from typing import List, Optional
from unidiff import PatchSet
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HunkDiff:
    """Represents a hunk in a diff."""
    source_start: int
    source_length: int
    target_start: int
    target_length: int
    added_lines: List[tuple[int, str]]  # (line_number, content)
    removed_lines: List[tuple[int, str]]  # (line_number, content)
    context_lines: List[tuple[int, str]]  # (line_number, content)


@dataclass
class FileDiff:
    """Represents a file diff."""
    source_file: str
    target_file: str
    is_new_file: bool
    is_deleted_file: bool
    is_binary: bool
    hunks: List[HunkDiff]
    additions: int
    deletions: int

    @property
    def file_path(self) -> str:
        """Get the file path (prefer target, fallback to source)."""
        if self.target_file and self.target_file != '/dev/null':
            # Remove 'b/' prefix if present
            return self.target_file.lstrip('b/')
        if self.source_file and self.source_file != '/dev/null':
            # Remove 'a/' prefix if present
            return self.source_file.lstrip('a/')
        return ""


class DiffParser:
    """Parser for git diff output."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def parse(self, diff_text: str) -> List[FileDiff]:
        """
        Parse unified diff text into structured file diffs.

        Args:
            diff_text: Unified diff text

        Returns:
            List of FileDiff objects
        """
        try:
            patch_set = PatchSet(diff_text)
            file_diffs = []

            for patched_file in patch_set:
                file_diff = self._parse_file(patched_file)
                file_diffs.append(file_diff)

            self.logger.info(
                f"Parsed {len(file_diffs)} files from diff",
                files=len(file_diffs)
            )
            return file_diffs

        except Exception as e:
            self.logger.error(f"Failed to parse diff: {e}", error=str(e))
            raise

    def _parse_file(self, patched_file) -> FileDiff:
        """Parse a single file from patch set."""
        hunks = []
        additions = 0
        deletions = 0

        for hunk in patched_file:
            hunk_diff = self._parse_hunk(hunk)
            hunks.append(hunk_diff)
            additions += len(hunk_diff.added_lines)
            deletions += len(hunk_diff.removed_lines)

        return FileDiff(
            source_file=patched_file.source_file,
            target_file=patched_file.target_file,
            is_new_file=patched_file.is_added_file,
            is_deleted_file=patched_file.is_removed_file,
            is_binary=patched_file.is_binary_file,
            hunks=hunks,
            additions=additions,
            deletions=deletions
        )

    def _parse_hunk(self, hunk) -> HunkDiff:
        """Parse a single hunk."""
        added_lines = []
        removed_lines = []
        context_lines = []

        for line in hunk:
            if line.is_added:
                added_lines.append((line.target_line_no, line.value))
            elif line.is_removed:
                removed_lines.append((line.source_line_no, line.value))
            else:  # context line
                if line.target_line_no:
                    context_lines.append((line.target_line_no, line.value))

        return HunkDiff(
            source_start=hunk.source_start,
            source_length=hunk.source_length,
            target_start=hunk.target_start,
            target_length=hunk.target_length,
            added_lines=added_lines,
            removed_lines=removed_lines,
            context_lines=context_lines
        )

    def get_file_changes_summary(self, file_diffs: List[FileDiff]) -> dict:
        """
        Get a summary of file changes.

        Args:
            file_diffs: List of file diffs

        Returns:
            Dictionary with summary statistics
        """
        total_additions = sum(f.additions for f in file_diffs)
        total_deletions = sum(f.deletions for f in file_diffs)
        new_files = sum(1 for f in file_diffs if f.is_new_file)
        deleted_files = sum(1 for f in file_diffs if f.is_deleted_file)
        modified_files = len(file_diffs) - new_files - deleted_files
        binary_files = sum(1 for f in file_diffs if f.is_binary)

        return {
            'total_files': len(file_diffs),
            'additions': total_additions,
            'deletions': total_deletions,
            'new_files': new_files,
            'deleted_files': deleted_files,
            'modified_files': modified_files,
            'binary_files': binary_files,
        }

    def extract_context(
        self,
        file_diff: FileDiff,
        line_number: int,
        context_lines: int = 3
    ) -> str:
        """
        Extract context around a specific line number.

        Args:
            file_diff: File diff object
            line_number: Target line number
            context_lines: Number of context lines before and after

        Returns:
            Context string
        """
        lines = []

        for hunk in file_diff.hunks:
            # Check if line is in this hunk
            if hunk.target_start <= line_number <= hunk.target_start + hunk.target_length:
                # Collect all lines in the hunk with their numbers
                all_lines = []
                all_lines.extend((num, f" {content}") for num, content in hunk.context_lines)
                all_lines.extend((num, f"+{content}") for num, content in hunk.added_lines)
                all_lines.sort(key=lambda x: x[0])

                # Find the target line and extract context
                for i, (num, content) in enumerate(all_lines):
                    if num == line_number:
                        start = max(0, i - context_lines)
                        end = min(len(all_lines), i + context_lines + 1)
                        lines = [f"{n}: {c}" for n, c in all_lines[start:end]]
                        break

        return "\n".join(lines)
