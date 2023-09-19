"""Models for the core app."""

from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext
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
        help_text=_(
            "Subscribe to our mailing list, and get helpful onboarding suggestions."
        ),
    )

    # Internal tracking
    whitelisted = models.BooleanField(_("Whitelisted"), default=False)
    banned = models.BooleanField(_("Banned"), default=False)

    # Opt-out on emails
    # NOTE: this is a temporary field that we can remove after September 25, 2023
    # See https://blog.readthedocs.com/migrate-configuration-v2/
    optout_email_config_file_deprecation = models.BooleanField(
        _("Opt-out from email about 'Config file deprecation'"),
        default=False,
        null=True,
    )
    # NOTE: this is a temporary field that we can remove after October 16, 2023
    # See https://blog.readthedocs.com/use-build-os-config/
    optout_email_build_image_deprecation = models.BooleanField(
        _("Opt-out from email about '\"build.image\" config key deprecation'"),
        default=False,
        null=True,
    )

    # Model history
    history = ExtraHistoricalRecords()

    def __str__(self):
        return gettext("%(username)s's profile") % {"username": self.user.username}

    def get_absolute_url(self):
        return reverse(
            "profiles_profile_detail",
            kwargs={"username": self.user.username},
        )


register(User, records_class=ExtraHistoricalRecords, app=__package__)
