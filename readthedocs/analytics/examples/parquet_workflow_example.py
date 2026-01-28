"""
Example: Parquet Analytics POC Workflow

This script demonstrates the complete workflow for:
1. Exporting pageview data to Parquet
2. Querying the Parquet data
3. Analyzing the results

Usage:
    python manage.py shell < examples/parquet_workflow_example.py
"""

from datetime import date
from datetime import timedelta

from readthedocs.analytics.models import PageView
from readthedocs.analytics.parquet import ParquetAnalyticsExporter
from readthedocs.analytics.parquet import ParquetAnalyticsQuerier
from readthedocs.projects.models import Project


print("=" * 60)
print("Parquet Analytics POC - Example Workflow")
print("=" * 60)

# Step 1: Create sample data (for demonstration)
print("\n1. Creating sample pageview data...")
project = Project.objects.first()  # Use existing project
if not project:
    print("   No projects found. Create a project first.")
else:
    target_date = date(2026, 1, 15)

    # Create some sample pageviews
    sample_paths = [
        ("/docs/guide/", "200"),
        ("/docs/installation/", "200"),
        ("/docs/api/", "200"),
        ("/missing-page/", "404"),
    ]

    for path, status in sample_paths:
        PageView.objects.get_or_create(
            project=project,
            path=path,
            date=target_date,
            status=int(status),
            defaults={
                "view_count": 50 if status == "200" else 10,
            },
        )

    pageview_count = PageView.objects.filter(date=target_date).count()
    print(f"   ✓ Created {pageview_count} sample pageviews for {target_date}")

# Step 2: Export to Parquet
print("\n2. Exporting pageview data to Parquet...")
try:
    exporter = ParquetAnalyticsExporter()
    result = exporter.export_daily_pageviews(target_date)

    print(f"   ✓ Exported {result['total_records']} records")
    print(f"   ✓ Files created: {len(result['files'])}")
    for path, count in result["files"].items():
        print(f"     - {path} ({count} records)")
except Exception as e:
    print(f"   ✗ Export failed: {e}")
    import traceback

    traceback.print_exc()

# Step 3: Query from Parquet (demonstrates the interface)
print("\n3. Querying Parquet data...")
try:
    querier = ParquetAnalyticsQuerier()

    # Get top pages
    print("\n   Top pages for the project:")
    top_pages = querier.get_top_pages_from_parquet(project.slug, since=target_date, limit=5)

    if top_pages:
        for page in top_pages:
            print(f"     - {page['path']}: {page['count']} views")
    else:
        print("     (No data available - need to run export first with real data)")

    # Get daily totals
    print("\n   Daily view totals:")
    daily_data = querier.get_daily_totals_from_parquet(
        project.slug, since=target_date - timedelta(days=7)
    )

    if daily_data["labels"]:
        for label, count in zip(daily_data["labels"], daily_data["int_data"]):
            print(f"     - {label}: {count} views")
    else:
        print("     (No data available)")

except Exception as e:
    print(f"   Note: Querying may fail without S3 access: {e}")

# Step 4: Show path structure
print("\n4. S3 Path Structure:")
print("   Main export path:")
print(f"     {exporter.get_parquet_path(target_date)}")
print("\n   Per-project path:")
print(f"     {exporter.get_parquet_path(target_date, project=project.slug)}")

# Step 5: Summary
print("\n" + "=" * 60)
print("Workflow Summary:")
print("=" * 60)
print("""
The Parquet POC provides:

✓ Daily export of pageview data to S3 Parquet files
✓ Efficient querying via DuckDB (no DB load)
✓ Organized directory structure for date-based partitioning
✓ Optional per-project file separation
✓ Data deletion from PostgreSQL (optional)

Next steps:
1. Configure S3 bucket credentials
2. Schedule nightly export task via Celery Beat
3. Integrate ParquetAnalyticsQuerier into dashboard views
4. Monitor export success and performance
5. Consider data retention policies
""")
