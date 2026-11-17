"""Basic tasks."""

import math
from datetime import timedelta

import redis
import requests
import structlog
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db.models import Exists
from django.db.models import F
from django.db.models import OuterRef
from django.utils import timezone

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.builds.utils import memcache_lock
from readthedocs.core.history import set_change_reason
from readthedocs.projects.models import Project
from readthedocs.worker import app


log = structlog.get_logger(__name__)

EMAIL_TIME_LIMIT = 30


@app.task(queue="web", time_limit=EMAIL_TIME_LIMIT)
def send_email_task(recipient, subject, content, content_html=None, from_email=None, **kwargs):
    """
    Send multipart email.

    recipient
        Email recipient address

    subject
        Email subject header

    content
        Plain text template to send

    content_html
        HTML content to send as new message part

    kwargs
        Additional options to the EmailMultiAlternatives option.
    """
    msg = EmailMultiAlternatives(
        subject, content, from_email or settings.DEFAULT_FROM_EMAIL, [recipient], **kwargs
    )
    if content_html:
        msg.attach_alternative(content_html, "text/html")
    log.info("Sending email to recipient.", recipient=recipient)
    msg.send()


@app.task(queue="web")
def cleanup_pidbox_keys():
    """
    Remove "pidbox" reply lists from Redis.

    Workers reply to broadcast commands into a per-requester list with no TTL.
    Replies arriving after the requester stops reading stay there forever.

    Delete lists idle for more than 15 minutes, and lists over
    ``PIDBOX_KEY_MAX_MB`` regardless of idle time (a worker stuck reconnecting
    keeps appending to the same list).

    https://github.com/celery/celery/issues/6089
    https://github.com/readthedocs/readthedocs-ops/issues/1260
    """
    PIDBOX_KEY_IDLE_SECONDS = 60 * 15
    PIDBOX_KEY_MAX_MB = 50

    client = redis.from_url(settings.CELERY_BROKER_URL)
    keys = client.keys("*reply.celery.pidbox*")
    total_memory = 0
    deleted = 0
    sizes = []
    for key in keys:
        idletime = client.object("idletime", key)  # seconds
        memory = math.ceil((client.memory_usage(key) or 0) / 1024 / 1024)  # MB
        total_memory += memory
        sizes.append((memory, key.decode(errors="replace")))

        if idletime > PIDBOX_KEY_IDLE_SECONDS or memory > PIDBOX_KEY_MAX_MB:
            client.delete(key)
            deleted += 1

    log.info(
        "Redis pidbox objects.",
        memory=total_memory,
        keys=len(keys),
        deleted=deleted,
        largest=[f"{key}={memory}MB" for memory, key in sorted(sizes, reverse=True)[:5]],
    )


@app.task(queue="web", bind=True)
def delete_object(self, model_name: str, pk: int, user_id: int | None = None):
    """
    Delete an object from the database asynchronously.

    This is useful for deleting large objects that may take time
    to delete, without timing out the request.

    :param model_name: The model name in the format 'app_label.ModelName'.
    :param pk: The primary key of the object to delete.
    :param user_id: The ID of the user performing the deletion.
     Just for logging purposes.
    """
    task_log = log.bind(model_name=model_name, object_id=pk, user_id=user_id)
    lock_id = f"{self.name}-{model_name}-{pk}-lock"
    lock_expire = 60 * 60 * 2  # 2 hours
    with memcache_lock(
        lock_id=lock_id, lock_expire=lock_expire, app_identifier=self.app.oid
    ) as acquired:
        if not acquired:
            task_log.info("Object is already being deleted.")
            return

        user = User.objects.filter(pk=user_id).first() if user_id else None
        Model = apps.get_model(model_name)
        obj = Model.objects.filter(pk=pk).first()
        if obj:
            task_log.info("Deleting object.")
            set_change_reason(obj, reason="Object deleted asynchronously", user=user)
            obj.delete()
            task_log.info("Object deleted.")
        else:
            task_log.info("Object does not exist.")


@app.task(queue="web")
def subscribe_active_users_to_newsletter(days=1):
    """
    Subscribe users to the newsletter once they've had their first successful build.

    Only users who opted in at signup, aren't banned,
    and have an active (non-spam) project are subscribed.
    This keeps spam signups off the newsletter list.
    """
    if not settings.BUTTONDOWN_API_KEY:
        return

    since = timezone.now() - timedelta(days=days)
    successful_builds = Build.objects.filter(state=BUILD_STATE_FINISHED, success=True)
    recent_user_ids = successful_builds.filter(date__gte=since).values("project__users")
    earlier_builds = successful_builds.filter(project__users=OuterRef("pk"), date__lt=since)
    users = (
        User.objects.filter(
            pk__in=recent_user_ids,
            profile__mailing_list=True,
            profile__banned=False,
            emailaddress__email=F("email"),
            emailaddress__verified=True,
        )
        .exclude(Exists(earlier_builds))
        .distinct()
    )
    for user in users:
        projects = Project.objects.filter(
            users=user,
            builds__success=True,
            builds__date__gte=since,
        ).distinct()
        if not any(Project.objects.is_active(project) for project in projects):
            continue

        log.info("Subscribing user to newsletter.", user_username=user.username)
        try:
            resp = requests.post(
                settings.BUTTONDOWN_API_SUBSCRIBERS_URL,
                # The email is already verified, so skip Buttondown's double opt-in.
                # Existing subscribers return an error instead of being resubscribed.
                json={"email_address": user.email, "type": "regular"},
                headers={"Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"},
                timeout=5,
            )
            if not resp.ok:
                log.warning(
                    "Error subscribing user to newsletter.",
                    user_username=user.username,
                    status_code=resp.status_code,
                    response=resp.text,
                )
        except requests.RequestException:
            log.exception("Error subscribing user to newsletter.", user_username=user.username)
