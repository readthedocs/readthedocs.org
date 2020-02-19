"""Views for builds app."""

import logging
import textwrap
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView
from requests.utils import quote

from readthedocs.builds.models import Build, Version
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import trigger_build
from readthedocs.doc_builder.exceptions import BuildEnvironmentError
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


class BuildBase:

    model = Build

    def get_queryset(self):
        self.project_slug = self.kwargs.get('project_slug', None)
        self.project = get_object_or_404(
            Project.objects.public(self.request.user),
            slug=self.project_slug,
        )
        queryset = Build.objects.public(
            user=self.request.user,
            project=self.project,
        ).select_related('project', 'version')

        return queryset


class BuildTriggerMixin:

    @method_decorator(login_required)
    def post(self, request, project_slug):
        project = get_object_or_404(Project, slug=project_slug)

        if not AdminPermission.is_admin(request.user, project):
            return HttpResponseForbidden()

        version_slug = request.POST.get('version_slug')
        version = get_object_or_404(
            self._get_versions(project),
            slug=version_slug,
        )

        update_docs_task, build = trigger_build(
            project=project,
            version=version,
        )
        if (update_docs_task, build) == (None, None):
            # Build was skipped
            messages.add_message(
                request,
                messages.WARNING,
                "This project is currently disabled and can't trigger new builds.",
            )
            return HttpResponseRedirect(
                reverse('builds_project_list', args=[project.slug]),
            )

        return HttpResponseRedirect(
            reverse('builds_detail', args=[project.slug, build.pk]),
        )

    def _get_versions(self, project):
        return Version.internal.public(
            user=self.request.user,
            project=project,
        )


class BuildList(BuildBase, BuildTriggerMixin, ListView):

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        active_builds = self.get_queryset().exclude(
            state='finished',
        ).values('id')

        context['project'] = self.project
        context['active_builds'] = active_builds
        context['versions'] = self._get_versions(self.project)
        context['build_qs'] = self.get_queryset()

        return context


class BuildDetail(BuildBase, DetailView):

    pk_url_kwarg = 'build_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        build = self.get_object()
        if build.error != BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(build_id=build.pk):
            # Do not suggest to open an issue if the error is not generic
            return context

        scheme = (
            'https://github.com/rtfd/readthedocs.org/issues/new'
            '?title={title}{build_id}'
            '&body={body}'
        )

        # TODO: we could use ``.github/ISSUE_TEMPLATE.md`` here, but we would
        # need to add some variables to it which could impact in the UX when
        # filling an issue from the web
        body = """
        ## Details:

        * Project URL: https://readthedocs.org/projects/{project_slug}/
        * Build URL(if applicable): https://readthedocs.org{build_path}
        * Read the Docs username(if applicable): {username}

        ## Expected Result

        *A description of what you wanted to happen*

        ## Actual Result

        *A description of what actually happened*""".format(
            project_slug=self.project,
            build_path=self.request.path,
            username=self.request.user,
        )

        scheme_dict = {
            'title': quote('Build error with build id #'),
            'build_id': context['build'].id,
            'body': quote(textwrap.dedent(body)),
        }

        issue_url = scheme.format(**scheme_dict)
        issue_url = urlparse(issue_url).geturl()
        context['issue_url'] = issue_url
        return context
