# Setup Guide

This guide provides detailed instructions for setting up the Code Review Agents.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Platform Configuration](#platform-configuration)
4. [LLM Provider Configuration](#llm-provider-configuration)
5. [Agent Configuration](#agent-configuration)
6. [Testing the Setup](#testing-the-setup)
7. [CI/CD Integration](#cicd-integration)

## Prerequisites

### Required

- Python 3.9 or higher
- Git
- pip (Python package manager)

### Platform Requirements

Choose one:

- **GitHub**: Personal Access Token with `repo` and `pull_request` permissions
- **GitLab**: Personal Access Token with `api`, `read_repository`, `write_repository` permissions
- **Azure DevOps**: Personal Access Token with Code (Read, Write) and Pull Request (Read, Write) permissions

### LLM Provider Requirements

Choose one:

- **Anthropic**: API key from https://console.anthropic.com/
- **Azure OpenAI**: API key and endpoint from Azure Portal

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/code-review-agents.git
cd code-review-agents
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Package

```bash
pip install -e .
```

## Platform Configuration

### GitHub Setup

1. Create a Personal Access Token:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `write:discussion`
   - Generate and copy the token

2. Configure environment variables:

```bash
PLATFORM=github
GITHUB_TOKEN=your_github_token_here
GITHUB_REPOSITORY=owner/repo
```

### GitLab Setup

1. Create a Personal Access Token:
   - Go to GitLab Settings → Access Tokens
   - Add a token with scopes: `api`, `read_repository`, `write_repository`
   - Generate and copy the token

2. Configure environment variables:

```bash
PLATFORM=gitlab
GITLAB_TOKEN=your_gitlab_token_here
GITLAB_URL=https://gitlab.com
GITLAB_PROJECT_ID=12345678
```

### Azure DevOps Setup

1. Create a Personal Access Token:
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create token with scopes: Code (Read, Write), Pull Request (Read, Write)
   - Generate and copy the token

2. Configure environment variables:

```bash
PLATFORM=azure_devops
AZURE_DEVOPS_PAT=your_pat_here
AZURE_DEVOPS_ORGANIZATION=your_org
AZURE_DEVOPS_PROJECT=your_project
AZURE_DEVOPS_REPOSITORY_ID=your_repo_id
```

## LLM Provider Configuration

### Anthropic Setup

1. Get API key from https://console.anthropic.com/

2. Configure environment variables:

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

### Azure OpenAI Setup

1. Create Azure OpenAI resource in Azure Portal

2. Deploy a model (GPT-4 recommended)

3. Get endpoint and API key from Azure Portal

4. Configure environment variables:

```bash
LLM_PROVIDER=azure_ai
AZURE_AI_API_KEY=your_api_key_here
AZURE_AI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_AI_DEPLOYMENT_NAME=gpt-4
AZURE_AI_API_VERSION=2024-02-15-preview
```

## Agent Configuration

### Review Agent Settings

```bash
# Enable/disable review
REVIEW_ENABLED=true

# Review depth: quick, standard, deep
REVIEW_DEPTH=standard

# Focus area: all, security, performance, style, bugs
REVIEW_FOCUS=all

# Maximum files to review
MAX_FILES_TO_REVIEW=50

# File patterns to exclude (comma-separated)
EXCLUDE_PATTERNS=*.md,*.txt,package-lock.json,*.min.js

# Comment settings
INCLUDE_LINE_COMMENTS=true
INCLUDE_FILE_COMMENTS=true
INCLUDE_PR_SUMMARY=true

# Severity threshold: critical, major, minor, suggestion
SEVERITY_THRESHOLD=minor

# Comment prefix
REVIEW_COMMENT_PREFIX=[AI Review]
```

### Fix Agent Settings

```bash
# Enable/disable fix agent
FIX_ENABLED=true

# Auto-create PR with fixes
FIX_AUTO_CREATE_PR=true

# Branch name prefix for fix PRs
FIX_BRANCH_PREFIX=fix/ai-review-

# Only fix issues >= this severity
FIX_SEVERITY_FILTER=major

# Maximum files to fix
FIX_MAX_FILES=20

# Validate syntax before committing
FIX_VALIDATE_SYNTAX=true

# Run tests before creating PR (requires test setup)
FIX_RUN_TESTS=false

# PR title prefix
FIX_PR_TITLE_PREFIX=[AI Fix]
```

### General Settings

```bash
# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Maximum retries for API calls
MAX_RETRIES=3

# Timeout for operations (seconds)
TIMEOUT_SECONDS=300
```

## Testing the Setup

### 1. Validate Configuration

```bash
python scripts/validate_config.py
```

Expected output:
```
🔍 Validating configuration...

✓ Platform: github
✓ Platform configuration valid

✓ LLM Provider: anthropic
✓ LLM configuration valid

✅ Configuration is valid!
```

### 2. Test Connections

```bash
python scripts/test_connection.py
```

This will test connectivity to your platform and LLM provider.

### 3. Test Review Agent

Create a test PR in your repository, then:

```bash
python -m agents.review_agent --pr-number <PR_NUMBER>
```

### 4. Test Fix Agent

After review agent has posted comments:

```bash
python -m agents.fix_agent --pr-number <PR_NUMBER>
```

## CI/CD Integration

### GitHub Actions

1. Add secrets to your repository:
   - Go to Settings → Secrets and variables → Actions
   - Add `ANTHROPIC_API_KEY` or `AZURE_AI_API_KEY`

2. The workflow file is already included at `.github/workflows/code-review.yml`

3. The workflow will run automatically on PRs

### GitLab CI

1. Add CI/CD variables:
   - Go to Settings → CI/CD → Variables
   - Add `GITLAB_ACCESS_TOKEN`
   - Add `ANTHROPIC_API_KEY` or `AZURE_AI_API_KEY`

2. The pipeline file is already included at `.gitlab-ci.yml`

3. The pipeline will run automatically on merge requests

### Azure Pipelines

1. Create variable group `code-review-agents`:
   - Go to Pipelines → Library → Variable groups
   - Create group with these variables:
     - `AZURE_DEVOPS_PAT`
     - `ANTHROPIC_API_KEY` or `AZURE_AI_API_KEY`

2. The pipeline file is already included at `azure-pipelines.yml`

3. Import the pipeline in Azure DevOps

## Webhook Setup (Optional)

For real-time processing, set up webhooks:

```bash
python scripts/setup_webhooks.py --webhook-url https://your-webhook-endpoint.com
```

This will configure webhooks on your platform to trigger agents automatically.

## Troubleshooting

### Configuration Issues

If validation fails:

1. Check that all required environment variables are set
2. Verify API tokens are valid and have correct permissions
3. Ensure platform-specific IDs (project ID, repository ID) are correct

### Connection Issues

If connection tests fail:

1. Verify network connectivity
2. Check API endpoint URLs
3. Confirm API tokens haven't expired
4. Check firewall/proxy settings

### Agent Execution Issues

If agents fail to run:

1. Check logs for detailed error messages
2. Verify PR exists and is accessible
3. Ensure sufficient API quota/limits
4. Check file permissions

For more help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Next Steps

- Review [API Documentation](API.md) for programmatic usage
- Check [Examples](EXAMPLES.md) for common scenarios
- Customize prompt templates in `templates/`
- Adjust configuration for your workflow

## Support

For issues:
- Check existing GitHub issues
- Create a new issue with detailed information
- Review documentation and examples
