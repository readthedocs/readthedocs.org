"""Parquet file handling for analytics data."""

import io
import logging
from datetime import date
from datetime import timedelta

import duckdb
import pandas as pd
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


class ParquetAnalyticsExporter:
    """Export pageview analytics data to Parquet files."""

    def __init__(self, storage=None):
        """
        Initialize the exporter.

        :param storage: Django storage backend (defaults to default storage)
        """
        if storage is None:
            from django.core.files.storage import default_storage

            storage = default_storage
        self.storage = storage

    def get_parquet_path(self, target_date=None, organization=None, project=None):
        """
        Get the S3 key for a parquet file.

        :param target_date: The date for the parquet file (defaults to yesterday)
        :param organization: Optional organization slug for org-specific files
        :param project: Optional project slug for project-specific files
        :return: S3 key path
        """
        if target_date is None:
            target_date = timezone.now().date() - timedelta(days=1)

        if not isinstance(target_date, date):
            target_date = timezone.now().date() - timedelta(days=1)

        # Build path: analytics/pageviews/YYYY/MM/DD/pageviews_YYYY-MM-DD.parquet
        # or: analytics/pageviews/org/{slug}/YYYY/MM/DD/pageviews_YYYY-MM-DD.parquet
        # or: analytics/pageviews/project/{slug}/YYYY/MM/DD/pageviews_YYYY-MM-DD.parquet
        base_path = "analytics/pageviews"

        if organization:
            base_path = f"{base_path}/org/{organization}"
        elif project:
            base_path = f"{base_path}/project/{project}"

        year = target_date.strftime("%Y")
        month = target_date.strftime("%m")
        day = target_date.strftime("%d")
        date_str = target_date.strftime("%Y-%m-%d")

        return f"{base_path}/{year}/{month}/{day}/pageviews_{date_str}.parquet"

    def export_daily_pageviews(self, target_date=None):
        """
        Export pageview data for a specific day to Parquet.

        Exports all pageviews for the given date, organized by organization/project.

        :param target_date: The date to export (defaults to yesterday)
        :return: dict with export results: {
            'date': date,
            'total_records': int,
            'files': {path: record_count, ...}
        }
        """
        if target_date is None:
            target_date = timezone.now().date() - timedelta(days=1)

        if isinstance(target_date, str):
            from django.utils.dateparse import parse_date

            target_date = parse_date(target_date)

        from readthedocs.analytics.models import PageView

        # Get all pageviews for the target date
        queryset = PageView.objects.filter(date=target_date).select_related(
            "project",
            "version",
        )

        if not queryset.exists():
            logger.info(f"No pageviews found for {target_date}")
            return {
                "date": target_date,
                "total_records": 0,
                "files": {},
            }

        # Convert to DataFrame
        data = list(
            queryset.values(
                "id",
                "project__id",
                "project__slug",
                "version__id",
                "version__slug",
                "path",
                "full_path",
                "view_count",
                "date",
                "status",
            )
        )

        df = pd.DataFrame(data)

        # Rename columns to remove double underscores
        df.rename(
            columns={
                "project__id": "project_id",
                "project__slug": "project_slug",
                "version__id": "version_id",
                "version__slug": "version_slug",
            },
            inplace=True,
        )

        # Export to main file (all data)
        main_path = self.get_parquet_path(target_date)
        self._write_parquet_file(df, main_path)

        result = {
            "date": target_date,
            "total_records": len(df),
            "files": {main_path: len(df)},
        }

        # Optionally export per-project files
        if getattr(settings, "RTD_PARQUET_EXPORT_PER_PROJECT", False):
            for project_slug in df["project_slug"].unique():
                project_df = df[df["project_slug"] == project_slug]
                project_path = self.get_parquet_path(
                    target_date,
                    project=project_slug,
                )
                self._write_parquet_file(project_df, project_path)
                result["files"][project_path] = len(project_df)

        logger.info(
            f"Exported pageviews for {target_date}: {len(df)} records to {len(result['files'])} files"
        )

        return result

    def _write_parquet_file(self, df, path):
        """
        Write a DataFrame to Parquet format in storage.

        :param df: pandas DataFrame
        :param path: Storage path/key
        """
        # Write DataFrame to in-memory bytes buffer
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, compression="snappy")
        buffer.seek(0)

        # Save to storage
        self.storage.save(path, buffer)
        logger.debug(f"Wrote parquet file: {path}")


class ParquetAnalyticsQuerier:
    """Query pageview analytics data from Parquet files."""

    def __init__(self, storage=None):
        """
        Initialize the querier.

        :param storage: Django storage backend (defaults to default storage)
        """
        if storage is None:
            from django.core.files.storage import default_storage

            storage = default_storage
        self.storage = storage

    def get_s3_url(self, path):
        """Get the full S3 URL for a parquet file."""
        # For S3, construct the URL
        if hasattr(self.storage, "bucket"):
            # boto3/S3 storage
            bucket = self.storage.bucket.name
            endpoint = getattr(self.storage, "endpoint_url", "s3.amazonaws.com")
            return f"https://{bucket}.{endpoint}/{path}"
        else:
            # Fallback to storage URL method
            return self.storage.url(path)

    def query_pageviews(self, project_slug, since=None, until=None):
        """
        Query pageviews for a project from Parquet files.

        :param project_slug: Project slug
        :param since: Start date (defaults to 30 days ago)
        :param until: End date (defaults to today)
        :return: DataFrame with query results
        """
        if since is None:
            since = timezone.now().date() - timedelta(days=30)
        if until is None:
            until = timezone.now().date()

        # Build S3 paths for the date range with wildcards
        # This allows DuckDB to fetch multiple files efficiently
        base_path = "analytics/pageviews/project"
        pattern = f"{base_path}/{project_slug}/*/*/*/pageviews_*.parquet"

        s3_url = self.get_s3_url(pattern)

        try:
            # Use DuckDB to query the parquet files
            conn = duckdb.connect()
            query = f"""
            SELECT
                id,
                project_id,
                project_slug,
                version_id,
                version_slug,
                path,
                full_path,
                view_count,
                date,
                status
            FROM read_parquet('{s3_url}')
            WHERE date >= '{since}' AND date <= '{until}'
            ORDER BY date DESC
            """
            result = conn.execute(query).fetchdf()
            return result
        except Exception as e:
            logger.error(f"Error querying parquet files: {e}")
            raise

    def get_top_pages_from_parquet(self, project_slug, since=None, limit=10, status=200):
        """
        Get top pages from parquet files.

        :param project_slug: Project slug
        :param since: Start date
        :param limit: Number of results
        :param status: HTTP status code to filter on
        :return: list of dicts with path and count
        """
        df = self.query_pageviews(project_slug, since=since)

        if df.empty:
            return []

        # Filter by status
        df = df[df["status"] == status]

        # Group by path and sum view counts
        grouped = df.groupby("path")["view_count"].sum().reset_index()
        grouped.columns = ["path", "count"]

        # Sort by count and limit
        result = grouped.sort_values("count", ascending=False).head(limit)

        return result.to_dict("records")

    def get_daily_totals_from_parquet(self, project_slug, since=None, status=200):
        """
        Get daily view totals from parquet files.

        :param project_slug: Project slug
        :param since: Start date
        :param status: HTTP status code to filter on
        :return: dict with labels and int_data for chart
        """
        df = self.query_pageviews(project_slug, since=since)

        if df.empty:
            return {"labels": [], "int_data": []}

        # Filter by status
        df = df[df["status"] == status]

        # Group by date and sum view counts
        daily = df.groupby("date")["view_count"].sum().reset_index()
        daily.columns = ["date", "count"]
        daily = daily.sort_values("date")

        # Convert to labels and data
        labels = [d.strftime("%d %b") for d in daily["date"]]
        int_data = daily["count"].tolist()

        return {
            "labels": labels,
            "int_data": int_data,
        }
