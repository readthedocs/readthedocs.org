"""
Most of this code is copied from:

  readthedocs/rtd_tests/tests/test_redirects.py

and adapted to use:

 * El Proxito
"""

import django_dynamic_fixture as fixture
import pytest
from django.http import Http404
from django.test.utils import override_settings

from readthedocs.builds.models import Version
from readthedocs.projects.models import Feature
from readthedocs.redirects.models import Redirect

from .base import BaseDocServing
from .mixins import MockStorageMixin


@override_settings(PUBLIC_DOMAIN="dev.readthedocs.io")
class InternalRedirectTests(BaseDocServing):

    """
    Test our own internal redirects.

    * redirects at / --happens at ``ServeDocs`` view
    * redirects on /page/.* --happens at ``URLConf``
    * invalid URLs --happens at ``URLConf``
    """

    def test_root_url(self):
        r = self.client.get("/", headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/",
        )

    def test_root_url_redirect_to_default_version(self):
        fixture.get(
            Version,
            project=self.project,
            active=True,
            slug="v3.0",
        )
        self.project.default_version = "v3.0"
        self.project.save()

        r = self.client.get("/", headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/v3.0/",
        )

    def test_page_on_main_site(self):
        r = self.client.get(
            "/page/test.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/test.html",
        )

    def test_page_redirect_with_query_params(self):
        r = self.client.get(
            "/page/test.html?foo=bar", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/test.html?foo=bar",
        )

    def test_url_with_nonexistent_slug(self):
        # Invalid URL for a not single version project
        r = self.client.get(
            "/nonexistent/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 404)

    def test_url_filename_only(self):
        # Invalid URL for a not single version project
        r = self.client.get(
            "/test.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 404)

    def test_url_dir_file(self):
        # Invalid URL for a not single version project
        r = self.client.get(
            "/nonexistent_dir/bogus.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

    def test_url_dir_subdir_file(self):
        # Invalid language in the URL
        r = self.client.get(
            "/nonexistent_dir/subdir/bogus.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

    def test_url_lang_file(self):
        # Invalid URL missing version
        r = self.client.get(
            "/en/bogus.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 404)

    def test_url_lang_subdir_file(self):
        # El Proxito does not check that the file exists when serving it and
        # returns a 200, if the file does not exist (we force this with
        # ``PTYHON_MEDIA=True``) the handler404 is executed. It will check again
        # for the file in the storage and it will fail.
        with override_settings(PYTHON_MEDIA=True):
            r = self.client.get(
                # This URL looks like a valid URL.
                # lang=en version=nonexistent_dir
                "/en/nonexistent_dir/bogus.html",
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(r.status_code, 404)

    def test_root_redirect_with_query_params(self):
        r = self.client.get("/?foo=bar", headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/?foo=bar",
        )


# Use ``PYTHON_MEDIA`` here to raise a 404 when trying to serve the file
# from disk and execute the code for the handler404 (the file does not
# exist). On production, this will happen when trying to serve from
# ``/proxito/ internal`` location
# NOTE: this could be achieved by mocking ``_serve_docs_nginx`` to raise a
# 404 directly and avoid using PYTHON_MEDIA.
@override_settings(
    PYTHON_MEDIA=True,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    ROOT_URLCONF="readthedocs.proxito.tests.handler_404_urls",
)
class UserRedirectTests(MockStorageMixin, BaseDocServing):
    def test_forced_redirect(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            force=True,
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

    def test_infinite_redirect(self):
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/install.html",
        )
        with pytest.raises(Http404):
            self.client.get("/en/latest/install.html", headers={"host": host})

        with pytest.raises(Http404):
            self.client.get("/en/latest/install.html?foo=bar", headers={"host": host})

    def test_infinite_redirect_changing_protocol(self):
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url=f"https://{host}/en/latest/install.html",
        )
        with pytest.raises(Http404):
            self.client.get("/en/latest/install.html", headers={"host": host})

        with pytest.raises(Http404):
            self.client.get("/en/latest/install.html?foo=bar", headers={"host": host})

    def test_redirect_prefix_infinite(self):
        """
        Avoid infinite redirects.

        If the URL hit is the same that the URL returned for redirection, we
        return a 404.

        These examples comes from this issue:
          * http://github.com/rtfd/readthedocs.org/issues/4673
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="prefix",
            from_url="/",
        )
        r = self.client.get(
            "/redirect.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/redirect.html",
        )

        r = self.client.get(
            "/redirect/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/redirect/",
        )

        with self.assertRaises(Http404):
            r = self.client.get(
                "/en/latest/redirect/", headers={"host": "project.dev.readthedocs.io"}
            )

    def test_redirect_root(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type="prefix",
            from_url="/woot/",
        )
        r = self.client.get(
            "/woot/faq.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq.html",
        )

        # Prefix redirects should match the whole path.
        with self.assertRaises(Http404):
            self.client.get(
                "/en/latest/woot/faq.html",
                headers={"host": "project.dev.readthedocs.io"},
            )

    def test_redirect_page(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html",
        )
        r = self.client.get(
            "/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

    def test_redirect_with_query_params_from_url(self):
        self._storage_exists(
            [
                "/media/html/project/latest/tutorial/install.html",
            ]
        )
        Redirect.objects.create(
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html",
        )
        r = self.client.get(
            "/install.html?foo=bar", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html?foo=bar",
        )

    def test_redirect_with_query_params_to_url(self):
        self._storage_exists(
            [
                "/media/html/project/latest/tutorial/install.html",
            ]
        )
        Redirect.objects.create(
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html?query=one",
        )
        r = self.client.get(
            "/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html?query=one",
        )

        r = self.client.get(
            "/install.html?query=two", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html?query=two&query=one",
        )

    def test_redirect_exact(self):
        self._storage_exists(
            [
                "/media/html/project/latest/guides/install.html",
            ]
        )

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

    def test_redirect_exact_looks_like_version(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/versions.json",
            to_url="/en/latest/versions.json",
        )
        r = self.client.get(
            "/en/versions.json", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/versions.json",
        )

    def test_redirect_exact_with_rest(self):
        """
        Exact redirects can have a ``$rest`` in the ``from_url``.

        Use case: we want to deprecate version ``2.0`` and replace it by
        ``3.0``. We write an exact redirect from ``/en/2.0/$rest`` to
        ``/en/3.0/``.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/$rest",
            to_url="/en/version/",  # change version
        )
        self.assertEqual(self.project.redirects.count(), 1)
        r = self.client.get(
            "/en/latest/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/version/guides/install.html",
        )

        # NOTE: I had to modify this test to add the Redirect in
        # ``self.translation`` instead of the root project. I think it makes
        # sense, but just wanted to mention to not forget to talk about
        # brackward compatibility
        fixture.get(
            Redirect,
            project=self.translation,
            redirect_type="exact",
            from_url="/es/version/$rest",
            to_url="/en/master/",  # change language and version
        )
        r = self.client.get(
            "/es/version/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/master/guides/install.html",
        )

    def test_redirect_inactive_version(self):
        """
        Inactive Version (``active=False``) should redirect properly.

        The function that servers the page should return 404 when serving a page
        of an inactive version and the redirect system should work.
        """
        fixture.get(
            Version,
            slug="oldversion",
            project=self.project,
            active=False,
        )
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/oldversion/",
            to_url="/en/newversion/",
        )
        r = self.client.get(
            "/en/oldversion/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/newversion/",
        )

    def test_redirect_keeps_version_number(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/how_to_install.html",
            to_url="/install.html",
        )
        r = self.client.get(
            "/en/0.8.2/how_to_install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/0.8.2/install.html",
        )

    def test_redirect_keeps_language(self):
        self.project.language = "de"
        self.project.save()
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/how_to_install.html",
            to_url="/install.html",
        )
        r = self.client.get(
            "/de/0.8.2/how_to_install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/de/0.8.2/install.html",
        )

    def test_redirect_recognizes_custom_cname(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html",
        )
        fixture.get(
            Feature,
            feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER,
            projects=[self.project],
        )
        r = self.client.get(
            "/install.html",
            headers={"host": "docs.project.io", "x-rtd-slug": "project"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://docs.project.io/en/latest/tutorial/install.html",
        )

    def test_redirect_html(self):
        self._storage_exists(
            [
                "/media/html/project/latest/faq.html",
            ]
        )
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_html",
        )
        r = self.client.get(
            "/en/latest/faq/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq.html",
        )

    def test_redirect_html_root_index(self):
        # The redirection code should never be executed when hitting
        # ``/en/latest/`` because we serve that path for both ``html`` and
        # ``htmldir``. In both cases, the project will have a
        # ``/html/project/latest/index.html`` in the storage and should never
        # hit our redirection code because we MUST check for that file before
        # calling our redirection code. In other words, this should never
        # jump into the ``ServeError404`` handler.
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_html",
        )

        with override_settings(PYTHON_MEDIA=False):
            # File exists in storage media
            r = self.client.get(
                "/en/latest/", headers={"host": "project.dev.readthedocs.io"}
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r["X-Accel-Redirect"],
                "/proxito/media/html/project/latest/index.html",
            )

        with override_settings(PYTHON_MEDIA=True):
            with self.assertRaises(Http404):
                # File does not exist in storage media
                r = self.client.get(
                    "/en/latest/", headers={"host": "project.dev.readthedocs.io"}
                )

    def test_redirect_html_index(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_html",
        )
        r = self.client.get(
            "/en/latest/faq/index.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq.html",
        )

    def test_redirect_htmldir(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_htmldir",
        )
        r = self.client.get(
            "/en/latest/faq.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq/",
        )

    def test_redirect_root_with_301_status(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="prefix",
            from_url="/woot/",
            http_status=301,
        )
        r = self.client.get(
            "/woot/faq.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 301)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq.html",
        )

    def test_not_found_page_without_trailing_slash(self):
        # https://github.com/readthedocs/readthedocs.org/issues/4673
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="prefix",
            from_url="/",
        )

        with self.assertRaises(Http404):
            # Avoid infinite redirect
            r = self.client.get(
                "/en/latest/section/file-not-found",
                headers={"host": "project.dev.readthedocs.io"},
            )


@override_settings(PUBLIC_DOMAIN="dev.readthedocs.io")
class UserForcedRedirectTests(BaseDocServing):
    def test_no_forced_redirect(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            force=False,
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)

    def test_prefix_redirect(self):
        """
        Test prefix redirect.

        Prefix redirects don't match a version,
        so they will return 404, and the redirect will
        be handled there.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="prefix",
            from_url="/woot/",
            force=True,
        )
        r = self.client.get(
            "/woot/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 404)

    def test_infinite_redirect(self):
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/install.html",
            force=True,
        )
        r = self.client.get("/en/latest/install.html", headers={"host": host})
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/en/latest/install.html?foo=bar", headers={"host": host})
        self.assertEqual(r.status_code, 200)

    def test_infinite_redirect_changing_protocol(self):
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/install.html",
            to_url=f"https://{host}/install.html",
            force=True,
        )
        r = self.client.get("/en/latest/install.html", headers={"host": host})
        self.assertEqual(r.status_code, 200)

        r = self.client.get(
            "/en/latest/install.html?foo=bar",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 200)

    def test_redirect_page(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html",
            force=True,
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

    def test_redirect_with_query_params(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html",
            force=True,
        )
        r = self.client.get(
            "/en/latest/install.html?foo=bar",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html?foo=bar",
        )

    def test_redirect_exact(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            force=True,
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

    def test_redirect_exact_with_rest(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/$rest",
            to_url="/en/version/",
            force=True,
        )
        self.assertEqual(self.project.redirects.count(), 1)
        r = self.client.get(
            "/en/latest/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/version/guides/install.html",
        )

        fixture.get(
            Redirect,
            project=self.translation,
            redirect_type="exact",
            from_url="/es/latest/$rest",
            to_url="/en/master/",
            force=True,
        )
        r = self.client.get(
            "/es/latest/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/master/guides/install.html",
        )

    def test_redirect_keeps_language(self):
        self.project.language = "de"
        self.project.save()
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/how_to_install.html",
            to_url="/install.html",
            force=True,
        )
        r = self.client.get(
            "/de/latest/how_to_install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/de/latest/install.html",
        )

    def test_redirect_recognizes_custom_cname(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="page",
            from_url="/install.html",
            to_url="/tutorial/install.html",
            force=True,
        )
        fixture.get(
            Feature,
            feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER,
            projects=[self.project],
        )
        r = self.client.get(
            "/en/latest/install.html",
            headers={"host": "docs.project.io", "x-rtd-slug": "project"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://docs.project.io/en/latest/tutorial/install.html",
        )

    def test_redirect_html(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_html",
            force=True,
        )
        r = self.client.get(
            "/en/latest/faq/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq.html",
        )

    def test_redirect_html_index(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_html",
            force=True,
        )
        r = self.client.get(
            "/en/latest/faq/index.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq.html",
        )

    def test_redirect_htmldir(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_htmldir",
            force=True,
        )
        r = self.client.get(
            "/en/latest/faq.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/faq/",
        )

    def test_redirect_with_301_status(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            http_status=301,
            force=True,
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 301)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )


@override_settings(
    PYTHON_MEDIA=True,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    ROOT_URLCONF="readthedocs.proxito.tests.handler_404_urls",
)
class UserRedirectCrossdomainTest(BaseDocServing):
    def test_redirect_prefix_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url.

        We also test by trying to bypass the protocol check with the special chars listed at
        https://github.com/python/cpython/blob/c3ffbbdf3d5645ee07c22649f2028f9dffc762ba/Lib/urllib/parse.py#L80-L81.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="prefix",
            from_url="/",
        )

        urls = [
            # Plain protocol, these are caught by the slash redirect.
            (
                "http://project.dev.readthedocs.io/http://my.host/path.html",
                "/http:/my.host/path.html",
            ),
            (
                "http://project.dev.readthedocs.io//my.host/path.html",
                "/my.host/path.html",
            ),
            # Trying to bypass the protocol check by including a `\r` char.
            (
                "http://project.dev.readthedocs.io/http:/%0D/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/http://my.host/path.html",
            ),
            (
                "http://project.dev.readthedocs.io/%0D/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/my.host/path.html",
            ),
            # Trying to bypass the protocol check by including a `\t` char.
            (
                "http://project.dev.readthedocs.io/http:/%09/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/http://my.host/path.html",
            ),
            (
                "http://project.dev.readthedocs.io/%09/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/my.host/path.html",
            ),
        ]
        for url, expected_location in urls:
            r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(r.status_code, 302, url)
            self.assertEqual(r["Location"], expected_location, url)

    def test_redirect_prefix_crossdomain_with_newline_chars(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="prefix",
            from_url="/",
        )
        urls = [
            (
                "http://project.dev.readthedocs.io/http:/%0A/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/http://my.host/path.html",
            ),
            (
                "http://project.dev.readthedocs.io/%0A/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/my.host/path.html",
            ),
        ]
        for url, expected_location in urls:
            r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(r.status_code, 302, url)
            self.assertEqual(r["Location"], expected_location, url)

    def test_redirect_sphinx_htmldir_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_htmldir",
        )

        urls = [
            # Plain protocol, these are caught by the slash redirect.
            (
                "http://project.dev.readthedocs.io/http://my.host/path.html",
                "/http:/my.host/path.html",
            ),
            (
                "http://project.dev.readthedocs.io//my.host/path.html",
                "/my.host/path.html",
            ),
            # Trying to bypass the protocol check by including a `\r` char.
            (
                "http://project.dev.readthedocs.io/http:/%0D/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/http://my.host/path/",
            ),
            (
                "http://project.dev.readthedocs.io/%0D/my.host/path.html",
                "http://project.dev.readthedocs.io/en/latest/my.host/path/",
            ),
        ]

        for url, expected_location in urls:
            r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(r.status_code, 302, url)
            self.assertEqual(r["Location"], expected_location, url)

    def test_redirect_sphinx_html_crossdomain(self):
        """Avoid redirecting to an external site unless the external site is in to_url."""
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type="sphinx_html",
        )

        urls = [
            # Plain protocol, these are caught by the slash redirect.
            (
                "http://project.dev.readthedocs.io/http://my.host/path/",
                "/http:/my.host/path/",
            ),
            ("http://project.dev.readthedocs.io//my.host/path/", "/my.host/path/"),
            # Trying to bypass the protocol check by including a `\r` char.
            (
                "http://project.dev.readthedocs.io/http:/%0D/my.host/path/",
                "http://project.dev.readthedocs.io/en/latest/http://my.host/path.html",
            ),
            (
                "http://project.dev.readthedocs.io/%0D/my.host/path/",
                "http://project.dev.readthedocs.io/en/latest/my.host/path.html",
            ),
        ]

        for url, expected_location in urls:
            r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(r.status_code, 302, url)
            self.assertEqual(r["Location"], expected_location, url)

    def test_redirect_using_projects_prefix(self):
        """
        Test that we can support redirects using the ``/projects/`` prefix.

        https://github.com/readthedocs/readthedocs.org/issues/7552
        """
        redirect = fixture.get(
            Redirect,
            project=self.project,
            redirect_type="exact",
            from_url="/projects/$rest",
            to_url="https://example.com/projects/",
        )
        self.assertEqual(self.project.redirects.count(), 1)
        r = self.client.get(
            "/projects/deleted-subproject/en/latest/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "https://example.com/projects/deleted-subproject/en/latest/guides/install.html",
        )

        redirect.from_url = "/projects/not-found/$rest"
        redirect.to_url = "/projects/subproject/"
        redirect.save()
        r = self.client.get(
            "/projects/not-found/en/latest/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/projects/subproject/en/latest/guides/install.html",
        )
