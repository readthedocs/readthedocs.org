"""Tasks to keep the edge redirect store in sync with the database."""

import structlog
from django.conf import settings

from readthedocs.redirects.edge import get_edge_store
from readthedocs.redirects.edge import remove_project
from readthedocs.redirects.edge import sync_project
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@app.task(queue="web")
def sync_project_to_edge(project_pk):
    """Replicate a project's routing config and redirects to the edge."""
    if not settings.RTD_EDGE_REDIRECTS_ENABLED:
        return

    # Imported here to avoid a circular import at module load time.
    from readthedocs.projects.models import Project

    project = Project.objects.filter(pk=project_pk).first()
    if not project:
        log.debug("Project not found, skipping edge sync.", project_pk=project_pk)
        return
    sync_project(project)


@app.task(queue="web")
def remove_project_from_edge(slug, hosts):
    """Remove a project and its hosts from the edge store."""
    if not settings.RTD_EDGE_REDIRECTS_ENABLED:
        return
    remove_project(slug, hosts)


@app.task(queue="web")
def remove_domain_from_edge(host):
    """Drop a single host mapping from the edge store."""
    if not settings.RTD_EDGE_REDIRECTS_ENABLED:
        return
    get_edge_store().delete_domain(host)
