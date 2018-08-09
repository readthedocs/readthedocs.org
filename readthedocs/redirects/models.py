"""Django models for the redirects app."""

from __future__ import absolute_import
from builtins import object
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
import logging
import re

from readthedocs.core.resolver import resolve_path
from readthedocs.projects.models import Project
from .managers import RedirectManager


log = logging.getLogger(__name__)


HTTP_STATUS_CHOICES = (
    (301, _('301 - Permanent Redirect')),
    (302, _('302 - Temporary Redirect')),
)

STATUS_CHOICES = (
    (True, _('Active')),
    (False, _('Inactive')),
)

TYPE_CHOICES = (
    ('prefix', _('Prefix Redirect')),
    ('page', _('Page Redirect')),
    ('exact', _('Exact Redirect')),
    ('sphinx_html', _('Sphinx HTMLDir -> HTML')),
    ('sphinx_htmldir', _('Sphinx HTML -> HTMLDir')),
    # ('advanced', _('Advanced')),
)

# FIXME: this help_text message should be dynamic since "Absolute path" doesn't
# make sense for "Prefix Redirects" since the from URL is considered after the
# ``/$lang/$version/`` part. Also, there is a feature for the "Exact
# Redirects" that should be mentioned here: the usage of ``$rest``
from_url_helptext = _('Absolute path, excluding the domain. '
                      'Example: <b>/docs/</b>  or <b>/install.html</b>'
                      )
to_url_helptext = _('Absolute or relative URL. Example: '
                    '<b>/tutorial/install.html</b>'
                    )
redirect_type_helptext = _('The type of redirect you wish to use.')


@python_2_unicode_compatible
class Redirect(models.Model):

    """A HTTP redirect associated with a Project."""

    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='redirects')

    redirect_type = models.CharField(_('Redirect Type'), max_length=255, choices=TYPE_CHOICES,
                                     help_text=redirect_type_helptext)

    from_url = models.CharField(_('From URL'), max_length=255,
                                db_index=True, help_text=from_url_helptext, blank=True)

    to_url = models.CharField(_('To URL'), max_length=255,
                              db_index=True, help_text=to_url_helptext, blank=True)

    http_status = models.SmallIntegerField(_('HTTP Status'),
                                           choices=HTTP_STATUS_CHOICES,
                                           default=301)
    status = models.BooleanField(choices=STATUS_CHOICES, default=True)

    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    objects = RedirectManager()

    class Meta(object):
        verbose_name = _('redirect')
        verbose_name_plural = _('redirects')
        ordering = ('-update_dt',)

    def __str__(self):
        redirect_text = '{type}: {from_to_url}'
        if self.redirect_type in ['prefix', 'page', 'exact']:
            return redirect_text.format(
                type=self.get_redirect_type_display(),
                from_to_url=self.get_from_to_url_display()
            )
        return ugettext('Redirect: {}'.format(
            self.get_redirect_type_display())
        )

    def get_from_to_url_display(self):
        if self.redirect_type in ['prefix', 'page', 'exact']:
            from_url = self.from_url
            to_url = self.to_url
            if self.redirect_type == 'prefix':
                to_url = '/{lang}/{version}/'.format(
                    lang=self.project.language,
                    version=self.project.default_version
                )
            return '{from_url} -> {to_url}'.format(
                from_url=from_url,
                to_url=to_url
            )
        return ''

    def get_full_path(self, filename, language=None, version_slug=None):
        """
        Return a full path for a given filename.

        This will include version and language information. No protocol/domain
        is returned.
        """
        # Handle explicit http redirects
        if re.match('^https?://', filename):
            return filename

        return resolve_path(
            project=self.project, language=language,
            version_slug=version_slug, filename=filename
        )

    def get_redirect_path(self, path, language=None, version_slug=None):
        method = getattr(self, 'redirect_{type}'.format(
            type=self.redirect_type))
        return method(path, language=language, version_slug=version_slug)

    def redirect_prefix(self, path, language=None, version_slug=None):
        if path.startswith(self.from_url):
            log.debug('Redirecting %s', self)
            cut_path = re.sub('^%s' % self.from_url, '', path)
            to = self.get_full_path(
                filename=cut_path,
                language=language,
                version_slug=version_slug)
            return to

    def redirect_page(self, path, language=None, version_slug=None):
        if path == self.from_url:
            log.debug('Redirecting %s', self)
            to = self.get_full_path(
                filename=self.to_url.lstrip('/'),
                language=language,
                version_slug=version_slug)
            return to

    def redirect_exact(self, path, language=None, version_slug=None):
        full_path = path
        if language and version_slug:
            # reconstruct the full path for an exact redirect
            full_path = self.get_full_path(path, language, version_slug)
        if full_path == self.from_url:
            log.debug('Redirecting %s', self)
            return self.to_url
        # Handle full sub-level redirects
        if '$rest' in self.from_url:
            match = self.from_url.split('$rest')[0]
            if full_path.startswith(match):
                cut_path = re.sub('^%s' % match, self.to_url, full_path)
                return cut_path

    def redirect_sphinx_html(self, path, language=None, version_slug=None):
        for ending in ['/', '/index.html']:
            if path.endswith(ending):
                log.debug('Redirecting %s', self)
                path = path[1:]  # Strip leading slash.
                to = re.sub(ending + '$', '.html', path)
                return self.get_full_path(
                    filename=to,
                    language=language,
                    version_slug=version_slug)

    def redirect_sphinx_htmldir(self, path, language=None, version_slug=None):
        if path.endswith('.html'):
            log.debug('Redirecting %s', self)
            path = path[1:]  # Strip leading slash.
            to = re.sub('.html$', '/', path)
            return self.get_full_path(
                filename=to,
                language=language,
                version_slug=version_slug)
