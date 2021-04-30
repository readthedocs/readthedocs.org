"""Search views."""
import collections
import logging

from django.conf import settings
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


class SearchView(View):

    """
    Global user search on the dashboard.

    This is for both the main search and project search.

    :param project_slug: Sent when the view is a project search
    """

    http_method_names = ['get']
    max_search_results = 50

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

    def get(self, request, project_slug=None):
        request_type = None
        use_advanced_query = True
        project_obj = None
        if project_slug:
            project_obj = self._get_project(project_slug)
            use_advanced_query = not project_obj.has_feature(
                Feature.DEFAULT_TO_FUZZY_SEARCH,
            )
            request_type = request.GET.get('type', 'file')

        version_slug = request.GET.get('version', LATEST)

        user_input = UserInput(
            query=request.GET.get('q'),
            type=request_type or request.GET.get('type', 'project'),
            project=project_slug or request.GET.get('project'),
            version=version_slug,
            language=request.GET.get('language'),
            role_name=request.GET.get('role_name'),
        )
        results = []
        facets = {}

        projects = []
        # If we allow private projects,
        # we only filter by the projects the user belongs or have access to.
        if settings.ALLOW_PRIVATE_REPOS:
            if project_obj:
                projects = [project_obj.slug]
            else:
                projects = list(
                    Project.objects.for_user(request.user)
                    .values_list('slug', flat=True)
                )

        if (
            user_input.query
            # Allow to filter by any project if we don't allow private projects.
            and (settings.ALLOW_PRIVATE_REPOS and projects or  not settings.ALLOW_PRIVATE_REPOS)
        ):
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
                projects=projects,
                use_advanced_query=use_advanced_query,
            )
            results = search[:self.max_search_results].execute()
            facets = results.facets

            log.info(
                LOG_TEMPLATE,
                {
                    'user': request.user,
                    'project': user_input.project or '',
                    'type': user_input.type or '',
                    'version': user_input.version or '',
                    'language': user_input.language or '',
                    'msg': user_input.query or '',
                }
            )

        # Make sure our selected facets are displayed even when they return 0 results
        for facet in facets:
            value = getattr(user_input, facet, None)
            if value and value not in (val[0] for val in facets[facet]):
                facets[facet].insert(0, (value, 0, True))

        serializers = {
            'project': ProjectSearchSerializer,
            'file': PageSearchSerializer,
        }
        serializer = serializers.get(user_input.type, ProjectSearchSerializer)
        if project_obj:
            context = self.get_serializer_context(project_obj, version_slug)
        else:
            context = {}
        results = serializer(results, many=True, context=context).data

        template_vars = user_input._asdict()
        template_vars.update({
            'results': results,
            'facets': facets,
        })

        if project_obj:
            template_vars.update({'project_obj': project_obj})

        return render(
            request,
            'search/elastic_search.html',
            template_vars,
        )
