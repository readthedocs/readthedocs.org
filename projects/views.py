from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.views.generic.list_detail import object_list, object_detail

from projects.forms import ProjectForm
from projects.models import Project


def project_index(request, username=None):
    queryset = Project.objects.all()
    if username:
        user = get_object_or_404(User, username=username)
        queryset = queryset.filter(user=user)
    else:
        user = None

    return object_list(
        request,
        queryset=queryset,
        extra_context={'user': user},
        paginate_by=20,
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
    )

def project_detail(request, username, project_slug):
    user = get_object_or_404(User, username=username)
    queryset = user.projects.all()
    
    return object_detail(
        request,
        queryset=queryset,
        slug_field='slug',
        slug=project_slug,
        extra_context={'user': user},
        template_object_name='project',
    )

@login_required
def project_edit(request, username, project_slug):
    user = get_object_or_404(User, username=username)
    project = get_object_or_404(user.projects.all(), slug=project_slug)

    form = ProjectForm(instance=project, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(project)

    return render_to_response(
        'projects/project_edit.html',
        {'form': form, 'project': project},
        context_instance=RequestContext(request)
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
            return redirect(project)

    return render_to_response(
        'projects/project_create.html',
        {'form': form},
        context_instance=RequestContext(request)
    )

@login_required
def project_import(request):
    """
    I guess a form here for configuring your import?
    """
    pass
