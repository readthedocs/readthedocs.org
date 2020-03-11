import logging
from datetime import timedelta

from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy as _

from readthedocs.core.utils import slugify

from . import constants
from .managers import TeamManager, TeamMemberManager
from .querysets import OrganizationQuerySet
from .utils import send_team_add_email, send_team_invite_email

log = logging.getLogger(__name__)


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
    slug = models.SlugField(_('Slug'), max_length=255, unique=True)
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

    stripe_id = models.CharField(
        _('Stripe customer ID'),
        max_length=100,
        blank=True,
        null=True,
    )

    # Manager
    objects = OrganizationQuerySet.as_manager()

    class Meta:
        base_manager_name = 'objects'
        ordering = ['name']
        get_latest_by = ['-pub_date']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization_detail', args=(self.slug,))

    @property
    def users(self):
        return self.members.all() | self.owners.all()

    @property
    def members(self):
        """Return members as an aggregate over all organization teams."""
        return User.objects.filter(
            Q(teams__organization=self) | Q(owner_organizations=self),
        ).distinct()

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def add_member(self, user, team):
        """
        Add member to organization team.

        user
            User to add to organization team

        team
            Team instance to add user to
        """
        if not team.members.filter(pk=user.pk).exists():
            TeamMember.objects.create(team=team, member=user)


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

    # Manager
    objects = TeamManager()

    class Meta:
        base_manager_name = 'objects'
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
        return '{organization}/{team}'.format(
            organization=self.organization.name,
            team=self.name,
        )

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TeamInvite(models.Model):
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

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        hash_ = salted_hmac(
            # HMAC key per applications
            '.'.join([self.__module__, self.__class__.__name__]),
            # HMAC message
            ''.join([str(self.team), str(self.email)]),
        )
        self.hash = hash_.hexdigest()[::2]
        super().save(*args, **kwargs)


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
        """Notify member or invite of being added to a team."""
        if self.invite is None and self.member is not None:
            send_team_add_email(team_member=self, request=request)
        elif self.member is None and self.invite is not None:
            send_team_invite_email(invite=self.invite, request=request)
