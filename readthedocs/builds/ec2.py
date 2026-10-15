"""
Scale-in protection and termination for build EC2 instances.

The worker on the instance holds no AWS credentials: it calls the
``instance/protect`` and ``instance/release`` build API endpoints and the web
tier performs the Auto Scaling calls with the ``scalein`` IAM user.
"""

import datetime
import re

import boto3
import structlog
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.models import Build


log = structlog.get_logger(__name__)


# Hostname set by cloud-init: ``build-isolated-i-0123456789abcdef0``.
BUILDER_HOSTNAME_RE = re.compile(r"^([a-z\-]+)-(i-[a-f0-9]+)$")

STATE_TERMINATED = "terminated"
STATE_KEPT = "kept"
STATE_FAILED = "failed"


class InvalidBuilder(ValueError):
    """``Build.builder`` is not a valid build instance hostname."""


def parse_builder(builder: str) -> tuple[str, str]:
    """Return ``(asg_name, instance_id)`` for a build hostname."""
    match = BUILDER_HOSTNAME_RE.match(builder or "")
    if not match or not match.group(1).startswith("build"):
        raise InvalidBuilder(builder)
    return match.group(1), match.group(2)


def _is_dev() -> bool:
    return settings.DEBUG or settings.RTD_DOCKER_COMPOSE


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


def protect_instance(asg_name: str, instance_id: str) -> bool:
    """Protect ``instance_id`` from ASG scale-in."""
    if _is_dev():
        log.info("Development environment. Skipping scale-in protection.")
        return False
    return _set_protection(_autoscaling_client(), asg_name, instance_id, protected=True)


def _queued_builds() -> int | None:
    """Builds dispatched to the isolated queue that no instance has started yet."""
    try:
        return Build.objects.filter(
            state=BUILD_STATE_TRIGGERED,
            dispatched_date__isnull=False,
            date__gte=timezone.now() - datetime.timedelta(days=1),
        ).count()
    except Exception:
        log.exception("Failed to count queued builds.")
        return None


def _idle_instances(client, asg_name: str, instance_id: str) -> int | None:
    """In-service, unprotected instances in the ASG, excluding ``instance_id``."""
    try:
        groups = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name],
        ).get("AutoScalingGroups", [])
    except Exception:
        log.exception("Failed to describe the autoscaling group.", asg_name=asg_name)
        return None

    if not groups:
        log.warning("Autoscaling group not found.", asg_name=asg_name)
        return None

    return sum(
        1
        for instance in groups[0].get("Instances", [])
        if instance.get("InstanceId") != instance_id
        and instance.get("LifecycleState") == "InService"
        and not instance.get("ProtectedFromScaleIn")
    )


def _should_decrement(client, asg_name: str, instance_id: str) -> bool:
    """
    Whether terminating this instance should shrink the fleet.

    Only while nothing is queued and the group already has the warm buffer
    idle; otherwise the ASG replaces it so the next build lands on a warm
    instance. Any failure answers ``False`` so the instance is replaced.
    """
    queued = _queued_builds()
    if queued is None or queued > 0:
        log.info("Builds queued or queue unknown; replacing the instance.", queued=queued)
        return False

    idle = _idle_instances(client, asg_name, instance_id)
    if idle is None:
        return False

    warm_buffer = settings.RTD_BUILD_ISOLATED_WARM_BUFFER
    decrement = idle >= warm_buffer
    log.info(
        "Warm buffer checked.",
        asg_name=asg_name,
        idle=idle,
        warm_buffer=warm_buffer,
        decrement=decrement,
    )
    return decrement


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


def release_instance(asg_name: str, instance_id: str, *, keep: bool = False) -> tuple[str, bool]:
    """
    Release ``instance_id`` once its build is over.

    Clears scale-in protection and terminates the instance, shrinking the
    fleet when the warm buffer allows it. With ``keep`` the instance is left
    running after the protection is cleared. Returns ``(state, decremented)``
    where ``state`` is ``terminated``, ``kept`` or ``failed``.
    """
    if _is_dev():
        log.info("Development environment. Skipping instance release.")
        return STATE_KEPT, False

    client = _autoscaling_client()
    _set_protection(client, asg_name, instance_id, protected=False)

    if keep:
        log.warning("Keeping the instance alive.", instance_id=instance_id)
        return STATE_KEPT, False

    decrement = _should_decrement(client, asg_name, instance_id)
    try:
        _terminate(client, instance_id, decrement)
        return STATE_TERMINATED, decrement
    except ClientError as exc:
        if _is_already_gone(exc):
            log.info("Instance already gone.", instance_id=instance_id)
            return STATE_TERMINATED, False
        if not (decrement and _is_at_min_size(exc)):
            log.exception("Instance termination failed.", instance_id=instance_id)
            return STATE_FAILED, False
    except Exception:
        log.exception("Instance termination failed.", instance_id=instance_id)
        return STATE_FAILED, False

    # Desired already equals MinSize. The instance stopped consuming the queue
    # when its build arrived, so leaving it alive would strand it: terminate
    # without the decrement and let the ASG replace it.
    log.info("Fleet at MinSize; terminating without decrement.", instance_id=instance_id)
    try:
        _terminate(client, instance_id, False)
        return STATE_TERMINATED, False
    except Exception:
        log.exception("Instance termination failed.", instance_id=instance_id)
        return STATE_FAILED, False
