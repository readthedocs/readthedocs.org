"""Pagination helpers for dashboard views."""

from django.core.paginator import Paginator


# Number of objects shown per page in dashboard lists.
PAGINATE_BY = 15


def paginate(request, queryset, per_page=PAGINATE_BY):
    """
    Paginate ``queryset`` using the ``page`` query parameter of ``request``.

    List views should set ``paginate_by`` instead. This is for lists rendered
    by views that don't paginate them on their own, like related objects on a
    detail view. An out of range page returns the last page.
    """
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))
