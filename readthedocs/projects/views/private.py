import os
import shutil
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list

from guardian.shortcuts import assign

from builds.forms import AliasForm
from builds.filters import VersionFilter
from builds.models import Version
from projects.forms import (ImportProjectForm, build_versions_form,
                            build_upload_html_form, SubprojectForm,
                            UserForm)
from projects.models import Project
from projects.tasks import unzip_files
from projects import constants


@login_required
def project_dashboard(request):
    """
    A dashboard!  If you aint know what that means you aint need to.
    Essentially we show you an overview of your content.
    """
    qs = Version.objects.active(user=request.user).filter(project__users__in=[request.user])
    filter = VersionFilter(constants.IMPORTANT_VERSION_FILTERS, queryset=qs)
    return object_list(
        request,
        queryset=request.user.projects.live(),
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
        template_name='projects/project_dashboard.html',
        extra_context={
            'filter': filter,
        }
    )

@login_required
def project_manage(request, project_slug):
    """
    The management view for a project, where you will have links to edit
    the projects' configuration, edit the files associated with that
    project, etc.

    Now redirects to the normal /projects/<slug> view.
    """
    return HttpResponseRedirect(reverse('projects_detail', args=[project_slug]))

@login_required
def project_edit(request, project_slug):
    """
    Edit an existing project - depending on what type of project is being
    edited (created or imported) a different form will be displayed
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)

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
def project_versions(request, project_slug):
    """
    Shows the available versions and lets the user choose which ones he would
    like to have built.
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)

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
def project_delete(request, project_slug):
    """
    Make a project as deleted on POST, otherwise show a form asking for
    confirmation of delete.
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)

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
def export(request, project_slug):
    """
    Export a projects' docs as a .zip file, including the .rst source
    """
    project = Project.objects.live().get(users=request.user, slug=project_slug)
    os.chdir(project.doc_path)
    dir_path = os.path.join(settings.MEDIA_ROOT, 'export', project_slug)
    zip_filename = '%s.zip' % project.slug
    file_path = os.path.join(dir_path, zip_filename)
    try:
        os.makedirs(dir_path)
    except OSError:
        #Directory already exists
        pass

    # Create a <slug>.zip file containing all files in file_path
    archive = zipfile.ZipFile(zip_filename, 'w')
    for root, subfolders, files in os.walk(file_path):
        for file in files:
            archive.write(os.path.join(root, file))
    archive.close()

    return HttpResponseRedirect(os.path.join(settings.MEDIA_URL, 'export', project_slug, zip_filename))


def upload_html(request, project_slug):
    proj = get_object_or_404(Project.objects.all(), slug=project_slug)
    FormClass = build_upload_html_form(proj)
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, request=request)
        if form.is_valid():
            file = request.FILES['content']
            version_slug = form.cleaned_data['version']
            version = proj.versions.get(slug=version_slug)
            #Copy file
            dest_dir = os.path.join(settings.UPLOAD_ROOT, proj.slug)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            dest_file = os.path.join(dest_dir, file.name)
            destination = open(dest_file, 'wb+')
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()

            #Mark version active.
            version.active = True
            version.uploaded = True
            version.built = False
            version.save()

            #Extract file into the correct place.
            html_path = proj.rtd_build_path(version.slug)
            unzip_files(dest_file, html_path)
            return HttpResponseRedirect(proj.get_absolute_url())
    else:
        form = FormClass(request=request)
    return render_to_response(
        'projects/upload_html.html',
        {'form': form, 'project': proj},
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

@login_required
def list_alias(request, project_slug):
    proj = get_object_or_404(Project.objects.all(), slug=project_slug)
    return object_list(
        request,
        queryset=proj.aliases.all(),
        template_object_name='alias',
        template_name='projects/alias_list.html',
    )

@login_required
def project_subprojects(request, project_slug):
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)

    form = SubprojectForm(data=request.POST or None, parent=project)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_detail', args=[project.slug])
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
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)

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
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    user = get_object_or_404(User.objects.all(), username=request.POST.get('username'))
    if user == request.user:
        raise Http404
    project.users.remove(user)
    project_dashboard = reverse('projects_users', args=[project.slug])
    return HttpResponseRedirect(project_dashboard)
