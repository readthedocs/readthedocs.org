from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from vanilla import CreateView, DeleteView, ListView, UpdateView

from readthedocs.organizations.forms import OrganizationTeamProjectForm

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


# Owners
class EditOrganizationOwners(OrganizationOwnerView, ListView):
    template_name = 'organizations/admin/owners_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(data=None, files=None)
        return context


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
