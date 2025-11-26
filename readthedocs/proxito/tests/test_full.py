import os
from textwrap import dedent
from unittest import mock

import django_dynamic_fixture as fixture
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.test.utils import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.audit.models import AuditLog
from readthedocs.builds.constants import EXTERNAL, INTERNAL, LATEST
from readthedocs.builds.models import Version
from readthedocs.projects import constants
from readthedocs.projects.constants import (
    DOWNLOADABLE_MEDIA_TYPES,
    MEDIA_TYPE_HTMLZIP,
    MKDOCS,
    MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS,
    PRIVATE,
    PUBLIC,
    SINGLE_VERSION_WITHOUT_TRANSLATIONS,
    SPHINX,
    SPHINX_HTMLDIR,
    SPHINX_SINGLEHTML,
)
from readthedocs.projects.models import Domain, Feature, HTMLFile, Project
from readthedocs.redirects.models import Redirect
from readthedocs.rtd_tests.storage import (
    BuildMediaFileSystemStorageTest,
    StaticFileSystemStorageTest,
)
from readthedocs.subscriptions.constants import TYPE_AUDIT_PAGEVIEWS, TYPE_CNAME
from readthedocs.subscriptions.products import RTDProductFeature

from .base import BaseDocServing


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
class TestFullDocServing(BaseDocServing):
    # Test the full range of possible doc URL's

    def test_health_check(self):
        url = reverse("health_check")
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": 200})

        # Test with IP address, which should still work
        # since we're skipping middleware
        host = "127.0.0.1"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": 200})
        self.assertEqual(resp["CDN-Cache-Control"], "private")

    def test_subproject_serving(self):
        url = "/projects/subproject/en/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/awesome.html",
        )

    def test_subproject_single_version(self):
        self.subproject.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.subproject.save()
        url = "/projects/subproject/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/awesome.html",
        )

    def test_subproject_translation_serving(self):
        url = "/projects/subproject/es/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-translation/latest/awesome.html",
        )

    def test_subproject_alias_serving(self):
        url = "/projects/this-is-an-alias/en/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-alias/latest/awesome.html",
        )

    def test_translation_serving(self):
        url = "/es/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/awesome.html",
        )

    def test_translation_zh_deprecated_code_serving(self):
        self.translation.language = "zh"
        self.translation.save()
        url = "/zh/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/awesome.html",
        )

    def test_normal_serving(self):
        url = "/en/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/awesome.html",
        )

    def test_single_version_serving(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/awesome.html",
        )

    def test_single_version_serving_looks_like_normal(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/en/stable/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/en/stable/awesome.html",
        )

    def test_index_serving(self):
        host = "project.dev.readthedocs.io"
        urls = ("/en/latest/awesome/", "/en/latest/awesome/index.html")
        for url in urls:
            resp = self.client.get(url, headers={"host": host})
            self.assertEqual(
                resp["x-accel-redirect"],
                "/proxito/media/html/project/latest/awesome/index.html",
            )

    def test_single_version_external_serving(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = "/awesome.html"
        host = "project--10.dev.readthedocs.build"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/external/html/project/10/awesome.html",
        )

    def test_external_version_serving(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = "/en/10/awesome.html"
        host = "project--10.dev.readthedocs.build"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/external/html/project/10/awesome.html",
        )

    def test_external_version_serving_old_slugs(self):
        """
        Test external version serving with projects with `--` in their slug.

        Some old projects may have been created with a slug containg `--`,
        our current code doesn't allow these type of slugs.
        """
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        self.project.slug = "test--project"
        self.project.save()

        host = "test--project--10.dev.readthedocs.build"
        resp = self.client.get("/en/10/awesome.html", headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/external/html/test--project/10/awesome.html",
        )

    # Invalid tests

    def test_non_existent_version(self):
        url = "/en/non-existent-version/"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    def test_non_existent_version_with_filename(self):
        url = "/en/non-existent-version/doesnt-exist.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    def test_inactive_version(self):
        url = "/en/inactive/"
        host = "project.dev.readthedocs.io"
        fixture.get(
            Version,
            verbose_name="inactive",
            slug="inactive",
            active=False,
            project=self.project,
        )
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    def test_serve_external_version_on_main_domain(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = "/en/10/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["X-RTD-Project"], "project")
        self.assertEqual(resp["X-RTD-Version"], "10")

    def test_serve_non_external_version_on_external_domain(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = "/en/latest/awesome.html"
        host = "project--10.dev.readthedocs.build"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["X-RTD-Project"], "project")
        self.assertEqual(resp["X-RTD-Version"], "10")

    def test_serve_different_external_version_from_domain(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        fixture.get(
            Version,
            verbose_name="11",
            slug="11",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        url = "/en/11/awesome.html"
        host = "project--10.dev.readthedocs.build"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["X-RTD-Project"], "project")
        self.assertEqual(resp["X-RTD-Version"], "10")

    def test_invalid_language_for_project_with_versions(self):
        url = "/foo/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    def test_invalid_translation_for_project_with_versions(self):
        url = "/cs/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    def test_invalid_subproject(self):
        url = "/projects/doesnt-exist/foo.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    # https://github.com/readthedocs/readthedocs.org/pull/6226/files/596aa85a4886407f0eb65233ebf9c38ee3e8d485#r332445803
    def test_valid_project_as_invalid_subproject(self):
        url = "/projects/translation/es/latest/foo.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

    def test_public_domain_hsts(self):
        host = "project.dev.readthedocs.io"
        response = self.client.get("/", headers={"host": host})
        self.assertFalse("strict-transport-security" in response)

        response = self.client.get("/", headers={"host": host}, secure=True)
        self.assertFalse("strict-transport-security" in response)

        with override_settings(PUBLIC_DOMAIN_USES_HTTPS=True):
            response = self.client.get("/", headers={"host": host})
            self.assertFalse("strict-transport-security" in response)

            response = self.client.get("/", headers={"host": host}, secure=True)
            self.assertEqual(
                response["strict-transport-security"],
                "max-age=31536000; includeSubDomains; preload",
            )

    def test_custom_domain_response_hsts(self):
        hostname = "docs.random.com"
        domain = fixture.get(
            Domain,
            project=self.project,
            domain=hostname,
            hsts_max_age=0,
            hsts_include_subdomains=False,
            hsts_preload=False,
        )

        response = self.client.get("/", headers={"host": hostname})
        self.assertFalse("strict-transport-security" in response)

        response = self.client.get("/", headers={"host": hostname}, secure=True)
        self.assertFalse("strict-transport-security" in response)

        domain.hsts_max_age = 3600
        domain.save()

        response = self.client.get("/", headers={"host": hostname})
        self.assertFalse("strict-transport-security" in response)

        response = self.client.get("/", headers={"host": hostname}, secure=True)
        self.assertTrue("strict-transport-security" in response)
        self.assertEqual(
            response["strict-transport-security"],
            "max-age=3600",
        )

        domain.hsts_include_subdomains = True
        domain.hsts_preload = True
        domain.save()

        response = self.client.get("/", headers={"host": hostname}, secure=True)
        self.assertTrue("strict-transport-security" in response)
        self.assertEqual(
            response["strict-transport-security"],
            "max-age=3600; includeSubDomains; preload",
        )

    def test_single_version_serving_projects_dir(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/projects/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/projects/awesome.html",
        )

    def test_single_version_serving_language_like_subdir(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/en/api/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/en/api/awesome.html",
        )

    def test_single_version_serving_language_like_dir(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/en/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/en/awesome.html",
        )

    def test_multiple_versions_without_translations_serving(self):
        self.project.versioning_scheme = MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/awesome.html"
        )

    def test_multiple_versions_without_translations_serving_language_like_subdir(self):
        self.project.versioning_scheme = MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/en/api/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        self.version.slug = "en"
        self.version.save()
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/en/api/awesome.html",
        )

    def test_multiple_versions_without_translations_serving_subprojects_like_subdir(
        self,
    ):
        self.project.versioning_scheme = MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
        self.project.save()
        url = "/projects/api/awesome.html"
        host = "project.dev.readthedocs.io"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        self.version.slug = "projects"
        self.version.save()
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/projects/api/awesome.html",
        )

    def test_old_language_code(self):
        self.project.language = "pt-br"
        self.project.save()
        host = "project.dev.readthedocs.io"

        url = "/pt_BR/latest/index.html"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["location"],
            "http://project.dev.readthedocs.io/pt-br/latest/index.html",
        )

        url = "/pt-br/latest/index.html"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        # Ambiguous path.
        url = "/pt-br/latest/bt_BR/index.html"
        resp = self.client.get(url, headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/bt_BR/index.html",
        )


@override_settings(
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
class TestDocServingBackends(BaseDocServing):
    # Test that nginx and python backends both work

    @override_settings(PYTHON_MEDIA=True)
    def test_python_media_serving(self):
        with mock.patch(
            "readthedocs.proxito.views.mixins.serve", return_value=HttpResponse()
        ) as serve_mock:
            url = "/en/latest/awesome.html"
            host = "project.dev.readthedocs.io"
            self.client.get(url, headers={"host": host})
            serve_mock.assert_called_with(
                mock.ANY,
                "/media/html/project/latest/awesome.html",
                os.path.join(settings.SITE_ROOT, "media"),
            )

    @override_settings(PYTHON_MEDIA=False)
    def test_nginx_media_serving(self):
        resp = self.client.get(
            "/en/latest/awesome.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/awesome.html",
        )

    @override_settings(PYTHON_MEDIA=False)
    def test_project_nginx_serving_unicode_filename(self):
        resp = self.client.get(
            "/en/latest/úñíčódé.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/%C3%BA%C3%B1%C3%AD%C4%8D%C3%B3d%C3%A9.html",
        )

    @override_settings(PYTHON_MEDIA=False)
    def test_download_files_public_version(self):
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/en/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp["Cache-Tag"], "project,project:latest")
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/project/latest/project.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "public")

            # Translation
            resp = self.client.get(
                f"/_/downloads/es/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp["Cache-Tag"], "translation,translation:latest")
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/translation/latest/translation.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "public")

    @override_settings(PYTHON_MEDIA=False)
    def test_download_project_with_old_language_code(self):
        self.project.language = "pt-br"
        self.project.save()
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/pt_BR/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["Location"],
                f"//project.dev.readthedocs.io/_/downloads/pt-br/latest/{type_}/",
            )

            resp = self.client.get(
                f"/_/downloads/pt-br/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/project/latest/project.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "public")

    @override_settings(PYTHON_MEDIA=False, ALLOW_PRIVATE_REPOS=True)
    def test_download_files_private_version(self):
        self.version.privacy_level = PRIVATE
        self.version.save()
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/en/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp["Cache-Tag"], "project,project:latest")
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/project/latest/project.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "private")

    @override_settings(PYTHON_MEDIA=False)
    def test_invalid_download_files(self):
        """
        Making sure we don't serve HTML or other formats here.

        See GHSA-98pf-gfh3-x3mp for more information.
        """
        for type_ in ["html", "foo", "zip"]:
            resp = self.client.get(
                f"/_/downloads/en/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 404)

    @override_settings(PYTHON_MEDIA=False)
    def test_download_files_from_external_version(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/en/10/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 404)

    @override_settings(PYTHON_MEDIA=False)
    def test_download_files_from_external_version_from_main_domain(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/en/latest/{type_}/",
                headers={"host": "project--10.dev.readthedocs.build"},
            )
            self.assertEqual(resp.status_code, 404)

    @override_settings(PYTHON_MEDIA=False)
    def test_download_files_from_external_version(self):
        fixture.get(
            Version,
            verbose_name="10",
            slug="10",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/en/10/{type_}/",
                headers={"host": "project--10.dev.readthedocs.build"},
            )
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/external/{type_}/project/10/project.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "public")

    @override_settings(PYTHON_MEDIA=False)
    def test_download_files_from_external_version_unmatching_versions(self):
        fixture.get(
            Version,
            verbose_name="11",
            slug="11",
            type=EXTERNAL,
            active=True,
            project=self.project,
        )
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/en/11/{type_}/",
                headers={"host": "project--10.dev.readthedocs.build"},
            )
            self.assertEqual(resp.status_code, 404)

    @override_settings(PYTHON_MEDIA=False)
    def test_download_files_from_subproject(self):
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                f"/_/downloads/subproject/en/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/subproject/latest/subproject.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "public")

            # Translation
            resp = self.client.get(
                f"/_/downloads/subproject/es/latest/{type_}/",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/subproject-translation/latest/subproject-translation.{extension}",
            )
            self.assertEqual(resp["CDN-Cache-Control"], "public")

    @override_settings(PYTHON_MEDIA=False)
    def test_filename_with_parent_paths(self):
        """
        Ensure the project, version, and language match the request

        See GHSA-5w8m-r7jm-mhp9 for more information.
        """
        relative_paths = [
            # Retarget version, lang and version, and project
            "/en/latest/../target/awesome.html",
            "/en/latest/../../en/target/awesome.html",
            "/en/latest/../../../someproject/en/target/awesome.html",
            # Same, but with Windows path separators
            "/en/latest/..\\../en/target/awesome.html",
            "/en/latest/..\\..\\../someproject/en/target/awesome.html",
            "/en/latest/..\\../someproject/en/target/awesome.html",
            "/en/latest/..\\\\../en/target/awesome.html",
            "/en/latest/..\\\\..\\\\../someproject/en/target/awesome.html",
            "/en/latest/..\\\\../someproject/en/target/awesome.html",
        ]
        for _path in relative_paths:
            resp = self.client.get(
                _path, headers={"host": "project.dev.readthedocs.io"}
            )
            self.assertEqual(resp.status_code, 400)

    def test_track_html_files_only(self):
        self.assertEqual(AuditLog.objects.all().count(), 0)
        url = "/en/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        with override_settings(RTD_DEFAULT_FEATURES={}):
            resp = self.client.get(url, headers={"host": host})
        self.assertIn("x-accel-redirect", resp)
        self.assertEqual(AuditLog.objects.all().count(), 0)

        url = "/en/latest/awesome.html"
        host = "project.dev.readthedocs.io"
        with override_settings(
            RTD_DEFAULT_FEATURES=dict(
                [RTDProductFeature(type=TYPE_AUDIT_PAGEVIEWS).to_item()]
            )
        ):
            resp = self.client.get(url, headers={"host": host})
        self.assertIn("x-accel-redirect", resp)
        self.assertEqual(AuditLog.objects.all().count(), 1)

        log = AuditLog.objects.last()
        self.assertEqual(log.user, None)
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.resource, url)
        self.assertEqual(log.action, AuditLog.PAGEVIEW)

        with override_settings(
            RTD_DEFAULT_FEATURES=dict(
                [RTDProductFeature(type=TYPE_AUDIT_PAGEVIEWS).to_item()]
            )
        ):
            resp = self.client.get("/en/latest/awesome.js", headers={"host": host})
        self.assertIn("x-accel-redirect", resp)

        with override_settings(
            RTD_DEFAULT_FEATURES=dict(
                [RTDProductFeature(type=TYPE_AUDIT_PAGEVIEWS).to_item()]
            )
        ):
            resp = self.client.get("/en/latest/awesome.css", headers={"host": host})
        self.assertIn("x-accel-redirect", resp)
        self.assertEqual(AuditLog.objects.all().count(), 1)

    def test_track_downloads(self):
        self.project.versions.update(
            has_pdf=True,
            has_epub=True,
            has_htmlzip=True,
        )

        self.assertEqual(AuditLog.objects.all().count(), 0)
        url = "/_/downloads/en/latest/pdf/"
        host = "project.dev.readthedocs.io"
        with override_settings(
            RTD_DEFAULT_FEATURES=dict(
                [RTDProductFeature(type=TYPE_AUDIT_PAGEVIEWS).to_item()]
            )
        ):
            resp = self.client.get(url, headers={"host": host})
        self.assertIn("x-accel-redirect", resp)
        self.assertEqual(AuditLog.objects.all().count(), 1)

        log = AuditLog.objects.last()
        self.assertEqual(log.user, None)
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.resource, url)
        self.assertEqual(log.action, AuditLog.DOWNLOAD)


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
# We are overriding the storage class instead of using RTD_BUILD_MEDIA_STORAGE,
# since the setting is evaluated just once (first test to use the storage
# backend will set it for the whole test suite).
@mock.patch(
    "readthedocs.proxito.views.mixins.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
@mock.patch(
    "readthedocs.proxito.views.serve.build_media_storage",
    new=BuildMediaFileSystemStorageTest(),
)
class TestAdditionalDocViews(BaseDocServing):
    # Test that robots.txt and sitemap.xml work

    def tearDown(self):
        super().tearDown()
        # Cleanup cache to avoid throttling on tests
        cache.clear()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "exists")
    def test_default_robots_txt(self, storage_exists):
        storage_exists.return_value = False
        self.project.versions.update(active=True, built=True)
        response = self.client.get(
            reverse("robots_txt"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(response.status_code, 200)
        expected = dedent(
            """
            User-agent: *

            Disallow: # Allow everything

            Sitemap: https://project.readthedocs.io/sitemap.xml
            """
        ).lstrip()
        self.assertContains(response, expected)

    @mock.patch.object(BuildMediaFileSystemStorageTest, "exists")
    def test_default_robots_txt_disallow_hidden_versions(self, storage_exists):
        storage_exists.return_value = False
        self.project.versions.update(active=True, built=True)
        fixture.get(
            Version,
            project=self.project,
            slug="hidden",
            active=True,
            hidden=True,
            privacy_level=PUBLIC,
        )
        fixture.get(
            Version,
            project=self.project,
            slug="hidden-2",
            active=True,
            hidden=True,
            privacy_level=PUBLIC,
        )
        fixture.get(
            Version,
            project=self.project,
            slug="hidden-and-inactive",
            active=False,
            hidden=True,
            privacy_level=PUBLIC,
        )
        fixture.get(
            Version,
            project=self.project,
            slug="hidden-and-private",
            active=False,
            hidden=True,
            privacy_level=PRIVATE,
        )

        response = self.client.get(
            reverse("robots_txt"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(response.status_code, 200)
        expected = dedent(
            """
            User-agent: *

            Disallow: /en/hidden-2/ # Hidden version

            Disallow: /en/hidden/ # Hidden version

            Sitemap: https://project.readthedocs.io/sitemap.xml
            """
        ).lstrip()
        self.assertContains(response, expected)

    @mock.patch.object(BuildMediaFileSystemStorageTest, "exists")
    def test_default_robots_txt_private_version(self, storage_exists):
        storage_exists.return_value = False
        self.project.versions.update(
            active=True, built=True, privacy_level=constants.PRIVATE
        )
        response = self.client.get(
            reverse("robots_txt"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(response.status_code, 404)

    def test_custom_robots_txt(self):
        self.project.versions.update(active=True, built=True)
        response = self.client.get(
            reverse("robots_txt"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(
            response["x-accel-redirect"],
            "/proxito/media/html/project/latest/robots.txt",
        )

    def test_custom_robots_txt_private_version(self):
        self.project.versions.update(
            active=True, built=True, privacy_level=constants.PRIVATE
        )
        response = self.client.get(
            reverse("robots_txt"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(response.status_code, 404)

    def test_directory_indexes(self):
        self.project.versions.update(active=True, built=True)

        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path="index-exists/index.html",
            name="index.html",
        )

        # Confirm we've serving from storage for the `index-exists/index.html` file
        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/latest/index-exists"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["location"],
            "/en/latest/index-exists/",
        )

    def test_versioned_no_slash(self):
        self.project.versions.update(active=True, built=True)
        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path="index.html",
            name="index.html",
        )
        response = self.client.get(
            reverse("proxito_404_handler", kwargs={"proxito_path": "/en/latest"}),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["location"],
            "/en/latest/",
        )

    def test_directory_indexes_get_args(self):
        self.project.versions.update(active=True, built=True)
        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path="index-exists/index.html",
            name="index.html",
        )
        # Confirm we've serving from storage for the `index-exists/index.html` file
        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/latest/index-exists"},
            )
            + "?foo=bar",
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["location"],
            "/en/latest/index-exists/?foo=bar",
        )

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_storage_serves_custom_404_sphinx(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX,
        )

        get(
            HTMLFile,
            project=self.project,
            version=fancy_version,
            path="404.html",
            name="404.html",
        )

        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_called_once_with("html/project/fancy-version/404.html")

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_index_redirect_skips_not_built_versions(self, storage_open):
        self.version.built = False
        self.version.save()
        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path="foo/index.html",
            name="index.html",
        )

        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/latest/foo"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_custom_404_skips_not_built_versions(self, storage_open):
        self.version.built = False
        self.version.save()

        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=False,
            project=self.project,
        )

        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path="404.html",
            name="404.html",
        )

        get(
            HTMLFile,
            project=self.project,
            version=fancy_version,
            path="404.html",
            name="404.html",
        )

        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_custom_404_doesnt_exist_in_storage(self, storage_open):
        storage_open.side_effect = FileNotFoundError
        get(
            HTMLFile,
            project=self.project,
            version=self.version,
            path="404.html",
            name="404.html",
        )
        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/latest/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_called_once_with("html/project/latest/404.html")

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_storage_serves_custom_404_sphinx_single_html(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX_SINGLEHTML,
        )

        get(
            HTMLFile,
            project=self.project,
            version=fancy_version,
            path="404.html",
            name="404.html",
        )

        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_called_once_with("html/project/fancy-version/404.html")

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_storage_serves_custom_404_sphinx_htmldir(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX_HTMLDIR,
        )

        get(
            HTMLFile,
            project=self.project,
            version=fancy_version,
            path="404.html",
            name="404.html",
        )
        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_called_once_with("html/project/fancy-version/404.html")

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_storage_serves_custom_404_mkdocs(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=MKDOCS,
        )

        get(
            HTMLFile,
            project=self.project,
            version=fancy_version,
            path="404.html",
            name="404.html",
        )

        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)
        storage_open.assert_called_once_with("html/project/fancy-version/404.html")

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_all_paths_checked_sphinx(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX,
        )
        latest = self.project.versions.get(slug=LATEST)
        latest.documentation_type = SPHINX
        latest.save()

        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_all_paths_checked_sphinx_single_html(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX_SINGLEHTML,
        )
        latest = self.project.versions.get(slug=LATEST)
        latest.documentation_type = SPHINX_SINGLEHTML
        latest.save()

        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_all_paths_checked_sphinx_html_dir(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX_HTMLDIR,
        )
        latest = self.project.versions.get(slug=LATEST)
        latest.documentation_type = SPHINX_HTMLDIR
        latest.save()

        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_all_paths_checked_mkdocs(self, storage_open):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=MKDOCS,
        )
        latest = self.project.versions.get(slug=LATEST)
        latest.documentation_type = MKDOCS
        latest.save()

        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)
        storage_open.assert_not_called()

    @mock.patch.object(BuildMediaFileSystemStorageTest, "open")
    def test_404_all_paths_checked_default_version_different_doc_type(
        self, storage_open
    ):
        self.project.versions.update(active=True, built=True)
        fancy_version = fixture.get(
            Version,
            slug="fancy-version",
            privacy_level=constants.PUBLIC,
            active=True,
            built=True,
            project=self.project,
            documentation_type=SPHINX,
        )
        latest = self.project.versions.get(slug=LATEST)
        latest.documentation_type = SPHINX_HTMLDIR
        latest.save()

        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/fancy-version/not-found"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)
        storage_open.assert_not_called()

    def test_sitemap_xml(self):
        self.project.versions.update(active=True)
        private_version = fixture.get(
            Version,
            privacy_level=constants.PRIVATE,
            project=self.project,
        )
        not_translated_public_version = fixture.get(
            Version,
            identifier="not-translated-version",
            verbose_name="not-translated-version",
            slug="not-translated-version",
            privacy_level=constants.PUBLIC,
            project=self.project,
            active=True,
        )
        stable_version = fixture.get(
            Version,
            identifier="stable",
            verbose_name="stable",
            slug="stable",
            privacy_level=constants.PUBLIC,
            project=self.project,
            active=True,
        )
        # This is a EXTERNAL Version
        external_version = fixture.get(
            Version,
            identifier="pr-version",
            verbose_name="pr-version",
            slug="pr-9999",
            project=self.project,
            active=True,
            type=EXTERNAL,
        )

        hidden_version = fixture.get(
            Version,
            identifier="hidden-version",
            verbose_name="hidden-version",
            slug="hidden-version",
            privacy_level=constants.PUBLIC,
            project=self.project,
            active=True,
            hidden=True,
        )
        # This also creates a Version `latest` Automatically for this project
        translation = fixture.get(
            Project,
            main_language_project=self.project,
            language="translation-es",
            privacy_level=constants.PUBLIC,
        )
        translation.versions.update(privacy_level=constants.PUBLIC)
        # sitemap hreflang should follow correct format.
        # ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
        hreflang_test_translation_project = fixture.get(
            Project,
            main_language_project=self.project,
            language="zh_CN",
            privacy_level=constants.PUBLIC,
        )
        hreflang_test_translation_project.versions.update(
            privacy_level=constants.PUBLIC,
        )

        response = self.client.get(
            reverse("sitemap_xml"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        for version in self.project.versions(manager=INTERNAL).filter(
            privacy_level=constants.PUBLIC,
            hidden=False,
        ):
            self.assertContains(
                response,
                self.project.get_docs_url(
                    version_slug=version.slug,
                    lang_slug=self.project.language,
                ),
            )

        # PRIVATE version should not appear here
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=private_version.slug,
                lang_slug=self.project.language,
            ),
        )

        # Hidden version should not appear here
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=hidden_version.slug,
                lang_slug=self.project.language,
            ),
        )

        # The `translation` project doesn't have a version named `not-translated-version`
        # so, the sitemap should not have a doc url for
        # `not-translated-version` with `translation-es` language.
        # ie: http://project.readthedocs.io/translation-es/not-translated-version/
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=not_translated_public_version.slug,
                lang_slug=translation.language,
            ),
        )
        # hreflang should use hyphen instead of underscore
        # in language and country value. (zh_CN should be zh-CN)
        self.assertContains(response, "zh-CN")

        # External Versions should not be in the sitemap_xml.
        self.assertNotContains(
            response,
            self.project.get_docs_url(
                version_slug=external_version.slug,
                lang_slug=self.project.language,
            ),
        )

        # Check if STABLE version has 'priority of 1 and changefreq of weekly.
        self.assertEqual(
            response.context["versions"][0]["loc"],
            self.project.get_docs_url(
                version_slug=stable_version.slug,
                lang_slug=self.project.language,
            ),
        )
        self.assertEqual(response.context["versions"][0]["priority"], 1)
        self.assertEqual(response.context["versions"][0]["changefreq"], "weekly")

        # Check if LATEST version has priority of 0.9 and changefreq of daily.
        self.assertEqual(
            response.context["versions"][1]["loc"],
            self.project.get_docs_url(
                version_slug="latest",
                lang_slug=self.project.language,
            ),
        )
        self.assertEqual(response.context["versions"][1]["priority"], 0.9)
        self.assertEqual(response.context["versions"][1]["changefreq"], "daily")

    def test_sitemap_all_private_versions(self):
        self.project.versions.update(
            active=True, built=True, privacy_level=constants.PRIVATE
        )
        response = self.client.get(
            reverse("sitemap_xml"), headers={"host": "project.readthedocs.io"}
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch(
        "readthedocs.proxito.views.mixins.staticfiles_storage",
        new=StaticFileSystemStorageTest(),
    )
    def test_serve_static_files(self):
        resp = self.client.get(
            reverse(
                "proxito_static_files",
                args=["javascript/readthedocs-doc-embed.js"],
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["x-accel-redirect"],
            "/proxito-static/media/javascript/readthedocs-doc-embed.js",
        )
        self.assertEqual(
            resp.headers["Cache-Tag"], "project,project:rtd-staticfiles,rtd-staticfiles"
        )

    @mock.patch(
        "readthedocs.proxito.views.mixins.staticfiles_storage",
        new=StaticFileSystemStorageTest(),
    )
    def test_serve_static_files_internal_nginx_redirect_always_appended(self):
        """Test for #11080."""
        resp = self.client.get(
            reverse(
                "proxito_static_files",
                args=["proxito-static/javascript/readthedocs-doc-embed.js"],
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["x-accel-redirect"],
            "/proxito-static/media/proxito-static/javascript/readthedocs-doc-embed.js",
        )
        self.assertEqual(
            resp.headers["Cache-Tag"], "project,project:rtd-staticfiles,rtd-staticfiles"
        )

    @mock.patch("readthedocs.proxito.views.mixins.staticfiles_storage")
    def test_serve_invalid_static_file(self, staticfiles_storage):
        staticfiles_storage.url.side_effect = Exception
        paths = ["../", "foo/../bar"]
        for path in paths:
            resp = self.client.get(
                reverse(
                    "proxito_static_files",
                    args=[path],
                ),
                headers={"host": "project.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 404)

    def test_404_download(self):
        response = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/_/downloads/en/latest/pdf/"},
            ),
            headers={"host": "project.readthedocs.io"},
        )
        self.assertEqual(response.status_code, 404)


@override_settings(
    ALLOW_PRIVATE_REPOS=True,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    PUBLIC_DOMAIN_USES_HTTPS=True,
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(type=TYPE_CNAME, value=2).to_item()]),
)
# We are overriding the storage class instead of using RTD_BUILD_MEDIA_STORAGE,
# since the setting is evaluated just once (first test to use the storage
# backend will set it for the whole test suite).
@mock.patch(
    "readthedocs.proxito.views.mixins.staticfiles_storage",
    new=StaticFileSystemStorageTest(),
)
class TestCDNCache(BaseDocServing):
    def _test_cache_control_header_project(self, expected_value, host=None):
        """
        Test the CDN-Cache-Control header on requests for `self.project`.

        :param expected_value: The expected value of the header: 'public' or 'private'.
        :param host: Hostname to use in the requests.
        """
        host = host or "project.dev.readthedocs.io"

        # Normal serving.
        urls = [
            "/en/latest/",
            "/en/latest/foo.html",
        ]
        for url in urls:
            resp = self.client.get(url, secure=True, headers={"host": host})
            self.assertEqual(resp.headers["CDN-Cache-Control"], expected_value, url)
            self.assertEqual(resp.headers["Cache-Tag"], "project,project:latest", url)

        # Page & system redirects are always cached.
        # Authz is done on the redirected URL.
        location = f"https://{host}/en/latest/"
        urls = [
            ["", location],
            ["/", location],
            ["/page/foo.html", f"https://{host}/en/latest/foo.html"],
        ]
        for url, location in urls:
            resp = self.client.get(url, secure=True, headers={"host": host})
            self.assertEqual(resp["Location"], location, url)
            self.assertEqual(resp.headers["CDN-Cache-Control"], "public", url)
            self.assertEqual(resp.headers["Cache-Tag"], "project", url)

        # Proxied static files are always cached.
        resp = self.client.get("/_/static/file.js", secure=True, headers={"host": host})
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(
            resp.headers["Cache-Tag"], "project,project:rtd-staticfiles,rtd-staticfiles"
        )

        # Slash redirects can always be cached.
        url = "/en//latest//"
        resp = self.client.get(url, secure=True, headers={"host": host})
        self.assertEqual(resp["Location"], "/en/latest/", url)
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public", url)
        self.assertEqual(resp.headers["Cache-Tag"], "project")

        # Forced redirects will be cached only if the version is public.
        get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            force=True,
        )
        url = "/en/latest/install.html"
        resp = self.client.get(url, secure=True, headers={"host": host})
        self.assertEqual(
            resp["Location"], f"https://{host}/en/latest/tutorial/install.html", url
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], expected_value, url)
        self.assertEqual(resp.headers["Cache-Tag"], "project,project:latest", url)

    def _test_cache_control_header_subproject(self, expected_value, host=None):
        """
        Test the CDN-Cache-Control header on requests for `self.subproject`.

        :param expected_value: The expected value of the header: 'public' or 'private'.
        :param host: Hostname to use in the requests.
        """
        host = host or "project.dev.readthedocs.io"

        # Normal serving.
        urls = [
            "/projects/subproject/en/latest/",
            "/projects/subproject/en/latest/foo.html",
        ]
        for url in urls:
            resp = self.client.get(url, secure=True, headers={"host": host})
            self.assertEqual(resp.headers["CDN-Cache-Control"], expected_value, url)
            self.assertEqual(
                resp.headers["Cache-Tag"], "subproject,subproject:latest", url
            )

        # Page & system redirects are always cached.
        # Authz is done on the redirected URL.
        location = f"https://{host}/projects/subproject/en/latest/"
        urls = [
            ["/projects/subproject", location],
            ["/projects/subproject/", location],
        ]
        for url, location in urls:
            resp = self.client.get(url, secure=True, headers={"host": host})
            self.assertEqual(resp["Location"], location, url)
            self.assertEqual(resp.headers["CDN-Cache-Control"], "public", url)
            self.assertEqual(resp.headers["Cache-Tag"], "subproject", url)

        # Proxied static files are always cached.
        resp = self.client.get("/_/static/file.js", secure=True, headers={"host": host})
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(
            resp.headers["Cache-Tag"], "project,project:rtd-staticfiles,rtd-staticfiles"
        )

        # Slash redirects can always be cached.
        url = "/projects//subproject//"
        resp = self.client.get(url, secure=True, headers={"host": host})
        self.assertEqual(resp["Location"], "/projects/subproject/", url)
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public", url)
        self.assertEqual(resp.headers["Cache-Tag"], "project")

    def test_cache_on_private_versions(self):
        self.project.versions.update(privacy_level=PRIVATE)
        self._test_cache_control_header_project(expected_value="private")

    def test_cache_on_private_versions_custom_domain(self):
        self.project.versions.update(privacy_level=PRIVATE)
        self.domain.canonical = True
        self.domain.save()
        self._test_cache_control_header_project(
            expected_value="private", host=self.domain.domain
        )

        # HTTPS redirects can always be cached.
        resp = self.client.get(
            "/en/latest/", secure=False, headers={"host": self.domain.domain}
        )
        self.assertEqual(resp["Location"], f"https://{self.domain.domain}/en/latest/")
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

    def test_cache_public_versions(self):
        self.project.versions.update(privacy_level=PUBLIC)
        self._test_cache_control_header_project(expected_value="public")

    def test_cache_public_versions_custom_domain(self):
        self.project.versions.update(privacy_level=PUBLIC)
        self.domain.canonical = True
        self.domain.save()
        self._test_cache_control_header_project(
            expected_value="public", host=self.domain.domain
        )

        # HTTPS redirect respects the privacy level of the version.
        resp = self.client.get(
            "/en/latest/", secure=False, headers={"host": self.domain.domain}
        )
        self.assertEqual(resp["Location"], f"https://{self.domain.domain}/en/latest/")
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project,project:latest")

    def test_cache_on_private_versions_subproject(self):
        self.subproject.versions.update(privacy_level=PRIVATE)
        self._test_cache_control_header_subproject(expected_value="private")

    def test_cache_on_private_versions_custom_domain_subproject(self):
        self.subproject.versions.update(privacy_level=PRIVATE)
        self.domain.canonical = True
        self.domain.save()
        self._test_cache_control_header_subproject(
            expected_value="private", host=self.domain.domain
        )

        # HTTPS redirects can always be cached.
        resp = self.client.get(
            "/projects/subproject/en/latest/",
            secure=False,
            headers={"host": self.domain.domain},
        )
        self.assertEqual(
            resp["Location"],
            f"https://{self.domain.domain}/projects/subproject/en/latest/",
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

    def test_cache_public_versions_subproject(self):
        self.subproject.versions.update(privacy_level=PUBLIC)
        self._test_cache_control_header_subproject(expected_value="public")

    def test_cache_public_versions_custom_domain(self):
        self.subproject.versions.update(privacy_level=PUBLIC)
        self.domain.canonical = True
        self.domain.save()
        self._test_cache_control_header_subproject(
            expected_value="public", host=self.domain.domain
        )

        # HTTPS redirects can always be cached.
        resp = self.client.get(
            "/projects/subproject/en/latest/",
            secure=False,
            headers={"host": self.domain.domain},
        )
        self.assertEqual(
            resp["Location"],
            f"https://{self.domain.domain}/projects/subproject/en/latest/",
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "public")
        self.assertEqual(resp.headers["Cache-Tag"], "project")

    def test_cache_disable_on_rtd_header_resolved_project(self):
        get(
            Feature,
            feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER,
            projects=[self.project],
        )
        resp = self.client.get(
            "/en/latest/index.html",
            secure=True,
            headers={"host": "docs.example.com", "x-rtd-slug": self.project.slug},
        )
        self.assertEqual(resp.headers["CDN-Cache-Control"], "private")
        self.assertEqual(resp.headers["Cache-Tag"], "project,project:latest")
