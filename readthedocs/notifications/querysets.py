from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class NotificationQuerySet(models.QuerySet):
    def add(self, *args, **kwargs):
        """
        Create a notification without duplicating it.

        If a notification with the same ``message_id`` is already attached to the object,
        its ``modified_at`` timestamp is updated.

        Otherwise, a new notification object is created for this object.
        """

        message_id = kwargs.get("message_id")
        attached_to = kwargs.pop("attached_to")

        content_type = ContentType.objects.get_for_model(attached_to)
        notification = self.filter(
            attached_to_content_type=content_type,
            attached_to_id=attached_to.id,
            message_id=message_id,
        ).first()

        if notification:
            self.filter(pk=notification.pk).update(
                *args, modified=timezone.now(), **kwargs
            )
            notification.refresh_from_db()
            return notification

        return super().create(*args, **kwargs)
