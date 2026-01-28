# Parquet Analytics POC - Implementation Checklist

## Phase 1: Foundation Setup ✓

- [x] Create `ParquetAnalyticsExporter` class
  - [x] Daily export to Parquet files
  - [x] Configurable S3 path structure
  - [x] Support for per-project/per-organization splits
  - [x] Error handling and logging

- [x] Create `ParquetAnalyticsQuerier` class
  - [x] DuckDB integration
  - [x] S3 range request support
  - [x] DataFrame results
  - [x] Helper methods for common queries

- [x] Create management command
  - [x] Manual export with date selection
  - [x] Optional deletion after export
  - [x] Progress reporting

- [x] Create Celery task
  - [x] `export_pageviews_to_parquet()` daily task
  - [x] Error handling and retry logic
  - [x] Task result tracking

- [x] Create comprehensive tests
  - [x] Exporter path generation
  - [x] Export with/without data
  - [x] Querier interface
  - [x] Integration tests

## Phase 2: Dashboard Integration

- [ ] Update analytics dashboard views
  - [ ] Replace `PageView.top_viewed_pages()` with `ParquetAnalyticsQuerier.get_top_pages_from_parquet()`
  - [ ] Replace `PageView.page_views_by_date()` with `ParquetAnalyticsQuerier.get_daily_totals_from_parquet()`
  - [ ] Add fallback to PostgreSQL for current-day data
  - [ ] Add caching layer

- [ ] Create hybrid query layer
  - [ ] Query recent data (< 7 days) from PostgreSQL
  - [ ] Query historical data (> 7 days) from Parquet
  - [ ] Combine results for date ranges spanning both sources

- [ ] Performance testing
  - [ ] Benchmark Parquet queries vs PostgreSQL
  - [ ] Test with production data volume
  - [ ] Monitor S3 costs

## Phase 3: Data Migration

- [ ] Backfill historical data
  ```bash
  # Export last N days of data
  for i in {30..1}; do
    python manage.py export_pageviews_to_parquet --date "2026-01-$(printf '%02d' $i)"
  done
  ```

- [ ] Validate data integrity
  - [ ] Record counts match between PostgreSQL and Parquet
  - [ ] Sum of views match
  - [ ] Query results match

- [ ] Set retention policy
  - [ ] Keep 7 days in PostgreSQL (hot data)
  - [ ] Archive > 7 days to Parquet
  - [ ] Delete from PostgreSQL after X days

## Phase 4: Automation Setup

- [ ] Configure Celery Beat schedule
  ```python
  CELERY_BEAT_SCHEDULE = {
      "export_pageviews_to_parquet": {
          "task": "readthedocs.analytics.tasks.export_pageviews_to_parquet",
          "schedule": crontab(hour=1, minute=0),  # 1 AM UTC daily
      },
  }
  ```

- [ ] Set up monitoring/alerting
  - [ ] Track export success/failure
  - [ ] Monitor S3 upload duration
  - [ ] Alert on failed exports

- [ ] Configure data retention
  ```python
  # Schedule deletion of old PageView records
  CELERY_BEAT_SCHEDULE = {
      "delete_old_page_counts": {
          "task": "readthedocs.analytics.tasks.delete_old_page_counts",
          "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
      },
  }
  ```

## Testing Checklist

- [x] Unit tests written
- [ ] Integration tests in staging
- [ ] Load tests with production volume
- [ ] Query accuracy validation
- [ ] Error handling under load
- [ ] S3 credential/permission testing

## Deployment Checklist

- [ ] Code review and approval
- [ ] Migrations applied (if any)
- [ ] Dependencies installed
  ```bash
  pip install duckdb pandas pyarrow
  ```

- [ ] Configuration added to settings
  ```python
  RTD_PARQUET_EXPORT_PER_PROJECT = False
  CELERY_BEAT_SCHEDULE = {...}
  ```

- [ ] Celery Beat configured and running
- [ ] S3 bucket created with proper permissions
- [ ] IAM roles updated for EC2/containers
- [ ] Monitoring and alerting configured

- [ ] Rollout plan
  - [ ] Dry run on staging
  - [ ] Monitor first day's exports
  - [ ] Validate data integrity
  - [ ] Enable for production

## Rollback Plan

If issues occur:

1. Stop Celery Beat task: `export_pageviews_to_parquet`
2. Revert code changes
3. Verify PageView data is still being collected in PostgreSQL
4. Investigate and fix issues

No data loss since exports are read-only and don't affect PostgreSQL data by default.

## Success Criteria

- [ ] Daily export completes in < 5 minutes
- [ ] Parquet files are < 50% of PostgreSQL storage size
- [ ] Query latency < 100ms for typical date ranges
- [ ] Export success rate > 99.5%
- [ ] No impact on production database performance
- [ ] Dashboard queries show accurate data

## Monitoring Queries

### Database size comparison
```sql
-- PostgreSQL size
SELECT
    pg_size_pretty(pg_table_size('analytics_pageview')) as table_size,
    COUNT(*) as record_count
FROM analytics_pageview;
```

### Daily pageviews
```python
from readthedocs.analytics.models import PageView
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
count = PageView.objects.filter(date=today).count()
print(f"Today's pageviews: {count}")
```

## Performance Metrics to Track

1. **Export metrics**
   - Duration (target: < 5 minutes)
   - Record count per day
   - File sizes
   - S3 upload bandwidth

2. **Query metrics**
   - Query latency
   - Data retrieved per query
   - S3 range request efficiency

3. **Storage metrics**
   - S3 storage cost
   - Database size trend
   - Compression ratio

## Future Enhancements

- [ ] Real-time Parquet updates using S3 Select
- [ ] DuckDB view for direct PostgreSQL→Parquet queries
- [ ] Automated data retention/deletion
- [ ] Per-organization isolated exports
- [ ] Encryption at rest for S3 files
- [ ] CloudFront distribution for global access

## Documentation

- [x] PARQUET_POC.md - Architecture and configuration
- [x] This checklist
- [x] Example workflow script
- [x] Code comments and docstrings
- [ ] Team documentation/wiki
- [ ] Runbook for troubleshooting
- [ ] Capacity planning guide
