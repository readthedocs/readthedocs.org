import random

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from redis import Redis

from readthedocs.donate.utils import get_ad_day


DISPLAY_CHOICES = (
    ('doc', 'Documentation Pages'),
    ('site-footer', 'Site Footer'),
    ('search', 'Search Pages'),
)


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


class SupporterPromo(models.Model):
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    name = models.CharField(_('Name'), max_length=200)
    analytics_id = models.CharField(_('Analytics ID'), max_length=200)
    text = models.TextField(_('Text'), blank=True)
    link = models.URLField(_('Link URL'), max_length=255, blank=True, null=True)
    image = models.URLField(_('Image URL'), max_length=255, blank=True, null=True)
    display_type = models.CharField(_('Display Type'), max_length=200,
                                    choices=DISPLAY_CHOICES, default='doc')

    live = models.BooleanField(_('Live'), default=False)

    def __str__(self):
        return self.name

    def as_dict(self):
        "A dict respresentation of this for JSON encoding"
        image_url = reverse(
            'donate_view_proxy',
            kwargs={'promo_id': self.pk, 'hash': random.randint(0, 10000000)}
        )
        link_url = reverse(
            'donate_click_proxy',
            kwargs={'promo_id': self.pk}
        )
        return {
            'id': self.analytics_id,
            'text': self.text,
            'link': link_url,
            'image': image_url,
        }

    def incr(self, type):
        """Add to the number of times this action has been performed, stored in the DB"""
        assert type in ['offers', 'views', 'clicks']
        day = get_ad_day()
        impression, _ = self.impressions.get_or_create(date=day)
        setattr(impression, type, models.F(type) + 1)
        impression.save()

    def incr_redis(self, type):
        """Add to the number of times this action has been performed, stored in the Redis"""
        assert type in ['offers', 'views', 'clicks']
        day = get_ad_day()
        redis = Redis.from_url(settings.BROKER_URL)
        redis.incr('{slug}-{year}-{month}-{day}-{type}'.format(
            slug=self.analytics_id,
            year=day.year,
            month=day.month,
            day=day.day,
            type=type,
        ))

    def shown(self, day=None):
        """Return the percentage of times this ad was shown when offered."""
        if not day:
            day = get_ad_day()
        impression = self.impressions.get(date=day)
        return float(impression.offers) / float(impression.views)


class SupporterImpressions(models.Model):
    """Track stats around how successful this promo has been. """
    promo = models.ForeignKey(SupporterPromo, related_name='impressions',
                              blank=True, null=True)
    date = models.DateField(_('Date'))
    offers = models.IntegerField(_('Offer'), default=0)
    views = models.IntegerField(_('View'), default=0)
    clicks = models.IntegerField(_('Clicks'), default=0)

    class Meta:
        ordering = ('-date',)
        unique_together = ('promo', 'date')
