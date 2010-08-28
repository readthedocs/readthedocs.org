from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail

from builds.models import Build
from projects.models import Project

from taggit.models import Tag

def build_list(request, username=None, project_slug=None, tag=None):
    queryset = Build.objects.all()
    if username:
        user = get_object_or_404(User, username=username)
        queryset = queryset.filter(project__user=user)
    else:
        user = None
    if tag:
        tag = get_object_or_404(Tag, slug=tag)
        queryset = queryset.filter(project__tags__in=[tag.slug])
    else:
        tag = None

    if project_slug and username:
        project = Project.objects.get(user=user, slug=project_slug)
        queryset = queryset.filter(project=project)
    else:
        project = None


    return object_list(
        request,
        queryset=queryset,
        extra_context={'person': user, 'project': project, 'tag': tag},
        template_object_name='build',
    )

def build_detail(request, username, project_slug, pk):
    user = get_object_or_404(User, username=username)
    queryset = Build.objects.all()

    if project_slug and username:
        project = Project.objects.get(user=user, slug=project_slug)
        queryset = queryset.filter(project=project)
    else:
        project = None

    return object_detail(
        request,
        queryset=queryset,
        object_id=pk,
        extra_context={'user': user, 'project': project },
        template_object_name='build',
    )
