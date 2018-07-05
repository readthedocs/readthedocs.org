# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import base64
import hashlib
import json

from builtins import zip
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from readthedocs.projects.models import Project

from .mixins import SSHKeyGenMixin
from .querysets import SSHKeyQuerySet


@python_2_unicode_compatible
class SSHKey(SSHKeyGenMixin, models.Model):

    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)

    public_key = models.TextField(
        _('Public SSH Key'),
        help_text='Add this to your version control to give us access.',
    )
    private_key = models.TextField(_('Private SSH Key'))
    project = models.ForeignKey(Project, related_name='sshkeys')
    json = models.TextField(_('Serialized API response'), blank=True, null=True)

    objects = SSHKeyQuerySet.as_manager()

    def __str__(self):
        return 'SSH Key for {}'.format(self.project)

    @property
    def service_id(self):
        if not self.json:
            return None

        data = json.loads(self.json)
        service_id = (
            data.get('id') or  # github / gitlab
            data.get('pk')  # bitbucket
        )
        return service_id

    def save(self, *args, **kwargs):  # pylitn: disable=arguments-differ
        if self.pk is None and not self.private_key:
            self.generate_keys(commit=kwargs.get('commit', False))
        super(SSHKey, self).save(*args, **kwargs)

    @property
    def fingerprint(self):
        """SSH fingerprint for public key"""
        key = self.public_key.strip().split()[1].encode('ascii')
        fingerprint = hashlib.md5(base64.b64decode(key)).hexdigest()
        return ':'.join(a + b for (a, b) in zip(fingerprint[::2],
                                                fingerprint[1::2]))
