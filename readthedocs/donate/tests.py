import json

from django.test import TestCase

from django_dynamic_fixture import get

from .models import SupporterPromo
from readthedocs.projects.models import Project


class PromoTests(TestCase):

    def setUp(self):
        self.promo = get(SupporterPromo,
                         slug='promo-slug',
                         link='http://example.com',
                         image='http://media.example.com/img.png')

    def test_clicks(self):
        resp = self.client.get('http://testserver/sustainability/click/%s/' % self.promo.id)
        self.assertEqual(resp._headers['location'][1], 'http://example.com')
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.clicks, 1)

    def test_views(self):
        resp = self.client.get('http://testserver/sustainability/click/%s/random_hash/' % self.promo.id)
        self.assertEqual(resp._headers['location'][1], 'http://media.example.com/img.png')
        promo = SupporterPromo.objects.get(pk=self.promo.pk)
        impression = promo.impressions.first()
        self.assertEqual(impression.views, 1)

    def test_stats(self):
        for x in range(5):
            self.promo.incr('offers')
        for x in range(2):
            self.promo.incr('views')
        self.assertEqual(self.promo.shown(), 2.5)


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
        self.assertEqual(resp['promo_data']['link'], '/sustainability/click/%s/' % self.promo.pk)
        impression = self.promo.impressions.first()
        self.assertEqual(impression.offers, 1)
