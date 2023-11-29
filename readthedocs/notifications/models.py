import textwrap

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_noop as _
from django_extensions.db.models import TimeStampedModel

from .constants import CANCELLED, DISMISSED, READ, UNREAD
from .messages import NOTIFICATION_MESSAGES


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

    def __str__(self):
        return self.message_id

    def get_message(self):
        return NOTIFICATION_MESSAGES.get(self.message_id)

    def get_header(self):
        return NOTIFICATION_MESSAGES.get(self.message_id).header

    def get_display_header(self):
        return textwrap.dedent(
            NOTIFICATION_MESSAGES.get(self.message_id).header.format(
                instance=self.attached_to,  # Build, Project, Organization, User
                **self.format_values,
            )
        )

    def get_body(self):
        return NOTIFICATION_MESSAGES.get(self.message_id).body

    def get_display_body(self):
        return textwrap.dedent(
            NOTIFICATION_MESSAGES.get(self.message_id).body.format(
                instance=self.attached_to,  # Build, Project, Organization, User
                **self.format_values,
            )
        )
