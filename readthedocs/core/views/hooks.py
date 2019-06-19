"""Views pertaining to builds."""

import logging

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
        sync_repository_task.delay(version.pk)
        return version.slug
    except Exception:
        log.exception('Unknown sync versions exception')
    return None
