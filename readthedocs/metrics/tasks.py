"""
Specific metric tasks for community.

Override the base metric tasks to add specific ones only required on community.
"""

# Disable import error because -ext is not available on pylint
# pylint: disable=import-error
from readthedocsext.monitoring.metrics.database import (
    AvgBuildTimeMetric,
    AvgBuildTriggeredAndFirstCommandTimeMetric,
    ConcurrencyLimitedBuildsMetric,
    RunningBuildsMetric,
)
from readthedocsext.monitoring.metrics.redislen import RedislenMetric
from readthedocsext.monitoring.metrics.latency import BuildLatencyMetric
from readthedocsext.monitoring.metrics.tasks import (
    Metrics1mTaskBase,
    Metrics5mTaskBase,
)


class CommunityMetrics1mTask(Metrics1mTaskBase):

    metrics = Metrics1mTaskBase.metrics + [
        RedislenMetric(queue_name='build-large'),
        RunningBuildsMetric(builder='large'),
        ConcurrencyLimitedBuildsMetric(builder='large'),
    ]


class CommunityMetrics5mTask(Metrics5mTaskBase):

    metrics = Metrics5mTaskBase.metrics + [
        AvgBuildTimeMetric(
            builder='large',
            minutes=Metrics5mTaskBase.interval,
        ),
        AvgBuildTriggeredAndFirstCommandTimeMetric(
            builder='large',
            minutes=Metrics5mTaskBase.interval,
        ),
        BuildLatencyMetric(
            project='time-test',
            queue_name='build-large',
            version='latency-test-large',
            doc='index',
            section='Time',
            doc_url=None,
            api_host='https://readthedocs.org',
            webhook_url='https://readthedocs.org/api/v2/webhook/time-test/125903/',
        ),
    ]
