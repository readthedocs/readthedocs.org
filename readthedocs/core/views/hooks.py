"""Views pertaining to builds."""

from dataclasses import dataclass
from typing import Literal

import structlog

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import EXTERNAL_VERSION_STATE_CLOSED
from readthedocs.builds.constants import EXTERNAL_VERSION_STATE_OPEN
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.builds import sync_repository_task


@dataclass
class VersionInfo:
    """
    Version information.

    If type is None, it means that the version can be either a branch or a tag.
    """

    name: str
    type: Literal["branch", "tag", None]


log = structlog.get_logger(__name__)


def _build_version(project, version):
    """
    Where we actually trigger builds for a project and version.

    All webhook logic should route here to call ``trigger_build``.
    """
    if not project.has_valid_webhook:
        project.has_valid_webhook = True
        project.save()
    # Previously we were building the latest version (inactive or active)
    # when building the default version,
    # some users may have relied on this to update the version list #4450
    if version.active:
        log.info(
            "Triggering build.",
            project_slug=project.slug,
            version_slug=version.slug,
        )
        trigger_build(project=project, version=version)
        return True

    log.info("Not building.", version_slug=version.slug)
    return False


def build_versions_from_names(project, versions_info: list[VersionInfo]):
    """
    Build the branches or tags from the project.

    :param project: Project instance
    :returns: A tuple with the versions that were built and the versions that were not built.
    """
    to_build = set()
    not_building = set()
    for version_info in versions_info:
        for version in project.versions_from_name(version_info.name, version_info.type):
            log.debug(
                "Processing.",
                project_slug=project.slug,
                version_slug=version.slug,
            )
            if version.slug in to_build:
                continue
            version_built = _build_version(project, version)
            if version_built:
                to_build.add(version.slug)
            else:
                not_building.add(version.slug)
    return to_build, not_building


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
            "Sync not triggered because project is not active.",
            project_slug=project.slug,
        )
        return None

    try:
        version = project.get_latest_version()
        if not version:
            log.info("Unable to sync versions, project doesn't have a valid latest version.")
            return None

        if project.has_feature(Feature.SKIP_SYNC_VERSIONS):
            log.info("Skipping sync versions for project.", project_slug=project.slug)
            return None

        _, build_api_key = BuildAPIKey.objects.create_key(project=project)

        log.debug(
            "Triggering sync repository.",
            project_slug=version.project.slug,
            version_slug=version.slug,
        )

        options = {}
        # Use custom queue if defined, as some repositories need to
        # be synced from a specific queue (like IP restricted ones).
        if project.build_queue:
            options["queue"] = project.build_queue

        sync_repository_task.apply_async(
            args=[version.pk],
            kwargs={"build_api_key": build_api_key},
            **options,
        )
        return version.slug
    except Exception:
        log.exception("Unknown sync versions exception")
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
            "External version created.",
            project_slug=project.slug,
            version_slug=external_version.slug,
        )
    else:
        # Identifier will change if there is a new commit to the Pull/Merge Request.
        external_version.identifier = version_data.commit
        # If the PR was previously closed it was marked as closed
        external_version.state = EXTERNAL_VERSION_STATE_OPEN
        external_version.active = True
        external_version.save()
        log.info(
            "External version updated.",
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
        project.versions(manager=EXTERNAL).filter(verbose_name=version_data.id).first()
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
        "Building external version",
        project_slug=project.slug,
        version_slug=version.slug,
    )
    trigger_build(project=project, version=version, commit=version.identifier)

    return version.verbose_name
