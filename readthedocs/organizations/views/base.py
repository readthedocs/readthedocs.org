"""Base classes for organization views."""

from functools import lru_cache

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.forms import OrganizationForm
from readthedocs.organizations.forms import OrganizationOwnerForm
from readthedocs.organizations.forms import OrganizationTeamBasicForm
from readthedocs.organizations.forms import OrganizationTeamMemberForm
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import OrganizationOwner
from readthedocs.organizations.models import Team
from readthedocs.organizations.models import TeamMember


class CheckOrganizationsEnabled:
    """
    Return 404 if organizations aren't enabled.

    All organization views should inherit this class.
    This is mainly for our tests to work,
    adding the organization urls conditionally on readthedocs/urls.py
    doesn't work as the file is evaluated only once, not per-test case.
    """

    def dispatch(self, *args, **kwargs):
        if not settings.RTD_ALLOW_ORGANIZATIONS:
            raise Http404
        return super().dispatch(*args, **kwargs)


# Mixins
class OrganizationMixin(SuccessMessageMixin, CheckOrganizationsEnabled):
    """
    Mixin class that provides organization sublevel objects.

    This mixin uses several class level variables

    org_url_field
        The URL kwarg name for the organization slug

    admin_only
        Boolean the dictacts access for organization owners only or just member
        access
    """

    org_url_field = "slug"
    admin_only = True

    def get_queryset(self):
        """Return queryset that returns organizations for user."""
        return self.get_organization_queryset()

    def get_organization_queryset(self):
        """
        Return organizations queryset for the request user.

        This will return organizations that the user has admin/owner access to
        if :py:data:`admin_only` is True.  Otherwise, this will return
        organizations where the request user is a member of the team
        """
        if self.admin_only:
            return Organization.objects.for_admin_user(user=self.request.user)
        return Organization.objects.for_user(user=self.request.user)

    @lru_cache(maxsize=1)
    def get_organization(self):
        """Return organization determined by url kwarg."""
        if self.org_url_field not in self.kwargs:
            return None
        return get_object_or_404(
            self.get_organization_queryset(),
            slug=self.kwargs[self.org_url_field],
        )

    def get_context_data(self, **kwargs):
        """Add organization to context data."""
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        context["organization"] = organization
        return context


class OrganizationTeamMixin(OrganizationMixin):
    """
    Add team query and instance methods for team related views.

    This extends the :py:cls:`OrganizationMixin` to provide both teams and
    organizations to the team views. Team forms are passed in the organization
    determined from the organization url kwarg.
    """

    def get_team_queryset(self):
        """
        Return teams visible to request user.

        This will either be team the user is a member of, or teams where the
        user is an owner of the organization.
        """
        return (
            Team.objects.member(self.request.user)
            .filter(
                organization=self.get_organization(),
            )
            .order_by("name")
        )

    @lru_cache(maxsize=1)
    def get_team(self):
        """Return team determined by url kwarg."""
        return get_object_or_404(
            self.get_team_queryset(),
            slug=self.kwargs["team"],
        )

    def get_form(self, data=None, files=None, **kwargs):
        """Pass in organization to form class instance."""
        kwargs["organization"] = self.get_organization()
        return self.form_class(data, files, **kwargs)


# Base views
class OrganizationView(SuccessMessageMixin, CheckOrganizationsEnabled):
    """Mixin for an organization view that doesn't have nested components."""

    model = Organization
    form_class = OrganizationForm
    admin_only = True

    # Only relevant when mixed into
    lookup_field = "slug"
    lookup_url_field = "slug"

    def get_queryset(self):
        if self.admin_only:
            return Organization.objects.for_admin_user(user=self.request.user)
        return Organization.objects.for_user(user=self.request.user)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["user"] = self.request.user
        cls = self.get_form_class()
        return cls(data, files, **kwargs)

    def get_context_data(self, **kwargs):
        """Add onboarding context."""
        context = super().get_context_data(**kwargs)
        if not self.get_queryset().exists():
            context["onboarding"] = True
        return context

    def get_success_url(self):
        return reverse_lazy(
            "organization_edit",
            args=[self.object.slug],
        )


class OrganizationOwnerView(OrganizationMixin):
    """Mixin for views related to organization owners."""

    model = OrganizationOwner
    form_class = OrganizationOwnerForm
    admin_only = True
    lookup_url_kwarg = "owner"

    def get_queryset(self):
        return OrganizationOwner.objects.filter(
            organization=self.get_organization(),
        ).select_related("owner")

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["organization"] = self.get_organization()
        kwargs["request"] = self.request
        return self.form_class(data, files, **kwargs)

    def _get_invitations(self):
        return Invitation.objects.for_object(self.get_organization())

    def _is_last_user(self):
        return self.get_queryset().count() <= 1

    def get_context_data(self, **kwargs):
        """Add list of related objects from queryset to context data."""
        context = super().get_context_data(**kwargs)
        context["owners"] = [orgowner.owner for orgowner in self.get_queryset()]
        context["owner_objs"] = self.get_queryset()
        context["is_last_user"] = self._is_last_user()
        context["invitations"] = self._get_invitations()
        return context

    def get_success_url(self):
        return reverse_lazy(
            "organization_owners",
            args=[self.get_organization().slug],
        )


class OrganizationTeamView(OrganizationTeamMixin):
    """Mixin for views related to organization teams."""

    model = Team
    form_class = OrganizationTeamBasicForm

    def get_queryset(self):
        return self.get_team_queryset()

    def get_object(self):
        return self.get_team()

    def get_success_url(self):
        return reverse_lazy(
            "organization_team_detail",
            args=[
                self.get_organization().slug,
                self.object.slug,
            ],
        )


class OrganizationTeamMemberView(OrganizationTeamMixin):
    """Mixin for views related to organization team members."""

    model = TeamMember
    form_class = OrganizationTeamMemberForm

    def get_queryset(self):
        return TeamMember.objects.sorted().filter(
            team=self.get_team(),
            team__organization=self.get_organization(),
        )

    def get_object(self):
        return self.get_queryset().get(pk=self.kwargs["member"])

    def _get_invitations(self):
        return Invitation.objects.for_object(self.get_team())

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["team"] = self.get_team()
        kwargs["request"] = self.request
        return self.form_class(data, files, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.get_team()
        context["invitations"] = self._get_invitations()
        return context

    def get_success_url(self):
        organization = self.get_organization()
        team = self.get_team()
        return reverse_lazy(
            "organization_team_detail",
            args=[organization.slug, team.slug],
        )
