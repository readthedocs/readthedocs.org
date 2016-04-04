from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from readthedocs.donate.utils import get_ad_day


DISPLAY_CHOICES = (
    ('doc', 'Documentation Pages'),
    ('site-footer', 'Site Footer'),
    ('search', 'Search Pages'),
)

OFFERS = 'offers'
VIEWS = 'views'
CLICKS = 'clicks'

IMPRESSION_TYPES = (
    OFFERS,
    VIEWS,
    CLICKS
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
        hash = get_random_string()
        domain = getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org')
        image_url = '//{host}{url}'.format(
            host=domain,
            url=reverse(
                'donate_view_proxy',
                kwargs={'promo_id': self.pk, 'hash': hash}
            ))
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
        assert type in IMPRESSION_TYPES
        return 'promo:{id}:{hash}:{type}'.format(id=self.analytics_id, hash=hash, type=type)

    def incr(self, type):
        """Add to the number of times this action has been performed, stored in the DB"""
        assert type in IMPRESSION_TYPES
        day = get_ad_day()
        impression, _ = self.impressions.get_or_create(date=day)
        setattr(impression, type, models.F(type) + 1)
        impression.save()

        # TODO: Support redis, more info on this PR
        # github.com/rtfd/readthedocs.org/pull/2105/files/1b5f8568ae0a7760f7247149bcff481efc000f32#r58253051

    def view_ratio(self, day=None):
        if not day:
            day = get_ad_day()
        impression = self.impressions.get(date=day)
        return impression.view_ratio

    def click_ratio(self, day=None):
        if not day:
            day = get_ad_day()
        impression = self.impressions.get(date=day)
        return impression.click_ratio


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

    @property
    def view_ratio(self):
        if self.offers == 0:
            return 0  # Don't divide by 0
        return float(self.views) / float(self.offers)

    @property
    def click_ratio(self):
        if self.views == 0:
            return 0  # Don't divide by 0
        return float(self.clicks) / float(self.views)
