"""Notifications related to OAuth."""

import textwrap

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import ERROR
from readthedocs.notifications.constants import INFO
from readthedocs.notifications.constants import WARNING
from readthedocs.notifications.messages import Message
from readthedocs.notifications.messages import registry


MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS = "oauth:webhook:no-permissions"
MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT = "oauth:webhook:no-account"
MESSAGE_OAUTH_WEBHOOK_INVALID = "oauth:webhook:invalid"
MESSAGE_OAUTH_BUILD_STATUS_FAILURE = "oauth:status:send-failed"
MESSAGE_OAUTH_DEPLOY_KEY_ATTACHED_FAILED = "oauth:deploy-key:attached-failed"
MESSAGE_OAUTH_WEBHOOK_NOT_REMOVED = "oauth:migration:webhook-not-removed"
MESSAGE_OAUTH_DEPLOY_KEY_NOT_REMOVED = "oauth:migration:ssh-key-not-removed"
MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP = "oauth:migration:projects-to-migrate-to-github-app"

messages = [
    Message(
        id=MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT,
        header=_("Unable to attach webhook to this project"),
        body=_(
            textwrap.dedent(
                """
            Could not add webhook for "{{instance.name}}".
            Please <a href="{{url_connect_account}}">connect your {{provider_name}} account</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS,
        header=_("Unable to attach webhook to this project"),
        body=_(
            textwrap.dedent(
                """
            Could not add webhook for "{{instance.name}}".
            Make sure <a href="{{url_docs_webhook}}">you have the correct {{provider_name}} permissions</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MESSAGE_OAUTH_WEBHOOK_INVALID,
        header=_("The project doesn't have a valid webhook set up"),
        body=_(
            textwrap.dedent(
                """
        The project "{{instance.name}}" doesn't have a valid webhook set up,
        commits won't trigger new builds for this project.
        See <a href='{{url_integrations}}'>the project integrations</a> for more information.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MESSAGE_OAUTH_BUILD_STATUS_FAILURE,
        header=_("{{provider_name}} build status report failed"),
        body=_(
            textwrap.dedent(
                """
        Could not send {{provider_name}} build status report for "{{instance.name}}".
        Make sure you have the correct {{provider_name}} repository permissions</a> and
        your <a href="{{url_connect_account}}">{{provider_name}} account</a>
        is connected to Read the Docs.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MESSAGE_OAUTH_DEPLOY_KEY_ATTACHED_FAILED,
        header=_("Failed to add deploy key to project"),
        body=_(
            textwrap.dedent(
                """
                Failed to add deploy key to {{provider_name}} project,
                ensure you have the correct permissions and try
                <a href="https://docs.readthedocs.com/platform/stable/guides/creating-project-private-repository.html#configuring-your-repository">
                  adding the key manually
                </a>.
                """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MESSAGE_OAUTH_WEBHOOK_NOT_REMOVED,
        header=_("Failed to remove webhook"),
        body=_(
            textwrap.dedent(
                """
                Failed to remove webhook from the <a href="https://github.com/{{ repo_full_name }}">{{ repo_full_name }}</a> repository, please remove it manually
                from the <a href="https://github.com/{{ repo_full_name }}/settings/hooks">repository settings</a> (search for a webhook containing "{{ project_slug }}" in the URL).
                """
            ).strip(),
        ),
        type=WARNING,
    ),
    Message(
        id=MESSAGE_OAUTH_DEPLOY_KEY_NOT_REMOVED,
        header=_("Failed to remove deploy key"),
        body=_(
            textwrap.dedent(
                """
                Failed to remove deploy key from the <a href="https://github.com/{{ repo_full_name }}">{{ repo_full_name }}</a> repository, please remove it manually
                from the <a href="https://github.com/{{ repo_full_name }}/settings/keys">repository settings</a> (search for a deploy key containing "{{ project_slug }}" in the title).
                """
            )
        ),
        type=WARNING,
    ),
    Message(
        id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
        header=_("You have projects that need to be migrated to the new GitHub App"),
        body=_(
            textwrap.dedent(
                """
                Migrate your projects automatically using the <a href="{% url "migrate_to_github_app" %}">migration page</a>.
                """
            ).strip(),
        ),
        type=INFO,
    ),
]
registry.add(messages)
