"""Common mixin classes for views."""
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import ListView

from readthedocs.projects.models import Feature
from readthedocs.subscriptions.models import PlanFeature


class ListViewWithForm(ListView):

    """List view that also exposes a create form."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form(data=None, files=None)
        return context


class PrivateViewMixin(LoginRequiredMixin):

    pass


class ProxiedAPIMixin:

    # DRF has BasicAuthentication and SessionAuthentication as default classes.
    # We don't support neither in the community site.
    authentication_classes = []


class CDNCacheControlMixin:

    """
    Allow to cache views at the CDN level when privacy levels are enabled.

    The cache control header is only used when privacy levels
    are enabled (otherwise everything is public by default).

    Views that can be cached should always return the same response for all
    users (anonymous and authenticated users), like when the version attached
    to the request is public.

    To cache a view you can either set the `cache_request` attribute to `True`,
    or override the `can_be_cached` method.

    We use ``CDN-Cache-Control``, to control caching at the CDN level only.
    This doesn't affect caching at the browser level (``Cache-Control``).

    See https://developers.cloudflare.com/cache/about/cdn-cache-control.
    """

    cache_request = False

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if settings.ALLOW_PRIVATE_REPOS and self.can_be_cached(request):
            response.headers['CDN-Cache-Control'] = 'public'
        return response

    def can_be_cached(self, request):
        return self.cache_request

    @lru_cache(maxsize=1)
    def _is_cache_enabled(self, project):
        """Helper function to check if CDN is enabled for a project."""
        plan_has_cdn = PlanFeature.objects.get_feature(
            obj=project, type=PlanFeature.TYPE_CDN
        )
        return settings.ALLOW_PRIVATE_REPOS and (
            plan_has_cdn or project.has_feature(Feature.CDN_ENABLED)
        )
