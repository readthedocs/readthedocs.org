"""Common utilty functions."""

import errno
import logging
import os
import re

from celery import chord, group
from django.conf import settings
from django.utils.functional import keep_lazy
from django.utils.safestring import SafeText, mark_safe
from django.utils.text import slugify as slugify_base

from readthedocs.builds.constants import (
    BUILD_STATE_TRIGGERED,
    BUILD_STATUS_PENDING,
    EXTERNAL,
)
from readthedocs.doc_builder.constants import DOCKER_LIMITS


log = logging.getLogger(__name__)


def broadcast(type, task, args, kwargs=None, callback=None):  # pylint: disable=redefined-builtin
    """
    Run a broadcast across our servers.

    Returns a task group that can be checked for results.

    `callback` should be a task signature that will be run once,
    after all of the broadcast tasks have finished running.
    """
    if type not in ['web', 'app', 'build']:
        raise ValueError('allowed value of `type` are web, app and build.')
    if kwargs is None:
        kwargs = {}

    if type in ['web', 'app']:
        servers = settings.MULTIPLE_APP_SERVERS
    elif type in ['build']:
        servers = settings.MULTIPLE_BUILD_SERVERS

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


def prepare_build(
        project,
        version=None,
        commit=None,
        record=True,
        force=False,
        immutable=True,
):
    """
    Prepare a build in a Celery task for project and version.

    If project has a ``build_queue``, execute the task on this build queue. If
    project has ``skip=True``, the build is not triggered.

    :param project: project's documentation to be built
    :param version: version of the project to be built. Default: ``project.get_default_version()``
    :param commit: commit sha of the version required for sending build status reports
    :param record: whether or not record the build in a new Build object
    :param force: build the HTML documentation even if the files haven't changed
    :param immutable: whether or not create an immutable Celery signature
    :returns: Celery signature of update_docs_task and Build instance
    :rtype: tuple
    """
    # Avoid circular import
    from readthedocs.builds.models import Build
    from readthedocs.projects.models import Project
    from readthedocs.projects.tasks import (
        update_docs_task,
        send_external_build_status,
        send_notifications,
    )

    build = None

    if not Project.objects.is_active(project):
        log.warning(
            'Build not triggered because Project is not active: project=%s',
            project.slug,
        )
        return (None, None)

    if not version:
        default_version = project.get_default_version()
        version = project.versions.get(slug=default_version)

    kwargs = {
        'record': record,
        'force': force,
        'commit': commit,
    }

    if record:
        build = Build.objects.create(
            project=project,
            version=version,
            type='html',
            state=BUILD_STATE_TRIGGERED,
            success=True,
            commit=commit
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

    if build and commit:
        # Send pending Build Status using Git Status API for External Builds.
        send_external_build_status(
            version_type=version.type, build_pk=build.id,
            commit=commit, status=BUILD_STATUS_PENDING
        )

    if build and version.type != EXTERNAL:
        # Send Webhook notification for build triggered.
        send_notifications.delay(version.pk, build_pk=build.pk, email=False)

    return (
        update_docs_task.signature(
            args=(version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        ),
        build,
    )


def trigger_build(project, version=None, commit=None, record=True, force=False):
    """
    Trigger a Build.

    Helper that calls ``prepare_build`` and just effectively trigger the Celery
    task to be executed by a worker.

    :param project: project's documentation to be built
    :param version: version of the project to be built. Default: ``latest``
    :param commit: commit sha of the version required for sending build status reports
    :param record: whether or not record the build in a new Build object
    :param force: build the HTML documentation even if the files haven't changed
    :returns: Celery AsyncResult promise and Build instance
    :rtype: tuple
    """
    update_docs_task, build = prepare_build(
        project,
        version,
        commit,
        record,
        force,
        immutable=True,
    )

    if (update_docs_task, build) == (None, None):
        # Build was skipped
        return (None, None)

    return (update_docs_task.apply_async(), build)


def send_email(
        recipient, subject, template, template_html, context=None, request=None,
        from_email=None, **kwargs
):  # pylint: disable=unused-argument
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
        scheme='https',
        host=settings.PRODUCTION_DOMAIN,
    )
    send_email_task.delay(
        recipient=recipient, subject=subject, template=template,
        template_html=template_html, context=context, from_email=from_email,
        **kwargs
    )


@keep_lazy(str, SafeText)
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
        if e.errno != errno.EEXIST:  # 17, FileExistsError
            raise


def safe_unlink(path):
    """
    Unlink ``path`` symlink using ``os.unlink``.

    This helper handles the exception ``FileNotFoundError`` to avoid logging in
    cases where the symlink does not exist already and there is nothing to
    unlink.

    :param path: symlink path to unlink
    :type path: str
    """
    try:
        os.unlink(path)
    except FileNotFoundError:
        log.warning('Unlink failed. Path %s does not exists', path)
