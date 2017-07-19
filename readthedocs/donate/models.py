"""Django models for the donate app."""
# We use 'type' and 'hash' heavily in the API here.
# pylint: disable=redefined-builtin
from __future__ import (absolute_import, division)

from past.utils import old_div
from builtins import object
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, pgettext
from django.core.urlresolvers import reverse
from django.conf import settings
from django_countries.fields import CountryField
import six

from readthedocs.donate.utils import get_ad_day
from readthedocs.donate.constants import (
    DISPLAY_CHOICES, FILTER_CHOICES, IMPRESSION_TYPES, THEMES, READTHEDOCS_THEME
)
from readthedocs.projects.models import Project
from readthedocs.projects.constants import PROGRAMMING_LANGUAGES


@python_2_unicode_compatible
class Supporter(models.Model):
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)
    public = models.BooleanField(_('Public'), default=True)

    name = models.CharField(_('name'), max_length=200, blank=True)
    email = models.EmailField(_('Email'), max_length=200, blank=True)
    user = models.ForeignKey('auth.User', verbose_name=_('User'),
                             related_name='goldonce', blank=True, null=True)
    dollars = models.IntegerField(_('Amount'), default=50)
    logo_url = models.URLField(_('Logo URL'), max_length=255, blank=True,
                               null=True)
    site_url = models.URLField(_('Site URL'), max_length=255, blank=True,
                               null=True)

    last_4_digits = models.CharField(max_length=4)
    stripe_id = models.CharField(max_length=255)
    subscribed = models.BooleanField(default=False)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class SupporterPromo(models.Model):

    """A banner advertisement."""

    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    name = models.CharField(_('Name'), max_length=200)
    analytics_id = models.CharField(_('Analytics ID'), max_length=200)
    text = models.TextField(_('Text'), blank=True)
    link = models.URLField(_('Link URL'), max_length=255, blank=True, null=True)
    image = models.URLField(_('Image URL'), max_length=255, blank=True, null=True)
    display_type = models.CharField(_('Display Type'), max_length=200,
                                    choices=DISPLAY_CHOICES, default='doc')
    sold_impressions = models.IntegerField(_('Sold Impressions'), default=1000000)
    sold_days = models.IntegerField(_('Sold Days'), default=30)
    sold_clicks = models.IntegerField(_('Sold Clicks'), default=0)
    programming_language = models.CharField(_('Programming Language'), max_length=20,
                                            choices=PROGRAMMING_LANGUAGES, default=None,
                                            blank=True, null=True)
    theme = models.CharField(_('Theme'), max_length=40,
                             choices=THEMES, default=READTHEDOCS_THEME,
                             blank=True, null=True)
    community = models.BooleanField(_('Community Ad'), default=False)
    live = models.BooleanField(_('Live'), default=False)

    class Meta(object):
        ordering = ('analytics_id', '-live')

    def __str__(self):
        return self.name

    def as_dict(self):
        """A dict respresentation of this for JSON encoding"""
        hash = get_random_string()
        domain = getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org')
        if self.image:
            image_url = '//{host}{url}'.format(
                host=domain,
                url=reverse(
                    'donate_view_proxy',
                    kwargs={'promo_id': self.pk, 'hash': hash}
                ))
        else:
            image_url = None
        # TODO: Store this hash and confirm that a proper hash was sent later
        link_url = '//{host}{url}'.format(
            host=domain,
            url=reverse(
                'donate_click_proxy',
                kwargs={'promo_id': self.pk, 'hash': hash}
            ))
        return {
            'id': self.analytics_id,
            'text': self.text,
            'link': link_url,
            'image': image_url,
            'hash': hash,
        }

    def cache_key(self, type, hash):
        assert type in IMPRESSION_TYPES + ('project',)
        return 'promo:{id}:{hash}:{type}'.format(id=self.analytics_id, hash=hash, type=type)

    def incr(self, type, project=None):
        """Add to the number of times this action has been performed, stored in the DB"""
        assert type in IMPRESSION_TYPES
        day = get_ad_day()
        if project:
            impression, _ = self.project_impressions.get_or_create(date=day, project=project)
        else:
            impression, _ = self.impressions.get_or_create(date=day)

        setattr(impression, type, models.F(type) + 1)
        impression.save()

        # TODO: Support redis, more info on this PR
        #
        # https://github.com/rtfd/readthedocs.org
        #     /pull/2105/files/1b5f8568ae0a7760f7247149bcff481efc000f32#r58253051

    def view_ratio(self, day=None):
        if not day:
            day = get_ad_day()
        impression = self.impressions.get_or_create(date=day)[0]
        return impression.view_ratio

    def click_ratio(self, day=None):
        if not day:
            day = get_ad_day()
        impression = self.impressions.get_or_create(date=day)[0]
        return impression.click_ratio

    def views_per_day(self):
        return int(old_div(float(self.sold_impressions), float(self.sold_days)))

    def views_shown_today(self, day=None):
        if not day:
            day = get_ad_day()
        impression = self.impressions.get_or_create(date=day)[0]
        return float(impression.views)

    def views_needed_today(self):
        ret = self.views_per_day() - self.views_shown_today()
        if ret < 0:
            return 0
        return ret

    def total_views(self):
        return sum(imp.views for imp in self.impressions.all())

    def total_clicks(self):
        return sum(imp.clicks for imp in self.impressions.all())

    def total_click_ratio(self):
        if self.total_views() == 0:
            return float(0)
        return '%.4f' % float(
            (old_div(float(self.total_clicks()), float(self.total_views()))) * 100
        )

    def report_html_text(self):
        """
        Include the link in the html text.

        Only used for reporting,
        doesn't include any click fraud protection!
        """
        return self.text.replace('<a>', "<a href='%s'>" % self.link)


class BaseImpression(models.Model):

    """Statistics for tracking."""

    date = models.DateField(_('Date'))
    offers = models.IntegerField(_('Offer'), default=0)
    views = models.IntegerField(
        pgettext('View', 'Number of display on a screen that were sold'), default=0)
    clicks = models.IntegerField(_('Clicks'), default=0)

    class Meta(object):
        ordering = ('-date',)
        unique_together = ('promo', 'date')
        abstract = True

    @property
    def view_ratio(self):
        if self.offers == 0:
            return 0  # Don't divide by 0
        return float(
            float(self.views) / float(self.offers) * 100
        )

    @property
    def click_ratio(self):
        if self.views == 0:
            return 0  # Don't divide by 0
        return '%.3f' % float(
            float(self.clicks) / float(self.views) * 100
        )


@python_2_unicode_compatible
class PromoImpressions(BaseImpression):

    """
    Track stats around how successful this promo has been.

    Indexed one per promo per day.
    """

    promo = models.ForeignKey(SupporterPromo, related_name='impressions',
                              blank=True, null=True)

    def __str__(self):
        return u'%s on %s' % (self.promo, self.date)


@python_2_unicode_compatible
class ProjectImpressions(BaseImpression):

    """
    Track stats for a specific project and promo.

    Indexed one per project per promo per day
    """

    promo = models.ForeignKey(SupporterPromo, related_name='project_impressions',
                              blank=True, null=True)
    project = models.ForeignKey(Project, related_name='impressions',
                                blank=True, null=True)

    class Meta(object):
        unique_together = ('project', 'promo', 'date')

    def __str__(self):
        return u'%s / %s on %s' % (self.promo, self.project, self.date)


@python_2_unicode_compatible
class Country(models.Model):
    country = CountryField(unique=True)

    def __str__(self):
        return six.text_type(self.country.name)


@python_2_unicode_compatible
class GeoFilter(models.Model):
    promo = models.ForeignKey(SupporterPromo, related_name='geo_filters',
                              blank=True, null=True)
    filter_type = models.CharField(_('Filter Type'), max_length=20,
                                   choices=FILTER_CHOICES, default='')
    countries = models.ManyToManyField(Country, related_name='filters')

    @property
    def codes(self):
        ret = []
        for wrapped_code in self.countries.values_list('country'):
            ret.append(wrapped_code[0])
        return ret

    def __str__(self):
        return u"Filter for {promo} that {type}s: {countries}".format(
            promo=self.promo.name, type=self.filter_type, countries=self.codes)
