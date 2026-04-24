"""Invitation models."""

import structlog
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from readthedocs.audit.models import AuditLog
from readthedocs.invitations.backends import get_backend


log = structlog.get_logger(__name__)


class InvitationQueryset(models.QuerySet):
    """Invitation queryset."""

    def expired(self, obj=None):
        queryset = self.filter(expiration_date__lte=timezone.now())
        if obj:
            queryset = self._for_object(obj=obj, queryset=queryset)
        return queryset

    def pending(self, obj=None):
        queryset = self.filter(expiration_date__gt=timezone.now())
        if obj:
            queryset = self._for_object(obj=obj, queryset=queryset)
        return queryset

    def invite(self, from_user, obj, to_user=None, to_email=None, request=None):
        """
        Create and send an invitation for `to_user` or `to_email` to join `object`.

        If the invitation already exists, we don't send the invitation again.

        :param request: If given, a log entry will be created.
        """
        if not to_user and not to_email:
            raise ValueError("A user or email must be provided")

        fields = {
            "content_type": ContentType.objects.get_for_model(obj),
            "object_id": obj.pk,
        }
        if to_user:
            fields["to_user"] = to_user
        else:
            fields["to_email"] = to_email

        invitation, created = self.get_or_create(
            **fields,
            defaults={
                "from_user": from_user,
            },
        )
        if created:
            if request:
                invitation.create_audit_log(
                    action=AuditLog.INVITATION_SENT,
                    request=request,
                    user=request.user,
                )
            invitation.send()
        return invitation, created

    def for_object(self, obj):
        return self._for_object(obj=obj, queryset=self.all())

    @staticmethod
    def _for_object(obj, queryset):
        return queryset.filter(
            object_id=obj.pk,
            content_type=ContentType.objects.get_for_model(obj),
        )


class Invitation(TimeStampedModel):
    """
    Invitation model.

    An invitation can be attached to an existing user or to an email.
    """

    # Generic foreign key.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey("content_type", "object_id")

    # Normal fields.
    from_user = models.ForeignKey(
        User,
        verbose_name=_("From user"),
        on_delete=models.CASCADE,
        related_name="invitations_sent",
    )
    to_user = models.ForeignKey(
        User,
        verbose_name=_("To user"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="invitations_received",
    )
    to_email = models.EmailField(_("E-mail"), null=True, blank=True)
    token = models.CharField(
        unique=True,
        max_length=32,
    )
    expiration_date = models.DateTimeField(_("Expiration date"))

    objects = InvitationQueryset.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        unique_together = [
            ("to_user", "content_type", "object_id"),
            ("to_email", "content_type", "object_id"),
        ]

    @property
    def username(self):
        if self.to_user:
            return self.to_user.username
        return self.to_email

    @property
    def expired(self):
        return timezone.now() > self.expiration_date

    @cached_property
    def backend(self):
        return get_backend(self)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()

        if not self.expiration_date:
            self.expiration_date = timezone.now() + timezone.timedelta(
                days=settings.RTD_INVITATIONS_EXPIRATION_DAYS
            )

        super().save(*args, **kwargs)

    @staticmethod
    def generate_token():
        return get_random_string(32)

    def redeem(self, user=None, request=None):
        """
        Redeem invitation.

        `user` will be used only if the invitation is attached
        to an email, otherwise `to_user` user will be used.

        :param request: If given, a log entry will be created.
        """
        if self.expired:
            return False
        if self.to_user:
            user = self.to_user
        log.info(
            "Redeeming invitation",
            invitation_pk=self.pk,
            for_user=user.username,
            object_type=self.object_type,
            object_name=self.object_name,
            object_pk=self.object.pk,
        )
        if request:
            self.create_audit_log(
                action=AuditLog.INVITATION_ACCEPTED,
                request=request,
                user=user,
            )
        return self.backend.redeem(user=user)

    def get_success_url(self):
        """URL to redirect after the invitation has been redeemed."""
        return self.backend.get_success_url()

    def get_origin_url(self):
        """URL from where the invitations for the object are created."""
        return self.backend.get_origin_url()

    def get_absolute_url(self):
        return reverse("invitations_redeem", args=[self.token])

    def can_revoke_invitation(self, user):
        """
        Check whether the user can revoke the invitation.

        A user can revoke an invitation if it's the owner
        of the object attached to it.
        """
        return self.backend.owns_object(user)

    @property
    def object_type(self):
        return self.content_type.model

    @property
    def object_name(self):
        return self.backend.get_object_name()

    @property
    def object_url(self):
        return self.backend.get_object_url()

    def send(self):
        self.backend.send_invitation()

    def create_audit_log(self, action, request, user=None):
        """Create an audit log entry for this invitation."""
        from readthedocs.audit.serializers import InvitationSerializer

        # Attach the proper project and organization to the log.
        kwargs = {}
        object_type = self.object_type
        if object_type == "organization":
            kwargs["organization"] = self.object
        elif object_type == "project":
            kwargs["project"] = self.object
        elif object_type == "team":
            kwargs["organization"] = self.object.organization

        AuditLog.objects.new(
            action=action,
            request=request,
            data=InvitationSerializer(self).data,
            user=user,
            **kwargs,
        )
