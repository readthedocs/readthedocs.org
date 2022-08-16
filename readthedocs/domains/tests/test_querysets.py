from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.projects.constants import (
    SSL_STATUS_INVALID,
    SSL_STATUS_PENDING,
    SSL_STATUS_VALID,
)
from readthedocs.projects.models import Domain, Project


class TestQuerysets(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.domain = get(Domain, project=self.project, ssl_status=SSL_STATUS_VALID)
        self.domain_pending = get(
            Domain, project=self.project, ssl_status=SSL_STATUS_PENDING
        )
        self.domain_invalid = get(
            Domain, project=self.project, ssl_status=SSL_STATUS_INVALID
        )
        self.domain_skip = get(
            Domain,
            project=self.project,
            ssl_status=SSL_STATUS_INVALID,
            skip_validation=True,
        )

        self.domain_recently_expired = get(
            Domain, project=self.project, ssl_status=SSL_STATUS_PENDING
        )
        self.domain_recently_expired.validation_process_start -= timezone.timedelta(
            days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD
        )
        self.domain_recently_expired.save()

        self.domain_expired = get(
            Domain, project=self.project, ssl_status=SSL_STATUS_PENDING
        )
        self.domain_expired.validation_process_start -= timezone.timedelta(
            days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD + 10
        )
        self.domain_expired.save()

    def test_pending(self):
        domains = set(Domain.objects.pending().all())
        self.assertEqual(domains, {self.domain_pending, self.domain_invalid})

        domains = set(Domain.objects.pending(include_recently_expired=True).all())
        self.assertEqual(
            domains,
            {self.domain_pending, self.domain_invalid, self.domain_recently_expired},
        )

    def test_valid(self):
        domains = set(Domain.objects.valid().all())
        self.assertEqual(domains, {self.domain})
