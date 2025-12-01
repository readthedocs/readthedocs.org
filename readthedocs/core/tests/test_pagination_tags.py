"""Tests for the pagination template tags."""

from django.template import Context, Template
from django.test import RequestFactory, TestCase


class PaginationTagsTestCase(TestCase):
    """Test cases for the pagination template tags."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.items = list(range(1, 101))  # 100 items

    def _render_template(self, template_string, context_dict):
        """Helper to render a template with given context."""
        template = Template(template_string)
        context = Context(context_dict)
        return template.render(context)

    def test_autopaginate_basic(self):
        """Test basic autopaginate functionality."""
        request = self.factory.get("/", {"page": "1"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"
            "{% for i in items %}{{ i }} {% endfor %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # First page should show items 1-10
        self.assertIn("1 2 3 4 5 6 7 8 9 10", result)
        # Should not contain items from page 2
        self.assertNotIn("11", result)

    def test_autopaginate_second_page(self):
        """Test autopaginate on second page."""
        request = self.factory.get("/", {"page": "2"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"
            "{% for i in items %}{{ i }} {% endfor %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # Second page should show items 11-20
        self.assertIn("11 12 13 14 15 16 17 18 19 20", result)
        # Should not contain items from page 1
        self.assertNotIn(" 1 ", result)

    def test_autopaginate_sets_context_variables(self):
        """Test that autopaginate sets paginator and page_obj in context."""
        request = self.factory.get("/", {"page": "1"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"
            "{{ paginator.count }}-{{ page_obj.number }}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # Should show total count and current page number
        self.assertIn("100-1", result)

    def test_paginate_renders_controls(self):
        """Test that paginate tag renders pagination controls."""
        request = self.factory.get("/", {"page": "3"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"
            "{% paginate %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # Should contain pagination div
        self.assertIn('class="pagination"', result)
        # Should have links to pages
        self.assertIn('class="prev"', result)
        self.assertIn('class="next"', result)
        # Current page should be highlighted
        self.assertIn('class="current page"', result)

    def test_paginate_no_controls_when_not_paginated(self):
        """Test that paginate tag renders nothing when not paginated."""
        request = self.factory.get("/", {"page": "1"})
        small_items = list(range(1, 6))  # Only 5 items
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"  # More than 5 items per page
            "{% paginate %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": small_items,
                "request": request,
            },
        )
        # Should not contain pagination div (not paginated)
        self.assertNotIn('class="pagination"', result)

    def test_autopaginate_invalid_page(self):
        """Test autopaginate behavior with invalid page."""
        request = self.factory.get("/", {"page": "invalid"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"
            "{% for i in items %}{{ i }} {% endfor %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # Should fall back to page 1
        self.assertIn("1 2 3 4 5 6 7 8 9 10", result)

    def test_paginate_preserves_get_params(self):
        """Test that paginate preserves other GET parameters."""
        request = self.factory.get("/", {"page": "2", "filter": "test", "sort": "asc"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 %}"
            "{% paginate %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # Should preserve filter and sort params in links
        self.assertIn("filter=test", result)
        self.assertIn("sort=asc", result)

    def test_autopaginate_with_as_variable(self):
        """Test autopaginate with 'as' keyword to store in different variable."""
        request = self.factory.get("/", {"page": "1"})
        template_string = (
            "{% load pagination_tags %}"
            "{% autopaginate items 10 as paginated_items %}"
            "{% for i in paginated_items %}{{ i }} {% endfor %}"
        )
        result = self._render_template(
            template_string,
            {
                "items": self.items,
                "request": request,
            },
        )
        # Should work with the aliased variable
        self.assertIn("1 2 3 4 5 6 7 8 9 10", result)
