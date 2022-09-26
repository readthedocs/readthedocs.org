"""Search views."""
import collections
import structlog

from django.conf import settings
from django.shortcuts import get_object_or_404, render
from readthedocs.search.backends import BackendV2
from django.views import View

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Feature, Project
from readthedocs.search.faceted_search import (
    PageSearch,
    ProjectSearch,
)

from .serializers import (
    PageSearchSerializer,
    ProjectData,
    ProjectSearchSerializer,
    VersionData,
)

from readthedocs.search.api import ProjectsToSearchMixin

log = structlog.get_logger(__name__)

UserInput = collections.namedtuple(
    'UserInput',
    (
        'query',
        'type',
        'language',
    ),
)


class SearchViewBase(View):

    http_method_names = ['get']
    max_search_results = 50

    def _search(self, *, user_input, projects, use_advanced_query):
        """Return search results and facets given a `user_input` and `projects` to filter by."""
        if not user_input.query:
            return [], {}

        filters = {}
        for avail_facet in ['language']:
            value = getattr(user_input, avail_facet, None)
            if value:
                filters[avail_facet] = value

        search_facets = {
            'project': ProjectSearch,
            'file': PageSearch,
        }
        faceted_search_class = search_facets.get(
            user_input.type,
            ProjectSearch,
        )
        search = faceted_search_class(
            query=user_input.query,
            filters=filters,
            projects=projects,
            use_advanced_query=use_advanced_query,
        )
        results = search[:self.max_search_results].execute()
        facets = results.facets

        # Make sure the selected facets are displayed,
        # even when they return 0 results.
        for facet in facets:
            value = getattr(user_input, facet, None)
            if value and value not in (name for name, *_ in facets[facet]):
                facets[facet].insert(0, (value, 0, True))

        return results, facets


class ProjectSearchView(SearchViewBase):

    """
    Search view of the ``search`` tab.

    Query params:

    - q: search term
    - version: version to filter by
    - role_name: sphinx role to filter by
    """

    def _get_project(self, project_slug):
        queryset = Project.objects.public(self.request.user)
        project = get_object_or_404(queryset, slug=project_slug)
        return project

    def _get_project_data(self, project, version_slug):
        docs_url = project.get_docs_url(version_slug=version_slug)
        version_data = VersionData(
            slug=version_slug,
            docs_url=docs_url,
        )
        project_data = {
            project.slug: ProjectData(
                alias=None,
                version=version_data,
            )
        }
        return project_data

    def get_serializer_context(self, project, version_slug):
        context = {
            'projects_data': self._get_project_data(project, version_slug),
        }
        return context

    def get(self, request, project_slug):
        project_obj = self._get_project(project_slug)
        use_advanced_query = not project_obj.has_feature(
            Feature.DEFAULT_TO_FUZZY_SEARCH,
        )

        user_input = UserInput(
            query=request.GET.get('q'),
            type='file',
            project=project_slug,
            version=request.GET.get('version', LATEST),
            role_name=request.GET.get('role_name'),
            language=None,
        )

        results, facets = self._search(
            user_input=user_input,
            projects=[user_input.project],
            use_advanced_query=use_advanced_query,
        )

        context = self.get_serializer_context(project_obj, user_input.version)
        results = PageSearchSerializer(results, many=True, context=context).data

        template_context = user_input._asdict()
        template_context.update({
            'results': results,
            'facets': facets,
            'project_obj': project_obj,
            'search_query': self._parser.query
        })

        return render(
            request,
            'search/elastic_search.html',
            template_context,
        )


class GlobalSearchView(SearchViewBase, ProjectsToSearchMixin):

    """
    Global search enabled for logged out users and anyone using the dashboard.

    Query params:

    - q: Search query
    - type: Type of document to search (project or file)
    """

    def get(self, request):
        user_input = UserInput(
            query=request.GET.get('q', ""),
            type=request.GET.get('type', 'project'),
            language=request.GET.get('language'),
        )

        backend = BackendV2(
            request=request,
            query=user_input.query,
            allow_search_all=not settings.ALLOW_PRIVATE_REPOS,
        )
        search = backend.search()
        results = []
        facets = {}
        if search:
            results = search[:self.max_search_results].execute()
            facets = results.facets

        serializers = {
            'project': ProjectSearchSerializer,
            'file': PageSearchSerializer,
        }
        serializer = serializers.get("file", ProjectSearchSerializer)
        results = serializer(results, many=True).data

        template_context = user_input._asdict()
        template_context.update({
            'results': results,
            'facets': facets,
            "parser": backend.parser,
            'search_query': backend.parser.query,
        })

        return render(
            request,
            'search/elastic_search.html',
            template_context,
        )
