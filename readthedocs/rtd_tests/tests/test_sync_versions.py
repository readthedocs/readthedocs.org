# -*- coding: utf-8 -*-

import json

from django.test import TestCase
from django.urls import reverse

from readthedocs.builds.constants import BRANCH, STABLE, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class TestSyncVersions(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        Version.objects.create(
            project=self.pip,
            identifier='origin/master',
            verbose_name='master',
            active=True,
            machine=True,
            type=BRANCH,
        )
        Version.objects.create(
            project=self.pip,
            identifier='to_delete',
            verbose_name='to_delete',
            active=False,
            type=TAG,
        )

    def test_proper_url_no_slash(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
        }

        r = self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        json_data = json.loads(r.content)
        self.assertEqual(json_data['deleted_versions'], ['to_delete'])
        self.assertEqual(json_data['added_versions'], ['to_add'])

    def test_new_tag_update_active(self):

        Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            active=True,
        )

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_9 = Version.objects.get(slug='0.9')
        self.assertTrue(version_9.active)

        # Version 0.9 becomes the stable version
        self.assertEqual(
            version_9.identifier,
            self.pip.get_stable_version().identifier,
        )

    def test_new_tag_dont_update_inactive(self):

        Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            type=TAG,
            active=False,
        )

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        # Version 0.9 becomes the stable version, but it's inactive
        version_9 = self.pip.versions.get(slug='0.9')
        self.assertEqual(
            version_9.identifier,
            self.pip.get_stable_version().identifier,
        )
        self.assertFalse(version_9.active)

        # Version 0.8.3 is still inactive
        version_8 = Version.objects.get(slug='0.8.3')
        self.assertFalse(version_8.active)

    def test_delete_version(self):
        Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            active=False,
        )

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
        }

        self.assertTrue(
            Version.objects.filter(slug='0.8.3').exists(),
        )

        self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        # There isn't a v0.8.3
        self.assertFalse(
            Version.objects.filter(slug='0.8.3').exists(),
        )

    def test_machine_attr_when_user_define_stable_tag_and_delete_it(self):
        """
        The user creates a tag named ``stable`` on an existing repo,
        when syncing the versions, the RTD's ``stable`` is lost
        (set to machine=False) and doesn't update automatically anymore,
        when the tag is deleted on the user repository, the RTD's ``stable``
        is back (set to machine=True).
        """
        version8 = Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            type=TAG,
            active=False,
            machine=False,
        )
        self.pip.update_stable_version()
        current_stable = self.pip.get_stable_version()

        # 0.8.3 is the current stable
        self.assertEqual(
            version8.identifier,
            current_stable.identifier,
        )
        self.assertTrue(current_stable.machine)

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                # User new stable
                {
                    'identifier': '1abc2def3',
                    'verbose_name': 'stable',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            '1abc2def3',
            current_stable.identifier,
        )

        # Deleting the tag should return the RTD's stable
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The version 8 should be the new stable.
        # The stable isn't stuck with the previous commit
        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            '0.8.3',
            current_stable.identifier,
        )
        self.assertTrue(current_stable.machine)

    def test_machine_attr_when_user_define_stable_tag_and_delete_it_new_project(self):
        """
        The user imports a new project with a tag named ``stable``,
        when syncing the versions, the RTD's ``stable`` is lost
        (set to machine=False) and doesn't update automatically anymore,
        when the tag is deleted on the user repository, the RTD's ``stable``
        is back (set to machine=True).
        """
        # There isn't a stable version yet
        self.pip.versions.exclude(slug='master').delete()
        current_stable = self.pip.get_stable_version()
        self.assertIsNone(current_stable)

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                # User stable
                {
                    'identifier': '1abc2def3',
                    'verbose_name': 'stable',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            '1abc2def3',
            current_stable.identifier,
        )

        # User activates the stable version
        current_stable.active = True
        current_stable.save()

        # Deleting the tag should return the RTD's stable
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The version 8 should be the new stable.
        # The stable isn't stuck with the previous commit
        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            '0.8.3',
            current_stable.identifier,
        )
        self.assertTrue(current_stable.machine)

    def test_machine_attr_when_user_define_stable_branch_and_delete_it(self):
        """
        The user creates a branch named ``stable`` on an existing repo,
        when syncing the versions, the RTD's ``stable`` is lost
        (set to machine=False) and doesn't update automatically anymore,
        when the branch is deleted on the user repository, the RTD's ``stable``
        is back (set to machine=True).
        """
        # Project with just branches
        self.pip.versions.filter(type=TAG).delete()
        Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            type=BRANCH,
            active=False,
            machine=False,
        )
        self.pip.update_stable_version()
        current_stable = self.pip.get_stable_version()

        # 0.8.3 is the current stable
        self.assertEqual(
            '0.8.3',
            current_stable.identifier,
        )
        self.assertTrue(current_stable.machine)

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                # User new stable
                {
                    'identifier': 'origin/stable',
                    'verbose_name': 'stable',
                },
                {
                    'identifier': 'origin/0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            'origin/stable',
            current_stable.identifier,
        )

        # Deleting the branch should return the RTD's stable
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The version 8 should be the new stable.
        # The stable isn't stuck with the previous branch
        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            'origin/0.8.3',
            current_stable.identifier,
        )
        self.assertTrue(current_stable.machine)

    def test_machine_attr_when_user_define_stable_branch_and_delete_it_new_project(self):
        """The user imports a new project with a branch named ``stable``, when
        syncing the versions, the RTD's ``stable`` is lost (set to
        machine=False) and doesn't update automatically anymore, when the branch
        is deleted on the user repository, the RTD's ``stable`` is back (set to
        machine=True)."""
        # There isn't a stable version yet
        self.pip.versions.exclude(slug='master').delete()
        current_stable = self.pip.get_stable_version()
        self.assertIsNone(current_stable)

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                # User stable
                {
                    'identifier': 'origin/stable',
                    'verbose_name': 'stable',
                },
                {
                    'identifier': 'origin/0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            'origin/stable',
            current_stable.identifier,
        )

        # User activates the stable version
        current_stable.active = True
        current_stable.save()

        # Deleting the branch should return the RTD's stable
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The version 8 should be the new stable.
        # The stable isn't stuck with the previous commit
        current_stable = self.pip.get_stable_version()
        self.assertEqual(
            'origin/0.8.3',
            current_stable.identifier,
        )
        self.assertTrue(current_stable.machine)

    def test_machine_attr_when_user_define_latest_tag_and_delete_it(self):
        """The user creates a tag named ``latest`` on an existing repo, when
        syncing the versions, the RTD's ``latest`` is lost (set to
        machine=False) and doesn't update automatically anymore, when the tag is
        deleted on the user repository, the RTD's ``latest`` is back (set to
        machine=True)."""
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                # User new stable
                {
                    'identifier': '1abc2def3',
                    'verbose_name': 'latest',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The tag is the new latest
        version_latest = self.pip.versions.get(slug='latest')
        self.assertEqual(
            '1abc2def3',
            version_latest.identifier,
        )

        # Deleting the tag should return the RTD's latest
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The latest isn't stuck with the previous commit
        version_latest = self.pip.versions.get(slug='latest')
        self.assertEqual(
            'master',
            version_latest.identifier,
        )
        self.assertTrue(version_latest.machine)

    def test_machine_attr_when_user_define_latest_branch_and_delete_it(self):
        """The user creates a branch named ``latest`` on an existing repo, when
        syncing the versions, the RTD's ``latest`` is lost (set to
        machine=False) and doesn't update automatically anymore, when the branch
        is deleted on the user repository, the RTD's ``latest`` is back (set to
        machine=True)."""
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                # User new latest
                {
                    'identifier': 'origin/latest',
                    'verbose_name': 'latest',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The branch is the new latest
        version_latest = self.pip.versions.get(slug='latest')
        self.assertEqual(
            'origin/latest',
            version_latest.identifier,
        )

        # Deleting the branch should return the RTD's latest
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # The latest isn't stuck with the previous branch
        version_latest = self.pip.versions.get(slug='latest')
        self.assertEqual(
            'master',
            version_latest.identifier,
        )
        self.assertTrue(version_latest.machine)

    def test_deletes_version_with_same_identifier(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '1234',
                    'verbose_name': 'one',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # We only have one version with an identifier `1234`
        self.assertEqual(
            self.pip.versions.filter(identifier='1234').count(),
            1,
        )

        # We add a new tag with the same identifier
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '1234',
                    'verbose_name': 'two',
                },
                {
                    'identifier': '1234',
                    'verbose_name': 'one',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # We have two versions with an identifier `1234`
        self.assertEqual(
            self.pip.versions.filter(identifier='1234').count(),
            2,
        )

        # We delete one version with identifier `1234`
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '1234',
                    'verbose_name': 'one',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # We have only one version with an identifier `1234`
        self.assertEqual(
            self.pip.versions.filter(identifier='1234').count(),
            1,
        )


class TestStableVersion(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')

    def test_stable_versions(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8',
                    'verbose_name': '0.8',
                },
            ],
        }

        self.assertRaises(
            Version.DoesNotExist,
            Version.objects.get,
            slug=STABLE,
        )
        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '0.9')

    def test_pre_release_are_not_stable(self):
        version_post_data = {
            'branches': [],
            'tags': [
                {'identifier': '1.0a1', 'verbose_name': '1.0a1'},
                {'identifier': '0.9', 'verbose_name': '0.9'},
                {'identifier': '0.9b1', 'verbose_name': '0.9b1'},
                {'identifier': '0.8', 'verbose_name': '0.8'},
                {'identifier': '0.8rc2', 'verbose_name': '0.8rc2'},
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '0.9')

    def test_post_releases_are_stable(self):
        version_post_data = {
            'branches': [],
            'tags': [
                {'identifier': '1.0', 'verbose_name': '1.0'},
                {'identifier': '1.0.post1', 'verbose_name': '1.0.post1'},
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.post1')

    def test_invalid_version_numbers_are_not_stable(self):
        self.pip.versions.all().delete()

        version_post_data = {
            'branches': [],
            'tags': [
                {
                    'identifier': 'this.is.invalid',
                    'verbose_name': 'this.is.invalid',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertFalse(Version.objects.filter(slug=STABLE).exists())

        version_post_data = {
            'branches': [],
            'tags': [
                {
                    'identifier': '1.0',
                    'verbose_name': '1.0',
                },
                {
                    'identifier': 'this.is.invalid',
                    'verbose_name': 'this.is.invalid',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0')

    def test_update_stable_version(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8',
                    'verbose_name': '0.8',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '0.9')

        version_post_data = {
            'tags': [
                {
                    'identifier': '1.0.0',
                    'verbose_name': '1.0.0',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.0')

        version_post_data = {
            'tags': [
                {
                    'identifier': '0.7',
                    'verbose_name': '0.7',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.0')

    def test_update_inactive_stable_version(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertEqual(version_stable.identifier, '0.9')
        version_stable.active = False
        version_stable.save()

        version_post_data['tags'].append({
            'identifier': '1.0.0',
            'verbose_name': '1.0.0',
        })

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        # The identifier of stable is updated
        # but the version is still not active
        version_stable = Version.objects.get(slug=STABLE)
        self.assertFalse(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.0')

    def test_stable_version_tags_over_branches(self):
        version_post_data = {
            'branches': [
                # 2.0 development
                {'identifier': 'origin/2.0', 'verbose_name': '2.0'},
                {'identifier': 'origin/0.9.1rc1', 'verbose_name': '0.9.1rc1'},
            ],
            'tags': [
                {'identifier': '1.0rc1', 'verbose_name': '1.0rc1'},
                {'identifier': '0.9', 'verbose_name': '0.9'},
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        # If there is a branch with a higher version, tags takes preferences
        # over the branches to select the stable version
        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '0.9')

        version_post_data['tags'].append({
            'identifier': '1.0',
            'verbose_name': '1.0',
        })

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0')

    def test_stable_version_same_id_tag_branch(self):
        version_post_data = {
            'branches': [
                # old 1.0 development branch
                {'identifier': 'origin/1.0', 'verbose_name': '1.0'},
            ],
            'tags': [
                # tagged 1.0 final version
                {'identifier': '1.0', 'verbose_name': '1.0'},
                {'identifier': '0.9', 'verbose_name': '0.9'},
            ],
        }

        self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0')
        self.assertEqual(version_stable.type, 'tag')

    def test_unicode(self):
        version_post_data = {
            'branches': [],
            'tags': [
                {'identifier': 'foo-£', 'verbose_name': 'foo-£'},
            ],
        }

        resp = self.client.post(
            '/api/v2/project/{}/sync_versions/'.format(self.pip.pk),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

    def test_user_defined_stable_version_tag_with_tags(self):
        Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            active=True,
        )

        # A pre-existing active stable tag that was machine created
        Version.objects.create(
            project=self.pip,
            identifier='foo',
            type=TAG,
            verbose_name='stable',
            active=True,
            machine=True,
        )

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                # A new user-defined stable tag
                {
                    'identifier': '1abc2def3',
                    'verbose_name': 'stable',
                },
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # Didn't update to newest tag
        version_9 = self.pip.versions.get(slug='0.9')
        self.assertFalse(version_9.active)

        # Did update to user-defined stable version
        version_stable = self.pip.versions.get(slug='stable')
        self.assertFalse(version_stable.machine)
        self.assertTrue(version_stable.active)
        self.assertEqual(
            '1abc2def3',
            self.pip.get_stable_version().identifier,
        )

        # There arent others stable slugs like stable_a
        other_stable = self.pip.versions.filter(
            slug__startswith='stable_',
        )
        self.assertFalse(other_stable.exists())

        # Check that posting again doesn't change anything from current state.
        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        version_stable = self.pip.versions.get(slug='stable')
        self.assertFalse(version_stable.machine)
        self.assertTrue(version_stable.active)
        self.assertEqual(
            '1abc2def3',
            self.pip.get_stable_version().identifier,
        )
        other_stable = self.pip.versions.filter(
            slug__startswith='stable_',
        )
        self.assertFalse(other_stable.exists())

    def test_user_defined_stable_version_branch_with_tags(self):
        Version.objects.create(
            project=self.pip,
            identifier='0.8.3',
            verbose_name='0.8.3',
            active=True,
        )

        # A pre-existing active stable branch that was machine created
        Version.objects.create(
            project=self.pip,
            identifier='foo',
            type=BRANCH,
            verbose_name='stable',
            active=True,
            machine=True,
        )

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                # A new user-defined stable branch
                {
                    'identifier': 'origin/stable',
                    'verbose_name': 'stable',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # Didn't update to newest tag
        version_9 = self.pip.versions.get(slug='0.9')
        self.assertFalse(version_9.active)

        # Did update to user-defined stable version
        version_stable = self.pip.versions.get(slug='stable')
        self.assertFalse(version_stable.machine)
        self.assertTrue(version_stable.active)
        self.assertEqual(
            'origin/stable',
            self.pip.get_stable_version().identifier,
        )
        # There arent others stable slugs like stable_a
        other_stable = self.pip.versions.filter(
            slug__startswith='stable_',
        )
        self.assertFalse(other_stable.exists())

        # Check that posting again doesn't change anything from current state.
        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        version_stable = self.pip.versions.get(slug='stable')
        self.assertFalse(version_stable.machine)
        self.assertTrue(version_stable.active)
        self.assertEqual(
            'origin/stable',
            self.pip.get_stable_version().identifier,
        )
        other_stable = self.pip.versions.filter(
            slug__startswith='stable_',
        )
        self.assertFalse(other_stable.exists())


class TestLatestVersion(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        Version.objects.create(
            project=self.pip,
            identifier='origin/master',
            verbose_name='master',
            active=True,
            machine=True,
            type=BRANCH,
        )
        # When the project is saved, the RTD's ``latest`` version
        # is created.
        self.pip.save()

    def test_user_defined_latest_version_tag(self):
        # TODO: the ``latest`` versions are created
        # as a BRANCH, then here we will have a
        # ``latest_a`` version.
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                # A new user-defined latest tag
                {
                    'identifier': '1abc2def3',
                    'verbose_name': 'latest',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # Did update to user-defined latest version
        version_latest = self.pip.versions.get(slug='latest')
        self.assertFalse(version_latest.machine)
        self.assertTrue(version_latest.active)
        self.assertEqual(
            '1abc2def3',
            version_latest.identifier,
        )

        # There arent others latest slugs like latest_a
        other_latest = self.pip.versions.filter(
            slug__startswith='latest_',
        )
        self.assertFalse(other_latest.exists())

        # Check that posting again doesn't change anything from current state.
        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        version_latest = self.pip.versions.get(slug='latest')
        self.assertFalse(version_latest.machine)
        self.assertTrue(version_latest.active)
        self.assertEqual(
            '1abc2def3',
            version_latest.identifier,
        )
        other_latest = self.pip.versions.filter(
            slug__startswith='latest_',
        )
        self.assertFalse(other_latest.exists())

    def test_user_defined_latest_version_branch(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                # A new user-defined latest branch
                {
                    'identifier': 'origin/latest',
                    'verbose_name': 'latest',
                },
            ],
        }

        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        # Did update to user-defined latest version
        version_latest = self.pip.versions.get(slug='latest')
        self.assertFalse(version_latest.machine)
        self.assertTrue(version_latest.active)
        self.assertEqual(
            'origin/latest',
            version_latest.identifier,
        )

        # There arent others latest slugs like latest_a
        other_latest = self.pip.versions.filter(
            slug__startswith='latest_',
        )
        self.assertFalse(other_latest.exists())

        # Check that posting again doesn't change anything from current state.
        resp = self.client.post(
            reverse('project-sync-versions', args=[self.pip.pk]),
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)

        version_latest = self.pip.versions.get(slug='latest')
        self.assertFalse(version_latest.machine)
        self.assertTrue(version_latest.active)
        self.assertEqual(
            'origin/latest',
            version_latest.identifier,
        )
        other_latest = self.pip.versions.filter(
            slug__startswith='latest_',
        )
        self.assertFalse(other_latest.exists())
