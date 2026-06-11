"""
Bootstrap task that dispatches a build to the isolated-builders Celery worker pool.

When a project has ``Feature.USE_ISOLATED_BUILDER`` enabled,
``trigger_build`` enqueues :func:`submit_build_to_isolated` here
instead of the legacy ``update_docs_task``. This task does the minimal
work needed *before* the build container starts:

1. Sparse-clones just the ``.readthedocs.yaml`` to learn ``build.os``.
2. Resolves the project's per-build memory / time limits.
3. Mints a per-build API key (24h-scoped).
4. Dispatches a Celery task to the ``isolated-builds`` queue with the
   build args + environment. A worker process on a dedicated EC2
   instance (one task per instance — the instance self-terminates
   after the task completes) picks it up and runs ``docker run`` to
   spawn the build container.
5. Stores the worker task's Celery id on ``Build.task_id`` so
   ``cancel_build`` can revoke it.

The full build itself (clone, install, build, upload, finalize) runs
inside an upstream ``readthedocs/build:<build_os>`` container — see
the ``readthedocs-builder`` repository for the runner.

See ``readthedocs-builder/docs/architecture.md`` for the broader design.
"""

import os
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

import structlog
import yaml
from django.conf import settings

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.builds.constants import BUILD_STATE_CANCELLED
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Feature
from readthedocs.worker import app


log = structlog.get_logger(__name__)


# Candidate paths the runner accepts as the project's config file.
# Mirrors the four-pattern sparse-checkout regex elsewhere in the codebase.
_CONFIG_FILENAMES = (
    ".readthedocs.yaml",
    ".readthedocs.yml",
    "readthedocs.yaml",
    "readthedocs.yml",
)


# Name + queue of the Celery task on the isolated-builders worker.
# The worker code lives in the ``readthedocs-builder`` repo under
# ``worker/`` — these strings must match what the worker registers as.
# We dispatch by name (rather than importing the function) so this
# codebase doesn't need to import the worker's package.
ISOLATED_BUILDER_TASK_NAME = "worker.tasks.run_build"
ISOLATED_BUILDER_QUEUE = "isolated-builds"


# ---- Helpers ----


def _sparse_clone_yaml(repo_url, ref, clone_token, dest):
    """
    Clone just the ``.readthedocs.yaml`` from a remote repo into ``dest``.

    Uses ``--filter=blob:none --no-checkout`` so only commit / tree metadata
    is downloaded, then ``sparse-checkout`` to pull just the config file.
    Returns the absolute path to the downloaded config file, or ``None`` if
    none of the candidate filenames were present.

    HTTPS auth: ``clone_token`` is injected into the URL when non-empty.
    SSH auth: not supported by this bootstrap path; SSH-hosted projects need
    to use the legacy path until we surface the deploy key here.
    """
    if not repo_url:
        raise BuildUserError(message_id=BuildUserError.GENERIC)

    if repo_url.startswith("git@"):
        # SSH clone needs a deploy key we don't have access to here.
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message=(
                f"ECS bootstrap doesn't support SSH clone URLs yet; project repo: {repo_url}"
            ),
        )

    auth_url = repo_url
    if clone_token and repo_url.startswith(("https://", "http://")):
        parsed = urlparse(repo_url)
        # x-access-token@host pattern is what GitHub/GitLab tokens expect.
        auth_url = f"{parsed.scheme}://{clone_token}@{parsed.netloc}{parsed.path}"

    # TODO: consider if we want to log these commands here.
    subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            "--depth=1",
            "-b",
            ref,
            auth_url,
            dest,
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", dest, "sparse-checkout", "init", "--no-cone"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", dest, "sparse-checkout", "set", *_CONFIG_FILENAMES],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", dest, "checkout"],
        check=True,
        capture_output=True,
    )

    for name in _CONFIG_FILENAMES:
        candidate = os.path.join(dest, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def _read_build_os(config_path):
    """
    Parse ``.readthedocs.yaml`` and return the ``build.os`` value.

    Resolves the ``ubuntu-lts-latest`` alias via
    ``settings.RTD_DOCKER_BUILD_SETTINGS`` so the rest of the pipeline only
    ever sees a concrete OS tag.
    """
    with open(config_path) as fh:
        config = yaml.safe_load(fh)

    if not isinstance(config, dict):
        raise BuildUserError(BuildUserError.NO_CONFIG_FILE_DEPRECATED)

    build_os = (config.get("build") or {}).get("os")
    if not build_os:
        raise BuildUserError(BuildUserError.BUILD_OS_REQUIRED)

    if build_os == "ubuntu-lts-latest":
        alias = settings.RTD_DOCKER_BUILD_SETTINGS["os"].get("ubuntu-lts-latest", "")
        if ":" in alias:
            build_os = alias.split(":", 1)[1]

    return build_os


def _parse_mem_limit_mb(value):
    """
    Coerce a project ``container_mem_limit`` value into MiB.

    Accepts the historical Docker formats (``"512m"``, ``"8g"``) for
    compatibility with existing rows, plus plain integers / int-strings
    (interpreted as MiB).
    """
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value

    match = re.fullmatch(r"\s*(\d+)\s*([mMgG]?)\s*", str(value))
    if not match:
        return None
    n = int(match.group(1))
    unit = match.group(2).lower()
    if unit == "g":
        return n * 1024
    # Default + 'm' suffix: already MiB.
    return n


def _resolve_build_resources(project):
    """
    Resolve the per-build memory / time-limit for ``project``.

    Layers:
      1. Project field, or settings default.
      2. Capped at ``settings.RTD_BUILD_MAX_*``.

    Returns ``(memory_mib, time_limit_seconds)``.

    Note: per-build CPU isn't part of the v1 model — each build gets
    the full EC2 instance via the ephemeral-host pattern (one task per
    instance, terminated after). The instance's resources are the
    build's resources.
    """
    raw_mem = _parse_mem_limit_mb(project.container_mem_limit) or settings.RTD_BUILD_DEFAULT_MEMORY
    raw_time = project.container_time_limit or settings.RTD_BUILD_DEFAULT_TIME_LIMIT

    memory = min(raw_mem, settings.RTD_BUILD_MAX_MEMORY)
    time_limit = min(raw_time, settings.RTD_BUILD_MAX_TIME_LIMIT)

    return memory, time_limit


def _dispatch_build_task(*, build_pk, build_os, memory, environment, command, no_self_terminate):
    """
    Send the build to the ``isolated-builds`` Celery queue.

    Same path in dev (docker-compose) and prod: the dispatcher always
    sends to the queue. In prod the ``isolated-builders`` ASG picks it
    up; in dev the ``isolated-builder`` compose service does. Either
    way the worker runs ``docker run`` to spawn the build container.

    ``no_self_terminate=True`` asks the worker to skip the post-build
    ``autoscaling:TerminateInstanceInAutoScalingGroup`` call so the
    instance stays alive for debugging (no-op in dev). Returns the
    worker task's Celery id so ``cancel_build`` can revoke it.
    """
    return _send_isolated_build_task(
        build_pk=build_pk,
        build_os=build_os,
        memory=memory,
        environment=environment,
        command=command,
        no_self_terminate=no_self_terminate,
    )


def _send_isolated_build_task(
    *, build_pk, build_os, memory, environment, command, no_self_terminate
):
    """
    Dispatch the build to the ``isolated-builds`` Celery queue.

    A worker process on a dedicated EC2 instance picks up the task and
    runs ``docker run`` with the args we pass. The worker package
    lives in the ``readthedocs-builder`` repo under ``worker/``; we
    dispatch by task name so this codebase doesn't need to import it.

    ``no_self_terminate=True`` asks the worker to skip its post-build
    ``autoscaling:TerminateInstanceInAutoScalingGroup`` call so the
    EC2 instance stays alive for debugging. Sourced from the
    ``KEEP_ISOLATED_BUILDER_INSTANCE`` project feature flag in
    :func:`_submit_build_to_isolated`.

    Returns the worker task's Celery id so ``cancel_build`` can revoke
    it. We don't import the worker package; ``app.send_task`` only
    needs the name + the broker connection (shared via Django settings).
    """
    result = app.send_task(
        ISOLATED_BUILDER_TASK_NAME,
        kwargs={
            "build_pk": build_pk,
            "build_os": build_os,
            "memory_mib": memory,
            "environment": environment,
            "command": command,
            "no_self_terminate": no_self_terminate,
        },
        queue=ISOLATED_BUILDER_QUEUE,
    )
    return result.id


# ---- Failure path ----


def _fail_build(build, exc):
    """
    Finalize a build that failed *before* the runner container started.

    The runner's own try/except (``builder.runner.Runner.run``) only
    catches exceptions raised inside the build container. Anything raised
    by ``submit_build_to_isolated`` itself (missing config file, malformed
    YAML, dispatch failure, etc.) never reaches that handler, so the
    build would be left stuck in ``triggered`` state with no
    user-facing explanation.

    Mirrors what the runner does on failure: attach a notification
    derived from the exception's ``message_id`` / ``format_values``, then
    PATCH the build to ``finished`` with ``success=False``.
    """
    fallback = (
        BuildUserError.GENERIC
        if isinstance(exc, BuildUserError)
        else BuildAppError.GENERIC_WITH_BUILD_ID
    )
    message_id = getattr(exc, "message_id", None) or fallback
    format_values = getattr(exc, "format_values", None) or {}

    log.error(
        "Failing build at bootstrap.",
        exception_type=type(exc).__name__,
        message_id=message_id,
        format_values=format_values,
    )

    Notification.objects.add(
        message_id=message_id,
        attached_to=build,
        format_values=format_values,
        dismissable=False,
    )

    build.state = BUILD_STATE_FINISHED
    build.success = False
    build.length = 0
    build.save(update_fields=["state", "success", "length"])


# ---- The bootstrap task ----


@app.task(bind=True, max_retries=3, default_retry_delay=30, queue="web")
def submit_build_to_isolated(self, build_pk):
    """
    Dispatch a build to the isolated-builders Celery worker pool.

    Replaces ``update_docs_task.delay`` for projects with
    ``Feature.USE_ISOLATED_BUILDER`` enabled. See module docstring for
    the full flow.
    """
    build = Build.objects.select_related("version__project").get(pk=build_pk)
    version = build.version
    project = version.project

    # The build was cancelled (e.g. via ``cancel_build`` while we were
    # waiting in the Celery queue) before we got a chance to dispatch.
    # Bail out without minting an API key or sending to the isolated
    # queue — the Build already reflects ``state=cancelled``.
    if build.state == BUILD_STATE_CANCELLED:
        log.info(
            "Build was cancelled before dispatch; skipping.",
            build_id=build.pk,
            project_slug=project.slug,
        )
        return

    structlog.contextvars.bind_contextvars(
        build_id=build.pk,
        project_slug=project.slug,
        version_slug=version.slug,
    )

    try:
        _submit_build_to_isolated(build, version, project)
    except (BuildUserError, BuildAppError) as exc:
        # Failures *before* the build container starts never reach the
        # runner's own try/except. Finalize the build at the API layer
        # so the user sees a proper notification + ``finished`` state
        # instead of a build stuck in ``triggered``.
        _fail_build(build, exc)
        log.exception("submit_build_to_isolated failed.")


def _submit_build_to_isolated(build, version, project):
    """
    Inner body of :func:`submit_build_to_isolated` — split out so the
    caller can wrap it in a single try/except that finalizes the build
    on any user / app error. See :func:`_fail_build` for the failure
    path.
    """
    if not project.has_feature(Feature.USE_ISOLATED_BUILDER):
        # Defensive: the dispatcher in ``trigger_build`` shouldn't route here
        # without the flag. If it does, fail loudly rather than silently
        # dispatching.
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message=(
                f"submit_build_to_isolated called for project '{project.slug}' "
                "without Feature.USE_ISOLATED_BUILDER set."
            ),
        )

    # 1. Sparse-clone just the YAML to learn build.os.
    tmp = tempfile.mkdtemp(prefix="rtd-bootstrap-")
    try:
        config_path = _sparse_clone_yaml(
            repo_url=project.repo,
            ref=version.identifier,
            clone_token=project.clone_token,
            dest=tmp,
        )
        if config_path is None:
            raise BuildUserError(message_id=BuildUserError.NO_CONFIG_FILE_DEPRECATED)
        build_os = _read_build_os(config_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    log.info("Resolved build.os.", build_os=build_os)

    # 2. Resolve per-build resource limits (memory + time).
    memory, time_limit = _resolve_build_resources(project)
    log.info(
        "Resolved build resources.",
        memory=memory,
        time_limit=time_limit,
    )

    # 3. Mint a per-build API key (24h-scoped).
    _, build_api_key = BuildAPIKey.objects.create_key(project=project)

    # 4. Build the env dict that flows into the container.
    environment = {
        "RTD_API_URL": getattr(settings, "RTD_API_URL", settings.PUBLIC_API_URL),
        "RTD_PRODUCTION_DOMAIN": settings.PRODUCTION_DOMAIN,
        "RTD_BUILD_API_KEY": build_api_key,
        "RTD_BUILDER_REF": settings.RTD_BUILDER_REF,
        "RTD_BUILDER_REPO": settings.RTD_BUILDER_REPO,
        "RTD_BUILD_TIME_LIMIT_SECONDS": time_limit,
        "RTD_BUILD_TIME_LIMIT_GRACE_SECONDS": settings.RTD_BUILD_TIME_LIMIT_GRACE_SECONDS,
        "RTD_BUILD_TIME_LIMIT_KILL_SECONDS": settings.RTD_BUILD_TIME_LIMIT_KILL_SECONDS,
    }
    # Forward the readthedocs-builder clone token when configured. The
    # entrypoint inside the container injects it into the clone URL at
    # clone time, so it never appears in container logs.
    if getattr(settings, "RTD_BUILDER_TOKEN", ""):
        environment["RTD_BUILDER_TOKEN"] = settings.RTD_BUILDER_TOKEN

    if settings.RTD_DOCKER_COMPOSE:
        # Local dev: the runner uses the API's STS endpoint for storage
        # credentials (same as production), but boto3 needs to know where
        # to point — the dev environment uses an S3-compatible service
        # at ``http://storage:9000`` (rustfs) instead of real AWS. Forward
        # only that URL; credentials + bucket names come from the API.
        environment["AWS_S3_ENDPOINT_URL"] = settings.AWS_S3_ENDPOINT_URL or ""
        # Skip the runuser privilege drop — the bind-mounted docroot in
        # dev is owned by the host UID, which won't match the container's
        # ``docs`` user (same trick ``dev-run.sh`` already uses).
        environment["RTD_DOCKER_USER"] = "root"
        # The build container joins ``RTD_DOCKER_COMPOSE_NETWORK`` so it
        # can reach ``nginx`` (which fronts the API on port 80) by docker
        # service-name DNS. ``HOSTIP`` doesn't work here: the compose
        # bridge can't route to the host's LAN IP on the port-forwarded
        # nginx port. ``dev-run.sh`` sidesteps this with ``--network=host``,
        # but that defeats the compose-network plumbing we want for the
        # rest of the runner's calls (storage, etc.).
        #
        # TODO: update ``RTD_API_URL`` in ``docker_compose.py`` once we are fully migrated
        # and remove this override here.
        environment["RTD_API_URL"] = "http://nginx"

    command = ["--build-pk", str(build.pk), "--run", "--record-commands"]

    # Debug knob: ``KEEP_ISOLATED_BUILDER_INSTANCE`` feature flag asks
    # the worker to skip its post-build self-terminate so the EC2 host
    # stays alive for inspection. Always False in dev (no instance to
    # keep) and ignored by the docker dispatch path.
    no_self_terminate = project.has_feature(Feature.KEEP_ISOLATED_BUILDER_INSTANCE)

    # 5. Dispatch — to the isolated-builds Celery queue in prod, or to
    # the host docker daemon in dev. Returns the worker Celery task id
    # in prod; ``None`` in dev (no long-running task to revoke; cancel
    # uses the container name).
    worker_task_id = _dispatch_build_task(
        build_pk=build.pk,
        build_os=build_os,
        memory=memory,
        environment=environment,
        command=command,
        no_self_terminate=no_self_terminate,
    )

    log.info(
        "Dispatched build.",
        backend="docker" if settings.RTD_DOCKER_COMPOSE else "isolated-builders",
        worker_task_id=worker_task_id,
    )

    # 6. Save the worker task id so ``cancel_build`` can revoke it.
    # In dev (no Celery worker task), worker_task_id is None and we
    # leave Build.task_id as-is (cancel_build branches on
    # RTD_DOCKER_COMPOSE to use the container name instead).
    if worker_task_id:
        build.task_id = worker_task_id
        build.save(update_fields=["task_id"])
