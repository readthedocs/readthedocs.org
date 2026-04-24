"""
Middleware for Proxito.

This is used to take the request and map the host to the proper project slug.

Additional processing is done to get the project from the URL in the ``views.py`` as well.
"""

import re
from urllib.parse import urlparse

import structlog
from corsheaders.middleware import ACCESS_CONTROL_ALLOW_METHODS
from corsheaders.middleware import ACCESS_CONTROL_ALLOW_ORIGIN
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import iri_to_uri
from django.utils.html import escape

from readthedocs.core.unresolver import InvalidCustomDomainError
from readthedocs.core.unresolver import InvalidExternalDomainError
from readthedocs.core.unresolver import InvalidSubdomainError
from readthedocs.core.unresolver import InvalidXRTDSlugHeaderError
from readthedocs.core.unresolver import SuspiciousHostnameError
from readthedocs.core.unresolver import unresolver
from readthedocs.core.utils import get_cache_tag
from readthedocs.projects.models import AddonsConfig
from readthedocs.proxito.cache import add_cache_tags
from readthedocs.proxito.cache import cache_response
from readthedocs.proxito.cache import private_response
from readthedocs.proxito.redirects import redirect_to_https

from .exceptions import DomainDNSHttp404
from .exceptions import ProjectHttp404


log = structlog.get_logger(__name__)


class ProxitoMiddleware(MiddlewareMixin):
    """The actual middleware we'll be using in prod."""

    # None of these need the proxito request middleware (response is needed).
    # The analytics API isn't listed because it depends on the unresolver,
    # which depends on the proxito middleware.
    skip_views = (
        "health_check",
        "search_api",
        "embed_api",
    )

    def add_proxito_headers(self, request, response):
        """Add debugging and cache headers to proxito responses."""

        project_slug = getattr(request, "path_project_slug", "")
        version_slug = getattr(request, "path_version_slug", "")
        path = getattr(response, "proxito_path", "")

        response["X-RTD-Domain"] = request.get_host()
        response["X-RTD-Project"] = project_slug

        if version_slug:
            response["X-RTD-Version"] = version_slug

        if path:
            response["X-RTD-Path"] = path

        # Include the project & project-version so we can do larger purges if needed
        cache_tags = []
        if project_slug:
            cache_tags.append(project_slug)
        if version_slug:
            cache_tags.append(get_cache_tag(project_slug, version_slug))

        if cache_tags:
            add_cache_tags(response, cache_tags)

        unresolved_domain = request.unresolved_domain
        if unresolved_domain:
            response["X-RTD-Project-Method"] = unresolved_domain.source.name
            if unresolved_domain.is_from_external_domain:
                response["X-RTD-Version-Method"] = "domain"
            else:
                response["X-RTD-Version-Method"] = "path"

    def add_user_headers(self, request, response):
        """
        Set specific HTTP headers requested by the user.

        The headers added come from ``projects.models.HTTPHeader`` associated
        with the ``Domain`` object.
        """
        unresolved_domain = request.unresolved_domain
        if unresolved_domain and unresolved_domain.is_from_custom_domain:
            response_headers = [header.lower() for header in response.headers.keys()]
            domain = unresolved_domain.domain
            for http_header in domain.http_headers.all():
                if http_header.name.lower() in response_headers:
                    log.error(
                        "Overriding an existing response HTTP header.",
                        http_header=http_header.name,
                        domain=domain.domain,
                    )
                log.debug(
                    "Adding custom response HTTP header.",
                    http_header=http_header.name,
                    domain=domain.domain,
                )

                if http_header.only_if_secure_request and not request.is_secure():
                    continue

                # HTTP headers here are limited to
                # ``HTTPHeader.HEADERS_CHOICES`` since adding arbitrary HTTP
                # headers is potentially dangerous
                response[http_header.name] = http_header.value

    def add_hsts_headers(self, request, response):
        """
        Set the Strict-Transport-Security (HSTS) header for docs sites.

        * For the public domain, set the HSTS header if settings.PUBLIC_DOMAIN_USES_HTTPS
        * For custom domains, check the HSTS values on the Domain object.
          The domain object should be saved already in request.domain.
        """
        if not request.is_secure():
            # Only set the HSTS header if the request is over HTTPS
            return response

        hsts_header_values = []
        unresolved_domain = request.unresolved_domain
        if (
            settings.PUBLIC_DOMAIN_USES_HTTPS
            and unresolved_domain
            and unresolved_domain.is_from_public_domain
        ):
            hsts_header_values = [
                "max-age=31536000",
                "includeSubDomains",
                "preload",
            ]
        elif unresolved_domain and unresolved_domain.is_from_custom_domain:
            domain = unresolved_domain.domain
            # TODO: migrate Domains with HSTS set using these fields to
            # ``HTTPHeader`` and remove this chunk of code from here.
            if domain.hsts_max_age:
                hsts_header_values.append(f"max-age={domain.hsts_max_age}")
                # These other options don't make sense without max_age > 0
                if domain.hsts_include_subdomains:
                    hsts_header_values.append("includeSubDomains")
                if domain.hsts_preload:
                    hsts_header_values.append("preload")

        if hsts_header_values:
            # See https://tools.ietf.org/html/rfc6797
            response["Strict-Transport-Security"] = "; ".join(hsts_header_values)

    def add_cache_headers(self, request, response):
        """Add `Cache-Control: no-cache` header (browser level) for external versions."""
        unresolved_domain = request.unresolved_domain
        if unresolved_domain and unresolved_domain.is_from_external_domain:
            response["Cache-Control"] = "no-cache"

    def add_cdn_cache_headers(self, request, response):
        """
        Add Cache-Control headers.

        If the `CDN-Cache-Control` header isn't already present, set the cache
        level to public or private, depending if we allow private repos or not.
        Or if the request was from the `X-RTD-Slug` header, we don't cache the
        response, since we could be caching a response in another domain.

        We use ``CDN-Cache-Control``, to control caching at the CDN level only.
        This doesn't affect caching at the browser level (``Cache-Control``).

        See https://developers.cloudflare.com/cache/about/cdn-cache-control.
        """
        unresolved_domain = request.unresolved_domain
        # Never trust projects resolving from the X-RTD-Slug header,
        # we don't want to cache their content on domains from other
        # projects, see GHSA-mp38-vprc-7hf5.
        if unresolved_domain and unresolved_domain.is_from_http_header:
            private_response(response, force=True)
            # SECURITY: Return early, we never want to cache this response.
            return

        # Mark the response as private or cache it, if it hasn't been marked as so already.
        if settings.ALLOW_PRIVATE_REPOS:
            private_response(response, force=False)
        else:
            cache_response(response, force=False)

    def add_x_robots_tag_headers(self, request, response):
        """Add `X-Robots-Tag: noindex` header for external versions."""
        unresolved_domain = request.unresolved_domain
        if unresolved_domain and unresolved_domain.is_from_external_domain:
            response["X-Robots-Tag"] = "noindex"

    def _set_request_attributes(self, request, unresolved_domain):
        """
        Set attributes in the request from the unresolved domain.

        - Set ``request.unresolved_domain`` to the unresolved domain.
        """
        request.unresolved_domain = unresolved_domain

    def process_request(self, request):  # noqa
        # Initialize our custom request attributes.
        request.unresolved_domain = None
        request.unresolved_url = None

        skip = any(request.path.startswith(reverse(view)) for view in self.skip_views)
        if skip:
            log.debug("Not processing Proxito middleware")
            return None

        try:
            unresolved_domain = unresolver.unresolve_domain_from_request(request)
        except SuspiciousHostnameError as exc:
            log.debug("Weird variation on our hostname.", domain=exc.domain)
            # Raise a contextualized 404 that will be handled by proxito's 404 handler
            raise DomainDNSHttp404(
                http_status=400,
                domain=exc.domain,
            ) from exc
        except (InvalidSubdomainError, InvalidExternalDomainError) as exc:
            log.debug("Invalid project set on the subdomain.")
            # Raise a contextualized 404 that will be handled by proxito's 404 handler
            raise ProjectHttp404(
                domain=exc.domain,
            ) from exc
        except InvalidCustomDomainError as exc:
            # Some person is CNAMEing to us without configuring a domain - 404.
            log.debug("CNAME 404.", domain=exc.domain)
            # Raise a contextualized 404 that will be handled by proxito's 404 handler
            raise DomainDNSHttp404(
                domain=exc.domain,
            ) from exc
        except InvalidXRTDSlugHeaderError as exc:
            raise SuspiciousOperation("Invalid X-RTD-Slug header.") from exc

        self._set_request_attributes(request, unresolved_domain)

        response = self._get_https_redirect(request)
        if response:
            return response

        # Remove multiple slashes from URL's
        if "//" in request.path:
            url_parsed = urlparse(request.get_full_path())
            clean_path = re.sub("//+", "/", url_parsed.path)
            new_parsed = url_parsed._replace(path=clean_path)
            final_url = new_parsed.geturl()
            # This protects against a couple issues:
            # * First is a URL like `//` which urlparse will return as a path of ''
            # * Second is URLs like `//google.com` which urlparse will return as `//google.com`
            #   We make sure there is _always_ a single slash in front to ensure relative redirects,
            #   instead of `//` redirects which are actually alternative domains.
            final_url = "/" + final_url.lstrip("/")
            log.debug(
                "Proxito Slash Redirect.",
                from_url=request.get_full_path(),
                to_url=final_url,
            )
            response = redirect(final_url)
            cache_response(response, cache_tags=[unresolved_domain.project.slug])
            return response

        project = unresolved_domain.project
        log.debug(
            "Proxito Project.",
            project_slug=project.slug,
        )

        return None

    def add_hosting_integrations_headers(self, request, response):
        """
        Add HTTP headers to communicate to Cloudflare Workers.

        We have configured Cloudflare Workers to inject the addons and remove
        the old flyout integration based on HTTP headers.
        This method uses two different headers for these purposes:

        - ``X-RTD-Force-Addons``: inject ``readthedocs-addons.js``
          and remove old flyout integration (via ``readthedocs-doc-embed.js``).
          Enabled on all projects by default starting on Oct 7, 2024.

        """
        addons = False
        project_slug = getattr(request, "path_project_slug", "")

        if project_slug:
            addons = AddonsConfig.objects.filter(project__slug=project_slug).first()

            if addons:
                if addons.enabled:
                    response["X-RTD-Force-Addons"] = "true"

    def add_cors_headers(self, request, response):
        """
        Add CORS headers only to files from docs.

        DocDiff addons requires making a request from
        ``RTD_EXTERNAL_VERSION_DOMAIN`` to ``PUBLIC_DOMAIN`` to be able to
        compare both DOMs and show the visual differences.

        This request needs ``Access-Control-Allow-Origin`` HTTP headers to be
        accepted by browsers. However, we cannot allow passing credentials,
        since we don't want cross-origin requests to be able to access
        private versions.

        We set this header to `*`, we don't care about the origin of the request.
        And we don't have the need nor want to allow passing credentials from
        cross-origin requests.

        See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin.
        """
        # TODO: se should add these headers to files from docs only,
        # proxied APIs and other endpoints should not have CORS headers.
        # These attributes aren't currently set for proxied APIs, but we shuold
        # find a better way to do this.
        project_slug = getattr(request, "path_project_slug", "")
        version_slug = getattr(request, "path_version_slug", "")

        if project_slug and version_slug:
            response.headers[ACCESS_CONTROL_ALLOW_ORIGIN] = "*"
            response.headers[ACCESS_CONTROL_ALLOW_METHODS] = "HEAD, OPTIONS, GET"

        return response

    def _get_https_redirect(self, request):
        """
        Get a redirect response if the request should be redirected to HTTPS.

        A request should be redirected to HTTPS if any of the following conditions are met:

        - It's from a custom domain and the domain has HTTPS enabled.
        - It's from a public domain, and the public domain uses HTTPS.
        """
        if request.is_secure():
            # The request is already HTTPS, so we skip redirecting it.
            return None

        unresolved_domain = request.unresolved_domain

        # HTTPS redirect for custom domains.
        if unresolved_domain.is_from_custom_domain:
            domain = unresolved_domain.domain
            if domain.https:
                return redirect_to_https(request, project=unresolved_domain.project)
            return None

        # HTTPS redirect for public domains.
        if (
            unresolved_domain.is_from_public_domain or unresolved_domain.is_from_external_domain
        ) and settings.PUBLIC_DOMAIN_USES_HTTPS:
            return redirect_to_https(request, project=unresolved_domain.project)

        return None

    def add_resolver_headers(self, request, response):
        if request.unresolved_url is not None:
            # TODO: add more ``X-RTD-Resolver-*`` headers
            uri_filename = iri_to_uri(request.unresolved_url.filename)
            header_value = escape(uri_filename)
            response["X-RTD-Resolver-Filename"] = header_value

    def process_response(self, request, response):  # noqa
        self.add_proxito_headers(request, response)
        self.add_cache_headers(request, response)
        self.add_cdn_cache_headers(request, response)
        self.add_x_robots_tag_headers(request, response)
        self.add_hsts_headers(request, response)
        self.add_user_headers(request, response)
        self.add_hosting_integrations_headers(request, response)
        self.add_resolver_headers(request, response)
        self.add_cors_headers(request, response)
        return response
