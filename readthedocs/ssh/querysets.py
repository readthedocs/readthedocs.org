# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.db import models

from .keys import generate_public_from_private_key


class SSHKeyQuerySet(models.QuerySet):

    def create_from_string(self, private_key, project):
        """
        Create a SSHKey instance from a private key.

        :param private_key: private key string
        :param project: project to attach the SSH key
        """
        key = self.create(
            private_key=private_key,
            public_key=generate_public_from_private_key(
                private_key,
                text_format=True,
            ),
            project=project,
        )
        return key
