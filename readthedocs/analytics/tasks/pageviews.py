import structlog

from readthedocs.analytics.models import PageView
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue="web")
def delete_project_pageviews(project_slug, version_slug=None):
    """
    Delete all PageView objects for a given project slug, or a specific version if version_slug is provided.
    """
    queryset = PageView.objects.filter(project__slug=project_slug)
    if version_slug is not None:
        queryset = queryset.filter(version__slug=version_slug)
    count, _ = queryset.delete()
    log.info(
        "Deleted PageViews for project",
        project_slug=project_slug,
        version_slug=version_slug,
        count=count,
    )
