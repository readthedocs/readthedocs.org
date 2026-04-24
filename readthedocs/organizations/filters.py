"""Filters used in the organization dashboard views."""

import structlog
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django_filters import ChoiceFilter
from django_filters import OrderingFilter

from readthedocs.core.filters import FilteredModelChoiceFilter
from readthedocs.core.filters import ModelFilterSet
from readthedocs.organizations.constants import ACCESS_LEVELS
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team


log = structlog.get_logger(__name__)


class OrganizationFilterSet(ModelFilterSet):
    """
    Organization base filter set.

    Adds some methods that are used for organization related queries and common
    base querysets for filter fields.

    Note, the querysets here are also found in the organization base views and
    mixin classes. These are redefined here instead of passing in the querysets
    from the view.

    :param organization: Organization instance for current view
    """

    def __init__(self, *args, organization=None, **kwargs):
        self.organization = organization
        super().__init__(*args, **kwargs)

    def get_organization_queryset(self):
        return Organization.objects.for_user(user=self.request.user)

    def get_team_queryset(self):
        return Team.objects.member(
            self.request.user,
            organization=self.organization,
        ).select_related("organization")


class OrganizationSortOrderingFilter(OrderingFilter):
    """Organization list sort ordering django_filters filter."""

    SORT_NAME = "name"
    SORT_CREATE_DATE = "pub_date"

    def __init__(self, *args, **kwargs):
        # The default filtering operation will be `name`, so we omit it
        # from choices to avoid showing it on the list twice.
        kwargs.setdefault("empty_label", _("Name"))
        kwargs.setdefault(
            "choices",
            (
                ("-" + self.SORT_CREATE_DATE, _("Recently created")),
                (self.SORT_CREATE_DATE, _("Least recently created")),
                (self.SORT_NAME, _("Name")),
                ("-" + self.SORT_NAME, _("Name (descending)")),
            ),
        )
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        # We use the None value from the custom filter, which django-filters is
        # a bit opinionated about. This is an explicit check for ``None``
        # instead of setting some default value, purposely to make display of
        # the unused/default filter correct.
        if not value:
            value = [self.SORT_NAME]

        order_bys = []
        for field_ordered in value:
            field = field_ordered.lstrip("-")

            if field_ordered == self.SORT_CREATE_DATE:
                order_bys.append(F(field).desc(nulls_last=True))
            elif field_ordered == "-" + self.SORT_CREATE_DATE:
                order_bys.append(F(field).asc(nulls_first=True))
            else:
                order_bys.append(field_ordered)

        return qs.order_by(*order_bys)


class OrganizationListFilterSet(OrganizationFilterSet):
    """Filter and sorting for organization listing page."""

    slug = FilteredModelChoiceFilter(
        label=_("Organization"),
        empty_label=_("All organizations"),
        to_field_name="slug",
        queryset_method="get_organization_queryset",
        method="get_organization",
        label_attribute="name",
    )

    sort = OrganizationSortOrderingFilter(
        field_name="sort",
        label=_("Sort by"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_organization(self, queryset, field_name, organization):
        return queryset.filter(slug=organization.slug)


class OrganizationProjectListFilterSet(OrganizationFilterSet):
    """
    Filter and sorting set for organization project listing page.

    This filter set creates the following filters in the organization project
    listing UI:

    Project
        A list of project names that the user has permissions to, using ``slug``
        as a lookup field. This is used when linking directly to a project in
        this filter list, and also for quick lookup in the list UI.

    Team
        A list of team names that the user has access to, using ``slug`` as a
        lookup field. This filter is linked to directly by the team listing
        view, as a shortcut for listing projects managed by the team.
    """

    slug = FilteredModelChoiceFilter(
        label=_("Project"),
        empty_label=_("All projects"),
        to_field_name="slug",
        queryset_method="get_project_queryset",
        method="get_project",
        label_attribute="name",
    )

    teams__slug = FilteredModelChoiceFilter(
        label=_("Team"),
        empty_label=_("All teams"),
        field_name="teams",
        to_field_name="slug",
        queryset_method="get_team_queryset",
        label_attribute="name",
    )

    def get_project_queryset(self):
        return self.queryset

    def get_project(self, queryset, field_name, project):
        return queryset.filter(slug=project.slug)


class OrganizationTeamListFilterSet(OrganizationFilterSet):
    """
    Filter and sorting for organization team listing page.

    This filter set creates the following filters in the organization team
    listing UI:

    Team
        A list of team names that the user has access to, using ``slug`` as a
        lookup field. This filter is used mostly for direct linking to a
        specific team in the listing UI, but can be used for quick filtering
        with the dropdown too.
    """

    slug = FilteredModelChoiceFilter(
        label=_("Team"),
        empty_label=_("All teams"),
        field_name="teams",
        to_field_name="slug",
        queryset_method="get_team_queryset",
        method="get_team",
        label_attribute="name",
    )

    def get_team_queryset(self):
        return self.queryset

    def get_team(self, queryset, field_name, team):
        return queryset.filter(slug=team.slug)


class OrganizationTeamMemberListFilterSet(OrganizationFilterSet):
    """
    Filter and sorting set for organization member listing page.

    This filter set's underlying queryset from the member listing view is the
    manager method ``Organization.members``. The model described in this filter
    is effectively ``User``, but through a union of ``TeamMembers.user`` and
    ``Organizations.owners``.

    This filter set will result in the following filters in the UI:

    Team
       A list of ``Team`` names, using ``Team.slug`` as the lookup field. This
       is linked to directly from the team listing page, to show the users that
       are members of a particular team.

    Access
       This is an extension of ``Team.access`` in a way, but with a new option
       (``ACCESS_OWNER``) to describe ownership privileges through organization
       ownership.

       Our modeling is not ideal here, so instead of aiming for model purity and
       a confusing UI/UX, this aims for hiding confusing modeling from the user
       with clear UI/UX. Otherwise, two competing filters are required for "user
       has privileges granted through a team" and "user has privileges granted
       through ownership".
    """

    ACCESS_OWNER = "owner"

    teams__slug = FilteredModelChoiceFilter(
        label=_("Team"),
        empty_label=_("All teams"),
        field_name="teams",
        to_field_name="slug",
        queryset_method="get_team_queryset",
        label_attribute="name",
    )

    access = ChoiceFilter(
        label=_("Access"),
        empty_label=_("All access levels"),
        choices=ACCESS_LEVELS + ((ACCESS_OWNER, _("Owner")),),
        method="get_access",
    )

    def get_access(self, queryset, field_name, value):
        # Note: the queryset here is effectively against the ``User`` model, and
        # is from Organization.members, a union of TeamMember.user and
        # Organization.owners.
        if value == self.ACCESS_OWNER:
            return queryset.filter(owner_organizations=self.organization)
        if value is not None:
            return queryset.filter(teams__access=value)
        return queryset
