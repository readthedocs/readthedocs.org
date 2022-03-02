import structlog
from pprint import pprint

import markdown
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Engine
from messages_extends import constants as message_constants

from readthedocs.notifications import SiteNotification
from readthedocs.notifications.backends import SiteBackend

log = structlog.get_logger(__name__)


def contact_users(
    users,
    email_subject=None,
    email_content=None,
    from_email=None,
    notification_content=None,
    sticky_notification=False,
    context_function=None,
    dryrun=True,
):
    """
    Send an email or a sticky notification to a list of users.

    :param users: Queryset of Users.
    :param string email_subject: Email subject
    :param string email_content: Email content (markdown)
    :param string from_email: Email to sent from (Test Support <support@test.com>)
    :param string notification_content: Content for the sticky notification (markdown)
    :param context_function: A callable that will receive an user
     and return a dict of additional context to be used in the email/notification content
    :param bool dryrun: If `True` don't sent the email or notification, just print the content

    The `email_content` and `notification_content` contents will be rendered using
    a template with the following context::

        {
            'user': <user object>,
            'domain': https://readthedocs.org,
        }

    :returns: A dictionary with a list of sent/failed emails/notifications.
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    context_function = context_function or (lambda user: {})
    sent_emails = set()
    failed_emails = set()
    sent_notifications = set()
    failed_notifications = set()

    backend = SiteBackend(request=None)

    engine = Engine.get_default()
    notification_template = engine.from_string(notification_content or '')

    email_template = engine.from_string(email_content or '')
    email_txt_template = engine.get_template('core/email/common.txt')
    email_html_template = engine.get_template('core/email/common.html')

    class TempNotification(SiteNotification):

        if sticky_notification:
            success_level = message_constants.SUCCESS_PERSISTENT

        def render(self, *args, **kwargs):
            context = {
                'user': self.user,
                'domain': f'https://{settings.PRODUCTION_DOMAIN}',
            }
            context.update(context_function(self.user))
            return markdown.markdown(
                notification_template.render(Context(context))
            )

    total = users.count()
    for count, user in enumerate(users.iterator(), start=1):
        context = {
            'user': user,
            'domain': f'https://{settings.PRODUCTION_DOMAIN}',
        }
        context.update(context_function(user))

        if notification_content:
            notification = TempNotification(
                user=user,
                success=True,
            )
            try:
                if not dryrun:
                    backend.send(notification)
                else:
                    pprint(markdown.markdown(
                        notification_template.render(Context(context))
                    ))
            except Exception:
                log.exception('Notification failed to send')
                failed_notifications.add(user.username)
            else:
                log.info(
                    'Successfully set notification.',
                    user_username=user.username,
                    count=count,
                    total=total,
                )
                sent_notifications.add(user.username)

        if email_subject:
            emails = list(
                user.emailaddress_set
                .filter(verified=True)
                .exclude(email=user.email)
                .values_list('email', flat=True)
            )
            emails.append(user.email)

            # First render the markdown context.
            email_txt_content = email_template.render(
                Context(context)
            )
            email_html_content = markdown.markdown(email_txt_content)

            # Now render it using the base email templates.
            email_txt_rendered = email_txt_template.render(
                Context({'content': email_txt_content})
            )
            email_html_rendered = email_html_template.render(
                Context({'content': email_html_content})
            )

            try:
                kwargs = dict(
                    subject=email_subject,
                    message=email_txt_rendered,
                    html_message=email_html_rendered,
                    from_email=from_email,
                    recipient_list=emails,
                )
                if not dryrun:
                    send_mail(**kwargs)
                else:
                    pprint(kwargs)
            except Exception:
                log.exception('Email failed to send')
                failed_emails.update(emails)
            else:
                log.info('Email sent.', emails=emails, count=count, total=total)
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
