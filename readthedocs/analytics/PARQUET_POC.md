# Parquet Analytics Configuration Guide

## Overview

This POC implements a system for exporting Read the Docs pageview analytics to Parquet files stored on S3, enabling efficient analytical queries without impacting the production database.

## Architecture

### Components

1. **ParquetAnalyticsExporter** (`readthedocs/analytics/parquet.py`)
   - Exports pageview data from PostgreSQL to Parquet files on S3
   - Supports daily exports with optional per-project/organization splits
   - Stores data with date-based directory structure for easy partitioning

2. **ParquetAnalyticsQuerier** (`readthedocs/analytics/parquet.py`)
   - Queries Parquet files using DuckDB
   - Provides efficient aggregations and filtering
   - Supports wildcard queries for date ranges

3. **Celery Task** (`readthedocs/analytics/tasks.py`)
   - `export_pageviews_to_parquet()` - Nightly export task
   - Can be scheduled to run daily after midnight

4. **Management Command** (`readthedocs/analytics/management/commands/export_pageviews_to_parquet.py`)
   - Manual export tool for backfilling data
   - Supports per-project exports
   - Optional deletion after successful export

## Configuration

Add to your Django settings:

```python
# Optional: Enable per-project Parquet files
RTD_PARQUET_EXPORT_PER_PROJECT = True

# S3/Storage configuration
AWS_STORAGE_BUCKET_NAME = "readthedocs-analytics"
AWS_S3_REGION_NAME = "us-west-2"
```

## Usage

### Manual Export

```bash
# Export yesterday's data
python manage.py export_pageviews_to_parquet

# Export specific date
python manage.py export_pageviews_to_parquet --date 2026-01-15

# Export and delete from database
python manage.py export_pageviews_to_parquet --date 2026-01-15 --delete-after-export

# Also create per-project files
python manage.py export_pageviews_to_parquet --per-project
```

### Celery Task

Configure in your celery beat schedule:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "export_pageviews_to_parquet": {
        "task": "readthedocs.analytics.tasks.export_pageviews_to_parquet",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM UTC
    },
}
```

### Using in Code

```python
from readthedocs.analytics.parquet import ParquetAnalyticsQuerier

# Query data from parquet files
querier = ParquetAnalyticsQuerier()

# Get top pages for a project
top_pages = querier.get_top_pages_from_parquet(
    project_slug="my-project",
    since=date(2026, 1, 1),
    limit=10,
)

# Get daily totals
daily_data = querier.get_daily_totals_from_parquet(
    project_slug="my-project",
    since=date(2026, 1, 1),
)
```

## Data Flow

### Daily Export Process

```
1. Nightly Task (1 AM UTC):
   - Queries pageview data for previous day
   - Converts to Parquet format
   - Uploads to S3
   - (Optional) Deletes from PostgreSQL

2. Storage Structure:
   analytics/pageviews/2026/01/15/pageviews_2026-01-15.parquet
   analytics/pageviews/project/{slug}/2026/01/15/pageviews_2026-01-15.parquet

3. Querying:
   - DuckDB uses S3 range requests to efficiently fetch data
   - No full file download needed
   - Results cached in DataFrame for processing
```

## Performance Characteristics

### Advantages

- **Database Load**: 0% impact on production PostgreSQL
- **Query Speed**: Analytical queries via DuckDB are nearly instant
- **Storage Efficiency**: Parquet compression (snappy) ~10x better than CSV
- **Cost**: S3 storage is much cheaper than PostgreSQL for historical data
- **Scalability**: Easily handles millions of daily pageviews

### Trade-offs

- **Latency**: Historical queries have 1-day lag (querying yesterday's data)
- **Real-time**: Current day data still in PostgreSQL
- **Freshness**: S3 eventual consistency (typically <1s, rarely >10s)

## Testing

Run tests:

```bash
pytest readthedocs/analytics/tests/test_parquet.py
```

## Migration Strategy

### Phase 1: Export Only
- Run nightly exports without deletion
- Validate data integrity in Parquet files
- Monitor export success rate

### Phase 2: Hybrid Model
- Export daily data
- Keep in PostgreSQL for 7 days (for real-time dashboards)
- Archive older data, delete from database

### Phase 3: Full Parquet Analytics
- All pageview queries use Parquet files
- PostgreSQL only keeps current day data
- Significant database load reduction

## S3 Path Reference

### Main Daily File
```
analytics/pageviews/{YYYY}/{MM}/{DD}/pageviews_{YYYY-MM-DD}.parquet
```

### Per-Project Files
```
analytics/pageviews/project/{project_slug}/{YYYY}/{MM}/{DD}/pageviews_{YYYY-MM-DD}.parquet
```

### Per-Organization Files
```
analytics/pageviews/org/{org_slug}/{YYYY}/{MM}/{DD}/pageviews_{YYYY-MM-DD}.parquet
```

## Parquet Schema

| Column | Type | Description |
|--------|------|-------------|
| id | int64 | PageView record ID |
| project_id | int32 | Project FK |
| project_slug | string | Project slug |
| version_id | int32 | Version FK (nullable) |
| version_slug | string | Version slug (nullable) |
| path | string | Normalized path |
| full_path | string | Full path with version |
| view_count | int32 | Number of views |
| date | date32 | Date of views |
| status | int16 | HTTP status code |

## Future Enhancements

1. **Per-Organization Exports**: Reduce data per query
2. **Incremental Updates**: Support real-time updates to Parquet files
3. **Edge Distribution**: Serve Parquet files from CDN via Lambda
4. **Compression Tuning**: Experiment with different compression algorithms
5. **Data Retention**: Automatic deletion of old Parquet files
6. **Analytics Views**: Direct integration with analytics dashboard
7. **Client Data Access**: Direct Parquet file URLs for large clients

## Dependencies

- pandas: Data manipulation
- duckdb: Querying Parquet files
- pyarrow: Parquet format support
- boto3: S3 interaction (via django-storages)
