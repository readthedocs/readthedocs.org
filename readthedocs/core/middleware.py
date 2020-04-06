import logging
import time

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest
from django.urls.base import set_urlconf
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date
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


class ReadTheDocsSessionMiddleware(SessionMiddleware):

    """
    An overridden session middleware with a few changes.

    - Doesn't create a session on logged out doc views.
    - Uses a fallback cookie for browsers that reject SameSite=None cookies
    - Modifies Django's behavior of treating SESSION_COOKIE_SAMESITE=None
      to mean SameSite unset and instead makes it mean SameSite=None

    This overrides and replaces Django's built-in SessionMiddleware completely.
    Much of this middleware is duplicated from Django 2.2's SessionMiddleware.

    In Django 3.1, Django will fully support SameSite=None cookies.
    However, we may still need this middleware to support browsers that reject
    SameSite=None cookies.
    https://www.chromium.org/updates/same-site/incompatible-clients
    """

    # Don't set a session cookie on these URLs unless the cookie is already set
    IGNORE_URLS = [
        '/api/v2/footer_html', '/sustainability/view', '/sustainability/click',
    ]

    # This is a fallback cookie for the regular session cookie
    # It is only used by clients that reject cookies with `SameSite=None`
    cookie_name_fallback = f"{settings.SESSION_COOKIE_NAME}-samesiteunset"

    def process_request(self, request):
        for url in self.IGNORE_URLS:
            if (
                request.path_info.startswith(url) and
                settings.SESSION_COOKIE_NAME not in request.COOKIES and
                self.cookie_name_fallback not in request.COOKIES
            ):
                # Hack request.session otherwise the Authentication middleware complains.
                request.session = SessionBase()  # create an empty session
                return

        if settings.SESSION_COOKIE_SAMESITE:
            super().process_request(request)
        else:
            if settings.SESSION_COOKIE_NAME in request.COOKIES:
                session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
            else:
                session_key = request.COOKIES.get(self.cookie_name_fallback)

            request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        for url in self.IGNORE_URLS:
            if (
                request.path_info.startswith(url) and
                settings.SESSION_COOKIE_NAME not in request.COOKIES and
                self.cookie_name_fallback not in request.COOKIES
            ):
                return response

        # Most of the code below is taken directly from Django's SessionMiddleware.
        # Some changes (marked with NOTE:) were added to support the fallback cookie.

        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            pass
        else:
            # First check if we need to delete this cookie.
            # The session should be deleted only if the session is entirely empty
            # NOTE: This was changed to support both cookies
            if (
                settings.SESSION_COOKIE_NAME in request.COOKIES or
                self.cookie_name_fallback in request.COOKIES
            ) and empty:
                for cookie_name in (settings.SESSION_COOKIE_NAME, self.cookie_name_fallback):
                    if cookie_name in request.COOKIES:
                        response.delete_cookie(
                            cookie_name,
                            path=settings.SESSION_COOKIE_PATH,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                        )
            else:
                if accessed:
                    patch_vary_headers(response, ('Cookie',))
                if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                    if request.session.get_expire_at_browser_close():
                        max_age = None
                        expires = None
                    else:
                        max_age = request.session.get_expiry_age()
                        expires_time = time.time() + max_age
                        expires = http_date(expires_time)
                    # Save the session data and refresh the client cookie.
                    # Skip session save for 500 responses, refs #3881.
                    if response.status_code != 500:
                        try:
                            request.session.save()
                        except UpdateError:
                            raise SuspiciousOperation(
                                "The request's session was deleted before the "
                                "request completed. The user may have logged "
                                "out in a concurrent request, for example."
                            )

                        response.set_cookie(
                            settings.SESSION_COOKIE_NAME,
                            request.session.session_key, max_age=max_age,
                            expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                            path=settings.SESSION_COOKIE_PATH,
                            secure=settings.SESSION_COOKIE_SECURE or None,
                            httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                            samesite=settings.SESSION_COOKIE_SAMESITE,
                        )

                        # NOTE: This was added to support the fallback cookie
                        if not settings.SESSION_COOKIE_SAMESITE:
                            # Forcibly set the session cookie to SameSite=None
                            # This isn't supported in Django<3.1
                            # https://github.com/django/django/pull/11894
                            response.cookies[settings.SESSION_COOKIE_NAME]["samesite"] = "None"

                            # Set the fallback cookie in case the above cookie is rejected
                            response.set_cookie(
                                self.cookie_name_fallback,
                                request.session.session_key, max_age=max_age,
                                expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                                path=settings.SESSION_COOKIE_PATH,
                                secure=settings.SESSION_COOKIE_SECURE or None,
                                httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                                samesite=settings.SESSION_COOKIE_SAMESITE,
                            )
        return response
