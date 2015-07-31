from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G

from readthedocs.projects.forms import SubprojectForm
from readthedocs.projects.models import Project


class SubprojectFormTests(TestCase):
    def test_name_validation(self):
        user = G(User)
        project = G(Project, slug='mainproject')

        form = SubprojectForm({},
                              parent=project, user=user)
        form.full_clean()
        self.assertTrue('subproject' in form.errors)

        form = SubprojectForm({'name': 'not-existent'},
                              parent=project, user=user)
        form.full_clean()
        self.assertTrue('subproject' in form.errors)

    def test_adding_subproject_fails_when_user_is_not_admin(self):
        # Make sure that a user cannot add a subproject that he is not the
        # admin of.

        user = G(User)
        project = G(Project, slug='mainproject')
        project.users.add(user)
        subproject = G(Project, slug='subproject')

        form = SubprojectForm({'subproject': subproject.slug},
                              parent=project, user=user)
        # Fails because user does not own subproject.
        form.full_clean()
        self.assertTrue('subproject' in form.errors)

    def test_admin_of_subproject_can_add_it(self):
        user = G(User)
        project = G(Project, slug='mainproject')
        project.users.add(user)
        subproject = G(Project, slug='subproject')
        subproject.users.add(user)

        # Works now as user is admin of subproject.
        form = SubprojectForm({'subproject': subproject.slug},
                              parent=project, user=user)
        # Fails because user does not own subproject.
        form.full_clean()
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            [r.child for r in project.subprojects.all()],
            [subproject])
