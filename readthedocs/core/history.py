from functools import partial

import structlog
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason


log = structlog.get_logger(__name__)


def set_change_reason(instance, reason, user=None):
    """
    Set the change reason for the historical record created from the instance.

    This method should be called before calling ``save()`` or ``delete``.
    It sets `reason` to the `_change_reason` attribute of the instance,
    that's used to create the historical record on the save/delete signals.

    `user` is useful to track who made the change, this is only needed
    if this method is called outside of a request context,
    as the middleware already sets the user from the request.

    See:
    - https://django-simple-history.readthedocs.io/en/latest/historical_model.html#change-reason
    - https://django-simple-history.readthedocs.io/en/latest/user_tracking.html
    """
    instance._change_reason = reason
    if user:
        instance._history_user = user


def safe_update_change_reason(instance, reason):
    """
    Wrapper around update_change_reason to catch exceptions.

    .. warning::

       The implementation of django-simple-history's `update_change_reason`
       is very brittle, as it queries for a previous historical record
       that matches the attributes of the instance to update the ``change_reason``,
       which could end up updating the wrong record, or not finding it.

       If you already have control over the object, use `set_change_reason`
       before updating/deleting the object instead.
       That's more safe, since the attribute is passed to the signal
       and used at the creation time of the record.

        https://django-simple-history.readthedocs.io/en/latest/historical_model.html#change-reason  # noqa
    """
    try:
        update_change_reason(instance=instance, reason=reason)
    except Exception:
        log.exception(
            "An error occurred while updating the change reason of the instance.",
            instance=instance,
        )


class ExtraFieldsHistoricalModel(models.Model):
    """
    Abstract model to allow history models track extra data.

    Extra data includes:

    - User information to retain after they have been deleted
    - IP & browser
    """

    extra_history_user_id = models.IntegerField(
        _("ID"),
        blank=True,
        null=True,
    )
    extra_history_user_username = models.CharField(
        _("username"),
        max_length=150,
        null=True,
    )
    extra_history_ip = models.CharField(
        _("IP address"),
        blank=True,
        null=True,
        max_length=250,
    )
    extra_history_browser = models.CharField(
        _("Browser user-agent"),
        max_length=250,
        blank=True,
        null=True,
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
        return f"origin=admin class={klass}"

    def save_model(self, request, obj, form, change):
        if obj:
            set_change_reason(obj, self.get_change_reason())
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if obj:
            set_change_reason(obj, self.get_change_reason())
        super().delete_model(request, obj)


class SimpleHistoryModelForm(forms.ModelForm):
    """Set the change_reason on the model changed through this form."""

    change_reason = None

    def get_change_reason(self):
        if self.change_reason:
            return self.change_reason
        klass = self.__class__.__name__
        return f"origin=form class={klass}"

    def save(self, commit=True):
        if self.instance:
            set_change_reason(self.instance, self.get_change_reason())
        return super().save(commit=commit)


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
        return f"origin=form class={klass}"

    def get_object(self):
        obj = super().get_object()
        set_change_reason(obj, self.get_change_reason())
        return obj
