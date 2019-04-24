# -*- coding: utf-8 -*-

"""Django models for recurring donations aka Gold Membership."""
import math
from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
import pytz

from readthedocs.projects.models import Project


#: The membership options that are currently available
LEVEL_CHOICES = (
    ('v1-org-5', '$5/mo'),
    ('v1-org-10', '$10/mo'),
    ('v1-org-15', '$15/mo'),
    ('v1-org-20', '$20/mo'),
    ('v1-org-50', '$50/mo'),
    ('v1-org-100', '$100/mo'),
)

#: An estimate of the cost of supporting one project for a month
DOLLARS_PER_PROJECT = 5


class GoldUser(models.Model):

    """A user subscription for gold membership."""

    # Gold members created after this date can no longer sponsor projects to be ad-free
    SPONSOR_PROJECT_CUTOFF = pytz.utc.localize(datetime(year=2019, month=5, day=1))

    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    user = models.ForeignKey(
        'auth.User',
        verbose_name=_('User'),
        unique=True,
        related_name='gold',
    )
    level = models.CharField(
        _('Level'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default=LEVEL_CHOICES[0][0],
    )
    projects = models.ManyToManyField(
        Project,
        verbose_name=_('Projects'),
        related_name='gold_owners',
    )

    last_4_card_digits = models.CharField(max_length=4)
    stripe_id = models.CharField(max_length=255)
    subscribed = models.BooleanField(default=False)
    business_vat_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return 'Gold Level {} for {}'.format(self.level, self.user)

    @property
    def num_supported_projects(self):
        dollars = int(self.level.split('-')[-1])
        num_projects = int(math.floor(dollars // DOLLARS_PER_PROJECT))
        return num_projects

    def can_sponsor_projects(self):
        if self.pub_date < self.SPONSOR_PROJECT_CUTOFF:
            return True

        return False
