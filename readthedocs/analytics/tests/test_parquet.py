"""Tests for Parquet analytics export and querying."""

import io
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from django.utils import timezone

from readthedocs.analytics.models import PageView
from readthedocs.analytics.parquet import (
    ParquetAnalyticsExporter,
    ParquetAnalyticsQuerier,
)
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestParquetAnalyticsExporter(TestCase):
    """Test Parquet exporter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Use get_or_create to avoid UNIQUE constraint failures
        self.project, _ = Project.objects.get_or_create(
            slug="test-project",
            defaults={"name": "Test Project"},
        )
        self.version, _ = Version.objects.get_or_create(
            project=self.project,
            slug="latest",
        )

    def test_get_parquet_path_default(self):
        """Test default parquet path generation."""
        exporter = ParquetAnalyticsExporter(storage=MagicMock())
        today = timezone.now().date()
        path = exporter.get_parquet_path()

        # Should be yesterday by default
        yesterday = today - timedelta(days=1)
        expected = (
            f"analytics/pageviews/{yesterday.year:04d}"
            f"/{yesterday.month:02d}/{yesterday.day:02d}"
            f"/pageviews_{yesterday.strftime('%Y-%m-%d')}.parquet"
        )
        assert path == expected

    def test_get_parquet_path_with_date(self):
        """Test parquet path with specific date."""
        exporter = ParquetAnalyticsExporter(storage=MagicMock())
        target_date = date(2026, 1, 15)
        path = exporter.get_parquet_path(target_date)

        expected = (
            "analytics/pageviews/2026/01/15/pageviews_2026-01-15.parquet"
        )
        assert path == expected

    def test_get_parquet_path_with_project(self):
        """Test parquet path for project-specific file."""
        exporter = ParquetAnalyticsExporter(storage=MagicMock())
        target_date = date(2026, 1, 15)
        path = exporter.get_parquet_path(
            target_date,
            project="test-project",
        )

        expected = (
            "analytics/pageviews/project/test-project/2026/01/15"
            "/pageviews_2026-01-15.parquet"
        )
        assert path == expected

    def test_get_parquet_path_with_organization(self):
        """Test parquet path for organization-specific file."""
        exporter = ParquetAnalyticsExporter(storage=MagicMock())
        target_date = date(2026, 1, 15)
        path = exporter.get_parquet_path(
            target_date,
            organization="my-org",
        )

        expected = (
            "analytics/pageviews/org/my-org/2026/01/15"
            "/pageviews_2026-01-15.parquet"
        )
        assert path == expected

    def test_export_daily_pageviews_no_data(self):
        """Test export with no pageview data."""
        exporter = ParquetAnalyticsExporter(storage=MagicMock())
        target_date = date(2026, 1, 15)

        result = exporter.export_daily_pageviews(target_date)

        assert result["date"] == target_date
        assert result["total_records"] == 0
        assert result["files"] == {}

    def test_export_daily_pageviews_with_data(self):
        """Test export with pageview data."""
        target_date = date(2026, 1, 15)

        # Create some pageviews
        PageView.objects.create(
            project=self.project,
            version=self.version,
            path="/docs/guide/",
            full_path="/en/latest/docs/guide/",
            view_count=10,
            date=target_date,
            status=200,
        )
        PageView.objects.create(
            project=self.project,
            path="/missing/",
            full_path="/missing/",
            view_count=5,
            date=target_date,
            status=404,
        )

        exporter = ParquetAnalyticsExporter(storage=MagicMock())

        with patch.object(exporter, "_write_parquet_file") as mock_write:
            result = exporter.export_daily_pageviews(target_date)

        assert result["date"] == target_date
        assert result["total_records"] == 2
        assert len(result["files"]) > 0

        # Verify write was called
        assert mock_write.called

    def test_export_with_string_date(self):
        """Test export with string date input."""
        exporter = ParquetAnalyticsExporter(storage=MagicMock())

        # Create a pageview for a specific date
        target_date = date(2026, 1, 15)
        PageView.objects.create(
            project=self.project,
            version=self.version,
            path="/docs/",
            view_count=1,
            date=target_date,
            status=200,
        )

        with patch.object(exporter, "_write_parquet_file") as mock_write:
            result = exporter.export_daily_pageviews("2026-01-15")

        assert result["total_records"] == 1
        assert mock_write.called


@pytest.mark.django_db
class TestParquetAnalyticsQuerier(TestCase):
    """Test Parquet querier functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Use get_or_create to avoid UNIQUE constraint failures
        self.project, _ = Project.objects.get_or_create(
            slug="test-project",
            defaults={"name": "Test Project"},
        )
        self.version, _ = Version.objects.get_or_create(
            project=self.project,
            slug="latest",
        )

    def test_get_s3_url_with_s3_storage(self):
        """Test S3 URL generation with S3 storage."""
        storage = MagicMock()
        storage.bucket = MagicMock()
        storage.bucket.name = "my-bucket"
        storage.endpoint_url = "s3.amazonaws.com"

        querier = ParquetAnalyticsQuerier(storage=storage)
        url = querier.get_s3_url("analytics/pageviews/2026/01/15/test.parquet")

        assert url == "https://my-bucket.s3.amazonaws.com/analytics/pageviews/2026/01/15/test.parquet"

    def test_top_pages_empty_result(self):
        """Test getting top pages with no data."""
        querier = ParquetAnalyticsQuerier(storage=MagicMock())

        with patch.object(querier, "query_pageviews") as mock_query:
            import pandas as pd

            mock_query.return_value = pd.DataFrame()
            result = querier.get_top_pages_from_parquet("test-project")

        assert result == []

    def test_daily_totals_empty_result(self):
        """Test getting daily totals with no data."""
        querier = ParquetAnalyticsQuerier(storage=MagicMock())

        with patch.object(querier, "query_pageviews") as mock_query:
            import pandas as pd

            mock_query.return_value = pd.DataFrame()
            result = querier.get_daily_totals_from_parquet("test-project")

        assert result == {"labels": [], "int_data": []}


@pytest.mark.django_db
class TestParquetExportIntegration(TestCase):
    """Integration tests for the export process."""

    def setUp(self):
        """Set up test fixtures."""
        # Use get_or_create to avoid UNIQUE constraint failures
        self.project, _ = Project.objects.get_or_create(
            slug="test-project",
            defaults={"name": "Test Project"},
        )
        self.version, _ = Version.objects.get_or_create(
            project=self.project,
            slug="latest",
        )

    def test_full_export_workflow(self):
        """Test the full export and potential delete workflow."""
        target_date = date(2026, 1, 15)

        # Create pageviews
        PageView.objects.create(
            project=self.project,
            version=self.version,
            path="/docs/",
            view_count=100,
            date=target_date,
            status=200,
        )

        initial_count = PageView.objects.filter(date=target_date).count()
        assert initial_count == 1

        exporter = ParquetAnalyticsExporter(storage=MagicMock())

        with patch.object(exporter, "_write_parquet_file") as mock_write:
            result = exporter.export_daily_pageviews(target_date)

        assert result["total_records"] == 1
        assert mock_write.called

        # Verify data still exists (not auto-deleted)
        still_exists = PageView.objects.filter(date=target_date).count()
        assert still_exists == 1
