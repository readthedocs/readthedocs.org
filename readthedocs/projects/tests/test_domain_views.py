from unittest import mock

import dns.resolver
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Domain, Project
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    RTD_DEFAULT_FEATURES=dict([RTDProductFeature(type=TYPE_CNAME, value=2).to_item()]),
)
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

        # Ensure a message is shown
        messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Domain created")

    def test_domain_deletion(self):
        domain = get(Domain, project=self.project, domain="test.example.com")
        self.assertEqual(self.project.domains.count(), 1)

        resp = self.client.post(
            reverse("projects_domains_delete", args=[self.project.slug, domain.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.project.domains.count(), 0)

        # Ensure a message is shown
        messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Domain deleted")

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

    @mock.patch("readthedocs.projects.forms.dns.resolver.resolve")
    def test_create_domain_with_chained_cname_record(self, dns_resolve_mock):
        dns_resolve_mock.side_effect = [
            [mock.MagicMock(target="docs.example.com.")],
            [mock.MagicMock(target="readthedocs.io.")],
        ]
        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "docs2.example.com"},
        )
        assert resp.status_code == 200
        form = resp.context_data["form"]
        assert not form.is_valid()
        assert (
            "This domain has a CNAME record pointing to another CNAME"
            in form.errors["domain"][0]
        )

    @mock.patch("readthedocs.projects.forms.dns.resolver.resolve")
    def test_create_domain_with_cname_record_to_apex_domain(self, dns_resolve_mock):
        dns_resolve_mock.side_effect = [
            [mock.MagicMock(target="example.com.")],
        ]
        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "www.example.com"},
        )
        assert resp.status_code == 200
        form = resp.context_data["form"]
        assert not form.is_valid()
        assert (
            "This domain has a CNAME record pointing to the APEX domain"
            in form.errors["domain"][0]
        )

    @mock.patch("readthedocs.projects.forms.dns.resolver.resolve")
    def test_create_domain_cname_timeout(self, dns_resolve_mock):
        dns_resolve_mock.side_effect = dns.resolver.LifetimeTimeout
        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "docs.example.com"},
        )
        assert resp.status_code == 200
        form = resp.context_data["form"]
        assert not form.is_valid()
        assert "DNS resolution timed out" in form.errors["domain"][0]

    @mock.patch("readthedocs.projects.forms.dns.resolver.resolve")
    def test_create_domain_with_single_cname(self, dns_resolve_mock):
        dns_resolve_mock.side_effect = [
            [mock.MagicMock(target="readthedocs.io.")],
            dns.resolver.NoAnswer,
        ]
        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "docs.example.com"},
        )
        assert resp.status_code == 302
        domain = self.project.domains.first()
        assert domain.domain == "docs.example.com"

    @mock.patch("readthedocs.projects.forms.dns.resolver.resolve")
    def test_editing_domain_doesnt_trigger_cname_validation(self, dns_resolve_mock):
        domain = get(Domain, project=self.project, domain="docs.example.com")
        assert not domain.canonical
        resp = self.client.post(
            reverse("projects_domains_edit", args=[self.project.slug, domain.pk]),
            data={"canonical": True},
        )
        assert resp.status_code == 302
        domain.refresh_from_db()
        assert domain.canonical
        dns_resolve_mock.assert_not_called()

    @override_settings(
        RTD_DEFAULT_FEATURES=dict(
            [RTDProductFeature(type=TYPE_CNAME, value=1).to_item()]
        ),
    )
    @mock.patch("readthedocs.projects.forms.dns.resolver.resolve")
    def test_domains_limit(self, dns_resolve_mock):
        dns_resolve_mock.side_effect = dns.resolver.NoAnswer
        assert self.project.domains.count() == 0

        # Create the first domain
        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "test1.example.com"},
        )
        assert resp.status_code == 302
        assert self.project.domains.count() == 1

        # Create the second domain
        resp = self.client.post(
            reverse("projects_domains_create", args=[self.project.slug]),
            data={"domain": "test2.example.com"},
        )
        assert resp.status_code == 200
        form = resp.context_data["form"]
        assert not form.is_valid()
        assert "has reached the limit" in form.errors["__all__"][0]
        assert self.project.domains.count() == 1

        # Edit the existing domain
        domain = self.project.domains.first()
        assert not domain.canonical
        resp = self.client.post(
            reverse("projects_domains_edit", args=[self.project.slug, domain.pk]),
            data={"canonical": True},
        )
        assert resp.status_code == 302
        assert self.project.domains.count() == 1
        domain = self.project.domains.first()
        assert domain.canonical


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestDomainViewsWithOrganizations(TestDomainViews):
    def setUp(self):
        super().setUp()
        self.org = get(
            Organization, owners=[self.user], projects=[self.project, self.subproject]
        )
