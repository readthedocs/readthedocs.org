"""
Management command to export pageview data to Parquet files and archive.

Usage:
    python manage.py export_pageviews_to_parquet --date 2026-01-27
    python manage.py export_pageviews_to_parquet  # Defaults to yesterday
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date

from readthedocs.analytics.models import PageView
from readthedocs.analytics.parquet import ParquetAnalyticsExporter


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Export pageview data to Parquet files and optionally delete from database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Date to export (YYYY-MM-DD). Defaults to yesterday.",
        )
        parser.add_argument(
            "--delete-after-export",
            action="store_true",
            default=False,
            help="Delete pageview data after successful export",
        )
        parser.add_argument(
            "--per-project",
            action="store_true",
            default=False,
            help="Also export per-project Parquet files",
        )

    def handle(self, *args, **options):
        # Parse the date
        if options["date"]:
            target_date = parse_date(options["date"])
            if not target_date:
                self.stderr.write(self.style.ERROR(f"Invalid date format: {options['date']}"))
                return
        else:
            target_date = timezone.now().date() - timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"Exporting pageviews for {target_date}..."))

        try:
            exporter = ParquetAnalyticsExporter()

            # Export to Parquet
            result = exporter.export_daily_pageviews(target_date)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Exported {result['total_records']} records to {len(result['files'])} file(s)"
                )
            )

            for path, count in result["files"].items():
                self.stdout.write(f"  - {path} ({count} records)")

            # Delete from database if requested
            if options["delete_after_export"]:
                qs = PageView.objects.filter(date=target_date)
                count = qs.count()
                qs._raw_delete(qs.db)
                self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count} records from database"))

            self.stdout.write(self.style.SUCCESS("Export completed successfully!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Export failed: {e}"))
            raise
