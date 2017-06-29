"""OAuth service models"""

from __future__ import absolute_import
from builtins import object
import json

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from django.core.urlresolvers import reverse
from allauth.socialaccount.models import SocialAccount

from readthedocs.projects.constants import REPO_CHOICES
from readthedocs.projects.models import Project

from .querysets import RemoteRepositoryQuerySet, RemoteOrganizationQuerySet


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')


@python_2_unicode_compatible
class RemoteOrganization(models.Model):

    """Organization from remote service

    This encapsulates both Github and Bitbucket
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='oauth_organizations')
    account = models.ForeignKey(
        SocialAccount, verbose_name=_('Connected account'),
        related_name='remote_organizations', null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)

    slug = models.CharField(_('Slug'), max_length=255)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)
    avatar_url = models.URLField(_('Avatar image URL'), null=True, blank=True)
    url = models.URLField(_('URL to organization page'), max_length=200,
                          null=True, blank=True)

    json = models.TextField(_('Serialized API response'))

    objects = RemoteOrganizationQuerySet.as_manager()

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


@python_2_unicode_compatible
class RemoteRepository(models.Model):

    """Remote importable repositories

    This models Github and Bitbucket importable repositories
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # This should now be a OneToOne
    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='oauth_repositories')
    account = models.ForeignKey(
        SocialAccount, verbose_name=_('Connected account'),
        related_name='remote_repositories', null=True, blank=True)
    organization = models.ForeignKey(
        RemoteOrganization, verbose_name=_('Organization'),
        related_name='repositories', null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)

    project = models.OneToOneField(Project, on_delete=models.SET_NULL,
                                   related_name='remote_repository', null=True,
                                   blank=True)
    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True,
                                   help_text=_('Description of the project'))
    avatar_url = models.URLField(_('Owner avatar image URL'), null=True,
                                 blank=True)

    ssh_url = models.URLField(_('SSH URL'), max_length=512, blank=True,
                              validators=[URLValidator(schemes=['ssh'])])
    clone_url = models.URLField(
        _('Repository clone URL'),
        max_length=512,
        blank=True,
        validators=[
            URLValidator(schemes=['http', 'https', 'ssh', 'git', 'svn'])])
    html_url = models.URLField(_('HTML URL'), null=True, blank=True)

    private = models.BooleanField(_('Private repository'), default=False)
    admin = models.BooleanField(_('Has admin privilege'), default=False)
    vcs = models.CharField(_('vcs'), max_length=200, blank=True,
                           choices=REPO_CHOICES)

    json = models.TextField(_('Serialized API response'))

    objects = RemoteRepositoryQuerySet.as_manager()

    class Meta(object):
        ordering = ['organization__name', 'name']
        verbose_name_plural = 'remote repositories'

    def __str__(self):
        return "Remote repository: %s" % (self.html_url)

    def get_serialized(self, key=None, default=None):
        try:
            data = json.loads(self.json)
            if key is not None:
                return data.get(key, default)
            return data
        except ValueError:
            pass

    @property
    def clone_fuzzy_url(self):
        """Try to match against several permutations of project URL"""
        pass

    def matches(self, user):
        """Projects that exist with repository URL already"""
        # Support Git scheme GitHub url format that may exist in database
        fuzzy_url = self.clone_url.replace('git://', '').replace('.git', '')
        projects = (Project
                    .objects
                    .public(user)
                    .filter(Q(repo=self.clone_url) |
                            Q(repo__iendswith=fuzzy_url) |
                            Q(repo__iendswith=fuzzy_url + '.git')))
        return [{'id': project.slug,
                 'url': reverse('projects_detail',
                                kwargs={'project_slug': project.slug})}
                for project in projects]
