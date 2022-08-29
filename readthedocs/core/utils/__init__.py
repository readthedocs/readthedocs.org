"""Common utility functions."""

import datetime
import re
import signal

import structlog
from django.conf import settings
from django.utils import timezone
from django.utils.functional import keep_lazy
from django.utils.safestring import SafeText, mark_safe
from django.utils.text import slugify as slugify_base

from readthedocs.builds.constants import (
    BUILD_FINAL_STATES,
    BUILD_STATE_CANCELLED,
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
    BUILD_STATUS_PENDING,
    EXTERNAL,
)
from readthedocs.doc_builder.exceptions import (
    BuildCancelled,
    BuildMaxConcurrencyError,
    DuplicatedBuildError,
)
from readthedocs.worker import app

log = structlog.get_logger(__name__)


def prepare_build(
        project,
        version=None,
        commit=None,
        immutable=True,
):
    """
    Prepare a build in a Celery task for project and version.

    If project has a ``build_queue``, execute the task on this build queue. If
    project has ``skip=True``, the build is not triggered.

    :param project: project's documentation to be built
    :param version: version of the project to be built. Default: ``project.get_default_version()``
    :param commit: commit sha of the version required for sending build status reports
    :param immutable: whether or not create an immutable Celery signature
    :returns: Celery signature of update_docs_task and Build instance
    :rtype: tuple
    """
    # Avoid circular import
    from readthedocs.builds.models import Build
    from readthedocs.builds.tasks import send_build_notifications
    from readthedocs.projects.models import Feature, Project, WebHookEvent
    from readthedocs.projects.tasks.builds import update_docs_task
    from readthedocs.projects.tasks.utils import send_external_build_status

    log.bind(project_slug=project.slug)

    if not Project.objects.is_active(project):
        log.warning(
            'Build not triggered because project is not active.',
        )
        return (None, None)

    if not version:
        default_version = project.get_default_version()
        version = project.versions.get(slug=default_version)

    build = Build.objects.create(
        project=project,
        version=version,
        type='html',
        state=BUILD_STATE_TRIGGERED,
        success=True,
        commit=commit
    )

    log.bind(
        build_id=build.id,
        version_slug=version.slug,
    )

    options = {}
    if project.build_queue:
        options['queue'] = project.build_queue

    # Set per-task time limit
    # TODO remove the use of Docker limits or replace the logic here. This
    # was pulling the Docker limits that were set on each stack, but we moved
    # to dynamic setting of the Docker limits. This sets a failsafe higher
    # limit, but if no builds hit this limit, it should be safe to remove and
    # rely on Docker to terminate things on time.
    # time_limit = DOCKER_LIMITS['time']
    time_limit = 7200
    try:
        if project.container_time_limit:
            time_limit = int(project.container_time_limit)
    except ValueError:
        log.warning("Invalid time_limit for project.")

    # Add 20% overhead to task, to ensure the build can timeout and the task
    # will cleanly finish.
    options['soft_time_limit'] = time_limit
    options['time_limit'] = int(time_limit * 1.2)

    if commit:
        log.bind(commit=commit)

        # Send pending Build Status using Git Status API for External Builds.
        send_external_build_status(
            version_type=version.type,
            build_pk=build.id,
            commit=commit,
            status=BUILD_STATUS_PENDING
        )

    if version.type != EXTERNAL:
        # Send notifications for build triggered.
        send_build_notifications.delay(
            version_pk=version.pk,
            build_pk=build.pk,
            event=WebHookEvent.BUILD_TRIGGERED,
        )

    skip_build = False
    # Reduce overhead when doing multiple push on the same version.
    if project.has_feature(Feature.CANCEL_OLD_BUILDS):
        running_builds = (
            Build.objects
            .filter(
                project=project,
                version=version,
            ).exclude(
                state__in=BUILD_FINAL_STATES,
            ).exclude(
                pk=build.pk,
            )
        )
        if running_builds.count() > 0:
            log.warning(
                "Canceling running builds automatically due a new one arrived.",
                running_builds=running_builds.count(),
            )

        # If there are builds triggered/running for this particular project and version,
        # we cancel all of them and trigger a new one for the latest commit received.
        for running_build in running_builds:
            cancel_build(running_build)
    else:
        # NOTE: de-duplicate builds won't be required if we enable `CANCEL_OLD_BUILDS`,
        # since canceling a build is more effective.
        # However, we are keepting `DEDUPLICATE_BUILDS` code around while we test
        # `CANCEL_OLD_BUILDS` with a few projects and we are happy with the results.
        # After that, we can remove `DEDUPLICATE_BUILDS` code
        # and make `CANCEL_OLD_BUILDS` the default behavior.
        if commit:
            skip_build = (
                Build.objects.filter(
                    project=project,
                    version=version,
                    commit=commit,
                )
                .exclude(
                    state__in=BUILD_FINAL_STATES,
                )
                .exclude(
                    pk=build.pk,
                )
                .exists()
            )
        else:
            skip_build = (
                Build.objects.filter(
                    project=project,
                    version=version,
                    state=BUILD_STATE_TRIGGERED,
                    # By filtering for builds triggered in the previous 5 minutes we
                    # avoid false positives for builds that failed for any reason and
                    # didn't update their state, ending up on blocked builds for that
                    # version (all the builds are marked as DUPLICATED in that case).
                    # Adding this date condition, we reduce the risk of hitting this
                    # problem to 5 minutes only.
                    date__gte=timezone.now() - datetime.timedelta(minutes=5),
                ).count()
                > 1
            )

        if not project.has_feature(Feature.DEDUPLICATE_BUILDS):
            log.debug(
                "Skipping deduplication of builds. Feature not enabled.",
            )
            skip_build = False

        if skip_build:
            # TODO: we could mark the old build as duplicated, however we reset our
            # position in the queue and go back to the end of it --penalization
            log.warning(
                "Marking build to be skipped by builder.",
            )
            build.error = DuplicatedBuildError.message
            build.status = DuplicatedBuildError.status
            build.exit_code = DuplicatedBuildError.exit_code
            build.success = False
            build.state = BUILD_STATE_CANCELLED
            build.save()

    # Start the build in X minutes and mark it as limited
    if not skip_build and project.has_feature(Feature.LIMIT_CONCURRENT_BUILDS):
        limit_reached, _, max_concurrent_builds = Build.objects.concurrent(project)
        if limit_reached:
            log.warning(
                'Delaying tasks at trigger step due to concurrency limit.',
            )
            # Delay the start of the build for the build retry delay.
            # We're still triggering the task, but it won't run immediately,
            # and the user will be alerted in the UI from the Error below.
            options['countdown'] = settings.RTD_BUILDS_RETRY_DELAY
            options['max_retries'] = settings.RTD_BUILDS_MAX_RETRIES
            build.error = BuildMaxConcurrencyError.message.format(
                limit=max_concurrent_builds,
            )
            build.save()

    return (
        update_docs_task.signature(
            args=(
                version.pk,
                build.pk,
            ),
            kwargs={
                'build_commit': commit,
            },
            options=options,
            immutable=True,
        ),
        build,
    )


def trigger_build(project, version=None, commit=None):
    """
    Trigger a Build.

    Helper that calls ``prepare_build`` and just effectively trigger the Celery
    task to be executed by a worker.

    :param project: project's documentation to be built
    :param version: version of the project to be built. Default: ``latest``
    :param commit: commit sha of the version required for sending build status reports
    :returns: Celery AsyncResult promise and Build instance
    :rtype: tuple
    """
    log.bind(
        project_slug=project.slug,
        version_slug=version.slug if version else None,
        commit=commit,
    )
    log.info("Triggering build.")
    update_docs_task, build = prepare_build(
        project=project,
        version=version,
        commit=commit,
        immutable=True,
    )

    if (update_docs_task, build) == (None, None):
        # Build was skipped
        return (None, None)

    task = update_docs_task.apply_async()

    # FIXME: I'm using `isinstance` here because I wasn't able to mock this
    # properly when running tests and it fails when trying to save a
    # `mock.Mock` object in the database.
    #
    # Store the task_id in the build object to be able to cancel it later.
    if isinstance(task.id, (str, int)):
        build.task_id = task.id
        build.save()

    return task, build


def cancel_build(build):
    """
    Cancel a triggered/running build.

    Depending on the current state of the build, it takes one approach or the other:

    - Triggered:
        Update the build status and tells Celery to revoke this task.
        Workers will know about this and will discard it.
    - Running:
        Communicate Celery to force the termination of the current build
        and rely on the worker to update the build's status.
    """
    # NOTE: `terminate=True` is required for the child to attend our call
    # immediately when it's running the build. Otherwise, it finishes the
    # task. However, to revoke a task that has not started yet, we don't
    # need it.
    if build.state == BUILD_STATE_TRIGGERED:
        # Since the task won't be executed at all, we need to update the
        # Build object here.
        terminate = False
        build.state = BUILD_STATE_CANCELLED
        build.success = False
        build.error = BuildCancelled.message
        build.length = 0
        build.save()
    else:
        # In this case, we left the update of the Build object to the task
        # itself to be executed in the `on_failure` handler.
        terminate = True

    log.warning(
        "Canceling build.",
        project_slug=build.project.slug,
        version_slug=build.version.slug,
        build_id=build.pk,
        build_task_id=build.task_id,
        terminate=terminate,
    )
    app.control.revoke(build.task_id, signal=signal.SIGINT, terminate=terminate)


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

    :param bool dns_safe: Replace special chars like underscores with ``-``.
     And remove trailing ``-``.
    """
    dns_safe = kwargs.pop('dns_safe', True)
    value = slugify_base(value, *args, **kwargs)
    if dns_safe:
        value = re.sub('[-_]+', '-', value)
        # DNS doesn't allow - at the beginning or end of subdomains
        value = mark_safe(value.strip('-'))
    return value


def get_cache_tag(*args):
    """
    Generate a cache tag from the given args.

    The final tag is composed of several parts
    that form a unique tag (like project and version slug).

    All parts are separated using a character that isn't
    allowed in slugs to avoid collisions.
    """
    return ':'.join(args)
