"""Organizations querysets."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from readthedocs.core.utils.extend import SettingsOverrideObject


class BaseOrganizationQuerySet(models.QuerySet):

    """Organizations queryset."""

    def public(self, user):
        """
        Return all organizations the user has access to.

        If ``ALLOW_PRIVATE_REPOS`` is `False`, all organizations are public by default.
        Otherwise, we return only the organizations where the user is a member or owner.
        """
        if not settings.ALLOW_PRIVATE_REPOS:
            return self.all()
        return self.for_user(user)

    def for_user(self, user):
        """List all organizations where the user is a member or owner."""
        if not user.is_authenticated:
            return self.none()
        return self.filter(
            Q(owners__in=[user]) | Q(teams__members__in=[user]),
        ).distinct()

    def for_admin_user(self, user):
        """List all organizations where the user is an owner."""
        if not user.is_authenticated:
            return self.none()
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
