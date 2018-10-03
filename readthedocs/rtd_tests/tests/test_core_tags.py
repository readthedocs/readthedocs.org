# -*- coding: utf-8 -*-
from __future__ import absolute_import
import mock
import pytest

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import Project
from readthedocs.builds.constants import LATEST
from readthedocs.core.templatetags import core_tags


@override_settings(USE_SUBDOMAIN=False, PRODUCTION_DOMAIN='readthedocs.org')
class CoreTagsTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        url_base = '{scheme}://{domain}/docs/pip{{version}}'.format(
            scheme=pytest.config.option.url_scheme,
            domain=settings.PRODUCTION_DOMAIN,
        )

        self.pip_latest_url = url_base.format(version='/en/latest/')
        self.pip_latest_fr_url = url_base.format(version='/fr/latest/')
        self.pip_abc_url = url_base.format(version='/en/abc/')
        self.pip_abc_fr_url = url_base.format(version='/fr/abc/')
        self.pip_abc_xyz_page_url = url_base.format(version='/en/abc/xyz.html')
        self.pip_abc_xyz_fr_page_url = url_base.format(version='/fr/abc/xyz.html')
        self.pip_abc_xyz_dir_url = url_base.format(version='/en/abc/xyz/')
        self.pip_abc_xyz_fr_dir_url = url_base.format(version='/fr/abc/xyz/')
        self.pip_abc_xyz_document = url_base.format(version='/en/abc/index.html#document-xyz')
        self.pip_abc_xyz_fr_document = url_base.format(version='/fr/abc/index.html#document-xyz')
        self.pip_latest_document_url = url_base.format(version='/en/latest/document/')
        self.pip_latest_document_page_url = url_base.format(version='/en/latest/document.html')

        with mock.patch('readthedocs.projects.models.broadcast'):
            self.client.login(username='eric', password='test')
            self.pip = Project.objects.get(slug='pip')
            self.pip_fr = Project.objects.create(name="PIP-FR", slug='pip-fr', language='fr', main_language_project=self.pip)

    def test_project_only(self):
        proj = Project.objects.get(slug='pip')
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_url)
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, self.pip_latest_url)

    def test_project_only_htmldir(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_url)
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, self.pip_latest_url)

    def test_project_only_singlehtml(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_singlehtml'
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_url)
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, self.pip_latest_url)

    def test_translation_project_only(self):
        proj = Project.objects.get(slug='pip-fr')
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_fr_url)
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, self.pip_latest_fr_url)

    def test_translation_project_only_htmldir(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_fr_url)
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, self.pip_latest_fr_url)

    def test_translation_project_only_singlehtml(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_singlehtml'
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_fr_url)
        url = core_tags.make_document_url(proj, '')
        self.assertEqual(url, self.pip_latest_fr_url)

    def test_project_and_version(self):
        proj = Project.objects.get(slug='pip')
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, self.pip_abc_url)
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, self.pip_abc_url)

    def test_project_and_version_htmldir(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, self.pip_abc_url)
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, self.pip_abc_url)

    def test_project_and_version_singlehtml(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_singlehtml'
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, self.pip_abc_url)
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, self.pip_abc_url)

    def test_translation_project_and_version(self):
        proj = Project.objects.get(slug='pip-fr')
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, self.pip_abc_fr_url)
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_translation_project_and_version_htmldir(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, self.pip_abc_fr_url)
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_translation_project_and_version_singlehtml(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_singlehtml'
        url = core_tags.make_document_url(proj, 'abc')
        self.assertEqual(url, self.pip_abc_fr_url)
        url = core_tags.make_document_url(proj, 'abc', '')
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_project_and_version_and_page(self):
        proj = Project.objects.get(slug='pip')
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, self.pip_abc_xyz_page_url)
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, self.pip_abc_url)

    def test_project_and_version_and_page_htmldir(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, self.pip_abc_xyz_dir_url)
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, self.pip_abc_url)

    def test_project_and_version_and_page_signlehtml(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'sphinx_singlehtml'
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, self.pip_abc_xyz_document)
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, self.pip_abc_url)

    def test_translation_project_and_version_and_page(self):
        proj = Project.objects.get(slug='pip-fr')
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, self.pip_abc_xyz_fr_page_url)
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_translation_project_and_version_and_page_htmldir(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_htmldir'
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, self.pip_abc_xyz_fr_dir_url)
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_translation_project_and_version_and_page_singlehtml(self):
        proj = Project.objects.get(slug='pip-fr')
        proj.documentation_type = 'sphinx_singlehtml'
        url = core_tags.make_document_url(proj, 'abc', 'xyz')
        self.assertEqual(url, self.pip_abc_xyz_fr_document)
        url = core_tags.make_document_url(proj, 'abc', 'index')
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_mkdocs(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'mkdocs'
        url = core_tags.make_document_url(proj, LATEST, 'document')
        self.assertEqual(url, self.pip_latest_document_url)

    def test_mkdocs_no_directory_urls(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'mkdocs'
        url = core_tags.make_document_url(proj, LATEST, 'document.html')
        self.assertEqual(url, self.pip_latest_document_page_url)

    def test_mkdocs_index(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'mkdocs'
        url = core_tags.make_document_url(proj, LATEST, 'index')
        self.assertEqual(url, self.pip_latest_url)

    def test_mkdocs_index_no_directory_urls(self):
        proj = Project.objects.get(slug='pip')
        proj.documentation_type = 'mkdocs'
        url = core_tags.make_document_url(proj, LATEST, 'index.html')
        self.assertEqual(url, self.pip_latest_url)

    def test_restructured_text(self):
        value = '*test*'
        result = core_tags.restructuredtext(value)
        self.assertIn('<em>test</em>', result)

    def test_restructured_text_invalid(self):
        value = (
            '*******\n'
            'Test\n'
            '****\n\n'
        )
        result = core_tags.restructuredtext(value)
        self.assertEqual(result, value)
