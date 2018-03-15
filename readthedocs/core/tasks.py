"""Basic tasks."""

from __future__ import absolute_import

from readthedocs.worker import app
import datetime
import hashlib
import json
import logging
import os
import shutil
import socket

from collections import defaultdict
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from readthedocs.doc_builder.constants import DOCKER_LIMITS

import requests
from builtins import str
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from readthedocs_build.config import ConfigError
from slumber.exceptions import HttpClientError

from .constants import LOG_TEMPLATE
from .exceptions import RepositoryError
from .models import ImportedFile, Project, Domain
from .signals import before_vcs, after_vcs, before_build, after_build
from readthedocs.builds.constants import (LATEST,
                                          BUILD_STATE_CLONING,
                                          BUILD_STATE_INSTALLING,
                                          BUILD_STATE_BUILDING,
                                          BUILD_STATE_FINISHED)
from readthedocs.builds.models import Build, Version, APIVersion
from readthedocs.builds.signals import build_complete
from readthedocs.builds.syncers import Syncer
from readthedocs.cdn.purge import purge
from readthedocs.core.resolver import resolve_path
from readthedocs.core.symlink import PublicSymlink, PrivateSymlink
from readthedocs.core.utils import send_email, broadcast
from readthedocs.core.tasks import fileify, send_notifications, email_notification
from readthedocs.core.tasks import webhook_notification, remove_dir, finish_inactive_builds
from readthedocs.core.tasks import clear_artifacts, clear_pdf_artifacts, clear_epub_artifacts
from readthedocs.core.tasks import clear_html_artifacts, clear_htmlzip_artifacts
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.doc_builder.environments import (LocalBuildEnvironment,
                                                  DockerBuildEnvironment)
from readthedocs.doc_builder.exceptions import BuildEnvironmentError
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Virtualenv, Conda
from readthedocs.projects.models import APIProject
from readthedocs.restapi.client import api as api_v2
from readthedocs.restapi.utils import index_search_request
from readthedocs.search.parse_json import process_all_json_files
from readthedocs.vcs_support import utils as vcs_support_utils
from readthedocs.worker import app


log = logging.getLogger(__name__)

EMAIL_TIME_LIMIT = 30


@app.task(queue='web', time_limit=EMAIL_TIME_LIMIT)
def send_email_task(recipient, subject, template, template_html,
                    context=None, from_email=None, **kwargs):
    """
    Send multipart email.

    recipient
        Email recipient address

    subject
        Email subject header

    template
        Plain text template to send

    template_html
        HTML template to send as new message part

    context
        A dictionary to pass into the template calls

    kwargs
        Additional options to the EmailMultiAlternatives option.
    """
    msg = EmailMultiAlternatives(
        subject,
        get_template(template).render(context),
        from_email or settings.DEFAULT_FROM_EMAIL,
        [recipient],
        **kwargs
    )
    try:
        msg.attach_alternative(get_template(template_html).render(context),
                               'text/html')
    except TemplateDoesNotExist:
        pass
    msg.send()
    log.info('Sent email to recipient: %s', recipient)


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


#Random Tasks
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
