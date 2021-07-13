import logging
from pprint import pprint

from django.conf import settings
from django.core.mail import send_mail

from readthedocs.notifications import SiteNotification
from readthedocs.notifications.backends import SiteBackend

log = logging.getLogger(__name__)


def contact_users(
    users,
    email_subject=None,
    email_content=None,
    email_content_html=None,
    from_email=None,
    notification_content=None,
    dryrun=True,
):
    """
    Send an email or a sticky notification to a list of users.

    :param users: Queryset of Users.
    :param string email_subject: Email subject
    :param string email_content: Email content (txt)
    :param string email_content_html: Email content (HTML)
    :param string from_email: Email to sent from (Test Support <support@test.com>)
    :param string notification_content: Content for the sticky notification.
    :param bool dryrun: If `True` don't sent the email or notification, just print the content.

    :returns: A dictionary with a list of sent/failed emails/notifications.
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    sent_emails = set()
    failed_emails = set()
    sent_notifications = set()
    failed_notifications = set()

    backend = SiteBackend(request=None)

    class TempNotification(SiteNotification):

        def render(self, *args, **kwargs):
            return notification_content

    for user in users.iterator():
        if notification_content:
            notification = TempNotification(
                user=user,
                success=True,
            )
            try:
                if not dryrun:
                    backend.send(notification)
                else:
                    pprint(notification_content)
            except Exception:
                log.exception('Notification failed to send')
                failed_notifications.add(user.pk)
            else:
                log.info('Successfully set notification user=%s', user)
                sent_notifications.add(user.pk)

        if email_subject:
            emails = list(
                user.emailaddress_set
                .filter(verified=True)
                .exclude(email=user.email)
                .values_list('email', flat=True)
            )
            emails.append(user.email)

            try:
                kwargs = dict(
                    subject=email_subject,
                    message=email_content,
                    html_message=email_content_html,
                    from_email=from_email,
                    recipient_list=emails,
                )
                if not dryrun:
                    send_mail(**kwargs)
                else:
                    pprint(kwargs)
            except Exception:
                log.exception('Mail failed to send')
                failed_emails.update(emails)
            else:
                log.info('Email sent to %s', emails)
                sent_emails.update(emails)

    return {
        'email': {
            'sent': sent_emails,
            'failed': failed_emails,
        },
        'notification': {
            'sent': sent_notifications,
            'failed': failed_emails,
        },
    }
