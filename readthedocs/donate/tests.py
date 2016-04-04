import json

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.cache import cache

from django_dynamic_fixture import get

from .models import SupporterPromo, CLICKS, VIEWS, OFFERS
from readthedocs.projects.models import Project


class PromoTests(TestCase):

    def setUp(self):
        self.promo = get(SupporterPromo,
                         slug='promo-slug',
                         link='http://example.com',
                         image='http://media.example.com/img.png')

    def test_clicks(self):
        cache.set(self.promo.cache_key(type=CLICKS, hash='random_hash'), 0)
        resp = self.client.get('http://testserver/sustainability/click/%s/random_hash/' % self.promo.id)
        self.assertEqual(resp._headers['location'][1], 'http://example.com')
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.clicks, 1)

    def test_views(self):
        cache.set(self.promo.cache_key(type=VIEWS, hash='random_hash'), 0)
        resp = self.client.get('http://testserver/sustainability/view/%s/random_hash/' % self.promo.id)
        self.assertEqual(resp._headers['location'][1], 'http://media.example.com/img.png')
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.views, 1)

    def test_stats(self):
        for x in range(50):
            self.promo.incr(OFFERS)
        for x in range(20):
            self.promo.incr(VIEWS)
        for x in range(3):
            self.promo.incr(CLICKS)
        self.assertEqual(self.promo.view_ratio(), 0.4)
        self.assertEqual(self.promo.click_ratio(), 0.15)

    def test_multiple_hash_usage(self):
        cache.set(self.promo.cache_key(type=VIEWS, hash='random_hash'), 0)
        self.client.get('http://testserver/sustainability/view/%s/random_hash/' % self.promo.id)
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.views, 1)

        # Don't increment again.
        self.client.get('http://testserver/sustainability/view/%s/random_hash/' % self.promo.id)
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.views, 1)


class FooterTests(TestCase):

    def setUp(self):
        self.promo = get(SupporterPromo,
                         live=True,
                         slug='promo-slug',
                         display_type='doc',
                         link='http://example.com',
                         image='http://media.example.com/img.png')
        self.pip = get(Project, slug='pip')

    def test_footer(self):
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertEqual(resp['promo_data']['link'], '//readthedocs.org/sustainability/click/%s/%s/' % (self.promo.pk, resp['promo_data']['hash']))
        impression = self.promo.impressions.first()
        self.assertEqual(impression.offers, 1)

    def test_integration(self):
        # Get footer promo
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertEqual(
            resp['promo_data']['link'],
            '//readthedocs.org/sustainability/click/%s/%s/' % (self.promo.pk, resp['promo_data']['hash'])
        )
        impression = self.promo.impressions.first()
        self.assertEqual(impression.offers, 1)
        self.assertEqual(impression.views, 0)
        self.assertEqual(impression.clicks, 0)

        # Assert view

        r = self.client.get(
            reverse(
                'donate_view_proxy',
                kwargs={'promo_id': self.promo.pk, 'hash': resp['promo_data']['hash']}
            )
        )
        impression = self.promo.impressions.first()
        self.assertEqual(impression.offers, 1)
        self.assertEqual(impression.views, 1)
        self.assertEqual(impression.clicks, 0)

        # Click

        r = self.client.get(
            reverse(
                'donate_click_proxy',
                kwargs={'promo_id': self.promo.pk, 'hash': resp['promo_data']['hash']}
            )
        )
        impression = self.promo.impressions.first()
        self.assertEqual(impression.offers, 1)
        self.assertEqual(impression.views, 1)
        self.assertEqual(impression.clicks, 1)
