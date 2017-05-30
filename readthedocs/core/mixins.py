"""Common mixin classes for views"""

from __future__ import absolute_import
from builtins import object
from vanilla import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class ListViewWithForm(ListView):

    """List view that also exposes a create form"""

    def get_context_data(self, **kwargs):
        context = super(ListViewWithForm, self).get_context_data(**kwargs)
        context['form'] = self.get_form(data=None, files=None)
        return context


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)
