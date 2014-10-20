from django.db import models
from django.utils.translation import ugettext_lazy as _

from projects.models import Project

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
    ('sphinx_html', _('Sphinx HTMLDir -> HTML')),
    ('sphinx_htmldir', _('Sphinx HTML -> HTMLDir')),
    # ('advanced', _('Advanced')),
)

from_url_helptext = _('Absolute path, excluding the domain. '
                      'Example: <b>/docs/</b>  or <b>/install.html</br>'
                      )
to_url_helptext = _('Absolute or relative url. Examples: '
                    '<b>/tutorial/install.html</br>'
                    )
redirect_type_helptext = _('The type of redirect you wish to use.')


class Redirect(models.Model):
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

    class Meta:
        verbose_name = _('redirect')
        verbose_name_plural = _('redirects')
        ordering = ('-update_dt',)

    def __unicode__(self):
        if self.redirect_type == 'prefix':
            return _('Redirect: %s ->' % self.from_url)
        elif self.redirect_type == 'page':
            return _('Redirect: %s -> %s' % (self.from_url, self.to_url))
        else:
            return _('Redirect: %s' % self.get_redirect_type_display())
