"""Project views for authenticated users."""

import csv
import logging

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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
from vanilla import CreateView, DeleteView, DetailView, GenericView, UpdateView

from readthedocs.builds.forms import VersionForm
from readthedocs.builds.models import Version
from readthedocs.core.mixins import ListViewWithForm, LoginRequiredMixin
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
from readthedocs.search.models import SearchQuery, PageView

from ..tasks import retry_domain_verification


log = logging.getLogger(__name__)


class PrivateViewMixin(LoginRequiredMixin):

    pass


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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


@login_required
def project_version_detail(request, project_slug, version_slug):
    """Project version detail page."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
    version = get_object_or_404(
        Version.internal.public(
            user=request.user,
            project=project,
            only_active=False,
        ),
        slug=version_slug,
    )

    form = VersionForm(request.POST or None, instance=version)

    if request.method == 'POST' and form.is_valid():
        version = form.save()
        if form.has_changed():
            if 'active' in form.changed_data and version.active is False:
                log.info('Removing files for version %s', version.slug)
                broadcast(
                    type='app',
                    task=tasks.remove_dirs,
                    args=[version.get_artifact_paths()],
                )
                version.built = False
                version.save()
        url = reverse('project_version_list', args=[project.slug])
        return HttpResponseRedirect(url)

    return render(
        request,
        'projects/project_version_detail.html',
        {'form': form, 'project': project, 'version': version},
    )


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


@login_required
def project_users(request, project_slug):
    """Project users view and form view."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )

    form = UserForm(data=request.POST or None, project=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_users', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    users = project.users.all()

    return render(
        request,
        'projects/project_users.html',
        {'form': form, 'project': project, 'users': users},
    )


@login_required
def project_users_delete(request, project_slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed('Only POST is allowed')
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
    user = get_object_or_404(
        User.objects.all(),
        username=request.POST.get('username'),
    )
    if user == request.user:
        raise Http404
    project.users.remove(user)
    project_dashboard = reverse('projects_users', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_notifications(request, project_slug):
    """Project notification view and form view."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )

    email_form = EmailHookForm(data=None, project=project)
    webhook_form = WebHookForm(data=None, project=project)

    if request.method == 'POST':
        if 'email' in request.POST.keys():
            email_form = EmailHookForm(data=request.POST, project=project)
            if email_form.is_valid():
                email_form.save()
        elif 'url' in request.POST.keys():
            webhook_form = WebHookForm(data=request.POST, project=project)
            if webhook_form.is_valid():
                webhook_form.save()

    emails = project.emailhook_notifications.all()
    urls = project.webhook_notifications.all()

    return render(
        request,
        'projects/project_notifications.html',
        {
            'email_form': email_form,
            'webhook_form': webhook_form,
            'project': project,
            'emails': emails,
            'urls': urls,
        },
    )


@login_required
def project_notifications_delete(request, project_slug):
    """Project notifications delete confirmation view."""
    if request.method != 'POST':
        return HttpResponseNotAllowed('Only POST is allowed')
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
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
    project_dashboard = reverse('projects_notifications', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_translations(request, project_slug):
    """Project translations view and form view."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
    form = TranslationForm(
        data=request.POST or None,
        parent=project,
        user=request.user,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse(
            'projects_translations',
            args=[project.slug],
        )
        return HttpResponseRedirect(project_dashboard)

    lang_projects = project.translations.all()

    return render(
        request,
        'projects/project_translations.html',
        {
            'form': form,
            'project': project,
            'lang_projects': lang_projects,
        },
    )


@login_required
def project_translations_delete(request, project_slug, child_slug):
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
    subproj = get_object_or_404(
        project.translations,
        slug=child_slug,
    )
    project.translations.remove(subproj)
    project_dashboard = reverse('projects_translations', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_redirects(request, project_slug):
    """Project redirects view and form view."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )

    form = RedirectForm(data=request.POST or None, project=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_redirects', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    redirects = project.redirects.all()

    return render(
        request,
        'projects/project_redirects.html',
        {'form': form, 'project': project, 'redirects': redirects},
    )


@login_required
def project_redirects_delete(request, project_slug):
    """Project redirect delete view."""
    if request.method != 'POST':
        return HttpResponseNotAllowed('Only POST is allowed')
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
    redirect = get_object_or_404(
        project.redirects,
        pk=request.POST.get('id_pk'),
    )
    if redirect.project == project:
        redirect.delete()
    else:
        raise Http404
    return HttpResponseRedirect(
        reverse('projects_redirects', args=[project.slug]),
    )


@login_required
def project_version_delete_html(request, project_slug, version_slug):
    """
    Project version 'delete' HTML.

    This marks a version as not built
    """
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )
    version = get_object_or_404(
        Version.internal.public(
            user=request.user,
            project=project,
            only_active=False,
        ),
        slug=version_slug,
    )

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
    return HttpResponseRedirect(
        reverse('project_version_list', kwargs={'project_slug': project_slug}),
    )


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


@login_required
def search_analytics_view(request, project_slug):
    """View for search analytics."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )

    if not project.has_feature(Feature.SEARCH_ANALYTICS):
        return render(
            request,
            'projects/projects_search_analytics.html',
            {
                'project': project,
                'show_analytics': False,
            }
        )

    download_data = request.GET.get('download', False)

    # if the user has requested to download all data
    # return csv file in response.
    if download_data:
        return _search_analytics_csv_data(request, project_slug)

    # data for plotting the line-chart
    query_count_of_1_month = SearchQuery.generate_queries_count_of_one_month(
        project_slug
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

    return render(
        request,
        'projects/projects_search_analytics.html',
        {
            'project': project,
            'queries': queries,
            'show_analytics': True,
            'query_count_of_1_month': query_count_of_1_month,
        }
    )


def _search_analytics_csv_data(request, project_slug):
    """Generate raw csv data of search queries."""
    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )

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
        project_slug=project_slug,
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


def page_views(request, project_slug):
    """View for page views."""

    project = get_object_or_404(
        Project.objects.for_admin_user(request.user),
        slug=project_slug,
    )

    top_viewed_pages = PageView.get_top_viewed_pages(project)
    top_viewed_pages_iter = zip(
        top_viewed_pages['pages'],
        top_viewed_pages['view_counts']
    )

    all_pages = PageView.objects.filter(project=project).values_list('path', flat=True)
    if all_pages.exists():
        all_pages = sorted(list(set(all_pages)))
        page_path = request.GET.get('page', all_pages[0])
    else:
        all_pages = []
        page_path = ''

    page_data = PageView.get_page_view_count_of_one_month(
        project_slug=project.slug,
        page_path=page_path
    )
    return render(
        request,
        'projects/project_page_views.html',
        {
            'project': project,
            'top_viewed_pages_iter': top_viewed_pages_iter,
            'page_data': page_data,
            'page_path': page_path,
            'all_pages': all_pages,
        },
    )
