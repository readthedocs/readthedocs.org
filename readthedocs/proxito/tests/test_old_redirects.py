"""
Most of this code is copied from:

  readthedocs/rtd_tests/tests/test_redirects.py

and adapted to use:

 * El Proxito
 * USE_SUBDOMAIN=True always
"""

import pytest

from django.test.utils import override_settings
import django_dynamic_fixture as fixture

from readthedocs.builds.models import Version
from readthedocs.redirects.models import Redirect

from .base import BaseDocServing


@override_settings(
    RTD_BUILD_MEDIA_STORAGE='readthedocs.builds.storage.BuildMediaFileSystemStorage',
)
class InternalRedirectTests(BaseDocServing):

    """
    Test our own internal redirects.

    * redirects at /
    * redirects on /page/.*
    * invalid URLs
    """

    def test_root_url(self):
        r = self.client.get('/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/',
        )

    def test_page_on_main_site(self):
        r = self.client.get('/page/test.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/test.html',
        )

    def test_page_redirect_with_query_params(self):
        r = self.client.get('/page/test.html?foo=bar', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/test.html?foo=bar',
        )

    # If slug is neither valid lang nor valid version, it should 404.
    def test_url_with_nonexistent_slug(self):
        r = self.client.get('/nonexistent/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    def test_url_filename_only(self):
        r = self.client.get('/test.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    def test_url_dir_file(self):
        r = self.client.get('/nonexistent_dir/bogus.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    def test_url_dir_subdir_file(self):
        r = self.client.get('/nonexistent_dir/subdir/bogus.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    def test_url_lang_file(self):
        r = self.client.get('/en/bogus.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    # Storage backend for testing El Proxito always return True when checking if
    # a file exists. As this URL seems valid, it will return 200.
    @pytest.mark.xfail(strict=True)
    def test_url_lang_subdir_file(self):
        r = self.client.get('/en/nonexistent_dir/bogus.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    # This it's returning 404 because /latest/ does not map to a language
    # def test_improper_url_version_dir_file(self):
    #     r = self.client.get('/latest/nonexistent_dir/bogus.html', HTTP_HOST='project.dev.readthedocs.io')
    #     self.assertEqual(r.status_code, 404)

    def test_root_redirect_with_query_params(self):
        r = self.client.get('/?foo=bar', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://project.dev.readthedocs.io/en/latest/?foo=bar'
        )

    def test_improper_subdomain_filename_only(self):
        r = self.client.get('/test.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)


# Use ``PYTHON_MEDIA`` here to raise a 404 when trying to serve the file
# from disk and execute the code for the handler404 (the file does not
# exist). On production, this will happen when trying to serve from
# ``/proxito/ internal`` location
# NOTE: this could be achieved by mocking ``_serve_docs_nginx`` to raise a
# 404 directly and avoid using PYTHON_MEDIA.
@override_settings(PYTHON_MEDIA=True)
class UserRedirectTests(BaseDocServing):

    def test_redirect_prefix_infinite(self):
        """
        Avoid infinite redirects.

        If the URL hit is the same that the URL returned for redirection, we
        return a 404.

        These examples comes from this issue:
          * http://github.com/rtfd/readthedocs.org/issues/4673
        """
        Redirect.objects.create(
            project=self.project, redirect_type='prefix',
            from_url='/',
        )
        r = self.client.get('/redirect.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/redirect.html',
        )

        r = self.client.get('/redirect/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/redirect/',
        )

        r = self.client.get('/en/latest/redirect/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 404)

    # FIXME: these tests are valid, but the problem I'm facing is that the
    # request is received as ``GET '//my.host/path/'`` (note that we are loosing
    # the http://)
    @pytest.mark.xfail(strict=True)
    def test_redirect_prefix_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.project, redirect_type='prefix',
            from_url='/',
        )

        r = self.client.get('http://testserver/http://my.host/path.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/http://my.host/path.html',
        )

        r = self.client.get('http://testserver//my.host/path.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/my.host/path.html',
        )

    @pytest.mark.xfail(strict=True)
    def test_redirect_sphinx_htmldir_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.project, redirect_type='sphinx_htmldir',
        )

        r = self.client.get('http://testserver/http://my.host/path.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/http://my.host/path/',
        )

        r = self.client.get('http://testserver//my.host/path.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/my.host/path/',
        )

    @pytest.mark.xfail(strict=True)
    def test_redirect_sphinx_html_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.project, redirect_type='sphinx_html',
        )

        r = self.client.get('http://testserver/http://my.host/path/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/http://my.host/path.html',
        )

        r = self.client.get('http://testserver//my.host/path/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/my.host/path.html',
        )

    # FIXME: this seems a valid test that it's currently not passing
    @pytest.mark.xfail(strict=True)
    def test_redirect_sphinx_htmldir_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in ``to_url``.
        """
        Redirect.objects.create(
            project=self.project,
            redirect_type='sphinx_htmldir',
        )

        r = self.client.get('/http://my.host/path.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/http://my.host/path/',
        )

        r = self.client.get('//my.host/path.html', HTTP_HOST='project.dev.readthedocs.io')
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
    @pytest.mark.xfail(strict=True)
    def test_redirect_sphinx_html_crossdomain_nosubdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
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
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/http://my.host/path.html',
        )

        r = self.client.get('//my.host/path/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/my.host/path.html',
        )

    def test_redirect_root(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type='prefix',
            from_url='/woot/',
        )
        r = self.client.get('/woot/faq.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/faq.html',
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
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/tutorial/install.html',
        )


    def test_redirect_with_query_params(self):
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
        Redirect.objects.create(
            project=self.project, redirect_type='exact',
            from_url='/en/latest/install.html', to_url='/en/latest/tutorial/install.html',
        )
        r = self.client.get('/en/latest/install.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/tutorial/install.html',
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
        r = self.client.get('/en/latest/guides/install.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/version/guides/install.html',
        )

        # NOTE: I had to modify this test to add the Redirect in
        # ``self.translation`` instead of the root project. I think it makes
        # sense, but just wanted to mention to not forget to talk about :)
        fixture.get(
            Redirect,
            project=self.translation,
            redirect_type='exact',
            from_url='/es/version/$rest',
            to_url='/en/master/',  # change language and version
        )
        r = self.client.get('/es/version/guides/install.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/master/guides/install.html',
        )

    def test_redirect_inactive_version(self):
        """
        Inactive Version (``active=False``) should redirect properly.

        The function that servers the page should return 404 when serving a page
        of an inactive version and the redirect system should work.
        """
        version = fixture.get(
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
        r = self.client.get('/en/oldversion/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/newversion/',
        )

    def test_redirect_keeps_version_number(self):
        # storage_mock()().exists.return_value = False
        Redirect.objects.create(
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
        Redirect.objects.create(
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
        Redirect.objects.create(
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

    @override_settings(USE_SUBDOMAIN=True, PYTHON_MEDIA=True)
    def test_redirect_html(self):
        Redirect.objects.create(
            project=self.project, redirect_type='sphinx_html',
        )
        r = self.client.get('/en/latest/faq/', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/faq.html',
        )

    @override_settings(USE_SUBDOMAIN=True, PYTHON_MEDIA=True)
    def test_redirect_html_index(self):
        Redirect.objects.create(
            project=self.project, redirect_type='sphinx_html',
        )
        r = self.client.get('/en/latest/faq/index.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/faq.html',
        )

    @override_settings(USE_SUBDOMAIN=True, PYTHON_MEDIA=True)
    def test_redirect_htmldir(self):
        Redirect.objects.create(
            project=self.project, redirect_type='sphinx_htmldir',
        )
        r = self.client.get('/en/latest/faq.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/faq/',
        )


    def test_redirect_root_with_301_status(self):
        Redirect.objects.create(
            project=self.project, redirect_type='prefix',
            from_url='/woot/', http_status=301,
        )
        r = self.client.get('/woot/faq.html', HTTP_HOST='project.dev.readthedocs.io')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(
            r['Location'], 'http://project.dev.readthedocs.io/en/latest/faq.html',
        )
