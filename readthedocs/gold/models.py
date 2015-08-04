import math

from django.db import models
from django.utils.translation import ugettext_lazy as _

from readthedocs.projects.models import Project

LEVEL_CHOICES = (
    ('v1-org-5', '$5/mo'),
    ('v1-org-10', '$10/mo'),
    ('v1-org-15', '$15/mo'),
    ('v1-org-20', '$20/mo'),
    ('v1-org-50', '$50/mo'),
    ('v1-org-100', '$100/mo'),
)

DOLLARS_PER_PROJECT = 5


class GoldUser(models.Model):
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    user = models.ForeignKey('auth.User', verbose_name=_('User'), unique=True, related_name='gold')
    level = models.CharField(_('Level'), max_length=20,
                             choices=LEVEL_CHOICES, default=LEVEL_CHOICES[0][0])
    projects = models.ManyToManyField(Project, verbose_name=_('Projects'),
                                      related_name='gold_owners')

    last_4_digits = models.CharField(max_length=4)
    stripe_id = models.CharField(max_length=255)
    subscribed = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Gold Level %s for %s' % (self.level, self.user)

    @property
    def num_supported_projects(self):
        dollars = int(self.level.split('-')[-1])
        num_projects = int(math.floor(dollars / DOLLARS_PER_PROJECT))
        return num_projects
