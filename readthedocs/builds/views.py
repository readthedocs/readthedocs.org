from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.conf import settings

from builds.models import Build, Version
from builds.filters import BuildFilter
from projects.models import Project

from redis import Redis, ConnectionError


class BuildList(ListView):
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
        context = super(BuildList, self).get_context_data(**kwargs)

        filter = BuildFilter(self.request.GET, queryset=self.get_queryset())
        active_builds = self.get_queryset().exclude(state="finished").values('id')

        context['project'] = self.project
        context['filter'] = filter
        context['active_builds'] = active_builds
        context['versions'] = Version.objects.public(user=self.request.user, project=self.project)

        try:
            redis = Redis(**settings.REDIS)
            context['queue_length'] = redis.llen('celery')
        except ConnectionError:
            context['queue_length'] = None

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
