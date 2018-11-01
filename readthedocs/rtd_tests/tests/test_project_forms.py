# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import mock
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get
from textclassifier.validators import ClassifierValidator

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.constants import (
    PRIVATE,
    PROTECTED,
    PUBLIC,
    REPO_TYPE_GIT,
    REPO_TYPE_HG,
)
from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.forms import (
    ProjectAdvancedForm,
    ProjectBasicsForm,
    ProjectExtraForm,
    TranslationForm,
    UpdateProjectForm,
)
from readthedocs.projects.models import Project


class TestProjectForms(TestCase):

    @mock.patch.object(ClassifierValidator, '__call__')
    def test_form_spam(self, mocked_validator):
        """Form description field fails spam validation."""
        mocked_validator.side_effect = ProjectSpamError

        data = {
            'description': 'foo',
            'documentation_type': 'sphinx',
            'language': 'en',
        }
        form = ProjectExtraForm(data)
        with self.assertRaises(ProjectSpamError):
            form.is_valid()

    def test_import_repo_url(self):
        """Validate different type of repository URLs on importing a Project."""

        common_urls = [
            # Invalid
            ('./path/to/relative/folder', False),
            ('../../path/to/relative/folder', False),
            ('../../path/to/@/folder', False),
            ('/path/to/local/folder', False),
            ('/path/to/@/folder', False),
            ('file:///path/to/local/folder', False),
            ('file:///path/to/@/folder', False),
            ('github.com/humitos/foo', False),
            ('https://github.com/|/foo', False),
            ('git://github.com/&&/foo', False),
            # Valid
            ('git://github.com/humitos/foo', True),
            ('http://github.com/humitos/foo', True),
            ('https://github.com/humitos/foo', True),
            ('http://gitlab.com/humitos/foo', True),
            ('http://bitbucket.com/humitos/foo', True),
            ('ftp://ftpserver.com/humitos/foo', True),
            ('ftps://ftpserver.com/humitos/foo', True),
            ('lp:zaraza', True),
        ]

        public_urls = [
            ('git@github.com:humitos/foo', False),
            ('ssh://git@github.com/humitos/foo', False),
            ('ssh+git://github.com/humitos/foo', False),
            ('strangeuser@bitbucket.org:strangeuser/readthedocs.git', False),
            ('user@one-ssh.domain.com:22/_ssh/docs', False),
        ] + common_urls

        private_urls = [
            ('git@github.com:humitos/foo', True),
            ('ssh://git@github.com/humitos/foo', True),
            ('ssh+git://github.com/humitos/foo', True),
            ('strangeuser@bitbucket.org:strangeuser/readthedocs.git', True),
            ('user@one-ssh.domain.com:22/_ssh/docs', True),
        ] + common_urls

        with override_settings(ALLOW_PRIVATE_REPOS=False):
            for url, valid in public_urls:
                initial = {
                    'name': 'foo',
                    'repo_type': 'git',
                    'repo': url,
                }
                form = ProjectBasicsForm(initial)
                self.assertEqual(form.is_valid(), valid, msg=url)

        with override_settings(ALLOW_PRIVATE_REPOS=True):
            for url, valid in private_urls:
                initial = {
                    'name': 'foo',
                    'repo_type': 'git',
                    'repo': url,
                }
                form = ProjectBasicsForm(initial)
                self.assertEqual(form.is_valid(), valid, msg=url)

    def test_empty_slug(self):
        initial = {
            'name': "''",
            'repo_type': 'git',
            'repo': 'https://github.com/user/repository',
        }
        form = ProjectBasicsForm(initial)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_changing_vcs_should_change_latest(self):
        """When changing the project's VCS, latest should be changed too."""
        project = get(Project, repo_type=REPO_TYPE_HG, default_branch=None)
        latest = project.versions.get(slug=LATEST)
        self.assertEqual(latest.identifier, 'default')

        form = ProjectBasicsForm(
            {
                'repo': 'http://github.com/test/test',
                'name': 'name',
                'repo_type': REPO_TYPE_GIT,
            },
            instance=project,
        )
        self.assertTrue(form.is_valid())
        form.save()
        latest.refresh_from_db()
        self.assertEqual(latest.identifier, 'master')

    def test_changing_vcs_should_not_change_latest_is_not_none(self):
        """
        When changing the project's VCS,
        we should respect the custom default branch.
        """
        project = get(Project, repo_type=REPO_TYPE_HG, default_branch='custom')
        latest = project.versions.get(slug=LATEST)
        self.assertEqual(latest.identifier, 'custom')

        form = ProjectBasicsForm(
            {
                'repo': 'http://github.com/test/test',
                'name': 'name',
                'repo_type': REPO_TYPE_GIT,
            },
            instance=project,
        )
        self.assertTrue(form.is_valid())
        form.save()
        latest.refresh_from_db()
        self.assertEqual(latest.identifier, 'custom')


class TestProjectAdvancedForm(TestCase):

    def setUp(self):
        self.project = get(Project)
        get(
            Version,
            project=self.project,
            slug='public-1',
            active=True,
            privacy_level=PUBLIC,
        )
        get(
            Version,
            project=self.project,
            slug='public-2',
            active=True,
            privacy_level=PUBLIC,
        )
        get(
            Version,
            project=self.project,
            slug='public-3',
            active=False,
            privacy_level=PROTECTED,
        )
        get(
            Version,
            project=self.project,
            slug='private',
            active=True,
            privacy_level=PRIVATE,
        )
        get(
            Version,
            project=self.project,
            slug='protected',
            active=True,
            privacy_level=PROTECTED,
        )

    def test_list_only_active_versions_on_default_version(self):
        form = ProjectAdvancedForm(instance=self.project)
        # This version is created automatically by the project on save
        self.assertTrue(self.project.versions.filter(slug=LATEST).exists())
        self.assertEqual(
            set(
                slug
                for slug, _ in form.fields['default_version'].widget.choices
            ),
            {'latest', 'public-1', 'public-2', 'private', 'protected'},
        )

    def test_list_all_versions_on_default_branch(self):
        form = ProjectAdvancedForm(instance=self.project)
        # This version is created automatically by the project on save
        self.assertTrue(self.project.versions.filter(slug=LATEST).exists())
        self.assertEqual(
            set(
                slug
                for slug, _ in form.fields['default_branch'].widget.choices
            ),
            {
                None, 'latest', 'public-1', 'public-2',
                'public-3', 'protected', 'private'
            },
        )


class TestTranslationForms(TestCase):

    def setUp(self):
        self.user_a = get(User)
        self.project_a_es = self.get_project(lang='es', users=[self.user_a])
        self.project_b_en = self.get_project(lang='en', users=[self.user_a])
        self.project_c_br = self.get_project(lang='br', users=[self.user_a])
        self.project_d_ar = self.get_project(lang='ar', users=[self.user_a])
        self.project_e_en = self.get_project(lang='en', users=[self.user_a])

        self.user_b = get(User)
        self.project_f_ar = self.get_project(lang='ar', users=[self.user_b])
        self.project_g_ga = self.get_project(lang='ga', users=[self.user_b])

        self.project_s_fr = self.get_project(
            lang='fr',
            users=[self.user_b, self.user_a]
        )

    def get_project(self, lang, users, **kwargs):
        return get(
            Project, language=lang, users=users,
            main_language_project=None, **kwargs
        )

    def test_list_only_owner_projects(self):
        form = TranslationForm(
            {'project': self.project_b_en.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertTrue(form.is_valid())
        expected_projects = [
            self.project_b_en,
            self.project_c_br,
            self.project_d_ar,
            self.project_e_en,
            self.project_s_fr,
        ]
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields['project'].choices},
            {project.slug for project in expected_projects}
        )

        form = TranslationForm(
            {'project': self.project_g_ga.slug},
            parent=self.project_f_ar,
            user=self.user_b,
        )
        self.assertTrue(form.is_valid())
        expected_projects = [
            self.project_g_ga,
            self.project_s_fr,
        ]
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields['project'].choices},
            {project.slug for project in expected_projects}
        )

    def test_excludes_existing_translations(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.translations.add(self.project_c_br)
        self.project_a_es.save()

        form = TranslationForm(
            {'project': self.project_d_ar.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertTrue(form.is_valid())
        expected_projects = [
            self.project_d_ar,
            self.project_e_en,
            self.project_s_fr,
        ]
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields['project'].choices},
            {project.slug for project in expected_projects}
        )

    def test_user_cant_add_other_user_project(self):
        form = TranslationForm(
            {'project': self.project_f_ar.slug},
            parent=self.project_b_en,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Select a valid choice',
            ''.join(form.errors['project'])
        )
        self.assertNotIn(
            self.project_f_ar,
            [proj_slug for proj_slug, _ in form.fields['project'].choices]
        )

    def test_user_cant_add_project_with_same_lang(self):
        form = TranslationForm(
            {'project': self.project_b_en.slug},
            parent=self.project_e_en,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Both projects can not have the same language (English).',
            ''.join(form.errors['project'])
        )

    def test_user_cant_add_project_with_same_lang_of_other_translation(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {'project': self.project_e_en.slug},
            parent=self.project_a_es,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'This project already has a translation for English.',
            ''.join(form.errors['project'])
        )

    def test_no_nesting_translation(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {'project': self.project_b_en.slug},
            parent=self.project_c_br,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Select a valid choice',
            ''.join(form.errors['project'])
        )

    def test_no_nesting_translation_case_2(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {'project': self.project_a_es.slug},
            parent=self.project_c_br,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'A project with existing translations can not',
            ''.join(form.errors['project'])
        )

    def test_not_already_translation(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.save()

        form = TranslationForm(
            {'project': self.project_c_br.slug},
            parent=self.project_b_en,
            user=self.user_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'is already a translation',
            ''.join(form.errors['project'])
        )

    def test_cant_change_language_to_translation_lang(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.translations.add(self.project_c_br)
        self.project_a_es.save()

        # Parent project tries to change lang
        form = UpdateProjectForm(
            {
                'documentation_type': 'sphinx',
                'language': 'en',
            },
            instance=self.project_a_es
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a "en" translation',
            ''.join(form.errors['language'])
        )

        # Translation tries to change lang
        form = UpdateProjectForm(
            {
                'documentation_type': 'sphinx',
                'language': 'es',
            },
            instance=self.project_b_en
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a "es" translation',
            ''.join(form.errors['language'])
        )

        # Translation tries to change lang
        # to the same as its sibling
        form = UpdateProjectForm(
            {
                'documentation_type': 'sphinx',
                'language': 'br',
            },
            instance=self.project_b_en
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a "br" translation',
            ''.join(form.errors['language'])
        )

    def test_can_change_language_to_self_lang(self):
        self.project_a_es.translations.add(self.project_b_en)
        self.project_a_es.translations.add(self.project_c_br)
        self.project_a_es.save()

        # Parent project tries to change lang
        form = UpdateProjectForm(
            {
                'repo': 'https://github.com/test/test',
                'repo_type': self.project_a_es.repo_type,
                'name': self.project_a_es.name,
                'documentation_type': 'sphinx',
                'language': 'es',
            },
            instance=self.project_a_es
        )
        self.assertTrue(form.is_valid())

        # Translation tries to change lang
        form = UpdateProjectForm(
            {
                'repo': 'https://github.com/test/test',
                'repo_type': self.project_b_en.repo_type,
                'name': self.project_b_en.name,
                'documentation_type': 'sphinx',
                'language': 'en',
            },
            instance=self.project_b_en
        )
        self.assertTrue(form.is_valid())
