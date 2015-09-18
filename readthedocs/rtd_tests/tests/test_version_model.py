from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get
from guardian.shortcuts import get_objects_for_user

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class VersionPermissionTests(TestCase):
    def test_version_save_sets_permission(self):
        user = get(User)
        project = get(Project)

        versions = get_objects_for_user(user, 'builds.view_version')
        self.assertEqual(len(versions), 0)

        version = get(Version, project=project)
        versions = get_objects_for_user(user, 'builds.view_version')
        self.assertTrue(version not in versions)

        # When user is added after version.
        project.users.add(user)
        versions = get_objects_for_user(user, 'builds.view_version')
        self.assertTrue(version in versions)

        # When user is moved for existing version.
        project.users.remove(user)
        versions = get_objects_for_user(user, 'builds.view_version')
        self.assertTrue(version not in versions)

        # When user is added before version.
        project.users.add(user)
        second = get(Version, project=project)
        versions = get_objects_for_user(user, 'builds.view_version')
        self.assertTrue(second in versions)

        # When project users are reset.
        project.users = []
        second = get(Version, project=project)
        versions = get_objects_for_user(user, 'builds.view_version')
        self.assertTrue(second not in versions)
