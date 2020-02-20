"""Project views for authenticated users."""

import csv
import logging

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, TemplateView, View
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

from readthedocs.builds.forms import RegexAutomationRuleForm, VersionForm
from readthedocs.builds.models import (
    RegexAutomationRule,
    Version,
    VersionAutomationRule,
)
from readthedocs.core.mixins import (
    ListViewWithForm,
    LoginRequiredMixin,
    PrivateViewMixin,
)
from readthedocs.core.utils import broadcast, trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.integrations.models import HttpExchange, Integration
from readthedocs.oauth.services import registry
from readthedocs.oauth.tasks import attach_webhook
from readthedocs.oauth.utils import update_webhook
from readthedocs.projects import tasks
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
    Feature,
    Project,
    ProjectRelationship,
    WebHook,
)
from readthedocs.projects.notifications import EmailConfirmNotification
from readthedocs.projects.utils import Echo
from readthedocs.projects.views.base import ProjectAdminMixin, ProjectSpamMixin
from readthedocs.projects.views.mixins import ProjectImportMixin
from readthedocs.search.models import SearchQuery

from ..tasks import retry_domain_verification

log = logging.getLogger(__name__)


class ProjectDashboard(PrivateViewMixin, ListView):

    """Project dashboard."""

    model = Project
    template_name = 'projects/project_dashboard.html'

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
        return Project.objects.dashboard(self.request.user)

    def get(self, request, *args, **kwargs):
        self.validate_primary_email(request.user)
        return super(ProjectDashboard, self).get(self, request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        return context


class ProjectMixin(PrivateViewMixin):

    """Common pieces for model views of Project."""

    model = Project
    lookup_url_kwarg = 'project_slug'
    lookup_field = 'slug'
    context_object_name = 'project'

    def get_queryset(self):
        return self.model.objects.for_admin_user(self.request.user)


class ProjectUpdate(ProjectSpamMixin, ProjectMixin, UpdateView):

    form_class = UpdateProjectForm
    success_message = _('Project settings updated')
    template_name = 'projects/project_edit.html'

    def get_success_url(self):
        return reverse('projects_detail', args=[self.object.slug])


class ProjectAdvancedUpdate(ProjectSpamMixin, ProjectMixin, UpdateView):

    form_class = ProjectAdvancedForm
    success_message = _('Project settings updated')
    template_name = 'projects/project_advanced.html'

    def get_success_url(self):
        return reverse('projects_detail', args=[self.object.slug])


class ProjectDelete(ProjectMixin, DeleteView):

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


class ProjectVersionDetail(ProjectVersionMixin, UpdateView):

    template_name = 'projects/project_version_detail.html'

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
                log.info('Removing files for version %s', version.slug)
                broadcast(
                    type='app',
                    task=tasks.remove_dirs,
                    args=[version.get_artifact_paths()],
                )
                tasks.clean_project_resources(
                    version.project,
                    version,
                )
                version.built = False
                version.save()
        return HttpResponseRedirect(self.get_success_url())


class ProjectVersionDeleteHTML(ProjectVersionMixin, GenericModelView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        version = self.get_object()
        if not version.active:
            version.built = False
            version.save()
            broadcast(
                type='app',
                task=tasks.remove_dirs,
                args=[version.get_artifact_paths()],
            )
        else:
            return HttpResponseBadRequest(
                "Can't delete HTML for an active version.",
            )
        return HttpResponseRedirect(self.get_success_url())


class ImportWizardView(
        ProjectImportMixin, ProjectSpamMixin, PrivateViewMixin,
        SessionWizardView,
):

    """Project import wizard."""

    form_list = [
        ('basics', ProjectBasicsForm),
        ('extra', ProjectExtraForm),
    ]
    condition_dict = {'extra': lambda self: self.is_advanced()}

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


class ImportDemoView(PrivateViewMixin, ProjectImportMixin, View):

    """View to pass request on to import form to import demo project."""

    form_class = ProjectBasicsForm
    request = None
    args = None
    kwargs = None

    def get(self, request, *args, **kwargs):
        """Process link request as a form post to the project import form."""
        self.request = request
        self.args = args
        self.kwargs = kwargs

        data = self.get_form_data()
        project = Project.objects.for_admin_user(
            request.user,
        ).filter(repo=data['repo']).first()
        if project is not None:
            messages.success(
                request,
                _('The demo project is already imported!'),
            )
        else:
            kwargs = self.get_form_kwargs()
            form = self.form_class(data=data, **kwargs)
            if form.is_valid():
                project = form.save()
                project.save()
                self.trigger_initial_build(project, request.user)
                messages.success(
                    request,
                    _('Your demo project is currently being imported'),
                )
            else:
                messages.error(
                    request,
                    _('There was a problem adding the demo project'),
                )
                return HttpResponseRedirect(reverse('projects_dashboard'))
        return HttpResponseRedirect(
            reverse('projects_detail', args=[project.slug]),
        )

    def get_form_data(self):
        """Get form data to post to import form."""
        return {
            'name': '{}-demo'.format(self.request.user.username),
            'repo_type': 'git',
            'repo': 'https://github.com/readthedocs/template.git',
        }

    def get_form_kwargs(self):
        """Form kwargs passed in during instantiation."""
        return {'user': self.request.user}

    def trigger_initial_build(self, project, user):
        """
        Trigger initial build.

        Allow to override the behavior from outside.
        """
        return trigger_build(project)


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
        for key in ['name', 'repo', 'repo_type', 'remote_repository']:
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

    def form_valid(self, form):
        broadcast(
            type='app',
            task=tasks.symlink_subproject,
            args=[self.get_project().pk],
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('projects_subprojects', args=[self.get_project().slug])


class ProjectRelationshipList(ProjectRelationshipMixin, ListView):

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


class ProjectUsersCreateList(ProjectUsersMixin, FormView):

    template_name = 'projects/project_users.html'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = self.get_queryset()
        return context


class ProjectUsersDelete(ProjectUsersMixin, GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        username = self.request.POST.get('username')
        user = get_object_or_404(
            self.get_queryset(),
            username=username,
        )
        if user == request.user:
            raise Http404

        project = self.get_project()
        project.users.remove(user)

        return HttpResponseRedirect(self.get_success_url())


class ProjecNotificationsMixin(ProjectAdminMixin, PrivateViewMixin):

    def get_success_url(self):
        return reverse(
            'projects_notifications',
            args=[self.get_project().slug],
        )


class ProjectNotications(ProjecNotificationsMixin, TemplateView):

    """Project notification view and form view."""

    template_name = 'projects/project_notifications.html'
    email_form = EmailHookForm
    webhook_form = WebHookForm

    def get_email_form(self):
        project = self.get_project()
        return self.email_form(
            self.request.POST or None,
            project=project,
        )

    def get_webhook_form(self):
        project = self.get_project()
        return self.webhook_form(
            self.request.POST or None,
            project=project,
        )

    def post(self, request, *args, **kwargs):
        if 'email' in request.POST:
            email_form = self.get_email_form()
            if email_form.is_valid():
                email_form.save()
        elif 'url' in request.POST:
            webhook_form = self.get_webhook_form()
            if webhook_form.is_valid():
                webhook_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        project = self.get_project()
        emails = project.emailhook_notifications.all()
        urls = project.webhook_notifications.all()

        context.update(
            {
                'email_form': self.get_email_form(),
                'webhook_form': self.get_webhook_form(),
                'emails': emails,
                'urls': urls,
            },
        )
        return context


class ProjectNoticationsDelete(ProjecNotificationsMixin, GenericView):

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


class DomainList(DomainMixin, ListViewWithForm):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Get the default docs domain
        ctx['default_domain'] = settings.PUBLIC_DOMAIN if settings.USE_SUBDOMAIN else settings.PRODUCTION_DOMAIN  # noqa

        # Retry validation on all domains if applicable
        for domain in ctx['domain_list']:
            retry_domain_verification.delay(domain_pk=domain.pk)

        return ctx


class DomainCreateBase(DomainMixin, CreateView):
    pass


class DomainCreate(SettingsOverrideObject):
    _default_class = DomainCreateBase


class DomainUpdateBase(DomainMixin, UpdateView):
    pass


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


class EnvironmentVariableDetail(EnvironmentVariableMixin, DetailView):

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
    pass


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


@login_required
def search_analytics_view(request, project_slug):
    """View for search analytics."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )


class SearchAnalytics(ProjectAdminMixin, PrivateViewMixin, TemplateView):

    template_name = 'projects/projects_search_analytics.html'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get('download', False)
        if download_data:
            return self._search_analytics_csv_data()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()

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
                .values_list('query', 'count')
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

    def _search_analytics_csv_data(self):
        """Generate raw csv data of search queries."""
        project = self.get_project()
        now = timezone.now().date()
        last_3_month = now - timezone.timedelta(days=90)

        data = (
            SearchQuery.objects.filter(
                project=project,
                created__date__gte=last_3_month,
                created__date__lte=now,
            )
            .order_by('-created')
            .values_list('created', 'query')
        )

        file_name = '{project_slug}_from_{start}_to_{end}.csv'.format(
            project_slug=project.slug,
            start=timezone.datetime.strftime(last_3_month, '%Y-%m-%d'),
            end=timezone.datetime.strftime(now, '%Y-%m-%d'),
        )
        # remove any spaces in filename.
        file_name = '-'.join([text for text in file_name.split() if text])

        csv_data = (
            [timezone.datetime.strftime(time, '%Y-%m-%d %H:%M:%S'), query]
            for time, query in data
        )
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in csv_data),
            content_type="text/csv",
        )
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
