import logging
import shutil

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView, TemplateView
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib.formtools.wizard.views import SessionWizardView

from guardian.shortcuts import assign

from builds.models import Version
from builds.forms import AliasForm, VersionForm
from builds.filters import VersionFilter
from builds.models import VersionAlias
from core.utils import trigger_build
from oauth.models import GithubProject
from oauth import utils as oauth_utils
from projects.forms import (ProjectBackendForm, ProjectBasicsForm,
                            ProjectExtraForm, ProjectAdvancedForm,
                            UpdateProjectForm, SubprojectForm,
                            build_versions_form, UserForm, EmailHookForm,
                            TranslationForm, RedirectForm, WebHookForm)
from projects.models import Project, EmailHook, WebHook
from projects import constants

from bookmarks.models import Bookmark

log = logging.getLogger(__name__)


class ProjectDashboard(ListView):

    """
    A dashboard!  If you aint know what that means you aint need to.
    Essentially we show you an overview of your content.
    """
    model = Project
    template_name = 'projects/project_dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectDashboard, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Project.objects.dashboard(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ProjectDashboard, self).get_context_data(**kwargs)
        filter = VersionFilter(constants.IMPORTANT_VERSION_FILTERS, queryset=self.get_queryset())
        context['filter'] = filter

        bookmarks = Bookmark.objects.filter(user=self.request.user)

        if bookmarks.exists:
            context['bookmark_list'] = bookmarks[:3]
        else:
            bookmarks = None

        return context


@login_required
def project_manage(request, project_slug):
    """
    The management view for a project, where you will have links to edit
    the projects' configuration, edit the files associated with that
    project, etc.

    Now redirects to the normal /projects/<slug> view.
    """
    return HttpResponseRedirect(reverse('projects_detail',
                                        args=[project_slug]))


@login_required
def project_edit(request, project_slug):
    """
    Edit an existing project - depending on what type of project is being
    edited (created or imported) a different form will be displayed
    """
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    form_class = UpdateProjectForm

    form = form_class(instance=project, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Project settings updated'))
        project_dashboard = reverse('projects_detail', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_edit.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
    )


@login_required
def project_advanced(request, project_slug):
    """
    Edit an existing project - depending on what type of project is being
    edited (created or imported) a different form will be displayed
    """
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)
    form_class = ProjectAdvancedForm
    form = form_class(instance=project, data=request.POST or None, initial={
                      'num_minor': 2, 'num_major': 2, 'num_point': 2})

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Project settings updated'))
        project_dashboard = reverse('projects_detail', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_advanced.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
    )


@login_required
def project_versions(request, project_slug):
    """
    Shows the available versions and lets the user choose which ones he would
    like to have built.
    """
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    if not project.is_imported:
        raise Http404

    form_class = build_versions_form(project)

    form = form_class(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Project versions updated'))
        project_dashboard = reverse('projects_detail', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_versions.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
    )


@login_required
def project_version_detail(request, project_slug, version_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user), slug=project_slug)
    version = get_object_or_404(Version.objects.public(user=request.user, project=project), slug=version_slug)

    form = VersionForm(request.POST or None, instance=version)

    if request.method == 'POST' and form.is_valid():
        form.save()
        url = reverse('projects_versions', args=[project.slug])
        return HttpResponseRedirect(url)

    return render_to_response(
        'projects/project_version_detail.html',
        {'form': form, 'project': project, 'version': version},
        context_instance=RequestContext(request)
    )


@login_required
def project_delete(request, project_slug):
    """
    Make a project as deleted on POST, otherwise show a form asking for
    confirmation of delete.
    """
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    if request.method == 'POST':
        # Remove the repository checkout
        shutil.rmtree(project.doc_path, ignore_errors=True)
        # Delete the project and everything related to it
        project.delete()
        messages.success(request, _('Project deleted'))
        project_dashboard = reverse('projects_dashboard')
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_delete.html',
        {'project': project},
        context_instance=RequestContext(request)
    )


class ImportWizardView(SessionWizardView):
    '''Project import wizard'''

    form_list = [('basics', ProjectBasicsForm),
                 ('extra', ProjectExtraForm),
                 ('advanced', ProjectAdvancedForm)]
    condition_dict = {'extra': lambda self: self.is_advanced(),
                      'advanced': lambda self: self.is_advanced()}

    def get_form_kwargs(self, step):
        '''Get args to pass into form instantiation'''
        kwargs = {}
        kwargs['user'] = self.request.user
        if step == 'basics':
            kwargs['show_advanced'] = True
        if step == 'extra':
            extra_form = self.get_form_from_step('basics')
            project = extra_form.save(commit=False)
            kwargs['instance'] = project
        if step == 'advanced':
            adv_form = self.get_form_from_step('extra')
            project = adv_form.save(commit=False)
            kwargs['instance'] = project
        return kwargs

    def get_form_from_step(self, step):
        return self.form_list[step](
            data=self.get_cleaned_data_for_step(step),
            **self.get_form_kwargs(step)
        )

    def get_template_names(self):
        '''Return template names based on step name'''
        return 'projects/import_{0}.html'.format(self.steps.current, 'base')

    def done(self, form_list, **kwargs):
        '''Save form data as object instance

        Don't save form data directly, instead bypass documentation building and
        other side effects for now, by signalling a save without commit. Then,
        finish by added the members to the project and saving.
        '''
        # expect the first form
        basics_form = form_list[0]
        # Save the basics form to create the project instance, then alter
        # attributes directly from other forms
        project = basics_form.save()
        for form in form_list[1:]:
            for (field, value) in form.cleaned_data.items():
                setattr(project, field, value)
        project.save()
        trigger_build(project)
        return HttpResponseRedirect(reverse('projects_detail',
                                            args=[project.slug]))

    def is_advanced(self):
        '''Determine if the user selected the `show advanced` field'''
        data = self.get_cleaned_data_for_step('basics') or {}
        return data.get('advanced', True)


class ImportView(TemplateView):
    '''On GET, show the source select template, on POST, mock out a wizard

    If we are accepting POST data, use the fields to seed the initial data in
    :py:cls:`ImportWizardView`.  The import templates will redirect the form to
    `/dashboard/import`
    '''

    template_name = 'projects/project_import.html'
    wizard_class = ImportWizardView

    def post(self, request, *args, **kwargs):
        initial_data = {}
        initial_data['basics'] = {}
        for key in ['name', 'repo', 'repo_type']:
            initial_data['basics'][key] = request.POST.get(key)
        initial_data['extra'] = {}
        for key in ['description', 'project_url']:
            initial_data['extra'][key] = request.POST.get(key)
        request.method = 'GET'
        return self.wizard_class.as_view(initial_dict=initial_data)(request)


@login_required
def edit_alias(request, project_slug, id=None):
    proj = get_object_or_404(Project.objects.for_admin_user(request.user), slug=project_slug)
    if id:
        alias = proj.aliases.get(pk=id)
        form = AliasForm(instance=alias, data=request.POST or None)
    else:
        form = AliasForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        alias = form.save()
        return HttpResponseRedirect(alias.project.get_absolute_url())
    return render_to_response(
        'projects/alias_edit.html',
        {'form': form},
        context_instance=RequestContext(request)
    )


class AliasList(ListView):
    model = VersionAlias
    template_context_name = 'alias'
    template_name = 'projects/alias_list.html',

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AliasList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.project = get_object_or_404(Project.objects.for_admin_user(self.request.user), slug=self.kwargs.get('project_slug'))
        return self.project.aliases.all()


@login_required
def project_subprojects(request, project_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    form = SubprojectForm(data=request.POST or None, parent=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse(
            'projects_subprojects', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    subprojects = project.subprojects.all()

    return render_to_response(
        'projects/project_subprojects.html',
        {'form': form, 'project': project, 'subprojects': subprojects},
        context_instance=RequestContext(request)
    )


@login_required
def project_subprojects_delete(request, project_slug, child_slug):
    parent = get_object_or_404(Project.objects.for_admin_user(request.user), slug=project_slug)
    child = get_object_or_404(Project.objects.for_admin_user(request.user), slug=child_slug)
    parent.remove_subproject(child)
    return HttpResponseRedirect(reverse('projects_subprojects',
                                        args=[parent.slug]))


@login_required
def project_users(request, project_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    form = UserForm(data=request.POST or None, project=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_users', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    users = project.users.all()

    return render_to_response(
        'projects/project_users.html',
        {'form': form, 'project': project, 'users': users},
        context_instance=RequestContext(request)
    )


@login_required
def project_users_delete(request, project_slug):
    if request.method != 'POST':
        raise Http404
    project = get_object_or_404(Project.objects.for_admin_user(request.user), slug=project_slug)
    user = get_object_or_404(User.objects.all(), username=request.POST.get('username'))
    if user == request.user:
        raise Http404
    project.users.remove(user)
    project_dashboard = reverse('projects_users', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_notifications(request, project_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    email_form = EmailHookForm(data=request.POST or None, project=project)
    webhook_form = WebHookForm(data=request.POST or None, project=project)

    if request.method == 'POST':
        if email_form.is_valid():
            email_form.save()
        if webhook_form.is_valid():
            webhook_form.save()
        project_dashboard = reverse('projects_notifications',
                                    args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    emails = project.emailhook_notifications.all()
    urls = project.webhook_notifications.all()

    return render_to_response(
        'projects/project_notifications.html',
        {
            'email_form': email_form,
            'webhook_form': webhook_form,
            'project': project,
            'emails': emails,
            'urls': urls,
        },
        context_instance=RequestContext(request)
    )


@login_required
def project_notifications_delete(request, project_slug):
    if request.method != 'POST':
        raise Http404
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)
    try:
        project.emailhook_notifications.get(email=request.POST.get('email')).delete()
    except EmailHook.DoesNotExist:
        try:
            project.webhook_notifications.get(url=request.POST.get('email')).delete()
        except WebHook.DoesNotExist:
            raise Http404
    project_dashboard = reverse('projects_notifications', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_translations(request, project_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)
    form = TranslationForm(data=request.POST or None, parent=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_translations',
                                    args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    lang_projects = project.translations.all()

    return render_to_response(
        'projects/project_translations.html',
        {'form': form, 'project': project, 'lang_projects': lang_projects},
        context_instance=RequestContext(request)
    )


@login_required
def project_translations_delete(request, project_slug, child_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user), slug=project_slug)
    subproj = get_object_or_404(Project.objects.for_admin_user(request.user), slug=child_slug)
    project.translations.remove(subproj)
    project_dashboard = reverse('projects_translations', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_redirects(request, project_slug):
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)

    form = RedirectForm(data=request.POST or None, project=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_redirects', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    redirects = project.redirects.all()

    return render_to_response(
        'projects/project_redirects.html',
        {'form': form, 'project': project, 'redirects': redirects},
        context_instance=RequestContext(request)
    )


@login_required
def project_redirects_delete(request, project_slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed('Only POST is allowed')
    project = get_object_or_404(Project.objects.for_admin_user(request.user),
                                slug=project_slug)
    redirect = get_object_or_404(project.redirects,
                                 pk=request.POST.get('id_pk'))
    if redirect.project == project:
        redirect.delete()
    else:
        raise Http404
    return HttpResponseRedirect(reverse('projects_redirects',
                                        args=[project.slug]))


@login_required
def project_import_github(request, sync=False):
    '''Show form that prefills import form with data from GitHub'''
    github_connected = oauth_utils.import_github(user=request.user, sync=sync)
    repos = GithubProject.objects.filter(users__in=[request.user])

    # Find existing projects that match a repo url
    for repo in repos:
        ghetto_repo = repo.git_url.replace('git://', '').replace('.git', '')
        projects = (Project
                    .objects
                    .public(request.user)
                    .filter(Q(repo__endswith=ghetto_repo) |
                            Q(repo__endswith=ghetto_repo + '.git')))
        if projects:
            repo.matches = [project.slug for project in projects]
        else:
            repo.matches = []

    return render_to_response(
        'projects/project_import_github.html',
        {
            'repos': repos,
            'github_connected': github_connected,
            'sync': sync,
        },
        context_instance=RequestContext(request)
    )
