from django.shortcuts import get_object_or_404
from core.generic.list_detail import object_list, object_detail
from django.views.generic import ListView, DetailView

from taggit.models import Tag

from builds.models import Build
from builds.filters import BuildFilter
from projects.models import Project

class BuildList(ListView):
    model = Build

    def get_queryset(self):
        self.project_slug = self.kwargs.get('project_slug', None)
        self.tag = self.kwargs.get('tag', None)

        self.project = get_object_or_404(
            Project.objects.protected(self.request.user),
            slug=self.project_slug
        )
        queryset = Build.objects.filter(project=self.project)

        if self.tag:
            self.tag = get_object_or_404(Tag, slug=self.tag)
            queryset = queryset.filter(project__tags__in=[self.tag.slug])

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BuildList, self).get_context_data(**kwargs)

        filter = BuildFilter(self.request.GET, queryset=self.queryset)
        active_builds = self.get_queryset().exclude(state="finished").values('id')

        context['tag'] = self.tag
        context['project'] = self.project
        context['filter'] = filter
        context['active_builds'] = active_builds
        return context

class BuildDetail(DetailView):
    model = Build

    def get_queryset(self):
        self.project_slug = self.kwargs.get('project_slug', None)

        self.project = get_object_or_404(
            Project.objects.protected(self.request.user),
            slug=self.project_slug
        )
        queryset = Build.objects.filter(project=self.project)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BuildDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context
