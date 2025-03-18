"""Search views."""

import collections
from urllib.parse import urlencode

import structlog
from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from readthedocs.projects.models import Project
from readthedocs.search.api.v2.serializers import ProjectSearchSerializer
from readthedocs.search.api.v3.executor import SearchExecutor
from readthedocs.search.api.v3.serializers import PageSearchSerializer
from readthedocs.search.api.v3.utils import should_use_advanced_query
from readthedocs.search.faceted_search import ProjectSearch


log = structlog.get_logger(__name__)

UserInput = collections.namedtuple(
    "UserInput",
    (
        "query",
        "type",
        "language",
    ),
)


class ProjectSearchView(View):
    """
    Search view of the ``search`` tab.

    This redirects to the main search now.

    Query params:

    - q: search term
    """

    http_method_names = ["get"]

    def get(self, request, project_slug):
        query = request.GET.get("q", "")
        url = reverse("search") + "?" + urlencode({"q": f"project:{project_slug} {query}"})
        return HttpResponseRedirect(url)


class GlobalSearchView(TemplateView):
    """
    Global search enabled for logged out users and anyone using the dashboard.

    Query params:

    - q: search term
    - type: type of document to search (project or file)
    - language: project language to filter by (only valid if type is project)
    """

    http_method_names = ["get"]
    max_search_results = 50
    available_facets = ["language"]
    template_name = "search/elastic_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_input = UserInput(
            query=self.request.GET.get("q"),
            type=self.request.GET.get("type", "file"),
            language=self.request.GET.get("language"),
        )
        if user_input.type == "file":
            context.update(self._searh_files())
        else:
            context.update(self._search_projects(user_input, self.request))
        return context

    def _searh_files(self):
        results, facets = [], {}
        search_query = ""
        total_count = 0
        query = self.request.GET.get("q")
        if query:
            search_executor = SearchExecutor(
                request=self.request,
                query=query,
                arguments_required=False,
                default_all=not settings.ALLOW_PRIVATE_REPOS,
            )
            search_query = search_executor.parser.query
            use_advanced_query = should_use_advanced_query(search_executor.projects)
            search = search_executor.search(use_advanced_query=use_advanced_query)
            if search:
                results = search[: self.max_search_results].execute()
                facets = results.facets
                total_count = results.hits.total["value"]
                results = PageSearchSerializer(
                    results,
                    projects=search_executor.projects,
                    many=True,
                ).data

        return {
            "query": query,
            "search_query": search_query,
            "results": results,
            "facets": facets,
            "total_count": total_count,
            "type": "file",
        }

    def _search_projects(self, user_input, request):
        total_count = 0
        projects = []
        # If we allow private projects,
        # we only search on projects the user belongs or have access to.
        if settings.ALLOW_PRIVATE_REPOS:
            projects = list(Project.objects.for_user(request.user).values_list("slug", flat=True))

        # Make sure we always have projects to filter by if we allow private projects.
        if settings.ALLOW_PRIVATE_REPOS and not projects:
            results, facets = [], {}
        else:
            results, facets = self._search(
                user_input=user_input,
                projects=projects,
                use_advanced_query=True,
            )
            if results:
                total_count = results.hits.total["value"]
                results = ProjectSearchSerializer(results, many=True).data
        context = user_input._asdict()
        context.update(
            {
                "search_query": user_input.query,
                "results": results,
                "total_count": total_count,
                "facets": facets,
            }
        )
        return context

    def _search(self, *, user_input, projects, use_advanced_query):
        """Return search results and facets given a `user_input` and `projects` to filter by."""
        if not user_input.query:
            return [], {}

        filters = {}
        for avail_facet in self.available_facets:
            value = getattr(user_input, avail_facet, None)
            if value:
                filters[avail_facet] = value

        search = ProjectSearch(
            query=user_input.query,
            filters=filters,
            projects=projects,
            use_advanced_query=use_advanced_query,
        )
        # pep8 and blank don't agree on having a space before :.
        results = search[: self.max_search_results].execute()  # noqa
        facets = results.facets

        # Make sure the selected facets are displayed,
        # even when they return 0 results.
        for facet in facets:
            value = getattr(user_input, facet, None)
            if value and value not in (name for name, *_ in facets[facet]):
                facets[facet].insert(0, (value, 0, True))

        return results, facets
