"""Organizations models."""
import structlog
from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _
from djstripe.enums import SubscriptionStatus

from readthedocs.core.history import ExtraHistoricalRecords
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.utils import slugify

from . import constants
from .managers import TeamManager, TeamMemberManager
from .querysets import OrganizationQuerySet
from .utils import send_team_add_email

log = structlog.get_logger(__name__)


class Organization(models.Model):

    """
    Organization model.

    stripe_id: Customer id from Stripe API
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # Foreign
    projects = models.ManyToManyField(
        'projects.Project',
        verbose_name=_('Projects'),
        related_name='organizations',
    )
    owners = models.ManyToManyField(
        User,
        verbose_name=_('Owners'),
        related_name='owner_organizations',
        through='OrganizationOwner',
    )

    # Local
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(
        _('Slug'),
        max_length=255,
        unique=True,
        null=False,
        blank=False,
    )
    email = models.EmailField(
        _('E-mail'),
        help_text='How can we get in touch with you?',
        max_length=255,
        blank=True,
        null=True,
    )
    description = models.TextField(
        _('Description'),
        help_text='Tell us a little about yourself.',
        blank=True,
        null=True,
    )
    url = models.URLField(
        _('Home Page'),
        help_text='The main website for your Organization',
        max_length=255,
        blank=True,
        null=True,
    )
    disabled = models.BooleanField(
        _('Disabled'),
        help_text='Docs and builds are disabled for this organization',
        default=False,
    )
    artifacts_cleaned = models.BooleanField(
        _('Artifacts Cleaned'),
        help_text='Artifacts are cleaned out from storage',
        default=False,
    )
    max_concurrent_builds = models.IntegerField(
        _('Maximum concurrent builds allowed for this organization'),
        null=True,
        blank=True,
    )

    stripe_id = models.CharField(
        _('Stripe customer ID'),
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

    # Managers
    objects = OrganizationQuerySet.as_manager()
    history = ExtraHistoricalRecords()

    class Meta:
        base_manager_name = 'objects'
        verbose_name = _("organization")
        ordering = ['name']
        get_latest_by = ['-pub_date']

    def __str__(self):
        return self.name

    def get_or_create_stripe_subscription(self):
        # TODO: remove this once we don't depend on our Subscription models.
        from readthedocs.subscriptions.models import Subscription

        subscription = Subscription.objects.get_or_create_default_subscription(self)
        if not subscription:
            # This only happens during development.
            log.warning("No default subscription created.")
            return None

        # Active subscriptions take precedence over non-active subscriptions,
        # otherwise we return the must recently created subscription.
        active_subscription = self.stripe_customer.subscriptions.filter(
            status=SubscriptionStatus.active
        ).first()
        if active_subscription:
            return active_subscription
        return self.stripe_customer.subscriptions.latest()

    def get_absolute_url(self):
        return reverse('organization_detail', args=(self.slug,))

    @property
    def users(self):
        return AdminPermission.members(self)

    @property
    def members(self):
        return AdminPermission.members(self)

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
        if not self.slug:
            self.slug = slugify(self.name)

        if self.stripe_customer:
            self.stripe_id = self.stripe_customer.id

        super().save(*args, **kwargs)

    def get_stripe_metadata(self):
        """Get metadata for the stripe account."""
        return {
            "org:id": self.id,
            "org:slug": self.slug,
        }

    # pylint: disable=no-self-use
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

    def __str__(self):
        return _('{org} owner {owner}').format(
            org=self.organization.name,
            owner=self.owner.username,
        )


class Team(models.Model):

    """Team model."""

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # Foreign
    organization = models.ForeignKey(
        Organization,
        related_name='teams',
        on_delete=models.CASCADE,
    )
    projects = models.ManyToManyField(
        'projects.Project',
        verbose_name=_('Projects'),
        related_name='teams',
        blank=True,
    )
    members = models.ManyToManyField(
        User,
        verbose_name=_('Users'),
        related_name='teams',
        blank=True,
        through='TeamMember',
    )

    # Local
    name = models.CharField(_('Name'), max_length=100)
    slug = AutoSlugField(
        populate_from='name',
        always_update=True,
        unique_with=['organization'],
    )
    access = models.CharField(
        _('Access'),
        max_length=100,
        choices=constants.ACCESS_LEVELS,
        default='readonly',
    )

    auto_join_email_users = models.BooleanField(
        default=False,
        help_text="Auto join users with an organization's email address to this team.",
    )

    # Managers
    objects = TeamManager()
    history = ExtraHistoricalRecords()

    class Meta:
        base_manager_name = 'objects'
        verbose_name = _("team")
        unique_together = (
            ('slug', 'organization'),
            ('name', 'organization'),
        )

    def get_absolute_url(self):
        return reverse(
            'organization_team_detail',
            args=(self.organization.slug, self.slug),
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TeamInvite(models.Model):

    """Model to keep track of invitations to an organization."""

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # Foreign
    organization = models.ForeignKey(
        Organization,
        related_name='invites',
        on_delete=models.CASCADE,
    )
    team = models.ForeignKey(
        Team,
        verbose_name=_('Team'),
        related_name='invites',
        on_delete=models.CASCADE,
    )

    email = models.EmailField(_('E-mail'))
    hash = models.CharField(_('Hash'), max_length=250)
    count = models.IntegerField(_('Count'), default=0)
    total = models.IntegerField(_('Total'), default=10)

    class Meta:
        unique_together = ('team', 'email')

    def __str__(self):
        return '{email} to {team}'.format(
            email=self.email,
            team=self.team,
        )

    def save(self, *args, **kwargs):  # pylint: disable=signature-differs
        hash_ = salted_hmac(
            # HMAC key per applications
            '.'.join([self.__module__, self.__class__.__name__]),
            # HMAC message
            ''.join([str(self.team), str(self.email)]),
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
            defaults=dict(
                from_user=owner,
                to_email=self.email,
                content_type=content_type,
                object_id=self.team.pk,
            ),
        )
        self.teammember_set.all().delete()
        return invitation, created


class TeamMember(models.Model):

    """Intermediate table for Team <-> Member/Invite relationships."""

    class Meta:
        unique_together = (
            ('team', 'member', 'invite'),
            ('team', 'member'),
            ('team', 'invite'),
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

    def __str__(self):
        state = ''
        if self.is_invite:
            state = ' (pending)'
        return '{username} to {team}{state}'.format(
            username=self.username,
            team=self.team,
            state=state,
        )

    @property
    def username(self):
        """Return member username or invite email as username."""
        if self.is_member:
            return self.member.username

        if self.invite is not None:
            return self.invite.email

        return 'Unknown'

    @property
    def full_name(self):
        """Return member or invite full name."""
        if self.is_member:
            return self.member.get_full_name()
        return ''

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
