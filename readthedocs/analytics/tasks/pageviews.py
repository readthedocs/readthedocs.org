import structlog
from celery import shared_task

from readthedocs.analytics.models import PageView


log = structlog.get_logger(__name__)


@shared_task(queue="web")
def delete_project_pageviews(project_slug):
    """
    Delete all PageView objects for a given project slug.
    """
    count, _ = PageView.objects.filter(project__slug=project_slug).delete()
    log.info("Deleted PageViews for project", project_slug=project_slug, count=count)
