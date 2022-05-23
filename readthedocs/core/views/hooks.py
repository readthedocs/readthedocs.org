"""Views pertaining to builds."""

import structlog

from readthedocs.builds.constants import (
    EXTERNAL,
    EXTERNAL_VERSION_STATE_CLOSED,
    EXTERNAL_VERSION_STATE_OPEN,
)
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Feature, Project
from readthedocs.projects.tasks.builds import sync_repository_task

log = structlog.get_logger(__name__)


def _build_version(project, slug, already_built=()):
    """
    Where we actually trigger builds for a project and slug.

    All webhook logic should route here to call ``trigger_build``.
    """
    if not project.has_valid_webhook:
        project.has_valid_webhook = True
        project.save()
    # Previously we were building the latest version (inactive or active)
    # when building the default version,
    # some users may have relied on this to update the version list #4450
    version = project.versions.filter(active=True, slug=slug).first()
    if version and slug not in already_built:
        log.info(
            'Building.',
            project_slug=project.slug,
            version_slug=version.slug,
        )
        trigger_build(project=project, version=version)
        return slug

    log.info('Not building.', version_slug=slug)
    return None


def build_branches(project, branch_list):
    """
    Build the branches for a specific project.

    Returns:
        to_build - a list of branches that were built
        not_building - a list of branches that we won't build
    """
    to_build = set()
    not_building = set()
    for branch in branch_list:
        versions = project.versions_from_branch_name(branch)

        for version in versions:
            log.debug(
                'Processing.',
                project_slug=project.slug,
                version_slug=version.slug,
            )
            ret = _build_version(project, version.slug, already_built=to_build)
            if ret:
                to_build.add(ret)
            else:
                not_building.add(version.slug)
    return (to_build, not_building)


def trigger_sync_versions(project):
    """
    Sync the versions of a repo using its latest version.

    This doesn't register a new build,
    but clones the repo and syncs the versions.
    Due that `sync_repository_task` is bound to a version,
    we always pass the default version.

    :returns: The version slug that was used to trigger the clone.
    :rtype: str or ``None`` if failed
    """

    if not Project.objects.is_active(project):
        log.warning(
            'Sync not triggered because project is not active.',
            project_slug=project.slug,
        )
        return None

    try:
        version_identifier = project.get_default_branch()
        version = (
            project.versions.filter(
                identifier=version_identifier,
            ).first()
        )
        if not version:
            log.info('Unable to sync from version.', version_identifier=version_identifier)
            return None

        if project.has_feature(Feature.SKIP_SYNC_VERSIONS):
            log.info('Skipping sync versions for project.', project_slug=project.slug)
            return None

        options = {}
        if project.build_queue:
            # respect the queue for this project
            options['queue'] = project.build_queue

        log.debug(
            'Triggering sync repository.',
            project_slug=version.project.slug,
            version_slug=version.slug,
        )
        sync_repository_task.apply_async(
            (version.pk,),
            **options,
        )
        return version.slug
    except Exception:
        log.exception('Unknown sync versions exception')
    return None


def get_or_create_external_version(project, version_data):
    """
    Get or create version using the ``commit`` as identifier, and PR id as ``verbose_name``.

    if external version does not exist create an external version

    :param project: Project instance
    :param version_data: A :py:class:`readthedocs.api.v2.views.integrations.ExternalVersionData`
     instance.
    :returns: External version.
    :rtype: Version
    """
    external_version, created = project.versions.get_or_create(
        verbose_name=version_data.id,
        type=EXTERNAL,
        defaults={
            "identifier": version_data.commit,
            "active": True,
            "state": EXTERNAL_VERSION_STATE_OPEN,
        },
    )

    if created:
        log.info(
            'External version created.',
            project_slug=project.slug,
            version_slug=external_version.slug,
        )
    else:
        # Identifier will change if there is a new commit to the Pull/Merge Request.
        external_version.identifier = version_data.commit
        # If the PR was previously closed it was marked as closed
        external_version.state = EXTERNAL_VERSION_STATE_OPEN
        external_version.save()
        log.info(
            'External version updated.',
            project_slug=project.slug,
            version_slug=external_version.slug,
        )
    return external_version


def close_external_version(project, version_data):
    """
    Close external versions using `identifier` and `verbose_name`.

    We mark the version's state as `closed` so another celery task will remove
    it after some days. If external version does not exist then returns `None`.

    :param project: Project instance
    :param version_data: A :py:class:`readthedocs.api.v2.views.integrations.ExternalVersionData`
     instance.
    :rtype: str
    """
    external_version = (
        project.versions(manager=EXTERNAL)
        .filter(
            verbose_name=version_data.id,
            identifier=version_data.commit,
        )
        .first()
    )

    if external_version:
        external_version.state = EXTERNAL_VERSION_STATE_CLOSED
        external_version.save()
        log.info(
            "External version marked as closed.",
            project_slug=project.slug,
            version_slug=external_version.slug,
        )
        return external_version.verbose_name
    return None


def build_external_version(project, version):
    """
    Where we actually trigger builds for external versions.

    All pull/merge request webhook logic should route here to call ``trigger_build``.
    """
    if not project.has_valid_webhook:
        project.has_valid_webhook = True
        project.save()

    # Build External version
    log.info(
        'Building external version',
        project_slug=project.slug,
        version_slug=version.slug,
    )
    trigger_build(project=project, version=version, commit=version.identifier)

    return version.verbose_name
