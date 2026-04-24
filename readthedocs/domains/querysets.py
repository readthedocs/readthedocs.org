"""Querysets for domain related models."""

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from readthedocs.projects.constants import SSL_STATUS_VALID
from readthedocs.projects.querysets import RelatedProjectQuerySet


class DomainQueryset(RelatedProjectQuerySet):
    """Domain querysets."""

    def pending(self, include_recently_expired=False):
        max_date = timezone.now() - timedelta(days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD)
        queryset = self.exclude(Q(ssl_status=SSL_STATUS_VALID) | Q(skip_validation=True))
        if include_recently_expired:
            return queryset.filter(validation_process_start__date__gte=max_date)
        return queryset.filter(validation_process_start__date__gt=max_date)

    def expired(self, when=None):
        """
        Return domains that have their validation process expired.

        :param when: If given, return domains that expired on this date only.
        """
        queryset = self.exclude(Q(ssl_status=SSL_STATUS_VALID) | Q(skip_validation=True))
        if when:
            start_date = when - timedelta(days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD)
            queryset = queryset.filter(validation_process_start__date=start_date)
        else:
            max_date = timezone.now() - timedelta(
                days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD
            )
            queryset = queryset.filter(validation_process_start__date__lte=max_date)
        return queryset

    def valid(self):
        return self.filter(ssl_status=SSL_STATUS_VALID)
