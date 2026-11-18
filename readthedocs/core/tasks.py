"""Basic tasks."""

import math

import redis
import structlog
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives

from readthedocs.builds.utils import memcache_lock
from readthedocs.core.history import set_change_reason
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
