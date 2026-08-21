"""Views for builds app."""

import textwrap
from urllib.parse import urlparse

import structlog
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic import ListView
from requests.utils import quote

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.filters import BuildListFilter
from readthedocs.builds.models import Build
from readthedocs.core.filters import FilterContextMixin
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import cancel_build
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.projects.models import Project
from readthedocs.projects.views.base import ProjectSpamMixin


log = structlog.get_logger(__name__)


class BuildBase:
    model = Build

    def get_queryset(self):
        self.project_slug = self.kwargs.get("project_slug", None)
        self.project = get_object_or_404(
            Project.objects.public(self.request.user),
            slug=self.project_slug,
        )
        queryset = Build.objects.public(
            user=self.request.user,
            project=self.project,
        ).select_related("project", "version")

        return queryset


class BuildList(
    FilterContextMixin,
    ProjectSpamMixin,
    BuildBase,
    ListView,
):
    filterset_class = BuildListFilter

    def _get_versions(self, project):
        project.versions(manager=INTERNAL).public(
            user=self.request.user,
        )

    def get_project(self):
        # Call ``.get_queryset()`` to get the current project from ``kwargs``
        self.get_queryset()
        return self.project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_builds = (
            self.get_queryset()
            .exclude(
                state__in=BUILD_FINAL_STATES,
            )
            .values("id")
        )

        context["project"] = self.project
        context["active_builds"] = active_builds
        context["versions"] = self._get_versions(self.project)

        builds = self.get_queryset()
        context["filter"] = self.get_filterset(
            queryset=builds,
            project=self.project,
        )
        builds = self.get_filtered_queryset()
        context["build_qs"] = builds

        return context


class BuildDetail(BuildBase, ProjectSpamMixin, DetailView):
    pk_url_kwarg = "build_pk"

    def get_project(self):
        return self.get_object().project

    @method_decorator(login_required)
    def post(self, request, project_slug, build_pk):
        project = get_object_or_404(Project, slug=project_slug)
        build = get_object_or_404(project.builds, pk=build_pk)

        if not AdminPermission.is_admin(request.user, project):
            return HttpResponseForbidden()

        cancel_build(build)

        return HttpResponseRedirect(
            reverse("builds_detail", args=[project.slug, build.pk]),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project

        build = self.get_object()
        context["notifications"] = build.notifications.all()
        if not build.notifications.filter(message_id=BuildAppError.GENERIC_WITH_BUILD_ID).exists():
            # Do not suggest to open an issue if the error is not generic
            return context

        scheme = (
            "https://github.com/rtfd/readthedocs.org/issues/new?title={title}{build_id}&body={body}"
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
            "title": quote("Build error with build id #"),
            "build_id": context["build"].id,
            "body": quote(textwrap.dedent(body)),
        }

        issue_url = scheme.format(**scheme_dict)
        issue_url = urlparse(issue_url).geturl()
        context["issue_url"] = issue_url

        return context
