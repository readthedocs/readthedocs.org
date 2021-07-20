"""Common mixin classes for views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from simple_history.utils import update_change_reason
from vanilla import ListView


class ListViewWithForm(ListView):

    """List view that also exposes a create form."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form(data=None, files=None)
        return context


class PrivateViewMixin(LoginRequiredMixin):

    pass


class UpdateChangeReasonForm:

    """Set the change_reason on the model changed through this form."""

    change_reason = 'Changed from: form'

    def save(self, commit=True):
        obj = super().save(commit=commit)
        update_change_reason(obj, self.change_reason)
        return obj


class UpdateChangeReasonAdmin:

    """Set the change_reason on the model changed through this admin view."""

    change_reason = 'Changed from: admin'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        update_change_reason(obj, self.change_reason)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        update_change_reason(obj, self.change_reason)


class UpdateChangeReasonPostView:

    """
    Set the change_reason on the model changed through the POST method of this view.

    Use this class for views that don't use a form, like ``DeleteView``.
    """

    change_reason = 'Changed from: form'

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().post(request, *args, **kwargs)
        update_change_reason(obj, self.change_reason)
        return response
