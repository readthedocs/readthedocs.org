# Parquet Analytics POC - Quick Reference

## Files Overview

| File | Purpose | Lines |
|------|---------|-------|
| `parquet.py` | Core export/query implementation | 420 |
| `tasks.py` | Celery nightly task | +30 |
| `export_pageviews_to_parquet.py` | Management command | 70 |
| `test_parquet.py` | Test suite | 200+ |
| `PARQUET_POC.md` | Architecture & config | 300+ |
| `IMPLEMENTATION_CHECKLIST.md` | Rollout guide | 200+ |
| `TROUBLESHOOTING.md` | Debug guide | 350+ |

## One-Line Commands

```bash
# Export yesterday's data
python manage.py export_pageviews_to_parquet

# Export specific date
python manage.py export_pageviews_to_parquet --date 2026-01-15

# Export and delete from DB
python manage.py export_pageviews_to_parquet --date 2026-01-15 --delete-after-export

# Run tests
pytest readthedocs/analytics/tests/test_parquet.py -v

# Try example workflow
python manage.py shell < readthedocs/analytics/examples/parquet_workflow_example.py
```

## Code Examples

### Export Data
```python
from readthedocs.analytics.parquet import ParquetAnalyticsExporter
from datetime import date

exporter = ParquetAnalyticsExporter()
result = exporter.export_daily_pageviews(date(2026, 1, 15))
print(f"Exported {result['total_records']} records")
```

### Query Data
```python
from readthedocs.analytics.parquet import ParquetAnalyticsQuerier
from datetime import date, timedelta

querier = ParquetAnalyticsQuerier()

# Top pages
pages = querier.get_top_pages_from_parquet("my-project")

# Daily totals
daily = querier.get_daily_totals_from_parquet(
    "my-project", since=date.today() - timedelta(days=30)
)
```

### Schedule Nightly Export
```python
# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "export_pageviews_to_parquet": {
        "task": "readthedocs.analytics.tasks.export_pageviews_to_parquet",
        "schedule": crontab(hour=1, minute=0),  # 1 AM UTC
    },
}
```

## S3 Path Examples

```
# Daily export (all projects)
analytics/pageviews/2026/01/15/pageviews_2026-01-15.parquet

# Per-project export
analytics/pageviews/project/django/2026/01/15/pageviews_2026-01-15.parquet

# Per-organization export
analytics/pageviews/org/python-foundation/2026/01/15/pageviews_2026-01-15.parquet
```

## Configuration

```python
# Required: S3 storage
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_STORAGE_BUCKET_NAME = "readthedocs-analytics"
AWS_S3_REGION_NAME = "us-west-2"

# Optional: Per-project files
RTD_PARQUET_EXPORT_PER_PROJECT = True

# Optional: Analytics retention days
RTD_ANALYTICS_DEFAULT_RETENTION_DAYS = 90
```

## Database Schema (Parquet)

```
id: int64
project_id: int32
project_slug: string
version_id: int32 (nullable)
version_slug: string (nullable)
path: string
full_path: string (nullable)
view_count: int32
date: date32
status: int16
```

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| Export fails | See TROUBLESHOOTING.md → Export Issues |
| Query slow | See TROUBLESHOOTING.md → Performance Issues |
| Memory error | Set `DuckDB memory_limit` or reduce date range |
| S3 not found | Check bucket credentials, verify file uploaded |
| Data mismatch | Compare DB count with Parquet count |
| Task not running | Check Celery Beat, verify schedule, check logs |

## Key Metrics to Monitor

```python
# Export time
duration = end_time - start_time  # Target: < 5 min

# File size
file_size = os.path.getsize(parquet_path)  # Typical: 5-50MB

# Compression ratio
ratio = db_size / parquet_size  # Target: > 5x

# Query latency
latency = query_end - query_start  # Target: < 100ms
```

## Performance Targets

| Metric | Target | Unit |
|--------|--------|------|
| Nightly export duration | < 5 | minutes |
| Parquet file size (daily) | < 50 | MB |
| Compression ratio | > 5x | ratio |
| Query latency | < 100 | ms |
| Export success rate | > 99.5 | % |

## Implementation Phases

```
Phase 1 (Week 1-2): Foundation
  - Deploy core code
  - Manual testing with --date flag

Phase 2 (Week 3-4): Integration
  - Update dashboard views
  - Test with production data volume

Phase 3 (Week 5-6): Automation
  - Enable Celery Beat task
  - Monitor nightly exports

Phase 4 (Week 7-8): Migration
  - Backfill historical data
  - Switch to hybrid model
```

## Support Contacts

- **Architecture Questions**: Review PARQUET_POC.md
- **Implementation Issues**: Check IMPLEMENTATION_CHECKLIST.md
- **Runtime Errors**: See TROUBLESHOOTING.md
- **Code Issues**: Check docstrings in parquet.py
- **Testing Help**: Run test_parquet.py with -v flag

## Related Documentation

- Read the Docs Analytics Docs
- Django ORM QuerySet docs
- DuckDB SQL docs: https://duckdb.org/
- Parquet Format: https://parquet.apache.org/
- S3 Select/Range Requests: AWS S3 docs

## Version Info

- **POC Version**: 1.0
- **Django**: >= 3.2
- **Python**: >= 3.8
- **DuckDB**: >= 0.5.0
- **Pandas**: >= 1.0.0
- **PyArrow**: >= 5.0.0

## Timeline Summary

```
Setup & Review (Day 1):
  - Code review
  - Deploy to staging

Testing (Day 2-3):
  - Run test suite
  - Manual export test
  - Query validation

Backfill (Day 4-5):
  - Export last 90 days
  - Validate data integrity

Deployment (Day 6-7):
  - Enable Celery Beat
  - Monitor first exports
  - Full production rollout
```

---

For detailed information, see:
- [PARQUET_POC.md](PARQUET_POC.md) - Complete architecture
- [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Step-by-step guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problem solving
- [POC_COMPLETE.md](POC_COMPLETE.md) - Full deliverables summary
