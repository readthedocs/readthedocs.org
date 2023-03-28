from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.projects.models import Feature
from readthedocs.proxito.tests.base import BaseDocServing


@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="readthedocs.build",
)
class TestCustomURLPatterns(BaseDocServing):
    def setUp(self):
        super().setUp()
        get(
            Feature,
            feature_id=Feature.USE_UNRESOLVER_WITH_PROXITO,
            default_true=True,
            future_default_true=True,
        )

    def test_custom_urlpattern_multi_version_project(self):
        self.project.urlpattern = (
            "/custom/prefix/{language}(/({version}(/{filename})?)?)?"
        )
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect.
        resp = self.client.get("/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        # Trailing slash redirect
        resp = self.client.get("/custom/prefix/en/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/prefix/en/latest/"
        )

        resp = self.client.get("/custom/prefix/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        resp = self.client.get(
            "/custom/prefix/en/latest/api/index.html", HTTP_HOST=host
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/api/index.html",
        )

    def test_custom_urlpattern_multi_version_project_translation(self):
        self.project.urlpattern = (
            "/custom/prefix/{language}(/({version}(/{filename})?)?)?"
        )
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/es/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        # Trailing slash redirect
        resp = self.client.get("/custom/prefix/es/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/prefix/es/latest/"
        )

        resp = self.client.get("/custom/prefix/es/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/index.html",
        )

        resp = self.client.get(
            "/custom/prefix/es/latest/api/index.html", HTTP_HOST=host
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/api/index.html",
        )

    def test_custom_urlpattern_reversed_components_multi_version_project(self):
        self.project.urlpattern = "/{version}(/({language}(/{filename})?)?)?"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        # Trailing slash redirect
        resp = self.client.get("/latest/en", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/latest/en/")

        resp = self.client.get("/latest/en/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        resp = self.client.get("/latest/en/api/index.html", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/api/index.html",
        )

    def test_custom_urlpattern_single_version_project(self):
        self.project.single_version = True
        self.project.urlpattern = "/custom-prefix(/{filename})?"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/"
        )

        # Trailing slash redirect
        resp = self.client.get("/custom-prefix", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom-prefix/"
        )

        resp = self.client.get("/custom-prefix/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/index.html",
        )

        resp = self.client.get("/custom-prefix/api/index.html", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/project/latest/api/index.html",
        )

    def test_custom_urlpattern_subproject(self):
        self.project.urlpattern_subproject = "/custom/{subproject}/prefix(/{filename})?"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/en/latest/")

        # Serving works on the main project.
        resp = self.client.get("/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/custom/subproject/prefix/"
        )

        resp = self.client.get("/en/latest/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/prefix/en/latest/",
        )

        # Old paths
        resp = self.client.get("/projects/subproject/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get("/projects/subproject/en/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        # Root redirect for the subproject
        resp = self.client.get("/custom/subproject/prefix", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/prefix/en/latest/",
        )

        resp = self.client.get("/custom/subproject/prefix/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/prefix/en/latest/",
        )

        # Trailing slash redirect
        resp = self.client.get("/custom/subproject/prefix/en/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/custom/subproject/prefix/en/latest/",
        )

        # Normal serving
        resp = self.client.get("/custom/subproject/prefix/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/custom/subproject/prefix/en/latest/api/index.html", HTTP_HOST=host
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_custom_urlpattern_subproject_empty(self):
        self.project.urlpattern_subproject = "/{subproject}(/{filename})?"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/en/latest/")

        # Serving works on the main project.
        resp = self.client.get("/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/subproject/")

        resp = self.client.get("/en/latest/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        # Root redirect for the subproject
        resp = self.client.get("/subproject", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        resp = self.client.get("/subproject/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        # Trailing slash redirect
        resp = self.client.get("/subproject/en/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/subproject/en/latest/"
        )

        # Normal serving
        resp = self.client.get("/subproject/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get("/subproject/en/latest/api/index.html", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_custom_urlpattern_and_urlpattern_subproject_in_superproject(self):
        self.project.urlpattern = "/prefix/{language}(/({version}(/{filename})?)?)?"
        self.project.urlpattern_subproject = "/s/{subproject}(/{filename})?"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/prefix/en/latest/"
        )

        resp = self.client.get("/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/"
        )

        resp = self.client.get("/en/latest/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Root redirect for the subproject
        resp = self.client.get("/s/subproject", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        resp = self.client.get("/s/subproject/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Trailing slash redirect
        resp = self.client.get("/s/subproject/en/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Normal serving
        resp = self.client.get("/s/subproject/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get("/s/subproject/en/latest/api/index.html", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )

    def test_custom_urlpattern_and_urlpattern_subproject_with_translations(self):
        self.project.urlpattern = "/prefix/{language}(/({version}(/{filename})?)?)?"
        self.project.urlpattern_subproject = "/s/{subproject}(/{filename})?"
        self.project.save()
        host = "project.readthedocs.io"

        resp = self.client.get("/es/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 404)

        # Serving works on the main project.
        resp = self.client.get("/prefix/es/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/translation/latest/index.html",
        )

        # Normal serving
        resp = self.client.get("/s/subproject/es/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-translation/latest/index.html",
        )

        resp = self.client.get("/s/subproject/es/latest/api/index.html", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject-translation/latest/api/index.html",
        )

    def test_custom_urlpattern_in_subproject_and_urlpattern_in_superproject(self):
        self.subproject.urlpattern = "/prefix/{language}(/({version}(/{filename})?)?)?"
        self.subproject.save()
        self.project.urlpattern_subproject = "/s/{subproject}(/{filename})?"
        self.project.save()
        host = "project.readthedocs.io"

        # Root redirect for the main project.
        resp = self.client.get("/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "http://project.readthedocs.io/en/latest/")

        # Serving works on the main project.
        resp = self.client.get("/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"], "/proxito/media/html/project/latest/index.html"
        )

        # Subproject to main project redirect
        resp = self.client.get("/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/"
        )

        resp = self.client.get("/en/latest/", HTTP_HOST="subproject.readthedocs.io")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"], "http://project.readthedocs.io/s/subproject/en/latest/"
        )

        # Root redirect for the subproject
        resp = self.client.get("/s/subproject", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/s/subproject/prefix/en/latest/",
        )

        resp = self.client.get("/s/subproject/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/s/subproject/prefix/en/latest/",
        )

        # Trailing slash redirect
        resp = self.client.get("/s/subproject/prefix/en/latest", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp["Location"],
            "http://project.readthedocs.io/s/subproject/prefix/en/latest/",
        )

        # Normal serving
        resp = self.client.get("/s/subproject/prefix/en/latest/", HTTP_HOST=host)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/index.html",
        )

        resp = self.client.get(
            "/s/subproject/prefix/en/latest/api/index.html", HTTP_HOST=host
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp["x-accel-redirect"],
            "/proxito/media/html/subproject/latest/api/index.html",
        )
