# -*- coding: utf-8 -*-
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from messages_extends.constants import ERROR_PERSISTENT

from readthedocs.notifications import SiteNotification


class AttachWebhookNotification(SiteNotification):

    # Fail reasons
    NO_PERMISSIONS = 'no_permissions'
    NO_ACCOUNTS = 'no_accounts'

    context_object_name = 'provider'
    success_message = _('Webhook successfully added.')
    failure_message = {
        NO_PERMISSIONS: _(
            'Could not add webhook for {{ project.name }}. Make sure <a href="{{ url_docs_webhook }}">you have the correct {{ provider.name }} permissions</a>.',  # noqa
        ),
        NO_ACCOUNTS: _(
            'Could not add webhook for {{ project.name }}. Please <a href="{{ url_connect_account }}">connect your {{ provider.name }} account</a>.',  # noqa
        ),
    }

    def get_context_data(self):
        context = super().get_context_data()
        project = self.extra_context.get('project')
        context.update({
            'url_connect_account': reverse(
                'projects_integrations',
                args=[project.slug],
            ),
            'url_docs_webhook': 'http://docs.readthedocs.io/en/latest/webhooks.html',  # noqa
        })
        return context


class InvalidProjectWebhookNotification(SiteNotification):

    context_object_name = 'project'
    failure_level = ERROR_PERSISTENT
    failure_message = _(
        "The project {{ project.name }} doesn't have a valid webhook set up, "
        "commits won't trigger new builds for this project. "
        "See <a href='{{ url_integrations }}'>the project integrations</a> for more information.",
    )  # noqa

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'url_integrations': reverse(
                'projects_integrations',
                args=[self.object.slug],
            ),
        })
        return context


class GitBuildStatusFailureNotification(SiteNotification):

    context_object_name = 'project'
    failure_level = ERROR_PERSISTENT
    failure_message = _(
        'Could not send {{ provider_name }} build status report for {{ project.name }}. '
        'Make sure you have the correct {{ provider_name }} repository permissions</a> and '
        'your <a href="{{ url_connect_account }}">{{ provider_name }} account</a> '
        'is connected to ReadtheDocs.'
    )  # noqa

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'url_connect_account': reverse('socialaccount_connections'),
        })
        return context
