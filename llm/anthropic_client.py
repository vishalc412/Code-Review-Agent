"""Anthropic API client for code review."""

from typing import List
from anthropic import Anthropic
from .base import BaseLLMClient, ReviewResult
from .prompts import (
    build_review_prompt,
    build_fix_prompt,
    build_analysis_prompt,
    parse_review_response,
    parse_fix_response,
    parse_analysis_response
)
from parsers.comment_parser import ReviewComment, CommentParser
from core.logger import get_logger
from core.exceptions import LLMError
from core.utils import retry_with_backoff


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
        prompt = build_review_prompt(diff, context, focus, depth)

        try:
            self.logger.info("Sending code review request to Claude", model=self.model)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            self.logger.info("Received response from Claude", tokens=tokens_used)

            comments, summary = parse_review_response(response_text, self.comment_parser)

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
        prompt = build_fix_prompt(file_content, comment, file_path)

        try:
            self.logger.info("Generating fix with Claude", file=file_path)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            fixed_content = parse_fix_response(response.content[0].text)
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
        prompt = build_analysis_prompt(comments, file_contents)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            return parse_analysis_response(response.content[0].text)

        except Exception as e:
            self.logger.error(f"Failed to analyze comments with Claude: {e}")
            raise LLMError(f"Claude API error: {e}")
