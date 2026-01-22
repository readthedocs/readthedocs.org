from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.core.utils.db import delete_in_batches
from readthedocs.projects.models import Project


class TestDeleteInBatches(TestCase):
    """Tests for the delete_in_batches utility function."""

    def test_empty_queryset(self):
        """Test deleting an empty queryset returns 0 deleted objects."""
        queryset = Project.objects.none()
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=10)

        assert total_deleted == 0
        assert deleted_counter == {}

    def test_queryset_smaller_than_batch_size(self):
        """Test that querysets smaller than batch_size use regular delete."""
        # Create 3 projects
        projects = [get(Project, slug=f"project-{i}") for i in range(3)]

        # Delete with a batch_size larger than the number of objects
        queryset = Project.objects.filter(slug__startswith="project-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=10)

        # Verify projects were deleted
        assert deleted_counter["projects.Project"] == 3
        # Verify related versions were also deleted (at least 1 per project)
        assert "builds.Version" in deleted_counter
        assert deleted_counter["builds.Version"] >= 3
        # Verify total includes all projects and related objects
        assert total_deleted >= 6  # At least 3 projects + at least 3 versions
        assert Project.objects.filter(slug__startswith="project-").count() == 0

    def test_queryset_equal_to_batch_size(self):
        """Test that querysets equal to batch_size use regular delete."""
        # Create exactly 5 projects
        projects = [get(Project, slug=f"project-{i}") for i in range(5)]

        # Delete with a batch_size equal to the number of objects
        queryset = Project.objects.filter(slug__startswith="project-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=5)

        assert total_deleted >= 5
        assert deleted_counter["projects.Project"] == 5
        assert Project.objects.filter(slug__startswith="project-").count() == 0

    def test_queryset_larger_than_batch_size(self):
        """Test that querysets larger than batch_size are deleted in batches."""
        # Create 10 projects
        projects = [get(Project, slug=f"project-{i}") for i in range(10)]

        # Delete with a batch_size smaller than the number of objects
        queryset = Project.objects.filter(slug__startswith="project-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=3)

        assert total_deleted >= 10
        assert deleted_counter["projects.Project"] == 10
        assert Project.objects.filter(slug__startswith="project-").count() == 0

    def test_deletion_with_related_objects(self):
        """Test that related objects are deleted correctly (cascade)."""
        # Create projects with versions
        project = get(Project, slug="test-project")
        # Versions are created automatically, but let's create additional ones
        version1 = get(Version, project=project, slug="v1.0")
        version2 = get(Version, project=project, slug="v2.0")

        initial_version_count = Version.objects.filter(project=project).count()
        assert initial_version_count >= 3  # At least 1 auto-created + 2 we created

        # Delete the project
        queryset = Project.objects.filter(slug="test-project")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=1)

        # Verify project is deleted
        assert Project.objects.filter(slug="test-project").count() == 0

        # Verify all related versions are also deleted
        assert Version.objects.filter(project=project).count() == 0

        # Verify the deletion counter includes both projects and versions
        assert deleted_counter["projects.Project"] == 1
        assert deleted_counter["builds.Version"] >= 3

    def test_multiple_batches(self):
        """Test deletion works correctly across multiple batches."""
        # Create 25 projects
        projects = [get(Project, slug=f"batch-project-{i}") for i in range(25)]

        # Delete with batch_size=7, requiring 4 batches (7, 7, 7, 4)
        queryset = Project.objects.filter(slug__startswith="batch-project-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=7)

        assert deleted_counter["projects.Project"] == 25
        assert Project.objects.filter(slug__startswith="batch-project-").count() == 0

    def test_batch_size_one(self):
        """Test deletion with batch_size=1 (edge case)."""
        # Create 3 projects
        projects = [get(Project, slug=f"single-{i}") for i in range(3)]

        queryset = Project.objects.filter(slug__startswith="single-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=1)

        assert deleted_counter["projects.Project"] == 3
        assert Project.objects.filter(slug__startswith="single-").count() == 0

    def test_versions_deletion_in_batches(self):
        """Test deleting versions directly (not through project cascade)."""
        # Create a project with multiple versions
        project = get(Project, slug="version-test")
        versions = [get(Version, project=project, slug=f"v{i}.0") for i in range(10)]

        # Delete versions in batches
        queryset = Version.objects.filter(project=project, slug__startswith="v")
        initial_count = queryset.count()
        assert initial_count == 10

        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=3)

        assert deleted_counter["builds.Version"] == 10
        assert Version.objects.filter(project=project, slug__startswith="v").count() == 0

        # The project should still exist
        assert Project.objects.filter(slug="version-test").count() == 1
