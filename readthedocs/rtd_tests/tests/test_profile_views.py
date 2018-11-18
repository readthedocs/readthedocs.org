from __future__ import division, print_function, unicode_literals

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_dynamic_fixture import get


class ProfileViewsTest(TestCase):

    def setUp(self):
        self.user = get(User)
        self.user.set_password('test')
        self.user.save()
        self.client.login(username=self.user.username, password='test')

    def test_edit_profile(self):
        resp = self.client.get(
            reverse('profiles_profile_edit'),
        )
        self.assertTrue(resp.status_code, 200)
        resp = self.client.post(
            reverse('profiles_profile_edit'),
            data={
                'first_name': 'Read',
                'last_name': 'Docs',
                'homepage': 'readthedocs.org',
            }
        )
        self.assertTrue(resp.status_code, 200)

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Read')
        self.assertEqual(self.user.last_name, 'Docs')
        self.assertEqual(self.user.profile.homepage, 'readthedocs.org')

    def test_edit_profile_with_invalid_values(self):
        resp = self.client.get(
            reverse('profiles_profile_edit'),
        )
        self.assertTrue(resp.status_code, 200)

        long_first_name = 'this-is-first_name-whose-length-is-greater-than-30'
        long_last_name = 'this-is-last_name-whose-length-is-greater-than-30'
        long_homepage = 'this-is-the-the-link-to-the-homepage-of-the-user-which-is-pretty-long-and-that-is-why-wrong-value.org'

        self.assertTrue(len(long_first_name) > 30)
        self.assertTrue(len(long_last_name) > 30)
        self.assertTrue(len(long_homepage) > 100)

        resp = self.client.post(
            reverse('profiles_profile_edit'),
            data={
                'first_name': long_first_name,
                'last_name': long_last_name,
                'homepage': long_homepage,
            }
        )

        FORM_ERROR_FORMAT = 'Ensure this value has at most {} characters (it has {}).'

        self.assertFormError(resp, form='form', field='first_name', errors=FORM_ERROR_FORMAT.format(30, len(long_first_name)))
        self.assertFormError(resp, form='form', field='last_name', errors=FORM_ERROR_FORMAT.format(30, len(long_last_name)))
        self.assertFormError(resp, form='form', field='homepage', errors=FORM_ERROR_FORMAT.format(100, len(long_homepage)))

    def test_delete_account(self):
        resp = self.client.get(
            reverse('delete_account')
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            reverse('delete_account'),
            data={
                'username': self.user.username,
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('homepage'))

        self.assertFalse(
            User.objects.filter(username=self.user.username).exists()
        )

    def test_profile_detail(self):
        resp = self.client.get(
            reverse('profiles_profile_detail', args=(self.user.username,)),
        )
        self.assertTrue(resp.status_code, 200)

    def test_profile_detail_logout(self):
        self.client.logout()
        resp = self.client.get(
            reverse('profiles_profile_detail', args=(self.user.username,)),
        )
        self.assertTrue(resp.status_code, 200)

    def test_profile_detail_not_found(self):
        resp = self.client.get(
            reverse('profiles_profile_detail', args=('not-found',)),
        )
        self.assertTrue(resp.status_code, 404)

    def test_account_advertising(self):
        resp = self.client.get(
            reverse('account_advertising')
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.user.profile.allow_ads)
        resp = self.client.post(
            reverse('account_advertising'),
            data={'allow_ads': False},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('account_advertising'))
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.allow_ads)
