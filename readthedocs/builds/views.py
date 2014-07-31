from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail

from taggit.models import Tag

from builds.models import Build
from builds.filters import BuildFilter
from projects.models import Project


def build_list(request, project_slug=None, tag=None):
    """Show a list of builds.
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)
    queryset = Build.objects.filter(project=project)

    if tag:
        tag = get_object_or_404(Tag, slug=tag)
        queryset = queryset.filter(project__tags__in=[tag.slug])
    else:
        tag = None

    filter = BuildFilter(request.GET, queryset=queryset)
    active_builds = queryset.exclude(state="finished").values('id')

    return object_list(
        request,
        queryset=queryset,
        extra_context={
            'project': project,
            'filter': filter,
            'tag': tag,
            'active_builds': active_builds
        },
        template_object_name='build',
    )


def build_detail(request, project_slug, pk):
    """Show the details of a particular build.
    """
    project = get_object_or_404(Project.objects.protected(request.user),
                                slug=project_slug)
    queryset = Build.objects.filter(project=project)

    return object_detail(
        request,
        queryset=queryset,
        object_id=pk,
        extra_context={'project': project},
        template_object_name='build',
    )
