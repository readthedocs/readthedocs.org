# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.utils.translation import ugettext_lazy as _
from readthedocs.notifications import SiteNotification


class AttachWebhookNotification(SiteNotification):

    NO_CONNECTED_SERVICES = 'no_connected_services'
    NO_PERMISSIONS = 'no_permissions'
    NO_ACCOUNTS = 'no_accounts'

    context_object_name = 'provider'
    success_message = _('Webhook activated successfully.')
    failure_message = {
        NO_CONNECTED_SERVICES: _('Webhook activation failed. There are no connected services for this project.'),
        NO_PERMISSIONS: _('Webhook activation failed. Make sure you have permissions to set it.'),
        NO_ACCOUNTS: _('No accounts available to set webhook on. Please connect your {provider.name} account.'),
    }
