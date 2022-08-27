"""Querysets for domain related models."""

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from readthedocs.projects.constants import SSL_STATUS_VALID
from readthedocs.projects.querysets import RelatedProjectQuerySet


class DomainQueryset(RelatedProjectQuerySet):
    def pending(self, include_recently_expired=False):
        max_date = timezone.now() - timezone.timedelta(
            days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD
        )
        queryset = self.exclude(
            Q(ssl_status=SSL_STATUS_VALID) | Q(skip_validation=True)
        )
        if include_recently_expired:
            return queryset.filter(validation_process_start__date__gte=max_date)
        return queryset.filter(validation_process_start__date__gt=max_date)

    def valid(self):
        return self.filter(ssl_status=SSL_STATUS_VALID)
