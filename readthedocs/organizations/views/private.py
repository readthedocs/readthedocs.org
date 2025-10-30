"""Views that require login."""
# pylint: disable=too-many-ancestors

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from vanilla import CreateView
from vanilla import FormView
from vanilla import ListView
from vanilla import UpdateView

from readthedocs.audit.filters import OrganizationSecurityLogFilter
from readthedocs.audit.models import AuditLog
from readthedocs.core.filters import FilterContextMixin
from readthedocs.core.history import UpdateChangeReasonPostView
from readthedocs.core.mixins import AsyncDeleteViewWithMessage
from readthedocs.core.mixins import DeleteViewWithMessage
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.filters import OrganizationListFilterSet
from readthedocs.organizations.forms import OrganizationSignupForm
from readthedocs.organizations.forms import OrganizationTeamProjectForm
from readthedocs.organizations.models import Organization
from readthedocs.organizations.views.base import OrganizationMixin
from readthedocs.organizations.views.base import OrganizationOwnerView
from readthedocs.organizations.views.base import OrganizationTeamMemberView
from readthedocs.organizations.views.base import OrganizationTeamView
from readthedocs.organizations.views.base import OrganizationView
from readthedocs.projects.utils import get_csv_file
from readthedocs.subscriptions.constants import TYPE_AUDIT_LOGS
from readthedocs.subscriptions.products import get_feature


# Organization views
class CreateOrganizationSignup(PrivateViewMixin, OrganizationView, CreateView):
    """View to create an organization after the user has signed up."""

    template_name = "organizations/organization_create.html"
    form_class = OrganizationSignupForm

    def get_form(self, data=None, files=None, **kwargs):
        """Add request user as default billing address email."""
        kwargs["initial"] = {"email": self.request.user.email}
        kwargs["user"] = self.request.user
        return super().get_form(data=data, files=files, **kwargs)

    def get_success_url(self):
        """
        Redirect to Organization's Detail page.

        .. note::

            This method is overridden here from
            ``OrganizationView.get_success_url`` because that method
            redirects to Organization's Edit page.
        """
        return reverse_lazy(
            "organization_detail",
            args=[self.object.slug],
        )


class ListOrganization(FilterContextMixin, PrivateViewMixin, OrganizationView, ListView):
    template_name = "organizations/organization_list.html"
    admin_only = False

    filterset_class = OrganizationListFilterSet

    def get_queryset(self):
        return Organization.objects.for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.get_filterset()
        context["organization_list"] = self.get_filtered_queryset()
        return context


class ChooseOrganization(ListOrganization):
    template_name = "organizations/organization_choose.html"

    def get(self, request, *args, **kwargs):
        self.next_name = self.kwargs["next_name"]
        self.next_querystring = self.request.GET.get("next_querystring")

        # Check if user has exactly 1 organization and automatically redirect in this case
        organizations = self.get_queryset()
        if organizations.count() == 1:
            redirect_url = reverse(self.next_name, kwargs={"slug": organizations[0].slug})
            if self.next_querystring:
                redirect_url += "?" + urlencode(self.next_querystring)
            return redirect(redirect_url)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c["next_name"] = self.next_name
        c["next_querystring"] = self.next_querystring
        return c


class EditOrganization(
    PrivateViewMixin,
    UpdateChangeReasonPostView,
    OrganizationView,
    UpdateView,
):
    template_name = "organizations/admin/organization_edit.html"
    success_message = _("Organization updated")


class DeleteOrganization(
    PrivateViewMixin,
    UpdateChangeReasonPostView,
    OrganizationView,
    AsyncDeleteViewWithMessage,
):
    http_method_names = ["post"]
    success_message = _("Organization queued for deletion")

    def get_success_url(self):
        return reverse_lazy("organization_list")


# Owners views
class EditOrganizationOwners(PrivateViewMixin, OrganizationOwnerView, ListView):
    template_name = "organizations/admin/owners_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class()
        return context


class AddOrganizationOwner(PrivateViewMixin, OrganizationOwnerView, FormView):
    template_name = "organizations/admin/owners_edit.html"
    success_message = _("Invitation sent")

    def form_valid(self, form):
        # Manually calling to save, since this isn't a ModelFormView.
        form.save()
        return super().form_valid(form)


class DeleteOrganizationOwner(PrivateViewMixin, OrganizationOwnerView, DeleteViewWithMessage):
    success_message = _("Owner removed")
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if self._is_last_user():
            return HttpResponseBadRequest(_("User is the last owner, can't be removed"))
        return super().post(request, *args, **kwargs)


# Team views
class AddOrganizationTeam(PrivateViewMixin, OrganizationTeamView, CreateView):
    template_name = "organizations/team_create.html"
    success_message = _("Team added")


class DeleteOrganizationTeam(
    PrivateViewMixin,
    UpdateChangeReasonPostView,
    OrganizationTeamView,
    DeleteViewWithMessage,
):
    http_method_names = ["post"]
    success_message = _("Team deleted")

    def get_success_url(self):
        return reverse_lazy(
            "organization_team_list",
            args=[self.get_organization().slug],
        )


class EditOrganizationTeam(PrivateViewMixin, OrganizationTeamView, UpdateView):
    template_name = "organizations/team_edit.html"
    success_message = _("Team updated")


class UpdateOrganizationTeamProject(PrivateViewMixin, OrganizationTeamView, UpdateView):
    form_class = OrganizationTeamProjectForm
    success_message = _("Team projects updated")
    template_name = "organizations/team_project_edit.html"


class AddOrganizationTeamMember(PrivateViewMixin, OrganizationTeamMemberView, FormView):
    template_name = "organizations/team_member_create.html"
    # No success message here, since it's set in the form.

    def form_valid(self, form):
        # Manually calling to save, since this isn't a ModelFormView.
        result = form.save()
        if isinstance(result, Invitation):
            messages.success(self.request, _("Invitation sent"))
        else:
            messages.success(self.request, _("Member added to team"))
        return super().form_valid(form)


class DeleteOrganizationTeamMember(
    PrivateViewMixin, OrganizationTeamMemberView, DeleteViewWithMessage
):
    success_message = _("Member removed from team")
    http_method_names = ["post"]


class OrganizationSecurityLog(PrivateViewMixin, OrganizationMixin, ListView):
    """Display security logs related to this organization."""

    model = AuditLog
    template_name = "organizations/security_log.html"
    feature_type = TYPE_AUDIT_LOGS

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get("download", False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def _get_csv_data(self):
        organization = self.get_organization()
        current_timezone = settings.TIME_ZONE
        values = [
            (f"Date ({current_timezone})", "created"),
            ("User", "log_user_username"),
            ("Project", "log_project_slug"),
            ("Organization", "log_organization_slug"),
            ("Action", "action"),
            ("Resource", "resource"),
            ("IP", "ip"),
            ("Browser", "browser"),
            ("Extra data", "data"),
        ]
        data = self.get_queryset().values_list(*[value for _, value in values])

        start_date = self._get_start_date()
        end_date = timezone.now().date()
        date_filter = self.filter.form.cleaned_data.get("date")
        if date_filter:
            start_date = date_filter.start or start_date
            end_date = date_filter.stop or end_date

        filename = "readthedocs_organization_security_logs_{organization}_{start}_{end}.csv".format(
            organization=organization.slug,
            start=timezone.datetime.strftime(start_date, "%Y-%m-%d"),
            end=timezone.datetime.strftime(end_date, "%Y-%m-%d"),
        )
        csv_data = [
            [timezone.datetime.strftime(date, "%Y-%m-%d %H:%M:%S"), *rest] for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def get_context_data(self, **kwargs):
        organization = self.get_organization()
        context = super().get_context_data(**kwargs)
        feature = self._get_feature(organization)
        context["enabled"] = bool(feature)
        context["days_limit"] = feature.value if feature else 0
        context["filter"] = self.filter
        context["AuditLog"] = AuditLog
        return context

    def _get_start_date(self):
        """Get the date to show logs from."""
        organization = self.get_organization()
        creation_date = organization.pub_date.date()
        feature = self._get_feature(organization)
        if feature.unlimited:
            return creation_date
        start_date = timezone.now().date() - timezone.timedelta(days=feature.value)
        # The max we can go back is to the creation of the organization.
        return max(start_date, creation_date)

    def _get_queryset(self):
        """Return the queryset without filters."""
        organization = self.get_organization()
        if not self._get_feature(organization):
            return AuditLog.objects.none()
        start_date = self._get_start_date()
        queryset = AuditLog.objects.filter(
            log_organization_id=organization.id,
            action__in=[action for action, _ in OrganizationSecurityLogFilter.allowed_actions],
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
        self.filter = OrganizationSecurityLogFilter(
            self.request.GET,
            queryset=queryset,
        )
        return self.filter.qs

    def _get_feature(self, organization):
        return get_feature(organization, self.feature_type)
