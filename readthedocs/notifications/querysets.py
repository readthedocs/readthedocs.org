from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from readthedocs.core.permissions import AdminPermission
from readthedocs.core.querysets import NoReprQuerySet

from .constants import CANCELLED
from .constants import READ
from .constants import UNREAD


class NotificationQuerySet(NoReprQuerySet, models.QuerySet):
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
            # Remove the fields we are overriding.
            # Avoids passing these fields twice to ``.update()`` which
            # raises an exception in that case.
            kwargs.pop("state", None)
            kwargs.pop("modified", None)

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

    def for_user(self, user, resource):
        """
        Retrieve notifications related to resource for a particular user.

        Given a user, returns all the notifications for the specified ``resource``
        considering permissions (e.g. does not return any notification if the ``user``
        doesn't have admin permissions on the ``resource``).

        If ``resource="all"``, it returns the following notifications:

         - are attached to an ``Organization`` where the user is owner
         - are attached to a ``Project`` where the user is admin
         - are attacehd to the ``User`` themselves

        It only returns notifications that are ``READ`` or ``UNREAD``.
        """
        # Need to be here due to circular imports
        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        if resource == "all":
            # http://chibisov.github.io/drf-extensions/docs/#usage-with-generic-relations
            user_notifications = self.filter(
                attached_to_content_type=ContentType.objects.get_for_model(User),
                attached_to_id=user.pk,
            )

            project_notifications = self.filter(
                attached_to_content_type=ContentType.objects.get_for_model(Project),
                attached_to_id__in=AdminPermission.projects(
                    user,
                    admin=True,
                    member=False,
                ).values("id"),
            )

            organization_notifications = self.filter(
                attached_to_content_type=ContentType.objects.get_for_model(Organization),
                attached_to_id__in=AdminPermission.organizations(
                    user,
                    owner=True,
                    member=False,
                ).values("id"),
            )

            # Return all the notifications related to this user attached to:
            # User, Project and Organization models where the user is admin.
            return (user_notifications | project_notifications | organization_notifications).filter(
                state__in=(UNREAD, READ)
            )

        if isinstance(resource, User):
            if user == resource:
                return self.filter(
                    attached_to_content_type=ContentType.objects.get_for_model(resource),
                    attached_to_id=resource.pk,
                    state__in=(UNREAD, READ),
                )

        if isinstance(resource, Project):
            if resource in AdminPermission.projects(user, admin=True, member=False):
                return self.filter(
                    attached_to_content_type=ContentType.objects.get_for_model(resource),
                    attached_to_id=resource.pk,
                    state__in=(UNREAD, READ),
                )

        if isinstance(resource, Organization):
            if resource in AdminPermission.organizations(
                user,
                owner=True,
                member=False,
            ):
                return self.filter(
                    attached_to_content_type=ContentType.objects.get_for_model(resource),
                    attached_to_id=resource.pk,
                    state__in=(UNREAD, READ),
                )

        return self.none()
