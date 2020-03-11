"""Organizations querysets."""

from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone

from readthedocs.core.utils.extend import SettingsOverrideObject


class BaseOrganizationQuerySet(models.QuerySet):

    """Organizations queryset."""

    def for_user(self, user=None):
        # Never list all for membership
        return self.filter(
            Q(owners__in=[user]) | Q(teams__members__in=[user]),
        ).distinct()

    def for_admin_user(self, user=None, include_all=False):
        if user.is_superuser and include_all:
            return self.all()
        return self.filter(owners__in=[user],).distinct()

    def created_days_ago(self, days, field='pub_date'):
        """
        Filter organizations by creation date.

        :param days: Days ago that organization was created
        :param field: Field name to use in comparison, default: pub_date
        """
        when = timezone.now() - timedelta(days=days)
        query_filter = {}
        query_filter[field + '__year'] = when.year
        query_filter[field + '__month'] = when.month
        query_filter[field + '__day'] = when.day
        return self.filter(**query_filter)


class OrganizationQuerySet(SettingsOverrideObject):

    _default_class = BaseOrganizationQuerySet
