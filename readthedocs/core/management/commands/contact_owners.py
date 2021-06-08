from pprint import pprint
import logging
import markdown

from django.core.management.base import BaseCommand

from readthedocs.organizations.models import OrganizationOwner
from readthedocs.notifications import SiteNotification
from readthedocs.notifications.backends import SiteBackend
from django.core.mail import send_mail

log = logging.getLogger(__name__)


class Command(BaseCommand):

    subject = 'Read the Docs for Business scheduled maintenance window'

    message = """
Hi,

You're receiving this email because you're an organization owner on Read the Docs for Business. We wanted to make you aware that on Friday, February 5 at 5:00pm PST (8:00pm EST, Saturday 01:00 UTC),
Read the Docs for Business (readthedocs.com) will be having a **scheduled downtime of approximately 2 hours**.

During this maintenance window, **documentation will continue to be online** but new documentation builds will not trigger and the Read the Docs dashboard will be read-only. New builds and webhooks will begin processing once the maintenance is over.

To ensure minimal impact for our users, we are performing this upgrade during a Friday afternoon which is one of our lowest usage periods. This maintenance window is for a required database version upgrade which we couldn't perform in place. While these kinds of things do happen from time to time, we haven't had a scheduled downtime on Read the Docs for Business in a few years. Doing this helps us ensure that our services perform well and have up-to-date security.

Thanks for your understanding of this maintenance downtime.

Read the Docs team

    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--production',
            action='store_true',
            dest='production',
            default=False,
            help='Use this flag when actually running in prod',
        )
        parser.add_argument(
            '--email',
            action='store_true',
            dest='email',
            default=False,
            help='Actually send the email',
        )
        parser.add_argument(
            '--notification',
            action='store_true',
            dest='notification',
            default=False,
            help='Create a notification',
        )

    def handle(self, *args, **options):
        """Build/index all versions or a single project's version."""
        if options['production']:
            org_owners = OrganizationOwner.objects.filter(organization__disabled=False)
        else:
            org_owners = OrganizationOwner.objects.filter(organization__slug='read-the-docs')

        log.info('len(owners)=%s production=%s email=%s notification=%s',
                 org_owners.count(), options['production'],
                 options['email'], options['notification']
                 )
        cont = input('Continue? y/n: ')
        if cont != 'y':
            log.warning('Aborting run.')
            return

        sent_emails = set()
        sent_notifications = set()

        backend = SiteBackend(request=None)
        class TempNotification(SiteNotification):
            name = 'pull-request-builder-general-availability'
            success_message = 'Blog post: pull request builders are now <a href="https://blog.readthedocs.com/pull-request-builder-general-availability/">available for all organizations</a>'

        html_message = markdown.markdown(self.message)

        for rel in org_owners.iterator():
            owner = rel.owner

            if options['notification']:

                if owner.pk in sent_notifications:
                    log.info('Already sent to this owner: owner=%s', owner)
                    continue

                sent_notifications.add(owner.pk)

                notification = TempNotification(
                    user=owner,
                    success=True,
                )
                backend.send(notification)

                log.info('Successfully set notification owner=%s', owner)

            if options['email']:
                if owner.pk in sent_emails:
                    log.info('Already sent to this owner: owner=%s', owner)
                    continue

                sent_emails.add(owner.pk)

                emails = [owner.email]
                for verified in owner.emailaddress_set.filter(verified=True):
                    if verified.email not in emails:
                        emails.append(verified.email)

                try:
                    kwargs = dict(
                        subject=self.subject,
                        message=self.message,
                        html_message=html_message,
                        from_email='Read the Docs <support@readthedocs.com>',
                        recipient_list=emails,
                    )
                    if options['send']:
                        log.info('Sending email to %s', emails)
                        send_mail(**kwargs)
                    else:
                        log.info('Only printing email')
                        pprint(kwargs)
                    sent_emails.extend(emails)
                except Exception:
                    # Handle errors gracefully
                    log.exception('Mail failed to send')
                    cont = input('Continue? y/n: ')
                    if cont != 'y':
                        log.warning('Aborting run.')
                        return

                log.info('All emails sent:')
                pprint(sent_emails)
                log.info('%s total emails', len(sent_emails))
