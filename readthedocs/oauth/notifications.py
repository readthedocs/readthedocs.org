# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from readthedocs.notifications import SiteNotification


class AttachWebhookNotification(SiteNotification):

    # Fail reasons
    NO_PERMISSIONS = 'no_permissions'
    NO_ACCOUNTS = 'no_accounts'

    context_object_name = 'provider'
    success_message = _('Webhook successfully added.')
    failure_message = {
        NO_PERMISSIONS: _('Could not add webhook for {{ project.name }}. Make sure <a href="{{ url_docs_webhook }}">you have the correct {{ provider.name }} permissions</a>.'),  # noqa
        NO_ACCOUNTS: _('Could not add webhook for {{ project.name }}. Please <a href="{{ url_connect_account }}">connect your {{ provider.name }} account</a>.'),  # noqa
    }

    def get_context_data(self):
        context = super(AttachWebhookNotification, self).get_context_data()
        project = self.extra_context.get('project')
        context.update({
            'url_connect_account': reverse(
                'projects_integrations',
                args=[project.slug],
            ),
            'url_docs_webhook': 'http://docs.readthedocs.io/en/latest/webhooks.html',  # noqa
        })
        return context
