import hashlib
import logging

import requests

from builds.models import Version
from projects.utils import slugify_uniquely
from search.indexes import PageIndex, ProjectIndex, SectionIndex

from betterversion.better import version_windows, BetterVersion

log = logging.getLogger(__name__)


def sync_versions(project, versions, type):
    """
    Update the database with the current versions from the repository.
    """
    # Bookkeeping for keeping tag/branch identifies correct
    verbose_names = [v['verbose_name'] for v in versions]
    project.versions.filter(verbose_name__in=verbose_names).update(type=type)

    old_versions = {}
    old_version_values = project.versions.values('identifier', 'verbose_name')
    for version in old_version_values:
        old_versions[version['verbose_name']] = version['identifier']

    added = set()
    # Add new versions
    for version in versions:
        version_id = version['identifier']
        version_name = version['verbose_name']
        if version_name in old_versions.keys():
            if version_id == old_versions[version_name]:
                # Version is correct
                continue
            else:
                # Update slug with new identifier
                Version.objects.filter(
                    project=project, verbose_name=version_name
                ).update(
                    identifier=version_id,
                    type=type,
                )
                log.info("(Sync Versions) Updated Version: [%s=%s] " % (version['verbose_name'], version['identifier']))
        else:
            # New Version
            slug = slugify_uniquely(Version, version['verbose_name'], 'slug', 255, project=project)
            Version.objects.create(
                project=project,
                slug=slug,
                type=type,
                identifier=version['identifier'],
                verbose_name=version['verbose_name'],
            )
            added.add(slug)
    if added:
        log.info("(Sync Versions) Added Versions: [%s] " % ' '.join(added))
    return added


def delete_versions(project, version_data):
    """
    Delete all versions not in the current repo.
    """
    current_versions = []
    if 'tags' in version_data:
        for version in version_data['tags']:
            current_versions.append(version['identifier'])
    if 'branches' in version_data:
        for version in version_data['branches']:
            current_versions.append(version['identifier'])
    to_delete_qs = project.versions.exclude(
        identifier__in=current_versions).exclude(
        uploaded=True).exclude(
        active=True).exclude(
        slug='latest')

    if to_delete_qs.count():
        ret_val = {obj.slug for obj in to_delete_qs}
        log.info("(Sync Versions) Deleted Versions: [%s]" % ' '.join(ret_val))
        to_delete_qs.delete()
        return ret_val
    else:
        return set()



def index_search_request(version, page_list):
    log_msg = ' '.join([page['path'] for page in page_list])
    log.info("(Server Search) Indexing Pages: %s [%s]" % (
        version.project.slug, log_msg))
    project = version.project
    page_obj = PageIndex()
    section_obj = SectionIndex()
    resp = requests.get('https://api.grokthedocs.com/api/v1/index/1/heatmap/', params={'project': project.slug, 'compare': True})
    ret_json = resp.json()
    project_scale = ret_json.get('scaled_project', {}).get(project.slug, 1)

    tags = []
    for tag in project.tags.all():
        tags.append({
            'slug': tag.slug,
            'name': tag.name,
        })

    project_obj = ProjectIndex()
    project_obj.index_document(data={
        'id': project.pk,
        'name': project.name,
        'slug': project.slug,
        'description': project.description,
        'lang': project.language,
        'author': [user.username for user in project.users.all()],
        'url': project.get_absolute_url(),
        'tags': tags,
        '_boost': project_scale,
    })

    index_list = []
    section_index_list = []
    for page in page_list:
        log.debug("(API Index) %s:%s" % (project.slug, page['path']))
        page_scale = ret_json.get('scaled_page', {}).get(page['path'], 1)
        page_id = hashlib.md5('%s-%s-%s' % (project.slug, version.slug, page['path'])).hexdigest()
        index_list.append({
            'id': page_id,
            'project': project.slug,
            'version': version.slug,
            'path': page['path'],
            'title': page['title'],
            'headers': page['headers'],
            'content': page['content'],
            'taxonomy': None,
            '_boost': page_scale + project_scale,
        })
        for section in page['sections']:
            section_index_list.append({
                'id': hashlib.md5('%s-%s-%s-%s' % (project.slug, version.slug, page['path'], section['id'])).hexdigest(),
                'project': project.slug,
                'version': version.slug,
                'path': page['path'],
                'page_id': section['id'],
                'title': section['title'],
                'content': section['content'],
                '_boost': page_scale,
            })
        section_obj.bulk_index(section_index_list, parent=page_id,
                               routing=project.slug)

    page_obj.bulk_index(index_list, parent=project.slug)
