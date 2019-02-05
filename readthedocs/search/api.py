import logging
from pprint import pformat

from rest_framework import generics
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from readthedocs.search.documents import PageDocument
from readthedocs.search.utils import get_project_list_or_404

log = logging.getLogger(__name__)


class SearchPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class PageSearchSerializer(serializers.Serializer):
    project = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()

    def get_link(self, obj):
        projects_url = self.context.get('projects_url')
        if projects_url:
            docs_url = projects_url[obj.project]
            return docs_url + obj.path

    def get_highlight(self, obj):
        highlight = getattr(obj.meta, 'highlight', None)
        if highlight:
            if hasattr(highlight, 'content'):
                # Change results to turn newlines in highlight into periods
                # https://github.com/rtfd/readthedocs.org/issues/5168
                highlight.content = [result.replace('\n', '. ') for result in highlight.content]
            ret = highlight.to_dict()
            log.debug('API Search highlight: %s', pformat(ret))
            return ret


class PageSearchAPIView(generics.ListAPIView):
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
        kwargs = {}
        kwargs['projects_list'] = [p.slug for p in self.get_all_projects()]
        kwargs['versions_list'] = self.request.query_params.get('version')
        user = ''
        if self.request.user.is_authenticated:
            user = self.request.user
        queryset = PageDocument.faceted_search(
            query=query, user=user, **kwargs
        )
        return queryset

    def validate_query_params(self):
        required_query_params = {'q', 'project', 'version'}  # python `set` literal is `{}`
        request_params = set(self.request.query_params.keys())
        missing_params = required_query_params - request_params
        if missing_params:
            errors = {}
            for param in missing_params:
                errors[param] = ["This query param is required"]

            raise ValidationError(errors)

    def get_serializer_context(self):
        context = super(PageSearchAPIView, self).get_serializer_context()
        context['projects_url'] = self.get_all_projects_url()
        return context

    def get_all_projects(self):
        project_slug = self.request.query_params.get('project')
        all_projects = get_project_list_or_404(project_slug=project_slug, user=self.request.user)
        return all_projects

    def get_all_projects_url(self):
        all_projects = self.get_all_projects()
        version_slug = self.request.query_params.get('version')
        projects_url = {}
        for project in all_projects:
            projects_url[project.slug] = project.get_docs_url(version_slug=version_slug)
        return projects_url
