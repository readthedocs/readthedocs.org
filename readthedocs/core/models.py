"""Models for the core app."""

from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from simple_history import register

from readthedocs.core.history import ExtraHistoricalRecords


class UserProfile(TimeStampedModel):
    """Additional information about a User."""

    user = AutoOneToOneField(
        User,
        verbose_name=_("User"),
        related_name="profile",
        on_delete=models.CASCADE,
    )
    # Shown on the users profile
    homepage = models.CharField(_("Homepage"), max_length=100, blank=True)

    # User configuration options
    allow_ads = models.BooleanField(
        _("See paid advertising"),
        help_text=_("If unchecked, you will still see community ads."),
        default=True,
    )

    mailing_list = models.BooleanField(
        default=False,
        help_text=_("Subscribe to our mailing list, and get helpful onboarding suggestions."),
    )

    # Internal tracking
    whitelisted = models.BooleanField(_("Whitelisted"), default=False)
    banned = models.BooleanField(_("Banned"), default=False)

    # Model history
    history = ExtraHistoricalRecords()

    def get_absolute_url(self):
        return reverse(
            "profiles_profile_detail",
            kwargs={"username": self.user.username},
        )


register(User, records_class=ExtraHistoricalRecords, app=__package__)
