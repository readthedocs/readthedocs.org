import copy
import mimetypes
from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.views.static import serve
from slugify import slugify as unicode_slugify

from readthedocs.audit.models import AuditLog
from readthedocs.builds.constants import EXTERNAL, INTERNAL
from readthedocs.core.resolver import resolve
from readthedocs.proxito.constants import REDIRECT_CANONICAL_CNAME, REDIRECT_HTTPS
from readthedocs.redirects.exceptions import InfiniteRedirectException
from readthedocs.storage import build_media_storage, staticfiles_storage

log = structlog.get_logger(__name__)  # noqa


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

        If ``download`` and ``version_slug`` are passed,
        the HTTP header ``Content-Disposition`` is added with the proper
        filename (e.g. "pip-pypa-io-en-latest.pdf" or "pip-pypi-io-en-v2.0.pdf"
        or "docs-celeryproject-org-kombu-en-stable.pdf")
        """

        self._track_pageview(
            project=final_project,
            path=path,
            request=request,
            download=download,
        )
        if settings.PYTHON_MEDIA:
            response = self._serve_file_from_python(request, path, build_media_storage)
        else:
            response = self._serve_file_from_nginx(path, root_path="proxito")

        # Set the filename of the download.
        if download:
            filename_ext = urlparse(path).path.rsplit(".", 1)[-1]
            domain = unicode_slugify(final_project.subdomain().replace(".", "-"))
            if final_project.is_subproject:
                alias = final_project.alias
                filename = f"{domain}-{alias}-{final_project.language}-{version_slug}.{filename_ext}"  # noqa
            else:
                filename = (
                    f"{domain}-{final_project.language}-{version_slug}.{filename_ext}"
                )
            response["Content-Disposition"] = f"filename={filename}"

        return response

    def _track_pageview(self, project, path, request, download):
        """Create an audit log of the page view if audit is enabled."""
        # Remove any query args (like the token access from AWS).
        path_only = urlparse(path).path
        track_file = path_only.endswith(('.html', '.pdf', '.epub', '.zip'))
        if track_file and self._is_audit_enabled(project):
            action = AuditLog.DOWNLOAD if download else AuditLog.PAGEVIEW
            AuditLog.objects.new(
                action=action,
                user=request.user,
                request=request,
                project=project,
            )

    def _is_audit_enabled(self, project):
        """
        Check if the project has the audit feature enabled to track individual page views.

        This feature is different from page views analytics,
        as it records every page view individually with more metadata like the user, IP, etc.
        """
        return False

    def _serve_static_file(self, request, path):
        if settings.PYTHON_MEDIA:
            return self._serve_file_from_python(request, path, staticfiles_storage)
        return self._serve_file_from_nginx(path, root_path="proxito-static")

    def _serve_file_from_nginx(self, path, root_path):
        """
        Serve a file from nginx.

        Returns a response with ``X-Accel-Redirect``, which will cause nginx to
        serve it directly as an internal redirect.

        :param path: The path of the file to serve.
        :param root_path: The root path of the internal redirect.
        """
        original_path = copy.copy(path)
        if not path.startswith(f"/{root_path}/"):
            if path[0] == '/':
                path = path[1:]
            path = f"/{root_path}/{path}"

        log.debug(
            'Nginx serve.',
            original_path=original_path,
            path=path,
        )

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

        # Needed to strip any GET args, etc.
        response.proxito_path = urlparse(path).path
        return response

    def _serve_file_from_python(self, request, path, storage):
        """
        Serve a file from Python.

        .. warning:: Don't use this in production!
        """
        log.debug("Django serve.", path=path)
        root_path = storage.path("")
        return serve(request, path, root_path)

    def _serve_401(self, request, project):
        res = render(request, '401.html')
        res.status_code = 401
        log.debug('Unauthorized access to documentation.', project_slug=project.slug)
        return res

    def allowed_user(self, *args, **kwargs):
        return True

    def get_version_from_host(self, request, version_slug):
        # Handle external domain
        if hasattr(request, 'external_domain'):
            self.version_type = EXTERNAL
            log.warning(
                'Using version slug from host.',
                version_slug=version_slug,
                host_version=request.host_version_slug,
            )
            version_slug = request.host_version_slug
        return version_slug

    def _spam_response(self, request, project):
        if 'readthedocsext.spamfighting' in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.utils import is_serve_docs_denied  # noqa
            if is_serve_docs_denied(project):
                return render(request, template_name='spam.html', status=410)


class ServeRedirectMixin:

    def system_redirect(self, request, final_project, lang_slug, version_slug, filename):
        """
        Return a redirect that is defined by RTD instead of the user.

        This is normally used for `/` and `/page/*` redirects.
        """
        urlparse_result = urlparse(request.get_full_path())
        if hasattr(request, 'external_domain'):
            log.debug('Request is external')
        to = resolve(
            project=final_project,
            version_slug=version_slug,
            filename=filename,
            query_params=urlparse_result.query,
            external=hasattr(request, 'external_domain'),
        )
        log.debug(
            "System Redirect.", host=request.get_host(), from_url=filename, to_url=to
        )
        resp = HttpResponseRedirect(to)
        resp['X-RTD-Redirect'] = 'system'
        return resp

    def canonical_redirect(self, request, final_project, version_slug, filename):
        """
        Return a redirect to the canonical domain including scheme.

        The following cases are covered:

        - Redirect a custom domain from http to https (if supported)
          http://project.rtd.io/ -> https://project.rtd.io/
        - Redirect a domain to a canonical domain (http or https).
          http://project.rtd.io/ -> https://docs.test.com/
          http://project.rtd.io/foo/bar/ -> https://docs.test.com/foo/bar/
        - Redirect from a subproject domain to the main domain
          https://subproject.rtd.io/en/latest/foo -> https://main.rtd.io/projects/subproject/en/latest/foo  # noqa
          https://subproject.rtd.io/en/latest/foo -> https://docs.test.com/projects/subproject/en/latest/foo  # noqa
        """
        from_url = request.build_absolute_uri()
        parsed_from = urlparse(from_url)

        redirect_type = getattr(request, 'canonicalize', None)
        if redirect_type == REDIRECT_HTTPS:
            to = parsed_from._replace(scheme='https').geturl()
        else:
            to = resolve(
                project=final_project,
                version_slug=version_slug,
                filename=filename,
                query_params=parsed_from.query,
                external=hasattr(request, 'external_domain'),
            )
            # When a canonical redirect is done, only change the domain.
            if redirect_type == REDIRECT_CANONICAL_CNAME:
                parsed_to = urlparse(to)
                to = parsed_from._replace(
                    scheme=parsed_to.scheme,
                    netloc=parsed_to.netloc,
                ).geturl()

        if from_url == to:
            # check that we do have a response and avoid infinite redirect
            log.warning(
                'Infinite Redirect: FROM URL is the same than TO URL.',
                url=to,
            )
            raise InfiniteRedirectException()

        log.info('Canonical Redirect.', host=request.get_host(), from_url=filename, to_url=to)
        resp = HttpResponseRedirect(to)
        resp['X-RTD-Redirect'] = getattr(request, 'canonicalize', 'unknown')
        return resp

    def get_redirect(
        self, project, lang_slug, version_slug, filename, full_path, forced_only=False
    ):
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
            forced_only=forced_only,
        )
        return redirect_path, http_status

    def get_redirect_response(self, request, redirect_path, proxito_path, http_status):
        """
        Build the response for the ``redirect_path``, ``proxito_path`` and its ``http_status``.

        :returns: redirect response with the correct path
        :rtype: HttpResponseRedirect or HttpResponsePermanentRedirect
        """
        # `proxito_path` doesn't include query params.
        query = urlparse(request.get_full_path()).query
        # Pass the query params from the original request to the redirect.
        new_path = urlparse(redirect_path)._replace(query=query).geturl()

        # Re-use the domain and protocol used in the current request.
        # Redirects shouldn't change the domain, version or language.
        # However, if the new_path is already an absolute URI, just use it
        new_path = request.build_absolute_uri(new_path)
        log.info(
            'Redirecting...',
            from_url=request.build_absolute_uri(proxito_path),
            to_url=new_path,
            http_status_code=http_status,
        )

        if request.build_absolute_uri(proxito_path) == new_path:
            # check that we do have a response and avoid infinite redirect
            log.warning(
                'Infinite Redirect: FROM URL is the same than TO URL.',
                url=new_path,
            )
            raise InfiniteRedirectException()

        if http_status and http_status == 301:
            resp = HttpResponsePermanentRedirect(new_path)
        else:
            resp = HttpResponseRedirect(new_path)

        # Add a user-visible header to make debugging easier
        resp['X-RTD-Redirect'] = 'user'
        return resp
