"""Search views."""
import collections

import structlog
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views import View
from readthedocs.search.api.v3.backend import Backend

from readthedocs.projects.models import Feature, Project
from readthedocs.search.api.v2.serializers import (
    ProjectSearchSerializer,
)
from readthedocs.search.api.v3.serializers import PageSearchSerializer
from readthedocs.search.faceted_search import PageSearch, ProjectSearch

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
    available_facets = ["language"]

    def _search(self, *, user_input, projects, use_advanced_query):
        """Return search results and facets given a `user_input` and `projects` to filter by."""
        if not user_input.query:
            return [], {}

        filters = {}
        for avail_facet in self.available_facets:
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

    def get(self, request, project_slug):
        project_obj = self._get_project(project_slug)
        use_advanced_query = not project_obj.has_feature(
            Feature.DEFAULT_TO_FUZZY_SEARCH,
        )

        user_input = UserInput(
            query=request.GET.get('q'),
            type='file',
            language=None,
        )

        results, facets = self._search(
            user_input=user_input,
            projects=[project_slug],
            use_advanced_query=use_advanced_query,
        )

        results = PageSearchSerializer(results, many=True).data

        template_context = user_input._asdict()
        template_context.update({
            "search_query": user_input.query,
            'results': results,
            "total_count": len(results),
            'facets': facets,
            'project_obj': project_obj,
        })

        return render(
            request,
            'search/elastic_search.html',
            template_context,
        )


class GlobalSearchView(SearchViewBase):

    """
    Global search enabled for logged out users and anyone using the dashboard.

    Query params:

    - q: search term
    - type: type of document to search (project or file)
    - language: project language to filter by (only valid if type is project)
    """

    def get(self, request):
        user_input = UserInput(
            query=request.GET.get('q'),
            type=request.GET.get('type', 'project'),
            language=request.GET.get('language'),
        )
        if user_input.type == "file":
            return self._searh_files()
        return self._search_projects(user_input, request)

    def _searh_files(self):
        results, facets = [], {}
        search_query = ""
        query = self.request.GET.get("q")
        if query:
            backend = Backend(
                request=self.request,
                query=query,
                allow_search_all=not settings.ALLOW_PRIVATE_REPOS,
            )
            search_query = backend.parser.query
            search = backend.search()
            if search:
                results = search[:self.max_search_results].execute()
                facets = results.facets
                results = PageSearchSerializer(results, projects=backend.projects, many=True).data

        return render(
            self.request,
            'search/elastic_search.html',
            {
                "query": query,
                "search_query": search_query,
                "results": results,
                "facets": facets,
                "total_count": len(results),
                "type": "file",
            },
        )


    def _search_projects(self, user_input, request):
        projects = []
        # If we allow private projects,
        # we only search on projects the user belongs or have access to.
        if settings.ALLOW_PRIVATE_REPOS:
            projects = list(
                Project.objects.for_user(request.user)
                .values_list('slug', flat=True)
            )

        # Make sure we always have projects to filter by if we allow private projects.
        if settings.ALLOW_PRIVATE_REPOS and not projects:
            results, facets = [], {}
        else:
            results, facets = self._search(
                user_input=user_input,
                projects=projects,
                use_advanced_query=True,
            )

        results = ProjectSearchSerializer(results, many=True).data
        template_context = user_input._asdict()
        template_context.update({
            "search_query": user_input.query,
            'results': results,
            "total_count": len(results),
            'facets': facets,
        })

        return render(
            request,
            'search/elastic_search.html',
            template_context,
        )
