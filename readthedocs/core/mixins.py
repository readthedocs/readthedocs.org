# -*- coding: utf-8 -*-

"""Common mixin classes for views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import ugettext_lazy as _
from vanilla import ListView

from readthedocs.projects.constants import PRIVACY_CHOICES, PROTECTED


class ListViewWithForm(ListView):

    """List view that also exposes a create form."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form(data=None, files=None)
        return context


class PrivateViewMixin(LoginRequiredMixin):

    pass


class HideProtectedLevelMixin:

    """
    Hide ``protected`` privacy level from Form.

    Remove Protected for now since it causes confusions to users.

    If the current ``privacy_level`` is ``protected`` we show it (so users keep
    seeing consistency values), and hide it otherwise (so it can't be selected).

    There is a better way to manage this by using Version states.
    See: https://github.com/rtfd/readthedocs.org/issues/5321
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance is None or self.instance.privacy_level != PROTECTED:
            privacy_level = list(PRIVACY_CHOICES)
            privacy_level.remove((PROTECTED, _('Protected')))
            self.fields['privacy_level'].choices = privacy_level
