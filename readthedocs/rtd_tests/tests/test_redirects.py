import logging

from django.http import Http404
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import fixture, get

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


# TODO: most of these tests are using USE_SUBDOMAIN, which is not supported anymore.
# Besides, most (or all of them) were migrated to ``readthedocs/proxito/tests/test_old_redirects.py``
# and they are using the correct settings (mocked storage to return correct value on ``.exists()``)
# These tests could be removed completely in the near future.
@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False, APPEND_SLASH=False)
class RedirectTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        logging.disable(logging.DEBUG)
        self.client.login(username='eric', password='test')
        pip = Project.objects.get(slug='pip')
        pip.versions.create_latest()

    def test_proper_url_no_slash(self):
        r = self.client.get('/docs/pip')
        self.assertEqual(r.status_code, 404)

    # Specific Page Redirects

    # If slug is neither valid lang nor valid version, it should 404.
    # TODO: This should 404 directly, not redirect first
    def test_improper_url_with_nonexistent_slug(self):
        r = self.client.get('/docs/pip/nonexistent/')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_filename_only(self):
        r = self.client.get('/docs/pip/test.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_dir_file(self):
        r = self.client.get('/docs/pip/nonexistent_dir/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_dir_subdir_file(self):
        r = self.client.get('/docs/pip/nonexistent_dir/subdir/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_lang_file(self):
        r = self.client.get('/docs/pip/en/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_lang_subdir_file(self):
        r = self.client.get('/docs/pip/en/nonexistent_dir/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_version_dir_file(self):
        r = self.client.get('/docs/pip/latest/nonexistent_dir/bogus.html')
        self.assertEqual(r.status_code, 404)

    # Specific Page Redirects

    @override_settings(USE_SUBDOMAIN=True)
    def test_improper_subdomain_filename_only(self):
        r = self.client.get('/test.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 404)


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False)
class RedirectAppTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.pip.versions.create_latest()


class CustomRedirectTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.pip = Project.objects.create(**{
            'repo_type': 'git',
            'name': 'Pip',
            'default_branch': '',
            'project_url': 'http://pip.rtfd.org',
            'repo': 'https://github.com/fail/sauce',
            'default_version': LATEST,
            'privacy_level': 'public',
            'description': 'wat',
            'documentation_type': 'sphinx',
        })
        Redirect.objects.create(
            project=cls.pip,
            redirect_type='page',
            from_url='/install.html',
            to_url='/install.html#custom-fragment',
        )

    def test_redirect_fragment(self):
        redirect = Redirect.objects.get(project=self.pip)
        path = redirect.get_redirect_path('/install.html')
        expected_path = '/docs/pip/en/latest/install.html#custom-fragment'
        self.assertEqual(path, expected_path)


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False)
class RedirectBuildTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            versions=[fixture()],
        )
        self.version = self.project.versions.all()[0]

    def test_redirect_list(self):
        r = self.client.get('/builds/project-1/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], '/projects/project-1/builds/')

    def test_redirect_detail(self):
        r = self.client.get('/builds/project-1/1337/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], '/projects/project-1/builds/1337/')


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False)
class GetFullPathTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.proj = Project.objects.get(slug='read-the-docs')
        self.redirect = get(Redirect, project=self.proj)

    def test_http_filenames_return_themselves(self):
        # If the crossdomain flag is False (default), then we don't redirect to a different host
        self.assertEqual(
            self.redirect.get_full_path('http://rtfd.org'),
            '/docs/read-the-docs/en/latest/http://rtfd.org',
        )

        self.assertEqual(
            self.redirect.get_full_path('http://rtfd.org', allow_crossdomain=True),
            'http://rtfd.org',
        )

    def test_redirects_no_subdomain(self):
        self.assertEqual(
            self.redirect.get_full_path('index.html'),
            '/docs/read-the-docs/en/latest/index.html',
        )

    @override_settings(
        USE_SUBDOMAIN=True, PRODUCTION_DOMAIN='rtfd.org',
    )
    def test_redirects_with_subdomain(self):
        self.assertEqual(
            self.redirect.get_full_path('faq.html'),
            '/en/latest/faq.html',
        )

    @override_settings(
        USE_SUBDOMAIN=True, PRODUCTION_DOMAIN='rtfd.org',
    )
    def test_single_version_with_subdomain(self):
        self.redirect.project.single_version = True
        self.assertEqual(
            self.redirect.get_full_path('faq.html'),
            '/faq.html',
        )

    def test_single_version_no_subdomain(self):
        self.redirect.project.single_version = True
        self.assertEqual(
            self.redirect.get_full_path('faq.html'),
            '/docs/read-the-docs/faq.html',
        )
