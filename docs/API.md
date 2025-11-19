# API Documentation

API reference for Code Review Agents.

## Agents

### ReviewAgent

Code review agent that analyzes PRs and posts comments.

```python
from agents.review_agent import ReviewAgent
from core.config import get_settings

agent = ReviewAgent(settings=get_settings())
result = agent.run(pr_id="123")
```

#### Methods

##### `run(pr_id: str) -> dict`

Run code review on a pull request.

**Parameters**:
- `pr_id` (str): Pull request ID or number

**Returns**:
- dict with keys:
  - `status`: "success" or "error"
  - `pr_id`: PR identifier
  - `pr_title`: PR title
  - `files_reviewed`: Number of files reviewed
  - `issues_found`: Number of issues found
  - `comments_posted`: Number of comments posted
  - `tokens_used`: LLM tokens consumed

**Example**:
```python
result = agent.run(pr_id="123")
print(f"Posted {result['comments_posted']} comments")
```

### FixAgent

Fix agent that generates fixes and creates PRs.

```python
from agents.fix_agent import FixAgent
from core.config import get_settings

agent = FixAgent(settings=get_settings())
result = agent.run(pr_id="123")
```

#### Methods

##### `run(pr_id: str, output_dir: Optional[str] = None) -> dict`

Generate fixes for review comments and create a new PR.

**Parameters**:
- `pr_id` (str): Original pull request ID or number
- `output_dir` (Optional[str]): Output directory for cloned repo

**Returns**:
- dict with keys:
  - `status`: "success" or "error"
  - `original_pr_id`: Original PR ID
  - `fix_pr_id`: Fix PR ID (if created)
  - `fix_pr_url`: Fix PR URL (if created)
  - `fixes_applied`: Number of fixes applied
  - `files_modified`: Number of files modified

**Example**:
```python
result = agent.run(pr_id="123")
if 'fix_pr_url' in result:
    print(f"Fix PR created: {result['fix_pr_url']}")
```

## Platform Integrations

### BasePlatform

Abstract base class for platform integrations.

#### Methods

##### `get_pull_request(pr_id: str) -> PullRequest`

Get PR details.

##### `get_pull_request_diff(pr_id: str) -> str`

Get unified diff for PR.

##### `get_pull_request_files(pr_id: str) -> List[dict]`

Get list of files changed in PR.

##### `post_review_comment(pr_id: str, body: str, file_path: Optional[str] = None, line_number: Optional[int] = None) -> PlatformComment`

Post a review comment on PR.

##### `get_review_comments(pr_id: str) -> List[PlatformComment]`

Get all review comments for a PR.

##### `create_pull_request(title: str, description: str, source_branch: str, target_branch: str) -> PullRequest`

Create a new PR.

##### `get_file_content(file_path: str, ref: Optional[str] = None) -> str`

Get file content from repository.

##### `update_file(file_path: str, content: str, branch: str, commit_message: str) -> None`

Update a file in the repository.

### GitHubPlatform

GitHub-specific implementation.

```python
from platforms.github import GitHubPlatform

platform = GitHubPlatform(
    token="ghp_xxx",
    repository="owner/repo"
)
```

### GitLabPlatform

GitLab-specific implementation.

```python
from platforms.gitlab import GitLabPlatform

platform = GitLabPlatform(
    token="glpat_xxx",
    project_id="12345678",
    url="https://gitlab.com"
)
```

### AzureDevOpsPlatform

Azure DevOps-specific implementation.

```python
from platforms.azure_devops import AzureDevOpsPlatform

platform = AzureDevOpsPlatform(
    pat="xxx",
    organization="myorg",
    project="myproject",
    repository_id="repo_id"
)
```

## LLM Providers

### BaseLLMClient

Abstract base class for LLM providers.

#### Methods

##### `review_code(diff: str, context: dict, focus: str = "all", depth: str = "standard") -> ReviewResult`

Review code changes using LLM.

**Parameters**:
- `diff` (str): Unified diff of code changes
- `context` (dict): Additional context (PR title, description, etc.)
- `focus` (str): Focus area (all, security, performance, style, bugs)
- `depth` (str): Review depth (quick, standard, deep)

**Returns**:
- `ReviewResult` with:
  - `comments`: List of ReviewComment
  - `summary`: Overall review summary
  - `raw_response`: Raw LLM response
  - `tokens_used`: Tokens consumed

##### `generate_fix(file_content: str, comment: ReviewComment, file_path: str) -> str`

Generate code fix based on review comment.

**Parameters**:
- `file_content` (str): Current file content
- `comment` (ReviewComment): Review comment to address
- `file_path` (str): Path to the file

**Returns**:
- Fixed code content

##### `analyze_comments(comments: List[ReviewComment], file_contents: dict[str, str]) -> dict`

Analyze review comments and determine fixability.

### AnthropicClient

Anthropic Claude API implementation.

```python
from llm.anthropic_client import AnthropicClient

client = AnthropicClient(
    api_key="sk-ant-xxx",
    model="claude-sonnet-4-5-20250929"
)
```

### AzureAIClient

Azure OpenAI implementation.

```python
from llm.azure_ai_client import AzureAIClient

client = AzureAIClient(
    api_key="xxx",
    endpoint="https://xxx.openai.azure.com/",
    deployment_name="gpt-4",
    api_version="2024-02-15-preview"
)
```

## Parsers

### DiffParser

Parse git diffs.

```python
from parsers.diff_parser import DiffParser

parser = DiffParser()
file_diffs = parser.parse(diff_text)
```

#### Methods

##### `parse(diff_text: str) -> List[FileDiff]`

Parse unified diff text.

##### `get_file_changes_summary(file_diffs: List[FileDiff]) -> dict`

Get summary statistics.

##### `extract_context(file_diff: FileDiff, line_number: int, context_lines: int = 3) -> str`

Extract context around a line.

### CommentParser

Parse review comments.

```python
from parsers.comment_parser import CommentParser

parser = CommentParser(comment_prefix="[AI Review]")
comments = parser.parse_json_comments(json_data)
```

#### Methods

##### `parse_json_comments(json_data: List[dict]) -> List[ReviewComment]`

Parse comments from JSON format.

##### `parse_platform_comments(platform_comments: List[dict], platform: str) -> List[ReviewComment]`

Parse comments from platform format.

##### `filter_by_severity(comments: List[ReviewComment], min_severity: Severity) -> List[ReviewComment]`

Filter comments by minimum severity.

##### `group_by_file(comments: List[ReviewComment]) -> dict[str, List[ReviewComment]]`

Group comments by file.

## Configuration

### Settings

Configuration management.

```python
from core.config import get_settings, Settings

settings = get_settings()
print(settings.platform)
```

#### Properties

- `platform`: Platform enum (GITHUB, GITLAB, AZURE_DEVOPS)
- `llm_provider`: LLM provider enum (ANTHROPIC, AZURE_AI)
- `review_enabled`: Boolean
- `review_depth`: ReviewDepth enum
- `review_focus`: ReviewFocus enum
- `fix_enabled`: Boolean
- `fix_auto_create_pr`: Boolean
- And many more...

#### Methods

##### `validate_platform_config() -> None`

Validate platform configuration.

##### `validate_llm_config() -> None`

Validate LLM provider configuration.

##### `validate_all() -> None`

Validate all configuration.

## Utilities

### Retry with Backoff

Decorator for retrying functions.

```python
from core.utils import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def api_call():
    # Your API call here
    pass
```

### Other Utilities

```python
from core.utils import (
    truncate_text,
    parse_repository_name,
    should_exclude_file,
    estimate_tokens,
    format_file_path,
    sanitize_branch_name,
    calculate_diff_stats
)
```

## Exceptions

### Custom Exceptions

```python
from core.exceptions import (
    CodeReviewAgentError,  # Base exception
    PlatformError,         # Platform API errors
    LLMError,              # LLM provider errors
    ConfigurationError,    # Configuration errors
    ValidationError,       # Validation errors
    GitOperationError,     # Git operation errors
    NetworkError,          # Network errors
    AuthenticationError,   # Authentication errors
    RateLimitError         # Rate limit errors
)
```

## Examples

### Custom Review Workflow

```python
from agents.review_agent import ReviewAgent
from core.config import Settings

# Custom settings
settings = Settings(
    platform="github",
    github_token="xxx",
    github_repository="owner/repo",
    llm_provider="anthropic",
    anthropic_api_key="xxx",
    review_depth="deep",
    review_focus="security",
    severity_threshold="major"
)

# Run review
agent = ReviewAgent(settings)
result = agent.run(pr_id="123")
```

### Custom Fix Workflow

```python
from agents.fix_agent import FixAgent
from core.config import Settings

settings = Settings(
    # ... configuration
    fix_auto_create_pr=True,
    fix_severity_filter="critical",
    fix_validate_syntax=True
)

agent = FixAgent(settings)
result = agent.run(pr_id="123")
```

### Direct LLM Usage

```python
from llm.anthropic_client import AnthropicClient

client = AnthropicClient(api_key="xxx")

diff = """diff --git a/file.py b/file.py
+def hello():
+    return "world"
"""

result = client.review_code(
    diff=diff,
    context={'title': 'Add hello function'},
    focus='all',
    depth='standard'
)

for comment in result.comments:
    print(f"{comment.severity}: {comment.message}")
```

### Direct Platform Usage

```python
from platforms.github import GitHubPlatform

platform = GitHubPlatform(token="xxx", repository="owner/repo")

# Get PR
pr = platform.get_pull_request("123")
print(pr.title)

# Post comment
platform.post_review_comment(
    pr_id="123",
    body="This looks good!",
    file_path="src/main.py",
    line_number=42
)
```
