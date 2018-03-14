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
