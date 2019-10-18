import logging

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest
from django.urls.base import set_urlconf
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render

from readthedocs.projects.models import Domain, Project


log = logging.getLogger(__name__)

LOG_TEMPLATE = '(Middleware) %(msg)s [%(host)s%(path)s]'


class SubdomainMiddleware(MiddlewareMixin):

    """Middleware to display docs for non-dashboard domains."""

    def process_request(self, request):
        """
        Process requests for unhandled domains.

        If the request is not for our ``PUBLIC_DOMAIN``, or if ``PUBLIC_DOMAIN``
        is not set and the request is for a subdomain on ``PRODUCTION_DOMAIN``,
        process the request as a request a documentation project.
        """
        if not settings.USE_SUBDOMAIN:
            return None

        full_host = host = request.get_host().lower()
        path = request.get_full_path()
        log_kwargs = dict(host=host, path=path)
        public_domain = settings.PUBLIC_DOMAIN

        if public_domain is None:
            public_domain = settings.PRODUCTION_DOMAIN
        if ':' in host:
            host = host.split(':')[0]
        domain_parts = host.split('.')

        # Serve subdomains - but don't depend on the production domain only having 2 parts
        if len(domain_parts) == len(public_domain.split('.')) + 1:
            subdomain = domain_parts[0]
            is_www = subdomain.lower() == 'www'
            if not is_www and (  # Support ports during local dev
                    public_domain in host or public_domain in full_host
            ):
                if not Project.objects.filter(slug=subdomain).exists():
                    raise Http404(_('Project not found'))
                request.subdomain = True
                request.slug = subdomain
                request.urlconf = settings.SUBDOMAIN_URLCONF
                return None

        # Serve CNAMEs
        if (
            public_domain not in host and
            settings.PRODUCTION_DOMAIN not in (host, full_host) and
            'localhost' not in host and
            'testserver' not in host and
                host != 'web'
        ):
            request.cname = True
            domains = Domain.objects.filter(domain=host)
            if domains.count():
                for domain in domains:
                    if domain.domain == host:
                        request.slug = domain.project.slug
                        request.urlconf = settings.SUBDOMAIN_URLCONF
                        request.domain_object = True
                        log.debug(
                            LOG_TEMPLATE,
                            dict(
                                {'msg': 'Domain Object Detected: %s' % 'domain'},
                                **log_kwargs
                            )
                        )
                        break
            if (
                not hasattr(request, 'domain_object') and
                'HTTP_X_RTD_SLUG' in request.META
            ):
                request.slug = request.META['HTTP_X_RTD_SLUG'].lower()
                request.urlconf = settings.SUBDOMAIN_URLCONF
                request.rtdheader = True
                log.debug(
                    LOG_TEMPLATE,
                    dict(
                        {'msg': 'X-RTD-Slug header detected: %s' % request.slug},
                        **log_kwargs
                    )
                )
            # Try header first, then DNS
            elif not hasattr(request, 'domain_object'):
                # Some person is CNAMEing to us without configuring a domain - 404.
                log.warning(
                    LOG_TEMPLATE,
                    dict({'msg': 'CNAME 404'}, **log_kwargs)
                )
                return render(request, 'core/dns-404.html', context={'host': host}, status=404)
        # Google was finding crazy www.blah.readthedocs.org domains.
        # Block these explicitly after trying CNAME logic.
        if len(domain_parts) > 3 and not settings.DEBUG:
            # Stop www.fooo.readthedocs.org
            if domain_parts[0] == 'www':
                log.debug(
                    LOG_TEMPLATE,
                    dict({'msg': '404ing long domain'}, **log_kwargs)
                )
                return HttpResponseBadRequest(_('Invalid hostname'))
            log.debug(
                LOG_TEMPLATE,
                dict(
                    {'msg': 'Allowing long domain name'},
                    **log_kwargs
                )
            )
        # Normal request.
        return None

    def process_response(self, request, response):
        # Reset URLconf for this thread
        # to the original one.
        set_urlconf(None)
        return response


class SingleVersionMiddleware(MiddlewareMixin):

    """
    Reset urlconf for requests for 'single_version' docs.

    In settings.MIDDLEWARE, SingleVersionMiddleware must follow after
    SubdomainMiddleware.
    """

    def _get_slug(self, request):
        """
        Get slug from URLs requesting docs.

        If URL is like '/docs/<project_name>/', we split path
        and pull out slug.

        If URL is subdomain or CNAME, we simply read request.slug, which is
        set by SubdomainMiddleware.
        """
        slug = None
        if hasattr(request, 'slug'):
            # Handle subdomains and CNAMEs.
            slug = request.slug.lower()
        else:
            # Handle '/docs/<project>/' URLs
            path = request.get_full_path()
            path_parts = path.split('/')
            if len(path_parts) > 2 and path_parts[1] == 'docs':
                slug = path_parts[2].lower()
        return slug

    def process_request(self, request):
        slug = self._get_slug(request)
        if slug:
            try:
                proj = Project.objects.get(slug=slug)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # Let 404 be handled further up stack.
                return None

            if getattr(proj, 'single_version', False):
                request.urlconf = settings.SINGLE_VERSION_URLCONF
                # Logging
                host = request.get_host()
                path = request.get_full_path()
                log_kwargs = dict(host=host, path=path)
                log.debug(
                    LOG_TEMPLATE,
                    dict(
                        {'msg': 'Handling single_version request'},
                        **log_kwargs
                    )
                )

        return None


class FooterNoSessionMiddleware(SessionMiddleware):

    """
    Middleware that doesn't create a session on logged out doc views.

    This will reduce the size of our session table drastically.
    """

    IGNORE_URLS = [
        '/api/v2/footer_html', '/sustainability/view', '/sustainability/click',
    ]

    def process_request(self, request):
        for url in self.IGNORE_URLS:
            if (
                request.path_info.startswith(url) and
                settings.SESSION_COOKIE_NAME not in request.COOKIES
            ):
                # Hack request.session otherwise the Authentication middleware complains.
                request.session = SessionBase()  # create an empty session
                return
        super().process_request(request)

    def process_response(self, request, response):
        for url in self.IGNORE_URLS:
            if (
                request.path_info.startswith(url) and
                settings.SESSION_COOKIE_NAME not in request.COOKIES
            ):
                return response
        return super().process_response(request, response)
