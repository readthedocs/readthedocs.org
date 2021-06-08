import logging
from pathlib import Path
from pprint import pprint
from textwrap import dedent

import markdown
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from readthedocs.core.utils.contact import contact_users

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = dedent(
        """
        Send an email or sticky notification from a file (markdown)
        to all organization owners.
        """
    ).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--production',
            action='store_true',
            dest='production',
            default=False,
            help=(
                'Send the email/notification for real, '
                'otherwise we only print the notification in the console (dryrun).'
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
        User = get_user_model()
        org_owners = (
            User.objects
            .filter(organizationowner__organization__disabled=False)
            .distinct()
        )

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

        notification_content = ''
        if options['notification']:
            file = Path(options['notification'])
            with file.open() as f:
                notification_content = markdown.markdown(f.read())

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

        resp = contact_users(
            users=org_owners,
            email_subject=email_subject,
            email_content=email_content,
            email_content_html=email_content_html,
            notification_content=notification_content,
            dryrun=not options['production'],
        )

        email = resp['email']
        total = len(email['sent'])
        total_failed = len(email['failed'])
        print(f'Emails sent ({total}):')
        pprint(email['sent'])
        print(f'Failed emails ({total_failed}):')
        pprint(email['failed'])

        notification = resp['notification']
        total = len(notification['sent'])
        total_failed = len(notification['failed'])
        print(f'Notifications sent ({total})')
        pprint(notification['sent'])
        print(f'Failed notifications ({total_failed})')
        pprint(notification['failed'])
