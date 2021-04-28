import logging

from django.db.models import F
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from formtools.wizard.views import SessionWizardView
from vanilla import CreateView, DetailView, GenericModelView, ListView

from readthedocs.organizations.forms import (
    OrganizationForm,
    OrganizationSignupForm,
)
from readthedocs.organizations.models import (
    Organization,
    OrganizationOwner,
    Team,
    TeamMember,
)
from readthedocs.projects.models import Project

from ...corporate.mixins import PricingMixin
from .base import (
    OrganizationMixin,
    OrganizationTeamMemberView,
    OrganizationTeamView,
    OrganizationView,
)

log = logging.getLogger(__name__)


# Organization
class ListOrganization(OrganizationView, ListView):
    template_name = 'organizations/organization_list.html'
    admin_only = False

    def get_queryset(self):
        return Organization.objects.for_user(user=self.request.user)


class CreateOrganizationSignup(OrganizationView, CreateView):
    template_name = 'organizations/organization_create.html'
    form_class = OrganizationSignupForm

    def get_form(self, data=None, files=None, **kwargs):
        """Add request user as default billing address email."""
        kwargs['initial'] = {'email': self.request.user.email}
        kwargs['user'] = self.request.user
        return super().get_form(data=data, files=files, **kwargs)

    def get_success_url(self):
        """
        Redirect to Organization's Detail page.

        .. note::

            This method is override here from
            ``OrganizationView.get_success_url`` because that method
            redirects to Organization's Edit page.
        """
        return reverse_lazy(
            'organization_detail',
            args=[self.object.slug],
        )


class DetailOrganization(OrganizationView, DetailView):
    template_name = 'organizations/organization_detail.html'
    admin_only = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()
        context['projects'] = (Project.objects
                               .for_user(self.request.user)
                               .filter(organizations=org)
                               .all())
        context['teams'] = (Team.objects
                            .member(
                                self.request.user,
                                organization=org,
                            )
                            .all())
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


class UpdateOrganizationTeamMember(GenericModelView):
    model = TeamMember

    def get_object(self):
        return self.get_queryset().filter(
            invite__hash=self.kwargs['hash'],
            invite__count__lte=F('invite__total'),
        ).first()

    def get(self, request, *args, **kwargs):
        """
        Process GET from link click and let user in to team.

        If user is already logged in, link the team member to that account. If
        the user is not logged in, and doesn't have an account, the user will be
        prompted to sign up.
        """
        member = self.object = self.get_object()
        if member is not None:
            if not request.user.is_authenticated:
                member.invite.count += 1
                member.invite.save()
                self.request.session.update({
                    'invite:allow_signup': True,
                    'invite:email': member.invite.email,
                    'invite': member.invite.pk,

                    # Auto-verify EmailAddress via django-allauth
                    'account_verified_email': member.invite.email,
                })
                return HttpResponseRedirect(reverse('account_signup'))

            # If use is logged in, try to set the request user on the
            # fetched team member. If the member already exists on the team,
            # just delete the current member. Finally, get rid of the
            # invite too.
            org_slug = member.team.organization.slug
            invite = member.invite

            queryset = TeamMember.objects.filter(
                team=invite.team,
                member=self.request.user,
            )
            if queryset.exists():
                member.delete()
            else:
                member.member = self.request.user
                member.save()
            invite.delete()
            return HttpResponseRedirect(
                reverse(
                    'organization_detail',
                    kwargs={'slug': org_slug},
                ),
            )

        return HttpResponseRedirect(reverse('homepage'))
