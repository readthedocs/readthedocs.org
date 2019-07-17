import itertools
import logging
from operator import attrgetter
from pprint import pformat

from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from readthedocs.search.faceted_search import PageSearch
from readthedocs.search import utils


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
            ret = utils._remove_newlines_from_dict(highlight.to_dict())
            log.debug('API Search highlight [Page title]: %s', pformat(ret))
            return ret

    def get_inner_hits(self, obj):
        inner_hits = getattr(obj.meta, 'inner_hits', None)
        if inner_hits:
            sections = inner_hits.sections or []
            domains = inner_hits.domains or []
            all_results = itertools.chain(sections, domains)

            sorted_results = [
                {
                    'type': hit._nested.field,
                    '_source': hit._source.to_dict(),
                    'highlight': self._get_inner_hits_highlights(hit),
                }
                for hit in sorted(all_results, key=attrgetter('_score'), reverse=True)
            ]

            return sorted_results

    def _get_inner_hits_highlights(self, hit):
        """Removes new lines from highlight and log it."""
        if hasattr(hit, 'highlight'):
            highlight_dict = utils._remove_newlines_from_dict(
                hit.highlight.to_dict()
            )

            log.debug('API Search highlight: %s', pformat(highlight_dict))
            return highlight_dict
        return None


class PageSearchAPIView(generics.ListAPIView):

    """Main entry point to perform a search using Elasticsearch."""

    pagination_class = SearchPagination
    serializer_class = PageSearchSerializer

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
        kwargs['filters']['version'] = self.request.query_params.get('version')
        if not kwargs['filters']['project']:
            raise ValidationError("Unable to find a project to search")
        if not kwargs['filters']['version']:
            raise ValidationError("Unable to find a version to search")
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

        The project slug is retrieved from ``project`` query param.

        :rtype: list

        :raises: Http404 if project is not found
        """
        project_slug = self.request.query_params.get('project')
        version_slug = self.request.query_params.get('version')
        all_projects = utils.get_project_list_or_404(
            project_slug=project_slug, user=self.request.user, version_slug=version_slug,
        )
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
        version_slug = self.request.query_params.get('version')
        projects_url = {}
        for project in all_projects:
            projects_url[project.slug] = project.get_docs_url(version_slug=version_slug)
        return projects_url
