import logging
import time

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
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


class ReferrerPolicyMiddleware:

    """
    A middleware implementing the Referrer-Policy header.

    The value of the header will be read from the SECURE_REFERRER_POLICY setting.

    Important:
        In Django 3.x, this feature is built-in to the SecurityMiddleware.
        After upgrading to Django3, this middleware should be removed.
        https://docs.djangoproject.com/en/3.1/ref/middleware/#referrer-policy

    Based heavily on: https://github.com/ubernostrum/django-referrer-policy
    """

    VALID_REFERRER_POLICIES = [
        'no-referrer',
        'no-referrer-when-downgrade',
        'origin',
        'origin-when-cross-origin',
        'same-origin',
        'strict-origin',
        'strict-origin-when-cross-origin',
        'unsafe-url',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

        if not settings.SECURE_REFERRER_POLICY:
            log.warning("SECURE_REFERRER_POLICY not set - not setting the referrer policy")
            raise MiddlewareNotUsed()
        if settings.SECURE_REFERRER_POLICY not in self.VALID_REFERRER_POLICIES:
            raise ImproperlyConfigured(
                "settings.SECURE_REFERRER_POLICY has an illegal value."
            )

    def __call__(self, request):
        response = self.get_response(request)
        response['Referrer-Policy'] = settings.SECURE_REFERRER_POLICY
        return response
