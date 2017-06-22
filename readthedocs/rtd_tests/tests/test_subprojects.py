from __future__ import absolute_import

import mock
import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.forms import ProjectRelationshipForm
from readthedocs.projects.models import Project, ProjectRelationship
from readthedocs.rtd_tests.utils import create_user


class SubprojectFormTests(TestCase):

    def test_empty_child(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug='mainproject')
        form = ProjectRelationshipForm(
            {},
            project=project,
            user=user
        )
        form.full_clean()
        self.assertEqual(len(form.errors['child']), 1)
        self.assertRegexpMatches(
            form.errors['child'][0],
            r'This field is required.'
        )

    def test_nonexistent_child(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug='mainproject')
        self.assertFalse(Project.objects.filter(pk=9999).exists())
        form = ProjectRelationshipForm(
            {'child': 9999},
            project=project,
            user=user
        )
        form.full_clean()
        self.assertEqual(len(form.errors['child']), 1)
        self.assertRegexpMatches(
            form.errors['child'][0],
            r'Select a valid choice.'
        )

    def test_adding_subproject_fails_when_user_is_not_admin(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug='mainproject')
        project.users.add(user)
        subproject = fixture.get(Project, slug='subproject')
        self.assertQuerysetEqual(
            Project.objects.for_admin_user(user),
            [project],
            transform=lambda n: n,
        )
        form = ProjectRelationshipForm(
            {'child': subproject.pk},
            project=project,
            user=user
        )
        form.full_clean()
        self.assertEqual(len(form.errors['child']), 1)
        self.assertRegexpMatches(
            form.errors['child'][0],
            r'Select a valid choice.'
        )

    def test_adding_subproject_passes_when_user_is_admin(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug='mainproject')
        project.users.add(user)
        subproject = fixture.get(Project, slug='subproject')
        subproject.users.add(user)
        self.assertQuerysetEqual(
            Project.objects.for_admin_user(user),
            [project, subproject],
            transform=lambda n: n,
        )
        form = ProjectRelationshipForm(
            {'child': subproject.pk},
            project=project,
            user=user
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(
            [r.child for r in project.subprojects.all()],
            [subproject]
        )

    def test_subproject_form_cant_create_sub_sub_project(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        subsubproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship, parent=project, child=subproject
        )
        self.assertQuerysetEqual(
            Project.objects.for_admin_user(user),
            [project, subproject, subsubproject],
            transform=lambda n: n,
        )
        form = ProjectRelationshipForm(
            {'child': subsubproject.pk},
            project=subproject,
            user=user
        )
        # The subsubproject is valid here, as far as the child check is
        # concerned, but the parent check should fail.
        self.assertEqual(
            [proj_id for (proj_id, __) in form.fields['child'].choices],
            ['', subsubproject.pk],
        )
        form.full_clean()
        self.assertEqual(len(form.errors['parent']), 1)
        self.assertRegexpMatches(
            form.errors['parent'][0],
            r'Subproject nesting is not supported'
        )

    def test_excludes_existing_subprojects(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship, parent=project, child=subproject
        )
        self.assertQuerysetEqual(
            Project.objects.for_admin_user(user),
            [project, subproject],
            transform=lambda n: n,
        )
        form = ProjectRelationshipForm(
            {'child': subproject.pk},
            project=project,
            user=user
        )
        self.assertEqual(
            [proj_id for (proj_id, __) in form.fields['child'].choices],
            [''],
        )


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class ResolverBase(TestCase):

    def setUp(self):
        with mock.patch('readthedocs.projects.models.broadcast'):
            self.owner = create_user(username='owner', password='test')
            self.tester = create_user(username='tester', password='test')
            self.pip = fixture.get(Project, slug='pip', users=[self.owner], main_language_project=None)
            self.subproject = fixture.get(Project, slug='sub', language='ja',
                                          users=[ self.owner],
                                          main_language_project=None)
            self.translation = fixture.get(Project, slug='trans', language='ja',
                                           users=[ self.owner],
                                           main_language_project=None)
            self.pip.add_subproject(self.subproject)
            self.pip.translations.add(self.translation)

    @override_settings(PRODUCTION_DOMAIN='readthedocs.org')
    def test_resolver_subproject_alias(self):
        relation = self.pip.subprojects.first()
        relation.alias = 'sub_alias'
        relation.save()
        with override_settings(USE_SUBDOMAIN=False):
            resp = self.client.get('/docs/pip/projects/sub_alias/')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp._headers['location'][1],
                'http://readthedocs.org/docs/pip/projects/sub_alias/ja/latest/'
            )
