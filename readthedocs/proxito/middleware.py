"""
Middleware for Proxito.

This is used to take the request and map the host to the proper project slug.

Additional processing is done to get the project from the URL in the ``views.py`` as well.
"""
import re
import sys
from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from readthedocs.core.unresolver import (
    DomainSourceType,
    InvalidCustomDomainError,
    InvalidExternalDomainError,
    InvalidSubdomainError,
    InvalidXRTDSlugHeader,
    SuspiciousHostnameError,
    unresolver,
)
from readthedocs.core.utils import get_cache_tag
from readthedocs.projects.models import Domain, ProjectRelationship
from readthedocs.proxito import constants

log = structlog.get_logger(__name__)


class ProxitoMiddleware(MiddlewareMixin):

    """The actual middleware we'll be using in prod."""

    # None of these need the proxito request middleware (response is needed).
    # The analytics API isn't listed because it depends on the unresolver,
    # which depends on the proxito middleware.
    skip_views = (
        'health_check',
        'footer_html',
        'search_api',
        'embed_api',
    )

    # pylint: disable=no-self-use
    def add_proxito_headers(self, request, response):
        """Add debugging and cache headers to proxito responses."""

        project_slug = getattr(request, 'path_project_slug', '')
        version_slug = getattr(request, 'path_version_slug', '')
        path = getattr(response, 'proxito_path', '')

        response['X-RTD-Domain'] = request.get_host()
        response['X-RTD-Project'] = project_slug

        if version_slug:
            response['X-RTD-Version'] = version_slug

        if path:
            response['X-RTD-Path'] = path

        # Include the project & project-version so we can do larger purges if needed
        cache_tag = response.get('Cache-Tag')
        cache_tags = [cache_tag] if cache_tag else []
        if project_slug:
            cache_tags.append(project_slug)
        if version_slug:
            cache_tags.append(get_cache_tag(project_slug, version_slug))

        if cache_tags:
            response['Cache-Tag'] = ','.join(cache_tags)

        if hasattr(request, 'rtdheader'):
            response['X-RTD-Project-Method'] = 'rtdheader'
        elif hasattr(request, 'subdomain'):
            response['X-RTD-Project-Method'] = 'subdomain'
        elif hasattr(request, 'cname'):
            response['X-RTD-Project-Method'] = 'cname'

        if hasattr(request, 'external_domain'):
            response['X-RTD-Version-Method'] = 'domain'
        else:
            response['X-RTD-Version-Method'] = 'path'

    def add_user_headers(self, request, response):
        """
        Set specific HTTP headers requested by the user.

        The headers added come from ``projects.models.HTTPHeader`` associated
        with the ``Domain`` object.
        """
        if hasattr(request, 'domain'):
            response_headers = [header.lower() for header in response.headers.keys()]
            for http_header in request.domain.http_headers.all():
                if http_header.name.lower() in response_headers:
                    log.error(
                        'Overriding an existing response HTTP header.',
                        http_header=http_header.name,
                        domain=request.domain.domain,
                    )
                log.info(
                    'Adding custom response HTTP header.',
                    http_header=http_header.name,
                    domain=request.domain.domain,
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

        host = request.get_host().lower().split(':')[0]
        public_domain = settings.PUBLIC_DOMAIN.lower().split(':')[0]
        hsts_header_values = []
        if settings.PUBLIC_DOMAIN_USES_HTTPS and public_domain in host:
            hsts_header_values = [
                'max-age=31536000',
                'includeSubDomains',
                'preload',
            ]
        elif hasattr(request, 'domain'):
            domain = request.domain
            # TODO: migrate Domains with HSTS set using these fields to
            # ``HTTPHeader`` and remove this chunk of code from here.
            if domain.hsts_max_age:
                hsts_header_values.append(f'max-age={domain.hsts_max_age}')
                # These other options don't make sense without max_age > 0
                if domain.hsts_include_subdomains:
                    hsts_header_values.append('includeSubDomains')
                if domain.hsts_preload:
                    hsts_header_values.append('preload')

        if hsts_header_values:
            # See https://tools.ietf.org/html/rfc6797
            response['Strict-Transport-Security'] = '; '.join(hsts_header_values)

    def add_cache_headers(self, request, response):
        """
        Add Cache-Control headers.

        If privacy levels are enabled and the header isn't already present,
        set the cache level to private.
        Or if the request was from the `X-RTD-Slug` header,
        we don't cache the response, since we could be caching a response in another domain.

        We use ``CDN-Cache-Control``, to control caching at the CDN level only.
        This doesn't affect caching at the browser level (``Cache-Control``).

        See https://developers.cloudflare.com/cache/about/cdn-cache-control.
        """
        header = "CDN-Cache-Control"
        # Never trust projects resolving from the X-RTD-Slug header,
        # we don't want to cache their content on domains from other
        # projects, see GHSA-mp38-vprc-7hf5.
        if hasattr(request, "rtdheader"):
            response.headers[header] = "private"

        if settings.ALLOW_PRIVATE_REPOS:
            # Set the key to private only if it hasn't already been set by the view.
            response.headers.setdefault(header, "private")

    def _set_request_attributes(self, request, unresolved_domain):
        """
        Set attributes in the request from the unresolved domain.

        - If the project was extracted from the ``X-RTD-Slug`` header,
          we set ``request.rtdheader`` to `True`.
        - If the project was extracted from the public domain,
          we set ``request.subdomain`` to `True`.
        - If the project was extracted from a custom domain,
          we set ``request.cname`` to `True`.
        - If the domain needs to redirect, set the canonicalize attribute accordingly.
        """
        # TODO: Set the unresolved domain in the request instead of each of these attributes.
        source = unresolved_domain.source
        project = unresolved_domain.project
        if source == DomainSourceType.http_header:
            request.rtdheader = True
        elif source == DomainSourceType.custom_domain:
            domain = unresolved_domain.domain
            request.cname = True
            request.domain = domain
            if domain.https and not request.is_secure():
                # Redirect HTTP -> HTTPS (302) for this custom domain.
                log.debug("Proxito CNAME HTTPS Redirect.", domain=domain.domain)
                request.canonicalize = constants.REDIRECT_HTTPS
        elif source == DomainSourceType.external_domain:
            request.external_domain = True
            request.host_version_slug = unresolved_domain.external_version_slug
        elif source == DomainSourceType.public_domain:
            request.subdomain = True
            canonical_domain = (
                Domain.objects.filter(project=project)
                .filter(canonical=True, https=True)
                .exists()
            )
            if canonical_domain:
                log.debug(
                    "Proxito Public Domain -> Canonical Domain Redirect.",
                    project_slug=project.slug,
                )
                request.canonicalize = constants.REDIRECT_CANONICAL_CNAME
            elif ProjectRelationship.objects.filter(child=project).exists():
                log.debug(
                    "Proxito Public Domain -> Subproject Main Domain Redirect.",
                    project_slug=project.slug,
                )
                request.canonicalize = constants.REDIRECT_SUBPROJECT_MAIN_DOMAIN
        else:
            raise NotImplementedError

    def process_request(self, request):  # noqa
        skip = any(
            request.path.startswith(reverse(view))
            for view in self.skip_views
        )
        if (
            skip
            or not settings.USE_SUBDOMAIN
            or 'localhost' in request.get_host()
            or 'testserver' in request.get_host()
        ):
            log.debug('Not processing Proxito middleware')
            return None

        try:
            unresolved_domain = unresolver.unresolve_domain_from_request(request)
        except SuspiciousHostnameError as exc:
            log.warning("Weird variation on our hostname.", domain=exc.domain)
            return render(
                request,
                "core/dns-404.html",
                context={"host": exc.domain},
                status=400,
            )
        except (InvalidSubdomainError, InvalidExternalDomainError):
            log.debug("Invalid project set on the subdomain.")
            raise Http404
        except InvalidCustomDomainError as exc:
            # Some person is CNAMEing to us without configuring a domain - 404.
            log.debug("CNAME 404.", domain=exc.domain)
            return render(
                request, "core/dns-404.html", context={"host": exc.domain}, status=404
            )
        except InvalidXRTDSlugHeader:
            raise SuspiciousOperation("Invalid X-RTD-Slug header.")

        self._set_request_attributes(request, unresolved_domain)

        # Remove multiple slashes from URL's
        if '//' in request.path:
            url_parsed = urlparse(request.get_full_path())
            clean_path = re.sub('//+', '/', url_parsed.path)
            new_parsed = url_parsed._replace(path=clean_path)
            final_url = new_parsed.geturl()
            # This protects against a couple issues:
            # * First is a URL like `//` which urlparse will return as a path of ''
            # * Second is URLs like `//google.com` which urlparse will return as `//google.com`
            #   We make sure there is _always_ a single slash in front to ensure relative redirects,
            #   instead of `//` redirects which are actually alternative domains.
            final_url = '/' + final_url.lstrip('/')
            log.debug(
                'Proxito Slash Redirect.',
                from_url=request.get_full_path(),
                to_url=final_url,
            )
            return redirect(final_url)

        project = unresolved_domain.project
        log.debug(
            'Proxito Project.',
            project_slug=project.slug,
        )

        # Otherwise set the slug on the request
        request.host_project_slug = request.slug = project.slug

        # This is hacky because Django wants a module for the URLConf,
        # instead of also accepting string
        if project.urlconf:

            # Stop Django from caching URLs
            # https://github.com/django/django/blob/7cf7d74/django/urls/resolvers.py#L65-L69  # noqa
            project_timestamp = project.modified_date.strftime("%Y%m%d.%H%M%S%f")
            url_key = f'readthedocs.urls.fake.{project.slug}.{project_timestamp}'

            log.info(
                'Setting URLConf',
                project_slug=project.slug,
                url_key=url_key,
                urlconf=project.urlconf,
            )
            if url_key not in sys.modules:
                sys.modules[url_key] = project.proxito_urlconf
            request.urlconf = url_key

        return None

    def process_response(self, request, response):  # noqa
        self.add_proxito_headers(request, response)
        self.add_cache_headers(request, response)
        self.add_hsts_headers(request, response)
        self.add_user_headers(request, response)
        return response
