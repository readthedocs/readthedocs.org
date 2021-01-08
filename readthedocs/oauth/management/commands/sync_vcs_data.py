from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from readthedocs.oauth.tasks import sync_remote_repositories


class Command(BaseCommand):
    help = "Sync OAuth RemoteRepository and RemoteOrganization"

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='resync-oauth',
            help='Celery queue name.',
        )
        parser.add_argument(
            '--users',
            nargs='+',
            type=str,
            default=[],
            help='Re-sync VCS provider data for specific users only.',
        )
        parser.add_argument(
            '--skip-users',
            nargs='+',
            type=str,
            default=[],
            help='Skip re-sync VCS provider data for specific users.',
        )
        parser.add_argument(
            '--max-users',
            type=int,
            default=100,
            help='Maximum number of users that should be synced.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Force re-sync VCS provider data even if the users are already synced.',
        )

    def handle(self, *args, **options):
        queue = options.get('queue')
        sync_users = options.get('users')
        skip_users = options.get('skip_users')
        max_users = options.get('max_users')
        force_sync = options.get('force')

        # Filter users who have social accounts connected to their RTD account
        users = User.objects.filter(
            socialaccount__isnull=False
        ).distinct()

        if not force_sync:
            users = users.filter(
                remote_repository_relations__isnull=True
            ).distinct()

        if sync_users:
            users = users.filter(username__in=sync_users)

        if skip_users:
            users = users.exclude(username__in=skip_users)

        users_to_sync = users.values_list('id', flat=True)[:max_users]

        self.stdout.write(
            self.style.SUCCESS(
                'Found %s user(s) with the given parameters' % users.count()
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Re-syncing VCS Providers for %s user(s)' % len(users_to_sync)
            )
        )

        for user_id in users_to_sync:
            # Trigger Sync Remote Repository Tasks for users
            sync_remote_repositories.apply_async(
                args=[user_id], queue=queue
            )
