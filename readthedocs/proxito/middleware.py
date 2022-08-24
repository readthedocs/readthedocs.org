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
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from readthedocs.core.unresolver import unresolver
from readthedocs.core.utils import get_cache_tag
from readthedocs.projects.models import Domain, Project, ProjectRelationship
from readthedocs.proxito import constants

log = structlog.get_logger(__name__)  # noqa


def map_host_to_project_slug(request):  # pylint: disable=too-many-return-statements
    """
    Take the request and map the host to the proper project slug.

    We check, in order:

    * The ``HTTP_X_RTD_SLUG`` host header for explicit Project mapping
        - This sets ``request.rtdheader`` True
    * The ``PUBLIC_DOMAIN`` where we can use the subdomain as the project name
        - This sets ``request.subdomain`` True
    * The hostname without port information, which maps to ``Domain`` objects
        - This sets ``request.cname`` True
    * The domain is the canonical one and using HTTPS if supported
        - This sets ``request.canonicalize`` with the value as the reason
    """

    host = unresolver.get_domain_from_host(request.get_host())
    public_domain = unresolver.get_domain_from_host(settings.PUBLIC_DOMAIN)
    external_domain = unresolver.get_domain_from_host(
        settings.RTD_EXTERNAL_VERSION_DOMAIN
    )

    # Explicit Project slug being passed in.
    if 'HTTP_X_RTD_SLUG' in request.META:
        project_slug = request.META['HTTP_X_RTD_SLUG'].lower()
        if Project.objects.filter(slug=project_slug).exists():
            request.rtdheader = True
            log.info('Setting project based on X_RTD_SLUG header.', project_slug=project_slug)
            return project_slug

    project_slug, domain_object, external = unresolver.unresolve_domain(host)
    if not project_slug:
        # Block domains that look like ours, may be phishing.
        if external_domain in host or public_domain in host:
            log.warning("Weird variation on our hostname.", host=host)
            return render(
                request,
                "core/dns-404.html",
                context={"host": host},
                status=400,
            )
        # Some person is CNAMEing to us without configuring a domain - 404.
        log.debug("CNAME 404.", host=host)
        return render(request, "core/dns-404.html", context={"host": host}, status=404)

    # Custom domain.
    if domain_object:
        request.cname = True
        request.domain = domain_object
        log.debug('Proxito CNAME.', host=host)

        if domain_object.https and not request.is_secure():
            # Redirect HTTP -> HTTPS (302) for this custom domain.
            log.debug('Proxito CNAME HTTPS Redirect.', host=host)
            request.canonicalize = constants.REDIRECT_HTTPS

        # NOTE: consider redirecting non-canonical custom domains to the canonical one
        # Whether that is another custom domain or the public domain

        return project_slug

    # Pull request previews.
    if external:
        subdomain, _ = host.split(".", maxsplit=1)
        _, version_slug = subdomain.rsplit("--", maxsplit=1)
        request.external_domain = True
        request.host_version_slug = version_slug
        log.debug("Proxito External Version Domain.", host=host)
        return project_slug

    # Normal doc serving.
    request.subdomain = True
    log.debug("Proxito Public Domain.", host=host)
    if (
        Domain.objects.filter(project__slug=project_slug)
        .filter(
            canonical=True,
            https=True,
        )
        .exists()
    ):
        log.debug("Proxito Public Domain -> Canonical Domain Redirect.", host=host)
        request.canonicalize = constants.REDIRECT_CANONICAL_CNAME
    elif ProjectRelationship.objects.filter(child__slug=project_slug).exists():
        log.debug(
            "Proxito Public Domain -> Subproject Main Domain Redirect.", host=host
        )
        request.canonicalize = constants.REDIRECT_SUBPROJECT_MAIN_DOMAIN
    return project_slug


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
            # Use a private method to get this
            # TODO: In Django 3.2 this has been upgraded to a top-level method
            # pylint: disable=protected-access
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

        We use ``CDN-Cache-Control``, to control caching at the CDN level only.
        This doesn't affect caching at the browser level (``Cache-Control``).

        See https://developers.cloudflare.com/cache/about/cdn-cache-control.
        """
        if settings.ALLOW_PRIVATE_REPOS:
            # Set the key to private only if it hasn't already been set by the view.
            response.headers.setdefault('CDN-Cache-Control', 'private')

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

        ret = map_host_to_project_slug(request)

        # Handle returning a response
        if hasattr(ret, 'status_code'):
            return ret

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

        log.debug(
            'Proxito Project.',
            project_slug=ret,
        )

        # Otherwise set the slug on the request
        request.host_project_slug = request.slug = ret

        try:
            project = Project.objects.get(slug=request.host_project_slug)
        except Project.DoesNotExist:
            log.debug("No host_project_slug set on project")
            return None

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
