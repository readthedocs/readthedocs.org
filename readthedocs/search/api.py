from rest_framework import generics
from rest_framework.exceptions import ValidationError

from readthedocs.search.documents import PageDocument
from readthedocs.search.filters import SearchFilterBackend
from readthedocs.search.pagination import SearchPagination
from readthedocs.search.serializers import PageSearchSerializer
from readthedocs.search.utils import get_project_list_or_404


class PageSearchAPIView(generics.ListAPIView):
    pagination_class = SearchPagination
    filter_backends = [SearchFilterBackend]
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
        queryset = PageDocument.simple_search(query=query)
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

    def get_all_projects_url(self):
        version_slug = self.request.query_params.get('version')
        project_slug = self.request.query_params.get('project')
        all_projects = get_project_list_or_404(project_slug=project_slug, user=self.request.user)
        projects_url = {}

        for project in all_projects:
            projects_url[project.slug] = project.get_docs_url(version_slug=version_slug)

        return projects_url
