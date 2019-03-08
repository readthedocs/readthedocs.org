"""
Tasks related to builds.

This includes creating and updating imported files,
sending email and webhook notifications, and finishing
inactive builds.

"""

import datetime
import fnmatch
import hashlib
import json
import logging
import os

import requests
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from sphinx.ext import intersphinx


from readthedocs.core.resolver import resolve_path
from readthedocs.core.utils import send_email
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.sphinx_domains.models import SphinxDomain
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.projects.models import HTMLFile, ImportedFile, Project
from readthedocs.projects.signals import (
    bulk_post_create,
    bulk_post_delete,
    files_changed,
)
from readthedocs.worker import app

from .models import Version, Build
from .constants import BUILD_STATE_FINISHED


log = logging.getLogger(__name__)


@app.task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return
    project = version.project

    if not commit:
        log.info(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg=(
                    'Imported File not being built because no commit '
                    'information'
                ),
            ),
        )
        return

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(
            LOG_TEMPLATE.format(
                project=version.project.slug,
                version=version.slug,
                msg='Creating ImportedFiles',
            ),
        )
        _manage_imported_files(version, path, commit)
        _update_intersphinx_data(version, path, commit)
    else:
        log.info(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg='No ImportedFile files',
            ),
        )


def _manage_imported_files(version, path, commit):
    """
    Update imported files for version.

    :param version: Version instance
    :param path: Path to search
    :param commit: Commit that updated path
    """
    changed_files = set()
    created_html_files = []
    for root, __, filenames in os.walk(path):
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.html'):
                model_class = HTMLFile
            else:
                model_class = ImportedFile

            dirpath = os.path.join(
                root.replace(path, '').lstrip('/'), filename.lstrip('/')
            )
            full_path = os.path.join(root, filename)
            md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            try:
                # pylint: disable=unpacking-non-sequence
                obj, __ = model_class.objects.get_or_create(
                    project=version.project,
                    version=version,
                    path=dirpath,
                    name=filename,
                )
            except model_class.MultipleObjectsReturned:
                log.warning('Error creating ImportedFile')
                continue
            if obj.md5 != md5:
                obj.md5 = md5
                changed_files.add(dirpath)
            if obj.commit != commit:
                obj.commit = commit
            obj.save()

            if model_class == HTMLFile:
                # the `obj` is HTMLFile, so add it to the list
                created_html_files.append(obj)

    # Send bulk_post_create signal for bulk indexing to Elasticsearch
    bulk_post_create.send(sender=HTMLFile, instance_list=created_html_files)

    # Delete the HTMLFile first from previous commit and
    # send bulk_post_delete signal for bulk removing from Elasticsearch
    delete_queryset = (
        HTMLFile.objects.filter(project=version.project,
                                version=version).exclude(commit=commit)
    )
    # Keep the objects into memory to send it to signal
    instance_list = list(delete_queryset)
    # Safely delete from database
    delete_queryset.delete()
    # Always pass the list of instance, not queryset.
    bulk_post_delete.send(sender=HTMLFile, instance_list=instance_list)

    # Delete ImportedFiles from previous versions
    (
        ImportedFile.objects.filter(project=version.project,
                                    version=version).exclude(commit=commit
                                                             ).delete()
    )
    changed_files = [
        resolve_path(
            version.project,
            filename=file,
            version_slug=version.slug,
        ) for file in changed_files
    ]
    files_changed.send(
        sender=Project,
        project=version.project,
        files=changed_files,
    )


@app.task(queue='web')
def send_notifications(version_pk, build_pk):
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version:
        return
    build = Build.objects.get(pk=build_pk)

    for hook in version.project.webhook_notifications.all():
        webhook_notification(version, build, hook.url)
    for email in version.project.emailhook_notifications.all().values_list(
            'email',
            flat=True,
    ):
        email_notification(version, build, email)


def email_notification(version, build, email):
    """
    Send email notifications for build failure.

    :param version: :py:class:`Version` instance that failed
    :param build: :py:class:`Build` instance that failed
    :param email: Email recipient address
    """
    log.debug(
        LOG_TEMPLATE.format(
            project=version.project.slug,
            version=version.slug,
            msg='sending email to: %s' % email,
        ),
    )

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
        'build_url': 'https://{}{}'.format(
            getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
            build.get_absolute_url(),
        ),
        'unsub_url': 'https://{}{}'.format(
            getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
            reverse('projects_notifications', args=[version.project.slug]),
        ),
    }

    if build.commit:
        title = _(
            'Failed: {project[name]} ({commit})',
        ).format(commit=build.commit[:8], **context)
    else:
        title = _('Failed: {project[name]} ({version[verbose_name]})').format(
            **context
        )

    send_email(
        email,
        title,
        template='projects/email/build_failed.txt',
        template_html='projects/email/build_failed.html',
        context=context,
    )


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
        },
    })
    log.debug(
        LOG_TEMPLATE.format(
            project=project.slug,
            version='',
            msg='sending notification to: %s' % hook_url,
        ),
    )
    try:
        requests.post(hook_url, data=data)
    except Exception:
        log.exception('Failed to POST on webhook url: url=%s', hook_url)


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
    query = (
        ~Q(state=BUILD_STATE_FINISHED) & Q(date__lte=timezone.now() - delta)
    )

    builds_finished = 0
    builds = Build.objects.filter(query)[:50]
    for build in builds:

        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit),
            )
            if build.date + custom_delta > timezone.now():
                # Do not mark as FINISHED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_FINISHED
        build.error = _(
            'This build was terminated due to inactivity. If you '
            'continue to encounter this error, file a support '
            'request with and reference this build id ({}).'.format(build.pk),
        )
        build.save()
        builds_finished += 1

    log.info(
        'Builds marked as "Terminated due inactivity": %s',
        builds_finished,
    )


def _update_intersphinx_data(version, path, commit):
    """
    Update intersphinx data for this version

    :param version: Version instance
    :param path: Path to search
    :param commit: Commit that updated path
    """
    object_file = os.path.join(path, 'objects.inv')
    if not os.path.exists(object_file):
        log.debug('No objects.inv, skipping intersphinx indexing.')
        return

    # These classes are copied from Sphinx
    # https://git.io/fhFbI
    class MockConfig:
        intersphinx_timeout = None
        tls_verify = False

    class MockApp:
        srcdir = ''
        config = MockConfig()

        def warn(self, msg):
            log.warning('Sphinx MockApp: %s', msg)

    invdata = intersphinx.fetch_inventory(MockApp(), '', object_file)
    for key, value in sorted(invdata.items() or {}):
        domain, _type = key.split(':')
        for name, einfo in sorted(value.items()):
            # project, version, url, display_name
            # ('Sphinx', '1.7.9', 'faq.html#epub-faq', 'Epub info')
            url = einfo[2]
            if '#' in url:
                doc_name, anchor = url.split(
                    '#',
                    # The anchor can contain ``#`` characters
                    maxsplit=1
                )
            else:
                doc_name, anchor = url, ''
            display_name = einfo[3]
            obj, _ = SphinxDomain.objects.get_or_create(
                project=version.project,
                version=version,
                domain=domain,
                name=name,
                display_name=display_name,
                type=_type,
                doc_name=doc_name,
                anchor=anchor,
            )
            if obj.commit != commit:
                obj.commit = commit
                obj.save()
    SphinxDomain.objects.filter(project=version.project,
                                version=version
                                ).exclude(commit=commit).delete()
