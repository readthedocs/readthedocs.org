from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Domain, Project
from readthedocs.subscriptions.models import Plan, PlanFeature, Subscription


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestDomainViews(TestCase):
    def setUp(self):
        self.user = get(User, username="user")
        self.project = get(Project, users=[self.user], slug="project")
        self.subproject = get(Project, users=[self.user], slug="subproject")
        self.project.add_subproject(self.subproject)
        self.client.force_login(self.user)

    def test_domain_creation(self):
        self.assertEqual(self.project.domains.count(), 0)

        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "test.example.com"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.domains.count(), 1)

        domain = self.project.domains.first()
        self.assertEqual(domain.domain, "test.example.com")

    def test_domain_deletion(self):
        domain = get(Domain, project=self.project, domain="test.example.com")
        self.assertEqual(self.project.domains.count(), 1)

        resp = self.client.post(
            reverse("projects_domains_delete", args=[self.project.slug, domain.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.domains.count(), 0)

    def test_domain_edit(self):
        domain = get(
            Domain, project=self.project, domain="test.example.com", canonical=False
        )

        self.assertEqual(domain.canonical, False)
        resp = self.client.post(
            reverse("projects_domains_edit", args=[self.project.slug, domain.pk]),
            data={"canonical": True},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.domains.count(), 1)

        domain = self.project.domains.first()
        self.assertEqual(domain.domain, "test.example.com")
        self.assertEqual(domain.canonical, True)

    def test_adding_domain_on_subproject(self):
        self.assertEqual(self.subproject.domains.count(), 0)

        resp = self.client.post(
            reverse("projects_domains_create", args=[self.subproject.slug]),
            data={"domain": "test.example.com"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(self.subproject.domains.count(), 0)

    def test_delete_domain_on_subproject(self):
        domain = get(Domain, project=self.subproject, domain="test.example.com")
        self.assertEqual(self.subproject.domains.count(), 1)

        resp = self.client.post(
            reverse("projects_domains_delete", args=[self.subproject.slug, domain.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.subproject.domains.count(), 0)

    def test_edit_domain_on_subproject(self):
        domain = get(
            Domain, project=self.subproject, domain="test.example.com", canonical=False
        )

        self.assertEqual(domain.canonical, False)
        resp = self.client.post(
            reverse("projects_domains_edit", args=[self.subproject.slug, domain.pk]),
            data={"canonical": True},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(self.subproject.domains.count(), 1)

        domain = self.subproject.domains.first()
        self.assertEqual(domain.domain, "test.example.com")
        self.assertEqual(domain.canonical, False)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestDomainViewsWithOrganizations(TestDomainViews):
    def setUp(self):
        super().setUp()
        self.org = get(
            Organization, owners=[self.user], projects=[self.project, self.subproject]
        )
        self.plan = get(
            Plan,
            published=True,
        )
        self.subscription = get(
            Subscription,
            plan=self.plan,
            organization=self.org,
        )
        self.feature = get(
            PlanFeature,
            plan=self.plan,
            feature_type=PlanFeature.TYPE_CNAME,
        )
