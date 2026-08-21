"""Organizations models."""

from pathlib import Path
from uuid import uuid4

import structlog
from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import storages
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _
from django_gravatar.helpers import get_gravatar_url
from djstripe.enums import SubscriptionStatus

from readthedocs.core.history import ExtraHistoricalRecords
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import slugify
from readthedocs.notifications.models import Notification

from . import constants
from .managers import TeamManager
from .managers import TeamMemberManager
from .querysets import OrganizationQuerySet
from .utils import send_team_add_email


log = structlog.get_logger(__name__)


def _upload_organization_avatar_to(instance, filename):
    """
    Generate the upload path for the organization avatar.

    The name of the file is an UUID, and the extension is preserved.
    If the instance already has an avatar, we use its name to keep the same UUID.
    """
    extension = filename.split(".")[-1].lower()
    try:
        previous_avatar = Organization.objects.get(pk=instance.pk).avatar
    except Organization.DoesNotExist:
        previous_avatar = None

    if not previous_avatar:
        uuid = uuid4().hex
    else:
        uuid = Path(previous_avatar.name).stem
    return f"avatars/organizations/{uuid}.{extension}"


def _get_user_content_storage():
    """
    Get the storage for user content.

    Use a function for storage instead of directly assigning the instance
    to avoid hardcoding the backend in the migration file.
    """
    return storages["usercontent"]


class Organization(models.Model):
    """Organization model."""

    # Auto fields
    pub_date = models.DateTimeField(_("Publication date"), auto_now_add=True)
    modified_date = models.DateTimeField(_("Modified date"), auto_now=True)

    # Foreign
    projects = models.ManyToManyField(
        "projects.Project",
        verbose_name=_("Projects"),
        related_name="organizations",
        blank=True,
    )
    owners = models.ManyToManyField(
        User,
        verbose_name=_("Owners"),
        related_name="owner_organizations",
        through="OrganizationOwner",
    )

    # Local
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        null=False,
        blank=False,
    )
    email = models.EmailField(
        _("Email"),
        help_text="Best email address for billing related inquiries",
        max_length=255,
        blank=True,
        null=True,
    )
    description = models.TextField(
        _("Description"),
        help_text="A short description shown on your profile page",
        blank=True,
        null=True,
    )
    url = models.URLField(
        _("Home Page"),
        help_text="The main website for your organization",
        max_length=255,
        blank=True,
        null=True,
    )
    never_disable = models.BooleanField(
        _("Never disable"),
        help_text="Never disable this organization, even if its subscription ends",
        # TODO: remove after migration
        null=True,
        default=False,
    )
    disabled = models.BooleanField(
        _("Disabled"),
        help_text="Docs and builds are disabled for this organization",
        default=False,
    )
    artifacts_cleaned = models.BooleanField(
        _("Artifacts Cleaned"),
        help_text="Artifacts are cleaned out from storage",
        default=False,
    )
    max_concurrent_builds = models.IntegerField(
        _("Maximum concurrent builds allowed for this organization"),
        null=True,
        blank=True,
    )

    # TODO: This field can be removed, we are now using stripe_customer instead.
    stripe_id = models.CharField(
        _("Stripe customer ID"),
        max_length=100,
        blank=True,
        null=True,
    )
    stripe_customer = models.OneToOneField(
        "djstripe.Customer",
        verbose_name=_("Stripe customer"),
        on_delete=models.SET_NULL,
        related_name="rtd_organization",
        null=True,
        blank=True,
    )
    stripe_subscription = models.OneToOneField(
        "djstripe.Subscription",
        verbose_name=_("Stripe subscription"),
        on_delete=models.SET_NULL,
        related_name="rtd_organization",
        null=True,
        blank=True,
    )

    notifications = GenericRelation(
        Notification,
        related_query_name="organization",
        content_type_field="attached_to_content_type",
        object_id_field="attached_to_id",
    )

    avatar = models.ImageField(
        _("Avatar"),
        upload_to=_upload_organization_avatar_to,
        storage=_get_user_content_storage,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
        blank=True,
        null=True,
        help_text="Avatar for your organization (JPG or PNG format, max 500x500px, 750KB)",
    )

    # Managers
    objects = OrganizationQuerySet.as_manager()
    history = ExtraHistoricalRecords()

    class Meta:
        base_manager_name = "objects"
        verbose_name = _("organization")
        ordering = ["name"]
        get_latest_by = ["-pub_date"]

    def __str__(self):
        return self.name

    def get_stripe_subscription(self):
        status_priority = [
            # Past due and unpaid should be taken into consideration first,
            # as the user needs to pay before they can access the service.
            # See https://docs.stripe.com/billing/subscriptions/overview#subscription-statuses.
            SubscriptionStatus.unpaid,
            SubscriptionStatus.past_due,
            SubscriptionStatus.incomplete_expired,
            SubscriptionStatus.incomplete,
            SubscriptionStatus.active,
            SubscriptionStatus.trialing,
        ]
        for status in status_priority:
            subscriptions = self.stripe_customer.subscriptions.filter(status=status)
            if subscriptions.exists():
                if subscriptions.count() > 1:
                    # NOTE: this should never happen, unless we manually
                    # created another subscription for the user or if there
                    # is a bug in our code.
                    log.exception(
                        "Organization has more than one subscription with the same status",
                        organization_slug=self.slug,
                        subscription_status=status,
                    )

                return subscriptions.order_by("created").last()

        # Fall back to the most recently created subscription.
        return self.stripe_customer.subscriptions.order_by("created").last()

    def get_absolute_url(self):
        return reverse("organization_detail", args=(self.slug,))

    @property
    def users(self):
        return AdminPermission.members(self)

    @property
    def members(self):
        return AdminPermission.members(self)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if self.stripe_customer:
            self.stripe_id = self.stripe_customer.id

        # If the avatar is being changed, delete the previous one.
        try:
            previous_avatar = Organization.objects.get(pk=self.pk).avatar
        except Organization.DoesNotExist:
            previous_avatar = None
        if previous_avatar and previous_avatar != self.avatar:
            previous_avatar.delete(save=False)

        super().save(*args, **kwargs)

    def get_stripe_metadata(self):
        """Get metadata for the stripe account."""
        return {
            "org:id": self.id,
            "org:slug": self.slug,
        }

    def add_member(self, user, team):
        """
        Add member to organization team.

        user
            User to add to organization team

        team
            Team instance to add user to
        """
        member = team.members.filter(pk=user.pk).first()
        if not member:
            member = TeamMember.objects.create(team=team, member=user)
        return member

    def get_avatar_url(self):
        """
        Get the URL of the organization's avatar.

        Use the `avatar` field if it exists, otherwise use
        the gravatar from the organization's email.
        """
        if self.avatar:
            return self.avatar.url
        if self.email:
            return get_gravatar_url(self.email, size=100)
        return settings.GRAVATAR_DEFAULT_IMAGE

    def delete(self, *args, **kwargs):
        """Override delete method to clean up related resources."""
        # Delete the avatar file.
        if self.avatar:
            self.avatar.delete(save=False)
        super().delete(*args, **kwargs)


class OrganizationOwner(models.Model):
    """Intermediate table for Organization <-> User relationships."""

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )


class Team(models.Model):
    """Team model."""

    # Auto fields
    pub_date = models.DateTimeField(_("Publication date"), auto_now_add=True)
    modified_date = models.DateTimeField(_("Modified date"), auto_now=True)

    # Foreign
    organization = models.ForeignKey(
        Organization,
        related_name="teams",
        on_delete=models.CASCADE,
    )
    projects = models.ManyToManyField(
        "projects.Project",
        verbose_name=_("Projects"),
        related_name="teams",
        blank=True,
    )
    members = models.ManyToManyField(
        User,
        verbose_name=_("Users"),
        related_name="teams",
        blank=True,
        through="TeamMember",
    )

    # Local
    name = models.CharField(_("Name"), max_length=100)
    slug = AutoSlugField(
        populate_from="name",
        always_update=True,
        unique_with=["organization"],
    )
    access = models.CharField(
        _("Access"),
        max_length=100,
        choices=constants.ACCESS_LEVELS,
        default="readonly",
    )

    auto_join_email_users = models.BooleanField(
        default=False,
        help_text="Auto join users with an organization's email address to this team.",
    )

    # Managers
    objects = TeamManager()
    history = ExtraHistoricalRecords()

    class Meta:
        base_manager_name = "objects"
        verbose_name = _("team")
        unique_together = (
            ("slug", "organization"),
            ("name", "organization"),
        )

    def get_absolute_url(self):
        return reverse(
            "organization_team_detail",
            args=(self.organization.slug, self.slug),
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TeamInvite(models.Model):
    """Model to keep track of invitations to an organization."""

    # Auto fields
    pub_date = models.DateTimeField(_("Publication date"), auto_now_add=True)
    modified_date = models.DateTimeField(_("Modified date"), auto_now=True)

    # Foreign
    organization = models.ForeignKey(
        Organization,
        related_name="invites",
        on_delete=models.CASCADE,
    )
    team = models.ForeignKey(
        Team,
        verbose_name=_("Team"),
        related_name="invites",
        on_delete=models.CASCADE,
    )

    email = models.EmailField(_("E-mail"))
    hash = models.CharField(_("Hash"), max_length=250)
    count = models.IntegerField(_("Count"), default=0)
    total = models.IntegerField(_("Total"), default=10)

    class Meta:
        unique_together = ("team", "email")

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        hash_ = salted_hmac(
            # HMAC key per applications
            ".".join([self.__module__, self.__class__.__name__]),
            # HMAC message
            "".join([str(self.team), str(self.email)]),
        )
        self.hash = hash_.hexdigest()[::2]
        super().save(*args, **kwargs)

    def migrate(self):
        """
        Migrate this invite to our new invitations model.

        New invitations require a from_user, old invitations don't
        track this, so we default to the first owner of the organization.

        The related TeamMember model will be deleted,
        so the invitation isn't listed twice in the team members page.
        """
        from readthedocs.invitations.models import Invitation

        owner = self.organization.owners.first()
        content_type = ContentType.objects.get_for_model(self.team)
        invitation, created = Invitation.objects.get_or_create(
            token=self.hash,
            defaults={
                "from_user": owner,
                "to_email": self.email,
                "content_type": content_type,
                "object_id": self.team.pk,
            },
        )
        self.teammember_set.all().delete()
        return invitation, created


class TeamMember(models.Model):
    """Intermediate table for Team <-> Member/Invite relationships."""

    class Meta:
        unique_together = (
            ("team", "member", "invite"),
            ("team", "member"),
            ("team", "invite"),
        )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
    )
    member = models.ForeignKey(
        User,
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
    )
    invite = models.ForeignKey(
        TeamInvite,
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    objects = TeamMemberManager()

    @property
    def username(self):
        """Return member username or invite email as username."""
        if self.is_member:
            return self.member.username

        if self.invite is not None:
            return self.invite.email

        return "Unknown"

    def get_full_name(self):
        """Return member or invite full name."""
        if self.is_member:
            return self.member.get_full_name()
        return ""

    @property
    def full_name(self):
        """
        Alias property for `get_full_name`.

        This is deprecated, use `get_full_name` as it matches the underlying
        :py:method:`User.get_full_name`.
        """
        return self.get_full_name()

    @property
    def email(self):
        """Return member or invite email address."""
        if self.is_member:
            return self.member.email
        return self.invite.email

    @property
    def is_member(self):
        """Is this team member a user yet."""
        return self.member is not None

    @property
    def is_invite(self):
        """Is this team member pending invite accept."""
        return self.member is None and self.invite is not None

    def send_add_notification(self, request):
        """Notify member of being added to a team."""
        send_team_add_email(team_member=self, request=request)
