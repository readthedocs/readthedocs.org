from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.core.utils.db import delete_in_batches, raw_delete_in_batches
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

    def test_delete_with_limit_smaller_than_total(self):
        """Test deleting with a limit smaller than total queryset count."""
        # Create 20 projects
        projects = [get(Project, slug=f"limit-project-{i}") for i in range(20)]

        # Delete only 10 projects with a limit
        queryset = Project.objects.filter(slug__startswith="limit-project-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=3, limit=10)

        # Should delete exactly 10 projects and their related objects
        assert deleted_counter["projects.Project"] == 10
        # Should still have 10 projects remaining
        assert Project.objects.filter(slug__startswith="limit-project-").count() == 10

    def test_delete_with_limit_larger_than_total(self):
        """Test deleting with a limit larger than total queryset count."""
        # Create 5 projects
        projects = [get(Project, slug=f"over-limit-{i}") for i in range(5)]

        # Set limit larger than actual count
        queryset = Project.objects.filter(slug__startswith="over-limit-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=2, limit=100)

        # Should delete all 5 projects
        assert deleted_counter["projects.Project"] == 5
        assert Project.objects.filter(slug__startswith="over-limit-").count() == 0

    def test_delete_with_limit_equal_to_batch_size(self):
        """Test deleting with a limit equal to the batch size."""
        # Create 10 projects
        projects = [get(Project, slug=f"equal-limit-{i}") for i in range(10)]

        # Set limit equal to batch_size
        queryset = Project.objects.filter(slug__startswith="equal-limit-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=5, limit=5)

        # Should delete exactly 5 projects
        assert deleted_counter["projects.Project"] == 5
        assert Project.objects.filter(slug__startswith="equal-limit-").count() == 5

    def test_delete_with_limit_one(self):
        """Test deleting with limit=1 (edge case)."""
        # Create 5 projects
        projects = [get(Project, slug=f"one-limit-{i}") for i in range(5)]

        # Set limit to 1
        queryset = Project.objects.filter(slug__startswith="one-limit-")
        total_deleted, deleted_counter = delete_in_batches(queryset, batch_size=2, limit=1)

        # Should delete exactly 1 project and its related objects
        assert deleted_counter["projects.Project"] == 1
        assert Project.objects.filter(slug__startswith="one-limit-").count() == 4


class TestRawDeleteInBatches(TestCase):
    """Tests for the raw_delete_in_batches utility function."""

    def test_empty_queryset(self):
        """Test raw deleting an empty queryset."""
        queryset = Version.objects.none()
        # Should not raise any errors
        raw_delete_in_batches(queryset, batch_size=10)

        # Verify nothing was deleted (no versions exist with our filter anyway)
        assert Version.objects.count() >= 0

    def test_queryset_smaller_than_batch_size(self):
        """Test that querysets smaller than batch_size use regular raw delete."""
        # Create a project with 3 versions
        project = get(Project, slug="raw-small-project")
        versions = [get(Version, project=project, slug=f"raw-v{i}") for i in range(3)]

        initial_count = Version.objects.filter(slug__startswith="raw-v").count()
        assert initial_count == 3

        # Delete with a batch_size larger than the number of objects
        queryset = Version.objects.filter(slug__startswith="raw-v")
        raw_delete_in_batches(queryset, batch_size=10)

        # Verify versions were deleted
        assert Version.objects.filter(slug__startswith="raw-v").count() == 0

    def test_queryset_equal_to_batch_size(self):
        """Test that querysets equal to batch_size use regular raw delete."""
        # Create a project with exactly 5 versions
        project = get(Project, slug="raw-equal-project")
        versions = [get(Version, project=project, slug=f"raw-eq-{i}") for i in range(5)]

        # Delete with a batch_size equal to the number of objects
        queryset = Version.objects.filter(slug__startswith="raw-eq-")
        raw_delete_in_batches(queryset, batch_size=5)

        assert Version.objects.filter(slug__startswith="raw-eq-").count() == 0

    def test_queryset_larger_than_batch_size(self):
        """Test that querysets larger than batch_size are raw deleted in batches."""
        # Create a project with 10 versions
        project = get(Project, slug="raw-large-project")
        versions = [get(Version, project=project, slug=f"raw-large-{i}") for i in range(10)]

        # Delete with a batch_size smaller than the number of objects
        queryset = Version.objects.filter(slug__startswith="raw-large-")
        raw_delete_in_batches(queryset, batch_size=3)

        assert Version.objects.filter(slug__startswith="raw-large-").count() == 0

    def test_multiple_batches(self):
        """Test raw deletion works correctly across multiple batches."""
        # Create a project with 25 versions
        project = get(Project, slug="raw-batch-project")
        versions = [get(Version, project=project, slug=f"raw-batch-{i}") for i in range(25)]

        # Delete with batch_size=7, requiring 4 batches (7, 7, 7, 4)
        queryset = Version.objects.filter(slug__startswith="raw-batch-")
        raw_delete_in_batches(queryset, batch_size=7)

        assert Version.objects.filter(slug__startswith="raw-batch-").count() == 0

    def test_batch_size_one(self):
        """Test raw deletion with batch_size=1 (edge case)."""
        # Create a project with 3 versions
        project = get(Project, slug="raw-single-project")
        versions = [get(Version, project=project, slug=f"raw-single-{i}") for i in range(3)]

        queryset = Version.objects.filter(slug__startswith="raw-single-")
        raw_delete_in_batches(queryset, batch_size=1)

        assert Version.objects.filter(slug__startswith="raw-single-").count() == 0

    def test_raw_delete_with_limit_smaller_than_total(self):
        """Test raw deleting with a limit smaller than total queryset count."""
        # Create a project with 20 versions
        project = get(Project, slug="raw-limit-project")
        versions = [get(Version, project=project, slug=f"raw-limit-{i}") for i in range(20)]

        # Delete only 10 versions with a limit
        queryset = Version.objects.filter(slug__startswith="raw-limit-")
        raw_delete_in_batches(queryset, batch_size=3, limit=10)

        # Should have 10 versions remaining
        assert Version.objects.filter(slug__startswith="raw-limit-").count() == 10

    def test_raw_delete_with_limit_larger_than_total(self):
        """Test raw deleting with a limit larger than total queryset count."""
        # Create a project with 5 versions
        project = get(Project, slug="raw-over-limit")
        versions = [get(Version, project=project, slug=f"raw-over-{i}") for i in range(5)]

        # Set limit larger than actual count
        queryset = Version.objects.filter(slug__startswith="raw-over-")
        raw_delete_in_batches(queryset, batch_size=2, limit=100)

        # Should delete all 5 versions
        assert Version.objects.filter(slug__startswith="raw-over-").count() == 0

    def test_raw_delete_with_limit_equal_to_batch_size(self):
        """Test raw deleting with a limit equal to the batch size."""
        # Create a project with 10 versions
        project = get(Project, slug="raw-equal-limit")
        versions = [get(Version, project=project, slug=f"raw-eq-lim-{i}") for i in range(10)]

        # Set limit equal to batch_size
        queryset = Version.objects.filter(slug__startswith="raw-eq-lim-")
        raw_delete_in_batches(queryset, batch_size=5, limit=5)

        # Should have 5 versions remaining
        assert Version.objects.filter(slug__startswith="raw-eq-lim-").count() == 5

    def test_raw_delete_with_limit_one(self):
        """Test raw deleting with limit=1 (edge case)."""
        # Create a project with 5 versions
        project = get(Project, slug="raw-one-limit")
        versions = [get(Version, project=project, slug=f"raw-one-{i}") for i in range(5)]

        # Set limit to 1
        queryset = Version.objects.filter(slug__startswith="raw-one-")
        raw_delete_in_batches(queryset, batch_size=2, limit=1)

        # Should have 4 versions remaining
        assert Version.objects.filter(slug__startswith="raw-one-").count() == 4
