from django.db import models
from django.utils.translation import ugettext_lazy as _


class BranchManager(models.Manager):
    def get_branch(self, user, project):
        try:
            return self.get(user=user, project=project, active=True)
        except:
            return self.create(user=user, project=project, active=True)


class Branch(models.Model):
    user = models.ForeignKey('auth.User')
    project = models.ForeignKey('projects.Project')
    active = models.BooleanField(default=True)
    pushed = models.BooleanField(default=False)
    title = models.TextField(default='')
    comment = models.TextField(default='')
    
    objects = BranchManager()
    
    def __unicode__(self):
        return _("Branch of") %s " + "_("by")" %s (%s)") % (self.project, self.user, self.pk)
