from functools import lru_cache

import structlog
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.models import Feature, Project
from readthedocs.search import tasks
from readthedocs.search.api.pagination import SearchPagination
from readthedocs.search.api.v2.serializers import (
    PageSearchSerializer,
    ProjectData,
    VersionData,
)
from readthedocs.search.faceted_search import PageSearch
from readthedocs.search.api import SearchPagination
from readthedocs.core.utils.extend import SettingsOverrideObject

log = structlog.get_logger(__name__)


class PageSearchAPIView(CDNCacheTagsMixin, GenericAPIView):

    """
    Server side search API.

    Required query parameters:

    - **q**: Search term.
    - **project**: Project to search.
    - **version**: Version to search.

    Check our [docs](https://docs.readthedocs.io/en/stable/server-side-search.html#api) for more information.
    """  # noqa

    http_method_names = ["get"]
    permission_classes = [IsAuthorizedToViewVersion]
    pagination_class = SearchPagination
    serializer_class = PageSearchSerializer
    project_cache_tag = "rtd-search"

    @lru_cache(maxsize=1)
    def _get_project(self):
        project_slug = self.request.GET.get("project", None)
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        version_slug = self.request.GET.get("version", None)
        project = self._get_project()
        version = get_object_or_404(
            project.versions.all(),
            slug=version_slug,
        )
        return version

    def _validate_query_params(self):
        """
        Validate all required query params are passed on the request.

        Query params required are: ``q``, ``project`` and ``version``.

        :rtype: None

        :raises: ValidationError if one of them is missing.
        """
        errors = {}
        required_query_params = {"q", "project", "version"}
        request_params = set(self.request.query_params.keys())
        missing_params = required_query_params - request_params
        for param in missing_params:
            errors[param] = [_("This query param is required")]
        if errors:
            raise ValidationError(errors)

    @lru_cache(maxsize=1)
    def _get_all_projects_data(self):
        """
        Return a dictionary of the project itself and all its subprojects.

        Example:

        .. code::

           {
               "requests": ProjectData(
                   alias='alias',
                   version=VersionData(
                        "latest",
                        "https://requests.readthedocs.io/en/latest/",
                    ),
               ),
               "requests-oauth": ProjectData(
                   alias=None,
                   version=VersionData(
                       "latest",
                       "https://requests-oauth.readthedocs.io/en/latest/",
                   ),
               ),
           }

        .. note:: The response is cached into the instance.

        :rtype: A dictionary of project slugs mapped to a `VersionData` object.
        """
        main_version = self._get_version()
        main_project = self._get_project()

        if not self._has_permission(self.request.user, main_version):
            return {}

        projects_data = {
            main_project.slug: self._get_project_data(main_project, main_version),
        }

        subprojects = Project.objects.filter(superprojects__parent_id=main_project.id)
        for subproject in subprojects:
            version = self._get_project_version(
                project=subproject,
                version_slug=main_version.slug,
                include_hidden=False,
            )

            # Fallback to the default version of the subproject.
            if not version and subproject.default_version:
                version = self._get_project_version(
                    project=subproject,
                    version_slug=subproject.default_version,
                    include_hidden=False,
                )

            if version and self._has_permission(self.request.user, version):
                projects_data[subproject.slug] = self._get_project_data(
                    subproject, version
                )

        return projects_data

    def _get_project_data(self, project, version):
        """Build a `ProjectData` object given a project and its version."""
        url = project.get_docs_url(version_slug=version.slug)
        project_alias = project.superprojects.values_list("alias", flat=True).first()
        version_data = VersionData(
            slug=version.slug,
            docs_url=url,
        )
        return ProjectData(
            alias=project_alias,
            version=version_data,
        )

    def _get_project_version(self, project, version_slug, include_hidden=True):
        """
        Get a version from a given project.

        :param project: A `Project` object.
        :param version_slug: The version slug.
        :param include_hidden: If hidden versions should be considered.
        """
        return (
            Version.internal.public(
                user=self.request.user,
                project=project,
                only_built=True,
                include_hidden=include_hidden,
            )
            .filter(slug=version_slug)
            .first()
        )

    def _has_permission(self, user, version):
        """
        Check if `user` is authorized to access `version`.

        The queryset from `_get_subproject_version` already filters public
        projects. This is mainly to be overridden in .com to make use of
        the auth backends in the proxied API.
        """
        return True

    def _get_search_query(self):
        return self.request.query_params["q"]

    def _record_query(self, response):
        project_slug = self._get_project().slug
        version_slug = self._get_version().slug
        total_results = response.data.get("count", 0)
        time = timezone.now()

        query = self._get_search_query().lower().strip()

        # Record the query with a celery task
        tasks.record_search_query.delay(
            project_slug,
            version_slug,
            query,
            total_results,
            time.isoformat(),
        )

    def _use_advanced_query(self):
        main_project = self._get_project()
        return not main_project.has_feature(Feature.DEFAULT_TO_FUZZY_SEARCH)

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        projects = {
            project: project_data.version.slug
            for project, project_data in self._get_all_projects_data().items()
        }
        # Check to avoid searching all projects in case it's empty.
        if not projects:
            log.info("Unable to find a version to search")
            return []

        query = self._get_search_query()
        queryset = PageSearch(
            query=query,
            projects=projects,
            aggregate_results=False,
            use_advanced_query=self._use_advanced_query(),
        )
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["projects_data"] = self._get_all_projects_data()
        return context

    def get(self, request, *args, **kwargs):
        self._validate_query_params()
        result = self.list()
        self._record_query(result)
        return result

    def list(self):
        """List the results using pagination."""
        queryset = self.get_queryset()
        page = self.paginator.paginate_queryset(
            queryset,
            self.request,
            view=self,
        )
        serializer = self.get_serializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class BaseProxiedPageSearchAPIView(PageSearchAPIView):

    pass


class ProxiedPageSearchAPIView(SettingsOverrideObject):

    _default_class = BaseProxiedPageSearchAPIView
