"""Backends for the objects from the invitations."""
import structlog
from django.urls import reverse
from django.utils import formats, timesince

from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import send_email
from readthedocs.organizations.models import Organization, Team
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
        return self.object.name

    def owns_object(self, user):
        raise NotImplementedError

    def redeem(self, user):
        raise NotImplementedError

    def get_object_description(self):
        raise NotImplementedError

    def send_invitation(self):
        """Send an email with the invitation to join the object."""
        email = self.invitation.to_email
        if not email:
            email = self.invitation.to_user.email

        from_user = self.invitation.from_user
        from_name = from_user.get_full_name() or from_user.username
        object_description = self.get_object_description()
        expiration_date = self.invitation.expiration_date
        log.info("Emailing invitation", email=email, invitation_pk=self.invitation.pk)
        send_email(
            recipient=email,
            subject=f"{from_name} has invite you to join the {object_description}",
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

    def owns_object(self, user):
        return user in AdminPermission.owners(self.object)

    def get_object_description(self):
        return f"{self.object.slug} project"


class OrganizationBackend(Backend):

    klass = Organization

    def get_origin_url(self):
        return reverse("organization_owners", args=[self.object.slug])

    def get_object_url(self):
        return reverse("organization_detail", args=[self.object.slug])

    def redeem(self, user):
        self.object.owners.add(user)
        return True

    def owns_object(self, user):
        return user in AdminPermission.owners(self.object)

    def get_object_description(self):
        return f"{self.object.slug} organization"


class TeamBackend(Backend):

    """Team backend."""

    klass = Team

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = self.object.organization

    def get_origin_url(self):
        return reverse(
            "organization_team_detail", args=[self.organization.slug, self.object.slug]
        )

    def get_object_url(self):
        return reverse(
            "organization_team_detail", args=[self.organization.slug, self.object.slug]
        )

    def get_success_url(self):
        return reverse("organization_detail", args=[self.organization.slug])

    def redeem(self, user):
        self.organization.add_member(user, self.object)
        return True

    def owns_object(self, user):
        return user in AdminPermission.owners(self.organization)

    def get_object_description(self):
        return f"{self.object.slug} team from the {self.organization.slug} organization"


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
