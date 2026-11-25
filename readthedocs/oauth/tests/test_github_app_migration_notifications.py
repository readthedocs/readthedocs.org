from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.models import Build
from readthedocs.notifications.constants import CANCELLED
from readthedocs.notifications.constants import DISMISSED
from readthedocs.notifications.constants import UNREAD
from readthedocs.notifications.models import Notification
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.notifications import MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP
from readthedocs.oauth.notifications import MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP_PULL_REQUESTS
from readthedocs.oauth.notifications import MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project


class GitHubAppMigrationNotificationsTests(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = self._create_pending_project("1111")
        get(Build, project=self.project)

    def _create_pending_project(self, remote_id, **kwargs):
        project = get(
            Project,
            users=[self.user],
            remote_repository=get(RemoteRepository, vcs_provider=GITHUB, remote_id=remote_id),
            external_builds_enabled=False,
            skip=False,
            **kwargs,
        )
        # Make tests work on .com.
        if settings.RTD_ALLOW_ORGANIZATIONS:
            get(Organization, owners=[self.user], projects=[project])
        return project

    def _migrate(self, project):
        project.remote_repository = get(
            RemoteRepository,
            vcs_provider=GITHUB_APP,
            remote_id=project.remote_repository.remote_id,
        )
        project.save()

    def _run_command(self, *args):
        call_command("notify_github_app_migration", *args, stdout=StringIO())

    def _project_notifications(self, project):
        return Notification.objects.filter(
            attached_to_id=project.pk,
            attached_to_content_type__model="project",
        )

    def test_dry_run_doesnt_add_notifications(self):
        self._run_command()
        assert not self._project_notifications(self.project).exists()

    def test_adds_notification_to_active_project(self):
        self._run_command("--production")
        notification = self._project_notifications(self.project).get()
        assert notification.message_id == MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP
        assert notification.dismissable is True

    def test_adds_pull_requests_notification_when_pull_request_builds_are_enabled(self):
        self.project.external_builds_enabled = True
        self.project.save()
        self._run_command("--production")
        notification = self._project_notifications(self.project).get()
        assert notification.message_id == MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP_PULL_REQUESTS

    def test_skips_inactive_project(self):
        Build.objects.filter(project=self.project).update(date=timezone.now() - timedelta(days=100))
        self._run_command("--production")
        assert not self._project_notifications(self.project).exists()

    def test_doesnt_notify_again_after_dismissed(self):
        self._run_command("--production")
        self._project_notifications(self.project).update(state=DISMISSED)
        self._run_command("--production")
        assert list(self._project_notifications(self.project).values_list("state", flat=True)) == [
            DISMISSED
        ]

    def test_cancels_user_notification_without_pending_projects(self):
        user_without_projects = get(User)
        stale = Notification.objects.add(
            message_id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
            attached_to=user_without_projects,
        )
        pending = Notification.objects.add(
            message_id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
            attached_to=self.user,
        )
        self._run_command("--production")
        stale.refresh_from_db()
        pending.refresh_from_db()
        assert stale.state == CANCELLED
        assert pending.state == UNREAD

    def test_migrating_project_cancels_notifications(self):
        project_notification = Notification.objects.add(
            message_id=MESSAGE_PROJECT_TO_MIGRATE_TO_GITHUB_APP,
            attached_to=self.project,
        )
        user_notification = Notification.objects.add(
            message_id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
            attached_to=self.user,
        )
        self._migrate(self.project)
        project_notification.refresh_from_db()
        user_notification.refresh_from_db()
        assert project_notification.state == CANCELLED
        assert user_notification.state == CANCELLED

    def test_migrating_project_keeps_user_notification_with_other_pending_projects(self):
        self._create_pending_project("2222")
        user_notification = Notification.objects.add(
            message_id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
            attached_to=self.user,
        )
        self._migrate(self.project)
        user_notification.refresh_from_db()
        assert user_notification.state == UNREAD
