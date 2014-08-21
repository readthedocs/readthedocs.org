from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

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

    def __unicode__(self):
        return "GitHub Organization: %s" % (self.html_url)


class GithubProject(models.Model):
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    users = models.ManyToManyField(User, verbose_name=_('Users'),
                                   related_name='github_projects')
    organization = models.ForeignKey(GithubOrganization, verbose_name=_('Organization'),
                                     related_name='projects', null=True, blank=True)
    name = models.CharField(_('Name'), max_length=255)
    full_name = models.CharField(_('Full Name'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True,
                                   help_text=_('The reStructuredText description of the project'))
    git_url = models.CharField(_('Git URL'), max_length=200, blank=True)
    ssh_url = models.CharField(_('SSH URL'), max_length=200, blank=True)
    html_url = models.URLField(_('HTML URL'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('Active'), default=False)
    json = models.TextField('JSON')

    def __unicode__(self):
        return "GitHub Project: %s" % (self.html_url)
