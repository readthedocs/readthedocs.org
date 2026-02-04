"""Tests for search integration with project groups."""

import pytest
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.models import Group
from readthedocs.search.api.v3.executor import SearchExecutor
from readthedocs.search.api.v3.queryparser import SearchQueryParser


@pytest.mark.django_db
class TestGroupSearchQueryParser(TestCase):
    """Test search query parser with project_group parameter."""

    def test_parse_project_group_argument(self):
        """Test that project_group argument is parsed correctly."""
        parser = SearchQueryParser("test query project_group:my-group")
        parser.parse()

        assert parser.query == "test query"
        assert "my-group" in parser.arguments["project_group"]

    def test_parse_multiple_project_groups(self):
        """Test parsing multiple project_group arguments."""
        parser = SearchQueryParser(
            "test query project_group:group1 project_group:group2"
        )
        parser.parse()

        assert parser.query == "test query"
        assert "group1" in parser.arguments["project_group"]
        assert "group2" in parser.arguments["project_group"]
        assert len(parser.arguments["project_group"]) == 2

    def test_project_group_with_other_arguments(self):
        """Test project_group combined with other arguments."""
        parser = SearchQueryParser(
            "test query project:myproject project_group:my-group"
        )
        parser.parse()

        assert parser.query == "test query"
        assert "myproject" in parser.arguments["project"]
        assert "my-group" in parser.arguments["project_group"]


@pytest.mark.django_db
class TestGroupSearchExecutor(TestCase):
    """Test search executor with project groups."""

    def setUp(self):
        """Set up test data."""
        # Create projects
        self.project1 = get(
            Project,
            slug="project1",
            name="Project 1",
            privacy_level="public",
        )
        self.project2 = get(
            Project,
            slug="project2",
            name="Project 2",
            privacy_level="public",
        )
        self.project3 = get(
            Project,
            slug="project3",
            name="Project 3",
            privacy_level="public",
        )

        # Create versions for each project
        self.version1 = get(
            Version,
            project=self.project1,
            slug="latest",
            active=True,
            built=True,
            privacy_level="public",
        )
        self.version2 = get(
            Version,
            project=self.project2,
            slug="latest",
            active=True,
            built=True,
            privacy_level="public",
        )
        self.version3 = get(
            Version,
            project=self.project3,
            slug="latest",
            active=True,
            built=True,
            privacy_level="public",
        )

        # Create project group
        self.group = Group.objects.create(
            name="Test Group",
            slug="test-group",
        )
        self.group.projects.add(self.project1, self.project2)

    def test_search_executor_with_project_group(self):
        """Test that search executor includes projects from group."""
        from unittest.mock import Mock

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        executor = SearchExecutor(
            request=request,
            query="test project_group:test-group",
        )

        projects = list(executor.projects)
        project_slugs = [project.slug for project, version in projects]

        assert "project1" in project_slugs
        assert "project2" in project_slugs
        # project3 should not be in the results
        assert "project3" not in project_slugs

    def test_search_executor_with_nonexistent_group(self):
        """Test that search executor handles nonexistent groups gracefully."""
        from unittest.mock import Mock

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        executor = SearchExecutor(
            request=request,
            query="test project_group:nonexistent-group",
        )

        projects = list(executor.projects)
        # Should return empty list for nonexistent group
        assert len(projects) == 0

    def test_search_executor_multiple_groups(self):
        """Test search executor with multiple project groups."""
        from unittest.mock import Mock

        # Create another group with project3
        group2 = Group.objects.create(
            name="Test Group 2",
            slug="test-group-2",
        )
        group2.projects.add(self.project3)

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        executor = SearchExecutor(
            request=request,
            query="test project_group:test-group project_group:test-group-2",
        )

        projects = list(executor.projects)
        project_slugs = [project.slug for project, version in projects]

        # All three projects should be in results
        assert "project1" in project_slugs
        assert "project2" in project_slugs
        assert "project3" in project_slugs

    def test_search_executor_combined_filters(self):
        """Test search executor with project_group and project filters."""
        from unittest.mock import Mock

        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        executor = SearchExecutor(
            request=request,
            query="test project_group:test-group project:project3",
        )

        projects = list(executor.projects)
        project_slugs = [project.slug for project, version in projects]

        # Should include projects from group and explicit project
        assert "project1" in project_slugs
        assert "project2" in project_slugs
        assert "project3" in project_slugs
