# -*- coding: utf-8 -*-
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication class exempt of CSRF.

    DRF by default when using a ``SessionAuthentication`` it enforces CSRF.

    See: https://github.com/encode/django-rest-framework/blob/3.9.0/rest_framework/authentication.py#L134-L144
    """

    def enforce_csrf(self, request):
        return
