"""Anthropic API client for code review."""

import json
from typing import List
from anthropic import Anthropic
from .base import BaseLLMClient, ReviewResult
from parsers.comment_parser import ReviewComment, CommentParser
from core.logger import get_logger
from core.exceptions import LLMError
from core.utils import retry_with_backoff

logger = get_logger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.comment_parser = CommentParser()
        self.logger = get_logger(__name__)

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def review_code(
        self,
        diff: str,
        context: dict,
        focus: str = "all",
        depth: str = "standard"
    ) -> ReviewResult:
        """Review code using Claude."""
        prompt = self._build_review_prompt(diff, context, focus, depth)

        try:
            self.logger.info("Sending code review request to Claude", model=self.model)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            self.logger.info(
                "Received response from Claude",
                tokens=tokens_used,
                model=self.model
            )

            # Parse the response
            comments, summary = self._parse_review_response(response_text)

            return ReviewResult(
                comments=comments,
                summary=summary,
                raw_response=response_text,
                tokens_used=tokens_used
            )

        except Exception as e:
            self.logger.error(f"Failed to review code with Claude: {e}")
            raise LLMError(f"Claude API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def generate_fix(
        self,
        file_content: str,
        comment: ReviewComment,
        file_path: str
    ) -> str:
        """Generate code fix using Claude."""
        prompt = self._build_fix_prompt(file_content, comment, file_path)

        try:
            self.logger.info(
                "Generating fix with Claude",
                file=file_path,
                line=comment.line
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            fixed_content = self._parse_fix_response(response.content[0].text)

            self.logger.info("Generated fix successfully", file=file_path)
            return fixed_content

        except Exception as e:
            self.logger.error(f"Failed to generate fix with Claude: {e}")
            raise LLMError(f"Claude API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def analyze_comments(
        self,
        comments: List[ReviewComment],
        file_contents: dict[str, str]
    ) -> dict:
        """Analyze comments to determine which are fixable."""
        prompt = self._build_analysis_prompt(comments, file_contents)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = self._parse_analysis_response(response.content[0].text)
            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze comments with Claude: {e}")
            raise LLMError(f"Claude API error: {e}")

    def _build_review_prompt(
        self,
        diff: str,
        context: dict,
        focus: str,
        depth: str
    ) -> str:
        """Build prompt for code review."""
        focus_instructions = self._get_focus_instructions(focus)
        depth_instructions = self._get_depth_instructions(depth)

        prompt = f"""You are an expert code reviewer. Analyze the following code changes and provide a comprehensive review.

**Pull Request Context:**
- Title: {context.get('title', 'N/A')}
- Description: {context.get('description', 'N/A')}
- Author: {context.get('author', 'N/A')}
- Files Changed: {context.get('files_changed', 0)}

**Review Focus:** {focus}
{focus_instructions}

**Review Depth:** {depth}
{depth_instructions}

**Code Changes:**
```diff
{diff}
```

**Review Instructions:**
1. Identify potential bugs, security vulnerabilities, and performance issues
2. Check code quality, readability, and adherence to best practices
3. Suggest improvements for better maintainability
4. Verify proper error handling and edge cases
5. Check for adequate documentation and comments

**Output Format:**
Provide your review as a JSON array followed by a summary. Format:

```json
[
  {{
    "file": "path/to/file.py",
    "line": 42,
    "severity": "major",
    "category": "bug",
    "message": "Detailed description of the issue",
    "suggestion": "Specific code suggestion or fix (optional)"
  }}
]
```

After the JSON array, provide a brief summary of the overall review.

Severity levels: critical, major, minor, suggestion
Categories: bug, security, performance, style, documentation, testing, other

Respond ONLY with the JSON array and summary, no other text."""

        return prompt

    def _build_fix_prompt(
        self,
        file_content: str,
        comment: ReviewComment,
        file_path: str
    ) -> str:
        """Build prompt for generating fix."""
        prompt = f"""You are an expert programmer. Fix the following issue in the code.

**File:** {file_path}
**Line:** {comment.line}
**Issue:** {comment.message}
**Category:** {comment.category}
**Severity:** {comment.severity}

**Current Code:**
```
{file_content}
```

**Instructions:**
1. Fix the identified issue
2. Maintain code style and formatting
3. Preserve all existing functionality
4. Do not make unrelated changes
5. Ensure the fix is complete and correct

**Output Format:**
Provide ONLY the complete fixed file content, with no explanations or markdown formatting.
Start your response with the first line of the file and end with the last line."""

        if comment.suggestion:
            prompt += f"\n\n**Suggested Fix:** {comment.suggestion}"

        return prompt

    def _build_analysis_prompt(
        self,
        comments: List[ReviewComment],
        file_contents: dict[str, str]
    ) -> str:
        """Build prompt for analyzing comments."""
        comments_text = "\n".join([
            f"- [{c.severity}] {c.file}:{c.line} - {c.message}"
            for c in comments
        ])

        prompt = f"""Analyze the following code review comments and categorize them as fixable or not fixable.

**Review Comments:**
{comments_text}

**Instructions:**
Determine which comments can be automatically fixed and which require human intervention.

**Output Format:**
```json
{{
  "fixable": [list of comment indices that can be auto-fixed],
  "manual": [list of comment indices that need manual review],
  "reasoning": {{
    "index": "brief explanation"
  }}
}}
```

Respond ONLY with the JSON object."""

        return prompt

    def _parse_review_response(self, response_text: str) -> tuple[List[ReviewComment], str]:
        """Parse Claude's review response."""
        try:
            # Extract JSON array
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                self.logger.warning("No JSON found in response, returning empty review")
                return [], response_text

            json_text = response_text[json_start:json_end]
            summary = response_text[json_end:].strip()

            # Parse JSON
            comments_data = json.loads(json_text)
            comments = self.comment_parser.parse_json_comments(comments_data)

            return comments, summary

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return [], response_text

    def _parse_fix_response(self, response_text: str) -> str:
        """Parse Claude's fix response."""
        # Remove markdown code blocks if present
        if "```" in response_text:
            lines = response_text.split('\n')
            code_lines = []
            in_code = False

            for line in lines:
                if line.strip().startswith('```'):
                    in_code = not in_code
                    continue
                if in_code:
                    code_lines.append(line)

            if code_lines:
                return '\n'.join(code_lines)

        return response_text.strip()

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse Claude's analysis response."""
        try:
            # Extract JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                return {"fixable": [], "manual": [], "reasoning": {}}

            json_text = response_text[json_start:json_end]
            return json.loads(json_text)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse analysis response: {e}")
            return {"fixable": [], "manual": [], "reasoning": {}}

    def _get_focus_instructions(self, focus: str) -> str:
        """Get focus-specific instructions."""
        focus_map = {
            "security": "Focus primarily on security vulnerabilities, authentication/authorization issues, input validation, and potential exploits.",
            "performance": "Focus primarily on performance issues, inefficient algorithms, resource usage, and optimization opportunities.",
            "style": "Focus primarily on code style, formatting, naming conventions, and code organization.",
            "bugs": "Focus primarily on potential bugs, logic errors, edge cases, and correctness issues.",
            "all": "Review all aspects including security, performance, style, bugs, and best practices."
        }
        return focus_map.get(focus, focus_map["all"])

    def _get_depth_instructions(self, depth: str) -> str:
        """Get depth-specific instructions."""
        depth_map = {
            "quick": "Perform a quick scan focusing on obvious issues and critical problems.",
            "standard": "Perform a standard review covering common issues and important improvements.",
            "deep": "Perform a thorough deep analysis including subtle issues, edge cases, and architectural concerns."
        }
        return depth_map.get(depth, depth_map["standard"])
