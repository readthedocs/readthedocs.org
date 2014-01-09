import logging

from builds.models import Version
from projects.utils import slugify_uniquely

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
            active=True
        )
    if to_delete_qs.count():
        ret_val = {obj.slug for obj in to_delete_qs}
        log.info("(Sync Versions) Deleted Versions: [%s]" % ' '.join(ret_val))
        to_delete_qs.delete()
        return ret_val
    else:
        return set()
