# -*- coding: utf-8 -*-

"""Views for builds app."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

from builtins import object
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponseForbidden,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from readthedocs.builds.models import Build, Version
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project

log = logging.getLogger(__name__)


class BuildBase(object):
    model = Build

    def get_queryset(self):
        self.project_slug = self.kwargs.get('project_slug', None)
        self.project = get_object_or_404(
            Project.objects.protected(self.request.user),
            slug=self.project_slug,
        )
        queryset = Build.objects.public(
            user=self.request.user, project=self.project
        )

        return queryset


class BuildTriggerMixin(object):

    @method_decorator(login_required)
    def post(self, request, project_slug):
        project = get_object_or_404(Project, slug=project_slug)

        if not AdminPermission.is_admin(request.user, project):
            return HttpResponseForbidden()

        version_slug = request.POST.get('version_slug')
        version = get_object_or_404(
            Version,
            project=project,
            slug=version_slug,
        )

        _, build = trigger_build(project=project, version=version)
        return HttpResponseRedirect(
            reverse('builds_detail', args=[project.slug, build.pk]),
        )


class BuildList(BuildBase, BuildTriggerMixin, ListView):

    def get_context_data(self, **kwargs):
        context = super(BuildList, self).get_context_data(**kwargs)

        active_builds = self.get_queryset().exclude(state='finished'
                                                    ).values('id')

        context['project'] = self.project
        context['active_builds'] = active_builds
        context['versions'] = Version.objects.public(
            user=self.request.user, project=self.project
        )
        context['build_qs'] = self.get_queryset()

        return context


class BuildDetail(BuildBase, DetailView):
    pk_url_kwarg = 'build_pk'

    def get_context_data(self, **kwargs):
        context = super(BuildDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context


# Old build view redirects


def builds_redirect_list(request, project_slug):  # pylint: disable=unused-argument
    return HttpResponsePermanentRedirect(
        reverse('builds_project_list', args=[project_slug])
    )


def builds_redirect_detail(request, project_slug, pk):  # pylint: disable=unused-argument
    return HttpResponsePermanentRedirect(
        reverse('builds_detail', args=[project_slug, pk])
    )
