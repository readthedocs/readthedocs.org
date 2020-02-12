"""Views pertaining to builds."""

import logging

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.utils import trigger_build
from readthedocs.projects.tasks import sync_repository_task


log = logging.getLogger(__name__)


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
            '(Version build) Building %s:%s',
            project.slug,
            version.slug,
        )
        trigger_build(project=project, version=version, force=True)
        return slug

    log.info('(Version build) Not Building %s', slug)
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
            log.info(
                '(Branch Build) Processing %s:%s',
                project.slug,
                version.slug,
            )
            ret = _build_version(project, version.slug, already_built=to_build)
            if ret:
                to_build.add(ret)
            else:
                not_building.add(version.slug)
    return (to_build, not_building)


def sync_versions(project):
    """
    Sync the versions of a repo using its latest version.

    This doesn't register a new build,
    but clones the repo and syncs the versions.
    Due that `sync_repository_task` is bound to a version,
    we always pass the default version.

    :returns: The version slug that was used to trigger the clone.
    :rtype: str
    """
    try:
        version_identifier = project.get_default_branch()
        version = (
            project.versions.filter(
                identifier=version_identifier,
            ).first()
        )
        if not version:
            log.info('Unable to sync from %s version', version_identifier)
            return None

        options = {}
        if project.build_queue:
            # respect the queue for this project
            options['queue'] = project.build_queue

        sync_repository_task.apply_async(
            (version.pk,),
            **options,
        )
        return version.slug
    except Exception:
        log.exception('Unknown sync versions exception')
    return None


def get_or_create_external_version(project, identifier, verbose_name):
    """
    Get or create external versions using `identifier` and `verbose_name`.

    if external version does not exist create an external version

    :param project: Project instance
    :param identifier: Commit Hash
    :param verbose_name: pull/merge request number
    :returns:  External version.
    :rtype: Version
    """
    external_version, created = project.versions.get_or_create(
        verbose_name=verbose_name,
        type=EXTERNAL,
        defaults={'identifier': identifier, 'active': True},
    )

    if created:
        log.info(
            '(Create External Version) Added Version: [%s] ',
            external_version.slug
        )
    else:
        # identifier will change if there is a new commit to the Pull/Merge Request
        if external_version.identifier != identifier:
            external_version.identifier = identifier
            external_version.save()

            log.info(
                '(Update External Version) Updated Version: [%s] ',
                external_version.slug
            )
    return external_version


def delete_external_version(project, identifier, verbose_name):
    """
    Delete external versions using `identifier` and `verbose_name`.

    if external version does not exist then returns `None`.

    :param project: Project instance
    :param identifier: Commit Hash
    :param verbose_name: pull/merge request number
    :returns:  verbose_name (pull/merge request number).
    :rtype: str
    """
    external_version = project.versions(manager=EXTERNAL).filter(
        verbose_name=verbose_name, identifier=identifier
    ).first()

    if external_version:
        # Delete External Version
        external_version.delete()
        log.info(
            '(Delete External Version) Deleted Version: [%s]',
            external_version.slug
        )

        return external_version.verbose_name
    return None


def build_external_version(project, version, commit):
    """
    Where we actually trigger builds for external versions.

    All pull/merge request webhook logic should route here to call ``trigger_build``.
    """
    if not project.has_valid_webhook:
        project.has_valid_webhook = True
        project.save()

    # Build External version
    log.info(
        '(External Version build) Building %s:%s',
        project.slug,
        version.slug,
    )
    trigger_build(project=project, version=version, commit=commit, force=True)

    return version.verbose_name
