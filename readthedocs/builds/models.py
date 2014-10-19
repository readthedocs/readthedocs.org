import re
import os.path

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext

from guardian.shortcuts import assign
from taggit.managers import TaggableManager

from privacy.loader import VersionManager
from projects.models import Project
from projects import constants
from .constants import BUILD_STATE, BUILD_TYPES, VERSION_TYPES


DEFAULT_VERSION_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_VERSION_PRIVACY_LEVEL', 'public')


class Version(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='versions')
    type = models.CharField(
        _('Type'), max_length=20,
        choices=VERSION_TYPES, default='unknown',
    )
    # used by the vcs backend
    identifier = models.CharField(_('Identifier'), max_length=255)

    verbose_name = models.CharField(_('Verbose Name'), max_length=255)
    slug = models.CharField(_('Slug'), max_length=255)

    supported = models.BooleanField(_('Supported'), default=True)
    active = models.BooleanField(_('Active'), default=False)
    built = models.BooleanField(_('Built'), default=False)
    uploaded = models.BooleanField(_('Uploaded'), default=False)
    privacy_level = models.CharField(
        _('Privacy Level'), max_length=20, choices=constants.PRIVACY_CHOICES,
        default=DEFAULT_VERSION_PRIVACY_LEVEL, help_text=_("Level of privacy for this Version.")
    )
    tags = TaggableManager(blank=True)
    machine = models.BooleanField(_('Machine Created'), default=False)
    objects = VersionManager()

    class Meta:
        unique_together = [('project', 'slug')]
        ordering = ['-verbose_name']
        permissions = (
            # Translators: Permission around whether a user can view the
            #              version
            ('view_version', _('View Version')),
        )

    def __unicode__(self):
        return ugettext(u"Version %(version)s of %(project)s (%(pk)s)" % {
            'version': self.verbose_name,
            'project': self.project,
            'pk': self.pk
        })

    def get_absolute_url(self):
        if not self.built and not self.uploaded:
            return ''
        return self.project.get_docs_url(version_slug=self.slug)

    def save(self, *args, **kwargs):
        """
        Add permissions to the Version for all owners on save.
        """
        obj = super(Version, self).save(*args, **kwargs)
        for owner in self.project.users.all():
            assign('view_version', owner, self)
        self.project.sync_supported_versions()
        return obj


    @property 
    def remote_slug(self):
        if self.slug == 'latest':
            if self.project.default_branch:
                return self.project.default_branch
            else:
                return self.project.vcs_repo().fallback_branch
        else:
            return self.slug


    def get_subdomain_url(self):
        use_subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
        if use_subdomain:
            return "/%s/%s/" % (
                self.project.language,
                self.slug,
            )
        else:
            return reverse('docs_detail', kwargs={
                'project_slug': self.project.slug,
                'lang_slug': self.project.language,
                'version_slug': self.slug,
                'filename': ''
            })

    def get_subproject_url(self):
        return "/projects/%s/%s/%s/" % (
            self.project.slug,
            self.project.language,
            self.slug,
        )

    def get_downloads(self, pretty=False):
        project = self.project
        data = {}
        if pretty:
            if project.has_pdf(self.slug):
                data['PDF'] = project.get_production_media_url('pdf', self.slug)
            if project.has_htmlzip(self.slug):
                data['HTML'] = project.get_production_media_url('htmlzip', self.slug)
            if project.has_epub(self.slug):
                data['Epub'] = project.get_production_media_url('epub', self.slug)
        else:
            if project.has_pdf(self.slug):
                data['pdf_url'] = project.get_production_media_url('pdf', self.slug)
            if project.has_htmlzip(self.slug):
                data['htmlzip_url'] = project.get_production_media_url('htmlzip', self.slug)
            if project.has_epub(self.slug):
                data['epub_url'] = project.get_production_media_url('epub', self.slug)
        return data

    def get_conf_py_path(self):
        # Hack this for now.
        return "/docs/"
        conf_py_path = self.project.conf_file(self.slug)
        conf_py_path = conf_py_path.replace(
            self.project.checkout_path(self.slug), '')
        return conf_py_path.replace('conf.py', '')

    def get_build_path(self):
        '''Return version build path if path exists, otherwise `None`'''
        path = self.project.checkout_path(version=self.slug)
        if os.path.exists(path):
            return path
        return None

    def get_github_url(self, docroot, filename, source_suffix='.rst', action='view'):
        GITHUB_REGEXS = [
            re.compile('github.com/(.+)/(.+)(?:\.git){1}'),
            re.compile('github.com/(.+)/(.+)'),
            re.compile('github.com:(.+)/(.+).git'),
        ]
        GITHUB_URL = 'https://github.com/{user}/{repo}/{action}/{version}{docroot}{path}{source_suffix}'

        repo_url = self.project.repo
        if 'github' not in repo_url:
            return ''

        if not docroot:
            return ''
        else:
            if docroot[0] != '/':
                docroot = "/%s" % docroot
            if docroot[-1] != '/':
                docroot = "%s/" % docroot

        if action == 'view':
            action_string = 'blob'
        elif action == 'edit':
            action_string = 'edit'

        for regex in GITHUB_REGEXS:
            match = regex.search(repo_url)
            if match:
                user, repo = match.groups()
                break
        else:
            return ''
        repo = repo.rstrip('/')

        return GITHUB_URL.format(
            user=user,
            repo=repo,
            version=self.remote_slug,
            docroot=docroot,
            path=filename,
            source_suffix=source_suffix,
            action=action_string,
            )

    def get_bitbucket_url(self, docroot, filename, source_suffix='.rst'):
        BB_REGEXS = [
            re.compile('bitbucket.org/(.+)/(.+).git'),
            re.compile('bitbucket.org/(.+)/(.+)/'),
            re.compile('bitbucket.org/(.+)/(.+)'),
        ]
        BB_URL = 'https://bitbucket.org/{user}/{repo}/src/{version}{docroot}{path}{source_suffix}'

        repo_url = self.project.repo
        if 'bitbucket' not in repo_url:
            return ''
        if not docroot:
            return ''

        for regex in BB_REGEXS:
            match = regex.search(repo_url)
            if match:
                user, repo = match.groups()
                break
        else:
            return ''
        repo = repo.rstrip('/')

        return BB_URL.format(
            user=user,
            repo=repo,
            version=self.remote_slug,
            docroot=docroot,
            path=filename,
            source_suffix=source_suffix,
            )



class VersionAlias(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='aliases')
    from_slug = models.CharField(_('From slug'), max_length=255, default='')
    to_slug = models.CharField(_('To slug'), max_length=255, default='',
                               blank=True)
    largest = models.BooleanField(_('Largest'), default=False)

    def __unicode__(self):
        return ugettext(u"Alias for %(project)s: %(from)s -> %(to)s" % {
            'project': self.project,
            'from': self.from_slug,
            'to': self.to_slug,
        })


class Build(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='builds')
    version = models.ForeignKey(Version, verbose_name=_('Version'), null=True,
                                related_name='builds')
    type = models.CharField(_('Type'), max_length=55, choices=BUILD_TYPES,
                            default='html')
    state = models.CharField(_('State'), max_length=55, choices=BUILD_STATE,
                             default='finished')
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    success = models.BooleanField(_('Success'), default=True)
    
    setup = models.TextField(_('Setup'), null=True, blank=True)
    setup_error = models.TextField(_('Setup error'), null=True, blank=True)
    output = models.TextField(_('Output'), default='', blank=True)
    error = models.TextField(_('Error'), default='', blank=True)
    exit_code = models.IntegerField(_('Exit code'), max_length=3, null=True,
                                    blank=True)
    commit = models.CharField(_('Commit'), max_length=255, null=True, blank=True) 

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return ugettext(u"Build %(project)s for %(usernames)s (%(pk)s)" % {
            'project': self.project,
            'usernames': ' '.join(self.project.users.all()
                                  .values_list('username', flat=True)),
            'pk': self.pk,
        })

    @models.permalink
    def get_absolute_url(self):
        return ('builds_detail', [self.project.slug, self.pk])
