"""Views that don't require login."""
# pylint: disable=too-many-ancestors
import structlog
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView
from vanilla import DetailView, GenericView, ListView

from readthedocs.organizations.models import Team
from readthedocs.organizations.views.base import (
    OrganizationMixin,
    OrganizationTeamMemberView,
    OrganizationTeamView,
    OrganizationView,
)
from readthedocs.organizations.views.decorators import (
    redirect_if_organizations_disabled,
)
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)


class OrganizationTemplateView(TemplateView):

    """Wrapper around `TemplateView` to check if organizations are enabled."""

    @redirect_if_organizations_disabled
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# Organization

class DetailOrganization(OrganizationView, DetailView):

    """Display information about an organization."""

    template_name = 'organizations/organization_detail.html'
    admin_only = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()
        context['projects'] = (
            Project.objects
            .for_user(self.request.user)
            .filter(organizations=org)
            .all()
        )
        context['teams'] = (
            Team.objects
            .member(self.request.user, organization=org)
            .prefetch_related('organization')
            .all()
        )
        context['owners'] = org.owners.all()
        return context


# Member Views
class ListOrganizationMembers(OrganizationMixin, ListView):
    template_name = 'organizations/member_list.html'
    context_object_name = 'members'
    admin_only = False

    def get_queryset(self):
        return self.get_organization().members

    def get_success_url(self):
        return reverse_lazy(
            'organization_members',
            args=[self.get_organization().slug],
        )


# Team Views
class ListOrganizationTeams(OrganizationTeamView, ListView):
    template_name = 'organizations/team_list.html'
    context_object_name = 'teams'
    admin_only = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        context['owners'] = org.owners.all()
        return context


class ListOrganizationTeamMembers(OrganizationTeamMemberView, ListView):
    template_name = 'organizations/team_detail.html'
    context_object_name = 'team_members'
    admin_only = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.get_team().projects.all()
        return context


class RedirectRedeemTeamInvitation(GenericView):

    """Redirect invitation links to the new view."""

    @redirect_if_organizations_disabled
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    # pylint: disable=unused-argument
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(
            reverse("invitations_redeem", args=[kwargs["hash"]])
        )
