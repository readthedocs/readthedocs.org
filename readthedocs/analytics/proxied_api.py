"""Analytics views that are served from the same domain as the docs."""

from functools import lru_cache

from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.analytics.models import PageView
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.core.unresolver import unresolve_from_request
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.models import Project


class BaseAnalyticsView(APIView):

    """
    Track page views.

    Query parameters:

    - project
    - version
    - absolute_uri: Full path with domain.
    """

    http_method_names = ['get']
    permission_classes = [IsAuthorizedToViewVersion]

    @lru_cache(maxsize=1)
    def _get_project(self):
        project_slug = self.request.GET.get('project')
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        version_slug = self.request.GET.get('version')
        project = self._get_project()
        version = get_object_or_404(
            project.versions.all(),
            slug=version_slug,
        )
        return version

    # pylint: disable=unused-argument
    def get(self, request, *args, **kwargs):
        project = self._get_project()
        version = self._get_version()
        absolute_uri = self.request.GET.get('absolute_uri')
        self.increase_page_view_count(
            request=request,
            project=project,
            version=version,
            absolute_uri=absolute_uri,
        )
        return Response(status=200)

    # pylint: disable=no-self-use
    def increase_page_view_count(self, request, project, version, absolute_uri):
        """Increase the page view count for the given project."""
        unresolved = unresolve_from_request(request, absolute_uri)
        if not unresolved:
            return

        path = unresolved.filename

        fields = dict(
            project=project,
            version=version,
            path=path,
            date=timezone.now().date(),
        )
        page_view = PageView.objects.filter(**fields).first()
        if page_view:
            page_view.view_count = F('view_count') + 1
            page_view.save(update_fields=['view_count'])
        else:
            PageView.objects.create(**fields, view_count=1)


class AnalyticsView(SettingsOverrideObject):

    _default_class = BaseAnalyticsView
