"""Notify projects still connected to the old GitHub OAuth integration to migrate to the GitHub App."""

from collections import Counter
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from readthedocs.builds.models import Build
from readthedocs.notifications.constants import CANCELLED
from readthedocs.notifications.constants import READ
from readthedocs.notifications.constants import UNREAD
from readthedocs.notifications.models import Notification
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.migrate import has_projects_pending_migration
from readthedocs.oauth.notifications import MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP
from readthedocs.oauth.notifications import MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP_PULL_REQUESTS
from readthedocs.oauth.notifications import MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP
from readthedocs.oauth.notifications import PROJECT_MIGRATION_MESSAGE_IDS
from readthedocs.projects.models import Project


class Command(BaseCommand):
    help = (
        "Add a GitHub App migration notification to active projects still connected "
        "to the old GitHub OAuth integration, and cancel the ones that no longer apply."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--production",
            action="store_true",
            default=False,
            help="Apply the changes, otherwise only report them (dry run).",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Only notify projects with a build in the last N days.",
        )

    def handle(self, *args, **options):
        production = options["production"]
        self.add_project_notifications(days=options["days"], production=production)
        self.cancel_project_notifications(production=production)
        self.cancel_user_notifications(production=production)
        if not production:
            self.stdout.write("Dry run, nothing was changed. Use --production to apply.")

    def add_project_notifications(self, days, production):
        # Never notify a project twice, even if the notification was dismissed.
        already_notified = Notification.objects.filter(
            attached_to_content_type=ContentType.objects.get_for_model(Project),
            message_id__in=PROJECT_MIGRATION_MESSAGE_IDS,
        ).values("attached_to_id")
        recently_built = Build.objects.filter(
            date__gte=timezone.now() - timedelta(days=days),
        ).values("project_id")
        projects = Project.objects.filter(
            remote_repository__vcs_provider=GITHUB,
            skip=False,
            pk__in=recently_built,
        ).exclude(pk__in=already_notified)

        added = Counter()
        for project in projects.iterator():
            if project.external_builds_enabled:
                message_id = MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP_PULL_REQUESTS
            else:
                message_id = MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP
            if production:
                Notification.objects.add(
                    message_id=message_id,
                    attached_to=project,
                    dismissable=True,
                )
            added[message_id] += 1

        for message_id, count in added.items():
            self.stdout.write(f"Project notifications added: {message_id}={count}")

    def cancel_project_notifications(self, production):
        stale = Notification.objects.filter(
            attached_to_content_type=ContentType.objects.get_for_model(Project),
            message_id__in=PROJECT_MIGRATION_MESSAGE_IDS,
            state__in=(UNREAD, READ),
        ).exclude(
            attached_to_id__in=Project.objects.filter(
                remote_repository__vcs_provider=GITHUB,
            ).values("pk"),
        )
        self.stdout.write(f"Project notifications cancelled: {stale.count()}")
        if production:
            stale.update(state=CANCELLED, modified=timezone.now())

    def cancel_user_notifications(self, production):
        notifications = Notification.objects.filter(
            attached_to_content_type=ContentType.objects.get_for_model(User),
            message_id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
            state__in=(UNREAD, READ),
        )
        stale_ids = []
        for notification in notifications.iterator():
            user = User.objects.filter(pk=notification.attached_to_id).first()
            if user is None or not has_projects_pending_migration(user):
                stale_ids.append(notification.pk)

        self.stdout.write(f"User notifications cancelled: {len(stale_ids)}")
        if production:
            Notification.objects.filter(pk__in=stale_ids).update(
                state=CANCELLED,
                modified=timezone.now(),
            )
