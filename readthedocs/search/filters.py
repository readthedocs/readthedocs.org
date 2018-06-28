from rest_framework import filters

from readthedocs.search.utils import get_project_slug_list_or_404


class SearchFilterBackend(filters.BaseFilterBackend):

    """Filter search result with project"""

    def filter_queryset(self, request, es_search, view):
        """Overwrite the method to compatible with Elasticsearch DSL Search object."""
        project_slug = request.query_params.get('project')
        version_slug = request.query_params.get('version')
        project_slug_list = get_project_slug_list_or_404(project_slug=project_slug,
                                                         user=request.user)
        # Elasticsearch ``terms`` query can take multiple values as list,
        # while ``term`` query takes single value.
        filtered_es_search = (es_search.filter('terms', project=project_slug_list)
                                       .filter('term', version=version_slug))
        return filtered_es_search
