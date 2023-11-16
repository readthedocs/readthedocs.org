from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.builds.constants import LATEST
from readthedocs.core.templatetags import core_tags
from readthedocs.projects.models import Project


@override_settings(PRODUCTION_DOMAIN="readthedocs.org", PUBLIC_DOMAIN="readthedocs.org")
class CoreTagsTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        url_base = "http://pip.{domain}{{version}}".format(
            domain=settings.PRODUCTION_DOMAIN,
        )

        self.pip_latest_url = url_base.format(version="/en/latest/")
        self.pip_latest_url_index = url_base.format(version="/en/latest/index.html")
        self.pip_latest_fr_url = url_base.format(version="/fr/latest/")
        self.pip_abc_url = url_base.format(version="/en/abc/")
        self.pip_abc_url_index = url_base.format(version="/en/abc/index.html")
        self.pip_abc_fr_url = url_base.format(version="/fr/abc/")
        self.pip_abc_fr_url_index = url_base.format(version="/fr/abc/index.html")
        self.pip_abc_xyz_page_url = url_base.format(version="/en/abc/xyz")
        self.pip_abc_xyz_fr_page_url = url_base.format(version="/fr/abc/xyz")
        self.pip_latest_document_url = url_base.format(version="/en/latest/document")
        self.pip_latest_document_page_url = url_base.format(
            version="/en/latest/document.html"
        )

        self.client.login(username="eric", password="test")
        self.pip = Project.objects.get(slug="pip")
        self.pip_fr = Project.objects.create(
            name="PIP-FR", slug="pip-fr", language="fr", main_language_project=self.pip
        )

    def test_project_only(self):
        proj = Project.objects.get(slug="pip")
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_url)
        url = core_tags.make_document_url(proj, "")
        self.assertEqual(url, self.pip_latest_url)

    def test_translation_project_only(self):
        proj = Project.objects.get(slug="pip-fr")
        url = core_tags.make_document_url(proj)
        self.assertEqual(url, self.pip_latest_fr_url)
        url = core_tags.make_document_url(proj, "")
        self.assertEqual(url, self.pip_latest_fr_url)

    def test_project_and_version(self):
        proj = Project.objects.get(slug="pip")
        url = core_tags.make_document_url(proj, "abc")
        self.assertEqual(url, self.pip_abc_url)
        url = core_tags.make_document_url(proj, "abc", "")
        self.assertEqual(url, self.pip_abc_url)

    def test_translation_project_and_version(self):
        proj = Project.objects.get(slug="pip-fr")
        url = core_tags.make_document_url(proj, "abc")
        self.assertEqual(url, self.pip_abc_fr_url)
        url = core_tags.make_document_url(proj, "abc", "")
        self.assertEqual(url, self.pip_abc_fr_url)

    def test_project_and_version_and_page(self):
        proj = Project.objects.get(slug="pip")
        url = core_tags.make_document_url(proj, "abc", "xyz")
        self.assertEqual(url, self.pip_abc_xyz_page_url)
        url = core_tags.make_document_url(proj, "abc", "index", "index.html")
        self.assertEqual(url, self.pip_abc_url_index)

    def test_translation_project_and_version_and_page(self):
        proj = Project.objects.get(slug="pip-fr")
        url = core_tags.make_document_url(proj, "abc", "xyz")
        self.assertEqual(url, self.pip_abc_xyz_fr_page_url)
        url = core_tags.make_document_url(proj, "abc", "index", "index.html")
        self.assertEqual(url, self.pip_abc_fr_url_index)

    def test_mkdocs(self):
        proj = Project.objects.get(slug="pip")
        url = core_tags.make_document_url(proj, LATEST, "document")
        self.assertEqual(url, self.pip_latest_document_url)

    def test_mkdocs_no_directory_urls(self):
        proj = Project.objects.get(slug="pip")
        url = core_tags.make_document_url(proj, LATEST, "document", "document.html")
        self.assertEqual(url, self.pip_latest_document_page_url)

    def test_mkdocs_index_no_directory_urls(self):
        proj = Project.objects.get(slug="pip")
        url = core_tags.make_document_url(proj, LATEST, "index", "index.html")
        self.assertEqual(url, self.pip_latest_url_index)

    def test_escapejson(self):
        tests = (
            ({}, "{}"),
            ({"a": "b"}, '{"a": "b"}'),
            ({"'; //": '""'}, '{"\'; //": "\\"\\""}'),
            (
                {"<script>alert('hi')</script>": ""},
                '{"\\u003Cscript\\u003Ealert(\'hi\')\\u003C/script\\u003E": ""}',
            ),
        )

        for in_value, out_value in tests:
            self.assertEqual(core_tags.escapejson(in_value), out_value)
