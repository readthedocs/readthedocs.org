from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext

from guardian.shortcuts import assign, get_objects_for_user

from projects.models import Project
from projects import constants
from .constants import BUILD_STATE, BUILD_TYPES


class VersionManager(models.Manager):
    def _filter_queryset(self, user, project, privacy_level, only_active):
        if isinstance(privacy_level, basestring):
            privacy_level = (privacy_level,)
        queryset = Version.objects.filter(privacy_level__in=privacy_level)
        if not user and not project:
            return queryset
        if user and user.is_authenticated():
            # Add in possible user-specific views
            user_queryset = get_objects_for_user(user, 'builds.view_version')
            queryset = user_queryset | queryset
        else:
            # Hack around get_objects_for_user not supporting global perms
            global_access = user.has_perm('builds.view_version')
            if global_access:
                queryset = Version.objects.all()
        if project:
            # Filter by project if requested
            queryset =  queryset.filter(project=project)
        if only_active:
            queryset = queryset.filter(active=True)
        return queryset

    def public(self, user=None, project=None, only_active=True, *args, **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PUBLIC),
            only_active=only_active
        )
        return queryset.filter(*args, **kwargs)

    def protected(self, user=None, project=None, only_active=True, *args, **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PUBLIC, constants.PROTECTED),
            only_active=only_active
        )
        return queryset.filter(*args, **kwargs)

    def private(self, user=None, project=None, only_active=True, *args, **kwargs):
        queryset = self._filter_queryset(
            user,
            project,
            privacy_level=(constants.PRIVATE),
            only_active=only_active
        )
        return queryset.filter(*args, **kwargs)

class Version(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='versions')
    identifier = models.CharField(_('Identifier'), max_length=255) # used by the vcs backend
    verbose_name = models.CharField(_('Verbose Name'), max_length=255)
    slug = models.CharField(_('Slug'), max_length=255)
    active = models.BooleanField(_('Active'), default=False)
    built = models.BooleanField(_('Built'), default=False)
    uploaded = models.BooleanField(_('Uploaded'), default=False)
    privacy_level = models.CharField(_('Privacy Level'), max_length=20,
        choices=constants.PRIVACY_CHOICES, default='public',
        help_text=_("Level of privacy for this Version."))

    objects = VersionManager()

    class Meta:
        unique_together = [('project', 'slug')]
        ordering = ['-verbose_name']
        permissions = (
            # Translators: Permission around whether a user can view the version
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
        return obj



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
    version = models.ForeignKey(Version, verbose_name=_('Version'), null=True, related_name='builds')
    type = models.CharField(_('Type'), max_length=55, choices=BUILD_TYPES, default='html')
    state = models.CharField(_('State'), max_length=55, choices=BUILD_STATE, default='finished')
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    success = models.BooleanField(_('Success'))
    setup = models.TextField(_('Setup'), null=True, blank=True)
    setup_error = models.TextField(_('Setup error'), null=True, blank=True)
    output = models.TextField(_('Output'), default='', blank=True)
    error = models.TextField(_('Error'), default='', blank=True)

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
