"""
Filters used in the organization dashboard.

Some of the below filters instantiate with multiple querysets as django-filter
doesn't use the supplied queryset for filter field choices. By default the
``all()`` manager method is used from the filter field model. ``FilterSet`` is
mostly instantiated at class definition time, not per-instance, so we need to
pass in related querysets at view time.
"""

import structlog
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django_filters import (
    ChoiceFilter,
    FilterSet,
    ModelChoiceFilter,
    OrderingFilter,
)

from readthedocs.organizations.constants import ACCESS_LEVELS
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)


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


class OrganizationListFilterSet(FilterSet):

    """Filter and sorting for organization listing page."""

    slug = ModelChoiceFilter(
        label=_("Organization"),
        empty_label=_("All organizations"),
        to_field_name="slug",
        # Queryset is required, give an empty queryset from the correct model
        queryset=Organization.objects.none(),
        method="get_organization",
    )

    sort = OrganizationSortOrderingFilter(
        field_name="sort",
        label=_("Sort by"),
    )

    def __init__(
        self,
        data=None,
        queryset=None,
        *,
        request=None,
        prefix=None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        # Redefine the querysets used for the filter fields using the querysets
        # defined at view time. This populates the filter field with only the
        # correct related objects for the user. Otherwise, the default for model
        # choice filter fields is ``<Model>.objects.all()``.
        self.filters["slug"].field.queryset = self.queryset.all()

    def get_organization(self, queryset, field_name, organization):
        return queryset.filter(slug=organization.slug)


class OrganizationProjectListFilterSet(FilterSet):

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

    This filter set takes an additional argument, used to limit the model choice
    filter field values:

    :param team_queryset: Organization team list queryset
    """

    slug = ModelChoiceFilter(
        label=_("Project"),
        empty_label=_("All projects"),
        to_field_name="slug",
        # Queryset is required, give an empty queryset from the correct model
        queryset=Project.objects.none(),
        method="get_project",
    )

    teams__slug = ModelChoiceFilter(
        label=_("Team"),
        empty_label=_("All teams"),
        field_name="teams",
        to_field_name="slug",
        # Queryset is required, give an empty queryset from the correct model
        queryset=Team.objects.none(),
    )

    def __init__(
        self,
        data=None,
        queryset=None,
        *,
        request=None,
        prefix=None,
        teams_queryset=None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        # Redefine the querysets used for the filter fields using the querysets
        # defined at view time. This populates the filter field with only the
        # correct related objects for the user. Otherwise, the default for model
        # choice filter fields is ``<Model>.objects.all()``.
        self.filters["slug"].field.queryset = self.queryset.all()
        self.filters["teams__slug"].field.queryset = teams_queryset.all()

    def get_project(self, queryset, field_name, project):
        return queryset.filter(slug=project.slug)


class OrganizationTeamListFilterSet(FilterSet):

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

    slug = ModelChoiceFilter(
        label=_("Team"),
        empty_label=_("All teams"),
        field_name="teams",
        to_field_name="slug",
        # Queryset is required, give an empty queryset from the correct model
        queryset=Team.objects.none(),
        method="get_team",
    )

    def __init__(
        self,
        data=None,
        queryset=None,
        *,
        request=None,
        prefix=None,
        teams_queryset=None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        # Redefine the querysets used for the filter fields using the querysets
        # defined at view time. This populates the filter field with only the
        # correct related objects for the user/organization. Otherwise, the
        # default for model choice filter fields is ``<Model>.objects.all()``.
        self.filters["slug"].field.queryset = queryset.all()

    def get_team(self, queryset, field_name, team):
        return queryset.filter(slug=team.slug)


class OrganizationTeamMemberListFilterSet(FilterSet):

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

    teams__slug = ModelChoiceFilter(
        label=_("Team"),
        empty_label=_("All teams"),
        field_name="teams",
        to_field_name="slug",
        queryset=Team.objects.none(),
    )

    access = ChoiceFilter(
        label=_("Access"),
        empty_label=_("All access levels"),
        choices=ACCESS_LEVELS + ((ACCESS_OWNER, _("Owner")),),
        method="get_access",
    )

    def __init__(
        self, data=None, queryset=None, *, request=None, prefix=None, organization=None
    ):
        """
        Organization members filter set.

        This filter set requires the following additional parameters:

        :param organization: Organization for field ``filter()`` and used to
                             check for organization owner access.
        """
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.organization = organization
        # Redefine the querysets used for the filter fields using the querysets
        # defined at view time. This populates the filter field with only the
        # correct related objects for the user/organization. Otherwise, the
        # default for model choice filter fields is ``<Model>.objects.all()``.
        filter_with_user_relationship = True
        team_queryset = self.organization.teams
        if filter_with_user_relationship:
            # XXX remove this conditional and decide which one of these is most
            # correct There are reasons for both showing all the teams here and
            # only the team that the user has access to.
            team_queryset = Team.objects.member(request.user).filter(
                organization=self.organization,
            )
        self.filters["teams__slug"].field.queryset = team_queryset.all()

    def get_access(self, queryset, field_name, value):
        # Note: the queryset here is effectively against the ``User`` model, and
        # is from Organization.members, a union of TeamMember.user and
        # Organization.owners.
        if value == self.ACCESS_OWNER:
            return queryset.filter(owner_organizations=self.organization)
        if value is not None:
            return queryset.filter(teams__access=value)
        return queryset
