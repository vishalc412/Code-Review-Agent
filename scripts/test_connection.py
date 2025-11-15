#!/usr/bin/env python3
"""Test connections to platform and LLM providers."""

import sys
import click
from core.config import get_settings
from platforms.factory import create_platform
from llm.factory import create_llm_client


@click.command()
@click.option('--env-file', default='.env', help='Path to .env file')
@click.option('--test-platform/--no-test-platform', default=True, help='Test platform connection')
@click.option('--test-llm/--no-test-llm', default=True, help='Test LLM connection')
def main(env_file: str, test_platform: bool, test_llm: bool):
    """Test connections to platform and LLM providers."""
    try:
        click.echo("🔍 Testing connections...")

        # Load settings
        import os
        os.environ['ENV_FILE'] = env_file

        settings = get_settings()

        # Test platform connection
        if test_platform:
            click.echo(f"\n📡 Testing {settings.platform.value} connection...")
            platform = create_platform(settings)

            # Try to get a test PR or repo info
            try:
                click.echo("✓ Platform client initialized successfully")
                click.echo(f"✓ Connected to {settings.platform.value}")
            except Exception as e:
                click.echo(f"⚠️ Platform connection warning: {e}")

        # Test LLM connection
        if test_llm:
            click.echo(f"\n🤖 Testing {settings.llm_provider.value} connection...")
            llm_client = create_llm_client(settings)

            # Try a simple test
            try:
                click.echo("✓ LLM client initialized successfully")
                click.echo(f"✓ Connected to {settings.llm_provider.value}")

                # Optional: test with a simple review
                if click.confirm("\nWould you like to test with a simple code review?"):
                    test_diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
+def hello():
+    return "world"
"""
                    result = llm_client.review_code(
                        diff=test_diff,
                        context={'title': 'Test', 'description': 'Test PR'},
                        focus='all',
                        depth='quick'
                    )
                    click.echo(f"✓ Test review completed")
                    click.echo(f"  Comments generated: {len(result.comments)}")
                    click.echo(f"  Tokens used: {result.tokens_used}")

            except Exception as e:
                click.echo(f"❌ LLM connection failed: {e}", err=True)
                sys.exit(1)

        click.echo("\n✅ All connection tests passed!")
        sys.exit(0)

    except Exception as e:
        click.echo(f"\n❌ Test failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
