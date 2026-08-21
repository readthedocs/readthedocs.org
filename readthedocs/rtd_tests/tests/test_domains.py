from unittest import mock

import dns.resolver
from django.conf import settings
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.projects.forms import DomainForm
from readthedocs.projects.models import Domain, Project
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import RTDProductFeature, get_feature


class ModelTests(TestCase):
    def setUp(self):
        self.project = get(Project, slug="kong")

    def test_save_parsing(self):
        domain = get(Domain, domain="google.com")
        self.assertEqual(domain.domain, "google.com")

        domain.domain = "google.com"
        self.assertEqual(domain.domain, "google.com")

        domain.domain = "https://google.com"
        domain.save()
        self.assertEqual(domain.domain, "google.com")

        domain.domain = "www.google.com"
        domain.save()
        self.assertEqual(domain.domain, "www.google.com")


# We are using random domain names to test the form validation,
# so we are mocking the DNS resolver to avoid making real DNS queries.
@mock.patch(
    "readthedocs.projects.forms.dns.resolver.resolve",
    new=mock.MagicMock(side_effect=dns.resolver.NoAnswer),
)
class FormTests(TestCase):
    def setUp(self):
        self.project = get(Project, slug="kong")

    def test_https(self):
        """Make sure https is an admin-only attribute."""
        form = DomainForm(
            {"domain": "example.com", "canonical": True},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertTrue(domain.https)
        form = DomainForm(
            {
                "domain": "example.com",
                "canonical": True,
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())

    def test_production_domain_not_allowed(self):
        """Make sure user can not enter production domain name."""
        form = DomainForm(
            {"domain": settings.PRODUCTION_DOMAIN},
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["domain"][0],
            f"{settings.PRODUCTION_DOMAIN} is not a valid domain.",
        )

        form2 = DomainForm(
            {"domain": "test." + settings.PRODUCTION_DOMAIN},
            project=self.project,
        )
        self.assertFalse(form2.is_valid())
        self.assertEqual(
            form2.errors["domain"][0],
            f"{settings.PRODUCTION_DOMAIN} is not a valid domain.",
        )

    @override_settings(
        RTD_RESTRICTED_DOMAINS=[
            "readthedocs.org",
            "readthedocs.io",
            "readthedocs.build",
        ],
    )
    def test_restricted_domains_not_allowed(self):
        """Make sure user can not enter public domain name."""
        invalid_domains = [
            "readthedocs.org",
            "test.readthedocs.org",
            "app.readthedocs.org",
            "test.app.readthedocs.org",
            "readthedocs.io",
            "test.readthedocs.io",
            "docs.readthedocs.io",
            "test.docs.readthedocs.io",
            "readthedocs.build",
            "test.readthedocs.build",
            "docs.readthedocs.build",
            "test.docs.readthedocs.build",
            # Trailing white spaces, sneaky.
            "https:// readthedocs.org /",
        ]

        for domain in invalid_domains:
            form = DomainForm(
                {"domain": domain},
                project=self.project,
            )
            assert not form.is_valid(), domain
            assert "is not a valid domain." in form.errors["domain"][0]

    def test_domain_with_path(self):
        form = DomainForm(
            {"domain": "domain.com/foo/bar"},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, "domain.com")

    def test_valid_domains(self):
        domains = [
            "python.org",
            "a.io",
            "a.e.i.o.org",
            "my.domain.com.edu",
            "my-domain.fav",
        ]
        for domain in domains:
            form = DomainForm(
                {"domain": domain},
                project=self.project,
            )
            self.assertTrue(form.is_valid(), domain)

    def test_invalid_domains(self):
        domains = [
            "python..org",
            "****.foo.com",
            "domain",
            "domain.com.",
            "My domain.org",
            "i.o",
            "[special].com",
            "some_thing.org",
            "invalid-.com",
            "1.1.1.1",
            "1.23.45.67",
            "127.0.0.1",
            "127.0.0.10",
            "[1.2.3.4.com",
        ]
        for domain in domains:
            form = DomainForm(
                {"domain": domain},
                project=self.project,
            )
            self.assertFalse(form.is_valid(), domain)

    def test_canonical_change(self):
        """Make sure canonical can be properly changed."""
        form = DomainForm(
            {"domain": "example.com", "canonical": True},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, "example.com")

        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, "example.com")

        form = DomainForm(
            {"domain": "example2.com", "canonical": True},
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["canonical"][0], "Only one domain can be canonical at a time."
        )

        form = DomainForm(
            {"canonical": False},
            project=self.project,
            instance=domain,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, "example.com")
        self.assertFalse(domain.canonical)

    def test_allow_change_http_to_https(self):
        domain = get(Domain, domain="docs.example.com", https=False)
        form = DomainForm(
            {"https": True},
            project=self.project,
            instance=domain,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertTrue(domain.https)

    def test_dont_allow_changin_https_to_http(self):
        domain = get(Domain, domain="docs.example.com", https=True)
        form = DomainForm(
            {"https": False},
            project=self.project,
            instance=domain,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertTrue(domain.https)

    @override_settings(
        RTD_DEFAULT_FEATURES=dict(
            [RTDProductFeature(type=TYPE_CNAME, value=2).to_item()]
        ),
    )
    def test_domains_limit(self):
        feature = get_feature(self.project, TYPE_CNAME)
        form = DomainForm(
            {
                "domain": "docs.user.example.com",
                "canonical": True,
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(self.project.domains.all().count(), 1)

        form = DomainForm(
            {
                "domain": "docs.dev.example.com",
                "canonical": False,
            },
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(self.project.domains.all().count(), 2)

        # Creating the third (3) domain should fail the validation form
        form = DomainForm(
            {
                "domain": "docs.customer.example.com",
                "canonical": False,
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())

        msg = (
            f"This project has reached the limit of {feature.value} domains. "
            "Consider removing unused domains."
        )
        if settings.RTD_ALLOW_ORGANIZATIONS:
            msg = (
                f"Your organization has reached the limit of {feature.value} domains. "
                "Consider removing unused domains or upgrading your plan."
            )
        self.assertEqual(form.errors["__all__"][0], msg)
