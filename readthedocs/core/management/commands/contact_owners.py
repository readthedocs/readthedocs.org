import structlog
import sys
from pathlib import Path
from pprint import pprint

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils.contact import contact_users
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project

User = get_user_model()  # noqa

log = structlog.get_logger(__name__)


class Command(BaseCommand):

    """
    Send an email or sticky notification from a file (markdown) to all owners.

    Usage examples
    --------------

    Email all owners of the site::

      django-admin contact_owners --email email.md

    Email and send an ephemeral (disappears after shown once) notification to all owners of the "readthedocs" organization::

      django-admin contact_owners --email email.md --notification notification.md --organization readthedocs  # noqa

    Where ``email.md`` is a markdown file with the first line as the subject, and the rest is the content.
    ``user`` and ``domain`` are available in the context.

    .. code:: markdown

       Read the Docs deprecated option, action required

       Dear {{ user.firstname }},

       Greetings from [Read the Docs]({{ domain }}).

    .. note::

       By default the command won't send the email/notification (dry-run mode),
       add the ``--production`` flag to actually send the email/notification.
    """

    help = 'Send an email or sticky notification from a file (markdown) to all owners.'

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
        parser.add_argument(
            '--sticky',
            action='store_true',
            dest='sticky',
            default=False,
            help=(
                'Make the notification sticky '
                '(the notification stays until the user closes it)'
            )
        )
        parser.add_argument(
            '--organization',
            help='Organization slug to filter by.',
        )
        parser.add_argument(
            '--project',
            help='Project slug to filter by.',
        )

    def handle(self, *args, **options):
        if not options['email'] and not options['notification']:
            print("--email or --notification is required.")
            sys.exit(1)

        project = options['project']
        organization = options['organization']
        if project and organization:
            print("--project and --organization can\'t be used together.")
            sys.exit(1)

        if project:
            project = Project.objects.get(slug=project)
            users = AdminPermission.owners(project)
        elif organization:
            organization = Organization.objects.get(slug=organization)
            users = AdminPermission.owners(organization)
        elif settings.RTD_ALLOW_ORGANIZATIONS:
            users = (
                User.objects
                .filter(organizationowner__organization__disabled=False)
                .distinct()
            )
        else:
            users = (
                User.objects
                .filter(projects__skip=False)
                .distinct()
            )

        print(
            'len(owners)={} production={} email={} notification={}'.format(
                users.count(),
                bool(options['production']),
                options['email'],
                options['notification'],
            )
        )

        if input('Continue? y/n: ') != 'y':
            print('Aborting run.')
            return

        notification_content = ''
        if options['notification']:
            file = Path(options['notification'])
            with file.open() as f:
                notification_content = f.read()

        email_subject = ''
        email_content = ''
        if options['email']:
            file = Path(options['email'])
            with file.open() as f:
                content = f.read().split('\n')
            email_subject = content[0].strip()
            email_content = '\n'.join(content[1:]).strip()

        resp = contact_users(
            users=users,
            email_subject=email_subject,
            email_content=email_content,
            notification_content=notification_content,
            sticky_notification=options['sticky'],
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
