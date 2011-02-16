from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail

from builds.models import Build
from projects.models import Project

from taggit.models import Tag

def build_list(request, project_slug=None, tag=None):
    """Show a list of builds.
    """
    queryset = Build.objects.all()

    if tag:
        tag = get_object_or_404(Tag, slug=tag)
        queryset = queryset.filter(project__tags__in=[tag.slug])
    else:
        tag = None

    project = get_object_or_404(Project, slug=project_slug)
    queryset = queryset.filter(project=project)

    return object_list(
        request,
        queryset=queryset,
        extra_context={'project': project, 'tag': tag},
        template_object_name='build',
    )

def legacy_build_list(request, username=None, project_slug=None, tag=None):
    return HttpResponsePermanentRedirect(
        reverse(build_list, kwargs={
            'project_slug': project_slug,
        })
    )

def build_detail(request, project_slug, pk):
    """Show the details of a particular build.
    """
    project = get_object_or_404(Project, slug=project_slug)
    queryset = Build.objects.filter(project=project)

    return object_detail(
        request,
        queryset=queryset,
        object_id=pk,
        extra_context={'project': project },
        template_object_name='build',
    )

def legacy_build_detail(request, username, project_slug, pk):
    return HttpResponsePermanentRedirect(
        reverse(build_detail, kwargs={
            'project_slug': project_slug,
            'pk': pk,
        })
    )
