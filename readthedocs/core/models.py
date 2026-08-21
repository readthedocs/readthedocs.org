"""Models for the core app."""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from simple_history import register

from readthedocs.core.history import ExtraHistoricalRecords


class UserProfile(TimeStampedModel):
    """Additional information about a User."""

    THEME_DEFAULT = "default"
    THEME_SYSTEM = "system"
    THEME_DARK = "dark"
    THEME_LIGHT = "light"
    THEMES = (
        (THEME_DEFAULT, _("Use default theme")),
        (THEME_LIGHT, _("Light theme")),
        (THEME_DARK, _("Dark theme")),
        (THEME_SYSTEM, _("Use system theme")),
    )

    user = models.OneToOneField(
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

    # First-touch attribution.
    # Captured in the session by FirstTouchAttributionMiddleware on the
    # visitor's first request carrying a UTM parameter or external referrer,
    # and stored here at signup. Empty for users who signed up before this
    # existed or arrived with no attribution signal (direct traffic).
    attribution_utm_source = models.CharField(
        _("Signup UTM source"), max_length=255, blank=True, default=""
    )
    attribution_utm_medium = models.CharField(
        _("Signup UTM medium"), max_length=255, blank=True, default=""
    )
    attribution_utm_campaign = models.CharField(
        _("Signup UTM campaign"), max_length=255, blank=True, default=""
    )
    attribution_utm_content = models.CharField(
        _("Signup UTM content"), max_length=255, blank=True, default=""
    )
    attribution_utm_term = models.CharField(
        _("Signup UTM term"), max_length=255, blank=True, default=""
    )
    attribution_referrer = models.CharField(
        _("Signup referrer"), max_length=512, blank=True, default=""
    )
    attribution_landing_page = models.CharField(
        _("Signup landing page"), max_length=512, blank=True, default=""
    )
    attribution_first_touch_date = models.DateTimeField(
        _("Signup first touch date"), null=True, blank=True
    )

    # Display settings
    theme = models.CharField(
        _("Dashboard theme"),
        choices=THEMES,
        default=THEME_DEFAULT,
    )

    # Model history
    history = ExtraHistoricalRecords()

    def get_absolute_url(self):
        return reverse(
            "profiles_profile_detail",
            kwargs={"username": self.user.username},
        )

    def use_dark_theme(self):
        return self.theme == self.THEME_DARK

    def use_light_theme(self):
        # For now, the `default` theme is the same as selecting `light` theme.
        # Once we have a user facing form, we can either change the `default` to
        # be the same as `system`, or just drop the option entirely if we're
        # confident in the dark theme.
        return self.theme in [self.THEME_DEFAULT, self.THEME_LIGHT]


register(User, records_class=ExtraHistoricalRecords, app=__package__)
