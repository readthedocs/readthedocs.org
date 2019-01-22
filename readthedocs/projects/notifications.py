# -*- coding: utf-8 -*-

"""Project notifications."""

from django.urls import reverse
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from messages_extends.constants import ERROR_PERSISTENT

from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class EmailConfirmNotification(SiteNotification):

    failure_level = ERROR_PERSISTENT
    failure_message = _(
        'Your primary email address is not verified. '
        'Please <a href="{{account_email_url}}">verify it here</a>.',
    )

    def get_context_data(self):
        context = super(EmailConfirmNotification, self).get_context_data()
        context.update({'account_email_url': reverse('account_email')})
        return context


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
