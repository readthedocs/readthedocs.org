from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import mock
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get
from textclassifier.validators import ClassifierValidator

from readthedocs.projects.exceptions import ProjectSpamError
from readthedocs.projects.forms import ProjectExtraForm, TranslationForm
from readthedocs.projects.models import Project


class TestProjectForms(TestCase):

    @mock.patch.object(ClassifierValidator, '__call__')
    def test_form_spam(self, mocked_validator):
        """Form description field fails spam validation"""
        mocked_validator.side_effect = ProjectSpamError

        data = {
            'description': 'foo',
            'documentation_type': 'sphinx',
            'language': 'en',
        }
        form = ProjectExtraForm(data)
        with self.assertRaises(ProjectSpamError):
            form.is_valid()


class TestTranslationForm(TestCase):

    def get_project(self, lang, users, **kwargs):
        return get(
            Project, language=lang, users=users,
            main_language_project=None, **kwargs
        )

    def test_form_translation_list_only_owner_projects(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='en', users=[user])
        project_c = self.get_project(lang='br', users=[user])

        user_b = get(User)
        project_d = self.get_project(lang='ar', users=[user_b])
        project_e = self.get_project(lang='ga', users=[user_b])

        # shared project
        project_s = self.get_project(lang='fr', users=[user_b, user])

        form = TranslationForm(
            {'project': project_b.slug},
            parent=project_a,
            user=user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields['project'].choices},
            {project_b.slug, project_c.slug, project_s.slug}
        )

        form = TranslationForm(
            {'project': project_e.slug},
            parent=project_d,
            user=user_b,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields['project'].choices},
            {project_e.slug, project_s.slug}
        )

    def test_form_translation_excludes_existing_translations(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='en', users=[user])
        project_c = self.get_project(lang='br', users=[user])
        project_d = self.get_project(lang='ar', users=[user])
        project_e = self.get_project(lang='aa', users=[user])

        project_a.translations.add(project_b)
        project_a.translations.add(project_c)
        project_a.save()

        form = TranslationForm(
            {'project': project_d.slug},
            parent=project_a,
            user=user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {proj_slug for proj_slug, _ in form.fields['project'].choices},
            {project_d.slug, project_e.slug}
        )

    def test_form_translation_user_cant_add_other_user_project(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])

        user_b = get(User)
        project_b = self.get_project(lang='en', users=[user_b])

        form = TranslationForm(
            {'project': project_b.slug},
            parent=project_a,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Select a valid choice',
            ''.join(form.errors['project'])
        )
        self.assertNotIn(
            project_b.slug,
            [proj_slug for proj_slug, _ in form.fields['project'].choices]
        )

    def test_form_translation_user_cant_add_project_with_same_lang(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='es', users=[user])

        form = TranslationForm(
            {'project': project_b.slug},
            parent=project_a,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Both projects have a language of "es"',
            ''.join(form.errors['project'])
        )

    def test_form_translation_user_cant_add_project_with_same_lang_of_other_translation(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='en', users=[user])
        project_c = self.get_project(lang='en', users=[user])

        project_a.translations.add(project_b)
        project_a.save()

        form = TranslationForm(
            {'project': project_c.slug},
            parent=project_a,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'There is already a translation of language "en"',
            ''.join(form.errors['project'])
        )

    def test_form_translation_no_nesting_translation(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='en', users=[user])
        project_c = self.get_project(lang='br', users=[user])

        project_a.translations.add(project_b)
        project_a.save()

        form = TranslationForm(
            {'project': project_b.slug},
            parent=project_c,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Select a valid choice',
            ''.join(form.errors['project'])
        )

    def test_form_translation_no_nesting_translation_case_2(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='en', users=[user])
        project_c = self.get_project(lang='br', users=[user])

        project_a.translations.add(project_b)
        project_a.save()

        form = TranslationForm(
            {'project': project_a.slug},
            parent=project_c,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'This project has translations',
            ''.join(form.errors['project'])
        )

    def test_form_translation_no_circular_translations(self):
        user = get(User)
        project_a = self.get_project(lang='es', users=[user])
        project_b = self.get_project(lang='en', users=[user])

        project_a.translations.add(project_b)
        project_a.save()

        form = TranslationForm(
            {'project': project_a.slug},
            parent=project_b,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'This project has translations',
            ''.join(form.errors['project'])
        )
