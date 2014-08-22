import logging
import datetime
from random import getrandbits

from django.db import models
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _

from acl import constants

log = logging.getLogger(__name__)


class ProjectAccessToken(models.Model):
    '''Access token for giving anonymous access to a project'''

    project = models.ForeignKey('projects.Project', verbose_name=_('Project'),
                                related_name='access_tokens')
    token = models.CharField(_('Token'), max_length=64)
    description = models.CharField(_('Description'), max_length=100)
    access_level = models.CharField(_('Access level'), max_length=10,
                                    choices=constants.ACCESS_LEVELS,
                                    default='readonly')
    expires = models.DateTimeField(_('Expires date'))

    def save(self, *args, **kwargs):
        if not self.expires:
            self.expires = self.generate_expiration()
        if not self.token:
            self.token = self.generate_token()
        super(ProjectAccessToken, self).save(*args, **kwargs)

    def is_valid(self):
        return datetime.datetime.now() < self.expires

    def generate_expiration(self):
        return datetime.datetime.now() + datetime.timedelta(days=365)

    def generate_token(self):
        # TODO copy django.contrib.auth.token hash
        return int_to_base36(getrandbits(63))

    @classmethod
    def get_validated_token(cls, token_id):
        try:
            token = cls.objects.get(token=token_id)
            if token and token.is_valid():
                return token
        except cls.DoesNotExist:
            pass
        return None

    def __unicode__(self):
        return self.token
