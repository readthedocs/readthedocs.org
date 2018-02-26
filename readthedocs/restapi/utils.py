# -*- coding: utf-8 -*-
"""Utility functions that are used by both views and celery tasks."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import hashlib
import logging

from rest_framework.pagination import PageNumberPagination

from readthedocs.builds.constants import NON_REPOSITORY_VERSIONS
from readthedocs.builds.models import Version
from readthedocs.search.indexes import PageIndex, ProjectIndex, SectionIndex

log = logging.getLogger(__name__)


def sync_versions(project, versions, type):  # pylint: disable=redefined-builtin
    """Update the database with the current versions from the repository."""
    old_versions = {}
    old_version_values = project.versions.filter(type=type).values(
        'identifier', 'verbose_name')
    for version in old_version_values:
        old_versions[version['verbose_name']] = version['identifier']

    added = set()
    # Add new versions
    for version in versions:
        version_id = version['identifier']
        version_name = version['verbose_name']
        if version_name in list(old_versions.keys()):
            if version_id == old_versions[version_name]:
                # Version is correct
                continue
            else:
                # Update slug with new identifier
                Version.objects.filter(
                    project=project, verbose_name=version_name).update(
                        identifier=version_id,
                        type=type,
                        machine=False,
                    )  # noqa

                log.info(
                    '(Sync Versions) Updated Version: [%s=%s] ',
                    version['verbose_name'],
                    version['identifier'],
                )
        else:
            # New Version
            created_version = Version.objects.create(
                project=project,
                type=type,
                identifier=version['identifier'],
                verbose_name=version['verbose_name'],
            )
            added.add(created_version.slug)
    if added:
        log.info('(Sync Versions) Added Versions: [%s] ', ' '.join(added))
    return added


def delete_versions(project, version_data):
    """Delete all versions not in the current repo."""
    current_versions = []
    if 'tags' in version_data:
        for version in version_data['tags']:
            current_versions.append(version['identifier'])
    if 'branches' in version_data:
        for version in version_data['branches']:
            current_versions.append(version['identifier'])
    to_delete_qs = project.versions.all()
    to_delete_qs = to_delete_qs.exclude(identifier__in=current_versions)
    to_delete_qs = to_delete_qs.exclude(uploaded=True)
    to_delete_qs = to_delete_qs.exclude(active=True)
    to_delete_qs = to_delete_qs.exclude(slug__in=NON_REPOSITORY_VERSIONS)

    if to_delete_qs.count():
        ret_val = {obj.slug for obj in to_delete_qs}
        log.info('(Sync Versions) Deleted Versions: [%s]', ' '.join(ret_val))
        to_delete_qs.delete()
        return ret_val
    return set()


def index_search_request(
        version, page_list, commit, project_scale, page_scale, section=True,
        delete=True):
    """
    Update search indexes with build output JSON.

    In order to keep sub-projects all indexed on the same shard, indexes will be
    updated using the parent project's slug as the routing value.
    """
    # TODO refactor this function
    # pylint: disable=too-many-locals
    project = version.project

    log_msg = ' '.join([page['path'] for page in page_list])
    log.info(
        'Updating search index: project=%s pages=[%s]',
        project.slug,
        log_msg,
    )

    project_obj = ProjectIndex()
    project_obj.index_document(
        data={
            'id': project.pk,
            'name': project.name,
            'slug': project.slug,
            'description': project.description,
            'lang': project.language,
            'author': [user.username for user in project.users.all()],
            'url': project.get_absolute_url(),
            'tags': None,
            'weight': project_scale,
        })

    page_obj = PageIndex()
    section_obj = SectionIndex()
    index_list = []
    section_index_list = []
    routes = [project.slug]
    routes.extend([p.parent.slug for p in project.superprojects.all()])
    for page in page_list:
        log.debug('Indexing page: %s:%s', project.slug, page['path'])
        to_hash = '-'.join([project.slug, version.slug, page['path']])
        page_id = hashlib.md5(to_hash.encode('utf-8')).hexdigest()
        index_list.append({
            'id': page_id,
            'project': project.slug,
            'version': version.slug,
            'path': page['path'],
            'title': page['title'],
            'headers': page['headers'],
            'content': page['content'],
            'taxonomy': None,
            'commit': commit,
            'weight': page_scale + project_scale,
        })
        if section:
            for sect in page['sections']:
                id_to_hash = '-'.join([
                    project.slug,
                    version.slug,
                    page['path'],
                    sect['id'],
                ])
                section_index_list.append({
                    'id': (hashlib.md5(id_to_hash.encode('utf-8')).hexdigest()),
                    'project': project.slug,
                    'version': version.slug,
                    'path': page['path'],
                    'page_id': sect['id'],
                    'title': sect['title'],
                    'content': sect['content'],
                    'weight': page_scale,
                })
            for route in routes:
                section_obj.bulk_index(
                    section_index_list,
                    parent=page_id,
                    routing=route,
                )

    for route in routes:
        page_obj.bulk_index(index_list, parent=project.slug, routing=route)

    if delete:
        log.info('Deleting files not in commit: %s', commit)
        # TODO: AK Make sure this works
        delete_query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'project': project.slug,
                            },
                        },
                        {
                            'term': {
                                'version': version.slug,
                            },
                        },
                    ],
                    'must_not': {
                        'term': {
                            'commit': commit,
                        },
                    },
                },
            },
        }
        page_obj.delete_document(body=delete_query)


class RemoteOrganizationPagination(PageNumberPagination):
    page_size = 25


class RemoteProjectPagination(PageNumberPagination):
    page_size = 15


class ProjectPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 1000
