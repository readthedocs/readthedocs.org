from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import fixture, get

from readthedocs.builds.constants import LATEST
from readthedocs.projects.constants import SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


class CustomRedirectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pip = Project.objects.create(
            **{
                "repo_type": "git",
                "name": "Pip",
                "default_branch": "",
                "project_url": "http://pip.rtfd.org",
                "repo": "https://github.com/fail/sauce",
                "default_version": LATEST,
                "privacy_level": "public",
                "description": "wat",
                "documentation_type": "sphinx",
            }
        )
        Redirect.objects.create(
            project=cls.pip,
            redirect_type="page",
            from_url="/install.html",
            to_url="/install.html#custom-fragment",
        )

    def test_redirect_fragment(self):
        redirect = Redirect.objects.get(project=self.pip)
        path = redirect.get_redirect_path("/install.html")
        expected_path = "/en/latest/install.html#custom-fragment"
        self.assertEqual(path, expected_path)


@override_settings(PUBLIC_DOMAIN="readthedocs.org")
class RedirectBuildTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.project = get(
            Project,
            slug="project-1",
            documentation_type="sphinx",
            conf_py_file="test_conf.py",
            versions=[fixture()],
        )
        self.version = self.project.versions.all()[0]

    def test_redirect_list(self):
        r = self.client.get("/builds/project-1/")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/projects/project-1/builds/")

    def test_redirect_detail(self):
        r = self.client.get("/builds/project-1/1337/")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/projects/project-1/builds/1337/")


@override_settings(PUBLIC_DOMAIN="readthedocs.org")
class GetFullPathTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.proj = Project.objects.get(slug="read-the-docs")
        self.redirect = get(Redirect, project=self.proj)

    def test_http_filenames_return_themselves(self):
        # If the crossdomain flag is False (default), then we don't redirect to a different host
        self.assertEqual(
            self.redirect.get_full_path("http://rtfd.org"),
            "/en/latest/http://rtfd.org",
        )

        self.assertEqual(
            self.redirect.get_full_path("http://rtfd.org", allow_crossdomain=True),
            "http://rtfd.org",
        )

    def test_redirects_no_subdomain(self):
        self.assertEqual(
            self.redirect.get_full_path("index.html"),
            "/en/latest/index.html",
        )

    @override_settings(
        PRODUCTION_DOMAIN="rtfd.org",
    )
    def test_redirects_with_subdomain(self):
        self.assertEqual(
            self.redirect.get_full_path("faq.html"),
            "/en/latest/faq.html",
        )

    @override_settings(
        PRODUCTION_DOMAIN="rtfd.org",
    )
    def test_single_version_with_subdomain(self):
        self.redirect.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.assertEqual(
            self.redirect.get_full_path("faq.html"),
            "/faq.html",
        )

    def test_single_version_no_subdomain(self):
        self.redirect.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.assertEqual(
            self.redirect.get_full_path("faq.html"),
            "/faq.html",
        )
