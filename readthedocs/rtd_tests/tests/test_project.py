import datetime
import json
from unittest import mock
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get
from rest_framework.reverse import reverse

from readthedocs.builds.constants import (
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
    EXTERNAL,
    LATEST,
    TAG,
)
from readthedocs.builds.models import Build, Version
from readthedocs.oauth.services import GitHubService, GitLabService
from readthedocs.projects.constants import GITHUB_BRAND, GITLAB_BRAND
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import finish_inactive_builds
from readthedocs.rtd_tests.mocks.paths import fake_paths_by_regex


class ProjectMixin:

    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: pull/merge request Version.
        self.external_version = get(
            Version,
            identifier='pr-version',
            verbose_name='99',
            slug='99',
            project=self.pip,
            active=True,
            type=EXTERNAL
        )


class TestProject(ProjectMixin, TestCase):

    def test_subprojects(self):
        r = self.client.get('/api/v2/project/6/subprojects/', {})
        resp = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(resp['subprojects'][0]['id'], 23)

    def test_token(self):
        r = self.client.get('/api/v2/project/6/token/', {})
        resp = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(resp['token'], None)

    def test_has_pdf(self):
        # The project has a pdf if the PDF file exists on disk.
        with fake_paths_by_regex(r'\.pdf$'):
            self.assertTrue(self.pip.has_pdf(LATEST))

        # The project has no pdf if there is no file on disk.
        with fake_paths_by_regex(r'\.pdf$', exists=False):
            self.assertFalse(self.pip.has_pdf(LATEST))

    def test_has_pdf_with_pdf_build_disabled(self):
        # The project doesn't depend on `enable_pdf_build`
        self.pip.enable_pdf_build = False
        with fake_paths_by_regex(r'\.pdf$'):
            self.assertTrue(self.pip.has_pdf(LATEST))

    def test_has_epub(self):
        # The project has a epub if the PDF file exists on disk.
        with fake_paths_by_regex(r'\.epub$'):
            self.assertTrue(self.pip.has_epub(LATEST))

        # The project has no epub if there is no file on disk.
        with fake_paths_by_regex(r'\.epub$', exists=False):
            self.assertFalse(self.pip.has_epub(LATEST))

    def test_has_epub_with_epub_build_disabled(self):
        # The project doesn't depend on `enable_epub_build`
        self.pip.enable_epub_build = False
        with fake_paths_by_regex(r'\.epub$'):
            self.assertTrue(self.pip.has_epub(LATEST))

    @patch('readthedocs.projects.models.Project.find')
    def test_conf_file_found(self, find_method):
        find_method.return_value = [
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/latest/src/conf.py',
        ]
        self.assertEqual(
            self.pip.conf_file(),
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/latest/src/conf.py',
        )

    @patch('readthedocs.projects.models.Project.find')
    def test_multiple_conf_file_one_doc_in_path(self, find_method):
        find_method.return_value = [
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/latest/src/conf.py',
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/latest/docs/conf.py',
        ]
        self.assertEqual(
            self.pip.conf_file(),
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/latest/docs/conf.py',
        )

    @patch('readthedocs.projects.models.Project.find')
    @patch('readthedocs.projects.models.Project.full_find')
    def test_conf_file_not_found(self, find_method, full_find_method):
        find_method.return_value = []
        full_find_method.return_value = []
        with self.assertRaisesMessage(
                ProjectConfigurationError,
                ProjectConfigurationError.NOT_FOUND,
        ) as cm:
            self.pip.conf_file()

    @patch('readthedocs.projects.models.Project.find')
    def test_multiple_conf_files(self, find_method):
        find_method.return_value = [
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/multi-conf.py/src/conf.py',
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/multi-conf.py/src/sub/conf.py',
            '/home/docs/rtfd/code/readthedocs.org/user_builds/pip/checkouts/multi-conf.py/src/sub/src/conf.py',
        ]
        with self.assertRaisesMessage(
                ProjectConfigurationError,
                ProjectConfigurationError.MULTIPLE_CONF_FILES,
        ) as cm:
            self.pip.conf_file()

    def test_get_storage_path(self):
        self.assertEqual(
            self.pip.get_storage_path('pdf', LATEST),
            'pdf/pip/latest/pip.pdf',
        )
        self.assertEqual(
            self.pip.get_storage_path('epub', LATEST),
            'epub/pip/latest/pip.epub',
        )
        self.assertEqual(
            self.pip.get_storage_path('htmlzip', LATEST),
            'htmlzip/pip/latest/pip.zip',
        )

    def test_get_storage_path_for_external_versions(self):
        self.assertEqual(
            self.pip.get_storage_path(
                'pdf', self.external_version.slug,
                version_type=self.external_version.type
            ),
            'external/pdf/pip/99/pip.pdf',
        )
        self.assertEqual(
            self.pip.get_storage_path('epub', self.external_version.slug,
                version_type=self.external_version.type
            ),
            'external/epub/pip/99/pip.epub',
        )
        self.assertEqual(
            self.pip.get_storage_path('htmlzip', self.external_version.slug,
                version_type=self.external_version.type
            ),
            'external/htmlzip/pip/99/pip.zip',
        )

    def test_ordered_active_versions_excludes_external_versions(self):
        self.assertNotIn(self.external_version, self.pip.ordered_active_versions())

    def test_active_versions_excludes_external_versions(self):
        self.assertNotIn(self.external_version, self.pip.active_versions())

    def test_all_active_versions_excludes_external_versions(self):
        self.assertNotIn(self.external_version, self.pip.all_active_versions())

    def test_update_stable_version_excludes_external_versions(self):
        # Delete all versions excluding External Versions.
        self.pip.versions.exclude(type=EXTERNAL).delete()
        # Test that External Version is not considered for stable.
        self.assertEqual(self.pip.update_stable_version(), None)

    def test_update_stable_version_machine_false(self):
        # Initial stable version from fixture
        self.assertEqual(self.pip.update_stable_version().slug, '0.8.1')

        # None, when there is no stable to promote
        self.assertEqual(self.pip.update_stable_version(), None)

        get(
            Version,
            identifier='9.0',
            verbose_name='9.0',
            slug='9.0',
            type=TAG,
            project=self.pip,
            active=True,
        )
        # New stable now is the newly created version
        self.assertEqual(self.pip.update_stable_version().slug, '9.0')

        # Make stable version machine=False
        stable = self.pip.get_stable_version()
        stable.machine = False
        stable.save()

        get(
            Version,
            identifier='10.0',
            verbose_name='10.0',
            slug='10.0',
            type=TAG,
            project=self.pip,
            active=True,
        )
        # None, since the stable version is marked as machine=False and Read
        # the Docs does not have control over it
        with patch('readthedocs.projects.models.determine_stable_version') as m:
            self.assertEqual(self.pip.update_stable_version(), None)
            m.assert_not_called()

    def test_has_good_build_excludes_external_versions(self):
        # Delete all versions excluding External Versions.
        self.pip.versions.exclude(type=EXTERNAL).delete()
        # Test that External Version is not considered for has_good_build.
        self.assertFalse(self.pip.has_good_build)

    def test_get_latest_build_excludes_external_versions(self):
        # Delete all versions excluding External Versions.
        self.pip.versions.exclude(type=EXTERNAL).delete()
        # Test that External Version is not considered for get_latest_build.
        self.assertEqual(self.pip.get_latest_build(), None)

    def test_git_provider_name_github(self):
        self.pip.repo = 'https://github.com/pypa/pip'
        self.pip.save()
        self.assertEqual(self.pip.git_provider_name, GITHUB_BRAND)

    def test_git_service_class_github(self):
        self.pip.repo = 'https://github.com/pypa/pip'
        self.pip.save()
        self.assertEqual(self.pip.git_service_class(), GitHubService)

    def test_git_provider_name_gitlab(self):
        self.pip.repo = 'https://gitlab.com/pypa/pip'
        self.pip.save()
        self.assertEqual(self.pip.git_provider_name, GITLAB_BRAND)

    def test_git_service_class_gitlab(self):
        self.pip.repo = 'https://gitlab.com/pypa/pip'
        self.pip.save()
        self.assertEqual(self.pip.git_service_class(), GitLabService)


@mock.patch('readthedocs.projects.forms.trigger_build', mock.MagicMock())
class TestProjectTranslations(ProjectMixin, TestCase):

    def test_translations(self):
        main_project = get(Project)

        # Create translation of ``main_project``.
        get(Project, main_language_project=main_project)

        url = reverse('project-translations', [main_project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        translation_ids_from_api = [
            t['id'] for t in response.data['translations']
        ]
        translation_ids_from_orm = [
            t[0] for t in main_project.translations.values_list('id')
        ]

        self.assertEqual(
            set(translation_ids_from_api),
            set(translation_ids_from_orm),
        )

    def test_translation_delete(self):
        """Ensure translation deletion doesn't cascade up to main project."""
        # In this scenario, a user has created a project and set the translation
        # to another project. If the user deletes this new project, the delete
        # operation shouldn't cascade up to the main project, and should instead
        # set None on the relation.
        project_keep = get(Project)
        project_delete = get(Project)
        project_delete.translations.add(project_keep)
        self.assertTrue(Project.objects.filter(pk=project_keep.pk).exists())
        self.assertTrue(Project.objects.filter(pk=project_delete.pk).exists())
        self.assertEqual(
            Project.objects.get(pk=project_keep.pk).main_language_project,
            project_delete,
        )
        project_delete.delete()
        self.assertFalse(Project.objects.filter(pk=project_delete.pk).exists())
        self.assertTrue(Project.objects.filter(pk=project_keep.pk).exists())
        self.assertIsNone(
            Project.objects.get(pk=project_keep.pk).main_language_project,
        )

    def test_user_can_add_own_project_as_translation(self):
        user_a = User.objects.get(username='eric')
        project_a = get(
            Project, users=[user_a],
            language='en', main_language_project=None,
        )
        project_b = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )

        self.client.login(username=user_a.username, password='test')
        self.client.post(
            reverse('projects_translations', args=[project_a.slug]),
            data={'project': project_b.slug},
        )

        self.assertEqual(project_a.translations.first(), project_b)
        project_b.refresh_from_db()
        self.assertEqual(project_b.main_language_project, project_a)

    def test_user_can_add_project_as_translation_if_is_owner(self):
        # Two users, two projects with different language
        user_a = User.objects.get(username='eric')
        project_a = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )

        user_b = User.objects.get(username='tester')
        # User A and B are owners of project B
        project_b = get(
            Project, users=[user_b, user_a],
            language='en', main_language_project=None,
        )

        self.client.login(username=user_a.username, password='test')
        self.client.post(
            reverse('projects_translations', args=[project_a.slug]),
            data={'project': project_b.slug},
        )

        self.assertEqual(project_a.translations.first(), project_b)

    def test_user_can_not_add_other_user_project_as_translation(self):
        # Two users, two projects with different language
        user_a = User.objects.get(username='eric')
        project_a = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )

        user_b = User.objects.get(username='tester')
        project_b = get(
            Project, users=[user_b],
            language='en', main_language_project=None,
        )

        # User A try to add project B as translation of project A
        self.client.login(username=user_a.username, password='test')
        resp = self.client.post(
            reverse('projects_translations', args=[project_a.slug]),
            data={'project': project_b.slug},
        )

        self.assertContains(resp, 'Select a valid choice')
        self.assertEqual(project_a.translations.count(), 0)
        project_b.refresh_from_db()
        self.assertIsNone(project_b.main_language_project)

    def test_previous_users_can_list_and_delete_translations_not_owner(self):
        """Test to make sure that previous users can list and delete projects
        where they aren't owners."""
        user_a = User.objects.get(username='eric')
        project_a = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )

        user_b = User.objects.get(username='tester')
        project_b = get(
            Project, users=[user_b],
            language='en', main_language_project=None,
        )

        project_a.translations.add(project_b)
        project_a.save()

        self.client.login(username=user_a.username, password='test')

        # Project B is listed under user A translations
        resp = self.client.get(
            reverse('projects_translations', args=[project_a.slug]),
        )
        self.assertContains(resp, project_b.slug)

        resp = self.client.post(
            reverse(
                'projects_translations_delete',
                args=[project_a.slug, project_b.slug],
            ),
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(project_b, project_a.translations.all())

    def test_user_cant_delete_other_user_translations(self):
        user_a = User.objects.get(username='eric')
        project_a = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )
        project_b = get(
            Project, users=[user_a],
            language='en', main_language_project=None,
        )

        project_a.translations.add(project_b)
        project_a.save()

        user_b = User.objects.get(username='tester')
        project_c = get(
            Project, users=[user_b],
            language='es', main_language_project=None,
        )
        project_d = get(
            Project, users=[user_b, user_a],
            language='en', main_language_project=None,
        )
        project_d.translations.add(project_c)
        project_d.save()

        # User B tries to delete translation from user A
        self.client.login(username=user_b.username, password='test')
        self.assertIn(project_b, project_a.translations.all())
        resp = self.client.post(
            reverse(
                'projects_translations_delete',
                args=[project_a.slug, project_b.slug],
            ),
            follow=True,
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn(project_b, project_a.translations.all())

        # User B tries to delete translation from user A
        # with a different parent
        self.client.login(username=user_b.username, password='test')
        self.assertIn(project_b, project_a.translations.all())
        resp = self.client.post(
            reverse(
                'projects_translations_delete',
                args=[project_d.slug, project_b.slug],
            ),
            follow=True,
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn(project_b, project_a.translations.all())

        # User A tries to delete translation from user A
        # with a different parent
        self.client.login(username=user_a.username, password='test')
        self.assertIn(project_b, project_a.translations.all())
        resp = self.client.post(
            reverse(
                'projects_translations_delete',
                args=[project_b.slug, project_b.slug],
            ),
            follow=True,
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn(project_b, project_a.translations.all())

    def test_user_cant_change_lang_to_translation_lang(self):
        user_a = User.objects.get(username='eric')
        project_a = Project.objects.get(slug='read-the-docs')
        project_b = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )

        project_a.translations.add(project_b)
        project_a.save()

        # User tries to change the language
        # to the same of the translation
        self.client.login(username=user_a.username, password='test')
        self.assertIn(project_b, project_a.translations.all())
        self.assertEqual(project_a.language, 'en')
        self.assertEqual(project_b.language, 'es')
        data = model_to_dict(project_a)

        # Remove None values from data
        data = {k: v for k, v in data.items() if v is not None}

        data['language'] = 'es'
        resp = self.client.post(
            reverse(
                'projects_edit',
                args=[project_a.slug],
            ),
            data=data,
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(
            resp,
            'There is already a &quot;es&quot; translation '
            'for the read-the-docs project',
        )

    def test_user_can_change_project_with_same_lang(self):
        user_a = User.objects.get(username='eric')
        project_a = Project.objects.get(slug='read-the-docs')
        project_b = get(
            Project, users=[user_a],
            language='es', main_language_project=None,
        )

        project_a.translations.add(project_b)
        project_a.save()

        # User save the project with no modifications
        self.client.login(username=user_a.username, password='test')
        self.assertIn(project_b, project_a.translations.all())
        self.assertEqual(project_a.language, 'en')
        self.assertEqual(project_b.language, 'es')
        data = model_to_dict(project_a)

        # Remove None values from data
        data = {k: v for k, v in data.items() if v is not None}

        # Same language
        data['language'] = 'en'
        resp = self.client.post(
            reverse(
                'projects_edit',
                args=[project_a.slug],
            ),
            data=data,
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'There is already a')


class TestFinishInactiveBuildsTask(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')

        self.taggit = Project.objects.get(slug='taggit')
        self.taggit.container_time_limit = 7200  # 2 hours
        self.taggit.save()

        # Build just started with the default time
        self.build_1 = Build.objects.create(
            project=self.pip,
            version=self.pip.get_stable_version(),
            state=BUILD_STATE_CLONING,
        )

        # Build started an hour ago with default time
        self.build_2 = Build.objects.create(
            project=self.pip,
            version=self.pip.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
        )
        self.build_2.date = (
            timezone.now() - datetime.timedelta(hours=1)
        )
        self.build_2.save()

        # Build started an hour ago with custom time (2 hours)
        self.build_3 = Build.objects.create(
            project=self.taggit,
            version=self.taggit.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
        )
        self.build_3.date = (
            timezone.now() - datetime.timedelta(hours=1)
        )
        self.build_3.save()

    @pytest.mark.xfail(reason='Fails while we work out Docker time limits', strict=True)
    def test_finish_inactive_builds_task(self):
        finish_inactive_builds()

        # Legitimate build (just started) not finished
        self.build_1.refresh_from_db()
        self.assertTrue(self.build_1.success)
        self.assertEqual(self.build_1.error, '')
        self.assertEqual(self.build_1.state, BUILD_STATE_CLONING)

        # Build with default time finished
        self.build_2.refresh_from_db()
        self.assertFalse(self.build_2.success)
        self.assertNotEqual(self.build_2.error, '')
        self.assertEqual(self.build_2.state, BUILD_STATE_FINISHED)

        # Build with custom time not finished
        self.build_3.refresh_from_db()
        self.assertTrue(self.build_3.success)
        self.assertEqual(self.build_3.error, '')
        self.assertEqual(self.build_3.state, BUILD_STATE_TRIGGERED)
