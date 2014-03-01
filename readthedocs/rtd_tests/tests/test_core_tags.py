from django.test import TestCase
from projects.models import Project
from builds.models import Version
from core.templatetags import core_tags

class CoreTagsTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.latest = Version.objects.create(project=self.pip, identifier='latest',
                               verbose_name='latest', slug='latest',
                               active=True)
        self.pip_fr = Project.objects.create(name="PIP-FR", slug='pip-fr', language='fr', main_language_project=self.pip)
        self.latest_fr = Version.objects.create(project=self.pip_fr, identifier='latest',
                               verbose_name='latest', slug='latest',
                               active=True)

    def test_project_only(self):
        proj = Project.objects.get(slug='pip')
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, '/docs/pip/en/latest/')
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, '/docs/pip/en/latest/')

    def test_project_only_htmldir(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, '/docs/pip/en/latest/')
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, '/docs/pip/en/latest/')

    def test_translation_project_only(self):
        proj = Project.objects.get(slug='pip-fr')
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, '/docs/pip/fr/latest/')
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, '/docs/pip/fr/latest/')

    def test_translation_project_only_htmldir(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, '/docs/pip/fr/latest/')
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, '/docs/pip/fr/latest/')


    def test_project_and_version(self):
        proj = Project.objects.get(slug='pip')
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, '/docs/pip/en/abc/')
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, '/docs/pip/en/abc/')

    def test_project_and_version_htmldir(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, '/docs/pip/en/abc/')
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, '/docs/pip/en/abc/')

    def test_translation_project_and_version(self):
        proj = Project.objects.get(slug='pip-fr')
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, '/docs/pip/fr/abc/')
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, '/docs/pip/fr/abc/')

    def test_translation_project_and_version_htmldir(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, '/docs/pip/fr/abc/')
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, '/docs/pip/fr/abc/')

    def test_project_and_version_and_page(self):
        proj = Project.objects.get(slug='pip')
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, '/docs/pip/en/abc/xyz.html')
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, '/docs/pip/en/abc/')

    def test_project_and_version_and_page_htmldir(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, '/docs/pip/en/abc/xyz/')
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, '/docs/pip/en/abc/')

    def test_translation_project_and_version_and_page(self):
        proj = Project.objects.get(slug='pip-fr')
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, '/docs/pip/fr/abc/xyz.html')
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, '/docs/pip/fr/abc/')

    def test_translation_project_and_version_and_page_htmldir(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, '/docs/pip/fr/abc/xyz/')
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, '/docs/pip/fr/abc/')

