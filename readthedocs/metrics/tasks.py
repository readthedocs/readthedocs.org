"""
Specific metric tasks for community.

Override the base metric tasks to add specific ones only required on community.
"""

# Disable import error because -ext is not available on pylint
# pylint: disable=import-error
from readthedocsext.monitoring.metrics.database import AvgBuildTimeMetric
from readthedocsext.monitoring.metrics.database import AvgBuildTriggeredAndFirstCommandTimeMetric
from readthedocsext.monitoring.metrics.database import ConcurrencyLimitedBuildsMetric
from readthedocsext.monitoring.metrics.database import RunningBuildsMetric
from readthedocsext.monitoring.metrics.latency import BuildLatencyMetric
from readthedocsext.monitoring.metrics.redislen import RedislenMetric
from readthedocsext.monitoring.metrics.tasks import Metrics1mTaskBase
from readthedocsext.monitoring.metrics.tasks import Metrics5mTaskBase


class CommunityMetrics1mTask(Metrics1mTaskBase):
    metrics = Metrics1mTaskBase.metrics + [
        RedislenMetric(queue_name="build-large"),
        RunningBuildsMetric(builder="large"),
        ConcurrencyLimitedBuildsMetric(builder="large"),
    ]


class CommunityMetrics5mTask(Metrics5mTaskBase):
    metrics = Metrics5mTaskBase.metrics + [
        AvgBuildTimeMetric(
            builder="large",
            minutes=Metrics5mTaskBase.interval,
        ),
        AvgBuildTriggeredAndFirstCommandTimeMetric(
            builder="large",
            minutes=Metrics5mTaskBase.interval,
        ),
        BuildLatencyMetric(
            project="time-test",
            queue_name="build-default",
            version="latency-test",
            doc_url="https://time-test.readthedocs.io/en/latency-test/",
            webhook_url="{api_host}/api/v2/webhook/{project}/{webhook_id}/",
        ),
    ]
