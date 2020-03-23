"""
Most of this code is copied from:

  readthedocs/rtd_tests/tests/test_redirects.py

and adapted to use:

 * El Proxito
 * USE_SUBDOMAIN=True always
"""

import django_dynamic_fixture as fixture
import pytest
from django.http import Http404
from django.test.utils import override_settings
from django.urls import reverse

from readthedocs.builds.models import Version
from readthedocs.redirects.models import Redirect

from .base import BaseDocServing
from .mixins import MockStorageMixin


@override_settings(PUBLIC_DOMAIN='dev.readthedocs.io')
class InternalRedirectTests(BaseDocServing):

    """
    Test our own internal redirects.

    * redirects at / --happens at ``ServeDocs`` view
    * redirects on /page/.* --happens at ``URLConf``
    * invalid URLs --happens at ``URLConf``
    """

    def test_root_url(self):
        r = self.client.get(
            '/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/',
        )

    def test_root_url_redirect_to_default_version(self):
        fixture.get(
            Version,
            project=self.project,
            active=True,
            slug='v3.0',
        )
        self.project.default_version = 'v3.0'
        self.project.save()

        r = self.client.get(
            '/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/v3.0/',
        )

    def test_page_on_main_site(self):
        r = self.client.get(
            '/page/test.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/test.html',
        )

    def test_page_redirect_with_query_params(self):
        r = self.client.get(
            '/page/test.html?foo=bar',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/test.html?foo=bar',
        )

    def test_url_with_nonexistent_slug(self):
        # Invalid URL for a not single version project
        r = self.client.get(
            '/nonexistent/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 404)

    def test_url_filename_only(self):
        # Invalid URL for a not single version project
        r = self.client.get(
            '/test.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 404)

    def test_url_dir_file(self):
        # Invalid URL for a not single version project
        r = self.client.get(
            '/nonexistent_dir/bogus.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 404)

    def test_url_dir_subdir_file(self):
        # Invalid language in the URL
        r = self.client.get(
            '/nonexistent_dir/subdir/bogus.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 404)

    def test_url_lang_file(self):
        # Invalid URL missing version
        r = self.client.get(
            '/en/bogus.html',
            HTTP_HOST='project.dev.readthedocs.io',
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
                '/en/nonexistent_dir/bogus.html',
                HTTP_HOST='project.dev.readthedocs.io',
            )
            self.assertEqual(r.status_code, 404)

    def test_root_redirect_with_query_params(self):
        r = self.client.get(
            '/?foo=bar',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/?foo=bar',
        )


# Use ``PYTHON_MEDIA`` here to raise a 404 when trying to serve the file
# from disk and execute the code for the handler404 (the file does not
# exist). On production, this will happen when trying to serve from
# ``/proxito/ internal`` location
# NOTE: this could be achieved by mocking ``_serve_docs_nginx`` to raise a
# 404 directly and avoid using PYTHON_MEDIA.
@override_settings(
    PYTHON_MEDIA=True,
    PUBLIC_DOMAIN='dev.readthedocs.io',
    ROOT_URLCONF='readthedocs.proxito.tests.handler_404_urls',
)
class UserRedirectTests(MockStorageMixin, BaseDocServing):

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
            project=self.project, redirect_type='prefix',
            from_url='/',
        )
        r = self.client.get(
            '/redirect.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/redirect.html',
        )

        r = self.client.get(
            '/redirect/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/redirect/',
        )

        with self.assertRaises(Http404):
            r = self.client.get(
                '/en/latest/redirect/',
                HTTP_HOST='project.dev.readthedocs.io',
            )


    def test_redirect_root(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type='prefix',
            from_url='/woot/',
        )
        r = self.client.get(
            '/woot/faq.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/faq.html',
        )

    def test_redirect_page(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type='page',
            from_url='/install.html',
            to_url='/tutorial/install.html',
        )
        r = self.client.get(
            '/install.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/tutorial/install.html',
        )

    def test_redirect_with_query_params(self):
        self._storage_exists([
            '/media/html/project/latest/tutorial/install.html',
        ])
        Redirect.objects.create(
            project=self.project,
            redirect_type='page',
            from_url='/install.html',
            to_url='/tutorial/install.html',
        )
        r = self.client.get(
            '/install.html?foo=bar',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/tutorial/install.html?foo=bar',
        )

    def test_redirect_exact(self):
        self._storage_exists([
            '/media/html/project/latest/guides/install.html',
        ])

        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='exact',
            from_url='/en/latest/install.html',
            to_url='/en/latest/tutorial/install.html',
        )
        r = self.client.get(
            '/en/latest/install.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/tutorial/install.html',
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
            redirect_type='exact',
            from_url='/en/latest/$rest',
            to_url='/en/version/',  # change version
        )
        self.assertEqual(self.project.redirects.count(), 1)
        r = self.client.get(
            '/en/latest/guides/install.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/version/guides/install.html',
        )

        # NOTE: I had to modify this test to add the Redirect in
        # ``self.translation`` instead of the root project. I think it makes
        # sense, but just wanted to mention to not forget to talk about
        # brackward compatibility
        fixture.get(
            Redirect,
            project=self.translation,
            redirect_type='exact',
            from_url='/es/version/$rest',
            to_url='/en/master/',  # change language and version
        )
        r = self.client.get(
            '/es/version/guides/install.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/master/guides/install.html',
        )

    def test_redirect_inactive_version(self):
        """
        Inactive Version (``active=False``) should redirect properly.

        The function that servers the page should return 404 when serving a page
        of an inactive version and the redirect system should work.
        """
        fixture.get(
            Version,
            slug='oldversion',
            project=self.project,
            active=False,
        )
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='exact',
            from_url='/en/oldversion/',
            to_url='/en/newversion/',
        )
        r = self.client.get(
            '/en/oldversion/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/newversion/',
        )

    def test_redirect_keeps_version_number(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='page',
            from_url='/how_to_install.html',
            to_url='/install.html',
        )
        r = self.client.get(
            '/en/0.8.2/how_to_install.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/0.8.2/install.html',
        )

    def test_redirect_keeps_language(self):
        self.project.language = 'de'
        self.project.save()
        fixture.get(
            Redirect,
            project=self.project, redirect_type='page',
            from_url='/how_to_install.html', to_url='/install.html',
        )
        r = self.client.get(
            '/de/0.8.2/how_to_install.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/de/0.8.2/install.html',
        )

    def test_redirect_recognizes_custom_cname(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='page',
            from_url='/install.html',
            to_url='/tutorial/install.html',
        )
        r = self.client.get(
            '/install.html',
            HTTP_HOST='docs.project.io',
            HTTP_X_RTD_SLUG='project',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://docs.project.io/en/latest/tutorial/install.html',
        )

    def test_redirect_html(self):
        self._storage_exists([
            '/media/html/project/latest/faq.html',
        ])
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='sphinx_html',
        )
        r = self.client.get(
            '/en/latest/faq/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/faq.html',
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
            redirect_type='sphinx_html',
        )

        with override_settings(PYTHON_MEDIA=False):
            # File exists in storage media
            r = self.client.get(
                '/en/latest/',
                HTTP_HOST='project.dev.readthedocs.io',
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                r['X-Accel-Redirect'],
                '/proxito/media/html/project/latest/index.html',
            )

        with override_settings(PYTHON_MEDIA=True):
            with self.assertRaises(Http404):
                # File does not exist in storage media
                r = self.client.get(
                    '/en/latest/',
                    HTTP_HOST='project.dev.readthedocs.io',
                )

    def test_redirect_html_index(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='sphinx_html',
        )
        r = self.client.get(
            '/en/latest/faq/index.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/faq.html',
        )

    def test_redirect_htmldir(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='sphinx_htmldir',
        )
        r = self.client.get(
            '/en/latest/faq.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/faq/',
        )

    def test_redirect_root_with_301_status(self):
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='prefix',
            from_url='/woot/',
            http_status=301,
        )
        r = self.client.get(
            '/woot/faq.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 301)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/faq.html',
        )

    def test_not_found_page_without_trailing_slash(self):
        # https://github.com/readthedocs/readthedocs.org/issues/4673
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='prefix',
            from_url='/',
        )

        with self.assertRaises(Http404):
            # Avoid infinite redirect
            r = self.client.get(
                '/en/latest/section/file-not-found',
                HTTP_HOST='project.dev.readthedocs.io',
            )


# FIXME: these tests are valid, but the problem I'm facing is that the request
# is received as ``GET '//my.host/path/'`` (note that we are loosing the http:)
@pytest.mark.xfail(strict=True)
class UserRedirectCrossdomainTest(BaseDocServing):

    def test_redirect_prefix_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        fixture.get(
            Redirect,
            project=self.project, redirect_type='prefix',
            from_url='/',
        )

        r = self.client.get(
            'http://testserver/http://my.host/path.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/http://my.host/path.html',
        )

        r = self.client.get(
            'http://testserver//my.host/path.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/my.host/path.html',
        )

    def test_redirect_sphinx_htmldir_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        fixture.get(
            Redirect,
            project=self.project, redirect_type='sphinx_htmldir',
        )

        r = self.client.get(
            'http://testserver/http://my.host/path.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/http://my.host/path/',
        )

        r = self.client.get(
            'http://testserver//my.host/path.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/my.host/path/',
        )

    def test_redirect_sphinx_html_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='sphinx_html',
        )

        r = self.client.get(
            'http://testserver/http://my.host/path/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/http://my.host/path.html',
        )

        r = self.client.get(
            'http://testserver//my.host/path/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/my.host/path.html',
        )

    def test_redirect_sphinx_htmldir_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in ``to_url``.
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='sphinx_htmldir',
        )

        r = self.client.get(
            '/http://my.host/path.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/http://my.host/path/',
        )

        r = self.client.get(
            '//my.host/path.html',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/my.host/path/',
        )

    # (Pdb) proxito_path
    # '//http://my.host/path/'
    # (Pdb) urlparse(proxito_path)
    # ParseResult(scheme='', netloc='http:', path='//my.host/path/', params='', query='', fragment='')
    # (Pdb)
    # since there is a netloc inside the path
    # I'm expecting,
    # ParseResult(scheme='', netloc='', path='//http://my.host/path/', params='', query='', fragment='')
    # https://github.com/readthedocs/readthedocs.org/blob/c3001be7a3ef41ebc181c194805f86fed6a009c8/readthedocs/redirects/utils.py#L78
    def test_redirect_sphinx_html_crossdomain_nosubdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        fixture.get(
            Redirect,
            project=self.project,
            redirect_type='sphinx_html',
        )

        # NOTE: it's mandatory to use http://testserver/ URL here, otherwise the
        # request does not receive the proper URL.
        r = self.client.get(
            'http://testserver//http://my.host/path/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/http://my.host/path.html',
        )

        r = self.client.get(
            '//my.host/path/',
            HTTP_HOST='project.dev.readthedocs.io',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/my.host/path.html',
        )
