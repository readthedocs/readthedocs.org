from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.projects.models import Project


class TestRemoteRepositoryQuerysets(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(
            Project,
            users=[self.user],
        )

        self.remote_repository_admin_public = get(
            RemoteRepository,
            private=False,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            remote_repository=self.remote_repository_admin_public,
            admin=True,
        )

        self.remote_repository_admin_private = get(
            RemoteRepository,
            private=True,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            remote_repository=self.remote_repository_admin_private,
            admin=True,
        )

        self.remote_repository_not_admin_public = get(
            RemoteRepository,
            private=False,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            remote_repository=self.remote_repository_not_admin_public,
            admin=False,
        )

        self.remote_repository_not_admin_private = get(
            RemoteRepository,
            private=True,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            remote_repository=self.remote_repository_not_admin_private,
            admin=False,
        )

        self.other_user = get(User)
        self.remote_repository_other_user = get(
            RemoteRepository,
            private=False,
        )
        get(
            RemoteRepositoryRelation,
            user=self.other_user,
            remote_repository=self.remote_repository_other_user,
            admin=True,
        )

    def test_for_project_linking(self):
        repositories = RemoteRepository.objects.for_project_linking(user=self.user)
        self.assertEqual(repositories.count(), 2)
        self.assertIn(self.remote_repository_admin_public, repositories)
        self.assertIn(self.remote_repository_admin_private, repositories)
        self.assertNotIn(self.remote_repository_not_admin_public, repositories)
        self.assertNotIn(self.remote_repository_not_admin_private, repositories)
        self.assertNotIn(self.remote_repository_other_user, repositories)

        repositories = RemoteRepository.objects.for_project_linking(
            user=self.other_user
        )
        self.assertEqual(repositories.count(), 1)
        self.assertIn(self.remote_repository_other_user, repositories)
