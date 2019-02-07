# -*- coding: utf-8 -*-

"""Models for the core app."""
import logging

from annoying.fields import AutoOneToOneField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _


STANDARD_EMAIL = 'anonymous@readthedocs.org'

log = logging.getLogger(__name__)


class UserProfile(models.Model):

    """Additional information about a User."""

    user = AutoOneToOneField(
        'auth.User',
        verbose_name=_('User'),
        related_name='profile',
    )
    whitelisted = models.BooleanField(_('Whitelisted'), default=False)
    banned = models.BooleanField(_('Banned'), default=False)
    homepage = models.CharField(_('Homepage'), max_length=100, blank=True)
    allow_ads = models.BooleanField(
        _('See paid advertising'),
        help_text=_('If unchecked, you will still see community ads.'),
        default=True,
    )
    allow_email = models.BooleanField(
        _('Allow email'),
        help_text=_('Show your email on VCS contributions.'),
        default=True,
    )

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

    def get_contribution_details(self):
        """
        Get the line to put into commits to attribute the author.

        Returns a tuple (name, email)
        """
        if self.user.first_name and self.user.last_name:
            name = '{} {}'.format(self.user.first_name, self.user.last_name)
        else:
            name = self.user.username
        if self.allow_email:
            email = self.user.email
        else:
            email = STANDARD_EMAIL
        return (name, email)
