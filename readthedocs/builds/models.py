from django.db import models
from projects.models import Project
from django.utils.translation import ugettext_lazy as _, ugettext

from .constants import BUILD_STATE, BUILD_TYPES


class Version(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='versions')
    identifier = models.CharField(_('Identifier'), max_length=255) # used by the vcs backend
    verbose_name = models.CharField(_('Verbose Name'), max_length=255)
    slug = models.CharField(_('Slug'), max_length=255)
    active = models.BooleanField(_('Active'), default=False)
    built = models.BooleanField(_('Built'), default=False)
    uploaded = models.BooleanField(_('Uploaded'), default=False)

    class Meta:
        unique_together = [('project', 'slug')]
        ordering = ['-verbose_name']

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


class VersionAlias(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='aliases')
    from_slug = models.CharField(_('From slug'), max_length=255, default='')
    to_slug = models.CharField(_('To slug'), max_length=255, default='', blank=True)
    largest = models.BooleanField(_('Largest'), default=False)

    def __unicode__(self):
        return ugettext(u"Alias for %(project)s: %(from)s -> %(to)s" % {
            'project': self.project,
            'form': self.from_slug,
            'to': self.to_slug,
        })


class Build(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='builds')
    type = models.CharField(_('Type'), max_length=55, choices=BUILD_TYPES, default='html')
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    success = models.BooleanField(_('Success'))
    setup = models.TextField(_('Setup'), null=True, blank=True)
    setup_error = models.TextField(_('Setup error'), null=True, blank=True)
    output = models.TextField(_('Output'))
    error = models.TextField(_('Error'))
    version = models.ForeignKey(Version, verbose_name=_('Version'), null=True, related_name='builds')
    state = models.CharField(_('State'), max_length=55, choices=BUILD_STATE, default='finished')

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return ugettext(u"Build %(project)s for %(usernames)s (%(pk)s)" % {
            'project': self.project,
            'usernames': ' '.join(self.project.users.all().values_list('username', flat=True)),
            'pk': self.pk,
        })

    @models.permalink
    def get_absolute_url(self):
        return ('builds_detail', [self.project.slug, self.pk])
