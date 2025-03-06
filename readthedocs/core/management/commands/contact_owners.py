import sys
from pathlib import Path

import structlog
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

    Email and send an ephemeral (disappears after shown once) notification
    to all owners of the "readthedocs" organization::

      django-admin contact_owners
        --email email.md
        --notification notification.md
        --organization readthedocs

    Send a sticky notifications to multiple users::

      django-admin contact_owners
        --notification notification.md
        --sticky
        --usernames usernames.txt

    * ``usernames.txt`` is a text file containing one username per line.
    * ``notifications.md`` is a Markdown file containing the message
       to be included in the notification.
    * ``email.md`` is a Markdown file with the first line as the subject,
      and the rest is the content.

      The context available is:
        * ``user``
        * ``production_uri``

    .. code:: markdown

       Read the Docs deprecated option, action required

       Dear {{ user.firstname }},

       Greetings from [Read the Docs]({{ production_uri }}).

    .. note::

       By default the command won't send the email/notification (dry-run mode),
       add the ``--production`` flag to actually send the email/notification.

    .. note::

       If you need to extend the behavior or add a new use case,
       we recommend creating a simple script file that re-use the methods
       and functions from this command.
       This is an example to contact Domain owners:
       https://gist.github.com/humitos/3e08ed4763a9312f5c0a9a997ea95a42
    """

    help = "Send an email or sticky notification from a file (Markdown) to users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--production",
            action="store_true",
            dest="production",
            default=False,
            help=(
                "Send the email/notification for real, "
                "otherwise we only logs the notification in the console (dryrun)."
            ),
        )
        parser.add_argument(
            "--email",
            help=(
                "Path to a file with the email content in markdown. "
                "The first line would be the subject."
            ),
        )
        parser.add_argument(
            "--notification",
            help="Path to a file with the notification content in markdown.",
        )
        parser.add_argument(
            "--sticky",
            action="store_true",
            dest="sticky",
            default=False,
            help=("Make the notification sticky (the notification stays until the user closes it)"),
        )
        parser.add_argument(
            "--organization",
            help="Organization slug to filter by.",
        )
        parser.add_argument(
            "--project",
            help="Project slug to filter by.",
        )
        parser.add_argument(
            "--usernames",
            help="Path to a file with one username per line to filter by.",
        )

    def handle(self, *args, **options):
        if not options["email"] and not options["notification"]:
            print("--email or --notification is required.")
            sys.exit(1)

        project = options["project"]
        organization = options["organization"]
        usernames = options["usernames"]
        if len([item for item in [project, organization, usernames] if bool(item)]) >= 2:
            print("--project, --organization and --usernames can't be used together.")
            sys.exit(1)

        if project:
            project = Project.objects.get(slug=project)
            users = AdminPermission.owners(project)
        elif organization:
            organization = Organization.objects.get(slug=organization)
            users = AdminPermission.owners(organization)
        elif usernames:
            file = Path(usernames)
            with file.open(encoding="utf8") as f:
                usernames = f.readlines()

            # remove "\n" from lines
            usernames = [line.strip() for line in usernames]

            users = User.objects.filter(username__in=usernames)
        elif settings.RTD_ALLOW_ORGANIZATIONS:
            users = User.objects.filter(organizationowner__organization__disabled=False).distinct()
        else:
            users = User.objects.filter(projects__skip=False).distinct()

        log.info(
            "Command arguments.",
            n_owners=users.count(),
            production=bool(options["production"]),
            email_filepath=options["email"],
            notification_filepath=options["notification"],
            sticky=options["sticky"],
        )

        if input("Continue? y/N: ") != "y":
            print("Aborting run.")
            return

        notification_content = ""
        if options["notification"]:
            file = Path(options["notification"])
            with file.open(encoding="utf8") as f:
                notification_content = f.read()

        email_subject = ""
        email_content = ""
        if options["email"]:
            file = Path(options["email"])
            with file.open(encoding="utf8") as f:
                content = f.read().split("\n")
            email_subject = content[0].strip()
            email_content = "\n".join(content[1:]).strip()

        resp = contact_users(
            users=users,
            email_subject=email_subject,
            email_content=email_content,
            notification_content=notification_content,
            sticky_notification=options["sticky"],
            dryrun=not options["production"],
        )

        email = resp["email"]
        log.info(
            "Sending emails finished.",
            total=len(email["sent"]),
            total_failed=len(email["failed"]),
            sent_emails=email["sent"],
            failed_emails=email["failed"],
        )

        notification = resp["notification"]
        log.info(
            "Sending notifications finished.",
            total=len(notification["sent"]),
            total_failed=len(notification["failed"]),
            sent_notifications=notification["sent"],
            failed_notifications=notification["failed"],
        )
