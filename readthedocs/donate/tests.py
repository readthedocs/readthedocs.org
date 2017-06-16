from __future__ import absolute_import

import json
import mock

from builtins import range
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.test.client import RequestFactory
from django_dynamic_fixture import get

from .core.middleware import FooterNoSessionMiddleware
from .models import SupporterPromo, GeoFilter, Country
from .constants import (CLICKS, VIEWS, OFFERS,
                        INCLUDE, EXCLUDE)
from .signals import show_to_geo, get_promo, choose_promo, show_to_programming_language
from readthedocs.projects.models import Project


class PromoTests(TestCase):

    def setUp(self):
        self.promo = get(SupporterPromo,
                         slug='promo-slug',
                         link='http://example.com',
                         image='http://media.example.com/img.png')
        self.pip = get(Project, slug='pip', allow_promos=True)

    def test_clicks(self):
        cache.set(self.promo.cache_key(type=CLICKS, hash='random_hash'), 0)
        resp = self.client.get(
            'http://testserver/sustainability/click/%s/random_hash/' % self.promo.id)
        self.assertEqual(resp._headers['location'][1], 'http://example.com')
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.clicks, 1)

    def test_views(self):
        cache.set(self.promo.cache_key(type=VIEWS, hash='random_hash'), 0)
        resp = self.client.get(
            'http://testserver/sustainability/view/%s/random_hash/' % self.promo.id)
        self.assertEqual(resp._headers['location'][1], 'http://media.example.com/img.png')
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.views, 1)

    def test_project_clicks(self):
        cache.set(self.promo.cache_key(type=CLICKS, hash='random_hash'), 0)
        cache.set(self.promo.cache_key(type='project', hash='random_hash'), self.pip.slug)
        self.client.get('http://testserver/sustainability/click/%s/random_hash/' % self.promo.id)
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.project_impressions.first()
        self.assertEqual(impression.clicks, 1)

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

    def test_invalid_id(self):
        resp = self.client.get('http://testserver/sustainability/view/invalid/data/')
        self.assertEqual(resp.status_code, 404)

    def test_invalid_hash(self):
        cache.set(self.promo.cache_key(type=VIEWS, hash='valid_hash'), 0)
        resp = self.client.get(
            'http://testserver/sustainability/view/%s/invalid_hash/' % self.promo.id)
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        self.assertEqual(promo.impressions.count(), 0)
        self.assertEqual(resp._headers['location'][1], 'http://media.example.com/img.png')


class FooterTests(TestCase):

    def setUp(self):
        self.promo = get(SupporterPromo,
                         live=True,
                         slug='promo-slug',
                         display_type='doc',
                         link='http://example.com',
                         image='http://media.example.com/img.png')
        self.pip = get(Project, slug='pip', allow_promos=True)

    def test_footer(self):
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertEqual(
            resp['promo_data']['link'],
            '//readthedocs.org/sustainability/click/%s/%s/' % (
                self.promo.pk, resp['promo_data']['hash']
            )
        )
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
            '//readthedocs.org/sustainability/click/%s/%s/' % (
                self.promo.pk, resp['promo_data']['hash'])
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

    def test_footer_setting(self):
        """Test that the promo doesn't show with USE_PROMOS is False"""
        with self.settings(USE_PROMOS=False):
            r = self.client.get(
                '/api/v2/footer_html/?project=pip&version=latest&page=index'
            )
            resp = json.loads(r.content)
            self.assertEqual(resp['promo'], False)

    def test_footer_no_obj(self):
        """Test that the promo doesn't get set with no SupporterPromo objects"""
        self.promo.delete()
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertEqual(resp['promo'], False)

    def test_project_disabling(self):
        """Test that the promo doesn't show when the project has it disabled"""
        self.pip.allow_promos = False
        self.pip.save()
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertEqual(resp['promo'], False)

    def test_user_disabling(self):
        """Test that the promo doesn't show when the project has it disabled"""
        user = User.objects.get(username='test')
        user.profile.allow_ads = False
        user.profile.save()

        # No ads for logged in user
        self.login('test', 'test')
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertEqual(resp['promo'], False)

        # Ads for logged out user
        self.logout()
        r = self.client.get(
            '/api/v2/footer_html/?project=pip&version=latest&page=index'
        )
        resp = json.loads(r.content)
        self.assertTrue(resp['promo'] is not False)


class FilterTests(TestCase):

    def setUp(self):
        us = get(Country, country='US')
        ca = get(Country, country='CA')
        mx = get(Country, country='MX')
        az = get(Country, country='AZ')

        # Only show in US,CA
        self.promo = get(SupporterPromo,
                         slug='promo-slug',
                         link='http://example.com',
                         live=True,
                         programming_language='py',
                         image='http://media.example.com/img.png'
                         )
        self.filter = get(GeoFilter,
                          promo=self.promo,
                          countries=[us, ca, mx],
                          filter_type=INCLUDE,
                          )

        # Don't show in AZ
        self.promo2 = get(SupporterPromo,
                          slug='promo2-slug',
                          link='http://example.com',
                          live=True,
                          programming_language='js',
                          image='http://media.example.com/img.png')
        self.filter2 = get(GeoFilter,
                           promo=self.promo2,
                           countries=[az],
                           filter_type=EXCLUDE,
                           )

        self.pip = get(Project, slug='pip', allow_promos=True, programming_language='py')

    def test_include(self):
        # US view
        ret = show_to_geo(self.promo, 'US')
        self.assertTrue(ret)

        ret = show_to_geo(self.promo2, 'US')
        self.assertTrue(ret)

    def test_exclude(self):
        # Az -- don't show AZ ad
        ret = show_to_geo(self.promo, 'AZ')
        self.assertFalse(ret)

        ret = show_to_geo(self.promo2, 'AZ')
        self.assertFalse(ret)

    def test_non_included_data(self):
        # Random Country -- don't show "only US" ad
        ret = show_to_geo(self.promo, 'FO')
        self.assertFalse(ret)

        ret2 = show_to_geo(self.promo2, 'FO')
        self.assertFalse(ret2)

    def test_get_promo(self):
        ret = get_promo('US')
        self.assertTrue(ret in [self.promo, self.promo2])

        ret = get_promo('MX')
        self.assertTrue(ret in [self.promo, self.promo2])

        ret = get_promo('FO')
        self.assertEqual(ret, self.promo2)

        ret = get_promo('AZ')
        self.assertEqual(ret, None)

        ret = get_promo('RANDOM')
        self.assertEqual(ret, self.promo2)

    def test_programming_language(self):
        ret = show_to_programming_language(self.promo, 'py')
        self.assertTrue(ret)

        ret = show_to_programming_language(self.promo, 'js')
        self.assertFalse(ret)

        ret = show_to_programming_language(self.promo2, 'py')
        self.assertTrue(ret)

        ret = show_to_programming_language(self.promo2, 'js')
        self.assertFalse(ret)


class ProbabilityTests(TestCase):

    def setUp(self):
        # Only show in US,CA
        self.promo = get(SupporterPromo,
                         slug='promo-slug',
                         link='http://example.com',
                         live=True,
                         image='http://media.example.com/img.png',
                         sold_impressions=1000,
                         )

        # Don't show in AZ
        self.promo2 = get(SupporterPromo,
                          slug='promo2-slug',
                          link='http://example.com',
                          live=True,
                          image='http://media.example.com/img.png',
                          sold_impressions=1000 * 1000,
                          )
        self.promo_list = [self.promo, self.promo2]

    def test_choose(self):
        # US view

        promo_prob = self.promo.views_needed()
        promo2_prob = self.promo2.views_needed()
        total = promo_prob + promo2_prob

        with mock.patch('random.randint') as randint:

            randint.return_value = -1
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, None)

            randint.return_value = 5
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, self.promo)

            randint.return_value = promo_prob - 1
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, self.promo)

            randint.return_value = promo_prob
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, self.promo)

            randint.return_value = promo_prob + 1
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, self.promo2)

            randint.return_value = total - 1
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, self.promo2)

            randint.return_value = total
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, self.promo2)

            randint.return_value = total + 1
            ret = choose_promo(self.promo_list)
            self.assertEqual(ret, None)


class CookieTests(TestCase):

    def setUp(self):
        self.promo = get(SupporterPromo, live=True)

    def test_no_cookie(self):
        mid = FooterNoSessionMiddleware()
        factory = RequestFactory()

        # Setup
        cache.set(self.promo.cache_key(type=VIEWS, hash='random_hash'), 0)
        request = factory.get(
            'http://testserver/sustainability/view/%s/random_hash/' % self.promo.id
        )

        # Null session here
        mid.process_request(request)
        self.assertEqual(request.session, {})

        # Proper session here
        home_request = factory.get('/')
        mid.process_request(home_request)
        self.assertTrue(home_request.session.TEST_COOKIE_NAME, 'testcookie')
