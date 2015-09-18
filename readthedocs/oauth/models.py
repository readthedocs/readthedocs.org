"""OAuth service models"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator

from readthedocs.projects.constants import REPO_CHOICES

from .constants import OAUTH_SOURCE
from .managers import BitbucketTeamManager
from .managers import BitbucketProjectManager
from .managers import GithubOrganizationManager
from .managers import GithubProjectManager
from .managers import OAuthRepositoryManager, OAuthOrganizationManager


class OAuthOrganization(models.Model):

    """Organization from OAuth service

    This encapsulates both Github and Bitbucket
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='oauth_organizations')
    active = models.BooleanField(_('Active'), default=False)

    slug = models.CharField(_('Slug'), max_length=255, unique=True)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)
    avatar_url = models.URLField(_('Avatar image URL'), null=True, blank=True)
    url = models.URLField(_('URL to organization page'), max_length=200,
                          null=True, blank=True)

    source = models.CharField(_('Repository source'), max_length=16,
                              choices=OAUTH_SOURCE)
    json = models.TextField(_('Serialized API response'))

    objects = OAuthOrganizationManager()

    def __unicode__(self):
        return "OAuth Organization: %s" % (self.url)

    def get_serialized(self, key=None, default=None):
        try:
            data = json.loads(self.json)
            if key is not None:
                return data.get(key, default)
            return data
        except ValueError:
            pass


class OAuthRepository(models.Model):

    """OAuth importable repositories

    This models Github and Bitbucket importable repositories
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # This should now be a OneToOne
    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='oauth_repositories')
    organization = models.ForeignKey(
        OAuthOrganization, verbose_name=_('Organization'),
        related_name='repositories', null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)

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

    source = models.CharField(_('Repository source'), max_length=16,
                              choices=OAUTH_SOURCE)
    json = models.TextField(_('Serialized API response'))

    objects = OAuthRepositoryManager()

    class Meta:
        ordering = ['organization__name', 'name']

    def __unicode__(self):
        return "OAuth importable repository: %s" % (self.html_url)

    def get_serialized(self, key=None, default=None):
        try:
            data = json.loads(self.json)
            if key is not None:
                return data.get(key, default)
            return data
        except ValueError:
            pass


class GithubOrganization(models.Model):
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='github_organizations')

    login = models.CharField(_('Login'), max_length=255, unique=True)

    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)

    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    html_url = models.URLField(_('HTML URL'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)
    json = models.TextField('JSON')

    objects = GithubOrganizationManager()

    def __unicode__(self):
        return "GitHub Organization: %s" % (self.html_url)

    def serialized_field(self, key=None, default=None):
        # TODO don't do this with eval!
        data = eval(self.json)
        if key is not None:
            return data.get(key, default)
        return data

    def avatar_url(self):
        return self.serialized_field('avatar_url')


class GithubProject(models.Model):
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # This should now be a OneToOne
    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='github_projects')
    organization = models.ForeignKey(GithubOrganization, verbose_name=_('Organization'),
                                     related_name='projects', null=True, blank=True)
    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True,
                                   help_text=_('The reStructuredText description of the project'))
    git_url = models.CharField(_('Git URL'), max_length=200, blank=True)
    ssh_url = models.CharField(_('SSH URL'), max_length=200, blank=True)
    html_url = models.URLField(_('HTML URL'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)
    json = models.TextField('JSON')

    objects = GithubProjectManager()

    class Meta:
        ordering = ['organization__name', 'name']

    def __unicode__(self):
        return "GitHub Project: %s" % (self.html_url)

    def serialized_field(self, key=None, default=None):
        # TODO don't do this with eval!
        data = eval(self.json)
        if key is not None:
            return data.get(key, default)
        return data

    def is_admin(self):
        permissions = self.serialized_field('permissions', {})
        return permissions.get('admin', False)

    def is_private(self):
        return self.serialized_field('private')

    def owner(self):
        owner = self.serialized_field('owner', {})
        return dict((key, val) for (key, val) in owner.items()
                    if key in ['avatar_url', 'login', 'name'])


class BitbucketTeam(models.Model):
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='bitbucket_organizations')

    login = models.CharField(_('Login'), max_length=255, unique=True)

    email = models.EmailField(_('Email'), max_length=255, null=True, blank=True)

    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    html_url = models.URLField(_('HTML URL'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)
    json = models.TextField('JSON')

    objects = BitbucketTeamManager()

    def __unicode__(self):
        return "Bitbucket Team: %s" % (self.html_url)


class BitbucketProject(models.Model):
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='bitbucket_projects')
    organization = models.ForeignKey(BitbucketTeam, verbose_name=_('Organization'),
                                     related_name='projects', null=True, blank=True)
    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True,
                                   help_text=_('The reStructuredText description of the project'))
    vcs = models.CharField(_('vcs'), max_length=200, blank=True)
    git_url = models.CharField(_('Git URL'), max_length=200, blank=True)
    ssh_url = models.CharField(_('SSH URL'), max_length=200, blank=True)
    html_url = models.URLField(_('HTML URL'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)
    json = models.TextField('JSON')

    objects = BitbucketProjectManager()

    def __unicode__(self):
        return "Bitbucket Project: %s" % (self.html_url)

    def is_private(self):
        full_json = eval(self.json)
        return full_json['is_private']
