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

    def test_form_translation_list_only_owner_projects(self):
        user = get(User)
        project_a = get(Project, users=[user], language='es')
        project_b = get(Project, users=[user], language='en')
        project_c = get(Project, users=[user], language='br')
        user_b = get(User)
        project_d = get(Project, users=[user_b], language='ar')

        form = TranslationForm(
            {'project': project_b.pk},
            parent=project_a,
            user=user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {proj_id for proj_id, _ in form.fields['project'].choices},
            {project_b.id, project_c.id}
        )

    def test_form_translation_list_all_projects_where_is_owner(self):
        user = get(User)
        project_a = get(Project, users=[user], language='es')
        project_b = get(Project, users=[user], language='en')
        project_c = get(Project, users=[user], language='br')
        user_b = get(User)
        project_d = get(Project, users=[user_b, user], language='ar')

        form = TranslationForm(
            {'project': project_b.pk},
            parent=project_a,
            user=user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {proj_id for proj_id, _ in form.fields['project'].choices},
            {project_b.id, project_c.id, project_d.id}
        )

    def test_form_translation_list_only_projects_with_different_lang(self):
        # This would be necessary?
        # Probably confusing
        pass

    def test_form_translation_excludes_existing_translations(self):
        user = get(User)
        project_a = get(Project, users=[user], language='es')
        project_b = get(Project, users=[user], language='en')
        project_c = get(Project, users=[user], language='br')
        project_d = get(Project, users=[user], language='ar')
        project_e = get(Project, users=[user], language='aa')

        project_a.translations.add(project_b)
        project_a.translations.add(project_c)
        project_a.save()

        form = TranslationForm(
            {'project': project_d.pk},
            parent=project_a,
            user=user,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            {proj_id for proj_id, _ in form.fields['project'].choices},
            {project_d.id, project_e.id}
        )

    def test_form_translation_user_cant_add_other_user_project(self):
        user = get(User)
        project_a = get(Project, users=[user], language='es')
        user_b = get(User)
        project_b = get(Project, users=[user_b], language='en')

        form = TranslationForm(
            {'project': project_b.pk},
            parent=project_a,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertNotIn(
            project_b.id,
            [proj_id for proj_id, _ in form.fields['project'].choices]
        )

    def test_form_translation_user_cant_add_project_with_same_lang(self):
        user = get(User)
        project_a = get(Project, users=[user], language='es')
        project_b = get(Project, users=[user], language='es')

        form = TranslationForm(
            {'project': project_b.pk},
            parent=project_a,
            user=user,
        )
        self.assertFalse(form.is_valid())

    def test_form_translation_user_cant_add_project_with_same_lang_of_other_translation(self):
        user = get(User)
        project_a = get(Project, users=[user], language='es')
        project_b = get(Project, users=[user], language='en')
        project_c = get(Project, users=[user], language='en')

        project_a.translations.add(project_b)
        project_a.save()

        form = TranslationForm(
            {'project': project_c.pk},
            parent=project_a,
            user=user,
        )
        self.assertFalse(form.is_valid())
