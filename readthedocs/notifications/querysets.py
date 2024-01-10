from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Subquery
from django.utils import timezone

from readthedocs.core.permissions import AdminPermission


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

        return super().create(*args, attached_to=attached_to, **kwargs)

    def for_user(self, user):
        """
        Retrieve all notifications related to a particular user.

        Given a user, returns all the notifications that:

         - are attached to an ``Organization`` where the user is owner
         - are attached to a ``Project`` where the user is admin
         - are attacehd to the ``User`` themselves
        """
        # Need to be here due to circular imports
        from readthedocs.organizations.models import Organization
        from readthedocs.projects.models import Project

        # http://chibisov.github.io/drf-extensions/docs/#usage-with-generic-relations
        user_notifications = self.filter(
            attached_to_content_type=ContentType.objects.get_for_model(User),
            attached_to_id=user.pk,
        )

        # NOTE: using ``Subquery`` work better regarding performance since it makes only one query to the databse,
        # instead of doing one to get the ids and another one to get the notifications.
        # It also works better for users that have many projects/organizations since we don't need to load the ids
        # in memory and then dump them into the SQL query.
        # Besides, it performs better when applying the filters via ``NotificationFilter``
        project_notifications = self.filter(
            attached_to_content_type=ContentType.objects.get_for_model(Project),
            attached_to_id__in=Subquery(
                AdminPermission.projects(
                    user,
                    admin=True,
                    member=False,
                ).values("id")
            ),
        )
        organization_notifications = self.filter(
            attached_to_content_type=ContentType.objects.get_for_model(Organization),
            attached_to_id__in=Subquery(
                AdminPermission.organizations(
                    user,
                    admin=True,
                    member=False,
                ).values("id")
            ),
        )

        # Return all the notifications related to this user attached to:
        # User, Project and Organization models where the user is admin.
        return user_notifications | project_notifications | organization_notifications
