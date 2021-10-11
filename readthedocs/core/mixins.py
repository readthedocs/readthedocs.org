"""Common mixin classes for views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import ListView


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
