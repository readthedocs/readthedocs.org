import datetime
import os
import re

import boto3
import structlog
from botocore.exceptions import ClientError
from celery.worker.request import Request
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import BUILD_STATE_CANCELLED
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.builds.tasks import send_build_status
from readthedocs.core.utils.filesystem import safe_rmtree
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.notifications.models import Notification
from readthedocs.storage import build_media_storage
from readthedocs.worker import app


log = structlog.get_logger(__name__)


def clean_build(version=None):
    """Clean the files used in the build of the given version."""
    if version:
        del_dirs = [
            os.path.join(version.project.doc_path, dir_, version.slug)
            for dir_ in ("checkouts", "envs", "conda", "artifacts")
        ]
        del_dirs.append(os.path.join(version.project.doc_path, ".cache"))

        log.info("Removing directories.", directories=del_dirs)
        for path in del_dirs:
            safe_rmtree(path, ignore_errors=True)

    # Clean up DOCROOT (e.g. `user_builds/`) completely
    else:
        log.info("Removing DOCROOT directory.", docroot=settings.DOCROOT)
        safe_rmtree(settings.DOCROOT, ignore_errors=True)
        os.makedirs(settings.DOCROOT)
        return


@app.task(queue="web")
def remove_build_storage_paths(paths):
    """
    Remove artifacts from build media storage (cloud or local storage).

    :param paths: list of paths in build media storage to delete
    """
    log.info("Removing path from media storage.", paths=paths)
    for storage_path in paths:
        build_media_storage.delete_directory(storage_path)


def clean_project_resources(project, version=None, version_slug=None):
    """
    Delete all extra resources used by `version` of `project`.

    It removes:

    - Artifacts from storage.
    - Search indexes from ES.
    - Imported files.

    :param version: Version instance. If isn't given,
     all resources of `project` will be deleted.
    :param version_slug: The version slug to use.
     Version resources are stored using the version's slug,
     since slugs can change, we need to be able to provide a different slug
     sometimes to clean old resources.

    .. note::

       This function shouldn't delete objects that can't be recreated
       by re-activating the version (e.g. page views, search queries),
       as it's used when a version is deactivated.

    .. note::

       This function is usually called just before deleting project.
       Make sure to not depend on the project object inside the tasks.
    """
    version_slug = version_slug or version.slug if version else None

    # Remove storage paths
    storage_paths = []
    if version:
        storage_paths = version.get_storage_paths(version_slug=version_slug)
    else:
        storage_paths = project.get_storage_paths()
    remove_build_storage_paths.delay(storage_paths)

    # Remove indexes
    from .search import remove_search_indexes  # noqa

    remove_search_indexes.delay(
        project_slug=project.slug,
        version_slug=version_slug,
    )

    # NOTE: We use _raw_delete to avoid Django fetching all objects
    # before the deletion. Be careful when using _raw_delete, signals
    # won't be sent, and can cause integrity problems if the model
    # has relations with other models.
    if version:
        qs = version.imported_files.all()
        qs._raw_delete(qs.db)
    else:
        qs = project.imported_files.all()
        qs._raw_delete(qs.db)


@app.task()
def finish_unhealthy_builds():
    """
    Finish inactive builds.

    A build is consider inactive if the last healthcheck reported was more than
    RTD_BUILD_HEALTHCHECK_TIMEOUT seconds ago.

    These inactive builds will be marked as ``success=False`` and
    ``state=CANCELLED`` with an ``error`` to be communicated to the user.
    """
    log.debug("Running task to finish inactive builds (no healtcheck received).")
    delta = datetime.timedelta(seconds=settings.RTD_BUILD_HEALTHCHECK_TIMEOUT)
    query = (
        # Grab 3 days old at most to use a fast DB index
        Q(date__gt=timezone.now() - datetime.timedelta(days=3))
        & ~Q(state__in=BUILD_FINAL_STATES)
        & Q(healthcheck__lt=timezone.now() - delta)
    )

    projects_finished = set()
    builds_finished = []
    builds = Build.objects.filter(query)[:50]
    for build in builds:
        build.success = False
        build.state = BUILD_STATE_CANCELLED
        build.save()

        # Tell Celery to cancel this task in case it's in a zombie state.
        app.control.revoke(build.task_id, signal="SIGINT", terminate=True)

        Notification.objects.add(
            message_id=BuildAppError.BUILD_TERMINATED_DUE_INACTIVITY,
            attached_to=build,
        )

        builds_finished.append(build.pk)
        projects_finished.add(build.project.slug)

    if builds_finished:
        log.info(
            'Builds marked as "Terminated due inactivity" (not healthcheck received).',
            count=len(builds_finished),
            project_slugs=projects_finished,
            build_pks=builds_finished,
        )


def send_external_build_status(version_type, build_pk, commit, status):
    """
    Check if build is external and Send Build Status for project external versions.

     :param version_type: Version type e.g EXTERNAL, BRANCH, TAG
     :param build_pk: Build pk
     :param commit: commit sha of the pull/merge request
     :param status: build status failed, pending, or success to be sent.
    """

    # Send status reports for only External (pull/merge request) Versions.
    if version_type == EXTERNAL:
        # call the task that actually send the build status.
        send_build_status.delay(build_pk, commit, status)


@app.task(queue="web")
def set_builder_scale_in_protection(builder, protected_from_scale_in, build_id=None):
    """
    Set scale-in protection on this builder ``builder``.

    This way, AWS will not scale-in this builder while it's building the documentation.
    This is pretty useful for long running tasks.
    """
    structlog.contextvars.bind_contextvars(
        build_id=build_id,
        builder=builder,
        protected_from_scale_in=protected_from_scale_in,
    )

    if settings.DEBUG or settings.RTD_DOCKER_COMPOSE:
        log.info(
            "Running development environment. Skipping scale-in protection.",
        )
        return

    asg = boto3.client(
        "autoscaling",
        aws_access_key_id=settings.RTD_AWS_SCALE_IN_ACCESS_KEY,
        aws_secret_access_key=settings.RTD_AWS_SCALE_IN_SECRET_ACCESS_KEY,
        region_name=settings.RTD_AWS_SCALE_IN_REGION_NAME,
    )

    # web-extra-i-0c3e866c4e323928f
    hostname_match = re.match(r"([a-z\-]+)-(i-[a-f0-9]+)", builder)
    if not hostname_match:
        log.warning(
            "Unable to set scale-in protection. Hostname name matching not found.",
        )
        return
    scaling_group, instance_id = hostname_match.groups()

    # Set protection on instance
    try:
        asg.set_instance_protection(
            InstanceIds=[instance_id],
            AutoScalingGroupName=scaling_group,
            ProtectedFromScaleIn=protected_from_scale_in,
        )
    except (ValidationError, ClientError):
        # Don't log these as exceptions,
        # since there isn't much we can do about it here.
        log.info("Failed when trying to set instance protection.")
    except Exception:
        log.exception("Unexpected error when trying to set instance protection.")


class BuildRequest(Request):
    def on_timeout(self, soft, timeout):
        super().on_timeout(soft, timeout)

        structlog.contextvars.bind_contextvars(
            task_name=self.task.name,
            project_slug=self.task.data.project.slug,
            build_id=self.task.data.build["id"],
            timeout=timeout,
            soft=soft,
        )
        if soft:
            log.warning("Build is taking too much time. Risk to be killed soon.")
        else:
            log.warning("A timeout was enforced for task.")
