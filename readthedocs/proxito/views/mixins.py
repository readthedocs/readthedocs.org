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

log = logging.getLogger(__name__)  # noqa


class ServeDocsMixin:

    """Class implementing all the logic to serve a document."""

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
        log.info('[Nginx serve] path=%s, project=%s', path, final_project.slug)

        if not path.startswith('/proxito/'):
            if path[0] == '/':
                path = path[1:]
            path = f'/proxito/{path}'

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
                filename = f'{domain}-{alias}-{final_project.language}-{version_slug}.{filename_ext}'
            else:
                filename = f'{domain}-{final_project.language}-{version_slug}.{filename_ext}'
            response['Content-Disposition'] = f'filename={filename}'

        return response

    def _serve_401(self, request, project):
        res = render(request, '401.html')
        res.status_code = 401
        log.debug('Unauthorized access to %s documentation', project.slug)
        return res


class ServeRedirectMixin:

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

    def get_redirect_response(self, request, redirect_path, http_status):
        """
        Build the response for the ``redirect_path`` and its ``http_status``.

        :returns: redirect respose with the correct path
        :rtype: HttpResponseRedirect or HttpResponsePermanentRedirect
        """
        schema, netloc, path, params, query, fragments = urlparse(request.path)
        new_path = urlunparse((schema, netloc, redirect_path, params, query, fragments))

        # Re-use the domain and protocol used in the current request.
        # Redirects shouldn't change the domain, version or language.
        # However, if the new_path is already an absolute URI, just use it
        new_path = request.build_absolute_uri(new_path)
        log.info(
            'Redirecting: from=%s to=%s http_status=%s',
            request.build_absolute_uri(),
            new_path,
            http_status,
        )

        if http_status and http_status == 301:
            return HttpResponsePermanentRedirect(new_path)

        return HttpResponseRedirect(new_path)
