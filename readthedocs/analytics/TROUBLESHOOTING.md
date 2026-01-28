# Parquet Analytics POC - Troubleshooting Guide

## Common Issues and Solutions

### Export Issues

#### Export fails with "No pageviews found"
**Symptom**: Export completes but creates no files
**Cause**: No pageview data for the target date
**Solution**:
```bash
# Check if pageviews exist for target date
python manage.py shell
>>> from readthedocs.analytics.models import PageView
>>> from datetime import date
>>> PageView.objects.filter(date=date(2026, 1, 15)).count()
```

#### Export fails with S3 permission error
**Symptom**: `ClientError: An error occurred (403) when calling the PutObject operation`
**Cause**: S3 bucket permissions not configured
**Solution**:
```python
# Verify S3 credentials in settings
# Check IAM policy includes s3:PutObject on target bucket
# Test with:
from django.core.files.storage import default_storage
default_storage.save('test-key', b'test data')
```

#### Export fails with "Storage not configured"
**Symptom**: `AttributeError: No storage configured`
**Cause**: Default storage backend not set
**Solution**:
```python
# In settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-west-2'
```

#### Parquet file is too large
**Symptom**: S3 upload takes > 10 minutes, high memory usage
**Cause**: Too much data for single Parquet file
**Solution**:
```python
# Enable per-project exports to split data
RTD_PARQUET_EXPORT_PER_PROJECT = True

# Or manually split by date range
python manage.py export_pageviews_to_parquet --date 2026-01-15
```

### Query Issues

#### DuckDB query fails with "File not found"
**Symptom**: `ParquetException: Unable to open file for reading`
**Cause**:
- Parquet file not uploaded yet
- Wrong S3 path or bucket
- S3 eventual consistency delay

**Solution**:
```bash
# Verify file exists
aws s3 ls s3://your-bucket/analytics/pageviews/

# Wait for S3 consistency (usually < 1 second)
time.sleep(5)

# Check S3 endpoint and credentials
aws s3 ls --endpoint-url https://your-custom-endpoint
```

#### DuckDB runs out of memory
**Symptom**: `MemoryError: Unable to allocate memory`
**Cause**: Large date range or many columns selected
**Solution**:
```python
# DuckDB default memory config for servers:
import duckdb
conn = duckdb.connect()
conn.execute("PRAGMA memory_limit='4GB'")
conn.execute("PRAGMA threads=4")

# Or limit query time range
since = date(2026, 1, 15)  # Don't query months of data
```

#### Query returns wrong results
**Symptom**: Count doesn't match expected, missing records
**Cause**:
- Data not exported yet
- Date filtering issues
- DataFrame aggregation errors

**Solution**:
```python
# Verify data was exported
from readthedocs.analytics.parquet import ParquetAnalyticsExporter
exporter = ParquetAnalyticsExporter()
result = exporter.export_daily_pageviews(date(2026, 1, 15))
print(f"Exported {result['total_records']} records")

# Compare with PostgreSQL
from readthedocs.analytics.models import PageView
db_count = PageView.objects.filter(date=date(2026, 1, 15)).count()
print(f"Database has {db_count} records")
```

### Performance Issues

#### Export takes too long (> 15 minutes)
**Symptom**: Management command hangs during export
**Cause**:
- Large number of pageviews (> 10M/day)
- Slow S3 connection
- CPU bottleneck

**Solution**:
```python
# Increase Parquet batch size
df.to_parquet(buffer, compression='snappy', row_group_size=1000000)

# Or use faster compression
df.to_parquet(buffer, compression='lz4')

# Monitor export progress
python manage.py export_pageviews_to_parquet --verbosity 3
```

#### Query latency is high (> 1 second)
**Symptom**: `ParquetAnalyticsQuerier.query_pageviews()` takes long
**Cause**:
- Querying large date range
- S3 network latency
- DuckDB optimization needed

**Solution**:
```python
# Reduce date range
since = date.today() - timedelta(days=90)  # Don't query 1+ years

# Add column filtering
query = """
SELECT path, SUM(view_count) as count
FROM read_parquet(...)
WHERE date >= '2026-01-15'
GROUP BY path
ORDER BY count DESC
LIMIT 10
"""

# Use caching
from django.views.decorators.cache import cache_page
@cache_page(3600)  # Cache for 1 hour
def get_analytics(request):
    ...
```

#### S3 costs are high
**Symptom**: Unexpected AWS charges
**Cause**:
- Many query requests
- Inefficient wildcard patterns
- No lifecycle policies

**Solution**:
```python
# Optimize queries to reduce requests
# Use date-based partitioning instead of wildcards
path = f"analytics/pageviews/2026/01/15/pageviews_2026-01-15.parquet"

# Set S3 lifecycle policies
# Delete files > 365 days old
# Move to Glacier > 90 days old

# Enable S3 caching headers
from django.core.files.storage import default_storage
storage.save(path, content, content_type='application/octet-stream')
```

### Data Issues

#### Missing pageviews in Parquet
**Symptom**: Some records don't appear in Parquet but exist in PostgreSQL
**Cause**:
- Selective export
- Data filtering in export
- Concurrent deletes

**Solution**:
```python
# Verify all data is exported
from readthedocs.analytics.models import PageView
target_date = date(2026, 1, 15)
db_count = PageView.objects.filter(date=target_date).count()

# Check export log
from readthedocs.analytics.parquet import ParquetAnalyticsExporter
result = ParquetAnalyticsExporter().export_daily_pageviews(target_date)
parquet_count = result['total_records']

if db_count != parquet_count:
    # Investigate discrepancy
    ...
```

#### Parquet file is corrupted
**Symptom**: `ParquetException: Column data type does not match`
**Cause**:
- Partial upload
- Concurrent writes
- Python version mismatch

**Solution**:
```bash
# Verify file integrity
python -c "import pandas as pd; df = pd.read_parquet('s3://...')"

# Re-export the file
python manage.py export_pageviews_to_parquet --date 2026-01-15

# Check for concurrent processes
ps aux | grep export_pageviews
```

### Celery Task Issues

#### Task never runs
**Symptom**: Celery Beat scheduled task doesn't execute
**Cause**:
- Celery Beat not running
- Task not registered
- Schedule not configured

**Solution**:
```bash
# Verify Celery Beat is running
ps aux | grep celery beat

# Check task registration
celery -A readthedocs.celery inspect registered

# Manual task execution for testing
python manage.py shell
>>> from readthedocs.analytics.tasks import export_pageviews_to_parquet
>>> result = export_pageviews_to_parquet.apply()
>>> result.get()
```

#### Task fails silently
**Symptom**: Celery task appears to run but produces no output
**Cause**: Exception in task not logged
**Solution**:
```python
# Enable task result tracking
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Check task results
celery -A readthedocs.celery events

# Enable task logging
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes

# Or run task directly
python manage.py export_pageviews_to_parquet --date 2026-01-15
```

#### Memory grows during export
**Symptom**: Process memory increases to GB during task
**Cause**:
- Large DataFrame in memory
- DuckDB memory settings
- Pandas chunking not used

**Solution**:
```python
# Export in chunks
batch_size = 100000
offset = 0
while True:
    batch = PageView.objects.filter(date=date).all()[offset:offset + batch_size]
    if not batch.exists():
        break
    # Process batch
    offset += batch_size
```

## Debugging Tips

### Enable verbose logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'readthedocs.analytics': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Check export logs
```bash
# Django logs
grep "Exported pageviews" /var/log/readthedocs.log

# Celery logs
tail -f /var/log/celery/worker.log
```

### Profile export performance
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

from readthedocs.analytics.tasks import export_pageviews_to_parquet
export_pageviews_to_parquet()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Test in isolation
```bash
# Test export only
python manage.py export_pageviews_to_parquet --date 2026-01-15

# Test query only
python manage.py shell
>>> from readthedocs.analytics.parquet import ParquetAnalyticsQuerier
>>> querier = ParquetAnalyticsQuerier()
>>> df = querier.query_pageviews('my-project', since=date(2026, 1, 1))
>>> print(df.head())
```

## Getting Help

1. Check logs for error messages
2. Review this troubleshooting guide
3. Check [PARQUET_POC.md](PARQUET_POC.md) for configuration
4. Enable debug logging and retry
5. Contact the Read the Docs team
