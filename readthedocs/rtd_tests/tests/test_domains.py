# -*- coding: utf-8 -*-

import json

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.projects.forms import DomainForm
from readthedocs.projects.models import Domain, Project


class ModelTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')

    def test_save_parsing(self):
        domain = get(Domain, domain='google.com')
        self.assertEqual(domain.domain, 'google.com')

        domain.domain = 'google.com'
        self.assertEqual(domain.domain, 'google.com')

        domain.domain = 'https://google.com'
        domain.save()
        self.assertEqual(domain.domain, 'google.com')

        domain.domain = 'www.google.com'
        domain.save()
        self.assertEqual(domain.domain, 'www.google.com')


class FormTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')

    def test_https(self):
        """Make sure https is an admin-only attribute."""
        form = DomainForm(
            {'domain': 'example.com', 'canonical': True},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertFalse(domain.https)
        form = DomainForm(
            {
                'domain': 'example.com', 'canonical': True,
                'https': True,
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())

    def test_canonical_change(self):
        """Make sure canonical can be properly changed."""
        form = DomainForm(
            {'domain': 'example.com', 'canonical': True},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, 'example.com')

        form = DomainForm(
            {'domain': 'example2.com', 'canonical': True},
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['canonical'][0], 'Only 1 Domain can be canonical at a time.')

        form = DomainForm(
            {'canonical': False},
            project=self.project,
            instance=domain,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, 'example.com')
        self.assertFalse(domain.canonical)


class TestAPI(TestCase):

    def setUp(self):
        self.project = get(Project)
        self.domain = self.project.domains.create(domain='djangokong.com')

    def test_basic_api(self):
        resp = self.client.get('/api/v2/domain/')
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['results'][0]['domain'], 'djangokong.com')
        self.assertEqual(obj['results'][0]['canonical'], False)
        self.assertNotIn('https', obj['results'][0])
