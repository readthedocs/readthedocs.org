"""Views for creating, editing and viewing site-specific user profiles."""

from enum import StrEnum
from enum import auto

import structlog
from allauth.account.views import LoginView as AllAuthLoginView
from allauth.account.views import LogoutView as AllAuthLogoutView
from allauth.socialaccount import providers
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from vanilla import CreateView
from vanilla import DeleteView
from vanilla import DetailView
from vanilla import FormView
from vanilla import ListView
from vanilla import TemplateView
from vanilla import UpdateView

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.audit.filters import UserSecurityLogFilter
from readthedocs.audit.models import AuditLog
from readthedocs.core.forms import UserAdvertisingForm
from readthedocs.core.forms import UserDeleteForm
from readthedocs.core.forms import UserProfileForm
from readthedocs.core.history import set_change_reason
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.models import UserProfile
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.notifications.models import Notification
from readthedocs.oauth.migrate import get_installation_target_groups_for_user
from readthedocs.oauth.migrate import get_migrated_projects
from readthedocs.oauth.migrate import get_migration_targets
from readthedocs.oauth.migrate import get_old_app_link
from readthedocs.oauth.migrate import get_valid_projects_missing_migration
from readthedocs.oauth.migrate import has_projects_pending_migration
from readthedocs.oauth.migrate import migrate_project_to_github_app
from readthedocs.oauth.notifications import MESSAGE_OAUTH_DEPLOY_KEY_NOT_REMOVED
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_NOT_REMOVED
from readthedocs.oauth.utils import is_access_revoked
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project
from readthedocs.projects.utils import get_csv_file


log = structlog.get_logger(__name__)


class LoginViewBase(AllAuthLoginView):
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        last_login_method = self.request.COOKIES.get("last-login-method")
        context_data["last_login_method"] = last_login_method

        last_login_tab = "vcs"  # Default tab"
        if last_login_method == "email":
            last_login_tab = "email"
        if last_login_method in providers.registry.provider_map.keys():
            last_login_tab = "vcs"
        if last_login_method == "sso":
            last_login_tab = "sso"
        log.debug(
            "Login method.",
            last_login_method=last_login_method,
            last_login_tab=last_login_tab,
        )
        context_data["last_login_tab"] = last_login_tab
        return context_data


class LoginView(SettingsOverrideObject):
    _default_class = LoginViewBase


class LogoutViewBase(AllAuthLogoutView):
    pass


class LogoutView(SettingsOverrideObject):
    _default_class = LogoutViewBase


class ProfileEdit(PrivateViewMixin, UpdateView):
    """Edit the current user's profile."""

    model = UserProfile
    form_class = UserProfileForm
    template_name = "profiles/private/edit_profile.html"
    context_object_name = "profile"

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse(
            "profiles_profile_edit",
        )


class AccountDelete(PrivateViewMixin, SuccessMessageMixin, FormView):
    form_class = UserDeleteForm
    template_name = "profiles/private/delete_account.html"
    success_message = _("You have successfully deleted your account")

    def get_object(self):
        return User.objects.get(pk=self.request.user.pk)

    def form_valid(self, form):
        user = self.get_object()
        logout(self.request)
        set_change_reason(user, self.get_change_reason())
        user.delete()
        return super().form_valid(form)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["instance"] = self.get_object()
        kwargs["initial"] = {"username": ""}
        return super().get_form(data, files, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["projects_to_be_deleted"] = Project.objects.single_owner(user)
        context["organizations_to_be_deleted"] = Organization.objects.single_owner(user)
        return context

    def get_success_url(self):
        return reverse("homepage")

    def get_change_reason(self):
        klass = self.__class__.__name__
        return f"origin=form class={klass}"


class ProfileDetail(DetailView):
    model = User
    template_name = "profiles/public/profile_detail.html"
    lookup_field = "username"

    def get_object(self):
        """
        Get the user object.

        If organizations are enabled, show the profile to users in the same organization only.
        Otherwise, all users can see the profile of others.
        """
        user = super().get_object()
        if not settings.RTD_ALLOW_ORGANIZATIONS:
            return user

        request_user = self.request.user
        if not request_user.is_authenticated:
            raise Http404()

        # Always allow users to see their own profile.
        if request_user == user:
            return user

        # Don't allow members to see another user profile if they don't share the same team.
        for org in Organization.objects.for_user(request_user):
            if user in AdminPermission.members(obj=org, user=request_user):
                return user
        raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.get_object().profile
        return context


class AccountAdvertisingEdit(PrivateViewMixin, SuccessMessageMixin, UpdateView):
    model = UserProfile
    form_class = UserAdvertisingForm
    context_object_name = "profile"
    template_name = "profiles/private/advertising_profile.html"
    success_message = _("Updated your advertising preferences")

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse("account_advertising")


class TokenMixin(PrivateViewMixin):
    """User token to access APIv3."""

    model = Token
    lookup_url_kwarg = "token_pk"
    template_name = "profiles/private/token_list.html"

    def get_queryset(self):
        # NOTE: we are currently showing just one token since the DRF model has
        # a OneToOneField relation with User. Although, we plan to have multiple
        # scope-based tokens.
        return Token.objects.filter(user__in=[self.request.user])

    def get_success_url(self):
        return reverse("profiles_tokens")


class TokenListView(TokenMixin, ListView):
    pass


class TokenCreateView(TokenMixin, CreateView):
    """Simple view to generate a Token object for the logged in User."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        _, created = Token.objects.get_or_create(user=self.request.user)
        if created:
            messages.info(request, "API Token created successfully")
        return HttpResponseRedirect(self.get_success_url())


class TokenDeleteView(TokenMixin, DeleteView):
    """View to delete/revoke the current Token of the logged in User."""

    http_method_names = ["post"]

    def get_object(self, queryset=None):  # noqa
        return self.request.user.auth_token


class UserSecurityLogView(PrivateViewMixin, ListView):
    model = AuditLog
    template_name = "profiles/private/security_log.html"
    days_limit = settings.RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get("download", False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def _get_start_date(self):
        """Get the date to show logs from."""
        creation_date = self.request.user.date_joined.date()
        start_date = timezone.now().date() - timezone.timedelta(days=self.days_limit)
        # The max we can go back is to the creation of the user.
        return max(start_date, creation_date)

    def _get_csv_data(self):
        current_timezone = settings.TIME_ZONE
        values = [
            (f"Date ({current_timezone})", "created"),
            ("User", "log_user_username"),
            ("Project", "log_project_slug"),
            ("Organization", "log_organization_slug"),
            ("Action", "action"),
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

        filename = "readthedocs_user_security_logs_{username}_{start}_{end}.csv".format(
            username=self.request.user.username,
            start=timezone.datetime.strftime(start_date, "%Y-%m-%d"),
            end=timezone.datetime.strftime(end_date, "%Y-%m-%d"),
        )
        csv_data = [
            [timezone.datetime.strftime(date, "%Y-%m-%d %H:%M:%S"), *rest] for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["days_limit"] = self.days_limit
        context["filter"] = self.filter
        context["AuditLog"] = AuditLog
        return context

    def _get_queryset(self):
        """Return the queryset without filters."""
        user = self.request.user
        start_date = self._get_start_date()
        queryset = AuditLog.objects.filter(
            user=user,
            action__in=[action for action, _ in UserSecurityLogFilter.allowed_actions],
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
        self.filter = UserSecurityLogFilter(
            self.request.GET,
            queryset=queryset,
        )
        return self.filter.qs


class MigrationSteps(StrEnum):
    overview = auto()
    connect = auto()
    install = auto()
    migrate = auto()
    revoke = auto()
    disconnect = auto()


class MigrateToGitHubAppView(PrivateViewMixin, TemplateView):
    """
    View to help users migrate their account to the new GitHub App.

    This view will guide the user through the process of migrating their account
    and projects to the new GitHub App.

    A get request will show the overview of the migration process,
    and each step to follow. A post request will migrate a single project
    if the project slug is provided in the request, otherwise, it will migrate
    all projects that can be migrated.

    In case we weren't able to remove the webhook or SSH key from the old GitHub App,
    we create a notification for the user, so they can manually remove it.
    """

    template_name = "profiles/private/migrate_to_gh_app.html"

    def get(self, request, *args, **kwargs):
        if not self._get_old_github_accounts().exists():
            if self._get_new_github_account():
                # NOTE: TBD what to do when the user has already migrated his account,
                # but still has projects connected to the old integration.
                msg = _("You have already migrated your account to the new GitHub App.")
            else:
                msg = _("You don't have any GitHub account connected.")
            messages.info(request, msg)
            return HttpResponseRedirect(reverse("homepage"))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        step = self.request.GET.get("step", MigrationSteps.overview)
        if step not in MigrationSteps:
            step = MigrationSteps.overview
        context["step"] = step

        user = self.request.user

        context["step_connect_completed"] = self._has_new_accounts_for_old_accounts()
        context["migrated_projects"] = get_migrated_projects(user)
        context["old_application_link"] = get_old_app_link()
        context["step_revoke_completed"] = self._is_access_to_old_github_accounts_revoked()
        context["old_github_accounts"] = self._get_old_github_accounts()

        # These can take some time, so we only load them when needed.
        if step == MigrationSteps.install:
            context["installation_target_groups"] = get_installation_target_groups_for_user(user)
        if step == MigrationSteps.migrate:
            context["migration_targets"] = get_migration_targets(user)
        if step == MigrationSteps.revoke:
            context["has_projects_pending_migration"] = has_projects_pending_migration(user)

        return context

    def _is_access_to_old_github_accounts_revoked(self):
        for old_account in self._get_old_github_accounts():
            if not is_access_revoked(old_account):
                return False
        return True

    def _has_new_accounts_for_old_accounts(self):
        """
        Check if the user has connected his account to the new GitHub App.

        The new connected account must the same as the old one.
        """
        old_accounts_uid = self._get_old_github_accounts().values_list("uid", flat=True)
        number_of_new_accounts_for_old_accounts = (
            self.request.user.socialaccount_set.filter(
                provider=GitHubAppProvider.id,
            )
            .filter(uid__in=old_accounts_uid)
            .count()
        )
        return number_of_new_accounts_for_old_accounts == len(old_accounts_uid)

    def _get_new_github_account(self):
        return self.request.user.socialaccount_set.filter(provider=GitHubAppProvider.id).first()

    def _get_old_github_accounts(self):
        return self.request.user.socialaccount_set.filter(provider=GitHubProvider.id)

    def post(self, request, *args, **kwargs):
        project_slug = request.POST.get("project")
        if project_slug:
            projects = AdminPermission.projects(request.user, admin=True).filter(slug=project_slug)
        else:
            projects = get_valid_projects_missing_migration(request.user)

        migrated_projects_count = 0
        for project in projects:
            result = migrate_project_to_github_app(project=project, user=request.user)
            if not result.webhook_removed:
                Notification.objects.add(
                    message_id=MESSAGE_OAUTH_WEBHOOK_NOT_REMOVED,
                    attached_to=request.user,
                    dismissable=True,
                    format_values={
                        "repo_full_name": project.remote_repository.full_name,
                        "project_slug": project.slug,
                    },
                )
            if not result.ssh_key_removed:
                Notification.objects.add(
                    message_id=MESSAGE_OAUTH_DEPLOY_KEY_NOT_REMOVED,
                    attached_to=request.user,
                    dismissable=True,
                    format_values={
                        "repo_full_name": project.remote_repository.full_name,
                        "project_slug": project.slug,
                    },
                )
            migrated_projects_count += 1

        if migrated_projects_count > 0:
            messages.success(
                request, _(f"Successfully migrated {migrated_projects_count} project(s).")
            )
        else:
            messages.info(request, _("No projects were migrated."))

        return HttpResponseRedirect(reverse("migrate_to_github_app") + "?step=migrate")
