# Code Review Agents

AI-powered code review automation for Azure DevOps, GitLab, and GitHub using LLM capabilities (Azure OpenAI or Anthropic Claude).

## Overview

This project provides two Python-based agents that automate code review processes:

1. **Review Agent (Agent 1)**: Analyzes PR code changes and posts review comments directly on the PR
2. **Fix Agent (Agent 2)**: Reads review comments, implements fixes, and creates a new PR with corrections

## Features

- ✅ **Multi-Platform Support**: Works with GitHub, GitLab, and Azure DevOps
- ✅ **Multiple LLM Providers**: Supports Anthropic Claude and Azure OpenAI
- ✅ **Comprehensive Reviews**: Analyzes code for bugs, security, performance, style, and best practices
- ✅ **Automated Fixes**: Generates and applies fixes based on review comments
- ✅ **Configurable**: Extensive configuration options for review depth, focus areas, and severity thresholds
- ✅ **CI/CD Integration**: Ready-to-use workflows for GitHub Actions, GitLab CI, and Azure Pipelines
- ✅ **Docker Support**: Containerized deployment option

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- API tokens for your platform (GitHub, GitLab, or Azure DevOps)
- API key for your LLM provider (Anthropic or Azure OpenAI)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/code-review-agents.git
cd code-review-agents
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Validate configuration:
```bash
python scripts/validate_config.py
```

### Usage

#### Review Agent

Run code review on a pull request:

```bash
# GitHub
python -m agents.review_agent --pr-number 123

# GitLab
python -m agents.review_agent --pr-id 456

# Azure DevOps
python -m agents.review_agent --pr-id 789
```

#### Fix Agent

Generate and apply fixes for review comments:

```bash
# GitHub
python -m agents.fix_agent --pr-number 123

# GitLab
python -m agents.fix_agent --pr-id 456

# Azure DevOps
python -m agents.fix_agent --pr-id 789
```

## Configuration

Configuration is managed through environment variables. See `.env.example` for all available options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `PLATFORM` | Platform to use (github, gitlab, azure_devops) | github |
| `LLM_PROVIDER` | LLM provider (anthropic, azure_ai) | anthropic |
| `REVIEW_DEPTH` | Review depth (quick, standard, deep) | standard |
| `REVIEW_FOCUS` | Focus area (all, security, performance, style, bugs) | all |
| `SEVERITY_THRESHOLD` | Minimum severity to report (critical, major, minor, suggestion) | minor |
| `FIX_AUTO_CREATE_PR` | Auto-create PR with fixes | true |

See [docs/SETUP.md](docs/SETUP.md) for detailed configuration guide.

## CI/CD Integration

### GitHub Actions

The workflow file is already included at `.github/workflows/code-review.yml`.

Configure secrets: `ANTHROPIC_API_KEY` or `AZURE_AI_API_KEY`

### GitLab CI

The pipeline file is already included at `.gitlab-ci.yml`.

Configure variables: `GITLAB_ACCESS_TOKEN`, `ANTHROPIC_API_KEY` or `AZURE_AI_API_KEY`

### Azure Pipelines

The pipeline file is already included at `azure-pipelines.yml`.

Configure variable group `code-review-agents` with required variables.

## Docker

Build and run with Docker:

```bash
# Build
docker build -t code-review-agents .

# Run review agent
docker run --env-file .env code-review-agents python -m agents.review_agent --pr-id 123

# Or use docker-compose
export PR_ID=123
docker-compose run review-agent
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                        │
│            (Azure/GitLab/GitHub Actions)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Code Review Agent (Agent 1)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. Fetch PR Changes                             │   │
│  │  2. Parse Code Diff                              │   │
│  │  3. Send to LLM for Analysis                     │   │
│  │  4. Post Review Comments on PR                   │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Code Review Fix Agent (Agent 2)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. Fetch PR Review Comments                     │   │
│  │  2. Analyze Comments with LLM                    │   │
│  │  3. Generate Code Fixes                          │   │
│  │  4. Create New Branch                            │   │
│  │  5. Apply Fixes and Commit                       │   │
│  │  6. Create New PR                                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Documentation

- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [API Documentation](docs/API.md) - API reference
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Testing

Run tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=. --cov-report=html tests/
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## Acknowledgments

- Anthropic Claude API
- Azure OpenAI Service
- GitHub, GitLab, and Azure DevOps APIs
