"""Views for builds app."""

from __future__ import absolute_import
from builtins import object
import logging

from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator

from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project

from redis import Redis, ConnectionError


log = logging.getLogger(__name__)


class BuildBase(object):
    model = Build

    def get_queryset(self):
        self.project_slug = self.kwargs.get('project_slug', None)
        self.project = get_object_or_404(
            Project.objects.protected(self.request.user),
            slug=self.project_slug
        )
        queryset = Build.objects.public(
            user=self.request.user, project=self.project)

        return queryset


class BuildTriggerMixin(object):

    @method_decorator(login_required)
    def post(self, request, project_slug):
        project = get_object_or_404(
            Project.objects.for_admin_user(self.request.user),
            slug=project_slug
        )
        version_slug = request.POST.get('version_slug')
        version = get_object_or_404(
            Version,
            project=project,
            slug=version_slug,
        )

        trigger_build(project=project, version=version)
        return HttpResponseRedirect(reverse('builds_project_list', args=[project.slug]))


class BuildList(BuildBase, BuildTriggerMixin, ListView):

    def get_context_data(self, **kwargs):
        context = super(BuildList, self).get_context_data(**kwargs)

        active_builds = self.get_queryset().exclude(state="finished").values('id')

        context['project'] = self.project
        context['active_builds'] = active_builds
        context['versions'] = Version.objects.public(
            user=self.request.user, project=self.project)
        context['build_qs'] = self.get_queryset()

        try:
            redis = Redis.from_url(settings.BROKER_URL)
            context['queue_length'] = redis.llen('celery')
        except ConnectionError:
            context['queue_length'] = None

        return context


class BuildDetail(BuildBase, DetailView):
    pk_url_kwarg = 'build_pk'

    def get_context_data(self, **kwargs):
        context = super(BuildDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context


# Old build view redirects

def builds_redirect_list(request, project_slug):  # pylint: disable=unused-argument
    return HttpResponsePermanentRedirect(reverse('builds_project_list', args=[project_slug]))


def builds_redirect_detail(request, project_slug, pk):  # pylint: disable=unused-argument
    return HttpResponsePermanentRedirect(reverse('builds_detail', args=[project_slug, pk]))
