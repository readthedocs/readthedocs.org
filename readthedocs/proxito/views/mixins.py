import copy
import logging
import mimetypes
from urllib.parse import urlparse, urlunparse
from slugify import slugify as unicode_slugify

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
)
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.views.static import serve

from readthedocs.builds.constants import EXTERNAL, INTERNAL
from readthedocs.core.resolver import resolve
from readthedocs.redirects.exceptions import InfiniteRedirectException

log = logging.getLogger(__name__)  # noqa


class ServeDocsMixin:

    """Class implementing all the logic to serve a document."""

    version_type = INTERNAL

    def _serve_docs(
            self,
            request,
            final_project,
            path,
            download=False,
            version_slug=None,
    ):
        """
        Serve documentation in the way specified by settings.

        Serve from the filesystem if using ``PYTHON_MEDIA``. We definitely
        shouldn't do this in production, but I don't want to force a check for
        ``DEBUG``.

        If ``download`` and ``version_slug`` are passed, when serving via NGINX
        the HTTP header ``Content-Disposition`` is added with the proper
        filename (e.g. "pip-pypa-io-en-latest.pdf" or "pip-pypi-io-en-v2.0.pdf"
        or "docs-celeryproject-org-kombu-en-stable.pdf")
        """

        if settings.PYTHON_MEDIA:
            return self._serve_docs_python(
                request,
                final_project=final_project,
                path=path,
            )

        return self._serve_docs_nginx(
            request,
            final_project=final_project,
            version_slug=version_slug,
            path=path,
            download=download,
        )

    def _serve_docs_python(self, request, final_project, path):
        """
        Serve docs from Python.

        .. warning:: Don't do this in production!
        """
        log.info('[Django serve] path=%s, project=%s', path, final_project.slug)

        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        root_path = storage.path('')
        # Serve from Python
        return serve(request, path, root_path)

    def _serve_docs_nginx(self, request, final_project, version_slug, path, download):
        """
        Serve docs from nginx.

        Returns a response with ``X-Accel-Redirect``, which will cause nginx to
        serve it directly as an internal redirect.
        """

        original_path = copy.copy(path)
        if not path.startswith('/proxito/'):
            if path[0] == '/':
                path = path[1:]
            path = f'/proxito/{path}'

        log.info('[Nginx serve] original_path=%s, proxito_path=%s, project=%s',
                 original_path, path, final_project.slug)

        content_type, encoding = mimetypes.guess_type(path)
        content_type = content_type or 'application/octet-stream'
        response = HttpResponse(
            f'Serving internal path: {path}', content_type=content_type
        )
        if encoding:
            response['Content-Encoding'] = encoding

        # NGINX does not support non-ASCII characters in the header, so we
        # convert the IRI path to URI so it's compatible with what NGINX expects
        # as the header value.
        # https://github.com/benoitc/gunicorn/issues/1448
        # https://docs.djangoproject.com/en/1.11/ref/unicode/#uri-and-iri-handling
        x_accel_redirect = iri_to_uri(path)
        response['X-Accel-Redirect'] = x_accel_redirect

        if download:
            filename_ext = urlparse(path).path.rsplit('.', 1)[-1]
            domain = unicode_slugify(final_project.subdomain().replace('.', '-'))
            if final_project.is_subproject:
                alias = final_project.alias
                filename = f'{domain}-{alias}-{final_project.language}-{version_slug}.{filename_ext}'  # noqa
            else:
                filename = f'{domain}-{final_project.language}-{version_slug}.{filename_ext}'
            response['Content-Disposition'] = f'filename={filename}'

        # Add debugging headers to proxito responses
        response['X-RTD-Domain'] = request.get_host()
        response['X-RTD-Project'] = final_project.slug
        response['X-RTD-Version'] = version_slug
        response['X-RTD-Path'] = path
        if hasattr(request, 'rtdheader'):
            response['X-RTD-Version-Method'] = 'rtdheader'
        if hasattr(request, 'subdomain'):
            response['X-RTD-Version-Method'] = 'subdomain'
        if hasattr(request, 'external_domain'):
            response['X-RTD-Version-Method'] = 'external_domain'
        if hasattr(request, 'cname'):
            response['X-RTD-Version-Method'] = 'cname'

        return response

    def _serve_401(self, request, project):
        res = render(request, '401.html')
        res.status_code = 401
        log.debug('Unauthorized access to %s documentation', project.slug)
        return res

    def allowed_user(self, *args, **kwargs):
        return True

    def get_version_from_host(self, request, version_slug):
        # Handle external domain
        if hasattr(request, 'external_domain'):
            self.version_type = EXTERNAL
            log.warning('Using version slug from host. url_version=%s host_version=%s',
                        version_slug, request.host_version_slug)
            version_slug = request.host_version_slug
        return version_slug


class ServeRedirectMixin:

    def system_redirect(self, request, final_project, lang_slug, version_slug, filename):
        """
        Return a redirect that is defined by RTD instead of the user.

        This is normally used for `/` and `/page/*` redirects.
        """
        urlparse_result = urlparse(request.get_full_path())
        to = resolve(
            project=final_project,
            version_slug=version_slug,
            filename=filename,
            query_params=urlparse_result.query,
            external=hasattr(request, 'external_domain'),
        )
        log.info('System Redirect: host=%s, from=%s, to=%s', request.get_host(), filename, to)
        resp = HttpResponseRedirect(to)
        resp['X-RTD-System-Redirect'] = True
        return resp

    def get_redirect(self, project, lang_slug, version_slug, filename, full_path):
        """
        Check for a redirect for this project that matches ``full_path``.

        :returns: the path to redirect the request and its status code
        :rtype: tuple
        """
        redirect_path, http_status = project.redirects.get_redirect_path_with_status(
            language=lang_slug,
            version_slug=version_slug,
            path=filename,
            full_path=full_path,
        )
        return redirect_path, http_status

    def get_redirect_response(self, request, redirect_path, proxito_path, http_status):
        """
        Build the response for the ``redirect_path``, ``proxito_path`` and its ``http_status``.

        :returns: redirect respose with the correct path
        :rtype: HttpResponseRedirect or HttpResponsePermanentRedirect
        """

        schema, netloc, path, params, query, fragments = urlparse(proxito_path)
        new_path = urlunparse((schema, netloc, redirect_path, params, query, fragments))

        # Re-use the domain and protocol used in the current request.
        # Redirects shouldn't change the domain, version or language.
        # However, if the new_path is already an absolute URI, just use it
        new_path = request.build_absolute_uri(new_path)
        log.info(
            'Redirecting: from=%s to=%s http_status=%s',
            request.build_absolute_uri(proxito_path),
            new_path,
            http_status,
        )

        if request.build_absolute_uri(proxito_path) == new_path:
            # check that we do have a response and avoid infinite redirect
            log.warning(
                'Infinite Redirect: FROM URL is the same than TO URL. url=%s',
                new_path,
            )
            raise InfiniteRedirectException()

        if http_status and http_status == 301:
            resp = HttpResponsePermanentRedirect(new_path)
        else:
            resp = HttpResponseRedirect(new_path)

        # Add a user-visible header to make debugging easier
        resp['X-RTD-User-Redirect'] = True
        return resp
