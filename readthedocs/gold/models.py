import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)

LEVEL_CHOICES = (
    (5, '$5'),
    (10, '$10'),
    (25, '$25'),
    (50, '1 Hour ($50)'),
    (100, '2 Hours ($100)'),
    (200, '4 Hours ($200)'),
    (400, '1 Day ($400)'),
    (800, '2 Days ($800)'),
    (2000, '5 Days ($2000)'),
)


class GoldUser(models.Model):
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    user = models.ForeignKey('auth.User', verbose_name=_('User'), unique=True, related_name='gold')
    level = models.CharField(_('Level'), max_length=20, choices=LEVEL_CHOICES, default='supporter')

    last_4_digits = models.CharField(max_length=4)
    stripe_id = models.CharField(max_length=255)
    subscribed = models.BooleanField(default=False)


class OnceUser(models.Model):
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)
    public = models.BooleanField(_('Public'), default=True)

    name = models.CharField(_('name'), max_length=200, blank=True)
    email = models.EmailField(_('Email'), max_length=200, blank=True)
    user = models.ForeignKey('auth.User', verbose_name=_('User'), related_name='goldonce', blank=True, null=True)
    dollars = models.IntegerField(_('Level'), max_length=30, choices=LEVEL_CHOICES, default=50)

    last_4_digits = models.CharField(max_length=4)
    stripe_id = models.CharField(max_length=255)
    subscribed = models.BooleanField(default=False)
