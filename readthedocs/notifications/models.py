import structlog
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_noop as _
from django_extensions.db.models import TimeStampedModel

from .constants import CANCELLED
from .constants import DISMISSED
from .constants import READ
from .constants import UNREAD
from .messages import registry
from .querysets import NotificationQuerySet


log = structlog.get_logger(__name__)


class Notification(TimeStampedModel):
    # Message identifier
    message_id = models.CharField(max_length=128)

    # UNREAD: the notification was not shown to the user
    # READ: the notifiation was shown
    # DISMISSED: the notification was shown and the user dismissed it
    # CANCELLED: removed automatically because the user has done the action required (e.g. paid the subscription)
    state = models.CharField(
        choices=[
            (UNREAD, UNREAD),
            (READ, READ),
            (DISMISSED, DISMISSED),
            (CANCELLED, CANCELLED),
        ],
        default=UNREAD,
        max_length=128,
        db_index=True,
    )

    # Makes the notification imposible to dismiss (useful for Build notifications)
    dismissable = models.BooleanField(default=False)

    # Show the notification under the bell icon for the user
    news = models.BooleanField(default=False, help_text=_("Show under bell icon"))

    # Notification attached to Organization, Project, Build or User
    #
    # Uses ContentType for this.
    # https://docs.djangoproject.com/en/4.2/ref/contrib/contenttypes/#generic-relations
    #
    attached_to_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    attached_to_id = models.PositiveIntegerField()
    attached_to = GenericForeignKey("attached_to_content_type", "attached_to_id")

    # Store values known at creation time that are required to render the final message
    format_values = models.JSONField(null=True, blank=True)

    # Use a custom manager with an ``.add()`` method that deduplicates
    # notifications attached to the same object.
    objects = NotificationQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["attached_to_content_type", "attached_to_id"]),
        ]

    def __str__(self):
        return self.message_id

    def get_message(self):
        # Pass the instance attached to this notification
        format_values = self.format_values or {}
        format_values.update(
            {
                "instance": self.attached_to,
            }
        )

        message = registry.get(self.message_id, format_values=format_values)
        if message is None:
            # Log the error and let the None message return through the API
            log.error(
                "The message ID retrieved is not in our registry anymore.",
                message_id=self.message_id,
            )

        return message

    def get_absolute_url(self):
        content_type_name = self.attached_to_content_type.name
        path = ""
        if content_type_name == "user":
            url = "users-notifications-detail"
            path = reverse(
                url,
                kwargs={
                    "notification_pk": self.pk,
                    "parent_lookup_user__username": self.attached_to.username,
                },
            )

        elif content_type_name == "build":
            url = "projects-builds-notifications-detail"
            project_slug = self.attached_to.project.slug
            path = reverse(
                url,
                kwargs={
                    "notification_pk": self.pk,
                    "parent_lookup_project__slug": project_slug,
                    "parent_lookup_build__id": self.attached_to_id,
                },
            )

        elif content_type_name == "project":
            url = "projects-notifications-detail"
            project_slug = self.attached_to.slug
            path = reverse(
                url,
                kwargs={
                    "notification_pk": self.pk,
                    "parent_lookup_project__slug": project_slug,
                },
            )

        elif content_type_name == "organization":
            url = "organizations-notifications-detail"
            path = reverse(
                url,
                kwargs={
                    "notification_pk": self.pk,
                    "parent_lookup_organization__slug": self.attached_to.slug,
                },
            )
        return path
