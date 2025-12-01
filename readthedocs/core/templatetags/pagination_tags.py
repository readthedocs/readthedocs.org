"""
Custom pagination template tags.

This module replaces the dj-pagination package with a custom implementation
using Django's built-in Paginator.
"""

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.template import Node, TemplateSyntaxError, Variable

register = template.Library()

# Default settings
DEFAULT_PAGINATION = getattr(settings, "PAGINATION_DEFAULT_PAGINATION", 20)
DEFAULT_ORPHANS = getattr(settings, "PAGINATION_DEFAULT_ORPHANS", 0)
DEFAULT_WINDOW = getattr(settings, "PAGINATION_DEFAULT_WINDOW", 4)
DEFAULT_MARGIN = getattr(settings, "PAGINATION_DEFAULT_MARGIN", 1)
INVALID_PAGE_RAISES_404 = getattr(settings, "PAGINATION_INVALID_PAGE_RAISES_404", False)
DISPLAY_PAGE_LINKS = getattr(settings, "PAGINATION_DISPLAY_PAGE_LINKS", True)
DISPLAY_DISABLED_PREVIOUS_LINK = getattr(
    settings, "PAGINATION_DISPLAY_DISABLED_PREVIOUS_LINK", True
)
DISPLAY_DISABLED_NEXT_LINK = getattr(
    settings, "PAGINATION_DISPLAY_DISABLED_NEXT_LINK", True
)
PREVIOUS_LINK_DECORATOR = getattr(settings, "PAGINATION_PREVIOUS_LINK_DECORATOR", "&laquo; ")
NEXT_LINK_DECORATOR = getattr(settings, "PAGINATION_NEXT_LINK_DECORATOR", " &raquo;")
DISABLE_LINK_FOR_FIRST_PAGE = getattr(
    settings, "PAGINATION_DISABLE_LINK_FOR_FIRST_PAGE", False
)


def unescape_string_literal(s):
    """
    Remove surrounding quotes from a string literal if present.

    Handles both single and double quotes.
    """
    if len(s) >= 2:
        if (s[0] == s[-1]) and s[0] in ('"', "'"):
            return s[1:-1]
    return s


def get_page_from_request(request, suffix=""):
    """
    Get the current page number from the request.

    This function extracts the page number from GET or POST parameters.
    """
    try:
        key = "page%s" % suffix
        value = request.POST.get(key)
        if value is None:
            value = request.GET.get(key)
        return int(value)
    except (KeyError, ValueError, TypeError):
        return 1


@register.tag
def autopaginate(parser, token):
    """
    Tag to paginate a queryset and set paginator/page_obj in context.

    Usage:
        {% autopaginate queryset [paginate_by] [orphans] [as context_var] %}

    Examples:
        {% autopaginate object_list %}
        {% autopaginate object_list 20 %}
        {% autopaginate object_list 20 3 %}
        {% autopaginate object_list 20 as paginated_list %}
    """
    bits = token.split_contents()
    tag_name = bits.pop(0)

    if len(bits) < 1:
        raise TemplateSyntaxError(
            "%r tag requires at least one argument: the queryset to paginate"
            % tag_name
        )

    queryset_var = bits.pop(0)
    paginate_by = None
    orphans = None
    context_var = None
    multiple_paginations = False

    # Parse remaining arguments
    i = iter(bits)
    for bit in i:
        if bit == "as":
            try:
                context_var = next(i)
            except StopIteration:
                raise TemplateSyntaxError(
                    "%r tag's 'as' argument requires a variable name" % tag_name
                )
        elif paginate_by is None:
            try:
                paginate_by = int(bit)
            except ValueError:
                paginate_by = bit
        elif orphans is None:
            try:
                orphans = int(bit)
            except ValueError:
                orphans = bit
        else:
            raise TemplateSyntaxError(
                "%r tag received too many arguments" % tag_name
            )

    return AutoPaginateNode(
        queryset_var, multiple_paginations, paginate_by, orphans, context_var
    )


class AutoPaginateNode(Node):
    """
    Node that paginates a queryset and sets context variables.

    Emits the required objects to allow for pagination:
    - paginator: The Paginator object
    - page_obj: The current Page object
    - The queryset variable is replaced with only objects for the current page
    """

    def __init__(
        self,
        queryset_var,
        multiple_paginations,
        paginate_by=None,
        orphans=None,
        context_var=None,
    ):
        if paginate_by is None:
            paginate_by = DEFAULT_PAGINATION
        if orphans is None:
            orphans = DEFAULT_ORPHANS
        self.queryset_var = Variable(queryset_var)
        if isinstance(paginate_by, int):
            self.paginate_by = paginate_by
        else:
            self.paginate_by = Variable(paginate_by)
        if isinstance(orphans, int):
            self.orphans = orphans
        else:
            self.orphans = Variable(orphans)
        self.context_var = context_var
        self.multiple_paginations = multiple_paginations

    def render(self, context):
        # Save multiple_paginations state in context
        if self.multiple_paginations and "multiple_paginations" not in context:
            context["multiple_paginations"] = True

        if context.get("multiple_paginations") or getattr(context, "paginator", None):
            page_suffix = "_%s" % self.queryset_var.var
        else:
            page_suffix = ""

        key = self.queryset_var.var
        value = self.queryset_var.resolve(context)
        if isinstance(self.paginate_by, int):
            paginate_by = self.paginate_by
        else:
            paginate_by = self.paginate_by.resolve(context)
        if isinstance(self.orphans, int):
            orphans = self.orphans
        else:
            orphans = self.orphans.resolve(context)
        paginator = Paginator(value, paginate_by, orphans)
        try:
            request = context["request"]
        except KeyError:
            raise ImproperlyConfigured(
                "You need to enable 'django.template.context_processors.request' "
                "in your TEMPLATE settings to use pagination."
            )
        try:
            page_number = get_page_from_request(request, page_suffix)
            page_obj = paginator.page(page_number)
        except InvalidPage:
            if INVALID_PAGE_RAISES_404:
                raise Http404(
                    "Invalid page requested. If DEBUG were set to "
                    "False, an HTTP 404 page would have been shown instead."
                )
            context[key] = []
            context["invalid_page"] = True
            return ""
        if self.context_var is not None:
            context[self.context_var] = page_obj.object_list
        else:
            context[key] = page_obj.object_list
        context["paginator"] = paginator
        context["page_obj"] = page_obj
        context["page_suffix"] = page_suffix
        return ""


@register.tag
def paginate(parser, token):
    """
    Tag to render pagination controls.

    Usage:
        {% paginate %}
        {% paginate using "custom_template.html" %}

    This tag renders the pagination controls for the most recent autopaginate list.
    """
    bits = token.split_contents()
    tag_name = bits.pop(0)
    template_name = None

    if len(bits) == 0:
        pass  # Use default template
    elif len(bits) == 2 and bits[0] == "using":
        template_name = unescape_string_literal(bits[1])
    else:
        raise TemplateSyntaxError(
            "Invalid syntax for %r tag. Use: {%% %s %%} or {%% %s using 'template.html' %%}"
            % (tag_name, tag_name, tag_name)
        )

    return PaginateNode(template_name)


class PaginateNode(Node):
    """Node that renders pagination controls."""

    def __init__(self, template_name=None):
        self.template_name = template_name

    def render(self, context):
        from django.template import loader

        template_list = ["pagination/pagination.html"]
        new_context = get_pagination_context(context)
        if self.template_name:
            template_list.insert(0, self.template_name)
        return loader.render_to_string(template_list, new_context)


def get_pagination_context(
    context, window=DEFAULT_WINDOW, margin=DEFAULT_MARGIN
):
    """
    Build context for pagination template.

    This function creates the context dictionary needed to render the pagination
    template, including page numbers with ellipses for gaps.
    """
    if window < 0:
        raise ValueError('Parameter "window" cannot be less than zero')
    if margin < 0:
        raise ValueError('Parameter "margin" cannot be less than zero')

    try:
        paginator = context["paginator"]
        page_obj = context["page_obj"]
        page_suffix = context.get("page_suffix", "")
        page_range = list(paginator.page_range)

        # Calculate the record range in the current page for display
        records = {"first": 1 + (page_obj.number - 1) * paginator.per_page}
        records["last"] = records["first"] + paginator.per_page - 1
        if records["last"] + paginator.orphans >= paginator.count:
            records["last"] = paginator.count

        # Figure window
        window_start = page_obj.number - window - 1
        window_end = page_obj.number + window

        # Solve if window exceeded page range
        if window_start < 0:
            window_end = window_end - window_start
            window_start = 0
        if window_end > paginator.num_pages:
            window_start = max(0, window_start - (window_end - paginator.num_pages))
            window_end = paginator.num_pages
        pages = page_range[window_start:window_end]

        # Figure margin and add ellipses
        if margin > 0 and pages:
            tmp_pages = set(pages)
            tmp_pages = tmp_pages.union(page_range[:margin])
            tmp_pages = tmp_pages.union(page_range[-margin:])
            tmp_pages = list(tmp_pages)
            tmp_pages.sort()
            if tmp_pages:
                pages = []
                pages.append(tmp_pages[0])
                for i in range(1, len(tmp_pages)):
                    # Figure gap size => add ellipses or fill in gap
                    gap = tmp_pages[i] - tmp_pages[i - 1]
                    if gap >= 3:
                        pages.append(None)
                    elif gap == 2:
                        pages.append(tmp_pages[i] - 1)
                    pages.append(tmp_pages[i])
        elif pages:
            if pages[0] != 1:
                pages.insert(0, None)
            if pages[-1] != paginator.num_pages:
                pages.append(None)

        new_context = {
            "MEDIA_URL": settings.MEDIA_URL,
            "STATIC_URL": getattr(settings, "STATIC_URL", None),
            "disable_link_for_first_page": DISABLE_LINK_FOR_FIRST_PAGE,
            "display_disabled_next_link": DISPLAY_DISABLED_NEXT_LINK,
            "display_disabled_previous_link": DISPLAY_DISABLED_PREVIOUS_LINK,
            "display_page_links": DISPLAY_PAGE_LINKS,
            "is_paginated": paginator.count > paginator.per_page,
            "next_link_decorator": NEXT_LINK_DECORATOR,
            "page_obj": page_obj,
            "page_suffix": page_suffix,
            "pages": pages,
            "paginator": paginator,
            "previous_link_decorator": PREVIOUS_LINK_DECORATOR,
            "records": records,
        }
        if "request" in context:
            new_context["request"] = context["request"]
            getvars = context["request"].GET.copy()
            if "page%s" % page_suffix in getvars:
                del getvars["page%s" % page_suffix]
            if len(getvars.keys()) > 0:
                new_context["getvars"] = "&%s" % getvars.urlencode()
            else:
                new_context["getvars"] = ""
        return new_context
    except (KeyError, AttributeError):
        return {}
