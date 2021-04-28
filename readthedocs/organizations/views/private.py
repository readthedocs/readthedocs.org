from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from vanilla import CreateView, DeleteView, UpdateView, FormView

from readthedocs.organizations.forms import OrganizationTeamProjectForm
from readthedocsinc.acl.sso.forms import SSOIntegrationForm
from readthedocsinc.acl.sso.models import SSOIntegration
from readthedocsinc.core.mixins import ListViewWithForm

from .base import (
    OrganizationOwnerView,
    OrganizationTeamMemberView,
    OrganizationTeamView,
    OrganizationView,
)


# Organization
class EditOrganization(OrganizationView, UpdateView):
    template_name = 'organizations/admin/organization_edit.html'


class DeleteOrganization(OrganizationView, DeleteView):
    template_name = 'organizations/admin/organization_delete.html'

    def get_success_url(self):
        return reverse_lazy('organization_list')


class OrganizationSSO(OrganizationView, UpdateView):
    form_class = SSOIntegrationForm
    template_name = 'organizations/admin/sso_edit.html'

    def get_form(self, data=None, files=None, **kwargs):
        self.organization = self.object
        try:
            ssointegration = self.organization.ssointegration
            ssodomain = ssointegration.domains.first()
            initial = {
                'enabled': True,
                'provider': ssointegration.provider,
                'domain': ssodomain.domain if ssodomain else None,
            }
        except SSOIntegration.DoesNotExist:
            ssointegration = None
            initial = {}

        kwargs.update({
            'instance': ssointegration,
            'initial': initial,
        })
        cls = self.get_form_class()
        return cls(self.organization, data, files, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'organization_sso',
            args=[self.organization.slug],
        )


# Owners
class EditOrganizationOwners(OrganizationOwnerView, ListViewWithForm):
    template_name = 'organizations/admin/owners_edit.html'


class AddOrganizationOwner(OrganizationOwnerView, CreateView):
    template_name = 'organizations/admin/owners_edit.html'
    success_message = _('Owner added')


class DeleteOrganizationOwner(OrganizationOwnerView, DeleteView):
    template_name = 'organizations/admin/owners_edit.html'
    success_message = _('Owner removed')


# Team Views
class AddOrganizationTeam(OrganizationTeamView, CreateView):
    template_name = 'organizations/team_create.html'
    success_message = _('Team added')


class DeleteOrganizationTeam(OrganizationTeamView, DeleteView):
    template_name = 'organizations/team_delete.html'
    success_message = _('Team deleted')

    def post(self, request, *args, **kwargs):
        """Hack to show messages on delete."""
        resp = super().post(request, *args, **kwargs)
        messages.success(self.request, self.success_message)
        return resp

    def get_success_url(self):
        return reverse_lazy(
            'organization_team_list',
            args=[self.get_organization().slug],
        )


class EditOrganizationTeam(OrganizationTeamView, UpdateView):
    template_name = 'organizations/team_edit.html'
    success_message = _('Team updated')


# Team Project Views
class UpdateOrganizationTeamProject(OrganizationTeamView, UpdateView):
    form_class = OrganizationTeamProjectForm
    success_message = _('Team projects updated')
    template_name = 'organizations/team_project_edit.html'


# Team Views


class AddOrganizationTeamMember(OrganizationTeamMemberView, CreateView):
    success_message = _('Member added to team')
    template_name = 'organizations/team_member_create.html'

    def form_valid(self, form):
        form.instance.send_add_notification(self.request)
        return super().form_valid(form)


class DeleteOrganizationTeamMember(OrganizationTeamMemberView, DeleteView):
    success_message = _('Member removed from team')

    def post(self, request, *args, **kwargs):
        """Hack to show messages on delete."""
        self.object = self.get_object()
        if self.object.invite:
            self.object.invite.delete()
        resp = super().post(request, *args, **kwargs)
        messages.success(self.request, self.success_message)
        return resp
