"""Utility functions that are used by both views and celery tasks."""

import logging

from rest_framework.pagination import PageNumberPagination

from readthedocs.builds.constants import (
    BRANCH,
    LATEST,
    LATEST_VERBOSE_NAME,
    NON_REPOSITORY_VERSIONS,
    STABLE,
    STABLE_VERBOSE_NAME,
    TAG,
)
from readthedocs.builds.models import Version


log = logging.getLogger(__name__)


def sync_versions(project, versions, type):  # pylint: disable=redefined-builtin
    """Update the database with the current versions from the repository."""
    old_version_values = project.versions.filter(type=type).values_list(
        'verbose_name',
        'identifier',
    )
    old_versions = dict(old_version_values)

    # Add new versions
    added = set()
    has_user_stable = False
    has_user_latest = False
    for version in versions:
        version_id = version['identifier']
        version_name = version['verbose_name']
        if version_name == STABLE_VERBOSE_NAME:
            has_user_stable = True
            created_version, created = set_or_create_version(
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
            created_version, created = set_or_create_version(
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
            else:
                # Update slug with new identifier
                Version.objects.filter(
                    project=project,
                    verbose_name=version_name,
                ).update(
                    identifier=version_id,
                    type=type,
                    machine=False,
                )  # noqa

                log.info(
                    '(Sync Versions) Updated Version: [%s=%s] ',
                    version_name,
                    version_id,
                )
        else:
            # New Version
            created_version = Version.objects.create(
                project=project,
                type=type,
                identifier=version_id,
                verbose_name=version_name,
            )
            added.add(created_version.slug)
    if not has_user_stable:
        stable_version = (
            project.versions.filter(slug=STABLE, type=type).first()
        )
        if stable_version:
            # Put back the RTD's stable version
            stable_version.machine = True
            stable_version.save()
    if not has_user_latest:
        latest_version = (
            project.versions.filter(slug=LATEST, type=type).first()
        )
        if latest_version:
            # Put back the RTD's latest version
            latest_version.machine = True
            latest_version.identifier = project.get_default_branch()
            latest_version.verbose_name = LATEST_VERBOSE_NAME
            latest_version.save()
    if added:
        log.info('(Sync Versions) Added Versions: [%s] ', ' '.join(added))
    return added


def set_or_create_version(project, slug, version_id, verbose_name, type_):
    """Search or create a version and set its machine attribute to false."""
    version = (project.versions.filter(slug=slug).first())
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


def delete_versions(project, version_data):
    """Delete all versions not in the current repo."""
    # We use verbose_name for tags
    # because several tags can point to the same identifier.
    versions_tags = [
        version['verbose_name'] for version in version_data.get('tags', [])
    ]
    versions_branches = [
        version['identifier'] for version in version_data.get('branches', [])
    ]
    to_delete_qs = project.versions.all()
    to_delete_qs = to_delete_qs.exclude(
        type=TAG,
        verbose_name__in=versions_tags,
    )
    to_delete_qs = to_delete_qs.exclude(
        type=BRANCH,
        identifier__in=versions_branches,
    )
    to_delete_qs = to_delete_qs.exclude(uploaded=True)
    to_delete_qs = to_delete_qs.exclude(active=True)
    to_delete_qs = to_delete_qs.exclude(slug__in=NON_REPOSITORY_VERSIONS)

    if to_delete_qs.count():
        ret_val = {obj.slug for obj in to_delete_qs}
        log.info('(Sync Versions) Deleted Versions: [%s]', ' '.join(ret_val))
        to_delete_qs.delete()
        return ret_val
    return set()


class RemoteOrganizationPagination(PageNumberPagination):
    page_size = 25


class RemoteProjectPagination(PageNumberPagination):
    page_size = 15


class ProjectPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 1000
