"""Views that don't require login."""

# pylint: disable=too-many-ancestors
import structlog
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from vanilla import DetailView
from vanilla import GenericView
from vanilla import ListView

from readthedocs.core.filters import FilterContextMixin
from readthedocs.core.permissions import AdminPermission
from readthedocs.notifications.models import Notification
from readthedocs.organizations.filters import OrganizationProjectListFilterSet
from readthedocs.organizations.filters import OrganizationTeamListFilterSet
from readthedocs.organizations.filters import OrganizationTeamMemberListFilterSet
from readthedocs.organizations.views.base import CheckOrganizationsEnabled
from readthedocs.organizations.views.base import OrganizationMixin
from readthedocs.organizations.views.base import OrganizationTeamMemberView
from readthedocs.organizations.views.base import OrganizationTeamView
from readthedocs.organizations.views.base import OrganizationView
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


class OrganizationTemplateView(CheckOrganizationsEnabled, TemplateView):
    """Wrapper around `TemplateView` to check if organizations are enabled."""


# Organization


class DetailOrganization(FilterContextMixin, OrganizationView, DetailView):
    """Display information about an organization."""

    template_name = "organizations/organization_detail.html"
    admin_only = False

    filterset_class = OrganizationProjectListFilterSet
    strict = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()
        projects = Project.objects.for_user(self.request.user).filter(organizations=org).all()
        context["filter"] = self.get_filterset(
            queryset=projects,
            organization=org,
        )
        projects = self.get_filtered_queryset()

        context["projects"] = projects
        context["notifications"] = Notification.objects.for_user(
            self.request.user,
            resource=org,
        )
        return context


# Member Views
class ListOrganizationMembers(FilterContextMixin, OrganizationMixin, ListView):
    template_name = "organizations/member_list.html"
    context_object_name = "members"
    admin_only = False

    filterset_class = OrganizationTeamMemberListFilterSet
    strict = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.get_filterset(
            organization=self.get_organization(),
        )
        context[self.get_context_object_name()] = self.get_filtered_queryset()
        return context

    def get_queryset(self):
        return AdminPermission.members(obj=self.get_organization(), user=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            "organization_members",
            args=[self.get_organization().slug],
        )


# Team Views
class ListOrganizationTeams(FilterContextMixin, OrganizationTeamView, ListView):
    template_name = "organizations/team_list.html"
    context_object_name = "teams"
    admin_only = False

    filterset_class = OrganizationTeamListFilterSet
    strict = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()

        # TODO the team queryset, used through ``get_queryset()`` defines
        # sorting. Sorting should only happen in the filterset, so it can be
        # controlled in the UI.
        context["filter"] = self.get_filterset(
            organization=org,
        )
        context[self.get_context_object_name()] = self.get_filtered_queryset()
        return context


class ListOrganizationTeamMembers(OrganizationTeamMemberView, ListView):
    template_name = "organizations/team_detail.html"
    context_object_name = "team_members"
    admin_only = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = self.get_team().projects.all()
        return context


class RedirectRedeemTeamInvitation(CheckOrganizationsEnabled, GenericView):
    """Redirect invitation links to the new view."""

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse("invitations_redeem", args=[kwargs["hash"]]))
