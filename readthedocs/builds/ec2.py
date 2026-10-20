"""
Fleet sizing, scale-in protection and termination for build EC2 instances.

The worker on the instance holds no AWS credentials: it calls the
``instance/protect`` and ``instance/release`` build API endpoints and the web
tier performs the Auto Scaling calls with the ``scalein`` IAM user.

A periodic task raises desired capacity so a buffer of idle instances stays
ahead of demand, and every finished build terminates its own instance
with a decrement, so idle capacity never grows and nothing has to scale in.
"""

import datetime
import re
from enum import StrEnum

import boto3
import structlog
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.models import Build


log = structlog.get_logger(__name__)


# Hostname set by cloud-init: ``build-isolated-i-0123456789abcdef0``.
BUILDER_HOSTNAME_RE = re.compile(r"^([a-z\-]+)-(i-[a-f0-9]+)$")


class InstanceState(StrEnum):
    """Outcome of an instance release, as reported to the worker."""

    TERMINATED = "terminated"
    KEPT = "kept"
    FAILED = "failed"


class InvalidBuilder(ValueError):
    """``Build.builder`` is not a valid build instance hostname."""


def parse_builder(builder: str) -> tuple[str, str]:
    """Return ``(asg_name, instance_id)`` for a build hostname."""
    match = BUILDER_HOSTNAME_RE.match(builder or "")
    if not match or not match.group(1).startswith("build"):
        raise InvalidBuilder(builder)
    return match.group(1), match.group(2)


def _autoscaling_client():
    return boto3.client(
        "autoscaling",
        aws_access_key_id=settings.RTD_AWS_SCALE_IN_ACCESS_KEY,
        aws_secret_access_key=settings.RTD_AWS_SCALE_IN_SECRET_ACCESS_KEY,
        region_name=settings.RTD_AWS_SCALE_IN_REGION_NAME,
    )


def _set_protection(client, asg_name: str, instance_id: str, protected: bool) -> bool:
    try:
        client.set_instance_protection(
            InstanceIds=[instance_id],
            AutoScalingGroupName=asg_name,
            ProtectedFromScaleIn=protected,
        )
    except Exception:
        log.exception(
            "Failed to set scale-in protection.",
            instance_id=instance_id,
            protected=protected,
        )
        return False

    log.info("Scale-in protection set.", instance_id=instance_id, protected=protected)
    return True


def protect_instance(builder: str) -> bool:
    """
    Protect the instance behind the ``builder`` hostname from ASG scale-in.

    In development there is no instance, so any hostname is accepted and
    nothing is called. Raises ``InvalidBuilder`` otherwise if the hostname
    isn't a build instance.
    """
    if settings.RTD_DOCKER_COMPOSE:
        log.info("Development environment. Skipping scale-in protection.", builder=builder)
        return False
    asg_name, instance_id = parse_builder(builder)
    return _set_protection(_autoscaling_client(), asg_name, instance_id, protected=True)


def _dispatched_builds() -> int:
    """
    Builds dispatched to the isolated fleet that haven't finished, queued or running.

    One instance is needed per build counted here. Same query as the
    "Builds dispatched" CloudWatch metric.
    """
    return (
        Build.objects.filter(
            dispatched_date__isnull=False,
            date__gte=timezone.now() - datetime.timedelta(days=1),
        )
        .exclude(state__in=BUILD_FINAL_STATES)
        .count()
    )


def _describe_group(client, asg_name: str) -> dict | None:
    """The ASG as ``DescribeAutoScalingGroups`` returns it, or ``None`` if missing."""
    groups = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name],
    ).get("AutoScalingGroups", [])
    if not groups:
        log.warning("Autoscaling group not found.", asg_name=asg_name)
        return None
    return groups[0]


def ensure_warm_buffer():
    """
    Raise the fleet's desired capacity so ``RTD_BUILD_ISOLATED_BUFFER`` idle
    instances stay ahead of demand.

    Called every few seconds from the ``autoscaling`` queue. Desired must cover
    every dispatched build plus the buffer. This only ever raises desired: a
    finished build removes its instance and its demand together.
    """
    # NOTE: eventually, when we have more ASG running isolated builds,
    # we will want to get the ASG name from the queue name (e.g., "build:isolated-large").
    asg_name = settings.RTD_BUILD_ISOLATED_ASG_NAME
    if settings.RTD_DOCKER_COMPOSE or not asg_name:
        return

    try:
        client = _autoscaling_client()
        group = _describe_group(client, asg_name)
        if group is None:
            return

        desired = group["DesiredCapacity"]
        dispatched = _dispatched_builds()
        target = min(dispatched + settings.RTD_BUILD_ISOLATED_BUFFER, group["MaxSize"])
        log.info(
            "Warm buffer checked.",
            asg_name=asg_name,
            dispatched=dispatched,
            desired=desired,
            target=target,
        )
        if target <= desired:
            return

        client.set_desired_capacity(
            AutoScalingGroupName=asg_name,
            DesiredCapacity=target,
            HonorCooldown=False,
        )
        log.info("Warm buffer lifted.", asg_name=asg_name, desired=desired, target=target)
    except Exception:
        log.exception("Failed to lift the warm buffer.", asg_name=asg_name)


def _error_message(exc: ClientError) -> str:
    return exc.response.get("Error", {}).get("Message", "").lower()


def _is_at_min_size(exc: ClientError) -> bool:
    """AWS refuses to decrement desired capacity below the group's MinSize."""
    message = _error_message(exc)
    return "minsize" in message or "min size" in message


def _is_already_gone(exc: ClientError) -> bool:
    """The instance already left the group (a retried release)."""
    return "not found" in _error_message(exc)


def _terminate(client, instance_id: str, decrement: bool):
    client.terminate_instance_in_auto_scaling_group(
        InstanceId=instance_id,
        ShouldDecrementDesiredCapacity=decrement,
    )
    log.info("Instance termination requested.", instance_id=instance_id, decrement=decrement)


def release_instance(builder: str, *, keep: bool = False) -> tuple[InstanceState, bool]:
    """
    Release the instance behind the ``builder`` hostname once its build is over.

    Clears scale-in protection and terminates the instance, always decrementing
    desired capacity. With ``keep`` the instance is left running after the protection is
    cleared. Returns ``(state, decremented)`` where ``state`` is
    ``terminated``, ``kept`` or ``failed``. In development there is no instance:
    any hostname is accepted and ``kept`` is returned. Raises ``InvalidBuilder``
    otherwise if the hostname isn't a build instance.
    """
    if settings.RTD_DOCKER_COMPOSE:
        log.info("Development environment. Skipping instance release.", builder=builder)
        return InstanceState.KEPT, False

    asg_name, instance_id = parse_builder(builder)
    client = _autoscaling_client()
    _set_protection(client, asg_name, instance_id, protected=False)

    if keep:
        log.warning("Keeping the instance alive.", instance_id=instance_id)
        return InstanceState.KEPT, False

    try:
        _terminate(client, instance_id, True)
        return InstanceState.TERMINATED, True
    except ClientError as exc:
        if _is_already_gone(exc):
            log.info("Instance already gone.", instance_id=instance_id)
            return InstanceState.TERMINATED, False

        if _is_at_min_size(exc):
            # Desired already equals MinSize. The instance stopped consuming the queue
            # when its build arrived, so leaving it alive would strand it: terminate
            # without the decrement and let the ASG replace it.
            log.info("Fleet at MinSize; terminating without decrement.", instance_id=instance_id)
            try:
                _terminate(client, instance_id, False)
                return InstanceState.TERMINATED, False
            except Exception:
                log.exception("Instance termination failed.", instance_id=instance_id)
                return InstanceState.FAILED, False
        else:
            log.exception("Instance termination failed.", instance_id=instance_id)
            return InstanceState.FAILED, False
    except Exception:
        log.exception("Instance termination failed.", instance_id=instance_id)
        return InstanceState.FAILED, False
