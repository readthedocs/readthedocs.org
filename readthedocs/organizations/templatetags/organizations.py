"""Tags for organization template queries."""

from django import template
from django.contrib.auth.models import User
from django.core.exceptions import FieldError

from readthedocs.core.permissions import AdminPermission
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.projects.models import Project


register = template.Library()


@register.filter
def organization(obj):
    """Return organizations related with an object."""
    if isinstance(obj, User):
        return Organization.objects.for_user(obj)

    if isinstance(obj, Project):
        return Organization.objects.filter(projects=obj).first()

    if isinstance(obj, Team):
        return Organization.objects.filter(teams=obj).first()


@register.filter
def org_owner(user, obj):  # noqa
    """
    Determine if user is an owner on the parent organization, or organization
    passed in.

    Inspect object organization and return if user is an owner

    user
        User to inspect
    obj
        Any model instance with a relationship with an organization, or an
        organization itself.
    """
    try:
        cls = type(obj)
        if cls is Organization:
            return user in obj.owners.all()
        return cls.objects.filter(
            organization__owners=user,
            organization=obj.organization,
        ).exists()
    except (FieldError, AttributeError):
        return False


@register.filter
def teams(user):
    """Return teams across all orgs for a user."""
    return Team.objects.member(user)


@register.filter
def owner_organizations(user):
    """Return organizations the user is owner."""
    return user.owner_organizations.all()


@register.filter
def admin_teams(user):
    """Return admin teams across all orgs for a user."""
    return Team.objects.admin(user)


@register.filter(name="has_sso_enabled")
def has_sso_enabled_filter(obj, provider=None):
    """Check if `obj` has sso enabled for `provider`."""
    return AdminPermission.has_sso_enabled(obj, provider)
