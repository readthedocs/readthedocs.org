import logging

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.middleware import SessionMiddleware


log = logging.getLogger(__name__)

LOG_TEMPLATE = '(Middleware) %(msg)s [%(host)s%(path)s]'


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
