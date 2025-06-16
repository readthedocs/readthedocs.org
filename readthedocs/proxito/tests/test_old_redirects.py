"""
Most of this code is copied from:

  readthedocs/rtd_tests/tests/test_redirects.py

and adapted to use:

 * El Proxito
"""

from django.urls import reverse
import django_dynamic_fixture as fixture
from django.test.utils import override_settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects.constants import SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.projects.models import Feature
from readthedocs.redirects.constants import (
    CLEAN_URL_TO_HTML_REDIRECT,
    EXACT_REDIRECT,
    HTML_TO_CLEAN_URL_REDIRECT,
    PAGE_REDIRECT,
)
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
    RTD_EXTERNAL_VERSION_DOMAIN="readthedocs.build",
)
class UserRedirectTests(MockStorageMixin, BaseDocServing):
    def test_forced_redirect(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
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

    def test_disabled_redirect(self):
        redirect = fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            enabled=True,
        )
        url = "/en/latest/install.html"
        r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

        redirect.enabled = False
        redirect.save()

        r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 404)

    def test_redirect_order(self):
        redirect_a = fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="/en/latest/tutorial/:splat",
            enabled=True,
        )
        redirect_b = fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url="/en/latest/installation.html",
            enabled=True,
        )

        redirect_a.refresh_from_db()
        self.assertEqual(redirect_b.position, 0)
        self.assertEqual(redirect_a.position, 1)

        url = "/en/latest/install.html"
        r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/installation.html",
        )

        redirect_a.position = 0
        redirect_a.save()
        redirect_b.refresh_from_db()

        self.assertEqual(redirect_a.position, 0)
        self.assertEqual(redirect_b.position, 1)

        url = "/en/latest/install.html"
        r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/tutorial/install.html",
        )

    def test_redirect_ignored_on_external_domain(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/*",
            to_url="/en/latest/:splat",
        )
        url = "/install.html"
        r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"], "http://project.dev.readthedocs.io/en/latest/install.html"
        )

        fixture.get(
            Version,
            project=self.project,
            active=True,
            built=True,
            slug="22",
            type=EXTERNAL,
        )
        r = self.client.get(url, headers={"host": "project--22.readthedocs.build"})
        self.assertEqual(r.status_code, 404)

    def test_infinite_redirect(self):
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url="/en/latest/install.html",
        )
        r = self.client.get("/en/latest/install.html", headers={"host": host})
        self.assertEqual(r.status_code, 404)

        r = self.client.get("/en/latest/install.html?foo=bar", headers={"host": host})
        self.assertEqual(r.status_code, 404)

    def test_infinite_redirect_on_404_view(self):
        """
        Explicitly test using the ``proxito_404_handler`` view.

        This mimics the actual request that happens when a page is not found.
        """
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url="/en/latest/install.html",
        )
        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/latest/install.html"},
            ),
            headers={"host": host},
        )
        assert r.status_code == 404

        r = self.client.get(
            reverse(
                "proxito_404_handler",
                kwargs={"proxito_path": "/en/latest/install.html"},
                query={"foo": "bar"},
            ),
            headers={"host": host},
        )
        assert r.status_code == 404

    def test_infinite_redirect_changing_protocol(self):
        host = "project.dev.readthedocs.io"
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url=f"https://{host}/en/latest/install.html",
        )

        r = self.client.get("/en/latest/install.html", headers={"host": host})
        self.assertEqual(r.status_code, 404)

        r = self.client.get("/en/latest/install.html?foo=bar", headers={"host": host})
        self.assertEqual(r.status_code, 404)

    def test_exact_redirect_avoid_infinite_redirect(self):
        """
        Avoid infinite redirects.

        If the URL hit is the same that the URL returned for redirection, we
        return a 404.

        These examples comes from this issue:
          * http://github.com/readthedocs/readthedocs.org/issues/4673
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/*",
            to_url="/en/latest/:splat",
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

        r = self.client.get(
            "/en/latest/redirect/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 404)

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="/en/latest/subdir/:splat",
        )
        r = self.client.get(
            "/en/latest/redirect.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/subdir/redirect.html",
        )

        r = self.client.get(
            "/en/latest/subdir/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

    def test_page_redirect_avoid_infinite_redirect(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/*",
            to_url="/subdir/:splat",
        )
        r = self.client.get(
            "/en/latest/redirect.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/subdir/redirect.html",
        )

        r = self.client.get(
            "/en/latest/subdir/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/dir/*",
            to_url="/dir/subdir/:splat",
        )
        r = self.client.get(
            "/en/latest/dir/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/dir/subdir/redirect.html",
        )

        r = self.client.get(
            "/en/latest/dir/subdir/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

    def test_exact_redirect_to_parent_path(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="/:splat",
        )
        r = self.client.get(
            "/en/latest/dir/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/dir/redirect.html",
        )

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/one/two/*",
            to_url="/one/:splat",
        )
        r = self.client.get(
            "/one/two/three/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/one/three/redirect.html",
        )

    def test_page_redirect_to_parent_path(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/guides/*",
            to_url="/:splat",
        )
        r = self.client.get(
            "/en/latest/guides/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/redirect.html",
        )

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/one/two/*",
            to_url="/one/:splat",
        )
        r = self.client.get(
            "/en/latest/one/two/three/redirect.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/one/three/redirect.html",
        )

    def test_redirect_root(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/woot/*",
            to_url="/en/latest/:splat",
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
        r = self.client.get(
            "/en/latest/woot/faq.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

    def test_redirect_page(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
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

    def test_redirect_exact_with_wildcard(self):
        """
        Exact redirects can have a ``*`` at the end of ``from_url``.

        Use case: we want to deprecate version ``2.0`` and replace it by
        ``3.0``. We write an exact redirect from ``/en/2.0/*`` to
        ``/en/3.0/:splat``.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="/en/version/:splat",  # change version
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
            redirect_type=EXACT_REDIRECT,
            from_url="/es/version/*",
            to_url="/en/master/:splat",  # change language and version
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

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/tutorials/*",
            to_url="/en/latest/tutorial.html",
        )
        r = self.client.get(
            "/en/latest/tutorials/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"], "http://project.dev.readthedocs.io/en/latest/tutorial.html"
        )

    def test_page_redirect_with_wildcard(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/*",
            to_url="/guides/:splat",
        )
        r = self.client.get(
            "/en/latest/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/guides/install.html",
        )

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/guides/*",
            to_url="/guides/redirects/:splat",
        )
        r = self.client.get(
            "/en/latest/guides/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"],
            "http://project.dev.readthedocs.io/en/latest/guides/redirects/install.html",
        )

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/tutorials/*",
            to_url="/tutorial.html",
        )
        r = self.client.get(
            "/en/latest/tutorials/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r["Location"], "http://project.dev.readthedocs.io/en/latest/tutorial.html"
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
            redirect_type=EXACT_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=CLEAN_URL_TO_HTML_REDIRECT,
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
            redirect_type=CLEAN_URL_TO_HTML_REDIRECT,
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
            # File does not exist in storage media
            r = self.client.get(
                "/en/latest/", headers={"host": "project.dev.readthedocs.io"}
            )
            self.assertEqual(r.status_code, 404)

    def test_redirect_html_index(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=CLEAN_URL_TO_HTML_REDIRECT,
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
            redirect_type=HTML_TO_CLEAN_URL_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
            from_url="/woot/*",
            to_url="/en/latest/:splat",
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
            redirect_type=EXACT_REDIRECT,
            from_url="/*",
            to_url="/en/latest/:splat",
        )

        # Avoid infinite redirect
        r = self.client.get(
            "/en/latest/section/file-not-found",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 404)

    def test_page_redirect_with_and_without_trailing_slash(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/install",
            to_url="/tutorial/install/",
        )

        for url in ["/en/latest/install", "/en/latest/install/"]:
            resp = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["Location"],
                "http://project.dev.readthedocs.io/en/latest/tutorial/install/",
            )

    def test_exact_redirect_with_and_without_trailing_slash(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install",
            to_url="/en/latest/tutorial/install/",
        )

        for url in ["/en/latest/install", "/en/latest/install/"]:
            resp = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(
                resp["Location"],
                "http://project.dev.readthedocs.io/en/latest/tutorial/install/",
            )


@override_settings(PUBLIC_DOMAIN="dev.readthedocs.io")
class UserForcedRedirectTests(BaseDocServing):
    def test_no_forced_redirect(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url="/en/latest/tutorial/install.html",
            force=False,
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 200)

    def test_exact_redirect_with_wildcard(self):
        """
        Test prefix redirect.

        Prefix redirects don't match a version,
        so they will return 404, and the redirect will
        be handled there.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/woot/*",
            to_url="/en/latest/:splat",
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
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

    def test_redirect_exact_with_wildcard(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="/en/version/:splat",
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
            redirect_type=EXACT_REDIRECT,
            from_url="/es/latest/*",
            to_url="/en/master/:splat",
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=PAGE_REDIRECT,
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
            redirect_type=CLEAN_URL_TO_HTML_REDIRECT,
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
            redirect_type=CLEAN_URL_TO_HTML_REDIRECT,
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
            redirect_type=HTML_TO_CLEAN_URL_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
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

    def test_page_root_redirect(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/",
            to_url="https://example.com/",
            force=True,
        )
        r = self.client.get(
            "/en/latest/", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/")

    def test_exact_root_redirect_single_version(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/",
            to_url="https://example.com/",
            force=True,
        )
        r = self.client.get("/", headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/")

    def test_page_root_redirect_single_version(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/",
            to_url="https://example.com/",
            force=True,
        )
        r = self.client.get("/", headers={"host": "project.dev.readthedocs.io"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/")


@override_settings(
    PYTHON_MEDIA=True,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    ROOT_URLCONF="readthedocs.proxito.tests.handler_404_urls",
)
class UserRedirectCrossdomainTest(BaseDocServing):
    def test_redirect_exact_redirect_with_wildcard_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url.

        We also test by trying to bypass the protocol check with the special chars listed at
        https://github.com/python/cpython/blob/c3ffbbdf3d5645ee07c22649f2028f9dffc762ba/Lib/urllib/parse.py#L80-L81.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/*",
            to_url="/en/latest/:splat",
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

    def test_redirect_exact_with_wildcard_crossdomain_with_newline_chars(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/*",
            to_url="/en/latest/:splat",
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

    def test_redirect_exact_with_wildcard_crossdomain(self):
        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="/:splat",
        )
        urls = [
            (
                "http://project.dev.readthedocs.io/en/latest/%0D/example.com/path.html",
                "http://project.dev.readthedocs.io//example.com/path.html",
            ),
            # These are caught by the slash redirect.
            (
                "http://project.dev.readthedocs.io/en/latest//example.com",
                "/en/latest/example.com",
            ),
            (
                "http://project.dev.readthedocs.io/en/latest/https://example.com",
                "/en/latest/https:/example.com",
            ),
        ]
        for url, expected_location in urls:
            r = self.client.get(url, headers={"host": "project.dev.readthedocs.io"})
            self.assertEqual(r.status_code, 302, url)
            self.assertEqual(r["Location"], expected_location, url)

    def test_redirect_html_to_clean_url_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=HTML_TO_CLEAN_URL_REDIRECT,
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

    def test_redirect_clean_url_to_html_crossdomain(self):
        """Avoid redirecting to an external site unless the external site is in to_url."""
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=CLEAN_URL_TO_HTML_REDIRECT,
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
            redirect_type=EXACT_REDIRECT,
            from_url="/projects/*",
            to_url="https://example.com/projects/:splat",
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

        redirect.from_url = "/projects/not-found/*"
        redirect.to_url = "/projects/subproject/:splat"
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

    def test_page_redirect_crossdomain(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/install.html",
            to_url="https://example.com/",
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/")

    def test_page_redirect_with_wildcard_crossdomain(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/tutorial/*",
            to_url="https://example.com/:splat",
        )
        r = self.client.get(
            "/en/latest/tutorial/install.html",
            headers={"host": "project.dev.readthedocs.io"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/install.html")

    def test_exact_redirect_crossdomain(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/install.html",
            to_url="https://example.com/",
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/")

    def test_exact_redirect_with_wildcard_crossdomain(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/en/latest/*",
            to_url="https://example.com/:splat",
        )
        r = self.client.get(
            "/en/latest/install.html", headers={"host": "project.dev.readthedocs.io"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/install.html")
