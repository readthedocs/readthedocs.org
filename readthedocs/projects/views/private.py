import os
import shutil
import simplejson
import zipfile

from django import forms
from django.forms.util import ErrorList
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.markup.templatetags.markup import restructuredtext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import linebreaks
from django.template.loader import render_to_string
from django.views.generic.list_detail import object_list

from bookmarks.models import Bookmark
from builds.forms import AliasForm
from builds.models import VersionAlias
from projects import constants
from projects.forms import (FileForm, CreateProjectForm,
                            ImportProjectForm, FileRevisionForm,
                            build_versions_form, build_upload_html_form)
from projects.models import Project, File
from projects.tasks import unzip_files





@login_required
def project_dashboard(request):
    """
    A dashboard!  If you aint know what that means you aint need to.
    Essentially we show you an overview of your content.
    """
    marks = Bookmark.objects.filter(user=request.user)[:5]
    return object_list(
        request,
        queryset=request.user.projects.live(),
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
        extra_context={'bookmark_list': marks },
        template_name='projects/project_dashboard.html',
    )

@login_required
def project_manage(request, project_slug):
    """
    The management view for a project, where you will have links to edit
    the projects' configuration, edit the files associated with that
    project, etc.
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    return object_list(
        request,
        queryset=project.files.live(),
        extra_context={'project': project},
        page=int(request.GET.get('page', 1)),
        template_object_name='file',
        template_name='projects/project_manage.html',
    )

@login_required
def project_create(request):
    """
    The view for creating a new project where the docs will be hosted
    as objects and edited through the site
    """
    form = CreateProjectForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.instance.user = request.user
        project = form.save()
        project_manage = reverse('projects_manage', args=[project.slug])
        return HttpResponseRedirect(project_manage)

    return render_to_response(
        'projects/project_create.html',
        {'form': form},
        context_instance=RequestContext(request)
    )

@login_required
def project_edit(request, project_slug):
    """
    Edit an existing project - depending on what type of project is being
    edited (created or imported) a different form will be displayed
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)

    if project.is_imported:
        form_class = ImportProjectForm
    else:
        form_class = CreateProjectForm

    form = form_class(instance=project, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('projects_manage', args=[project.slug])
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
        project_dashboard = reverse('projects_manage', args=[project.slug])
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
        shutil.rmtree(project.user_doc_path)
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
        form.instance.user = request.user
        project = form.save()
        project_manage = reverse('projects_manage', args=[project.slug])
        return HttpResponseRedirect(project_manage + '?docs_not_built=True')

    return render_to_response(
        'projects/project_import.html',
        {'form': form},
        context_instance=RequestContext(request)
    )

@login_required
def file_add(request, project_slug):
    """
    Add a file to a project, redirecting on success to the projects mgmt page
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    file = File(project=project)

    form = FileForm(instance=file, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.instance.project = project
        file = form.save()
        project_manage = reverse('projects_manage', args=[project.slug])
        return HttpResponseRedirect(project_manage)

    return render_to_response(
        'projects/file_add.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
    )

@login_required
def file_edit(request, project_slug, file_id):
    """
    Edit an existing file
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    file = get_object_or_404(project.files.live(), pk=file_id)

    form = FileForm(instance=file, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_manage = reverse('projects_manage', args=[project.slug])
        return HttpResponseRedirect(project_manage)

    return render_to_response(
        'projects/file_edit.html',
        {'form': form, 'project': project, 'file': file},
        context_instance=RequestContext(request)
    )

@login_required
def file_delete(request, project_slug, file_id):
    """
    Mark a given file as deleted on POST, otherwise ask for confirmation
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    file = get_object_or_404(project.files.live(), pk=file_id)

    if request.method == 'POST':
        file.status = constants.DELETED_STATUS
        file.save()
        project_manage = reverse('projects_manage', args=[project.slug])
        return HttpResponseRedirect(project_manage)

    return render_to_response(
        'projects/file_delete.html',
        {'project': project, 'file': file},
        context_instance=RequestContext(request)
    )

@login_required
def file_history(request, project_slug, file_id):
    """
    A view that provides diffing from current to any revision, and when
    posted to allows you to revert
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    file = get_object_or_404(project.files.live(), pk=file_id)

    form = FileRevisionForm(file, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.cleaned_data['revision'].apply()
        history = reverse('projects_file_history', args=[project.slug, file.pk])
        return HttpResponseRedirect(history)

    return object_list(
        request,
        queryset=file.revisions.all(),
        extra_context={'project': project, 'file': file, 'form': form},
        page=int(request.GET.get('page', 1)),
        template_object_name='revision',
        template_name='projects/file_history.html',
    )

@login_required
def file_diff(request, project_slug, file_id, from_id, to_id):
    """
    Return the contents of a given revision.
    """
    project = get_object_or_404(request.user.projects.live(), slug=project_slug)
    file = get_object_or_404(project.files.live(), pk=file_id)

    # grab the requested revisions
    from_rev = get_object_or_404(file.revisions.all(), pk=from_id)
    to_rev = get_object_or_404(file.revisions.all(), pk=to_id)

    # generate a pretty html diff
    diff = file.get_html_diff(from_rev.revision_number, to_rev.revision_number)
    contents = linebreaks(to_rev.get_file_content())

    payload = {
        'diff': diff,
        'contents': contents,
        'display': str(to_rev),
    }

    # return it assuming json
    return HttpResponse(simplejson.dumps(payload), mimetype='text/javascript')

@login_required
def file_preview(request):
    """
    Live preview of restructuredtext payload - currently not wired up
    """
    f = File(
        heading=request.POST['heading'],
        content=request.POST['content'],
    )
    rendered_base = render_to_string('projects/doc_file.rst.html', {'file': f})
    rendered = restructuredtext(rendered_base)

    json_response = simplejson.dumps({'payload': rendered})
    return HttpResponse(json_response, mimetype='text/javascript')

@login_required
def export(request, project_slug):
    """
    Export a projects' docs as a .zip file, including the .rst source
    """
    project = Project.objects.live().get(user=request.user, slug=project_slug)
    os.chdir(project.user_doc_path)
    dir_path = os.path.join(settings.MEDIA_ROOT, 'export', project.user.username)
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

    return HttpResponseRedirect(os.path.join(settings.MEDIA_URL, 'export', project.user.username, zip_filename))


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
            unzip_files.delay(dest_file, html_path)
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
    """
    The view for creating a new project where the docs will be hosted
    as objects and edited through the site
    """
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
    """
    The view for creating a new project where the docs will be hosted
    as objects and edited through the site
    """
    proj = get_object_or_404(Project.objects.all(), slug=project_slug)
    return object_list(
        request,
        queryset=proj.aliases.all(),
        template_object_name='alias',
        template_name='projects/alias_list.html',
    )
