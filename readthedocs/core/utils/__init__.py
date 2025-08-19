"""Common utility functions."""

import re

import structlog
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.functional import keep_lazy
from django.utils.safestring import SafeText
from django.utils.safestring import mark_safe
from django.utils.text import slugify as slugify_base

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import BUILD_STATE_CANCELLED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import BUILD_STATUS_PENDING
from readthedocs.builds.constants import EXTERNAL
from readthedocs.doc_builder.exceptions import BuildCancelled
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.notifications.models import Notification
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
    from readthedocs.api.v2.models import BuildAPIKey
    from readthedocs.builds.models import Build
    from readthedocs.builds.tasks import send_build_notifications
    from readthedocs.projects.models import Feature
    from readthedocs.projects.models import Project
    from readthedocs.projects.models import WebHookEvent
    from readthedocs.projects.tasks.builds import update_docs_task
    from readthedocs.projects.tasks.utils import send_external_build_status

    structlog.contextvars.bind_contextvars(project_slug=project.slug)

    if not Project.objects.is_active(project):
        log.warning(
            "Build not triggered because project is not active.",
        )
        return (None, None)

    if not version:
        default_version = project.get_default_version()
        version = project.versions.get(slug=default_version)

    build = Build.objects.create(
        project=project,
        version=version,
        type="html",
        state=BUILD_STATE_TRIGGERED,
        success=True,
        commit=commit,
    )

    structlog.contextvars.bind_contextvars(
        build_id=build.id,
        version_slug=version.slug,
    )

    options = {}
    if project.build_queue:
        options["queue"] = project.build_queue

    # Set per-task time limit
    time_limit = project.container_time_limit or settings.BUILD_TIME_LIMIT

    # Add 20% overhead to task, to ensure the build can timeout and the task
    # will cleanly finish.
    options["soft_time_limit"] = time_limit
    options["time_limit"] = int(time_limit * 1.2)

    if commit:
        structlog.contextvars.bind_contextvars(commit=commit)

        # Send pending Build Status using Git Status API for External Builds.
        send_external_build_status(
            version_type=version.type,
            build_pk=build.id,
            commit=commit,
            status=BUILD_STATUS_PENDING,
        )

    if version.type != EXTERNAL:
        # Send notifications for build triggered.
        send_build_notifications.delay(
            version_pk=version.pk,
            build_pk=build.pk,
            event=WebHookEvent.BUILD_TRIGGERED,
        )

    # Reduce overhead when doing multiple push on the same version.
    running_builds = (
        Build.objects.filter(
            project=project,
            version=version,
        )
        .exclude(
            state__in=BUILD_FINAL_STATES,
        )
        .exclude(
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

    # Start the build in X minutes and mark it as limited
    limit_reached, _, max_concurrent_builds = Build.objects.concurrent(project)
    if limit_reached:
        log.warning(
            "Delaying tasks at trigger step due to concurrency limit.",
        )
        # Delay the start of the build for the build retry delay.
        # We're still triggering the task, but it won't run immediately,
        # and the user will be alerted in the UI from the Error below.
        options["countdown"] = settings.RTD_BUILDS_RETRY_DELAY
        options["max_retries"] = settings.RTD_BUILDS_MAX_RETRIES

        Notification.objects.add(
            message_id=BuildMaxConcurrencyError.LIMIT_REACHED,
            attached_to=build,
            dismissable=False,
            format_values={"limit": max_concurrent_builds},
        )

    _, build_api_key = BuildAPIKey.objects.create_key(project=project)

    # Disable ``ACKS_LATE`` for this particular build task to try out running builders longer than 1h.
    # At 1h exactly, the task is grabbed by another worker and re-executed,
    # even while it's still running on the original worker.
    # https://github.com/readthedocs/readthedocs.org/issues/12317
    if (
        project.has_feature(Feature.BUILD_NO_ACKS_LATE)
        or project.container_time_limit
        and project.container_time_limit > settings.BUILD_TIME_LIMIT
    ):
        log.info("Disabling ACKS_LATE for this particular build.")
        options["acks_late"] = False

    # Log all the extra options passed to the task
    structlog.contextvars.bind_contextvars(**options)

    # NOTE: call this log here as well to log all the context variables added
    # inside this function. This is useful when debugging.
    log.info("Build created and ready to be executed.")

    return (
        update_docs_task.signature(
            args=(
                version.pk,
                build.pk,
            ),
            kwargs={
                "build_commit": commit,
                "build_api_key": build_api_key,
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
    structlog.contextvars.bind_contextvars(
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

        # Add a notification for this build
        Notification.objects.add(
            message_id=BuildCancelled.CANCELLED_BY_USER,
            attached_to=build,
            dismissable=False,
        )

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
    app.control.revoke(build.task_id, signal="SIGINT", terminate=terminate)


def send_email_from_object(email: EmailMultiAlternatives | EmailMessage):
    """Given an email object, send it using our send_email_task task."""
    from readthedocs.core.tasks import send_email_task

    html_content = None
    if isinstance(email, EmailMultiAlternatives):
        for content, mimetype in email.alternatives:
            if mimetype == "text/html":
                html_content = content
                break
    send_email_task.delay(
        recipient=email.to[0],
        subject=email.subject,
        content=email.body,
        content_html=html_content,
        from_email=email.from_email,
    )


def send_email(
    recipient,
    subject,
    template,
    template_html,
    context=None,
    request=None,
    from_email=None,
    **kwargs,
):
    """
    Alter context passed in and call email send task.

    .. seealso::

        Task :py:func:`readthedocs.core.tasks.send_email_task`
            Task that handles templating and sending email message
    """
    from ..tasks import send_email_task

    if context is None:
        context = {}
    context["uri"] = "{scheme}://{host}".format(
        scheme="https",
        host=settings.PRODUCTION_DOMAIN,
    )
    content = render_to_string(template, context)
    content_html = None
    if template_html:
        content_html = render_to_string(template_html, context)
    send_email_task.delay(
        recipient=recipient,
        subject=subject,
        content=content,
        content_html=content_html,
        from_email=from_email,
        **kwargs,
    )


@keep_lazy(str, SafeText)
def slugify(value, *args, **kwargs):
    """
    Add a DNS safe option to slugify.

    :param bool dns_safe: Replace special chars like underscores with ``-``.
     And remove trailing ``-``.
    """
    dns_safe = kwargs.pop("dns_safe", True)
    value = slugify_base(value, *args, **kwargs)
    if dns_safe:
        value = re.sub("[-_]+", "-", value)
        # DNS doesn't allow - at the beginning or end of subdomains
        value = mark_safe(value.strip("-"))
    return value


def get_cache_tag(*args):
    """
    Generate a cache tag from the given args.

    The final tag is composed of several parts
    that form a unique tag (like project and version slug).

    All parts are separated using a character that isn't
    allowed in slugs to avoid collisions.
    """
    return ":".join(args)


def extract_valid_attributes_for_model(model, attributes):
    """
    Extract the valid attributes for a model from a dictionary of attributes.

    :param model: Model class to extract the attributes for.
    :param attributes: Dictionary of attributes to extract.
    :returns: Tuple with the valid attributes and the invalid attributes if any.
    """
    attributes = attributes.copy()
    valid_field_names = {field.name for field in model._meta.get_fields()}
    valid_attributes = {}
    # We can't change a dictionary while interating over its keys,
    # so we make a copy of its keys.
    keys = list(attributes.keys())
    for key in keys:
        if key in valid_field_names:
            valid_attributes[key] = attributes.pop(key)
    return valid_attributes, attributes
