"""Tests for Group model and search integration."""

import pytest
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.projects.models import Project
from readthedocs.projects.models import Group
from readthedocs.projects.models import ProjectRelationship


@pytest.mark.django_db
class TestGroup(TestCase):
    """Test Group model."""

    def test_create_group(self):
        """Test creating a group."""
        group = Group.objects.create(
            name="Test Group",
            slug="test-group",
        )
        assert group.name == "Test Group"
        assert group.slug == "test-group"
        assert group.projects.count() == 0

    def test_add_projects_to_group(self):
        """Test adding projects to a group."""
        group = Group.objects.create(
            name="Test Group",
            slug="test-group",
        )
        project1 = get(Project, slug="project1", name="Project 1")
        project2 = get(Project, slug="project2", name="Project 2")

        group.projects.add(project1, project2)

        assert group.projects.count() == 2
        assert project1 in group.projects.all()
        assert project2 in group.projects.all()

    def test_get_project_slugs(self):
        """Test getting project slugs from a group."""
        group = Group.objects.create(
            name="Test Group",
            slug="test-group",
        )
        project1 = get(Project, slug="project1", name="Project 1")
        project2 = get(Project, slug="project2", name="Project 2")

        group.projects.add(project1, project2)

        slugs = group.get_project_slugs()
        assert "project1" in slugs
        assert "project2" in slugs
        assert len(slugs) == 2


@pytest.mark.django_db
class TestGroupSignals(TestCase):
    """Test automatic group creation via signals."""

    def test_subproject_creates_group(self):
        """Test that creating a subproject relationship creates a group."""
        parent = get(Project, slug="parent-project", name="Parent Project")
        child = get(Project, slug="child-project", name="Child Project")

        # Create subproject relationship
        ProjectRelationship.objects.create(
            parent=parent,
            child=child,
        )

        # Check that a group was created
        group_slug = f"{parent.slug}-subprojects"
        group = Group.objects.filter(slug=group_slug).first()

        assert group is not None
        assert group.name == f"{parent.name} - Subprojects"
        assert parent in group.projects.all()
        assert child in group.projects.all()

    def test_translation_creates_group(self):
        """Test that setting a main_language_project creates a group."""
        main_project = get(Project, slug="main-project", name="Main Project")
        translation = get(
            Project,
            slug="translation-project",
            name="Translation Project",
            main_language_project=main_project,
        )

        # Check that a group was created
        group_slug = f"{main_project.slug}-translations"
        group = Group.objects.filter(slug=group_slug).first()

        assert group is not None
        assert group.name == f"{main_project.name} - Translations"
        assert main_project in group.projects.all()
        assert translation in group.projects.all()

    def test_multiple_subprojects_same_group(self):
        """Test that multiple subprojects are added to the same group."""
        parent = get(Project, slug="parent-project", name="Parent Project")
        child1 = get(Project, slug="child-project-1", name="Child Project 1")
        child2 = get(Project, slug="child-project-2", name="Child Project 2")

        # Create first subproject relationship
        ProjectRelationship.objects.create(parent=parent, child=child1)

        # Create second subproject relationship
        ProjectRelationship.objects.create(parent=parent, child=child2)

        # Check that both are in the same group
        group_slug = f"{parent.slug}-subprojects"
        group = Group.objects.get(slug=group_slug)

        assert group.projects.count() == 3  # parent + 2 children
        assert parent in group.projects.all()
        assert child1 in group.projects.all()
        assert child2 in group.projects.all()


@pytest.mark.django_db
class TestGroupAdmin(TestCase):
    """Test Group admin interface."""

    def test_group_str(self):
        """Test string representation of Group."""
        group = Group.objects.create(
            name="Test Group",
            slug="test-group",
        )
        assert str(group) == "Test Group"

    def test_group_ordering(self):
        """Test that groups are ordered by name."""
        group_b = Group.objects.create(name="B Group", slug="b-group")
        group_a = Group.objects.create(name="A Group", slug="a-group")
        group_c = Group.objects.create(name="C Group", slug="c-group")

        groups = list(Group.objects.all())
        assert groups[0] == group_a
        assert groups[1] == group_b
        assert groups[2] == group_c
