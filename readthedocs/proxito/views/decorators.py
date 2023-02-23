from functools import wraps

import structlog
from django.db.models import Q

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
        # Something not entirely clear is happening when unpacking args and kwargs
        # so the project is fetched from kwarg dictionary.
        project = kwargs["project"]
        if subproject is None and subproject_slug:
            # Try to fetch by subproject alias first, otherwise we might end up
            # redirected to an unrelated project.
            # Depends on a project passed into kwargs
            rel = (
                ProjectRelationship.objects.filter(parent=project)
                .filter(Q(alias=subproject_slug) | Q(child__slug=subproject_slug))
                .first()
            )
            if rel:
                subproject = rel.child
            else:
                log.warning(
                    "The slug is not subproject of project.",
                    subproject_slug=subproject_slug,
                    project_slug=project.slug,
                    project=project,
                )
                raise ProxitoSubProjectHttp404(
                    "Invalid subproject slug",
                    project_slug=project.slug,
                    project=project,
                    subproject_slug=subproject_slug,
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
            # Get the project from the request if it can't be found in the URL
            unresolved_domain = request.unresolved_domain
            if unresolved_domain and not project_slug:
                log.debug(
                    'Inserting project slug from request.',
                    project_slug=project_slug,
                )
                project = unresolved_domain.project
            elif project_slug:
                try:
                    project = Project.objects.get(slug=project_slug)
                except Project.DoesNotExist:
                    log.debug(f"No project found with slug {project_slug}")
                    raise ProxitoProjectHttp404(
                        "Project does not exist.", project_slug=project_slug
                    )
        return view_func(request, project=project, *args, **kwargs)

    return inner_view
