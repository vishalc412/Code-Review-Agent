# Troubleshooting Guide

Common issues and solutions for Code Review Agents.

## Table of Contents

1. [Configuration Issues](#configuration-issues)
2. [Platform Connection Issues](#platform-connection-issues)
3. [LLM Provider Issues](#llm-provider-issues)
4. [Agent Execution Issues](#agent-execution-issues)
5. [CI/CD Issues](#cicd-issues)
6. [Performance Issues](#performance-issues)

## Configuration Issues

### Error: "Configuration validation failed"

**Symptoms**: `validate_config.py` fails with configuration errors

**Solutions**:

1. Check `.env` file exists and is readable:
   ```bash
   ls -la .env
   ```

2. Verify all required variables are set:
   ```bash
   cat .env
   ```

3. Check for typos in variable names

4. Ensure no extra spaces around `=` signs

### Error: "Invalid platform: xyz"

**Cause**: Platform value is not one of: `github`, `gitlab`, `azure_devops`

**Solution**:
```bash
# In .env file
PLATFORM=github  # or gitlab, or azure_devops
```

### Error: "Invalid LLM provider: xyz"

**Cause**: LLM provider value is not one of: `anthropic`, `azure_ai`

**Solution**:
```bash
# In .env file
LLM_PROVIDER=anthropic  # or azure_ai
```

## Platform Connection Issues

### GitHub Issues

#### Error: "Bad credentials"

**Cause**: Invalid or expired GitHub token

**Solutions**:

1. Regenerate token:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` and `write:discussion` scopes

2. Update `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_new_token_here
   ```

#### Error: "Resource not accessible by integration"

**Cause**: Token doesn't have required permissions

**Solution**: Ensure token has these scopes:
- `repo` (full control)
- `write:discussion`

#### Error: "Repository not found"

**Cause**: Incorrect repository name or lack of access

**Solutions**:

1. Verify repository format:
   ```bash
   GITHUB_REPOSITORY=owner/repo  # Not: github.com/owner/repo
   ```

2. Check you have access to the repository

3. For private repos, ensure token has access

### GitLab Issues

#### Error: "401 Unauthorized"

**Solutions**:

1. Verify token is valid:
   ```bash
   curl --header "PRIVATE-TOKEN: your_token" https://gitlab.com/api/v4/user
   ```

2. Check token scopes include: `api`, `read_repository`, `write_repository`

#### Error: "Project not found"

**Cause**: Incorrect project ID

**Solution**:

1. Get correct project ID:
   - Go to project page on GitLab
   - Look for "Project ID" under project name
   - Or use API:
     ```bash
     curl --header "PRIVATE-TOKEN: your_token" \
          "https://gitlab.com/api/v4/projects?search=project_name"
     ```

2. Update `.env`:
   ```bash
   GITLAB_PROJECT_ID=12345678
   ```

### Azure DevOps Issues

#### Error: "TF401019: The Git repository with name or identifier XYZ does not exist"

**Solutions**:

1. Get correct repository ID:
   ```bash
   # Use Azure DevOps UI
   # Project Settings → Repositories → Select repo → Copy ID from URL
   ```

2. Or use repository name instead of ID

#### Error: "VS403403: The request has been blocked because it's from an untrusted source"

**Cause**: Security policy blocking API access

**Solutions**:

1. Enable third-party application access:
   - Organization Settings → Policies → Third-party application access via OAuth
   - Set to "On"

2. Or use OAuth authentication instead of PAT

## LLM Provider Issues

### Anthropic Issues

#### Error: "Invalid API key"

**Solutions**:

1. Verify API key from https://console.anthropic.com/

2. Ensure no extra spaces:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxx  # No spaces before or after
   ```

#### Error: "Rate limit exceeded"

**Solutions**:

1. Wait and retry (exponential backoff is automatic)

2. Reduce review frequency

3. Upgrade Anthropic plan for higher limits

#### Error: "Model not found"

**Cause**: Invalid model name

**Solution**:
```bash
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # Verify model name
```

### Azure OpenAI Issues

#### Error: "The API deployment for this resource does not exist"

**Solutions**:

1. Verify deployment name in Azure Portal:
   - Azure OpenAI resource → Deployments

2. Update `.env`:
   ```bash
   AZURE_AI_DEPLOYMENT_NAME=your_actual_deployment_name
   ```

#### Error: "Invalid endpoint"

**Solutions**:

1. Get correct endpoint from Azure Portal

2. Format should be:
   ```bash
   AZURE_AI_ENDPOINT=https://your-resource.openai.azure.com/
   ```

3. Ensure trailing slash is present

## Agent Execution Issues

### Review Agent Issues

#### Issue: No comments posted

**Possible Causes**:

1. **No issues found**: LLM didn't find any problems
   - Solution: Check logs, review might be genuinely clean

2. **Severity threshold too high**:
   ```bash
   SEVERITY_THRESHOLD=suggestion  # Lower threshold
   ```

3. **All files excluded**:
   - Check `EXCLUDE_PATTERNS`
   - Verify file extensions aren't excluded

4. **Platform API error**:
   - Check logs for specific errors
   - Verify permissions

#### Issue: Too many comments posted

**Solutions**:

1. Increase severity threshold:
   ```bash
   SEVERITY_THRESHOLD=major  # Only critical and major issues
   ```

2. Reduce review depth:
   ```bash
   REVIEW_DEPTH=quick  # Faster, fewer comments
   ```

3. Add more exclusion patterns:
   ```bash
   EXCLUDE_PATTERNS=*.md,*.txt,test/**,*.json
   ```

### Fix Agent Issues

#### Issue: No fixes applied

**Possible Causes**:

1. **No actionable comments**: Comments are questions or approvals
   - Solution: Review comments must be specific issues

2. **Severity filter too high**:
   ```bash
   FIX_SEVERITY_FILTER=minor  # Lower threshold
   ```

3. **Syntax validation failed**:
   - Disable validation temporarily:
     ```bash
     FIX_VALIDATE_SYNTAX=false
     ```
   - Check generated fixes manually

#### Issue: Syntax errors in fixed code

**Solutions**:

1. Enable syntax validation:
   ```bash
   FIX_VALIDATE_SYNTAX=true
   ```

2. Use more specific review comments

3. Lower LLM temperature (requires code change)

#### Issue: Fix PR creation failed

**Solutions**:

1. Check branch creation permissions

2. Verify target branch exists

3. Check for branch name conflicts:
   ```bash
   FIX_BRANCH_PREFIX=fix/ai-review-v2-  # Use different prefix
   ```

## CI/CD Issues

### GitHub Actions

#### Issue: Workflow doesn't trigger

**Solutions**:

1. Verify workflow file is in `.github/workflows/`

2. Check trigger configuration in workflow file

3. Ensure Actions are enabled:
   - Repository Settings → Actions → General
   - Allow all actions

#### Issue: Secret not found

**Solutions**:

1. Add secret to repository:
   - Settings → Secrets and variables → Actions
   - Add required secrets

2. Verify secret name matches workflow:
   ```yaml
   env:
     ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
   ```

### GitLab CI

#### Issue: Pipeline fails with "permission denied"

**Solutions**:

1. Verify CI/CD variables are set:
   - Settings → CI/CD → Variables

2. Check runner permissions

3. Ensure token has sufficient scopes

### Azure Pipelines

#### Issue: Variable group not found

**Solutions**:

1. Create variable group:
   - Pipelines → Library → Variable groups

2. Link to pipeline:
   - Edit pipeline → Variables → Variable groups

## Performance Issues

### Issue: Review takes too long

**Solutions**:

1. Reduce files to review:
   ```bash
   MAX_FILES_TO_REVIEW=20  # Lower limit
   ```

2. Use quick review depth:
   ```bash
   REVIEW_DEPTH=quick
   ```

3. Add more exclusion patterns

4. Focus on specific areas:
   ```bash
   REVIEW_FOCUS=security  # Only security issues
   ```

### Issue: High API costs

**Solutions**:

1. Limit review frequency (only on important branches)

2. Use cheaper model:
   ```bash
   # For Azure OpenAI
   AZURE_AI_DEPLOYMENT_NAME=gpt-3.5-turbo
   ```

3. Reduce max files:
   ```bash
   MAX_FILES_TO_REVIEW=10
   ```

4. Use quick depth for initial review

## Getting Help

If issues persist:

1. Enable debug logging:
   ```bash
   LOG_LEVEL=DEBUG
   ```

2. Check logs for detailed error messages

3. Search existing GitHub issues

4. Create new issue with:
   - Error message
   - Configuration (redact secrets)
   - Steps to reproduce
   - Log output

5. Review documentation:
   - [Setup Guide](SETUP.md)
   - [Examples](EXAMPLES.md)
   - [API Documentation](API.md)
