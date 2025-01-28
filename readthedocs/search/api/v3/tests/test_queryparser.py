from django.test import TestCase

from readthedocs.search.api.v3.queryparser import SearchQueryParser


class TestQueryParser(TestCase):
    def test_no_arguments(self):
        parser = SearchQueryParser("search query")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], [])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "")
        self.assertEqual(parser.query, "search query")

    def test_project_arguments(self):
        parser = SearchQueryParser("project:foo query")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], ["foo"])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "")
        self.assertEqual(parser.query, "query")

    def test_multiple_project_arguments(self):
        parser = SearchQueryParser("project:foo query project:bar")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], ["foo", "bar"])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "")
        self.assertEqual(parser.query, "query")

    def test_user_argument(self):
        parser = SearchQueryParser("query user:foo")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], [])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "foo")
        self.assertEqual(parser.query, "query")

    def test_multiple_user_arguments(self):
        parser = SearchQueryParser("search user:foo query user:bar")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], [])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "bar")
        self.assertEqual(parser.query, "search query")

    def test_subprojects_argument(self):
        parser = SearchQueryParser("search subprojects:foo query ")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], [])
        self.assertEqual(arguments["subprojects"], ["foo"])
        self.assertEqual(arguments["user"], "")
        self.assertEqual(parser.query, "search query")

    def test_multiple_subprojects_arguments(self):
        parser = SearchQueryParser("search subprojects:foo query  subprojects:bar")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], [])
        self.assertEqual(arguments["subprojects"], ["foo", "bar"])
        self.assertEqual(arguments["user"], "")
        self.assertEqual(parser.query, "search query")

    def test_escaped_argument(self):
        parser = SearchQueryParser(r"project\:foo project:bar query")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], ["bar"])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "")
        self.assertEqual(parser.query, "project:foo query")

    def test_only_arguments(self):
        parser = SearchQueryParser(r"project:foo user:bar")
        parser.parse()
        arguments = parser.arguments
        self.assertEqual(arguments["project"], ["foo"])
        self.assertEqual(arguments["subprojects"], [])
        self.assertEqual(arguments["user"], "bar")
        self.assertEqual(parser.query, "")
