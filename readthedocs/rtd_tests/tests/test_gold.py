from __future__ import absolute_import
from django.core.urlresolvers import reverse
from django.test import TestCase

from django_dynamic_fixture import get, fixture

from readthedocs.gold.models import GoldUser, LEVEL_CHOICES
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.utils import create_user


class GoldViewTests(TestCase):

    def setUp(self):
        self.user = create_user(username='owner', password='test')

        self.project = get(Project, slug='test', users=[fixture(), self.user])

        self.golduser = get(GoldUser, user=self.user, level=LEVEL_CHOICES[0][0])

        self.client.login(username='owner', password='test')

    def test_adding_projects(self):
        self.assertEqual(self.golduser.projects.count(), 0)
        resp = self.client.post(reverse('gold_projects'), data={'project': 'test'})
        self.assertEqual(self.golduser.projects.count(), 1)
        self.assertEqual(resp.status_code, 302)

    def test_too_many_projects(self):
        self.project2 = get(Project, slug='test2')

        self.assertEqual(self.golduser.projects.count(), 0)
        resp = self.client.post(reverse('gold_projects'), data={'project': self.project.slug})
        self.assertEqual(self.golduser.projects.count(), 1)
        self.assertEqual(resp.status_code, 302)
        resp = self.client.post(reverse('gold_projects'), data={'project': self.project2.slug})
        self.assertFormError(
            resp, form='form', field=None, errors='You already have the max number of supported projects.'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.golduser.projects.count(), 1)

    def test_remove_project(self):
        self.assertEqual(self.golduser.projects.count(), 0)
        self.client.post(reverse('gold_projects'), data={'project': self.project.slug})
        self.assertEqual(self.golduser.projects.count(), 1)

        self.client.post(
            reverse('gold_projects_remove', args=[self.project.slug]),
        )
        self.assertEqual(self.golduser.projects.count(), 0)
