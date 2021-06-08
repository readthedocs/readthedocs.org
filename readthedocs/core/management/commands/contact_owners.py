from pprint import pprint
import logging
import markdown

from django.core.management.base import BaseCommand
from pathlib import Path

from readthedocs.organizations.models import OrganizationOwner
from readthedocs.notifications import SiteNotification
from readthedocs.notifications.backends import SiteBackend
from django.core.mail import send_mail

log = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--production',
            action='store_true',
            dest='production',
            default=False,
            help=(
                'Send the email/notification for real, '
                'otherwise we only print the notification in the console.'
            )
        )
        parser.add_argument(
            '--email',
            help=(
                'Path to a file with the email content in markdown. '
                'The first line would be the subject.'
            ),       
        )
        parser.add_argument(
            '--notification',
            help='Path to a file with the notification content in markdown.',
        )

    def handle(self, *args, **options):
        """Build/index all versions or a single project's version."""
        org_owners = OrganizationOwner.objects.filter(organization__disabled=False).distinct()

        print(
            'len(owners)={} production={} email={} notification={}'.format(
                org_owners.count(),
                options['production'],
                options['email'],
                options['notification'],
            )
        )
        cont = input('Continue? y/n: ')
        if cont != 'y':
            print('Aborting run.')
            return

        sent_emails = set()
        failed_emails = set()
        sent_notifications = set()
        failed_notifications = set()

        notification_content = ''
        if options['notification']:
            file = Path(options['notification'])
            with file.open() as f:
                notification_content = markdown.markdown(f.read())

        backend = SiteBackend(request=None)
        class TempNotification(SiteNotification):

            def render(self, *args, **kwargs):
                return notification_content

        email_subject = ''
        email_content = ''
        email_content_html = ''
        if options['email']:
            file = Path(options['email'])
            with file.open() as f:
                content = f.read().split('\n')
            email_subject = content[0].strip()
            email_content = '\n'.join(content[1:]).strip()
            email_content_html = markdown.markdown(email_content)

        for rel in org_owners.iterator():
            owner = rel.owner

            if options['notification']:
                notification = TempNotification(
                    user=owner,
                    success=True,
                )
                try:
                    if options['production']:
                        backend.send(notification)
                    else:
                        pprint(notification_content)
                except Exception:
                    log.exception('Notification failed to send')
                    failed_notifications.add(owner.pk)
                else:
                    log.info('Successfully set notification owner=%s', owner)
                    sent_notifications.add(owner.pk)

            if options['email']:
                emails = list(
                    owner.emailaddress_set
                    .filter(verified=True)
                    .exclude(email=owner.email)
                    .values_list('email', flat=True)
                )
                emails.append(owner.email)

                try:
                    kwargs = dict(
                        subject=email_subject,
                        message=email_content,
                        html_message=email_content_html,
                        from_email='Read the Docs <support@readthedocs.com>',
                        recipient_list=emails,
                    )
                    if options['production']:
                        send_mail(**kwargs)
                    else:
                        pprint(kwargs)
                except Exception:
                    log.exception('Mail failed to send')
                    failed_emails.update(emails)
                else:
                    log.info('Email sent to %s', emails)
                    sent_emails.update(emails)

        total = len(sent_emails)
        total_failed = len(failed_emails)
        print(f'Emails sent ({total}):')
        pprint(sent_emails)
        print(f'Failed emails ({total_failed}):')
        pprint(failed_emails)

        total = len(sent_notifications)
        total_failed = len(failed_notifications)
        print(f'Notifications sent ({total})')
        pprint(sent_notifications)
        print(f'Failed notifications ({total_failed})')
        pprint(failed_notifications)
