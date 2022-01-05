"""Project views for authenticated users."""

import structlog

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView
from formtools.wizard.views import SessionWizardView
from vanilla import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    GenericModelView,
    GenericView,
    UpdateView,
)

from readthedocs.analytics.models import PageView
from readthedocs.builds.forms import RegexAutomationRuleForm, VersionForm
from readthedocs.builds.models import (
    AutomationRuleMatch,
    RegexAutomationRule,
    Version,
    VersionAutomationRule,
)
from readthedocs.core.history import UpdateChangeReasonPostView
from readthedocs.core.mixins import ListViewWithForm, PrivateViewMixin
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.integrations.models import HttpExchange, Integration
from readthedocs.oauth.services import registry
from readthedocs.oauth.tasks import attach_webhook
from readthedocs.oauth.utils import update_webhook
from readthedocs.projects import tasks
from readthedocs.projects.filters import ProjectListFilterSet
from readthedocs.projects.forms import (
    DomainForm,
    EmailHookForm,
    EnvironmentVariableForm,
    IntegrationForm,
    ProjectAdvancedForm,
    ProjectAdvertisingForm,
    ProjectBasicsForm,
    ProjectExtraForm,
    ProjectRelationshipForm,
    RedirectForm,
    TranslationForm,
    UpdateProjectForm,
    UserForm,
    WebHookForm,
)
from readthedocs.projects.models import (
    Domain,
    EmailHook,
    EnvironmentVariable,
    Project,
    ProjectRelationship,
    WebHook,
)
from readthedocs.projects.notifications import EmailConfirmNotification
from readthedocs.projects.utils import get_csv_file
from readthedocs.projects.views.base import ProjectAdminMixin
from readthedocs.projects.views.mixins import (
    ProjectImportMixin,
    ProjectRelationListMixin,
)
from readthedocs.search.models import SearchQuery

log = structlog.get_logger(__name__)


class ProjectDashboard(PrivateViewMixin, ListView):

    """Project dashboard."""

    model = Project
    template_name = 'projects/project_dashboard.html'

    # pylint: disable=arguments-differ
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Set the default search to search files instead of projects
        context['type'] = 'file'

        if settings.RTD_EXT_THEME_ENABLED:
            filter = ProjectListFilterSet(self.request.GET, queryset=self.get_queryset())
            context['filter'] = filter
            context['project_list'] = filter.qs
            # Alternatively, dynamically override super()-derived `project_list` context_data
            # context[self.get_context_object_name(filter.qs)] = filter.qs

        return context

    def validate_primary_email(self, user):
        """
        Sends a persistent error notification.

        Checks if the user has a primary email or if the primary email
        is verified or not. Sends a persistent error notification if
        either of the condition is False.
        """
        email_qs = user.emailaddress_set.filter(primary=True)
        email = email_qs.first()
        if not email or not email.verified:
            notification = EmailConfirmNotification(user=user, success=False)
            notification.send()

    def get_queryset(self):
        sort = self.request.GET.get('sort')
        if sort not in ['modified_date', '-modified_date', 'slug', '-slug']:
            sort = 'slug'
        return Project.objects.dashboard(self.request.user).order_by(sort)

    def get(self, request, *args, **kwargs):
        self.validate_primary_email(request.user)
        return super(ProjectDashboard, self).get(self, request, *args, **kwargs)


class ProjectMixin(PrivateViewMixin):

    """Common pieces for model views of Project."""

    model = Project
    lookup_url_kwarg = 'project_slug'
    lookup_field = 'slug'
    context_object_name = 'project'

    def get_queryset(self):
        return self.model.objects.for_admin_user(self.request.user)


class ProjectUpdate(ProjectMixin, UpdateView):

    form_class = UpdateProjectForm
    success_message = _('Project settings updated')
    template_name = 'projects/project_edit.html'

    def get_success_url(self):
        return reverse('projects_detail', args=[self.object.slug])


class ProjectAdvancedUpdate(ProjectMixin, UpdateView):

    form_class = ProjectAdvancedForm
    success_message = _('Project settings updated')
    template_name = 'projects/project_advanced.html'

    def get_success_url(self):
        return reverse('projects_detail', args=[self.object.slug])


class ProjectDelete(UpdateChangeReasonPostView, ProjectMixin, DeleteView):

    success_message = _('Project deleted')
    template_name = 'projects/project_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superproject'] = (
            self.object.subprojects.all().exists()
        )
        return context

    def get_success_url(self):
        return reverse('projects_dashboard')


class ProjectVersionMixin(ProjectAdminMixin, PrivateViewMixin):

    model = Version
    context_object_name = 'version'
    form_class = VersionForm
    lookup_url_kwarg = 'version_slug'
    lookup_field = 'slug'

    def get_success_url(self):
        return reverse(
            'project_version_list',
            kwargs={'project_slug': self.get_project().slug},
        )


class ProjectVersionEditMixin(ProjectVersionMixin):

    def get_queryset(self):
        return Version.internal.public(
            user=self.request.user,
            project=self.get_project(),
            only_active=False,
        )

    def get_form(self, data=None, files=None, **kwargs):
        # This overrides the method from `ProjectAdminMixin`,
        # since we don't have a project.
        return self.get_form_class()(data, files, **kwargs)

    def form_valid(self, form):
        version = form.save()
        if form.has_changed():
            if 'active' in form.changed_data and version.active is False:
                log.info('Removing files for version.', version_slug=version.slug)
                tasks.clean_project_resources(
                    version.project,
                    version,
                )
                version.built = False
                version.save()
        return HttpResponseRedirect(self.get_success_url())


class ProjectVersionCreate(ProjectVersionEditMixin, CreateView):

    template_name = 'projects/project_version_detail.html'


class ProjectVersionDetail(ProjectVersionEditMixin, UpdateView):

    template_name = 'projects/project_version_detail.html'


class ProjectVersionDeleteHTML(ProjectVersionMixin, GenericModelView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        version = self.get_object()
        if not version.active:
            version.built = False
            version.save()
            log.info('Removing files for version.', version_slug=version.slug)
            tasks.clean_project_resources(
                version.project,
                version,
            )
        else:
            return HttpResponseBadRequest(
                "Can't delete HTML for an active version.",
            )
        return HttpResponseRedirect(self.get_success_url())


class ImportWizardView(ProjectImportMixin, PrivateViewMixin, SessionWizardView):

    """
    Project import wizard.

    The get and post methods are overridden in order to save the initial_dict data
    per session (since it's per class).
    """

    form_list = [
        ('basics', ProjectBasicsForm),
        ('extra', ProjectExtraForm),
    ]
    condition_dict = {'extra': lambda self: self.is_advanced()}

    initial_dict_key = 'initial-data'

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

    def post(self, *args, **kwargs):  # pylint: disable=arguments-differ
        self._set_initial_dict()

        log.bind(user_username=request.user.username)

        if request.user.profile.banned:
            log.info('Rejecting project POST from shadowbanned user.')
            return HttpResponseRedirect(reverse('homepage'))

        # The storage is reset after everything is done.
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        """Get args to pass into form instantiation."""
        kwargs = {}
        kwargs['user'] = self.request.user
        if step == 'basics':
            kwargs['show_advanced'] = True
        return kwargs

    def get_template_names(self):
        """Return template names based on step name."""
        return 'projects/import_{}.html'.format(self.steps.current)

    def done(self, form_list, **kwargs):
        """
        Save form data as object instance.

        Don't save form data directly, instead bypass documentation building and
        other side effects for now, by signalling a save without commit. Then,
        finish by added the members to the project and saving.
        """
        form_data = self.get_all_cleaned_data()
        extra_fields = ProjectExtraForm.Meta.fields
        # expect the first form; manually wrap in a list in case it's a
        # View Object, as it is in Python 3.
        basics_form = list(form_list)[0]
        # Save the basics form to create the project instance, then alter
        # attributes directly from other forms
        project = basics_form.save()

        # Remove tags to avoid setting them in raw instead of using ``.add``
        tags = form_data.pop('tags', [])

        for field, value in list(form_data.items()):
            if field in extra_fields:
                setattr(project, field, value)
        project.save()

        self.finish_import_project(self.request, project, tags)

        return HttpResponseRedirect(
            reverse('projects_detail', args=[project.slug]),
        )

    def is_advanced(self):
        """Determine if the user selected the `show advanced` field."""
        data = self.get_cleaned_data_for_step('basics') or {}
        return data.get('advanced', True)


class ImportView(PrivateViewMixin, TemplateView):

    """
    On GET, show the source an import view, on POST, mock out a wizard.

    If we are accepting POST data, use the fields to seed the initial data in
    :py:class:`ImportWizardView`.  The import templates will redirect the form to
    `/dashboard/import`
    """

    template_name = 'projects/project_import.html'
    wizard_class = ImportWizardView

    def get(self, request, *args, **kwargs):
        """
        Display list of repositories to import.

        Adds a warning to the listing if any of the accounts connected for the
        user are not supported accounts.
        """
        deprecated_accounts = (
            SocialAccount.objects
            .filter(user=self.request.user)
            .exclude(
                provider__in=[
                    service.adapter.provider_id for service in registry
                ],
            )
        )  # yapf: disable
        for account in deprecated_accounts:
            provider_account = account.get_provider_account()
            messages.error(
                request,
                mark_safe((
                    _(
                        'There is a problem with your {service} account, '
                        'try reconnecting your account on your '
                        '<a href="{url}">connected services page</a>.',
                    ).format(
                        service=provider_account.get_brand()['name'],
                        url=reverse('socialaccount_connections'),
                    )
                )),  # yapf: disable
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        initial_data = {}
        initial_data['basics'] = {}
        for key in ['name', 'repo', 'repo_type', 'remote_repository', 'default_branch']:
            initial_data['basics'][key] = request.POST.get(key)
        initial_data['extra'] = {}
        for key in ['description', 'project_url']:
            initial_data['extra'][key] = request.POST.get(key)
        request.method = 'GET'
        return self.wizard_class.as_view(initial_dict=initial_data)(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_csrf_token'] = get_token(self.request)
        context['has_connected_accounts'] = SocialAccount.objects.filter(
            user=self.request.user,
        ).exists()
        return context


class ProjectRelationshipMixin(ProjectAdminMixin, PrivateViewMixin):

    model = ProjectRelationship
    form_class = ProjectRelationshipForm
    lookup_field = 'child__slug'
    lookup_url_kwarg = 'subproject_slug'

    def get_queryset(self):
        self.project = self.get_project()
        return self.model.objects.filter(parent=self.project)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['user'] = self.request.user
        return super().get_form(data, files, **kwargs)

    def get_success_url(self):
        return reverse('projects_subprojects', args=[self.get_project().slug])


class ProjectRelationshipList(ProjectRelationListMixin, ProjectRelationshipMixin, ListView):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['superproject'] = self.project.superprojects.first()
        return ctx


class ProjectRelationshipCreate(ProjectRelationshipMixin, CreateView):

    pass


class ProjectRelationshipUpdate(ProjectRelationshipMixin, UpdateView):

    pass


class ProjectRelationshipDelete(ProjectRelationshipMixin, DeleteView):

    http_method_names = ['post']


class ProjectUsersMixin(ProjectAdminMixin, PrivateViewMixin):

    form_class = UserForm

    def get_queryset(self):
        project = self.get_project()
        return project.users.all()

    def get_success_url(self):
        return reverse('projects_users', args=[self.get_project().slug])

    def _is_last_user(self):
        return self.get_queryset().count() <= 1


class ProjectUsersCreateList(ProjectUsersMixin, FormView):

    template_name = 'projects/project_users.html'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = self.get_queryset()
        context['is_last_user'] = self._is_last_user()
        return context


class ProjectUsersDelete(ProjectUsersMixin, GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        username = self.request.POST.get('username')
        user = get_object_or_404(
            self.get_queryset(),
            username=username,
        )
        if self._is_last_user():
            return HttpResponseBadRequest(_(f'{username} is the last owner, can\'t be removed'))

        project = self.get_project()
        project.users.remove(user)

        if user == request.user:
            return HttpResponseRedirect(reverse('projects_dashboard'))

        return HttpResponseRedirect(self.get_success_url())


class ProjectNotificationsMixin(ProjectAdminMixin, PrivateViewMixin):

    def get_success_url(self):
        return reverse(
            'projects_notifications',
            args=[self.get_project().slug],
        )


class ProjectNotifications(ProjectNotificationsMixin, TemplateView):

    """Project notification view and form view."""

    template_name = 'projects/project_notifications.html'
    email_form = EmailHookForm

    def get_email_form(self):
        project = self.get_project()
        return self.email_form(
            self.request.POST or None,
            project=project,
        )

    def post(self, request, *args, **kwargs):
        if 'email' in request.POST:
            email_form = self.get_email_form()
            if email_form.is_valid():
                email_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def _has_old_webhooks(self):
        """
        Check if the project has webhooks from the old implementation created.

        Webhooks from the old implementation don't have a custom payload.
        """
        project = self.get_project()
        return (
            project.webhook_notifications
            .filter(Q(payload__isnull=True) | Q(payload=''))
            .exists()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        project = self.get_project()
        emails = project.emailhook_notifications.all()
        context.update(
            {
                'email_form': self.get_email_form(),
                'emails': emails,
                'has_old_webhooks': self._has_old_webhooks(),
            },
        )
        return context


class ProjectNotificationsDelete(ProjectNotificationsMixin, GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        try:
            project.emailhook_notifications.get(
                email=request.POST.get('email'),
            ).delete()
        except EmailHook.DoesNotExist:
            try:
                project.webhook_notifications.get(
                    url=request.POST.get('email'),
                ).delete()
            except WebHook.DoesNotExist:
                raise Http404
        return HttpResponseRedirect(self.get_success_url())


class WebHookMixin(ProjectAdminMixin, PrivateViewMixin):

    model = WebHook
    lookup_url_kwarg = 'webhook_pk'
    form_class = WebHookForm

    def get_success_url(self):
        return reverse(
            'projects_webhooks',
            args=[self.get_project().slug],
        )


class WebHookList(WebHookMixin, ListView):

    pass


class WebHookCreate(WebHookMixin, CreateView):

    def get_success_url(self):
        return reverse(
            'projects_webhooks_edit',
            args=[self.get_project().slug, self.object.pk],
        )


class WebHookUpdate(WebHookMixin, UpdateView):

    def get_success_url(self):
        return reverse(
            'projects_webhooks_edit',
            args=[self.get_project().slug, self.object.pk],
        )


class WebHookDelete(WebHookMixin, DeleteView):

    http_method_names = ['post']


class WebHookExchangeDetail(WebHookMixin, DetailView):

    model = HttpExchange
    lookup_url_kwarg = 'webhook_exchange_pk'
    webhook_url_kwarg = 'webhook_pk'
    template_name = 'projects/webhook_exchange_detail.html'

    def get_queryset(self):
        return self.model.objects.filter(webhook=self.get_webhook())

    def get_webhook(self):
        return get_object_or_404(
            WebHook,
            pk=self.kwargs[self.webhook_url_kwarg],
            project=self.get_project(),
        )


class ProjectTranslationsMixin(ProjectAdminMixin, PrivateViewMixin):

    def get_success_url(self):
        return reverse(
            'projects_translations',
            args=[self.get_project().slug],
        )


class ProjectTranslationsListAndCreate(ProjectTranslationsMixin, FormView):

    """Project translations view and form view."""

    form_class = TranslationForm
    template_name = 'projects/project_translations.html'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['parent'] = self.get_project()
        kwargs['user'] = self.request.user
        return self.form_class(data, files, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context['lang_projects'] = project.translations.all()
        return context


class ProjectTranslationsDelete(ProjectTranslationsMixin, GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        translation = self.get_translation(kwargs['child_slug'])
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

    def get_success_url(self):
        return reverse(
            'projects_redirects',
            args=[self.get_project().slug],
        )


class ProjectRedirects(ProjectRedirectsMixin, FormView):

    form_class = RedirectForm
    template_name = 'projects/project_redirects.html'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context['redirects'] = project.redirects.all()
        return context


class ProjectRedirectsDelete(ProjectRedirectsMixin, GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        redirect = get_object_or_404(
            project.redirects,
            pk=request.POST.get('id_pk'),
        )
        if redirect.project == project:
            redirect.delete()
        else:
            raise Http404
        return HttpResponseRedirect(self.get_success_url())


class DomainMixin(ProjectAdminMixin, PrivateViewMixin):
    model = Domain
    form_class = DomainForm
    lookup_url_kwarg = 'domain_pk'

    def get_success_url(self):
        return reverse('projects_domains', args=[self.get_project().slug])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context['enabled'] = self._is_enabled(project)
        return context

    def _is_enabled(self, project):
        """Should we allow custom domains for this project?"""
        return True


class DomainListBase(DomainMixin, ListViewWithForm):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Get the default docs domain
        ctx['default_domain'] = (
            settings.PUBLIC_DOMAIN
            if settings.USE_SUBDOMAIN
            else settings.PRODUCTION_DOMAIN
        )

        return ctx


class DomainList(SettingsOverrideObject):

    _default_class = DomainListBase


class DomainCreateBase(DomainMixin, CreateView):

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        if self._is_enabled(project):
            return super().post(request, *args, **kwargs)
        return HttpResponse('Action not allowed', status=401)

    def get_success_url(self):
        """Redirect to the edit view so users can follow the next steps."""
        return reverse(
            'projects_domains_edit',
            args=[
                self.get_project().slug,
                self.object.pk,
            ],
        )


class DomainCreate(SettingsOverrideObject):

    _default_class = DomainCreateBase


class DomainUpdateBase(DomainMixin, UpdateView):

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        if self._is_enabled(project):
            return super().post(request, *args, **kwargs)
        return HttpResponse('Action not allowed', status=401)


class DomainUpdate(SettingsOverrideObject):

    _default_class = DomainUpdateBase


class DomainDelete(DomainMixin, DeleteView):

    pass


class IntegrationMixin(ProjectAdminMixin, PrivateViewMixin):

    """Project external service mixin for listing webhook objects."""

    model = Integration
    integration_url_field = 'integration_pk'
    form_class = IntegrationForm

    def get_queryset(self):
        return self.get_integration_queryset()

    def get_object(self):
        return self.get_integration()

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
        return reverse('projects_integrations', args=[self.get_project().slug])

    def get_template_names(self):
        if self.template_name:
            return self.template_name
        return 'projects/integration{}.html'.format(self.template_name_suffix)


class IntegrationList(IntegrationMixin, ListView):

    pass


class IntegrationCreate(IntegrationMixin, CreateView):

    def form_valid(self, form):
        self.object = form.save()
        if self.object.has_sync:
            attach_webhook(
                project_pk=self.get_project().pk,
                user_pk=self.request.user.pk,
                integration=self.object
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'projects_integrations_detail',
            kwargs={
                'project_slug': self.get_project().slug,
                'integration_pk': self.object.id,
            },
        )


class IntegrationDetail(IntegrationMixin, DetailView):

    # Some of the templates can be combined, we'll avoid duplicating templates
    SUFFIX_MAP = {
        Integration.GITHUB_WEBHOOK: 'webhook',
        Integration.GITLAB_WEBHOOK: 'webhook',
        Integration.BITBUCKET_WEBHOOK: 'webhook',
        Integration.API_WEBHOOK: 'generic_webhook',
    }

    def get_template_names(self):
        if self.template_name:
            return self.template_name
        integration_type = self.get_integration().integration_type
        suffix = self.SUFFIX_MAP.get(integration_type, integration_type)
        return (
            'projects/integration_{}{}.html'
            .format(suffix, self.template_name_suffix)
        )


class IntegrationDelete(IntegrationMixin, DeleteView):

    http_method_names = ['post']


class IntegrationExchangeDetail(IntegrationMixin, DetailView):

    model = HttpExchange
    lookup_url_kwarg = 'exchange_pk'
    template_name = 'projects/integration_exchange_detail.html'

    def get_queryset(self):
        return self.model.objects.filter(integrations=self.get_integration())

    def get_object(self):
        return DetailView.get_object(self)


class IntegrationWebhookSync(IntegrationMixin, GenericView):

    """
    Resync a project webhook.

    The signal will add a success/failure message on the request.
    """

    def post(self, request, *args, **kwargs):
        # pylint: disable=unused-argument
        if 'integration_pk' in kwargs:
            integration = self.get_integration()
            update_webhook(self.get_project(), integration, request=request)
        else:
            # This is a brute force form of the webhook sync, if a project has a
            # webhook or a remote repository object, the user should be using
            # the per-integration sync instead.
            attach_webhook(
                project_pk=self.get_project().pk,
                user_pk=request.user.pk,
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('projects_integrations', args=[self.get_project().slug])


class ProjectAdvertisingUpdate(PrivateViewMixin, UpdateView):

    model = Project
    form_class = ProjectAdvertisingForm
    success_message = _('Project has been opted out from advertisement support')
    template_name = 'projects/project_advertising.html'
    lookup_url_kwarg = 'project_slug'
    lookup_field = 'slug'

    def get_queryset(self):
        return self.model.objects.for_admin_user(self.request.user)

    def get_success_url(self):
        return reverse('projects_advertising', args=[self.object.slug])


class EnvironmentVariableMixin(ProjectAdminMixin, PrivateViewMixin):

    """Environment Variables to be added when building the Project."""

    model = EnvironmentVariable
    form_class = EnvironmentVariableForm
    lookup_url_kwarg = 'environmentvariable_pk'

    def get_success_url(self):
        return reverse(
            'projects_environmentvariables',
            args=[self.get_project().slug],
        )


class EnvironmentVariableList(EnvironmentVariableMixin, ListView):

    pass


class EnvironmentVariableCreate(EnvironmentVariableMixin, CreateView):

    pass


class EnvironmentVariableDelete(EnvironmentVariableMixin, DeleteView):

    http_method_names = ['post']


class AutomationRuleMixin(ProjectAdminMixin, PrivateViewMixin):

    model = VersionAutomationRule
    lookup_url_kwarg = 'automation_rule_pk'

    def get_success_url(self):
        return reverse(
            'projects_automation_rule_list',
            args=[self.get_project().slug],
        )


class AutomationRuleList(AutomationRuleMixin, ListView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['matches'] = (
            AutomationRuleMatch.objects
            .filter(rule__project=self.get_project())
        )
        return context


class AutomationRuleMove(AutomationRuleMixin, GenericModelView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        rule = self.get_object()
        steps = int(self.kwargs.get('steps', 0))
        rule.move(steps)
        return HttpResponseRedirect(
            reverse(
                'projects_automation_rule_list',
                args=[self.get_project().slug],
            )
        )


class AutomationRuleDelete(AutomationRuleMixin, DeleteView):

    http_method_names = ['post']


class RegexAutomationRuleMixin(AutomationRuleMixin):

    model = RegexAutomationRule
    form_class = RegexAutomationRuleForm


class RegexAutomationRuleCreate(RegexAutomationRuleMixin, CreateView):
    pass


class RegexAutomationRuleUpdate(RegexAutomationRuleMixin, UpdateView):
    pass


class SearchAnalyticsBase(ProjectAdminMixin, PrivateViewMixin, TemplateView):

    template_name = 'projects/projects_search_analytics.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get('download', False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        enabled = self._is_enabled(project)
        context.update({'enabled': enabled})
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
                qs.values('query')
                .annotate(count=Count('id'))
                .order_by('-count', 'query')
                .values_list('query', 'count', 'total_results')
            )

            # only show top 100 queries
            queries = qs[:100]

        context.update(
            {
                'queries': queries,
                'query_count_of_1_month': query_count_of_1_month,
            },
        )
        return context

    def _get_csv_data(self):
        """Generate raw csv data of search queries."""
        project = self.get_project()
        now = timezone.now().date()
        retention_limit = self._get_retention_days_limit(project)
        if retention_limit in [None, -1]:
            # Unlimited.
            days_ago = project.pub_date.date()
        else:
            days_ago = now - timezone.timedelta(days=retention_limit)

        values = [
            ('Created Date', 'created'),
            ('Query', 'query'),
            ('Total Results', 'total_results'),
        ]
        data = []
        if self._is_enabled(project):
            data = (
                SearchQuery.objects.filter(
                    project=project,
                    created__date__gte=days_ago,
                )
                .order_by('-created')
                .values_list(*[value for _, value in values])
            )

        filename = 'readthedocs_search_analytics_{project_slug}_{start}_{end}.csv'.format(
            project_slug=project.slug,
            start=timezone.datetime.strftime(days_ago, '%Y-%m-%d'),
            end=timezone.datetime.strftime(now, '%Y-%m-%d'),
        )

        csv_data = [
            [timezone.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'), *rest]
            for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def _get_retention_days_limit(self, project):
        """From how many days we need to show data for this project?"""
        return settings.RTD_ANALYTICS_DEFAULT_RETENTION_DAYS

    def _is_enabled(self, project):
        """Should we show search analytics for this project?"""
        return True


class SearchAnalytics(SettingsOverrideObject):
    _default_class = SearchAnalyticsBase


class TrafficAnalyticsViewBase(ProjectAdminMixin, PrivateViewMixin, TemplateView):

    template_name = 'projects/project_traffic_analytics.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get('download', False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        enabled = self._is_enabled(project)
        context.update({'enabled': enabled})
        if not enabled:
            return context

        # Count of views for top pages over the month
        top_pages = PageView.top_viewed_pages(project, limit=25)
        top_viewed_pages = list(zip(
            top_pages['pages'],
            top_pages['view_counts']
        ))

        # Aggregate pageviews grouped by day
        page_data = PageView.page_views_by_date(
            project_slug=project.slug,
        )

        context.update({
            'top_viewed_pages': top_viewed_pages,
            'page_data': page_data,
        })

        return context

    def _get_csv_data(self):
        project = self.get_project()
        now = timezone.now().date()
        retention_limit = self._get_retention_days_limit(project)
        if retention_limit in [None, -1]:
            # Unlimited.
            days_ago = project.pub_date.date()
        else:
            days_ago = now - timezone.timedelta(days=retention_limit)

        values = [
            ('Date', 'date'),
            ('Version', 'version__slug'),
            ('Path', 'path'),
            ('Views', 'view_count'),
        ]
        data = []
        if self._is_enabled(project):
            data = (
                PageView.objects.filter(
                    project=project,
                    date__gte=days_ago,
                )
                .order_by('-date')
                .values_list(*[value for _, value in values])
            )

        filename = 'readthedocs_traffic_analytics_{project_slug}_{start}_{end}.csv'.format(
            project_slug=project.slug,
            start=timezone.datetime.strftime(days_ago, '%Y-%m-%d'),
            end=timezone.datetime.strftime(now, '%Y-%m-%d'),
        )
        csv_data = [
            [timezone.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'), *rest]
            for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def _get_retention_days_limit(self, project):
        """From how many days we need to show data for this project?"""
        return settings.RTD_ANALYTICS_DEFAULT_RETENTION_DAYS

    def _is_enabled(self, project):
        """Should we show traffic analytics for this project?"""
        return True


class TrafficAnalyticsView(SettingsOverrideObject):
    _default_class = TrafficAnalyticsViewBase
