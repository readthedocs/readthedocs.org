"""Search views."""
import collections
import logging

from django.shortcuts import get_object_or_404, render
from django.views import View

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Feature, Project
from readthedocs.search.faceted_search import (
    ALL_FACETS,
    PageSearch,
    ProjectSearch,
)

from .serializers import (
    PageSearchSerializer,
    ProjectData,
    ProjectSearchSerializer,
    VersionData,
)

log = logging.getLogger(__name__)
LOG_TEMPLATE = '(Elastic Search) [%(user)s:%(type)s] [%(project)s:%(version)s:%(language)s] %(msg)s'

UserInput = collections.namedtuple(
    'UserInput',
    (
        'query',
        'type',
        'project',
        'version',
        'language',
        'role_name',
    ),
)


class SearchViewBase(View):

    http_method_names = ['get']
    max_search_results = 50

    def _search(self, user_input, use_advanced_query):
        """Return search results and facets given a `user_input` to filter by."""
        if not user_input.query:
            return [], {}

        filters = {}
        for avail_facet in ALL_FACETS:
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
            user=self.request.user,
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
            use_advanced_query=use_advanced_query,
        )

        context = self.get_serializer_context(project_obj, user_input.version)
        results = PageSearchSerializer(results, many=True, context=context).data

        template_context = user_input._asdict()
        template_context.update({
            'results': results,
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
    - project: project to filter by
    - language: project language to filter by
    - version: version to filter by
    - role_name: sphinx role to filter by
    """

    def get(self, request):
        user_input = UserInput(
            query=request.GET.get('q'),
            type=request.GET.get('type', 'project'),
            project=request.GET.get('project'),
            version=request.GET.get('version', LATEST),
            language=request.GET.get('language'),
            role_name=request.GET.get('role_name'),
        )

        results, facets = self._search(
            user_input=user_input,
            use_advanced_query=True,
        )

        serializers = {
            'project': ProjectSearchSerializer,
            'file': PageSearchSerializer,
        }
        serializer = serializers.get(user_input.type, ProjectSearchSerializer)
        results = serializer(results, many=True).data

        template_context = user_input._asdict()
        template_context.update({
            'results': results,
            'facets': facets,
        })

        return render(
            request,
            'search/elastic_search.html',
            template_context,
        )
