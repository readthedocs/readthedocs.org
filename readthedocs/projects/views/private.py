import os
import shutil
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView
from django.utils.decorators import method_decorator

from allauth.socialaccount.models import SocialToken
from guardian.shortcuts import assign
from requests_oauthlib import OAuth2Session

from builds.forms import AliasForm, VersionForm
from builds.filters import VersionFilter
from builds.models import VersionAlias, Version
from projects.forms import (ImportProjectForm, build_versions_form,
                            build_upload_html_form, SubprojectForm,
                            UserForm, EmailHookForm, TranslationForm,
                            AdvancedProjectForm, RedirectForm)
from projects.models import Project, EmailHook, GithubProject
from projects import constants
from redirects.models import Redirect


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
        return self.request.user.projects.live()

    def get_context_data(self, **kwargs):
        context = super(ProjectDashboard, self).get_context_data(**kwargs)
        qs = (Version.objects.active(user=self.request.user)
              .filter(project__users__in=[self.request.user]))
        filter = VersionFilter(
            constants.IMPORTANT_VERSION_FILTERS, queryset=self.get_queryset())
        context['filter'] = filter
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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)

    form_class = ImportProjectForm

    form = form_class(instance=project, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    form_class = AdvancedProjectForm
    form = form_class(instance=project, data=request.POST or None, initial={
                      'num_minor': 2, 'num_major': 2, 'num_point': 2})

    if request.method == 'POST' and form.is_valid():
        form.save()
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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)

    if not project.is_imported:
        raise Http404

    form_class = build_versions_form(project)

    form = form_class(data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_detail', args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_versions.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
    )


@login_required
def project_version_detail(request, project_slug, version_slug):
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    version = get_object_or_404(project.versions.all(), slug=version_slug)

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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)

    if request.method == 'POST':
        # Remove the repository checkout
        shutil.rmtree(project.doc_path, ignore_errors=True)
        # Delete the project and everything related to it
        project.delete()
        project_dashboard = reverse('projects_dashboard')
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_delete.html',
        {'project': project},
        context_instance=RequestContext(request)
    )


@login_required
def project_import(request):
    """
    Import docs from an repo
    """
    form = ImportProjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        project = form.save()
        form.instance.users.add(request.user)
        assign('view_project', request.user, project)
        project_manage = reverse('projects_detail', args=[project.slug])
        return HttpResponseRedirect(project_manage + '?docs_not_built=True')

    return render_to_response(
        'projects/project_import.html',
        {'form': form},
        context_instance=RequestContext(request)
    )


@login_required
def edit_alias(request, project_slug, id=None):
    proj = get_object_or_404(Project.objects.all(), slug=project_slug)
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
        self.project = get_object_or_404(
            Project.objects.all(), slug=self.kwargs.get('project_slug'))
        return self.project.aliases.all()


@login_required
def project_subprojects(request, project_slug):
    project = get_object_or_404(request.user.projects.live(),
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
    parent = get_object_or_404(request.user.projects.live(), slug=project_slug)
    child = get_object_or_404(Project.objects.all(), slug=child_slug)

    parent.remove_subproject(child)

    project_dashboard = reverse('projects_detail', args=[parent.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_users(request, project_slug):
    project = get_object_or_404(request.user.projects.live(),
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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    user = get_object_or_404(User.objects.all(),
                             username=request.POST.get('username'))
    if user == request.user:
        raise Http404
    project.users.remove(user)
    project_dashboard = reverse('projects_users', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_notifications(request, project_slug):
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    form = EmailHookForm(data=request.POST or None, project=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_notifications',
                                    args=[project.slug])
        return HttpResponseRedirect(project_dashboard)

    emails = project.emailhook_notifications.all()

    return render_to_response(
        'projects/project_notifications.html',
        {'form': form, 'project': project, 'emails': emails},
        context_instance=RequestContext(request)
    )


@login_required
def project_notifications_delete(request, project_slug):
    if request.method != 'POST':
        raise Http404
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    notification = get_object_or_404(EmailHook.objects.all(),
                                     email=request.POST.get('email'))
    notification.delete()
    project_dashboard = reverse('projects_notifications', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_translations(request, project_slug):
    project = get_object_or_404(request.user.projects.live(),
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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    subproj = get_object_or_404(Project.objects.public(), slug=child_slug)
    project.translations.remove(subproj)
    project_dashboard = reverse('projects_translations', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_redirects(request, project_slug):
    project = get_object_or_404(request.user.projects.live(),
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
    project = get_object_or_404(request.user.projects.live(),
                                slug=project_slug)
    redirect = get_object_or_404(Redirect.objects.all(),
                                 pk=request.POST.get('pk'))
    if redirect.project == project:
        redirect.delete()
    else:
        raise Http404
    project_dashboard = reverse('projects_redirects', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)


@login_required
def project_import_github(request, repo_type='public', sync=True):
    """
    Integrate with GitHub to pull repos from there.

    Params:

    repo_type - The type of accounts to get for a user. ``private`` or ``public``
    """
    tokens = SocialToken.objects.filter(
        account__user__username=request.user.username, app__provider='github')
    if tokens.exists():
        github_connected = True
        if sync:
            repos = []
            token = tokens[0]
            session = OAuth2Session(
                client_id=token.app.client_id,
                token={
                    'access_token': str(token.token),
                    'token_type': 'bearer'
                }
            )
            resp = session.get(
                'https://api.github.com/user/repos?per_page=100&type=%s' % repo_type)
            for repo in resp.json():
                project, created = GithubProject.objects.get_or_create(
                    user=request.user,
                    name=repo['name'],
                    full_name=repo['full_name'],
                    description=repo['description'],
                    git_url=repo['git_url'],
                    ssh_url=repo['ssh_url'],
                    html_url=repo['html_url'],
                    json=repo,
                )
    else:
        github_connected = False

    repos = GithubProject.objects.filter(user=request.user)
    for repo in repos:
        ghetto_repo = repo.git_url.replace('git://', '').replace('.git', '')
        projects = Project.objects.filter(repo__endswith=ghetto_repo) | Project.objects.filter(repo__endswith=ghetto_repo + '.git')
        if projects:
            repo.matches = [project.slug for project in projects]
        else:
            repo.matches = []

    return render_to_response(
        'projects/project_import_github.html',
        {
            'repos': repos,
            'github_connected': github_connected,
        },
        context_instance=RequestContext(request)
    )
