"""OAuth service models."""

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from readthedocs.projects.constants import REPO_CHOICES
from readthedocs.projects.models import Project

from .constants import VCS_PROVIDER_CHOICES
from .querysets import RemoteOrganizationQuerySet, RemoteRepositoryQuerySet


class RemoteOrganization(TimeStampedModel):

    """
    Organization from remote service.

    This encapsulates both Github and Bitbucket
    """

    users = models.ManyToManyField(
        User,
        verbose_name=_('Users'),
        related_name='oauth_organizations',
        through='RemoteOrganizationRelation'
    )
    slug = models.CharField(_('Slug'), max_length=255)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)
    avatar_url = models.URLField(
        _('Avatar image URL'),
        null=True,
        blank=True,
        max_length=255,
    )
    url = models.URLField(
        _('URL to organization page'),
        max_length=200,
        null=True,
        blank=True,
    )
    # VCS provider organization id
    remote_id = models.CharField(
        db_index=True,
        max_length=128
    )
    vcs_provider = models.CharField(
        _('VCS provider'),
        choices=VCS_PROVIDER_CHOICES,
        max_length=32
    )

    objects = RemoteOrganizationQuerySet.as_manager()

    class Meta:
        ordering = ['name']
        unique_together = ('remote_id', 'vcs_provider',)
        db_table = 'oauth_remoteorganization_2020'

    def __str__(self):
        return 'Remote organization: {name}'.format(name=self.slug)

    def get_remote_organization_relation(self, user, social_account):
        """Return RemoteOrganizationRelation object for the remote organization."""
        remote_organization_relation, _ = (
            RemoteOrganizationRelation.objects.get_or_create(
                remote_organization=self,
                user=user,
                account=social_account
            )
        )
        return remote_organization_relation


class RemoteOrganizationRelation(TimeStampedModel):
    remote_organization = models.ForeignKey(
        RemoteOrganization,
        related_name='remote_organization_relations',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='remote_organization_relations',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        SocialAccount,
        verbose_name=_('Connected account'),
        related_name='remote_organization_relations',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('remote_organization', 'account',)

    def __str__(self):
        return f'{self.user.username} <-> {self.remote_organization.name}'


class RemoteRepository(TimeStampedModel):

    """
    Remote importable repositories.

    This models Github and Bitbucket importable repositories
    """

    # This should now be a OneToOne
    users = models.ManyToManyField(
        User,
        verbose_name=_('Users'),
        related_name='oauth_repositories',
        through='RemoteRepositoryRelation'
    )
    organization = models.ForeignKey(
        RemoteOrganization,
        verbose_name=_('Organization'),
        related_name='repositories',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(
        _('Full Name'),
        max_length=255,
        db_index=True,
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        null=True,
        help_text=_('Description of the project'),
    )
    avatar_url = models.URLField(
        _('Owner avatar image URL'),
        null=True,
        blank=True,
        max_length=255,
    )

    ssh_url = models.URLField(
        _('SSH URL'),
        max_length=512,
        blank=True,
        validators=[URLValidator(schemes=['ssh'])],
    )
    clone_url = models.URLField(
        _('Repository clone URL'),
        max_length=512,
        blank=True,
        validators=[
            URLValidator(schemes=['http', 'https', 'ssh', 'git', 'svn']),
        ],
    )
    html_url = models.URLField(_('HTML URL'), null=True, blank=True)

    private = models.BooleanField(_('Private repository'), default=False)
    vcs = models.CharField(
        _('vcs'),
        max_length=200,
        blank=True,
        choices=REPO_CHOICES,
    )
    default_branch = models.CharField(
        _('Default branch of the repository'),
        max_length=150,
        null=True,
        blank=True,
    )
    # VCS provider repository id
    remote_id = models.CharField(
        db_index=True,
        max_length=128
    )
    vcs_provider = models.CharField(
        _('VCS provider'),
        choices=VCS_PROVIDER_CHOICES,
        max_length=32
    )

    objects = RemoteRepositoryQuerySet.as_manager()

    class Meta:
        ordering = ['full_name']
        verbose_name_plural = 'remote repositories'
        unique_together = ('remote_id', 'vcs_provider',)
        db_table = 'oauth_remoterepository_2020'

    def __str__(self):
        return 'Remote repository: {}'.format(self.html_url)

    def matches(self, user):
        """Existing projects connected to this RemoteRepository."""

        # TODO: remove this method and refactor the API response in ``/api/v2/repos/``
        # (or v3) to just return the linked Project (slug, url) if the ``RemoteRepository``
        # connection exists. Note the frontend needs to be simplified as well in
        # ``import.js`` and ``project_import.html``.

        projects = Project.objects.public(user).filter(
            remote_repository=self,
        ).values('slug')

        return [{
            'id': project['slug'],
            'url': reverse(
                'projects_detail',
                kwargs={
                    'project_slug': project['slug'],
                },
            ),
        } for project in projects]

    def get_remote_repository_relation(self, user, social_account):
        """Return RemoteRepositoryRelation object for the remote repository."""
        remote_repository_relation, _ = (
            RemoteRepositoryRelation.objects.get_or_create(
                remote_repository=self,
                user=user,
                account=social_account
            )
        )
        return remote_repository_relation


class RemoteRepositoryRelation(TimeStampedModel):
    remote_repository = models.ForeignKey(
        RemoteRepository,
        related_name='remote_repository_relations',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='remote_repository_relations',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        SocialAccount,
        verbose_name=_('Connected account'),
        related_name='remote_repository_relations',
        on_delete=models.CASCADE
    )
    admin = models.BooleanField(_('Has admin privilege'), default=False)

    class Meta:
        unique_together = ('remote_repository', 'account',)

    def __str__(self):
        return f'{self.user.username} <-> {self.remote_repository.full_name}'
