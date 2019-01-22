# -*- coding: utf-8 -*-

"""Project notifications."""

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.http import HttpRequest
from django.urls import reverse
from messages_extends.constants import ERROR_PERSISTENT

from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class AbandonedProjectNotification(SiteNotification):

    level = REQUIREMENT
    send_email = True
    failure_level = ERROR_PERSISTENT
    subject = 'Abandoned project {{ proj_name }}'
    failure_message = _(
        'Your project {{ proj_name }} is marked as abandoned. Update link '
        'for the project docs is <a href="{{ proj_url }}">{{ proj_url }}</a>.'
    )

    def get_context_data(self):
        context = super(AbandonedProjectNotification, self).get_context_data()
        project = self.extra_context.get('project')
        proj_url = '{base}{url}'.format(
            base=settings.PRODUCTION_DOMAIN,
            url=project.get_absolute_url()
        )
        context.update({
            'proj_name': project.name,
            'proj_url': proj_url
        })
        return context


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
