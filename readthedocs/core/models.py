"""Models for the core app."""

from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import (
    CreationDateTimeField,
    ModificationDateTimeField,
)
from django_extensions.db.models import TimeStampedModel
from simple_history import register

from readthedocs.core.history import ExtraHistoricalRecords


class UserProfile(TimeStampedModel):

    """Additional information about a User."""

    # TODO: Overridden from TimeStampedModel just to allow null values,
    # remove after deploy.
    created = CreationDateTimeField(
        _('created'),
        null=True,
        blank=True,
    )
    modified = ModificationDateTimeField(
        _('modified'),
        null=True,
        blank=True,
    )

    user = AutoOneToOneField(
        User,
        verbose_name=_('User'),
        related_name='profile',
        on_delete=models.CASCADE,
    )
    whitelisted = models.BooleanField(_('Whitelisted'), default=False)
    banned = models.BooleanField(_('Banned'), default=False)
    homepage = models.CharField(_('Homepage'), max_length=100, blank=True)
    allow_ads = models.BooleanField(
        _('See paid advertising'),
        help_text=_('If unchecked, you will still see community ads.'),
        default=True,
    )
    history = ExtraHistoricalRecords()

    def __str__(self):
        return (
            ugettext("%(username)s's profile") %
            {'username': self.user.username}
        )

    def get_absolute_url(self):
        return reverse(
            'profiles_profile_detail',
            kwargs={'username': self.user.username},
        )


register(User, records_class=ExtraHistoricalRecords, app=__package__)
