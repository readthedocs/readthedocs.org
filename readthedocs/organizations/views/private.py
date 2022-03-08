"""Views that require login."""
# pylint: disable=too-many-ancestors

from django.conf import settings
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from vanilla import CreateView, DeleteView, ListView, UpdateView

from readthedocs.audit.filters import OrganizationSecurityLogFilter
from readthedocs.audit.models import AuditLog
from readthedocs.core.history import UpdateChangeReasonPostView
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.organizations.forms import (
    OrganizationSignupForm,
    OrganizationTeamProjectForm,
)
from readthedocs.organizations.models import Organization
from readthedocs.organizations.views.base import (
    OrganizationMixin,
    OrganizationOwnerView,
    OrganizationTeamMemberView,
    OrganizationTeamView,
    OrganizationView,
)
from readthedocs.projects.utils import get_csv_file


# Organization views
class CreateOrganizationSignup(PrivateViewMixin, OrganizationView, CreateView):

    """View to create an organization after the user has signed up."""

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

            This method is overriden here from
            ``OrganizationView.get_success_url`` because that method
            redirects to Organization's Edit page.
        """
        return reverse_lazy(
            'organization_detail',
            args=[self.object.slug],
        )


class ListOrganization(PrivateViewMixin, OrganizationView, ListView):
    template_name = 'organizations/organization_list.html'
    admin_only = False

    def get_queryset(self):
        return Organization.objects.for_user(user=self.request.user)


class EditOrganization(
        PrivateViewMixin,
        UpdateChangeReasonPostView,
        OrganizationView,
        UpdateView,
):
    template_name = 'organizations/admin/organization_edit.html'


class DeleteOrganization(
        PrivateViewMixin,
        UpdateChangeReasonPostView,
        OrganizationView,
        DeleteView,
):
    template_name = 'organizations/admin/organization_delete.html'

    def get_success_url(self):
        return reverse_lazy('organization_list')


# Owners views
class EditOrganizationOwners(PrivateViewMixin, OrganizationOwnerView, ListView):
    template_name = 'organizations/admin/owners_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context


class AddOrganizationOwner(PrivateViewMixin, OrganizationOwnerView, CreateView):
    template_name = 'organizations/admin/owners_edit.html'
    success_message = _('Owner added')


class DeleteOrganizationOwner(PrivateViewMixin, OrganizationOwnerView, DeleteView):
    success_message = _('Owner removed')
    http_method_names = ['post']


# Team views
class AddOrganizationTeam(PrivateViewMixin, OrganizationTeamView, CreateView):
    template_name = 'organizations/team_create.html'
    success_message = _('Team added')


class DeleteOrganizationTeam(
        PrivateViewMixin,
        UpdateChangeReasonPostView,
        OrganizationTeamView,
        DeleteView,
):
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


class EditOrganizationTeam(PrivateViewMixin, OrganizationTeamView, UpdateView):
    template_name = 'organizations/team_edit.html'
    success_message = _('Team updated')


class UpdateOrganizationTeamProject(PrivateViewMixin, OrganizationTeamView, UpdateView):
    form_class = OrganizationTeamProjectForm
    success_message = _('Team projects updated')
    template_name = 'organizations/team_project_edit.html'


class AddOrganizationTeamMember(PrivateViewMixin, OrganizationTeamMemberView, CreateView):
    success_message = _('Member added to team')
    template_name = 'organizations/team_member_create.html'

    def form_valid(self, form):
        form.instance.send_add_notification(self.request)
        return super().form_valid(form)


class DeleteOrganizationTeamMember(PrivateViewMixin, OrganizationTeamMemberView, DeleteView):
    success_message = _('Member removed from team')
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        """Hack to show messages on delete."""
        # Linter doesn't like declaring `self.object` outside `__init__`.
        self.object = self.get_object()  # noqa
        if self.object.invite:
            self.object.invite.delete()
        resp = super().post(request, *args, **kwargs)
        messages.success(self.request, self.success_message)
        return resp


class OrganizationSecurityLogBase(PrivateViewMixin, OrganizationMixin, ListView):

    """Display security logs related to this organization."""

    model = AuditLog
    template_name = 'organizations/security_log.html'

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get('download', False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def _get_csv_data(self):
        organization = self.get_organization()
        current_timezone = settings.TIME_ZONE
        values = [
            (f'Date ({current_timezone})', 'created'),
            ('User', 'log_user_username'),
            ('Project', 'log_project_slug'),
            ('Organization', 'log_organization_slug'),
            ('Action', 'action'),
            ('Resource', 'resource'),
            ('IP', 'ip'),
            ('Browser', 'browser'),
        ]
        data = self.get_queryset().values_list(*[value for _, value in values])

        start_date = self._get_start_date()
        end_date = timezone.now().date()
        date_filter = self.filter.form.cleaned_data.get('date')
        if date_filter:
            start_date = date_filter.start or start_date
            end_date = date_filter.stop or end_date

        filename = 'readthedocs_organization_security_logs_{organization}_{start}_{end}.csv'.format(
            organization=organization.slug,
            start=timezone.datetime.strftime(start_date, '%Y-%m-%d'),
            end=timezone.datetime.strftime(end_date, '%Y-%m-%d'),
        )
        csv_data = [
            [timezone.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'), *rest]
            for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def get_context_data(self, **kwargs):
        organization = self.get_organization()
        context = super().get_context_data(**kwargs)
        context['enabled'] = self._is_enabled(organization)
        context['days_limit'] = self._get_retention_days_limit(organization)
        context['filter'] = self.filter
        context['AuditLog'] = AuditLog
        return context

    def _get_start_date(self):
        """Get the date to show logs from."""
        organization = self.get_organization()
        creation_date = organization.pub_date.date()
        retention_limit = self._get_retention_days_limit(organization)
        if retention_limit in [None, -1]:
            # Unlimited.
            return creation_date
        start_date = timezone.now().date() - timezone.timedelta(days=retention_limit)
        # The max we can go back is to the creation of the organization.
        return max(start_date, creation_date)

    def _get_queryset(self):
        """Return the queryset without filters."""
        organization = self.get_organization()
        if not self._is_enabled(organization):
            return AuditLog.objects.none()
        start_date = self._get_start_date()
        queryset = AuditLog.objects.filter(
            log_organization_id=organization.id,
            action__in=[
                AuditLog.AUTHN,
                AuditLog.AUTHN_FAILURE,
                AuditLog.PAGEVIEW,
                AuditLog.DOWNLOAD,
            ],
            created__gte=start_date,
        )
        return queryset

    def get_queryset(self):
        """
        Return the queryset with filters.

        If you want the original queryset without filters,
        use `_get_queryset`.
        """
        queryset = self._get_queryset()
        # Set filter on self, so we can use it in the context.
        # Without executing it twice.
        # pylint: disable=attribute-defined-outside-init
        self.filter = OrganizationSecurityLogFilter(
            self.request.GET,
            queryset=queryset,
        )
        return self.filter.qs

    def _get_retention_days_limit(self, organization):  # noqa
        """From how many days we need to show data for this project?"""
        return settings.RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS

    def _is_enabled(self, organization):  # noqa
        """Should we show audit logs for this organization?"""
        return True


class OrganizationSecurityLog(SettingsOverrideObject):
    _default_class = OrganizationSecurityLogBase
