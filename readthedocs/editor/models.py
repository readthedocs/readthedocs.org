from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext


class BranchManager(models.Manager):
    def get_branch(self, user, project):
        try:
            return self.get(user=user, project=project, active=True)
        except:
            return self.create(user=user, project=project, active=True)


class Branch(models.Model):
    user = models.ForeignKey('auth.User', verbose_name=_('User'))
    project = models.ForeignKey('projects.Project', verbose_name=_('Project'))
    active = models.BooleanField(_('Active'), default=True)
    pushed = models.BooleanField(_('Pushed'), default=False)
    title = models.TextField(_('Title'), default='')
    comment = models.TextField(_('Comment'), default='')
    
    objects = BranchManager()
    
    def __unicode__(self):
        return ugettext("Branch of %(project)s by %(username)s (%(pk)s)") % {
            'project': self.project,
            'user': self.user,
            'pk': self.pk,
        }
