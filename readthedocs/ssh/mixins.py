# -*- coding: utf-8 -*-
"""Helper mixin to manipulate SSH keys."""
from __future__ import division, print_function, unicode_literals

from .keys import generate_ssh_pair_keys


class SSHKeyGenMixin(object):

    """Mixin for models with SSH fields."""

    def generate_keys(self, commit=True):
        """
        Generate random SSH pair keys.

        The generated keys are assigned to ``self.private_key`` and
        ``self.public_key``.

        :param commit: whether or not call the ``self.save`` method after the
            keys are generated
        """
        self.private_key, self.public_key = generate_ssh_pair_keys()
        if commit:
            self.save()
