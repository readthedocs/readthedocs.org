# -*- coding: utf-8 -*-

"""OAuth service models."""

import json

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel
from jsonfield import JSONField

from readthedocs.projects.constants import REPO_CHOICES
from readthedocs.projects.models import Project

from .querysets import RemoteOrganizationQuerySet, RemoteRepositoryQuerySet


class RemoteOrganizationRelationship(TimeStampedModel):
    user = models.ForeignKey(
        User,
        verbose_name=_('OAuth repositories'),
        related_name='oauth_organizations',
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        RemoteOrganization,
        verbose_name=_('OAuth relationships'),
        related_name='oauth_relationship',
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey(
        SocialAccount,
        verbose_name=_('Connected account'),
        related_name='remote_organizations',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    json = JSONField(_('Serialized API response'))


class RemoteOrganization(TimeStampedModel):

    """
    Organization from remote service.

    This encapsulates Github, GitLab and Bitbucket
    """

    users = models.ManyToManyField(
        User,
        verbose_name=_('Users'),
        related_name='oauth_organizations',
        through=RemoteOrganizationRelationship,
    )

    slug = models.CharField(_('Slug'), max_length=255)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    remote_id = models.IntegerField(
        _('Remote ID'),
        db_index=True,
    )
    provider = models.CharField(
        _('VCS provider'),
        max_length=32,
        choices=PROVIDER_CHOICES,
    )
    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)
    avatar_url = models.URLField(_('Avatar image URL'), null=True, blank=True)
    url = models.URLField(
        _('URL to organization page'),
        max_length=200,
        null=True,
        blank=True,
    )

    objects = RemoteOrganizationQuerySet.as_manager()

    class Meta:
        unique_together = ['remote_id', 'provider']

    def __str__(self):
        return 'Remote organization: {name}'.format(name=self.slug)

    def get_serialized(self, key=None, default=None):
        try:
            data = json.loads(self.json)
            if key is not None:
                return data.get(key, default)
            return data
        except ValueError:
            pass


class RemoteRepositoryRelationship(TimeStampedModel):

    """
    User-specific data for related RemoteRepository.

    This model contains user-specific data like if this user has admin
    permission over the related ``RemoteRepository`` and the full response from
    the API.
    """

    user = models.ForeignKey(
        User,
        verbose_name=_('OAuth repositories'),
        related_name='oauth_repositories',
        on_delete=models.CASCADE,
    )
    repository = models.ForeignKey(
        RemoteRepository,
        verbose_name=_('OAuth relationships'),
        related_name='oauth_relationship',
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey(
        SocialAccount,
        verbose_name=_('Connected account'),
        related_name='remote_repositories',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    admin = models.BooleanField(default=False)
    json = JSONField(_('Serialized API response'))


class RemoteRepository(TimeStampedModel):

    """
    Remote importable repositories.

    This models GitHub, GitLab and Bitbucket importable repositories
    """

    users = models.ManyToManyField(
        User,
        verbose_name=_('Users'),
        through=RemoteRepositoryRelationship,
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        RemoteOrganization,
        verbose_name=_('Organization'),
        related_name='repositories',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    # TODO: think more about the case for translations. Using a OneToOneField
    # here, will avoid to import the same repository multiple times and setup
    # it for different languages. I think we don't allow this already, but
    # worth considering it, though
    project = models.OneToOneField(
        Project,
        on_delete=models.SET_NULL,
        related_name='remote_repository',
        null=True,
        blank=True,
    )

    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(
        _('Full Name'),
        max_length=255,
        db_index=True,
    )
    remote_id = models.CharField(
        _('Remote ID'),
        max_length=64,
        db_index=True,
    )
    provider = models.CharField(
        _('VCS provider'),
        max_length=32,
        choices=PROVIDER_CHOICES,
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

    objects = RemoteRepositoryQuerySet.as_manager()

    class Meta:
        unique_together = ['remote_id', 'provider']
        ordering = ['organization__name', 'name']
        verbose_name_plural = 'remote repositories'

    def __str__(self):
        return 'Remote repository: {}'.format(self.html_url)

    def matches(self, user):
        """Projects that exist with repository URL already."""
        # Support Git scheme GitHub url format that may exist in database
        truncated_url = self.clone_url.replace('.git', '')
        http_url = self.clone_url.replace('git://', 'https://').replace('.git', '')

        projects = Project.objects.public(user).filter(
            Q(repo=self.clone_url) |
            Q(repo=truncated_url) |
            Q(repo=truncated_url + '.git') |
            Q(repo=http_url) |
            Q(repo=http_url + '.git')
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
