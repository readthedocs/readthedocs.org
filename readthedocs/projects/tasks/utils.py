import datetime
import os
import re

import boto3
import structlog
from celery.worker.request import Request
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djstripe.enums import SubscriptionStatus
from messages_extends.constants import WARNING_PERSISTENT

from readthedocs.builds.constants import (
    BUILD_FINAL_STATES,
    BUILD_STATE_CANCELLED,
    EXTERNAL,
)
from readthedocs.builds.models import Build
from readthedocs.builds.tasks import send_build_status
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils.filesystem import safe_rmtree
from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.backends import EmailBackend
from readthedocs.notifications.constants import REQUIREMENT
from readthedocs.projects.models import Project
from readthedocs.storage import build_media_storage
from readthedocs.worker import app

log = structlog.get_logger(__name__)


def clean_build(version):
    """Clean the files used in the build of the given version."""
    del_dirs = [
        os.path.join(version.project.doc_path, dir_, version.slug)
        for dir_ in ("checkouts", "envs", "conda", "artifacts")
    ]
    del_dirs.append(os.path.join(version.project.doc_path, ".cache"))

    log.info("Removing directories.", directories=del_dirs)
    for path in del_dirs:
        safe_rmtree(path, ignore_errors=True)


@app.task(queue="web")
def remove_build_storage_paths(paths):
    """
    Remove artifacts from build media storage (cloud or local storage).

    :param paths: list of paths in build media storage to delete
    """
    log.info("Removing path from media storage.", paths=paths)
    for storage_path in paths:
        build_media_storage.delete_directory(storage_path)


def clean_project_resources(project, version=None):
    """
    Delete all extra resources used by `version` of `project`.

    It removes:

    - Artifacts from storage.
    - Search indexes from ES.
    - Imported files.

    :param version: Version instance. If isn't given,
                    all resources of `project` will be deleted.

    .. note::
       This function is usually called just before deleting project.
       Make sure to not depend on the project object inside the tasks.
    """
    # Remove storage paths
    storage_paths = []
    if version:
        storage_paths = version.get_storage_paths()
    else:
        storage_paths = project.get_storage_paths()
    remove_build_storage_paths.delay(storage_paths)

    # Remove indexes
    from .search import remove_search_indexes  # noqa

    remove_search_indexes.delay(
        project_slug=project.slug,
        version_slug=version.slug if version else None,
    )

    # Remove imported files
    if version:
        version.imported_files.all().delete()
    else:
        project.imported_files.all().delete()


@app.task()
def finish_inactive_builds():
    """
    Finish inactive builds.

    A build is consider inactive if it's not in a final state and it has been
    "running" for more time that the allowed one (``Project.container_time_limit``
    or ``DOCKER_LIMITS['time']`` plus a 20% of it).

    These inactive builds will be marked as ``success`` and ``CANCELLED`` with an
    ``error`` to be communicated to the user.
    """
    # TODO similar to the celery task time limit, we can't infer this from
    # Docker settings anymore, because Docker settings are determined on the
    # build servers dynamically.
    # time_limit = int(DOCKER_LIMITS['time'] * 1.2)
    # Set time as maximum celery task time limit + 5m
    time_limit = 7200 + 300
    delta = datetime.timedelta(seconds=time_limit)
    query = (
        ~Q(state__in=BUILD_FINAL_STATES)
        & Q(date__lt=timezone.now() - delta)
        & Q(date__gt=timezone.now() - datetime.timedelta(days=1))
    )

    projects_finished = set()
    builds_finished = []
    builds = Build.objects.filter(query)[:50]
    for build in builds:
        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit),
            )
            if build.date + custom_delta > timezone.now():
                # Do not mark as CANCELLED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_CANCELLED
        build.error = _(
            "This build was terminated due to inactivity. If you "
            "continue to encounter this error, file a support "
            "request with and reference this build id ({}).".format(build.pk),
        )
        build.save()
        builds_finished.append(build.pk)
        projects_finished.add(build.project.slug)

    log.info(
        'Builds marked as "Terminated due inactivity".',
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


class DeprecatedConfigFileSiteNotification(SiteNotification):
    # TODO: mention all the project slugs here
    # Maybe trim them to up to 5 projects to avoid sending a huge blob of text
    failure_message = _(
        'Your project(s) "{{ project_slugs }}" don\'t have a configuration file. '
        "Configuration files will <strong>soon be required</strong> by projects, "
        "and will no longer be optional. "
        '<a href="https://blog.readthedocs.com/migrate-configuration-v2/">Read our blog post to create one</a> '  # noqa
        "and ensure your project continues building successfully."
    )
    failure_level = WARNING_PERSISTENT


class DeprecatedConfigFileEmailNotification(Notification):
    app_templates = "projects"
    name = "deprecated_config_file_used"
    subject = "[Action required] Add a configuration file to your project to prevent build failures"
    level = REQUIREMENT

    def send(self):
        """Method overwritten to remove on-site backend."""
        backend = EmailBackend(self.request)
        backend.send(self)


@app.task(queue="web")
def deprecated_config_file_used_notification():
    """
    Create a notification about not using a config file for all the maintainers of the project.

    This is a scheduled task to be executed on the webs.
    Note the code uses `.iterator` and `.only` to avoid killing the db with this query.
    Besdies, it excludes projects with enough spam score to be skipped.
    """
    # Skip projects with a spam score bigger than this value.
    # Currently, this gives us ~250k in total (from ~550k we have in our database)
    spam_score = 300

    projects = set()
    start_datetime = datetime.datetime.now()
    queryset = Project.objects.exclude(users__profile__banned=True)
    if settings.ALLOW_PRIVATE_REPOS:
        # Only send emails to active customers
        queryset = queryset.filter(
            organizations__stripe_subscription__status=SubscriptionStatus.active
        )
    else:
        # Take into account spam score on community
        queryset = queryset.annotate(spam_score=Sum("spam_rules__value")).filter(
            Q(spam_score__lt=spam_score) | Q(is_spam=False)
        )
    queryset = queryset.only("slug", "default_version").order_by("id")
    n_projects = queryset.count()

    for i, project in enumerate(queryset.iterator()):
        if i % 500 == 0:
            log.info(
                "Finding projects without a configuration file.",
                progress=f"{i}/{n_projects}",
                current_project_pk=project.pk,
                current_project_slug=project.slug,
                projects_found=len(projects),
                time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
            )

        # Only check for the default version because if the project is using tags
        # they won't be able to update those and we will send them emails forever.
        # We can update this query if we consider later.
        version = (
            project.versions.filter(slug=project.default_version).only("id").first()
        )
        if version:
            # Use a fixed date here to avoid changing the date on each run
            years_ago = timezone.datetime(2022, 6, 1)
            build = (
                version.builds.filter(success=True, date__gt=years_ago)
                .only("_config")
                .order_by("-date")
                .first()
            )
            if build and build.deprecated_config_used():
                projects.add(project.slug)

    # Store all the users we want to contact
    users = set()

    n_projects = len(projects)
    queryset = Project.objects.filter(slug__in=projects).order_by("id")
    for i, project in enumerate(queryset.iterator()):
        if i % 500 == 0:
            log.info(
                "Querying all the users we want to contact.",
                progress=f"{i}/{n_projects}",
                current_project_pk=project.pk,
                current_project_slug=project.slug,
                users_found=len(users),
                time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
            )

        users.update(AdminPermission.owners(project).values_list("username", flat=True))

    # Only send 1 email per user,
    # even if that user has multiple projects without a configuration file.
    # The notification will mention all the projects.
    queryset = User.objects.filter(
        username__in=users,
        profile__banned=False,
        profile__optout_email_config_file_deprecation=False,
    ).order_by("id")

    n_users = queryset.count()
    for i, user in enumerate(queryset.iterator()):
        if i % 500 == 0:
            log.info(
                "Sending deprecated config file notification to users.",
                progress=f"{i}/{n_users}",
                current_user_pk=user.pk,
                current_user_username=user.username,
                time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
            )

        # All the projects for this user that don't have a configuration file
        # Use set() intersection in Python that's pretty quick since we only need the slugs.
        # Otherwise we have to pass 82k slugs to the DB query, which makes it pretty slow.
        user_projects = AdminPermission.projects(user, admin=True).values_list(
            "slug", flat=True
        )
        user_projects_slugs = list(set(user_projects) & projects)
        user_projects = Project.objects.filter(slug__in=user_projects_slugs)

        # Create slug string for onsite notification
        user_project_slugs = ", ".join(user_projects_slugs[:5])
        if len(user_projects) > 5:
            user_project_slugs += " and others..."

        n_site = DeprecatedConfigFileSiteNotification(
            user=user,
            context_object=user,
            extra_context={"project_slugs": user_project_slugs},
            success=False,
        )
        n_site.send()

        n_email = DeprecatedConfigFileEmailNotification(
            user=user,
            context_object=user,
            extra_context={"projects": user_projects},
        )
        n_email.send()

    log.info(
        "Finish sending deprecated config file notifications.",
        time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
    )


class DeprecatedBuildImageSiteNotification(SiteNotification):
    failure_message = _(
        'Your project(s) "{{ project_slugs }}" are using the deprecated "build.image" '
        'config on their ".readthedocs.yaml" file. '
        'This config is deprecated in favor of "build.os" and <strong>will be removed on October 16, 2023</strong>. '  # noqa
        '<a href="https://blog.readthedocs.com/use-build-os-config/">Read our blog post to migrate to "build.os"</a> '  # noqa
        "and ensure your project continues building successfully."
    )
    failure_level = WARNING_PERSISTENT


class DeprecatedBuildImageEmailNotification(Notification):
    app_templates = "projects"
    name = "deprecated_build_image_used"
    subject = '[Action required] Update your ".readthedocs.yaml" file to use "build.os"'
    level = REQUIREMENT

    def send(self):
        """Method overwritten to remove on-site backend."""
        backend = EmailBackend(self.request)
        backend.send(self)


@app.task(queue="web")
def deprecated_build_image_notification():
    """
    Send an email notification about using "build.image" to all maintainers of the project.

    This is a scheduled task to be executed on the webs.
    Note the code uses `.iterator` and `.only` to avoid killing the db with this query.
    Besdies, it excludes projects with enough spam score to be skipped.
    """
    # Skip projects with a spam score bigger than this value.
    # Currently, this gives us ~250k in total (from ~550k we have in our database)
    spam_score = 300

    projects = set()
    start_datetime = datetime.datetime.now()
    queryset = Project.objects.exclude(users__profile__banned=True)
    if settings.ALLOW_PRIVATE_REPOS:
        # Only send emails to active customers
        queryset = queryset.filter(
            organizations__stripe_subscription__status=SubscriptionStatus.active
        )
    else:
        # Take into account spam score on community
        queryset = queryset.annotate(spam_score=Sum("spam_rules__value")).filter(
            Q(spam_score__lt=spam_score) | Q(is_spam=False)
        )
    queryset = queryset.only("slug", "default_version").order_by("id")
    n_projects = queryset.count()

    for i, project in enumerate(queryset.iterator()):
        if i % 500 == 0:
            log.info(
                'Finding projects using "build.image" config key.',
                progress=f"{i}/{n_projects}",
                current_project_pk=project.pk,
                current_project_slug=project.slug,
                projects_found=len(projects),
                time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
            )

        # Only check for the default version because if the project is using tags
        # they won't be able to update those and we will send them emails forever.
        # We can update this query if we consider later.
        version = (
            project.versions.filter(slug=project.default_version).only("id").first()
        )
        if version:
            # Use a fixed date here to avoid changing the date on each run
            years_ago = timezone.datetime(2022, 8, 1)
            build = (
                version.builds.filter(success=True, date__gt=years_ago)
                .only("_config")
                .order_by("-date")
                .first()
            )
            if build and build.deprecated_build_image_used():
                projects.add(project.slug)

    # Store all the users we want to contact
    users = set()

    n_projects = len(projects)
    queryset = Project.objects.filter(slug__in=projects).order_by("id")
    for i, project in enumerate(queryset.iterator()):
        if i % 500 == 0:
            log.info(
                'Querying all the users we want to contact about "build.image" deprecation.',
                progress=f"{i}/{n_projects}",
                current_project_pk=project.pk,
                current_project_slug=project.slug,
                users_found=len(users),
                time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
            )

        users.update(AdminPermission.owners(project).values_list("username", flat=True))

    # Only send 1 email per user,
    # even if that user has multiple projects using "build.image".
    # The notification will mention all the projects.
    queryset = User.objects.filter(
        username__in=users,
        profile__banned=False,
        profile__optout_email_build_image_deprecation=False,
    ).order_by("id")

    n_users = queryset.count()
    for i, user in enumerate(queryset.iterator()):
        if i % 500 == 0:
            log.info(
                'Sending deprecated "build.image" config key notification to users.',
                progress=f"{i}/{n_users}",
                current_user_pk=user.pk,
                current_user_username=user.username,
                time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
            )

        # All the projects for this user that are using "build.image".
        # Use set() intersection in Python that's pretty quick since we only need the slugs.
        # Otherwise we have to pass 82k slugs to the DB query, which makes it pretty slow.
        user_projects = AdminPermission.projects(user, admin=True).values_list(
            "slug", flat=True
        )
        user_projects_slugs = list(set(user_projects) & projects)
        user_projects = Project.objects.filter(slug__in=user_projects_slugs)

        # Create slug string for onsite notification
        user_project_slugs = ", ".join(user_projects_slugs[:5])
        if len(user_projects) > 5:
            user_project_slugs += " and others..."

        n_site = DeprecatedBuildImageSiteNotification(
            user=user,
            context_object=user,
            extra_context={"project_slugs": user_project_slugs},
            success=False,
        )
        n_site.send()

        n_email = DeprecatedBuildImageEmailNotification(
            user=user,
            context_object=user,
            extra_context={"projects": user_projects},
        )
        n_email.send()

    log.info(
        'Finish sending deprecated "build.image" config key notifications.',
        time_elapsed=(datetime.datetime.now() - start_datetime).seconds,
    )


@app.task(queue="web")
def set_builder_scale_in_protection(instance, protected_from_scale_in):
    """
    Set scale-in protection on this builder ``instance``.

    This way, AWS will not scale-in this instance while it's building the documentation.
    This is pretty useful for long running tasks.
    """
    log.bind(instance=instance, protected_from_scale_in=protected_from_scale_in)

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
    hostname_match = re.match(r"([a-z\-]+)-(i-[a-f0-9]+)", instance)
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
    except Exception:
        log.exception("Failed when trying to set instance protection.")


class BuildRequest(Request):
    def on_timeout(self, soft, timeout):
        super().on_timeout(soft, timeout)

        log.bind(
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
