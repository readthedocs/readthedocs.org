from functools import partial

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason


class ExtraFieldsHistoricalModel(models.Model):

    """
    Abstract model to allow history models track extra data.

    Extra data includes:

    - Users after they have been deleted.
    """

    extra_history_user_id = models.IntegerField(
        _('ID'),
        blank=True,
        null=True,
        db_index=True,
    )
    extra_history_user_username = models.CharField(
        _('username'),
        max_length=150,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


ExtraHistoricalRecords = partial(HistoricalRecords, bases=[ExtraFieldsHistoricalModel])
"""Helper partial to use instead of HistoricalRecords."""


class ExtraSimpleHistoryAdmin(SimpleHistoryAdmin):

    """Set the change_reason on the model changed through this admin view."""

    change_reason = None

    def get_change_reason(self):
        if self.change_reason:
            return self.change_reason
        klass = self.__class__.__name__
        return f'origin=admin class={klass}'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        update_change_reason(obj, self.get_change_reason())

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        update_change_reason(obj, self.change_reason)


class SimpleHistoryModelForm(forms.ModelForm):

    """Set the change_reason on the model changed through this form."""

    change_reason = None

    def get_change_reason(self):
        if self.change_reason:
            return self.change_reason
        klass = self.__class__.__name__
        return f'origin=form class={klass}'

    def save(self, commit=True):
        obj = super().save(commit=commit)
        update_change_reason(obj, self.get_change_reason())
        return obj


class UpdateChangeReasonPostView:

    """
    Set the change_reason on the model changed through the POST method of this view.

    Use this class for views that don't use a form, like ``DeleteView``.
    """

    change_reason = None

    def get_change_reason(self):
        if self.change_reason:
            return self.change_reason
        klass = self.__class__.__name__
        return f'origin=form class={klass}'

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().post(request, *args, **kwargs)
        update_change_reason(obj, self.get_change_reason())
        return response
