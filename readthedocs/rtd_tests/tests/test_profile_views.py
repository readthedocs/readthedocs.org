# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get
from rest_framework.authtoken.models import Token


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
            },
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

        resp = self.client.post(
            reverse('profiles_profile_edit'),
            data={
                'first_name': 'a' * 31,
                'last_name': 'b' * 31,
                'homepage': 'c' * 101,
            },
        )

        FORM_ERROR_FORMAT = 'Ensure this value has at most {} characters (it has {}).'

        self.assertFormError(resp, form='form', field='first_name', errors=FORM_ERROR_FORMAT.format(30, 31))
        self.assertFormError(resp, form='form', field='last_name', errors=FORM_ERROR_FORMAT.format(30, 31))
        self.assertFormError(resp, form='form', field='homepage', errors=FORM_ERROR_FORMAT.format(100, 101))

    def test_delete_account(self):
        resp = self.client.get(
            reverse('delete_account'),
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            reverse('delete_account'),
            data={
                'username': self.user.username,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('homepage'))

        self.assertFalse(
            User.objects.filter(username=self.user.username).exists(),
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
            reverse('account_advertising'),
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

    def test_list_api_tokens(self):
        resp = self.client.get(reverse('profiles_tokens'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No API Tokens currently configured.')

        Token.objects.create(user=self.user)
        resp = self.client.get(reverse('profiles_tokens'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'Token: {self.user.auth_token.key}')

    def test_create_api_token(self):
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)

        resp = self.client.get(reverse('profiles_tokens_create'))
        self.assertEqual(resp.status_code, 405)  # GET not allowed

        resp = self.client.post(reverse('profiles_tokens_create'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_delete_api_token(self):
        Token.objects.create(user=self.user)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

        resp = self.client.post(reverse('profiles_tokens_delete'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)
