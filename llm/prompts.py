"""Shared prompt templates for LLM providers."""

import json
from typing import List
from parsers.comment_parser import ReviewComment


def build_review_prompt(
    diff: str,
    context: dict,
    focus: str,
    depth: str
) -> str:
    """Build prompt for code review."""
    focus_instructions = {
        "security": "Focus primarily on security vulnerabilities, authentication/authorization issues, input validation, and potential exploits.",
        "performance": "Focus primarily on performance issues, inefficient algorithms, resource usage, and optimization opportunities.",
        "style": "Focus primarily on code style, formatting, naming conventions, and code organization.",
        "bugs": "Focus primarily on potential bugs, logic errors, edge cases, and correctness issues.",
        "all": "Review all aspects including security, performance, style, bugs, and best practices."
    }.get(focus, "Review all aspects including security, performance, style, bugs, and best practices.")

    depth_instructions = {
        "quick": "Perform a quick scan focusing on obvious issues and critical problems.",
        "standard": "Perform a standard review covering common issues and important improvements.",
        "deep": "Perform a thorough deep analysis including subtle issues, edge cases, and architectural concerns."
    }.get(depth, "Perform a standard review covering common issues and important improvements.")

    return f"""You are an expert code reviewer. Analyze the following code changes and provide a comprehensive review.

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


def build_fix_prompt(
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


def build_analysis_prompt(
    comments: List[ReviewComment],
    file_contents: dict[str, str]
) -> str:
    """Build prompt for analyzing comments."""
    comments_text = "\n".join([
        f"- [{c.severity}] {c.file}:{c.line} - {c.message}"
        for c in comments
    ])

    return f"""Analyze the following code review comments and categorize them as fixable or not fixable.

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


def parse_review_response(response_text: str, comment_parser) -> tuple[List[ReviewComment], str]:
    """Parse LLM review response."""
    try:
        # Extract JSON array
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1

        if json_start == -1 or json_end == 0:
            return [], response_text

        json_text = response_text[json_start:json_end]
        summary = response_text[json_end:].strip()

        # Parse JSON
        comments_data = json.loads(json_text)
        comments = comment_parser.parse_json_comments(comments_data)

        return comments, summary

    except json.JSONDecodeError:
        return [], response_text


def parse_fix_response(response_text: str) -> str:
    """Parse LLM fix response."""
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


def parse_analysis_response(response_text: str) -> dict:
    """Parse LLM analysis response."""
    try:
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            return {"fixable": [], "manual": [], "reasoning": {}}

        json_text = response_text[json_start:json_end]
        return json.loads(json_text)

    except json.JSONDecodeError:
        return {"fixable": [], "manual": [], "reasoning": {}}
