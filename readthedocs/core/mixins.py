# -*- coding: utf-8 -*-

"""Common mixin classes for views."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from vanilla import ListView


class ListViewWithForm(ListView):

    """List view that also exposes a create form."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form(data=None, files=None)
        return context


class LoginRequiredMixin:

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
