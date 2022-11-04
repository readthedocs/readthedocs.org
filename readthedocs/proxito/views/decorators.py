from functools import wraps

import structlog

from readthedocs.projects.models import Project, ProjectRelationship
from readthedocs.proxito.exceptions import (
    ProxitoProjectHttp404,
    ProxitoSubProjectHttp404,
)

log = structlog.get_logger(__name__)  # noqa


def map_subproject_slug(view_func):
    """
    A decorator that maps a ``subproject_slug`` URL param into a Project.

    :raises: Http404 if the Project doesn't exist

    .. warning:: Does not take into account any kind of privacy settings.
    """

    @wraps(view_func)
    def inner_view(  # noqa
            request, subproject=None, subproject_slug=None, *args, **kwargs
    ):
        if subproject is None and subproject_slug:
            # Try to fetch by subproject alias first, otherwise we might end up
            # redirected to an unrelated project.
            # Depends on a project passed into kwargs
            rel = ProjectRelationship.objects.filter(
                parent=kwargs['project'],
                alias=subproject_slug,
            ).first()
            if rel:
                subproject = rel.child
            else:
                rel = ProjectRelationship.objects.filter(
                    parent=kwargs['project'],
                    child__slug=subproject_slug,
                ).first()
                if rel:
                    subproject = rel.child
                else:
                    log.warning(
                        'The slug is not subproject of project.',
                        subproject_slug=subproject_slug,
                        project_slug=kwargs['project'].slug,
                    )
                    raise ProxitoSubProjectHttp404(
                        "Invalid subproject slug", subproject_slug=subproject_slug
                    )
        return view_func(request, subproject=subproject, *args, **kwargs)

    return inner_view


def map_project_slug(view_func):
    """
    A decorator that maps a ``project_slug`` URL param into a Project.

    :raises: Http404 if the Project doesn't exist

    .. warning:: Does not take into account any kind of privacy settings.
    """

    @wraps(view_func)
    def inner_view(  # noqa
            request, project=None, project_slug=None, *args, **kwargs
    ):
        if project is None:
            # Get a slug from the request if it can't be found in the URL
            if not project_slug:
                project_slug = getattr(request, 'host_project_slug', None)
                log.debug(
                    'Inserting project slug from request.',
                    project_slug=project_slug,
                )
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                log.debug(
                    "Project not found.",
                    project_slug=project_slug,
                )
                raise ProxitoProjectHttp404(
                    "Project does not exist.", project_slug=project_slug
                )
        return view_func(request, project=project, *args, **kwargs)

    return inner_view
