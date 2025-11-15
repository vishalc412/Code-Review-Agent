#!/usr/bin/env python3
"""Setup webhooks for code review agents."""

import sys
import click
from core.config import get_settings, Platform


@click.command()
@click.option('--webhook-url', required=True, help='Webhook endpoint URL')
@click.option('--env-file', default='.env', help='Path to .env file')
def main(webhook_url: str, env_file: str):
    """Setup webhooks for the configured platform."""
    try:
        click.echo("🔧 Setting up webhooks...")

        # Load settings
        import os
        os.environ['ENV_FILE'] = env_file

        settings = get_settings()

        if settings.platform == Platform.GITHUB:
            setup_github_webhook(settings, webhook_url)
        elif settings.platform == Platform.GITLAB:
            setup_gitlab_webhook(settings, webhook_url)
        elif settings.platform == Platform.AZURE_DEVOPS:
            setup_azure_devops_webhook(settings, webhook_url)
        else:
            click.echo(f"❌ Unsupported platform: {settings.platform}", err=True)
            sys.exit(1)

        click.echo("\n✅ Webhook setup completed!")

    except Exception as e:
        click.echo(f"\n❌ Webhook setup failed: {e}", err=True)
        sys.exit(1)


def setup_github_webhook(settings, webhook_url: str):
    """Setup GitHub webhook."""
    from github import Github

    click.echo(f"\n📡 Setting up GitHub webhook...")

    client = Github(settings.github_token)
    owner, repo_name = settings.github_repository.split('/')
    repo = client.get_repo(f"{owner}/{repo_name}")

    # Create webhook
    config = {
        "url": webhook_url,
        "content_type": "json",
        "secret": settings.webhook_secret or "",
    }

    events = ["pull_request", "pull_request_review_comment"]

    hook = repo.create_hook(
        name="web",
        config=config,
        events=events,
        active=True
    )

    click.echo(f"✓ Webhook created: {hook.url}")
    click.echo(f"  ID: {hook.id}")
    click.echo(f"  Events: {', '.join(events)}")


def setup_gitlab_webhook(settings, webhook_url: str):
    """Setup GitLab webhook."""
    import gitlab

    click.echo(f"\n📡 Setting up GitLab webhook...")

    client = gitlab.Gitlab(settings.gitlab_url, private_token=settings.gitlab_token)
    client.auth()
    project = client.projects.get(settings.gitlab_project_id)

    # Create webhook
    hook = project.hooks.create({
        'url': webhook_url,
        'merge_requests_events': True,
        'note_events': True,
        'token': settings.webhook_secret or "",
    })

    click.echo(f"✓ Webhook created: {hook.url}")
    click.echo(f"  ID: {hook.id}")
    click.echo(f"  Events: merge_requests, notes")


def setup_azure_devops_webhook(settings, webhook_url: str):
    """Setup Azure DevOps webhook (service hook)."""
    click.echo(f"\n📡 Setting up Azure DevOps service hook...")

    click.echo("\nℹ️ Azure DevOps service hooks must be configured manually:")
    click.echo(f"1. Go to: https://dev.azure.com/{settings.azure_devops_organization}/_settings/serviceHooks")
    click.echo(f"2. Create a new subscription")
    click.echo(f"3. Select 'Web Hooks' as the service")
    click.echo(f"4. Select these events:")
    click.echo(f"   - Pull request created")
    click.echo(f"   - Pull request updated")
    click.echo(f"   - Pull request commented on")
    click.echo(f"5. Use this URL: {webhook_url}")
    click.echo(f"6. Add your webhook secret if configured")


if __name__ == '__main__':
    main()
