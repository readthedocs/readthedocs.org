# -*- coding: utf-8 -*-
"""Notifications for SSH key Project Admin tab."""
from __future__ import division, print_function, unicode_literals

from readthedocs.notifications import SiteNotification


class DeployKeyAddedNotification(SiteNotification):

    """Message shown after added the deploy key to the service."""

    name = 'deploy_key_added'
    context_object_name = 'socialaccount'
    success_message = 'Successfully added deploy key to {{ socialaccount.get_provider.name }} project.'  # noqa
    failure_message = 'Failed to add deploy key to {{ socialaccount.get_provider.name }} project, ensure you have the correct permissions and try importing again.'  # noqa


class DeployKeyDeletedNotification(SiteNotification):

    """Message shown after deleted the deploy key to the service."""

    name = 'deploy_key_deleted'
    context_object_name = 'socialaccount'
    success_message = 'Successfully deleted deploy key from {{ socialaccount.get_provider.name }} project.'  # noqa
    failure_message = 'Failed to delete deploy key from {{ socialaccount.get_provider.name }} project. Please, delete it manually from {{ socialaccount.get_provider.name }} page.'  # noqa
