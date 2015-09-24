from django.test import TestCase

from readthedocs.projects.models import Project

from django_dynamic_fixture import get, new
# Once this util gets merged remove them here
# from readthedocs.rtd_tests.utils import create_user
from django.contrib.auth.models import User


def create_user(username, password):
    user = new(User, username=username)
    user.set_password(password)
    user.save()
    return user


class SubprojectTests(TestCase):

    def setUp(self):
        self.owner = create_user(username='owner', password='test')
        self.pip = get(Project, slug='pip', users=[self.owner])
        self.subproject = get(Project, slug='sub')
        self.pip.add_subproject(self.subproject)

    def test_proper_subproject_url_full_with_filename(self):
        r = self.client.get('/docs/pip/projects/sub/en/latest/usage.html')
        self.assertEqual(r.status_code, 200)

    def test_proper_subproject_url_subdomain(self):
        r = self.client.get('/projects/sub/usage.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 200)

    def test_docs_url_generation(self):

        with self.settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.subproject.get_docs_url(), '/projects/sub/en/latest/')
        with self.settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.subproject.get_docs_url(), 'http://pip.readthedocs.org/')

        with self.settings(USE_SUBDOMAIN=False):
            self.assertEqual(self.pip.get_docs_url(), '/docs/pip/en/latest/')
        with self.settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.pip.get_docs_url(), 'http://pip.readthedocs.org/en/latest/')
