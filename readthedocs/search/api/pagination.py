from collections import namedtuple
from math import ceil

from django.utils.translation import gettext as _
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination


class PaginatorPage:
    """
    Mimics the result from a paginator.

    By using this class, we avoid having to override a lot of methods
    of `PageNumberPagination` to make it work with the ES DSL object.
    """

    def __init__(self, page_number, total_pages, count):
        self.number = page_number
        Paginator = namedtuple("Paginator", ["num_pages", "count"])
        self.paginator = Paginator(total_pages, count)

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1


class SearchPagination(PageNumberPagination):
    """Paginator for the results of PageSearch."""

    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 30

    def _get_page_number(self, number):
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            number = -1
        return number

    def paginate_queryset(self, queryset, request, view=None):
        """
        Override to get the paginated result from the ES queryset.

        This makes use of our custom paginator and slicing support from the ES DSL object,
        instead of the one used by django's ORM.

        Mostly inspired by https://github.com/encode/django-rest-framework/blob/acbd9d8222e763c7f9c7dc2de23c430c702e06d4/rest_framework/pagination.py#L191  # noqa
        """
        # Needed for other methods of this class.
        self.request = request

        page_size = self.get_page_size(request)
        page_number = request.query_params.get(self.page_query_param, 1)

        original_page_number = page_number
        page_number = self._get_page_number(page_number)

        if page_number <= 0:
            msg = self.invalid_page_message.format(
                page_number=original_page_number,
                message=_("Invalid page"),
            )
            raise NotFound(msg)

        start = (page_number - 1) * page_size
        end = page_number * page_size

        result = []
        total_count = 0
        total_pages = 1

        if queryset:
            result = queryset[start:end].execute()
            total_count = result.hits.total["value"]
            hits = max(1, total_count)
            total_pages = ceil(hits / page_size)

        if total_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        # Needed for other methods of this class.
        self.page = PaginatorPage(
            page_number=page_number,
            total_pages=total_pages,
            count=total_count,
        )

        return result
