"""Azure OpenAI client for code review."""

from typing import List
from openai import AzureOpenAI
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


class AzureAIClient(BaseLLMClient):
    """Azure OpenAI API client."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview"
    ):
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment = deployment_name
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
        """Review code using Azure OpenAI."""
        prompt = build_review_prompt(diff, context, focus, depth)

        try:
            self.logger.info("Sending code review request to Azure OpenAI", deployment=self.deployment)

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer with deep knowledge of software engineering best practices."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=8000
            )

            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            self.logger.info("Received response from Azure OpenAI", tokens=tokens_used)

            comments, summary = parse_review_response(response_text, self.comment_parser)

            return ReviewResult(
                comments=comments,
                summary=summary,
                raw_response=response_text,
                tokens_used=tokens_used
            )

        except Exception as e:
            self.logger.error(f"Failed to review code with Azure OpenAI: {e}")
            raise LLMError(f"Azure OpenAI API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def generate_fix(
        self,
        file_content: str,
        comment: ReviewComment,
        file_path: str
    ) -> str:
        """Generate code fix using Azure OpenAI."""
        prompt = build_fix_prompt(file_content, comment, file_path)

        try:
            self.logger.info("Generating fix with Azure OpenAI", file=file_path)

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert programmer who fixes code issues while maintaining style and functionality."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            fixed_content = parse_fix_response(response.choices[0].message.content)
            self.logger.info("Generated fix successfully", file=file_path)
            return fixed_content

        except Exception as e:
            self.logger.error(f"Failed to generate fix with Azure OpenAI: {e}")
            raise LLMError(f"Azure OpenAI API error: {e}")

    @retry_with_backoff(max_retries=3, exceptions=(Exception,))
    def analyze_comments(
        self,
        comments: List[ReviewComment],
        file_contents: dict[str, str]
    ) -> dict:
        """Analyze comments to determine which are fixable."""
        prompt = build_analysis_prompt(comments, file_contents)

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing code review comments and determining fixability."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            return parse_analysis_response(response.choices[0].message.content)

        except Exception as e:
            self.logger.error(f"Failed to analyze comments with Azure OpenAI: {e}")
            raise LLMError(f"Claude API error: {e}")
