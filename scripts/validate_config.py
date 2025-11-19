#!/usr/bin/env python3
"""Validate configuration for code review agents."""

import sys
import click
from core.config import get_settings, Settings
from core.exceptions import ConfigurationError


@click.command()
@click.option('--env-file', default='.env', help='Path to .env file')
def main(env_file: str):
    """Validate configuration for code review agents."""
    try:
        click.echo("🔍 Validating configuration...")

        # Load settings
        import os
        os.environ['ENV_FILE'] = env_file

        settings = get_settings()

        # Validate platform config
        click.echo(f"\n✓ Platform: {settings.platform.value}")
        settings.validate_platform_config()
        click.echo("✓ Platform configuration valid")

        # Validate LLM config
        click.echo(f"\n✓ LLM Provider: {settings.llm_provider.value}")
        settings.validate_llm_config()
        click.echo("✓ LLM configuration valid")

        # Display settings
        click.echo("\n" + "=" * 50)
        click.echo("Configuration Summary:")
        click.echo("=" * 50)
        click.echo(f"Platform: {settings.platform.value}")
        click.echo(f"LLM Provider: {settings.llm_provider.value}")
        click.echo(f"Review Enabled: {settings.review_enabled}")
        click.echo(f"Fix Enabled: {settings.fix_enabled}")
        click.echo(f"Review Depth: {settings.review_depth.value}")
        click.echo(f"Review Focus: {settings.review_focus.value}")
        click.echo(f"Max Files to Review: {settings.max_files_to_review}")
        click.echo(f"Fix Auto Create PR: {settings.fix_auto_create_pr}")
        click.echo(f"Log Level: {settings.log_level}")
        click.echo("=" * 50)

        click.echo("\n✅ Configuration is valid!")
        sys.exit(0)

    except ConfigurationError as e:
        click.echo(f"\n❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
