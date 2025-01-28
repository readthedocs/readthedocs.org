"""Notifications related to OAuth."""

import textwrap

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import ERROR
from readthedocs.notifications.messages import Message, registry

MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS = "oauth:webhook:no-permissions"
MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT = "oauth:webhook:no-account"
MESSAGE_OAUTH_WEBHOOK_INVALID = "oauth:webhook:invalid"
MESSAGE_OAUTH_BUILD_STATUS_FAILURE = "oauth:status:send-failed"
MESSAGE_OAUTH_DEPLOY_KEY_ATTACHED_FAILED = "oauth:deploy-key:attached-failed"

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
            Failed to add deploy key to {{provider_name}} project, ensure you have the correct permissions and try importing again.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
]
registry.add(messages)
