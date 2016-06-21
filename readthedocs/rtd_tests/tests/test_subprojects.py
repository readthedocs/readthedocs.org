import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User

from readthedocs.projects.forms import SubprojectForm
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.utils import create_user

from django_dynamic_fixture import get


class SubprojectFormTests(TestCase):

    def test_name_validation(self):
        user = get(User)
        project = get(Project, slug='mainproject')

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

        user = get(User)
        project = get(Project, slug='mainproject')
        project.users.add(user)
        subproject = get(Project, slug='subproject')

        form = SubprojectForm({'subproject': subproject.slug},
                              parent=project, user=user)
        # Fails because user does not own subproject.
        form.full_clean()
        self.assertTrue('subproject' in form.errors)

    def test_admin_of_subproject_can_add_it(self):
        user = get(User)
        project = get(Project, slug='mainproject')
        project.users.add(user)
        subproject = get(Project, slug='subproject')
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


@override_settings(PUBLIC_DOMAIN='readthedocs.org')
class ResolverBase(TestCase):

    def setUp(self):
        with mock.patch('readthedocs.projects.models.broadcast'):
            with mock.patch('readthedocs.projects.models.update_static_metadata'):
                self.owner = create_user(username='owner', password='test')
                self.tester = create_user(username='tester', password='test')
                self.pip = get(Project, slug='pip', users=[self.owner], main_language_project=None)
                self.subproject = get(Project, slug='sub', language='ja', users=[
                                      self.owner], main_language_project=None)
                self.translation = get(Project, slug='trans', language='ja', users=[
                                       self.owner], main_language_project=None)
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
