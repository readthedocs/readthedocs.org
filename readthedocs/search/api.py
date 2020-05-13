import itertools
import logging
import re

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.models import Version
from readthedocs.projects.constants import MKDOCS, SPHINX_HTMLDIR
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
    full_path = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()
    inner_hits = serializers.SerializerMethodField()

    def get_link(self, obj):
        project_data = self.context['projects_data'].get(obj.project)
        if not project_data:
            return None

        docs_url, doctype = project_data
        path = obj.full_path

        # Generate an appropriate link for the doctypes that use htmldir,
        # and always end it with / so it goes directly to proxito.
        if doctype in {SPHINX_HTMLDIR, MKDOCS}:
            new_path = re.sub('(^|/)index.html$', '/', path)
            # docs_url already ends with /,
            # make sure to not include it twice.
            path = new_path.lstrip('/')

        return docs_url + path

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

        # Check to avoid searching all projects in case these filters are empty.
        if not kwargs['filters']['project']:
            log.info("Unable to find a project to search")
            return HTMLFile.objects.none()
        if not kwargs['filters']['version']:
            log.info("Unable to find a version to search")
            return HTMLFile.objects.none()

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
        context['projects_data'] = self.get_all_projects_data()
        return context

    def get_all_projects(self):
        """
        Return a list of the project itself and all its subprojects the user has permissions over.

        :rtype: list
        """
        main_version = self._get_version()
        main_project = self._get_project()

        all_projects = [main_project]

        subprojects = Project.objects.filter(
            superprojects__parent_id=main_project.id,
        )
        for project in subprojects:
            version = (
                Version.internal
                .public(user=self.request.user, project=project, include_hidden=False)
                .filter(slug=main_version.slug)
                .first()
            )
            if version:
                all_projects.append(version.project)
        return all_projects

    def get_all_projects_data(self):
        """
        Return a dict containing the project slug and its version URL and version's doctype.

        The dictionary contains the project and its subprojects. Each project's
        slug is used as a key and a tuple with the documentation URL and doctype
        from the version. Example:

        {
            "requests": (
                "https://requests.readthedocs.io/en/latest/",
                "sphinx",
            ),
            "requests-oauth": (
                "https://requests-oauth.readthedocs.io/en/latest/",
                "sphinx_htmldir",
            ),
        }

        :rtype: dict
        """
        all_projects = self.get_all_projects()
        version_slug = self._get_version().slug
        project_urls = {}
        for project in all_projects:
            project_urls[project.slug] = project.get_docs_url(version_slug=version_slug)

        versions_doctype = (
            Version.objects
            .filter(project__slug__in=project_urls.keys(), slug=version_slug)
            .values_list('project__slug', 'documentation_type')
        )

        projects_data = {
            project_slug: (project_urls[project_slug], doctype)
            for project_slug, doctype in versions_doctype
        }
        return projects_data

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
