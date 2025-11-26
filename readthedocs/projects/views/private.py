"""Project views for authenticated users."""

from functools import lru_cache

import structlog
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView
from vanilla import CreateView
from vanilla import DetailView
from vanilla import FormView
from vanilla import GenericModelView
from vanilla import GenericView
from vanilla import UpdateView

from readthedocs.analytics.models import PageView
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.forms import RegexAutomationRuleForm
from readthedocs.builds.forms import VersionForm
from readthedocs.builds.models import AutomationRuleMatch
from readthedocs.builds.models import RegexAutomationRule
from readthedocs.builds.models import Version
from readthedocs.builds.models import VersionAutomationRule
from readthedocs.core.filters import FilterContextMixin
from readthedocs.core.history import UpdateChangeReasonPostView
from readthedocs.core.mixins import AsyncDeleteViewWithMessage
from readthedocs.core.mixins import DeleteViewWithMessage
from readthedocs.core.mixins import ListViewWithForm
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.notifications import MESSAGE_EMAIL_VALIDATION_PENDING
from readthedocs.core.permissions import AdminPermission
from readthedocs.integrations.models import HttpExchange
from readthedocs.integrations.models import Integration
from readthedocs.invitations.models import Invitation
from readthedocs.notifications.models import Notification
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.services import GitHubService
from readthedocs.oauth.tasks import attach_webhook
from readthedocs.oauth.utils import update_webhook
from readthedocs.projects.filters import ProjectListFilterSet
from readthedocs.projects.forms import AddonsConfigForm
from readthedocs.projects.forms import DomainForm
from readthedocs.projects.forms import EmailHookForm
from readthedocs.projects.forms import EnvironmentVariableForm
from readthedocs.projects.forms import IntegrationForm
from readthedocs.projects.forms import ProjectAdvertisingForm
from readthedocs.projects.forms import ProjectAutomaticForm
from readthedocs.projects.forms import ProjectBasicsForm
from readthedocs.projects.forms import ProjectConfigForm
from readthedocs.projects.forms import ProjectManualForm
from readthedocs.projects.forms import ProjectPullRequestForm
from readthedocs.projects.forms import ProjectRelationshipForm
from readthedocs.projects.forms import RedirectForm
from readthedocs.projects.forms import TranslationForm
from readthedocs.projects.forms import UpdateProjectForm
from readthedocs.projects.forms import UserForm
from readthedocs.projects.forms import WebHookForm
from readthedocs.projects.models import Domain
from readthedocs.projects.models import EmailHook
from readthedocs.projects.models import EnvironmentVariable
from readthedocs.projects.models import Project
from readthedocs.projects.models import ProjectRelationship
from readthedocs.projects.models import WebHook
from readthedocs.projects.notifications import MESSAGE_PROJECT_DEPRECATED_WEBHOOK
from readthedocs.projects.tasks.utils import clean_project_resources
from readthedocs.projects.utils import get_csv_file
from readthedocs.projects.views.base import ProjectAdminMixin
from readthedocs.projects.views.mixins import ProjectImportMixin
from readthedocs.projects.views.mixins import ProjectRelationListMixin
from readthedocs.search.models import SearchQuery
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.constants import TYPE_PAGEVIEW_ANALYTICS
from readthedocs.subscriptions.constants import TYPE_SEARCH_ANALYTICS
from readthedocs.subscriptions.products import get_feature


log = structlog.get_logger(__name__)


class ProjectDashboard(FilterContextMixin, PrivateViewMixin, ListView):
    """Project dashboard."""

    model = Project
    template_name = "projects/project_dashboard.html"
    filterset_class = ProjectListFilterSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Set the default search to search files instead of projects
        context["type"] = "file"

        context["filter"] = self.get_filterset()
        context["project_list"] = self.get_filtered_queryset()
        # Alternatively, dynamically override super()-derived `project_list` context_data
        # context[self.get_context_object_name(filter.qs)] = filter.qs

        template_name = None
        projects = AdminPermission.projects(user=self.request.user, admin=True)
        n_projects = projects.count()

        # We can't yet back down to another announcement as we don't have
        # the ability to evaluate local storage. Until we add the ability to
        # dynamically change the announcement, this is going to be the only
        # announcement shown.
        if n_projects == 0 or (
            n_projects < 3 and (timezone.now() - projects.first().pub_date).days < 7
        ):
            template_name = "example-projects.html"
        elif n_projects:
            template_name = "github-app.html"
        elif n_projects and not projects.filter(external_builds_enabled=True).exists():
            template_name = "pull-request-previews.html"
        elif n_projects and not projects.filter(addons__analytics_enabled=True).exists():
            template_name = "traffic-analytics.html"
        elif AdminPermission.organizations(
            user=self.request.user,
            owner=True,
        ).exists():
            template_name = "security-logs.html"

        if template_name:
            context["announcement"] = f"projects/partials/announcements/{template_name}"

        return context

    def validate_primary_email(self, user):
        """
        Sends a dismissable site notification to this user.

        Checks if the user has a primary email or if the primary email
        is verified or not. Sends a dismissable notification if
        either of the condition is False.
        """
        email_qs = user.emailaddress_set.filter(primary=True)
        email = email_qs.first()
        if not email or not email.verified:
            Notification.objects.add(
                attached_to=user,
                message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
                dismissable=True,
            )

    # NOTE: This method is called twice, on .org it doesn't matter,
    # as the queryset is straightforward, but on .com it
    # does some extra work that results in several queries.
    @lru_cache(maxsize=1)
    def get_queryset(self):
        return Project.objects.dashboard(self.request.user)

    def get(self, request, *args, **kwargs):
        self.validate_primary_email(request.user)
        return super().get(self, request, *args, **kwargs)


# SuccessMessageMixin is used when we are operating on the Project model itself,
# instead of a related model, where we use ProjectAdminMixin.
class ProjectMixin(SuccessMessageMixin, PrivateViewMixin):
    """Common pieces for model views of Project."""

    model = Project
    lookup_url_kwarg = "project_slug"
    lookup_field = "slug"
    context_object_name = "project"

    def get_queryset(self):
        return self.model.objects.for_admin_user(self.request.user)


class ProjectUpdate(ProjectMixin, UpdateView):
    form_class = UpdateProjectForm
    success_message = _("Project settings updated")
    template_name = "projects/project_edit.html"

    def get_success_url(self):
        return reverse("projects_detail", args=[self.object.slug])

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["user"] = self.request.user
        return super().get_form(data, files, **kwargs)


class ProjectDelete(UpdateChangeReasonPostView, ProjectMixin, AsyncDeleteViewWithMessage):
    success_message = _("Project queued for deletion")
    template_name = "projects/project_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_superproject"] = self.object.subprojects.all().exists()
        return context

    def get_success_url(self):
        return reverse("projects_dashboard")


class AddonsConfigUpdate(ProjectAdminMixin, PrivateViewMixin, CreateView, UpdateView):
    form_class = AddonsConfigForm
    success_message = _("Project addons updated")
    template_name = "projects/addons_form.html"

    def get_success_url(self):
        return reverse("projects_addons", args=[self.object.project.slug])


class ProjectVersionMixin(ProjectAdminMixin, PrivateViewMixin):
    model = Version
    context_object_name = "version"
    form_class = VersionForm
    lookup_url_kwarg = "version_slug"
    lookup_field = "slug"

    def get_success_url(self):
        # Redirect to the main version listing view instead of the version
        # admin listing. The version admin view, ``project_version_list``,
        # is an old view without filtering and splits up active/inactive
        # versions into two separate querysets.
        #
        # See: https://github.com/readthedocs/ext-theme/issues/288
        return reverse(
            "projects_detail",
            kwargs={"project_slug": self.get_project().slug},
        )


class ProjectVersionEditMixin(ProjectVersionMixin):
    def get_queryset(self):
        return (
            self.get_project()
            .versions(manager=INTERNAL)
            .public(
                user=self.request.user,
                only_active=False,
            )
        )

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())


class ProjectVersionCreate(ProjectVersionEditMixin, CreateView):
    success_message = _("Version created")
    template_name = "projects/project_version_detail.html"


class ProjectVersionDetail(ProjectVersionEditMixin, UpdateView):
    success_message = _("Version updated")
    template_name = "projects/project_version_detail.html"


class ProjectVersionDeleteHTML(ProjectVersionMixin, GenericModelView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        version = self.get_object()
        if not version.active:
            version.built = False
            version.save()
            log.info("Removing files for version.", version_slug=version.slug)
            clean_project_resources(
                version.project,
                version,
            )
        else:
            return HttpResponseBadRequest(
                "Can't delete HTML for an active version.",
            )
        return HttpResponseRedirect(self.get_success_url())


def show_config_step(wizard):
    """
    Decide whether or not show the config step on "Add project" wizard.

    If the `.readthedocs.yaml` file already exist in the default branch, we
    don't show this step.
    """

    # Try to get the cleaned data from the "basics" step only if
    # we are in a step after it, otherwise, return True since we don't
    # have the data yet, and django-forms calls this function multiple times.
    basics_step = "basics"
    cleaned_data = wizard.get_cleaned_data_for_step(basics_step) or {}
    repo = cleaned_data.get("repo")
    remote_repository = cleaned_data.get("remote_repository")
    default_branch = cleaned_data.get("default_branch")

    if repo and default_branch and remote_repository and remote_repository.vcs_provider == GITHUB:
        # I don't know why `show_config_step` is called multiple times (at least 4).
        # This is a problem for us because we perform external calls here and add messages to the request.
        # Due to that, we are adding this instance variable to prevent this function to run multiple times.
        # Maybe related to https://github.com/jazzband/django-formtools/issues/134
        if hasattr(wizard, "_show_config_step_executed"):
            return False

        remote_repository_relations = (
            remote_repository.remote_repository_relations.filter(
                user=wizard.request.user,
                account__isnull=False,
            )
            .select_related("account", "user")
            .only("user", "account")
        )
        for relation in remote_repository_relations:
            service = GitHubService(relation.user, relation.account)
            session = service.session

            for yaml in [
                ".readthedocs.yaml",
                ".readthedocs.yml",
                "readthedocs.yaml",
                "readthedocs.yml",
            ]:
                try:
                    querystrings = f"?ref={default_branch}" if default_branch else ""
                    response = session.head(
                        f"https://api.github.com/repos/{remote_repository.full_name}/contents/{yaml}{querystrings}",
                        timeout=1,
                    )
                    if response.ok:
                        log.info(
                            "Read the Docs YAML file found for this repository.",
                            filename=yaml,
                        )
                        messages.success(
                            wizard.request,
                            _(
                                "We detected a configuration file in your repository and started your project's first build."
                            ),
                        )
                        wizard._show_config_step_executed = True
                        return False
                except Exception:
                    log.warning(
                        "Failed when hitting GitHub API to check for .readthedocs.yaml file.",
                        filename=yaml,
                    )
                    continue
    return True


class ImportWizardView(ProjectImportMixin, PrivateViewMixin, SessionWizardView):
    """
    Project import wizard.

    The get and post methods are overridden in order to save the initial_dict data
    per session (since it's per class).
    """

    initial_dict_key = "initial-data"
    condition_dict = {"config": show_config_step}
    form_list = [
        ("basics", ProjectBasicsForm),
        ("config", ProjectConfigForm),
    ]

    def get(self, *args, **kwargs):
        # The method from the parent should run first,
        # as the storage is initialized there.
        response = super().get(*args, **kwargs)
        self._set_initial_dict()
        return response

    def _set_initial_dict(self):
        """Set or restore the initial_dict from the session."""
        if self.initial_dict:
            self.storage.data[self.initial_dict_key] = self.initial_dict
        else:
            self.initial_dict = self.storage.data.get(self.initial_dict_key, {})

    def post(self, *args, **kwargs):
        self._set_initial_dict()

        structlog.contextvars.bind_contextvars(user_username=self.request.user.username)

        if self.request.user.profile.banned:
            log.info("Rejecting project POST from shadowbanned user.")
            return HttpResponseRedirect(reverse("homepage"))

        # The storage is reset after everything is done.
        return super().post(*args, **kwargs)

    def get_form_kwargs(self, step=None):
        """Get args to pass into form instantiation."""
        kwargs = {}
        kwargs["user"] = self.request.user
        return kwargs

    def get_template_names(self):
        """Return template names based on step name."""
        return f"projects/import_{self.steps.current}.html"

    def done(self, form_list, **kwargs):
        """
        Save form data as object instance.

        Don't save form data directly, instead bypass documentation building and
        other side effects for now, by signalling a save without commit. Then,
        finish by added the members to the project and saving.
        """

        # We need to find the "basics" for here by iterating the list of bounded instance forms
        # because community and business have different steps -- it's not always the first one.
        basics_form = None
        for form in form_list:
            if isinstance(form, self.form_list.get("basics")):
                basics_form = form
                break

        # Save the basics form to create the project instance, then alter
        # attributes directly from other forms
        project = basics_form.save()

        self.finish_import_project(self.request, project)

        return HttpResponseRedirect(
            reverse("projects_detail", args=[project.slug]),
        )


class ImportView(PrivateViewMixin, TemplateView):
    """
    On GET, show the source an import view, on POST, mock out a wizard.

    If we are accepting POST data, use the fields to seed the initial data in
    :py:class:`ImportWizardView`.  The import templates will redirect the form to
    `/dashboard/import`
    """

    template_name = "projects/project_import.html"
    wizard_class = ImportWizardView

    def post(self, request, *args, **kwargs):
        initial_data = {}
        initial_data["basics"] = {}
        for key in ["name", "repo", "repo_type", "remote_repository", "default_branch"]:
            initial_data["basics"][key] = request.POST.get(key)
        initial_data["extra"] = {}
        for key in ["description", "project_url"]:
            initial_data["extra"][key] = request.POST.get(key)
        request.method = "GET"
        return self.wizard_class.as_view(initial_dict=initial_data)(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_csrf_token"] = get_token(self.request)

        context["allow_private_repos"] = settings.ALLOW_PRIVATE_REPOS
        context["form_automatic"] = ProjectAutomaticForm(user=self.request.user)
        context["form_manual"] = ProjectManualForm(user=self.request.user)

        # Provider list for simple lookup of connected services, used for
        # conditional content
        context["socialaccount_providers"] = self.request.user.socialaccount_set.values_list(
            "provider", flat=True
        )

        return context


class ProjectRelationshipMixin(ProjectAdminMixin, PrivateViewMixin):
    model = ProjectRelationship
    form_class = ProjectRelationshipForm
    lookup_field = "child__slug"
    lookup_url_kwarg = "subproject_slug"

    def get_queryset(self):
        self.project = self.get_project()
        return self.model.objects.filter(parent=self.project)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["user"] = self.request.user
        return super().get_form(data, files, **kwargs)

    def get_success_url(self):
        return reverse("projects_subprojects", args=[self.get_project().slug])


class ProjectRelationshipList(ProjectRelationListMixin, ProjectRelationshipMixin, ListView):
    pass


class ProjectRelationshipCreate(ProjectRelationshipMixin, CreateView):
    success_message = _("Subproject created")


class ProjectRelationshipUpdate(ProjectRelationshipMixin, UpdateView):
    success_message = _("Subproject updated")


class ProjectRelationshipDelete(ProjectRelationshipMixin, DeleteViewWithMessage):
    http_method_names = ["post"]
    success_message = _("Subproject deleted")


class ProjectUsersMixin(ProjectAdminMixin, PrivateViewMixin):
    form_class = UserForm

    def get_queryset(self):
        project = self.get_project()
        return project.users.all()

    def get_success_url(self):
        return reverse("projects_users", args=[self.get_project().slug])

    def _is_last_user(self):
        return self.get_queryset().count() <= 1

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["request"] = self.request
        return super().get_form(data, files, **kwargs)


class ProjectUsersList(ProjectUsersMixin, FormView):
    # We only use this to display the form in the list view.
    http_method_names = ["get"]
    template_name = "projects/project_users.html"

    def _get_invitations(self):
        return Invitation.objects.for_object(self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = self.get_queryset()
        context["invitations"] = self._get_invitations()
        context["is_last_user"] = self._is_last_user()
        return context


class ProjectUsersCreate(ProjectUsersMixin, CreateView):
    success_message = _("Invitation sent")
    template_name = "projects/project_users_form.html"


class ProjectUsersDelete(ProjectUsersMixin, GenericView):
    success_message = _("User deleted")
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        username = self.request.POST.get("username")
        user = get_object_or_404(
            self.get_queryset(),
            username=username,
        )
        if self._is_last_user():
            # NOTE: don't include user input in the message, since it's a security risk.
            return HttpResponseBadRequest(_("User is the last owner, can't be removed"))

        project = self.get_project()
        project.users.remove(user)

        messages.success(self.request, self.success_message)

        if user == request.user:
            return HttpResponseRedirect(reverse("projects_dashboard"))

        return HttpResponseRedirect(self.get_success_url())


class ProjectNotificationsMixin(ProjectAdminMixin, PrivateViewMixin):
    form_class = EmailHookForm

    def get_success_url(self):
        return reverse(
            "projects_notifications",
            args=[self.get_project().slug],
        )

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["project"] = self.get_project()
        return super().get_form(data, files, **kwargs)


class ProjectNotifications(ProjectNotificationsMixin, FormView):
    """Project notification view and form view."""

    # We only use this to display the form in the list view.
    http_method_names = ["get"]
    template_name = "projects/project_notifications.html"

    def _has_old_webhooks(self):
        """
        Check if the project has webhooks from the old implementation created.

        Webhooks from the old implementation don't have a custom payload.
        """
        project = self.get_project()
        return project.webhook_notifications.filter(
            Q(payload__isnull=True) | Q(payload="")
        ).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.get_project()
        emails = project.emailhook_notifications.all()
        context.update(
            {
                # TODO: delete once we no longer need the form in the list view.
                "email_form": context["form"],
                "emails": emails,
                "has_old_webhooks": self._has_old_webhooks(),
            },
        )
        return context


class ProjectEmailNotificationsCreate(ProjectNotificationsMixin, CreateView):
    template_name = "projects/project_notifications_form.html"
    success_message = _("Notification created")


class ProjectNotificationsDelete(ProjectNotificationsMixin, GenericView):
    http_method_names = ["post"]
    success_message = _("Notification deleted")

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        try:
            project.emailhook_notifications.get(
                email=request.POST.get("email"),
            ).delete()
        except EmailHook.DoesNotExist:
            try:
                project.webhook_notifications.get(
                    url=request.POST.get("email"),
                ).delete()
            except WebHook.DoesNotExist:
                raise Http404
        return HttpResponseRedirect(self.get_success_url())


class WebHookMixin(ProjectAdminMixin, PrivateViewMixin):
    model = WebHook
    lookup_url_kwarg = "webhook_pk"
    form_class = WebHookForm

    def get_success_url(self):
        return reverse(
            "projects_webhooks",
            args=[self.get_project().slug],
        )


class WebHookList(WebHookMixin, ListView):
    pass


class WebHookCreate(WebHookMixin, CreateView):
    success_message = _("Webhook created")

    def get_success_url(self):
        return reverse(
            "projects_webhooks_edit",
            args=[self.get_project().slug, self.object.pk],
        )


class WebHookUpdate(WebHookMixin, UpdateView):
    success_message = _("Webhook updated")

    def get_success_url(self):
        return reverse(
            "projects_webhooks_edit",
            args=[self.get_project().slug, self.object.pk],
        )


class WebHookDelete(WebHookMixin, DeleteViewWithMessage):
    success_message = _("Webhook deleted")
    http_method_names = ["post"]


class WebHookExchangeDetail(WebHookMixin, DetailView):
    model = HttpExchange
    lookup_url_kwarg = "webhook_exchange_pk"
    webhook_url_kwarg = "webhook_pk"
    template_name = "projects/webhook_exchange_detail.html"

    def get_queryset(self):
        # NOTE: We are explicitly using the id instead of the the object
        # to avoid a bug where the id is wrongly casted as an uuid.
        # https://code.djangoproject.com/ticket/33450
        return self.model.objects.filter(webhook__id=self.get_webhook().id)

    def get_webhook(self):
        return get_object_or_404(
            WebHook,
            pk=self.kwargs[self.webhook_url_kwarg],
            project=self.get_project(),
        )


class ProjectTranslationsMixin(ProjectAdminMixin, PrivateViewMixin):
    form_class = TranslationForm

    def get_success_url(self):
        return reverse(
            "projects_translations",
            args=[self.get_project().slug],
        )

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["parent"] = self.get_project()
        kwargs["user"] = self.request.user
        return self.form_class(data, files, **kwargs)


class ProjectTranslationsList(ProjectTranslationsMixin, FormView):
    """Project translations view and form view."""

    # We only use this to display the form in the list view.
    http_method_names = ["get"]
    template_name = "projects/project_translations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["lang_projects"] = project.translations.all()
        return context


class ProjectTranslationsCreate(ProjectTranslationsMixin, CreateView):
    success_message = _("Translation created")
    template_name = "projects/project_translations_form.html"


class ProjectTranslationsDelete(ProjectTranslationsMixin, GenericView):
    success_message = _("Translation deleted")
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        translation = self.get_translation(kwargs["child_slug"])
        project.translations.remove(translation)
        return HttpResponseRedirect(self.get_success_url())

    def get_translation(self, slug):
        project = self.get_project()
        translation = get_object_or_404(
            project.translations,
            slug=slug,
        )
        return translation


class ProjectRedirectsMixin(ProjectAdminMixin, PrivateViewMixin):
    """Project redirects view and form view."""

    form_class = RedirectForm
    template_name = "redirects/redirect_form.html"
    context_object_name = "redirect"
    lookup_url_kwarg = "redirect_pk"

    def get_success_url(self):
        return reverse(
            "projects_redirects",
            args=[self.get_project().slug],
        )

    def get_queryset(self):
        return self.get_project().redirects.all()


class ProjectRedirectsList(ProjectRedirectsMixin, ListView):
    template_name = "redirects/redirect_list.html"
    context_object_name = "redirects"


class ProjectRedirectsCreate(ProjectRedirectsMixin, CreateView):
    success_message = _("Redirect created")


class ProjectRedirectsUpdate(ProjectRedirectsMixin, UpdateView):
    success_message = _("Redirect updated")


class ProjectRedirectsInsert(ProjectRedirectsMixin, GenericModelView):
    """
    Insert a redirect in a specific position.

    This is done by changing the position of the redirect,
    after saving the redirect, all other positions are updated
    automatically.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        redirect = self.get_object()
        position = int(self.kwargs["position"])
        redirect.position = position
        redirect.save()
        return HttpResponseRedirect(
            reverse(
                "projects_redirects",
                args=[self.get_project().slug],
            )
        )


class ProjectRedirectsDelete(ProjectRedirectsMixin, DeleteViewWithMessage):
    http_method_names = ["post"]
    success_message = _("Redirect deleted")


class DomainMixin(ProjectAdminMixin, PrivateViewMixin):
    model = Domain
    form_class = DomainForm
    lookup_url_kwarg = "domain_pk"
    feature_type = TYPE_CNAME

    def get_success_url(self):
        return reverse("projects_domains", args=[self.get_project().slug])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["enabled"] = self._is_enabled(project)
        return context

    def _is_enabled(self, project):
        return bool(get_feature(project, feature_type=self.feature_type))


class DomainList(DomainMixin, ListViewWithForm):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Get the default docs domain
        ctx["default_domain"] = settings.PUBLIC_DOMAIN

        return ctx


class DomainCreate(DomainMixin, CreateView):
    success_message = _("Domain created")

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        if self._is_enabled(project) and not project.superproject:
            return super().post(request, *args, **kwargs)
        return HttpResponse("Action not allowed", status=401)

    def get_success_url(self):
        """Redirect to the edit view so users can follow the next steps."""
        return reverse(
            "projects_domains_edit",
            args=[
                self.get_project().slug,
                self.object.pk,
            ],
        )


class DomainUpdate(DomainMixin, UpdateView):
    success_message = _("Domain updated")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.restart_validation_process()
        return response

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        if self._is_enabled(project) and not project.superproject:
            return super().post(request, *args, **kwargs)
        return HttpResponse("Action not allowed", status=401)


class DomainDelete(DomainMixin, DeleteViewWithMessage):
    success_message = _("Domain deleted")


class IntegrationMixin(ProjectAdminMixin, PrivateViewMixin):
    """Project external service mixin for listing webhook objects."""

    model = Integration
    integration_url_field = "integration_pk"
    form_class = IntegrationForm

    def get_queryset(self):
        return self.get_integration_queryset()

    def get_object(self):
        integration = self.get_integration()
        # Don't allow an integration detail page if the integration subclass
        # does not support configuration
        if integration.is_remote_only:
            raise Http404
        return self.get_integration()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "object_list" in context:
            context["subclassed_object_list"] = context["object_list"].subclass()
        return context

    def get_integration_queryset(self):
        self.project = self.get_project()
        return self.model.objects.filter(project=self.project)

    def get_integration(self):
        """Return project integration determined by url kwarg."""
        if self.integration_url_field not in self.kwargs:
            return None
        return get_object_or_404(
            Integration,
            pk=self.kwargs[self.integration_url_field],
            project=self.get_project(),
        )

    def get_success_url(self):
        return reverse("projects_integrations", args=[self.get_project().slug])

    def get_template_names(self):
        if self.template_name:
            return self.template_name
        return "projects/integration{}.html".format(self.template_name_suffix)


class IntegrationList(IntegrationMixin, ListView):
    pass


class IntegrationCreate(IntegrationMixin, CreateView):
    success_message = _("Integration created")

    def form_valid(self, form):
        self.object = form.save()
        if self.object.has_sync:
            attach_webhook(
                project_pk=self.get_project().pk,
                integration=self.object,
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "projects_integrations_detail",
            kwargs={
                "project_slug": self.get_project().slug,
                "integration_pk": self.object.id,
            },
        )


class IntegrationDetail(IntegrationMixin, DetailView):
    template_name = "projects/integration_webhook_detail.html"


class IntegrationDelete(IntegrationMixin, DeleteViewWithMessage):
    success_message = _("Integration deleted")
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        # Dismiss notification about removing the GitHub webhook.
        project = self.get_project()
        if (
            project.is_github_app_project
            and not project.integrations.filter(
                integration_type=Integration.GITHUB_WEBHOOK
            ).exists()
        ):
            Notification.objects.cancel(
                attached_to=project,
                message_id=MESSAGE_PROJECT_DEPRECATED_WEBHOOK,
            )
        return resp


class IntegrationExchangeDetail(IntegrationMixin, DetailView):
    model = HttpExchange
    lookup_url_kwarg = "exchange_pk"
    template_name = "projects/integration_exchange_detail.html"

    def get_queryset(self):
        # NOTE: We are explicitly using the id instead of the the object
        # to avoid a bug where the id is wrongly casted as an uuid.
        # https://code.djangoproject.com/ticket/33450
        return self.model.objects.filter(integrations__id=self.get_integration().id)

    def get_object(self):
        return DetailView.get_object(self)


class IntegrationWebhookSync(IntegrationMixin, GenericView):
    """
    Resync a project webhook.

    The signal will add a success/failure message on the request.
    """

    def post(self, request, *args, **kwargs):
        if "integration_pk" in kwargs:
            integration = self.get_integration()
            update_webhook(self.get_project(), integration, request=request)
        else:
            # This is a brute force form of the webhook sync, if a project has a
            # webhook or a remote repository object, the user should be using
            # the per-integration sync instead.
            attach_webhook(project_pk=self.get_project().pk)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("projects_integrations", args=[self.get_project().slug])


class ProjectAdvertisingUpdate(SuccessMessageMixin, PrivateViewMixin, UpdateView):
    model = Project
    form_class = ProjectAdvertisingForm
    success_message = _("Project has been opted out from advertisement support")
    template_name = "projects/project_advertising.html"
    lookup_url_kwarg = "project_slug"
    lookup_field = "slug"

    def get_queryset(self):
        return self.model.objects.for_admin_user(self.request.user)

    def get_success_url(self):
        return reverse("projects_advertising", args=[self.object.slug])


class EnvironmentVariableMixin(ProjectAdminMixin, PrivateViewMixin):
    """Environment variables to be added when building the Project."""

    model = EnvironmentVariable
    form_class = EnvironmentVariableForm
    lookup_url_kwarg = "environmentvariable_pk"

    def get_success_url(self):
        return reverse(
            "projects_environmentvariables",
            args=[self.get_project().slug],
        )


class EnvironmentVariableList(EnvironmentVariableMixin, ListView):
    pass


class EnvironmentVariableCreate(EnvironmentVariableMixin, CreateView):
    success_message = _("Environment variable created")


class EnvironmentVariableDelete(EnvironmentVariableMixin, DeleteViewWithMessage):
    success_message = _("Environment variable deleted")
    http_method_names = ["post"]


class AutomationRuleMixin(ProjectAdminMixin, PrivateViewMixin):
    model = VersionAutomationRule
    lookup_url_kwarg = "automation_rule_pk"

    def get_success_url(self):
        return reverse(
            "projects_automation_rule_list",
            args=[self.get_project().slug],
        )


class AutomationRuleList(AutomationRuleMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matches"] = AutomationRuleMatch.objects.filter(rule__project=self.get_project())
        return context


class AutomationRuleMove(AutomationRuleMixin, GenericModelView):
    success_message = _("Automation rule moved")
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        rule = self.get_object()
        steps = int(self.kwargs.get("steps", 0))
        rule.move(steps)
        return HttpResponseRedirect(
            reverse(
                "projects_automation_rule_list",
                args=[self.get_project().slug],
            )
        )


class AutomationRuleDelete(AutomationRuleMixin, DeleteViewWithMessage):
    success_message = _("Automation rule deleted")
    http_method_names = ["post"]


class RegexAutomationRuleMixin(AutomationRuleMixin):
    model = RegexAutomationRule
    form_class = RegexAutomationRuleForm


class RegexAutomationRuleCreate(RegexAutomationRuleMixin, CreateView):
    success_message = _("Automation rule created")


class RegexAutomationRuleUpdate(RegexAutomationRuleMixin, UpdateView):
    success_message = _("Automation rule updated")


class SearchAnalytics(ProjectAdminMixin, PrivateViewMixin, TemplateView):
    template_name = "projects/projects_search_analytics.html"
    http_method_names = ["get"]
    feature_type = TYPE_SEARCH_ANALYTICS

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get("download", False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        enabled = bool(self._get_feature(project))
        context.update({"enabled": enabled})
        if not enabled:
            return context

        # data for plotting the line-chart
        query_count_of_1_month = SearchQuery.generate_queries_count_of_one_month(
            project.slug,
        )

        queries = []
        qs = SearchQuery.objects.filter(project=project)
        if qs.exists():
            qs = (
                qs.values("query")
                .annotate(count=Count("id"))
                .order_by("-count", "query")
                .values_list("query", "count", "total_results")
            )

            # only show top 100 queries
            queries = qs[:100]

        context.update(
            {
                "queries": queries,
                "query_count_of_1_month": query_count_of_1_month,
            },
        )
        return context

    def _get_csv_data(self):
        """Generate raw csv data of search queries."""
        project = self.get_project()
        now = timezone.now().date()
        feature = self._get_feature(project)
        if not feature:
            raise Http404
        if feature.unlimited:
            days_ago = project.pub_date.date()
        else:
            days_ago = now - timezone.timedelta(days=feature.value)

        values = [
            ("Created Date", "created"),
            ("Query", "query"),
            ("Total Results", "total_results"),
        ]
        data = (
            SearchQuery.objects.filter(
                project=project,
                created__date__gte=days_ago,
            )
            .order_by("-created")
            .values_list(*[value for _, value in values])
        )

        filename = "readthedocs_search_analytics_{project_slug}_{start}_{end}.csv".format(
            project_slug=project.slug,
            start=timezone.datetime.strftime(days_ago, "%Y-%m-%d"),
            end=timezone.datetime.strftime(now, "%Y-%m-%d"),
        )

        csv_data = [
            [timezone.datetime.strftime(date, "%Y-%m-%d %H:%M:%S"), *rest] for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def _get_feature(self, project):
        return get_feature(project, feature_type=self.feature_type)


class TrafficAnalyticsView(ProjectAdminMixin, PrivateViewMixin, TemplateView):
    template_name = "projects/project_traffic_analytics.html"
    http_method_names = ["get"]
    feature_type = TYPE_PAGEVIEW_ANALYTICS

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get("download", False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        enabled = bool(self._get_feature(project))
        context.update({"enabled": enabled})
        if not enabled:
            return context

        # Count of views for top pages over the month
        top_pages_200 = PageView.top_viewed_pages(project, limit=25)
        top_pages_404 = PageView.top_viewed_pages(
            project,
            limit=25,
            status=404,
            per_version=True,
        )

        # Aggregate pageviews grouped by day
        page_data = PageView.page_views_by_date(
            project_slug=project.slug,
        )

        context.update(
            {
                "top_pages_200": top_pages_200,
                "page_data": page_data,
                "top_pages_404": top_pages_404,
            }
        )

        return context

    def _get_csv_data(self):
        project = self.get_project()
        now = timezone.now().date()
        feature = self._get_feature(project)
        if not feature:
            raise Http404
        if feature.unlimited:
            days_ago = project.pub_date.date()
        else:
            days_ago = now - timezone.timedelta(days=feature.value)

        values = [
            ("Date", "date"),
            ("Version", "version__slug"),
            ("Path", "path"),
            ("Views", "view_count"),
        ]
        data = (
            PageView.objects.filter(
                project=project,
                date__gte=days_ago,
                status=200,
            )
            .order_by("-date")
            .values_list(*[value for _, value in values])
        )

        filename = "readthedocs_traffic_analytics_{project_slug}_{start}_{end}.csv".format(
            project_slug=project.slug,
            start=timezone.datetime.strftime(days_ago, "%Y-%m-%d"),
            end=timezone.datetime.strftime(now, "%Y-%m-%d"),
        )
        csv_data = [
            [timezone.datetime.strftime(date, "%Y-%m-%d %H:%M:%S"), *rest] for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def _get_feature(self, project):
        return get_feature(project, feature_type=self.feature_type)


class ProjectPullRequestsUpdate(SuccessMessageMixin, PrivateViewMixin, UpdateView):
    model = Project
    form_class = ProjectPullRequestForm
    success_message = _("Pull request settings have been updated")
    template_name = "projects/pull_requests_form.html"
    lookup_url_kwarg = "project_slug"
    lookup_field = "slug"

    def get_queryset(self):
        return self.model.objects.for_admin_user(self.request.user)

    def get_success_url(self):
        return reverse("projects_pull_requests", args=[self.object.slug])
