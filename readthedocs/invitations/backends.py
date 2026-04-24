"""Backends for the objects from the invitations."""

import structlog
from django.conf import settings
from django.urls import reverse
from django.utils import formats
from django.utils import timesince
from django.utils import translation

from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import send_email
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


class Backend:
    """Base backend to define the behavior of the object attached the the invitation."""

    klass = None

    def __init__(self, invitation):
        self.invitation = invitation
        self.object = invitation.object

    def get_origin_url(self):
        raise NotImplementedError

    def get_success_url(self):
        return self.get_object_url()

    def get_object_url(self):
        raise NotImplementedError

    def get_object_name(self):
        return self.object.slug

    def owns_object(self, user):
        return user in AdminPermission.owners(self.object)

    def redeem(self, user):
        raise NotImplementedError

    def _get_email_object_description(self):
        # We don't want to use the current language when
        # sending the email to the target user.
        with translation.override(settings.LANGUAGE_CODE):
            target_type = self.object._meta.verbose_name
            return f"{self.get_object_name()} {target_type}"

    def send_invitation(self):
        """Send an email with the invitation to join the object."""
        email = self.invitation.to_email
        if not email:
            email = self.invitation.to_user.email

        from_user = self.invitation.from_user
        from_name = from_user.get_full_name() or from_user.username
        object_description = self._get_email_object_description()
        expiration_date = self.invitation.expiration_date
        log.info(
            "Emailing invitation",
            email=email,
            invitation_pk=self.invitation.pk,
            object_type=self.invitation.object_type,
            object_name=self.invitation.object_name,
            object_pk=self.invitation.object.pk,
        )
        send_email(
            recipient=email,
            subject=f"{from_name} has invited you to join the {object_description}",
            template="invitations/email/invitation.txt",
            template_html="invitations/email/invitation.html",
            context={
                "from_name": from_name,
                "object_description": object_description,
                "invite_url": self.invitation.get_absolute_url(),
                "valid_until": timesince.timeuntil(expiration_date),
                "expiration_date": formats.date_format(expiration_date),
            },
        )


class ProjectBackend(Backend):
    klass = Project

    def get_origin_url(self):
        return reverse("projects_users", args=[self.object.slug])

    def get_object_url(self):
        return reverse("projects_detail", args=[self.object.slug])

    def redeem(self, user):
        self.object.users.add(user)
        return True


class OrganizationBackend(Backend):
    klass = Organization

    def get_origin_url(self):
        return reverse("organization_owners", args=[self.object.slug])

    def get_object_url(self):
        return reverse("organization_detail", args=[self.object.slug])

    def redeem(self, user):
        self.object.owners.add(user)
        return True


class TeamBackend(Backend):
    """Team backend."""

    klass = Team

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = self.object.organization

    def get_origin_url(self):
        return reverse("organization_team_detail", args=[self.organization.slug, self.object.slug])

    def get_object_url(self):
        return reverse("organization_team_detail", args=[self.organization.slug, self.object.slug])

    def get_success_url(self):
        return reverse("organization_detail", args=[self.organization.slug])

    def redeem(self, user):
        self.organization.add_member(user, self.object)
        return True

    def owns_object(self, user):
        return user in AdminPermission.owners(self.organization)

    def get_object_name(self):
        return f"{self.organization.slug} {self.object.slug}"


def get_backend(invitation):
    """Get the proper backend for the invitation."""
    backends = [
        OrganizationBackend,
        ProjectBackend,
        TeamBackend,
    ]
    for backend in backends:
        if isinstance(invitation.object, backend.klass):
            return backend(invitation)
    raise ValueError(f"Backend not found for object of class {object.__class__}")
