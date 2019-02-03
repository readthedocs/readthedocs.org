from rest_framework import filters


class SearchFilterBackend(filters.BaseFilterBackend):

    """Filter search result with project"""

    def filter_queryset(self, request, queryset, view):
        """Overwrite the method to compatible with Elasticsearch DSL Search object."""
        # ``queryset`` is actually a Elasticsearch DSL ``Search`` object.
        # So change the variable name
        es_search = queryset
        version_slug = request.query_params.get('version')
        projects_info = view.get_all_projects_url()
        project_slug_list = list(projects_info.keys())
        # Elasticsearch ``terms`` query can take multiple values as list,
        # while ``term`` query takes single value.
        filtered_es_search = (es_search.filter('terms', project=project_slug_list)
                                       .filter('term', version=version_slug))
        return filtered_es_search
