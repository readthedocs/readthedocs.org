from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from .constants import CANCELLED, READ, UNREAD


class NotificationQuerySet(models.QuerySet):
    def add(self, *args, **kwargs):
        """
        Create a notification without duplicating it.

        If a notification with the same ``message_id`` is already attached to the object,
        its ``modified_at`` timestamp and ``state`` is updated.

        Otherwise, a new notification object is created for this object.
        """

        message_id = kwargs.get("message_id")
        attached_to = kwargs.pop("attached_to")

        content_type = ContentType.objects.get_for_model(attached_to)
        notification = self.filter(
            attached_to_content_type=content_type,
            attached_to_id=attached_to.id,
            message_id=message_id,
            # Update only ``READ`` and ``UNREAD`` notifications because we want
            # to keep track of ``DISMISSED`` and ``CANCELLED`` ones.
            state__in=(UNREAD, READ),
        ).first()

        if notification:
            self.filter(pk=notification.pk).update(
                *args,
                modified=timezone.now(),
                state=UNREAD,
                **kwargs,
            )
            notification.refresh_from_db()
            return notification

        return super().create(*args, attached_to=attached_to, **kwargs)

    def cancel(self, message_id, attached_to):
        """
        Cancel an on-going notification because the underlying state has changed.

        When a notification is not valid anymore because the user has made the
        required action (e.g. paid an unpaid subscription) we use this method
        to mark those notifications as ``CANCELLED``.

        It only cancels notifications that are ``UNREAD`` or ``READ``.
        """
        content_type = ContentType.objects.get_for_model(attached_to)

        self.filter(
            attached_to_content_type=content_type,
            attached_to_id=attached_to.id,
            message_id=message_id,
            state__in=(UNREAD, READ),
        ).update(
            state=CANCELLED,
            modified=timezone.now(),
        )

    def _for_object(self, obj):
        """
        Generic method to return notifications attached to a particular object.

        It only returns notifications that are ``READ`` or ``UNREAD``.
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(
            attached_to_content_type=content_type,
            attached_to_id=obj.id,
            state__in=(UNREAD, READ),
        )

    def for_user(self, user):
        """
        Return all the notifications to shown to the user.

        It uses ``_for_object()`` behind the scenes which returns only ``READ``
        and ``UNREAD`` notifications.
        """
        return self._for_object(user)
