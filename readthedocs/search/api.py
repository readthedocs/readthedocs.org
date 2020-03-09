import itertools
import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search import tasks, utils
from readthedocs.search.faceted_search import PageSearch

log = logging.getLogger(__name__)


class SearchPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class PageSearchSerializer(serializers.Serializer):
    project = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()
    inner_hits = serializers.SerializerMethodField()

    def get_link(self, obj):
        projects_url = self.context.get('projects_url')
        if projects_url:
            docs_url = projects_url[obj.project]
            return docs_url + obj.path

    def get_highlight(self, obj):
        highlight = getattr(obj.meta, 'highlight', None)
        if highlight:
            ret = highlight.to_dict()
            log.debug('API Search highlight [Page title]: %s', ret)
            return ret

    def get_inner_hits(self, obj):
        inner_hits = getattr(obj.meta, 'inner_hits', None)
        if inner_hits:
            sections = inner_hits.sections or []
            domains = inner_hits.domains or []
            all_results = itertools.chain(sections, domains)

            sorted_results = utils._get_sorted_results(
                results=all_results,
                source_key='_source',
            )

            log.debug('[API] Sorted Results: %s', sorted_results)
            return sorted_results


class PageSearchAPIView(generics.ListAPIView):

    """
    Main entry point to perform a search using Elasticsearch.

    Required query params:
    - q (search term)
    - project
    - version

    .. note::

       The methods `_get_project` and `_get_version`
       are called many times, so a basic cache is implemented.
    """

    permission_classes = [IsAuthorizedToViewVersion]
    pagination_class = SearchPagination
    serializer_class = PageSearchSerializer

    def _get_project(self):
        cache_key = '_cached_project'
        project = getattr(self, cache_key, None)

        if not project:
            project_slug = self.request.GET.get('project', None)
            project = get_object_or_404(Project, slug=project_slug)
            setattr(self, cache_key, project)

        return project

    def _get_version(self):
        cache_key = '_cached_version'
        version = getattr(self, cache_key, None)

        if not version:
            version_slug = self.request.GET.get('version', None)
            project = self._get_project()
            version = get_object_or_404(
                project.versions.all(),
                slug=version_slug,
            )
            setattr(self, cache_key, version)

        return version

    def get_queryset(self):
        """
        Return Elasticsearch DSL Search object instead of Django Queryset.

        Django Queryset and elasticsearch-dsl ``Search`` object is similar pattern.
        So for searching, its possible to return ``Search`` object instead of queryset.
        The ``filter_backends`` and ``pagination_class`` is compatible with ``Search``
        """
        # Validate all the required params are there
        self.validate_query_params()
        query = self.request.query_params.get('q', '')
        kwargs = {'filter_by_user': False, 'filters': {}}
        kwargs['filters']['project'] = [p.slug for p in self.get_all_projects()]
        kwargs['filters']['version'] = self._get_version().slug
        user = self.request.user
        queryset = PageSearch(
            query=query, user=user, **kwargs
        )
        return queryset

    def validate_query_params(self):
        """
        Validate all required query params are passed on the request.

        Query params required are: ``q``, ``project`` and ``version``.

        :rtype: None

        :raises: ValidationError if one of them is missing.
        """
        required_query_params = {'q', 'project', 'version'}  # python `set` literal is `{}`
        request_params = set(self.request.query_params.keys())
        missing_params = required_query_params - request_params
        if missing_params:
            errors = {}
            for param in missing_params:
                errors[param] = ["This query param is required"]

            raise ValidationError(errors)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['projects_url'] = self.get_all_projects_url()
        return context

    def get_all_projects(self):
        """
        Return a list containing the project itself and all its subprojects.

        :rtype: list
        """
        main_version = self._get_version()
        main_project = self._get_project()

        subprojects = Project.objects.filter(
            superprojects__parent_id=main_project.id,
        )
        all_projects = []
        for project in list(subprojects) + [main_project]:
            version = (
                Version.objects
                .public(user=self.request.user, project=project)
                .filter(slug=main_version.slug)
                .first()
            )
            if version:
                all_projects.append(version.project)
        return all_projects

    def get_all_projects_url(self):
        """
        Return a dict containing the project slug and its version URL.

        The dictionary contains the project and its subprojects . Each project's
        slug is used as a key and the documentation URL for that project and
        version as the value.

        Example:

        {
            "requests": "https://requests.readthedocs.io/en/latest/",
            "requests-oauth": "https://requests-oauth.readthedocs.io/en/latest/",
        }

        :rtype: dict
        """
        all_projects = self.get_all_projects()
        version_slug = self._get_version().slug
        projects_url = {}
        for project in all_projects:
            projects_url[project.slug] = project.get_docs_url(version_slug=version_slug)
        return projects_url

    def list(self, request, *args, **kwargs):
        """Overriding ``list`` method to record query in database."""

        response = super().list(request, *args, **kwargs)

        project_slug = self._get_project().slug
        version_slug = self._get_version().slug
        total_results = response.data.get('count', 0)
        time = timezone.now()

        query = self.request.query_params.get('q', '')
        query = query.lower().strip()

        # record the search query with a celery task
        tasks.record_search_query.delay(
            project_slug,
            version_slug,
            query,
            total_results,
            time.isoformat(),
        )

        return response
