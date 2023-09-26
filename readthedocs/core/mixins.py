"""Common mixin classes for views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import ListView

from readthedocs.proxito.cache import cache_response, private_response


class ListViewWithForm(ListView):

    """List view that also exposes a create form."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form(data=None, files=None)
        return context


class PrivateViewMixin(LoginRequiredMixin):
    pass


class ProxiedAPIMixin:
    # DRF has BasicAuthentication and SessionAuthentication as default classes.
    # We don't support neither in the community site.
    authentication_classes = []


class CDNCacheControlMixin:

    """
    Explicitly cache or not a view at the CDN level.

    The cache control header is used to mark the response as public/private,
    so it can be cached or not.

    Views that can be cached should always return the same response for all
    users (anonymous and authenticated users), like when the version attached
    to the request is public.

    To explicitly cache a view you can either set the `cache_response`
    attribute to `True`/`False`, or override the `can_be_cached` method
    (which defaults to return the `cache_response` attribute).
    If set to `None` (default), the cache header won't be set, so the default
    value can be set by our middleware (public for .org and private for .com).

    We use ``CDN-Cache-Control``, to control caching at the CDN level only.
    This doesn't affect caching at the browser level (``Cache-Control``).

    See https://developers.cloudflare.com/cache/about/cdn-cache-control.
    """

    cache_response = None

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        can_be_cached = self.can_be_cached(request)
        if can_be_cached is not None:
            if can_be_cached:
                cache_response(response)
            else:
                private_response(response)
        return response

    def can_be_cached(self, request):
        return self.cache_response
