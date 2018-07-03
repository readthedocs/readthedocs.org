# -*- coding: utf-8 -*-
"""Common utilty functions."""

from __future__ import absolute_import

import errno
import getpass
import logging
import os
import re

from django.conf import settings
from django.utils import six
from django.utils.functional import allow_lazy
from django.utils.safestring import SafeText, mark_safe
from django.utils.text import slugify as slugify_base
from future.backports.urllib.parse import urlparse
from celery import group, chord

from readthedocs.builds.constants import LATEST, BUILD_STATE_TRIGGERED
from readthedocs.doc_builder.constants import DOCKER_LIMITS


log = logging.getLogger(__name__)

SYNC_USER = getattr(settings, 'SYNC_USER', getpass.getuser())


def broadcast(type, task, args, kwargs=None, callback=None):  # pylint: disable=redefined-builtin
    """
    Run a broadcast across our servers.

    Returns a task group that can be checked for results.

    `callback` should be a task signature that will be run once,
    after all of the broadcast tasks have finished running.
    """
    assert type in ['web', 'app', 'build']
    if kwargs is None:
        kwargs = {}
    default_queue = getattr(settings, 'CELERY_DEFAULT_QUEUE', 'celery')
    if type in ['web', 'app']:
        servers = getattr(settings, "MULTIPLE_APP_SERVERS", [default_queue])
    elif type in ['build']:
        servers = getattr(settings, "MULTIPLE_BUILD_SERVERS", [default_queue])

    tasks = []
    for server in servers:
        task_sig = task.s(*args, **kwargs).set(queue=server)
        tasks.append(task_sig)
    if callback:
        task_promise = chord(tasks, callback).apply_async()
    else:
        # Celery's Group class does some special handling when an iterable with
        # len() == 1 is passed in. This will be hit if there is only one server
        # defined in the above queue lists
        if len(tasks) > 1:
            task_promise = group(*tasks).apply_async()
        else:
            task_promise = group(tasks).apply_async()
    return task_promise


def clean_url(url):
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return parsed.netloc
    return parsed.path


def cname_to_slug(host):
    from dns import resolver
    answer = [ans for ans in resolver.query(host, 'CNAME')][0]
    domain = answer.target.to_unicode()
    slug = domain.split('.')[0]
    return slug


def prepare_build(
        project, version=None, record=True, force=False, immutable=True):
    """
    Prepare a build in a Celery task for project and version.

    If project has a ``build_queue``, execute the task on this build queue. If
    project has ``skip=True``, the build is not triggered.

    :param project: project's documentation to be built
    :param version: version of the project to be built. Default: ``latest``
    :param record: whether or not record the build in a new Build object
    :param force: build the HTML documentation even if the files haven't changed
    :param immutable: whether or not create an immutable Celery signature
    :returns: Celery signature of UpdateDocsTask to be executed
    """
    # Avoid circular import
    from readthedocs.projects.tasks import UpdateDocsTask
    from readthedocs.builds.models import Build

    if project.skip:
        log.info(
            'Build not triggered because Project.skip=True: project=%s',
            project.slug,
        )
        return None

    if not version:
        version = project.versions.get(slug=LATEST)

    kwargs = {
        'version_pk': version.pk,
        'record': record,
        'force': force,
    }

    if record:
        build = Build.objects.create(
            project=project,
            version=version,
            type='html',
            state=BUILD_STATE_TRIGGERED,
            success=True,
        )
        kwargs['build_pk'] = build.pk

    options = {}
    if project.build_queue:
        options['queue'] = project.build_queue

    # Set per-task time limit
    time_limit = DOCKER_LIMITS['time']
    try:
        if project.container_time_limit:
            time_limit = int(project.container_time_limit)
    except ValueError:
        log.warning('Invalid time_limit for project: %s', project.slug)

    # Add 20% overhead to task, to ensure the build can timeout and the task
    # will cleanly finish.
    options['soft_time_limit'] = time_limit
    options['time_limit'] = int(time_limit * 1.2)

    update_docs_task = UpdateDocsTask()

    # Py 2.7 doesn't support ``**`` expand syntax twice. We create just one big
    # kwargs (including the options) for this and expand it just once.
    # return update_docs_task.si(project.pk, **kwargs, **options)
    kwargs.update(options)

    return update_docs_task.si(project.pk, **kwargs)


def trigger_build(project, version=None, record=True, force=False):
    """
    Trigger a Build.

    Helper that calls ``prepare_build`` and just effectively trigger the Celery
    task to be executed by a worker.

    :param project: project's documentation to be built
    :param version: version of the project to be built. Default: ``latest``
    :param record: whether or not record the build in a new Build object
    :param force: build the HTML documentation even if the files haven't changed
    :returns: Celery AsyncResult promise
    """
    update_docs_task = prepare_build(
        project,
        version,
        record,
        force,
        immutable=True,
    )

    if update_docs_task is None:
        # Current project is skipped
        return None

    return update_docs_task.apply_async()


def send_email(recipient, subject, template, template_html, context=None,
               request=None, from_email=None, **kwargs):  # pylint: disable=unused-argument
    """
    Alter context passed in and call email send task.

    .. seealso::

        Task :py:func:`readthedocs.core.tasks.send_email_task`
            Task that handles templating and sending email message
    """
    from ..tasks import send_email_task

    if context is None:
        context = {}
    context['uri'] = '{scheme}://{host}'.format(
        scheme='https', host=settings.PRODUCTION_DOMAIN)
    send_email_task.delay(recipient=recipient, subject=subject, template=template,
                          template_html=template_html, context=context, from_email=from_email,
                          **kwargs)


def slugify(value, *args, **kwargs):
    """
    Add a DNS safe option to slugify.

    :param dns_safe: Remove underscores from slug as well
    """
    dns_safe = kwargs.pop('dns_safe', True)
    value = slugify_base(value, *args, **kwargs)
    if dns_safe:
        value = mark_safe(re.sub('[-_]+', '-', value))
    return value


slugify = allow_lazy(slugify, six.text_type, SafeText)


def safe_makedirs(directory_name):
    """
    Safely create a directory.

    Makedirs has an issue where it has a race condition around checking for a
    directory and then creating it. This catches the exception in the case where
    the dir already exists.
    """
    try:
        os.makedirs(directory_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        raise


def get_support_email():
    """
    Return the support email.

    Use ``SUPPORT_EMAIL`` setting and if it's not found returns
    support@``PRODUCTION_DOMAIN``.
    """
    support_email = getattr(settings, 'SUPPORT_EMAIL', None)
    if not support_email:
        support_email = 'support@{domain}'.format(
            domain=getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'))
    return support_email
