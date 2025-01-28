import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from readthedocs.core.notifications import MESSAGE_EMAIL_VALIDATION_PENDING
from readthedocs.notifications.constants import CANCELLED, DISMISSED, READ, UNREAD
from readthedocs.notifications.models import Notification


@pytest.mark.django_db
class TestNotificationQuerySet:
    def test_add(self):
        user = fixture.get(
            User,
        )

        # There is any notification attached to this user
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
            ).count()
            == 0
        )

        Notification.objects.add(
            attached_to=user,
            message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
        )

        # There is 1 notification attached to this user
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
            ).count()
            == 1
        )

        old_notification = Notification.objects.first()
        old_notification.state = READ
        old_notification.save()

        # Add the same notification again
        Notification.objects.add(
            attached_to=user,
            message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
        )

        # Notification is not duplicated, but timestamp and state is updated
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
            ).count()
            == 1
        )

        new_notification = Notification.objects.first()
        assert old_notification.pk == new_notification.pk
        assert old_notification.modified < new_notification.modified
        assert old_notification.state == READ
        assert new_notification.state == UNREAD

        # Add another notification
        Notification.objects.add(
            attached_to=user,
            message_id="user:another:notification",
        )

        # Notification is added
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
            ).count()
            == 2
        )

    def test_cancel(self):
        user = fixture.get(User)

        Notification.objects.add(
            attached_to=user,
            message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
        )

        # There is one UNREAD notification attached to this user
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
                state=UNREAD,
            ).count()
            == 1
        )

        Notification.objects.cancel(
            attached_to=user,
            message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
        )

        # There is none UNREAD notification attached to this user
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
                state=UNREAD,
            ).count()
            == 0
        )

        # There is one CANCELLED notification attached to this user
        assert (
            Notification.objects.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.id,
                state=CANCELLED,
            ).count()
            == 1
        )

    def test_for_user(self):
        user = fixture.get(User)

        Notification.objects.add(
            attached_to=user,
            message_id="user:notification:read",
            state=READ,
        )
        Notification.objects.add(
            attached_to=user,
            message_id="user:notification:unread",
            state=UNREAD,
        )
        Notification.objects.add(
            attached_to=user,
            message_id="user:notification:dismissed",
            state=DISMISSED,
        )
        Notification.objects.add(
            attached_to=user,
            message_id="user:notification:cancelled",
            state=CANCELLED,
        )

        assert [
            n.message_id for n in Notification.objects.for_user(user, resource="all")
        ] == [
            "user:notification:read",
            "user:notification:unread",
        ]
