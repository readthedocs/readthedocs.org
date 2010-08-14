from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.views.generic.list_detail import object_list

from projects.forms import ProjectForm
from projects.models import Project


@login_required
def project_dashboard(request):
    return object_list(
        request,
        queryset=request.user.projects.all(),
        paginate_by=20,
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
    )

@login_required
def project_create(request):
    """
    A form for creating a brand new project?
    """
    form = ProjectForm(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            form.instance.user = request.user
            project = form.save()
            project_edit = reverse('project_edit', args=[project.slug])
            return HttpResponseRedirect(project_edit)

    return render_to_response(
        'projects/project_create.html',
        {'form': form},
        context_instance=RequestContext(request)
    )

@login_required
def project_edit(request, project_slug):
    project = get_object_or_404(request.user.projects.all(), slug=project_slug)

    form = ProjectForm(instance=project, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        project_dashboard = reverse('project_dashboard')
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_edit.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
    )

@login_required
def project_delete(request, project_slug):
    project = get_object_or_404(request.user.projects.all(), slug=project_slug)

    if request.method == 'POST':
        project.delete()
        project_dashboard = reverse('project_dashboard')
        return HttpResponseRedirect(project_dashboard)

    return render_to_response(
        'projects/project_delete.html',
        {'project': project},
        context_instance=RequestContext(request)
    )

@login_required
def project_import(request):
    """
    I guess a form here for configuring your import?
    """
    pass
