# -*- coding: utf-8 -*-
"""Project notifications"""

from __future__ import absolute_import
from datetime import timedelta
from django.utils import timezone
from django.http import HttpRequest
from messages_extends.models import Message
from readthedocs.notifications import Notification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class DeprecatedViewNotification(Notification):

    """Notification to alert user of a view that is going away."""

    context_object_name = 'project'
    subject = '{{ project.name }} project webhook needs to be updated'
    level = REQUIREMENT

    @classmethod
    def notify_project_users(cls, projects):
        """
        Notify project users of deprecated view.

        :param projects: List of project instances
        :type projects: [:py:class:`Project`]
        """
        for project in projects:
            # Send one notification to each owner of the project
            for user in project.users.all():
                notification = cls(
                    context_object=project,
                    request=HttpRequest(),
                    user=user,
                )
                notification.send()


class DeprecatedGitHubWebhookNotification(DeprecatedViewNotification):

    name = 'deprecated_github_webhook'


class DeprecatedBuildWebhookNotification(DeprecatedViewNotification):

    name = 'deprecated_build_webhook'
