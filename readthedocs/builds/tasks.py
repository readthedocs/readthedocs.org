import json
from io import BytesIO

import requests
import structlog
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

from readthedocs import __version__
from readthedocs.api.v2.serializers import BuildCommandSerializer
from readthedocs.api.v2.utils import delete_versions_from_db
from readthedocs.api.v2.utils import get_deleted_active_versions
from readthedocs.api.v2.utils import run_automation_rules
from readthedocs.api.v2.utils import sync_versions_to_db
from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import BUILD_STATUS_FAILURE
from readthedocs.builds.constants import BUILD_STATUS_PENDING
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import EXTERNAL_VERSION_STATE_CLOSED
from readthedocs.builds.constants import LOCK_EXPIRE
from readthedocs.builds.constants import MAX_BUILD_COMMAND_SIZE
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.builds.reporting import get_build_overview
from readthedocs.builds.utils import memcache_lock
from readthedocs.core.utils import send_email
from readthedocs.core.utils import trigger_build
from readthedocs.integrations.models import HttpExchange
from readthedocs.notifications.models import Notification
from readthedocs.oauth.notifications import MESSAGE_OAUTH_BUILD_STATUS_FAILURE
from readthedocs.projects.models import Project
from readthedocs.projects.models import WebHookEvent
from readthedocs.storage import build_commands_storage
from readthedocs.worker import app


log = structlog.get_logger(__name__)


class TaskRouter:
    """
    Celery tasks router.

    It allows us to decide which queue is where we want to execute the task
    based on project's settings.

    1. the project is using conda
    2. new project with less than N successful builds
    3. version to be built is external

    It ignores projects that have already set ``build_queue`` attribute.

    https://docs.celeryproject.org/en/stable/userguide/routing.html#manual-routing
    https://docs.celeryproject.org/en/stable/userguide/configuration.html#std:setting-task_routes
    """

    MIN_SUCCESSFUL_BUILDS = 5
    N_LAST_BUILDS = 15
    TIME_AVERAGE = 350

    BUILD_DEFAULT_QUEUE = "build:default"
    BUILD_LARGE_QUEUE = "build:large"

    def route_for_task(self, task, args, kwargs, **__):
        log.debug("Executing TaskRouter.", task=task)
        if task not in (
            "readthedocs.projects.tasks.builds.update_docs_task",
            "readthedocs.projects.tasks.builds.sync_repository_task",
        ):
            log.debug("Skipping routing non-build task.", task=task)
            return

        version = self._get_version(task, args, kwargs)
        if not version:
            log.debug("No Build/Version found. No routing task.", task=task)
            return

        project = version.project

        # Do not override the queue defined in the project itself
        if project.build_queue:
            log.info(
                "Skipping routing task because project has a custom queue.",
                project_slug=project.slug,
                queue=project.build_queue,
            )
            return project.build_queue

        # Use last queue used by the default version for external versions
        # We always want the same queue as the previous default version,
        # so that users will have the same outcome for PR's as normal builds.
        if version.type == EXTERNAL:
            last_build_for_default_version = (
                project.builds.filter(
                    version__slug=project.get_default_version(), builder__isnull=False
                )
                .order_by("-date")
                .first()
            )
            if last_build_for_default_version:
                if "default" in last_build_for_default_version.builder:
                    routing_queue = self.BUILD_DEFAULT_QUEUE
                else:
                    routing_queue = self.BUILD_LARGE_QUEUE
                log.info(
                    "Routing task because is a external version.",
                    project_slug=project.slug,
                    queue=routing_queue,
                )
                return routing_queue

        last_builds = version.builds.order_by("-date")[: self.N_LAST_BUILDS]
        # Version has used conda in previous builds
        for build in last_builds.iterator():
            build_tools_python = ""
            conda = None
            if build.config:
                build_tools_python = (
                    build.config.get("build", {})
                    .get("tools", {})
                    .get("python", {})
                    .get("version", "")
                )
                conda = build.config.get("conda", None)

            uses_conda = any(
                [
                    conda,
                    build_tools_python.startswith("miniconda"),
                ]
            )
            if uses_conda:
                log.info(
                    "Routing task because project uses conda.",
                    project_slug=project.slug,
                    queue=self.BUILD_LARGE_QUEUE,
                )
                return self.BUILD_LARGE_QUEUE

        successful_builds_count = version.builds.filter(success=True).order_by("-date").count()
        # We do not have enough builds for this version yet
        if successful_builds_count < self.MIN_SUCCESSFUL_BUILDS:
            log.info(
                "Routing task because it does not have enough successful builds yet.",
                project_slug=project.slug,
                queue=self.BUILD_LARGE_QUEUE,
            )
            return self.BUILD_LARGE_QUEUE

        log.debug(
            "No routing task because no conditions were met.",
            project_slug=project.slug,
        )
        return

    def _get_version(self, task, args, kwargs):
        tasks = [
            "readthedocs.projects.tasks.builds.update_docs_task",
            "readthedocs.projects.tasks.builds.sync_repository_task",
        ]
        version = None
        if task in tasks:
            version_pk = args[0]
            try:
                version = Version.objects.get(pk=version_pk)
            except Version.DoesNotExist:
                log.debug(
                    "Version does not exist. Routing task to default queue.",
                    version_id=version_pk,
                )
        return version


@app.task(queue="web", bind=True)
def archive_builds_task(self, days=14, limit=200, delete=False):
    """
    Task to archive old builds to cold storage.

    :arg days: Find builds older than `days` days.
    :arg delete: If True, deletes BuildCommand objects after archiving them
    """
    if not settings.RTD_SAVE_BUILD_COMMANDS_TO_STORAGE:
        return

    lock_id = "{0}-lock".format(self.name)
    with memcache_lock(lock_id, LOCK_EXPIRE, self.app.oid) as acquired:
        if not acquired:
            log.warning("Archive Builds Task still locked")
            return False

        max_date = timezone.now() - timezone.timedelta(days=days)
        queryset = (
            Build.objects.exclude(cold_storage=True)
            .filter(
                date__lt=max_date,
                date__gt=max_date - timezone.timedelta(days=90),
            )
            .prefetch_related("commands")
            .only("date", "cold_storage")[:limit]
        )

        for build in queryset:
            commands = BuildCommandSerializer(build.commands, many=True).data
            if commands:
                for cmd in commands:
                    if len(cmd["output"]) > MAX_BUILD_COMMAND_SIZE:
                        cmd["output"] = cmd["output"][-MAX_BUILD_COMMAND_SIZE:]
                        cmd["output"] = (
                            "\n\n"
                            "... (truncated) ..."
                            "\n\n"
                            "Command output too long. Truncated to last 1MB."
                            "\n\n" + cmd["output"]
                        )  # noqa
                        log.debug("Truncating build command for build.", build_id=build.id)
                output = BytesIO(json.dumps(commands).encode("utf8"))
                filename = "{date}/{id}.json".format(date=str(build.date.date()), id=build.id)
                try:
                    build_commands_storage.save(name=filename, content=output)
                    if delete:
                        build.commands.all().delete()
                except IOError:
                    log.exception("Cold Storage save failure")
                    continue

            build.cold_storage = True
            build.save()


@app.task(queue="web")
def delete_closed_external_versions(limit=200, days=30 * 3):
    """
    Delete external versions that have been marked as closed after ``days``.

    The commit status is updated to link to the build page, as the docs are removed.
    """
    days_ago = timezone.now() - timezone.timedelta(days=days)
    queryset = Version.external.filter(
        state=EXTERNAL_VERSION_STATE_CLOSED,
        modified__lte=days_ago,
    ).order_by("modified")[:limit]
    for version in queryset:
        try:
            last_build = version.last_build
            if last_build:
                status = BUILD_STATUS_PENDING
                if last_build.finished:
                    status = BUILD_STATUS_SUCCESS if last_build.success else BUILD_STATUS_FAILURE
                send_build_status(
                    build_pk=last_build.pk,
                    commit=last_build.commit,
                    status=status,
                )
        except (TokenExpiredError, InvalidGrantError):
            log.info("Failed to send status due to expired/invalid token.")
        except Exception:
            log.exception(
                "Failed to send status",
                project_slug=version.project.slug,
                version_slug=version.slug,
            )
        else:
            log.info(
                "Removing external version.",
                project_slug=version.project.slug,
                version_slug=version.slug,
            )
            version.delete()


@app.task(max_retries=1, default_retry_delay=60, queue="web")
def sync_versions_task(project_pk, tags_data, branches_data, **kwargs):
    """
    Sync the version data in the repo (from build server) into our database.

    Creates new Version objects for tags/branches that aren't tracked in the database,
    and deletes Version objects for tags/branches that don't exists in the repository.

    :param tags_data: List of dictionaries with ``verbose_name`` and ``identifier``
                      Example: [
                          {"verbose_name": "v1.0.0",
                           "identifier": "67a9035990f44cb33091026d7453d51606350519"},
                      ].
    :param branches_data: Same as ``tags_data`` but for branches (branch name, branch identifier).
                      Example: [
                          {"verbose_name": "latest",
                           "identifier": "main"},
                      ].
    :returns: `True` or `False` if the task succeeded.
    """
    project = Project.objects.get(pk=project_pk)

    # If the currently highest non-prerelease version is active, then make
    # the new latest version active as well.
    current_stable = project.get_original_stable_version()
    if current_stable is not None:
        activate_new_stable = current_stable.active
    else:
        activate_new_stable = False

    try:
        # Update All Versions
        added_versions = set()
        result = sync_versions_to_db(
            project=project,
            versions=tags_data,
            type=TAG,
        )
        added_versions.update(result)

        result = sync_versions_to_db(
            project=project,
            versions=branches_data,
            type=BRANCH,
        )
        added_versions.update(result)

        delete_versions_from_db(
            project=project,
            tags_data=tags_data,
            branches_data=branches_data,
        )
        deleted_active_versions = get_deleted_active_versions(
            project=project,
            tags_data=tags_data,
            branches_data=branches_data,
        )
    except Exception:
        log.exception("Sync Versions Error")
        return False

    try:
        # The order of added_versions isn't deterministic.
        # We don't track the commit time or any other metadata.
        # We usually have one version added per webhook.
        run_automation_rules(project, added_versions, deleted_active_versions)
    except Exception:
        # Don't interrupt the request if something goes wrong
        # in the automation rules.
        log.exception(
            "Failed to execute automation rules.",
            project_slug=project.slug,
            versions=added_versions,
        )

    # Sync latest and stable to match the correct type and identifier.
    project.update_latest_version()
    # TODO: move this to an automation rule
    promoted_version = project.update_stable_version()
    new_stable = project.get_stable_version()
    if promoted_version and new_stable and new_stable.active:
        log.info(
            "Triggering new stable build.",
            project_slug=project.slug,
            version_identifier=new_stable.identifier,
        )
        trigger_build(project=project, version=new_stable)

        # Marking the tag that is considered the new stable version as
        # active and building it if it was just added.
        if activate_new_stable and promoted_version.slug in added_versions:
            promoted_version.active = True
            promoted_version.save()
            trigger_build(project=project, version=promoted_version)
    return True


@app.task(max_retries=3, default_retry_delay=60, queue="web")
def send_build_status(build_pk, commit, status):
    """
    Send build status to GitHub/GitLab for a given build/commit.

    :param build_pk: Build primary key
    :param commit: commit sha of the pull/merge request
    :param status: build status failed, pending, or success to be sent.
    """
    build = Build.objects.filter(pk=build_pk).first()
    if not build:
        return

    structlog.contextvars.bind_contextvars(
        build_id=build.pk,
        project_slug=build.project.slug,
        commit=commit,
        status=status,
    )

    log.debug("Sending build status.")

    # Get the service class for the project e.g: GitHubService.
    # We fallback to guess the service from the repo,
    # in the future we should only consider projects that have a remote repository.
    service_class = build.project.get_git_service_class(fallback_to_clone_url=True)
    if not service_class:
        log.info("Project isn't connected to a Git service, not sending build status.")
        return False

    if not service_class.supports_build_status:
        log.info("Git service doesn't support build status.")
        return False

    for service in service_class.for_project(build.project):
        success = service.send_build_status(
            build=build,
            commit=commit,
            status=status,
        )
        if success:
            log.debug("Build status report sent correctly.")
            return True

    Notification.objects.add(
        message_id=MESSAGE_OAUTH_BUILD_STATUS_FAILURE,
        attached_to=build.project,
        format_values={
            "provider_name": service_class.allauth_provider.name,
            "url_connect_account": reverse("socialaccount_connections"),
        },
        dismissable=True,
    )

    log.info("No social account or repository permission available, no build status sent.")
    return False


@app.task(max_retries=3, default_retry_delay=60, queue="web")
def post_build_overview(build_pk):
    """
    Post an overview about the build to the project's Git service.

    The overview contains information about the build,
    and the list of files that were changed in the build.

    If no files changed in the build,
    we only update the build overview if there is an existing comment.

    Only GitHub is supported at the moment.
    """
    build = Build.objects.filter(pk=build_pk).first()
    if not build:
        return

    version = build.version
    structlog.contextvars.bind_contextvars(
        build_id=build.pk,
        project_slug=build.project.slug,
        version_slug=version.slug,
    )

    if not version.is_external:
        log.debug("Build is not for an external version, skipping build overview.")
        return

    service_class = build.project.get_git_service_class()
    if not service_class:
        log.debug("Project isn't connected to a Git service, skipping build overview.")
        return

    if not service_class.supports_commenting:
        log.debug("Git service doesn't support creating comments.")
        return

    build_overview = get_build_overview(build)
    if not build_overview:
        log.debug("No build overview available, skipping posting comment.")
        return

    for service in service_class.for_project(build.project):
        service.post_comment(
            build=build,
            comment=build_overview.content,
            create_new=bool(build_overview.diff.files),
        )
        log.debug("PR comment posted successfully.")
        return

    log.debug("No service available, no build overview posted.")


@app.task(queue="web")
def send_build_notifications(version_pk, build_pk, event):
    version = Version.objects.get_object_or_log(pk=version_pk)
    if not version or version.type == EXTERNAL:
        return

    build = Build.objects.filter(pk=build_pk).first()
    if not build:
        return

    # NOTE: this class is used to send email/webhook notification on build success/failure
    sender = BuildNotificationSender(
        version=version,
        build=build,
        event=event,
    )
    sender.send()


class BuildNotificationSender:
    webhook_timeout = 2

    def __init__(self, version, build, event):
        self.version = version
        self.build = build
        self.project = version.project
        self.event = event

    def send(self):
        """
        Send email and webhook notifications for `project` about the `build`.

        Email notifications are only send for build:failed events.
        Webhooks choose to what events they subscribe to.
        """
        if self.event == WebHookEvent.BUILD_FAILED:
            email_addresses = self.project.emailhook_notifications.all().values_list(
                "email", flat=True
            )
            for email in email_addresses:
                try:
                    self.send_email(email)
                except Exception:
                    log.exception(
                        "Failed to send email notification.",
                        email=email,
                        project_slug=self.project.slug,
                        version_slug=self.version.slug,
                        build_id=self.build.id,
                    )

        webhooks = self.project.webhook_notifications.filter(events__name=self.event)
        for webhook in webhooks:
            try:
                self.send_webhook(webhook)
            except Exception:
                log.exception(
                    "Failed to send webhook.",
                    webhook_id=webhook.id,
                    project_slug=self.project.slug,
                    version_slug=self.version.slug,
                    build_id=self.build.id,
                )

    def send_email(self, email):
        """Send email notifications for build failures."""
        protocol = "http" if settings.DEBUG else "https"
        context = {
            "version": {
                "verbose_name": self.version.verbose_name,
            },
            "project": {
                "name": self.project.name,
            },
            "build": {
                "pk": self.build.pk,
                "error": self.build.error,
            },
            "build_url": "{}://{}{}".format(
                protocol,
                settings.PRODUCTION_DOMAIN,
                self.build.get_absolute_url(),
            ),
            "build_raw": "{}://{}{}".format(
                protocol,
                settings.PRODUCTION_DOMAIN,
                reverse("build-detail", args=[self.build.pk, "txt"]),
            ),
            "unsubscribe_url": "{}://{}{}".format(
                protocol,
                settings.PRODUCTION_DOMAIN,
                reverse("projects_notifications", args=[self.project.slug]),
            ),
        }

        if self.build.commit:
            title = _("Failed: {project[name]} ({commit})").format(
                commit=self.build.commit[:8],
                **context,
            )
        else:
            title = _("Failed: {project[name]} ({version[verbose_name]})").format(**context)

        log.info(
            "Sending email notification.",
            email=email,
            project_slug=self.project.slug,
            version_slug=self.version.slug,
            build_id=self.build.id,
        )
        send_email(
            email,
            title,
            template="projects/email/build_failed.txt",
            template_html="projects/email/build_failed.html",
            context=context,
        )

    def send_webhook(self, webhook):
        """
        Send webhook notification.

        The payload is signed using HMAC-SHA256,
        for users to be able to verify the authenticity of the request.

        Webhooks that don't have a payload,
        are from the old implementation, for those we keep sending the
        old default payload.

        An HttpExchange object is created for each transaction.
        """
        payload = webhook.get_payload(
            version=self.version,
            build=self.build,
            event=self.event,
        )
        if not payload:
            # Default payload from old webhooks.
            payload = json.dumps(
                {
                    "name": self.project.name,
                    "slug": self.project.slug,
                    "build": {
                        "id": self.build.id,
                        "commit": self.build.commit,
                        "state": self.build.state,
                        "success": self.build.success,
                        "date": self.build.date.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                }
            )

        headers = {
            "content-type": "application/json",
            "User-Agent": f"Read-the-Docs/{__version__} ({settings.PRODUCTION_DOMAIN})",
            "X-RTD-Event": self.event,
        }
        if webhook.secret:
            headers["X-Hub-Signature"] = webhook.sign_payload(payload)

        try:
            log.info(
                "Sending webhook notification.",
                webhook_id=webhook.id,
                project_slug=self.project.slug,
                version_slug=self.version.slug,
                build_id=self.build.id,
            )
            response = requests.post(
                webhook.url,
                data=payload,
                headers=headers,
                timeout=self.webhook_timeout,
            )
            HttpExchange.objects.from_requests_exchange(
                response=response,
                related_object=webhook,
            )
        except Exception:
            log.exception(
                "Failed to POST to webhook url.",
                webhook_id=webhook.id,
                webhook_url=webhook.url,
            )
