"""
Bootstrap task that dispatches a build to AWS Fargate.

When a project has ``Feature.USE_FARGATE_BUILDER`` enabled, ``trigger_build``
enqueues :func:`submit_build_to_ecs` here instead of the legacy
``update_docs_task``. This task does the minimal work needed *before* the
Fargate task can run:

1. Sparse-clones just the ``.readthedocs.yaml`` to learn ``build.os``.
2. Resolves ``build.os`` to an ECS task definition name and snaps the
   project's per-build resource limits to a Fargate-supported CPU/memory pair.
3. Mints a per-build API key.
4. Calls ``ecs:RunTask`` with the right image + command + env.
5. Stores the returned ECS task ARN on ``Build.task_arn`` so
   ``cancel_build`` can later call ``ecs:StopTask``.

The full Fargate build itself (clone, install, build, upload, finalize) runs
inside the ``readthedocs/builder:<build_os>`` container — see the
``readthedocs-builder`` repository for the runner.

See ``readthedocs-builder/docs/architecture.md`` for the broader design.
"""

import os
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

import boto3
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


# Fargate's supported task-level CPU/memory matrix. Memory values are in MiB.
# Source: AWS docs — "Task CPU and memory" under Fargate task definitions.
_FARGATE_CPU_MEMORY_MATRIX = {
    256: [512, 1024, 2048],
    512: [1024, 2048, 3072, 4096],
    1024: [2048, 3072, 4096, 5120, 6144, 7168, 8192],
    2048: list(range(4096, 16384 + 1, 1024)),
    4096: list(range(8192, 30720 + 1, 1024)),
    8192: list(range(16384, 61440 + 1, 4096)),
    16384: list(range(32768, 122880 + 1, 8192)),
}
_FARGATE_CPU_VALUES = sorted(_FARGATE_CPU_MEMORY_MATRIX.keys())


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
                f"Fargate bootstrap doesn't support SSH clone URLs yet; project repo: {repo_url}"
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


def _snap_to_fargate_pair(cpu, memory):
    """
    Round ``(cpu, memory)`` up to the smallest Fargate-supported pair.

    Returns ``(cpu, memory)`` integers. Caps at the largest supported pair
    so a misconfigured project can't accidentally request unbounded compute.
    """
    cpu = next((c for c in _FARGATE_CPU_VALUES if c >= cpu), _FARGATE_CPU_VALUES[-1])
    allowed = _FARGATE_CPU_MEMORY_MATRIX[cpu]
    memory = next((m for m in allowed if m >= memory), allowed[-1])
    return cpu, memory


def _resolve_fargate_resources(project):
    """
    Resolve the per-build CPU / memory / time-limit for ``project``.

    Layers:
      1. Project field, or settings default.
      2. Capped at ``settings.RTD_BUILD_MAX_*``.
      3. CPU+memory snapped to a valid Fargate pair (CPU-first wins).

    Returns ``(cpu, memory_mib, time_limit_seconds)``.
    """
    raw_cpu = project.container_cpu_limit or settings.RTD_BUILD_DEFAULT_CPU
    raw_mem = _parse_mem_limit_mb(project.container_mem_limit) or settings.RTD_BUILD_DEFAULT_MEMORY
    raw_time = project.container_time_limit or settings.RTD_BUILD_DEFAULT_TIME_LIMIT

    cpu = min(raw_cpu, settings.RTD_BUILD_MAX_CPU)
    memory = min(raw_mem, settings.RTD_BUILD_MAX_MEMORY)
    time_limit = min(raw_time, settings.RTD_BUILD_MAX_TIME_LIMIT)

    cpu, memory = _snap_to_fargate_pair(cpu, memory)
    return cpu, memory, time_limit


def _dispatch_build_task(*, build_pk, build_os, cpu, memory, environment, command):
    """
    Dispatch a build to either Fargate (prod) or local Docker (dev).

    Branches on ``settings.RTD_DOCKER_COMPOSE``: docker-compose dev runs
    the build in a sibling container on the host's docker daemon via
    docker-py; production hits ``ecs:RunTask``. Returns the task
    identifier stored on ``Build.task_arn`` — a container id under
    docker-compose, a real ECS task ARN in production. ``cancel_build``
    branches on the same setting to interpret it.
    """
    if settings.RTD_DOCKER_COMPOSE:
        return _docker_run_task(
            build_pk=build_pk,
            cpu=cpu,
            memory=memory,
            environment=environment,
            command=command,
        )
    return _ecs_run_task(
        build_os=build_os,
        cpu=cpu,
        memory=memory,
        environment=environment,
        command=command,
    )


def _docker_run_task(*, build_pk, cpu, memory, environment, command):
    """
    Spawn a builder container via the host's docker daemon (dev only).

    Returns the resulting container id (stored on ``Build.task_arn``;
    ``cancel_build`` knows whether to interpret it as a container id or
    an ECS ARN based on ``settings.RTD_DOCKER_COMPOSE``).

    The container shares the docker-compose network (so it can reach
    ``web``, ``storage``, etc.) and gets the same resource constraints
    Fargate would apply (cpus + memory). When
    ``settings.RTD_PATH_BUILDER`` is set, the host-side
    readthedocs-builder checkout is bind-mounted at ``/opt/builder`` so
    the entrypoint skips the GitHub clone — matches the
    ``dev-run.sh`` iteration loop.

    Requires the celery container to have ``/var/run/docker.sock``
    bind-mounted (docker-out-of-docker).
    """
    # Import lazily so the prod settings don't need the ``docker`` package
    # available at import time. (It already is, via the legacy
    # DockerBuildEnvironment, but lazy keeps the dep graph clean.)
    import docker

    client = docker.from_env()
    # TODO: in production this is derived from build.os and points to a
    # readthedocs/builder:<os> image. For local dev we currently use a
    # single ``builder-dev:latest`` image regardless of build.os because
    # we don't have the OS image matrix yet. Match production once the
    # matrix exists.
    image = settings.RTD_LOCAL_BUILDER_IMAGE

    volumes = {}
    if settings.RTD_PATH_BUILDER:
        # The path here is resolved by the *host* docker daemon (we're
        # talking to it via the bind-mounted socket), so
        # ``RTD_PATH_BUILDER`` must be a host-side absolute path —
        # not a path inside the celery container.
        volumes[settings.RTD_PATH_BUILDER] = {
            "bind": "/opt/builder",
            "mode": "ro",
        }
        # ``entrypoint.sh`` is COPYed into the image at ``/opt/entrypoint.sh``
        # (see ``readthedocs-builder/Dockerfile``) — outside the
        # ``/opt/builder`` bind-mount above, so edits on the host don't
        # take effect without a full image rebuild. Bind-mount the host
        # copy on top so dev iterations on the entrypoint (signal
        # handling, watchdog, etc.) are live.
        volumes[os.path.join(settings.RTD_PATH_BUILDER, "scripts/entrypoint.sh")] = {
            "bind": "/opt/entrypoint.sh",
            "mode": "ro",
        }

    # Stable container name so the user can ``docker logs build-<pk>``
    # without having to look up the random id. If a stopped container
    # from a previous run of the same pk is still around, remove it
    # first so the name is free.
    container_name = f"build-{build_pk}"
    try:
        existing = client.containers.get(container_name)
    except docker.errors.NotFound:
        pass
    else:
        log.info("Removing stale container.", container_name=container_name)
        existing.remove(force=True)

    try:
        container = client.containers.run(
            image=image,
            name=container_name,
            command=list(command),
            environment={k: str(v) for k, v in environment.items()},
            # Fargate CPU units (1024 = 1 vCPU) -> Docker nano_cpus (1e9 = 1 vCPU).
            nano_cpus=int(cpu * 1_000_000_000 // 1024),
            mem_limit=f"{memory}m",
            network=settings.RTD_DOCKER_COMPOSE_NETWORK,
            volumes=volumes,
            detach=True,
            # Keep the container around after exit in dev so its logs
            # remain inspectable via ``docker logs build-<pk>``. Prune
            # accumulated stopped containers periodically with
            # ``docker container prune``. Production (``_ecs_run_task``)
            # doesn't hit this path — CloudWatch handles log retention.
            auto_remove=False,
        )
    except Exception as exc:
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message=f"docker run failed: {exc}",
        ) from exc

    log.info(
        "Dispatched build to local Docker.",
        image=image,
        container_id=container.id,
        nano_cpus=int(cpu * 1_000_000_000 // 1024),
        mem_limit=f"{memory}m",
        network=settings.RTD_DOCKER_COMPOSE_NETWORK,
        bind_mount=bool(volumes),
    )
    return container.id


def _ecs_run_task(*, build_os, cpu, memory, environment, command):
    """
    Call ``ecs:RunTask`` and return the resulting task ARN.

    Uses Fargate Spot as the primary capacity (with Fargate on-demand as
    fallback could be configured at the cluster level via a default
    capacity provider strategy; here we always request Spot first).

    Raises :class:`BuildAppError` on any AWS error so the failure flows
    through the caller's exception handling.
    """
    client = boto3.client("ecs", region_name=settings.RTD_ECS_REGION or None)
    task_definition = settings.RTD_ECS_TASK_DEFINITION_FORMAT.format(build_os=build_os)

    try:
        response = client.run_task(
            cluster=settings.RTD_ECS_CLUSTER,
            taskDefinition=task_definition,
            capacityProviderStrategy=[
                {"capacityProvider": "FARGATE_SPOT", "weight": 1},
            ],
            count=1,
            overrides={
                "cpu": str(cpu),
                "memory": str(memory),
                "containerOverrides": [
                    {
                        "name": "builder",
                        "command": list(command),
                        "environment": [
                            {"name": k, "value": str(v)} for k, v in environment.items()
                        ],
                    },
                ],
            },
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": list(settings.RTD_ECS_SUBNETS),
                    "securityGroups": list(settings.RTD_ECS_SECURITY_GROUPS),
                    "assignPublicIp": settings.RTD_ECS_ASSIGN_PUBLIC_IP,
                },
            },
        )
    except Exception as exc:
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message=f"ecs:RunTask failed: {exc}",
        ) from exc

    tasks = response.get("tasks") or []
    failures = response.get("failures") or []
    if not tasks:
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message=f"ecs:RunTask returned no tasks; failures={failures}",
        )

    return tasks[0]["taskArn"]


# ---- The bootstrap task ----


def _fail_build(build, exc):
    """
    Finalize a build that failed *before* the runner container started.

    The runner's own try/except (``builder.runner.Runner.run``) only
    catches exceptions raised inside the build container. Anything raised
    by ``submit_build_to_ecs`` itself (missing config file, malformed
    YAML, ECS RunTask failure, etc.) never reaches that handler, so the
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


@app.task(bind=True, max_retries=3, default_retry_delay=30, queue="web")
def submit_build_to_ecs(self, build_pk):
    """
    Dispatch a build to AWS Fargate.

    Replaces ``update_docs_task.delay`` for projects with
    ``Feature.USE_FARGATE_BUILDER`` enabled. See module docstring for the
    full flow.
    """
    build = Build.objects.select_related("version__project").get(pk=build_pk)
    version = build.version
    project = version.project

    # The build was cancelled (e.g. via ``cancel_build`` while we were
    # waiting in the Celery queue) before we got a chance to dispatch.
    # Bail out without minting an API key or hitting ECS — the Build
    # already reflects ``state=cancelled``.
    if build.state == BUILD_STATE_CANCELLED:
        log.info(
            "Build was cancelled before Fargate dispatch; skipping.",
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
        _submit_build_to_ecs(build, version, project)
    except (BuildUserError, BuildAppError) as exc:
        # Failures *before* the build container starts never reach the
        # runner's own try/except. Finalize the build at the API layer
        # so the user sees a proper notification + ``finished`` state
        # instead of a build stuck in ``triggered``.
        _fail_build(build, exc)
        log.exception("submit_build_to_ecs failed.")


def _submit_build_to_ecs(build, version, project):
    """
    Inner body of :func:`submit_build_to_ecs` — split out so the caller
    can wrap it in a single try/except that finalizes the build on any
    user / app error. See :func:`_fail_build` for the failure path.
    """
    if not project.has_feature(Feature.USE_FARGATE_BUILDER):
        # Defensive: the dispatcher in ``trigger_build`` shouldn't route here
        # without the flag. If it does, fail loudly rather than silently
        # dispatching to Fargate.
        raise BuildAppError(
            BuildAppError.GENERIC_WITH_BUILD_ID,
            exception_message=(
                f"submit_build_to_ecs called for project '{project.slug}' "
                "without Feature.USE_FARGATE_BUILDER set."
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

    # 2. Resolve per-build resource limits.
    cpu, memory, time_limit = _resolve_fargate_resources(project)
    log.info(
        "Resolved Fargate resources.",
        cpu=cpu,
        memory=memory,
        time_limit=time_limit,
    )

    # 3. Mint a per-build API key (24h-scoped).
    _, build_api_key = BuildAPIKey.objects.create_key(project=project)

    # 4. Submit to ECS (prod) or local Docker (dev).
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

    task_arn = _dispatch_build_task(
        build_pk=build.pk,
        build_os=build_os,
        cpu=cpu,
        memory=memory,
        environment=environment,
        command=command,
    )

    log.info(
        "Dispatched build.",
        backend="docker" if settings.RTD_DOCKER_COMPOSE else "fargate",
        task_arn=task_arn,
    )

    # 5. Store the (pseudo-)ARN so cancel_build can stop the task.
    build.task_arn = task_arn
    build.save(update_fields=["task_arn"])
