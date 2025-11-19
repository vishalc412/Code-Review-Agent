"""Pytest configuration and fixtures."""

import pytest
from core.config import Settings


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        platform="github",
        github_token="test_token",
        github_repository="test/repo",
        llm_provider="anthropic",
        anthropic_api_key="test_key",
        anthropic_model="claude-sonnet-4-5-20250929",
        review_enabled=True,
        fix_enabled=True,
        log_level="DEBUG"
    )


@pytest.fixture
def sample_diff():
    """Sample diff for testing."""
    return """diff --git a/test.py b/test.py
index 0000000..1234567 100644
--- a/test.py
+++ b/test.py
@@ -1,0 +1,2 @@
+def hello():
+    return "world"
"""


@pytest.fixture
def sample_pr_data():
    """Sample PR data for testing."""
    return {
        'id': '1',
        'number': 1,
        'title': 'Test PR',
        'description': 'Test description',
        'author': 'testuser',
        'source_branch': 'feature',
        'target_branch': 'main',
        'state': 'open',
        'web_url': 'https://example.com/pr/1',
        'created_at': '2025-01-01T00:00:00Z',
        'updated_at': '2025-01-01T00:00:00Z'
    }
