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

from_url_helptext = _('Absolute path, excluding the domain. Example: < i > /docs /$path < /i > .'
                      'Use <b>$path</b> to specify the remainder of the previous path')

to_url_helptext = _('Absolute or relative url. Examples: '
                    '\'http://www.example.com/$path\', \'/en/latest/$path\'. '
                    'Use <b>$path</b> to specify the previous URL'
                    )


class Redirect(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='redirects')
    from_url = models.CharField(_('From URL'), max_length=255,
                                db_index=True, help_text=from_url_helptext)

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
        return _("Redirect: %(from)s --> %(to)s") % {'from': self.from_url, 'to': self.to_url}
