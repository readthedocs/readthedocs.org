"""Utility functions that are used by both views and celery tasks."""

import itertools
import re

import structlog
from django.conf import settings
from rest_framework.pagination import PageNumberPagination

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import LATEST_VERBOSE_NAME
from readthedocs.builds.constants import NON_REPOSITORY_VERSIONS
from readthedocs.builds.constants import STABLE
from readthedocs.builds.constants import STABLE_VERBOSE_NAME
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import RegexAutomationRule
from readthedocs.builds.models import Version


log = structlog.get_logger(__name__)


def sync_versions_to_db(project, versions, type):
    """
    Update the database with the current versions from the repository.

    - check if user has a ``stable`` / ``latest`` version and disable ours
    - update old versions with newer configs (identifier, type, machine)
    - create new versions that do not exist on DB (in bulk)
    - it does not delete versions

    :param project: project to update versions
    :param versions: list of VCSVersion fetched from the repository
    :param type: internal or external version
    :returns: set of versions' slug added
    """
    old_version_values = project.versions.filter(type=type).values_list(
        "verbose_name",
        "identifier",
    )
    old_versions = dict(old_version_values)

    # Add new versions
    versions_to_create = []
    added = set()
    has_user_stable = False
    has_user_latest = False
    for version in versions:
        version_id = version["identifier"]
        version_name = version["verbose_name"]
        if version_name == STABLE_VERBOSE_NAME:
            has_user_stable = True
            created_version, created = _set_or_create_version(
                project=project,
                slug=STABLE,
                version_id=version_id,
                verbose_name=version_name,
                type_=type,
            )
            if created:
                added.add(created_version.slug)
        elif version_name == LATEST_VERBOSE_NAME:
            has_user_latest = True
            created_version, created = _set_or_create_version(
                project=project,
                slug=LATEST,
                version_id=version_id,
                verbose_name=version_name,
                type_=type,
            )
            if created:
                added.add(created_version.slug)
        elif version_name in old_versions:
            if version_id == old_versions[version_name]:
                # Version is correct
                continue

            # Update slug with new identifier
            Version.objects.filter(
                project=project,
                verbose_name=version_name,
                # Always filter by type, a tag and a branch
                # can share the same verbose_name.
                type=type,
            ).update(
                identifier=version_id,
                machine=False,
            )

            log.info(
                "Re-syncing versions: version updated.",
                version_verbose_name=version_name,
                version_id=version_id,
            )
        else:
            # New Version
            versions_to_create.append((version_id, version_name))

    added.update(_create_versions(project, type, versions_to_create))

    if not has_user_stable:
        stable_version = project.versions.filter(slug=STABLE, type=type).first()
        if stable_version:
            # Put back the RTD's stable version
            stable_version.machine = True
            stable_version.save()
    if not has_user_latest:
        latest_version = project.versions.filter(slug=LATEST, type=type).first()
        if latest_version:
            # Put back the RTD's latest version
            latest_version.machine = True
            latest_version.save()
    if added:
        log.info(
            "Re-syncing versions: versions added.",
            count=len(added),
            versions=",".join(itertools.islice(added, 100)),
        )
    return added


def _create_versions(project, type, versions):
    """
    Create versions (tuple of version_id and version_name).

    Returns the slug of all added versions.

    .. note::

       ``Version.slug`` relies on the post_save signal,
       so we can't use bulk_create.
    """
    versions_objs = (
        Version(
            project=project,
            type=type,
            identifier=version_id,
            verbose_name=version_name,
        )
        for version_id, version_name in versions
    )
    added = set()
    for version in versions_objs:
        version.save()
        added.add(version.slug)
    return added


def _set_or_create_version(project, slug, version_id, verbose_name, type_):
    """Search or create a version and set its machine attribute to false."""
    version = project.versions.filter(slug=slug).first()
    if version:
        version.identifier = version_id
        version.machine = False
        version.type = type_
        version.save()
    else:
        created_version = Version.objects.create(
            project=project,
            type=type_,
            identifier=version_id,
            verbose_name=verbose_name,
        )
        return created_version, True
    return version, False


def _get_deleted_versions_qs(project, tags_data, branches_data):
    # We use verbose_name for tags
    # because several tags can point to the same identifier.
    versions_tags = [version["verbose_name"] for version in tags_data]
    versions_branches = [version["identifier"] for version in branches_data]

    to_delete_qs = (
        project.versions(manager=INTERNAL)
        .exclude(uploaded=True)
        .exclude(slug__in=NON_REPOSITORY_VERSIONS)
    )

    to_delete_qs = to_delete_qs.exclude(
        type=TAG,
        verbose_name__in=versions_tags,
    )
    to_delete_qs = to_delete_qs.exclude(
        type=BRANCH,
        identifier__in=versions_branches,
    )
    return to_delete_qs


def delete_versions_from_db(project, tags_data, branches_data):
    """
    Delete all versions not in the current repo.

    :returns: The slug of the deleted versions from the database.
    """
    to_delete_qs = _get_deleted_versions_qs(
        project=project,
        tags_data=tags_data,
        branches_data=branches_data,
    ).exclude(active=True)
    _, deleted = to_delete_qs.delete()
    versions_count = deleted.get("builds.Version", 0)
    log.info(
        "Re-syncing versions: versions deleted.",
        project_slug=project.slug,
        count=versions_count,
    )


def get_deleted_active_versions(project, tags_data, branches_data):
    """Return the slug of active versions that were deleted from the repository."""
    to_delete_qs = _get_deleted_versions_qs(
        project=project,
        tags_data=tags_data,
        branches_data=branches_data,
    ).filter(active=True)
    return set(to_delete_qs.values_list("slug", flat=True))


def run_automation_rules(project, added_versions, deleted_active_versions):
    """
    Runs the automation rules on each version.

    The rules are sorted by priority.

    :param added_versions: Slugs of versions that were added.
    :param deleted_active_versions: Slugs of active versions that were deleted from the repository.

    .. note::

       Currently the versions aren't sorted in any way,
       the same order is keeped.
    """
    class_ = RegexAutomationRule
    actions = [
        (added_versions, class_.allowed_actions_on_create),
        (deleted_active_versions, class_.allowed_actions_on_delete),
    ]
    for versions_slug, allowed_actions in actions:
        versions = project.versions.filter(slug__in=versions_slug)
        rules = project.automation_rules.filter(action__in=allowed_actions)
        for version, rule in itertools.product(versions, rules):
            rule.run(version)


def normalize_build_command(command, project_slug, version_slug):
    """
    Sanitize the build command to be shown to users.

    It removes internal variables and long paths to make them nicer.
    """
    docroot = settings.DOCROOT.rstrip("/")  # remove trailing '/'

    # Remove Docker hash from DOCROOT when running it locally
    # DOCROOT contains the Docker container hash (e.g. b7703d1b5854).
    # We have to remove it from the DOCROOT it self since it changes each time
    # we spin up a new Docker instance locally.
    container_hash = "/"
    if settings.RTD_DOCKER_COMPOSE:
        docroot = re.sub("/[0-9a-z]+/?$", "", settings.DOCROOT, count=1)
        container_hash = "/([0-9a-z]+/)?"

    regex = f"{docroot}{container_hash}{project_slug}/envs/{version_slug}(/bin/)?"
    command = re.sub(regex, "", command, count=1)

    # Remove explicit variable names we use to run commands,
    # since users don't care about these.
    regex = r"^\$READTHEDOCS_VIRTUALENV_PATH/bin/"
    command = re.sub(regex, "", command, count=1)

    regex = r"^\$CONDA_ENVS_PATH/\$CONDA_DEFAULT_ENV/bin/"
    command = re.sub(regex, "", command, count=1)
    return command


class RemoteOrganizationPagination(PageNumberPagination):
    page_size = 25


class RemoteProjectPagination(PageNumberPagination):
    page_size = 15


class ProjectPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 1000
