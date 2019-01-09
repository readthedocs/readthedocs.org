# -*- coding: utf-8 -*-
"""Project notifications"""

from __future__ import absolute_import
from datetime import timedelta
from django.utils import timezone
from messages_extends.models import Message
from readthedocs.notifications import Notification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class DeprecatedViewNotification(Notification):

    """
    Notification to alert user of a view that is going away.

    This notification is used for cases where we want to alert the project
    users that a view that they are using is going to be going away.

    .. warning::
        This is currently used primarily for deprecated webhook endpoints, which
        aren't even hit by a user. There are likely some mechanics to this
        class that expect a webhook endpoint and not a generic view.

    The first time that a notification is sent to a user, ``SiteBackend`` will
    create (avoiding duplication) a site notification and the ``EmailBackend``
    will send an email notification. The :py:cls:`Message` object will now have
    ``extra_tags`` of ``email_delayed``. This means that the first email was
    sent and that we won't send the second email for
    ``DeprecatedViewNotification.email_period``.

    The second time that a notification is sent to a user,
    :py:cls:`message_extends.models.Message` will deduplicate the site message
    and we rely on message meta data, stored in ``extra_tags`` on the model, to
    determine if an email was already sent. We will send a second email to a
    :py:cls:`Message` that has ``email_delayed`` in extra_tags, at which point
    we'll set ``extra_tags`` to have ``email_sent``. Any further attempts to
    send a message won't work as the ``extra_tags`` is no longer
    ``email_delayed``.
    """

    # This is an abstract class, we won't set a name yet.
    name = None
    context_object_name = 'project'
    subject = '{{ project.name }} project webhook needs to be updated'
    send_email = False
    email_period = timedelta(days=7)
    level = REQUIREMENT

    def __init__(self, context_object, request, user=None):
        super(DeprecatedViewNotification, self).__init__(
            context_object,
            request,
            user,
        )
        self.message, created = self._create_message()

        if self.name is None:
            raise ValueError('{} is an abstract class.'.format(
                self.__class__.__name__,
            ))

        # Mark this notification to be sent as email the first time that it's
        # created (user hits this endpoint for the first time)
        if created:
            self.send_email = True

    @classmethod
    def for_project_users(cls, projects):
        """
        Notify project users of deprecated view.

        This is primarily used for deprecated webhook endpoints, though is not
        particular to this usage.

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

    def _create_message(self):
        # Each time this class is instantiated we create a new Message (it's
        # de-duplicated by using the ``message``, ``user`` and ``extra_tags``
        # status)
        return Message.objects.get_or_create(
            message='{}: {}'.format(self.name, self.get_subject()),
            level=self.level,
            user=self.user,
            extra_tags='email_delayed',
        )

    def send(self, *args, **kwargs):  # noqa
        if self.message.created + self.email_period < timezone.now():
            # Mark this instance to really send the email and rely on the
            # EmailBackend to effectively send the email
            self.send_email = True

            # Mark the message as sent and send the email
            self.message.extra_tags = 'email_sent'
            self.message.save()

            # Create a new Message with ``email_delayed`` so we are prepared to
            # de-duplicate the following one
            self._create_message()

        super(DeprecatedViewNotification, self).send(*args, **kwargs)


class DeprecatedGitHubWebhookNotification(DeprecatedViewNotification):

    name = 'deprecated_github_webhook'


class DeprecatedBuildWebhookNotification(DeprecatedViewNotification):

    name = 'deprecated_build_webhook'
