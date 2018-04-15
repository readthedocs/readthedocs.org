
from __future__ import absolute_import

import datetime
import logging
import json
import shutil

import requests
from django.conf import settings
from django.db.models import Q

from .constants import LOG_TEMPLATE
from readthedocs.builds.constants import (LATEST,
                                          BUILD_STATE_CLONING,
                                          BUILD_STATE_INSTALLING,
                                          BUILD_STATE_BUILDING,
                                          BUILD_STATE_FINISHED)
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.core.utils import send_email, broadcast
from readthedocs.builds.models import Build, Version, APIVersion
from readthedocs.worker import app

log = logging.getLogger(__name__)

#copy of this function exists in projects/tasks.py
def _manage_imported_files(version, path, commit):
    """
    Update imported files for version.

    :param version: Version instance
    :param path: Path to search
    :param commit: Commit that updated path
    """
    changed_files = set()
    for root, __, filenames in os.walk(path):
        for filename in filenames:
            dirpath = os.path.join(root.replace(path, '').lstrip('/'),
                                   filename.lstrip('/'))
            full_path = os.path.join(root, filename)
            md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            try:
                obj, __ = ImportedFile.objects.get_or_create(
                    project=version.project,
                    version=version,
                    path=dirpath,
                    name=filename,
                )
            except ImportedFile.MultipleObjectsReturned:
                log.warning('Error creating ImportedFile')
                continue
            if obj.md5 != md5:
                obj.md5 = md5
                changed_files.add(dirpath)
            if obj.commit != commit:
                obj.commit = commit
            obj.save()
    # Delete ImportedFiles from previous versions
    ImportedFile.objects.filter(project=version.project,
                                version=version
                                ).exclude(commit=commit).delete()
    # Purge Cache
    cdn_ids = getattr(settings, 'CDN_IDS', None)
    if cdn_ids:
        if version.project.slug in cdn_ids:
            changed_files = [resolve_path(
                version.project, filename=fname, version_slug=version.slug,
            ) for fname in changed_files]
            purge(cdn_ids[version.project.slug], changed_files)


@app.task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get(pk=version_pk)
    project = version.project

    if not commit:
        log.info(LOG_TEMPLATE
                 .format(project=project.slug, version=version.slug,
                         msg=('Imported File not being built because no commit '
                              'information')))
        return

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(LOG_TEMPLATE
                 .format(project=version.project.slug, version=version.slug,
                         msg='Creating ImportedFiles'))
        _manage_imported_files(version, path, commit)
    else:
        log.info(LOG_TEMPLATE
                 .format(project=project.slug, version=version.slug,
                         msg='No ImportedFile files'))


def webhook_notification(version, build, hook_url):
    """
    Send webhook notification for project webhook.

    :param version: Version instance to send hook for
    :param build: Build instance that failed
    :param hook_url: Hook URL to send to
    """
    project = version.project

    data = json.dumps({
        'name': project.name,
        'slug': project.slug,
        'build': {
            'id': build.id,
            'success': build.success,
            'date': build.date.strftime('%Y-%m-%d %H:%M:%S'),
        }
    })
    log.debug(LOG_TEMPLATE
              .format(project=project.slug, version='',
                      msg='sending notification to: %s' % hook_url))
    try:
        requests.post(hook_url, data=data)
    except Exception:
        log.exception('Failed to POST on webhook url: url=%s', hook_url)


@app.task(queue='web')
def send_notifications(version_pk, build_pk):
    version = Version.objects.get(pk=version_pk)
    build = Build.objects.get(pk=build_pk)

    for hook in version.project.webhook_notifications.all():
        webhook_notification(version, build, hook.url)
    for email in version.project.emailhook_notifications.all().values_list('email', flat=True):
        email_notification(version, build, email)


def email_notification(version, build, email):
    """
    Send email notifications for build failure.

    :param version: :py:class:`Version` instance that failed
    :param build: :py:class:`Build` instance that failed
    :param email: Email recipient address
    """
    log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug,
                                  msg='sending email to: %s' % email))

    # We send only what we need from the Django model objects here to avoid
    # serialization problems in the ``readthedocs.core.tasks.send_email_task``
    context = {
        'version': {
            'verbose_name': version.verbose_name,
        },
        'project': {
            'name': version.project.name,
        },
        'build': {
            'pk': build.pk,
            'error': build.error,
        },
        'build_url': 'https://{0}{1}'.format(
            getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
            build.get_absolute_url(),
        ),
        'unsub_url': 'https://{0}{1}'.format(
            getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
            reverse('projects_notifications', args=[version.project.slug]),
        ),
    }

    if build.commit:
        title = _('Failed: {project[name]} ({commit})').format(commit=build.commit[:8], **context)
    else:
        title = _('Failed: {project[name]} ({version[verbose_name]})').format(**context)

    send_email(
        email,
        title,
        template='projects/email/build_failed.txt',
        template_html='projects/email/build_failed.html',
        context=context,
    )


# Random Tasks
@app.task()
def remove_dir(path):
    """
    Remove a directory on the build/celery server.

    This is mainly a wrapper around shutil.rmtree so that app servers can kill
    things on the build server.
    """
    log.info("Removing %s", path)
    shutil.rmtree(path, ignore_errors=True)


@app.task()
def clear_artifacts(version_pk):
    """Remove artifacts from the web servers."""
    version = Version.objects.get(pk=version_pk)
    clear_pdf_artifacts(version)
    clear_epub_artifacts(version)
    clear_htmlzip_artifacts(version)
    clear_html_artifacts(version)


@app.task()
def clear_pdf_artifacts(version):
    if isinstance(version, int):
        version = Version.objects.get(pk=version)
    remove_dir(version.project.get_production_media_path(
        type_='pdf', version_slug=version.slug))


@app.task()
def clear_epub_artifacts(version):
    if isinstance(version, int):
        version = Version.objects.get(pk=version)
    remove_dir(version.project.get_production_media_path(
        type_='epub', version_slug=version.slug))


@app.task()
def clear_htmlzip_artifacts(version):
    if isinstance(version, int):
        version = Version.objects.get(pk=version)
    remove_dir(version.project.get_production_media_path(
        type_='htmlzip', version_slug=version.slug))


@app.task()
def clear_html_artifacts(version):
    if isinstance(version, int):
        version = Version.objects.get(pk=version)
    remove_dir(version.project.rtd_build_path(version=version.slug))


@app.task()
def finish_inactive_builds():
    """
    Finish inactive builds.

    A build is consider inactive if it's not in ``FINISHED`` state and it has been
    "running" for more time that the allowed one (``Project.container_time_limit``
    or ``DOCKER_LIMITS['time']`` plus a 20% of it).

    These inactive builds will be marked as ``success`` and ``FINISHED`` with an
    ``error`` to be communicated to the user.
    """
    time_limit = int(DOCKER_LIMITS['time'] * 1.2)
    delta = datetime.timedelta(seconds=time_limit)
    query = (~Q(state=BUILD_STATE_FINISHED) &
             Q(date__lte=datetime.datetime.now() - delta))

    builds_finished = 0
    builds = Build.objects.filter(query)[:50]
    for build in builds:

        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit))
            if build.date + custom_delta > datetime.datetime.now():
                # Do not mark as FINISHED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_FINISHED
        build.error = _(
            'This build was terminated due to inactivity. If you '
            'continue to encounter this error, file a support '
            'request with and reference this build id ({0}).'.format(build.pk)
        )
        build.save()
        builds_finished += 1

    log.info(
        'Builds marked as "Terminated due inactivity": %s',
        builds_finished,
    )
