# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from .keys import generate_ssh_pair_keys


class SSHKeyGenMixin(object):

    def generate_keys(self, commit=True):
        """Generate random SSH pair keys."""
        self.private_key, self.public_key = generate_ssh_pair_keys()
        if commit:
            self.save()
