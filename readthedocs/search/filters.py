from rest_framework import filters

from readthedocs.search.utils import get_project_slug_list_or_404


class SearchFilterBackend(filters.BaseFilterBackend):
    """
    Filter search result with project
    """

    def filter_queryset(self, request, queryset, view):
        project_slug = request.query_params.get('project')
        project_slug_list = get_project_slug_list_or_404(project_slug=project_slug,
                                                         user=request.user)
        return queryset.filter('terms', project=project_slug_list)
