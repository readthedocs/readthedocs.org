from django.test.utils import override_settings

from readthedocs.projects.constants import (
    MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS,
    SINGLE_VERSION_WITHOUT_TRANSLATIONS,
)
from readthedocs.proxito.tests.base import BaseDocServing


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="readthedocs.build",
)
class TestCustomPathPrefixes(BaseDocServing):
    def test_custom_prefix_multi_version_project(self):
        self.project.custom_prefix = "/custom/prefix/"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect.
        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Trailing slash redirect
        resp = self.client.get("/custom/prefix/en/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/prefix/en/latest/"
        )

        resp = self.client.get("/custom/prefix/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        resp = self.client.get(
            "/custom/prefix/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/api/index.html",
        )

    def test_custom_prefix_multi_version_project_translation(self):
        self.project.custom_prefix = "/custom/prefix/"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/es/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Trailing slash redirect
        resp = self.client.get("/custom/prefix/es/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/prefix/es/latest/"
        )

        resp = self.client.get("/custom/prefix/es/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/index.html",
        )

        resp = self.client.get(
            "/custom/prefix/es/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/api/index.html",
        )

    def test_custom_prefix_single_version_project(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.custom_prefix = "/custom-prefix/"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/"
        )

        # Trailing slash redirect
        resp = self.client.get("/custom-prefix", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/"
        )

        resp = self.client.get("/custom-prefix/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        resp = self.client.get("/custom-prefix/api/index.html", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/api/index.html",
        )

    def test_custom_prefix_multiple_versions_without_translations_project(self):
        self.project.versioning_scheme = MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
        self.project.custom_prefix = "/custom-prefix/"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect.
        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/latest/"
        )

        # Root prefix redirect.
        resp = self.client.get("/custom-prefix/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/latest/"
        )

        # Trailing slash redirect
        resp = self.client.get("/custom-prefix/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/latest/"
        )

        resp = self.client.get("/custom-prefix/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        resp = self.client.get(
            "/custom-prefix/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/api/index.html",
        )

    def test_custom_subproject_prefix(self):
        self.project.custom_subproject_prefix = "/custom/"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/en/latest/")

        # Serving works on the main project.
        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", headers={"host": "subproject.readthedocs.io"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/subproject/"
        )

        resp = self.client.get(
            "/en/latest/", headers={"host": "subproject.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/en/latest/",
        )

        # Old paths
        resp = self.client.get("/projects/subproject/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get("/projects/subproject/en/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Root redirect for the subproject
        resp = self.client.get("/custom/subproject", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/en/latest/",
        )

        resp = self.client.get("/custom/subproject/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/en/latest/",
        )

        # Trailing slash redirect
        resp = self.client.get("/custom/subproject/en/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/en/latest/",
        )

        # Normal serving
        resp = self.client.get("/custom/subproject/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/custom/subproject/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_custom_subproject_prefix_empty(self):
        self.project.custom_subproject_prefix = "/"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/en/latest/")

        # Serving works on the main project.
        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", headers={"host": "subproject.readthedocs.io"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/subproject/")

        resp = self.client.get(
            "/en/latest/", headers={"host": "subproject.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        # Root redirect for the subproject
        resp = self.client.get("/subproject", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        resp = self.client.get("/subproject/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        # Trailing slash redirect
        resp = self.client.get("/subproject/en/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        # Normal serving
        resp = self.client.get("/subproject/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/subproject/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_custom_prefix_and_custom_subproject_prefix_in_superproject(self):
        self.project.custom_prefix = "/prefix/"
        self.project.custom_subproject_prefix = "/s/"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", headers={"host": "subproject.readthedocs.io"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/"
        )

        resp = self.client.get(
            "/en/latest/", headers={"host": "subproject.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Root redirect for the subproject
        resp = self.client.get("/s/subproject", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        resp = self.client.get("/s/subproject/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Trailing slash redirect
        resp = self.client.get("/s/subproject/en/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Normal serving
        resp = self.client.get("/s/subproject/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/s/subproject/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_custom_prefix_and_custom_subproject_prefix_with_translations(self):
        self.project.custom_prefix = "/prefix/"
        self.project.custom_subproject_prefix = "/s/"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/es/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/es/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/index.html",
        )

        # Normal serving
        resp = self.client.get("/s/subproject/es/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-translation/latest/index.html",
        )

        resp = self.client.get(
            "/s/subproject/es/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-translation/latest/api/index.html",
        )

    def test_custom_prefix_in_subproject_and_custom_prefix_in_superproject(self):
        self.subproject.custom_prefix = "/prefix/"
        self.subproject.save()
        self.project.custom_subproject_prefix = "/s/"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/en/latest/")

        # Serving works on the main project.
        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", headers={"host": "subproject.readthedocs.io"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/"
        )

        resp = self.client.get(
            "/en/latest/", headers={"host": "subproject.readthedocs.io"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Root redirect for the subproject
        resp = self.client.get("/s/subproject", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/s/subproject/prefix/en/latest/",
        )

        resp = self.client.get("/s/subproject/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/s/subproject/prefix/en/latest/",
        )

        # Trailing slash redirect
        resp = self.client.get("/s/subproject/prefix/en/latest", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/s/subproject/prefix/en/latest/",
        )

        # Normal serving
        resp = self.client.get(
            "/s/subproject/prefix/en/latest/", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/s/subproject/prefix/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_same_prefixes(self):
        self.project.custom_prefix = "/prefix/"
        self.project.custom_subproject_prefix = "/prefix/"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Root redirect for the subproject
        resp = self.client.get("/prefix/subproject", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/prefix/subproject/en/latest/",
        )

        # Normal serving
        resp = self.client.get("/prefix/subproject/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/prefix/subproject/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_valid_overlapping_prefixes(self):
        self.project.custom_prefix = "/prefix/"
        self.project.custom_subproject_prefix = "/prefix/s/"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Root redirect for the subproject
        resp = self.client.get("/prefix/s/subproject", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/prefix/s/subproject/en/latest/",
        )

        # Normal serving
        resp = self.client.get(
            "/prefix/s/subproject/en/latest/", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/prefix/s/subproject/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_invalid_overlapping_prefixes(self):
        self.project.custom_prefix = "/prefix/"
        self.project.custom_subproject_prefix = "/prefix/es/"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/", headers={"host": host})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/en/latest/", headers={"host": host})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # We can't access to the subproject.
        resp = self.client.get("/prefix/es/subproject/", headers={"host": host})
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(
            "/prefix/es/subproject/en/latest/", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(
            "/prefix/es/subproject/en/latest/api/index.html", headers={"host": host}
        )
        self.assertEqual(resp.status_code, 404)
