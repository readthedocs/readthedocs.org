import copy
import mimetypes
from urllib.parse import parse_qsl, urlencode, urlparse

import structlog
from django.conf import settings
from django.core.exceptions import BadRequest
from django.http import (
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.views.static import serve
from slugify import slugify as unicode_slugify

from readthedocs.analytics.tasks import analytics_event
from readthedocs.analytics.utils import get_client_ip
from readthedocs.audit.models import AuditLog
from readthedocs.builds.constants import INTERNAL
from readthedocs.core.resolver import resolve
from readthedocs.projects.constants import MEDIA_TYPE_HTML
from readthedocs.proxito.constants import RedirectType
from readthedocs.redirects.exceptions import InfiniteRedirectException
from readthedocs.storage import build_media_storage, staticfiles_storage
from readthedocs.subscriptions.constants import TYPE_AUDIT_PAGEVIEWS
from readthedocs.subscriptions.products import get_feature

log = structlog.get_logger(__name__)


class InvalidPathError(Exception):

    """An invalid path was passed to storage."""


class StorageFileNotFound(Exception):

    """The file wasn't found in the storage backend."""


class ServeDocsMixin:

    """Class implementing all the logic to serve a document."""

    # We force all storage calls to use internal versions
    # unless explicitly set to external.
    version_type = INTERNAL

    def _serve_docs(self, request, project, version, filename, check_if_exists=False):
        """
        Serve a documentation file.

        :param check_if_exists: If `True` we check if the file exists before trying
         to serve it. This will raisen an exception if the file doesn't exists.
         Useful to make sure were are serving a file that exists in storage,
         checking if the file exists will make one additional request to the storage.
        """
        base_storage_path = project.get_storage_path(
            type_=MEDIA_TYPE_HTML,
            version_slug=version.slug,
            include_file=False,
            # Force to always read from the internal or extrernal storage,
            # according to the current request.
            version_type=self.version_type,
        )

        # Handle our backend storage not supporting directory indexes,
        # so we need to append index.html when appropriate.
        if not filename or filename.endswith("/"):
            filename += "index.html"

        # If the filename starts with `/`, the join will fail,
        # so we strip it before joining it.
        try:
            storage_path = build_media_storage.join(
                base_storage_path, filename.lstrip("/")
            )
        except ValueError:
            # We expect this exception from the django storages safe_join
            # function, when the filename resolves to a higher relative path.
            # The request is malicious or malformed in this case.
            raise BadRequest("Invalid URL")

        if check_if_exists and not build_media_storage.exists(storage_path):
            raise StorageFileNotFound

        self._track_pageview(
            project=project,
            path=filename,
            request=request,
            download=False,
        )
        return self._serve_file(
            request=request,
            storage_path=storage_path,
            storage_backend=build_media_storage,
        )

    def _serve_dowload(self, request, project, version, type_):
        """
        Serve downloadable content for the given version.

        The HTTP header ``Content-Disposition`` is added with the proper
        filename (e.g. "pip-pypa-io-en-latest.pdf" or "pip-pypi-io-en-v2.0.pdf"
        or "docs-celeryproject-org-kombu-en-stable.pdf").
        """
        storage_path = project.get_storage_path(
            type_=type_,
            version_slug=version.slug,
            # Force to always read from the internal or extrernal storage,
            # according to the current request.
            version_type=self.version_type,
            include_file=True,
        )
        self._track_pageview(
            project=project,
            path=storage_path,
            request=request,
            download=True,
        )

        # Send media download to analytics - sensitive data is anonymized
        analytics_event.delay(
            event_category="Build Media",
            event_action=f"Download {type_}",
            event_label=str(version),
            ua=request.headers.get("User-Agent"),
            uip=get_client_ip(request),
        )

        response = self._serve_file(
            request=request,
            storage_path=storage_path,
            storage_backend=build_media_storage,
        )

        # Set the filename of the download.
        filename_ext = storage_path.rsplit(".", 1)[-1]
        domain = unicode_slugify(project.subdomain().replace(".", "-"))
        if project.is_subproject:
            filename = f"{domain}-{project.alias}-{project.language}-{version.slug}.{filename_ext}"
        else:
            filename = f"{domain}-{project.language}-{version.slug}.{filename_ext}"
        response["Content-Disposition"] = f"filename={filename}"
        return response

    def _serve_file(self, request, storage_path, storage_backend):
        """
        Serve a file from storage.

        Serve from the filesystem if using ``PYTHON_MEDIA``. We definitely
        shouldn't do this in production, but I don't want to force a check for
        ``DEBUG``.

        :param storage_path: Path to file to serve.
        :param storage_backend: Storage backend class from where to serve the file.
        """
        storage_url = self._get_storage_url(
            request=request,
            storage_path=storage_path,
            storage_backend=storage_backend,
        )
        if settings.PYTHON_MEDIA:
            return self._serve_file_from_python(request, storage_url, storage_backend)

        return self._serve_file_from_nginx(
            storage_url,
            root_path=storage_backend.internal_redirect_root_path,
        )

    def _get_storage_url(self, request, storage_path, storage_backend):
        """
        Get the full storage URL from a storage path.

        The URL will be without scheme and domain,
        this is to perform an NGINX internal redirect.
        Authorization query arguments will stay in place
        (useful for private buckets).
        """
        # We are catching a broader exception,
        # since depending on the storage backend,
        # an invalid path may raise a different exception.
        try:
            # NOTE: calling ``.url`` will remove any double slashes.
            # e.g: '/foo//bar///' -> '/foo/bar/'.
            storage_url = storage_backend.url(storage_path, http_method=request.method)
        except Exception as e:
            log.info("Invalid storage path.", path=storage_path, exc_info=e)
            raise InvalidPathError

        parsed_url = urlparse(storage_url)._replace(scheme="", netloc="")
        return parsed_url.geturl()

    def _track_pageview(self, project, path, request, download):
        """Create an audit log of the page view if audit is enabled."""
        # Remove any query args (like the token access from AWS).
        path_only = urlparse(path).path
        track_file = path_only.endswith((".html", ".pdf", ".epub", ".zip"))
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
        return bool(get_feature(project, feature_type=TYPE_AUDIT_PAGEVIEWS))

    def _serve_static_file(self, request, filename):
        return self._serve_file(
            request=request,
            storage_path=filename,
            storage_backend=staticfiles_storage,
        )

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
            if path[0] == "/":
                path = path[1:]
            path = f"/{root_path}/{path}"

        log.debug(
            "Nginx serve.",
            original_path=original_path,
            path=path,
        )

        content_type, encoding = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"
        response = HttpResponse(
            f"Serving internal path: {path}", content_type=content_type
        )
        if encoding:
            response["Content-Encoding"] = encoding

        # NGINX does not support non-ASCII characters in the header, so we
        # convert the IRI path to URI so it's compatible with what NGINX expects
        # as the header value.
        # https://github.com/benoitc/gunicorn/issues/1448
        # https://docs.djangoproject.com/en/1.11/ref/unicode/#uri-and-iri-handling
        x_accel_redirect = iri_to_uri(path)
        response["X-Accel-Redirect"] = x_accel_redirect

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
        res = render(request, "401.html")
        res.status_code = 401
        log.debug("Unauthorized access to documentation.", project_slug=project.slug)
        return res

    def allowed_user(self, request, version):
        return True

    def _spam_response(self, request, project):
        if "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.utils import is_serve_docs_denied  # noqa

            if is_serve_docs_denied(project):
                return render(request, template_name="spam.html", status=410)


class ServeRedirectMixin:
    def system_redirect(
        self, request, final_project, version_slug, filename, is_external_version=False
    ):
        """
        Return a redirect that is defined by RTD instead of the user.

        This is normally used for `/` and `/page/*` redirects.

        :param request: Request object.
        :param final_project: The current project being served.
        :param version_slug: The current version slug being served.
        :param filename: The filename being served.
        :param external: If the version is from a pull request preview.
        """
        urlparse_result = urlparse(request.get_full_path())
        to = resolve(
            project=final_project,
            version_slug=version_slug,
            filename=filename,
            query_params=urlparse_result.query,
            external=is_external_version,
        )
        log.debug(
            "System Redirect.", host=request.get_host(), from_url=filename, to_url=to
        )
        # All system redirects can be cached, since the final URL will check for authz.
        self.cache_response = True
        resp = HttpResponseRedirect(to)
        resp["X-RTD-Redirect"] = RedirectType.system.name
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
        query_list = parse_qsl(
            urlparse(request.get_full_path()).query,
            keep_blank_values=True,
        )

        # Combine the query params from the original request with the ones from the redirect.
        redirect_parsed = urlparse(redirect_path)
        query_list.extend(parse_qsl(redirect_parsed.query, keep_blank_values=True))
        query = urlencode(query_list)
        new_path = redirect_parsed._replace(query=query).geturl()

        # Re-use the domain and protocol used in the current request.
        # Redirects shouldn't change the domain, version or language.
        # However, if the new_path is already an absolute URI, just use it
        new_path = request.build_absolute_uri(new_path)
        log.debug(
            "Redirecting...",
            from_url=request.build_absolute_uri(proxito_path),
            to_url=new_path,
            http_status_code=http_status,
        )

        new_path_parsed = urlparse(new_path)
        old_path_parsed = urlparse(request.build_absolute_uri(proxito_path))
        # Check explicitly only the path and hostname, since a different
        # protocol or query parameters could lead to a infinite redirect.
        if (
            new_path_parsed.hostname == old_path_parsed.hostname
            and new_path_parsed.path == old_path_parsed.path
        ):
            # check that we do have a response and avoid infinite redirect
            log.debug(
                "Infinite Redirect: FROM URL is the same than TO URL.",
                url=new_path,
            )
            raise InfiniteRedirectException()

        if http_status and http_status == 301:
            resp = HttpResponsePermanentRedirect(new_path)
        else:
            resp = HttpResponseRedirect(new_path)

        # Add a user-visible header to make debugging easier
        resp["X-RTD-Redirect"] = RedirectType.user.name
        return resp
