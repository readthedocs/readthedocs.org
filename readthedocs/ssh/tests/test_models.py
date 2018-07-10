# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.test import TestCase
import django_dynamic_fixture as fixture

from readthedocs.projects.models import Project

from .utils import PRIVATE_KEY_STRING

from ..models import SSHKey


class SSHKeyModelTests(TestCase):

    def test_fingerprint(self):
        public_key = (
            'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBFPEZe1XSoPsV9LOqzoPRe4pAWL'
            'W6+sPO3EWv+NFGSFEZh7BYA9T8B05boRkLhFqkmMMcDM1GOTqZ5cEB1rmJHWc7yYlZ'
            'MQbd4CwNSxD14HRoL5QSmM07QpwjhzpSHlKsb2HZCxpbmuXOcft940PrVZVP7rc+MI'
            'i6uBEF5HwalxazujW4eBHU8HRgACemjhaYScOeYJDfkjES4FyhW+En4w6ApO4RbRbP'
            'vnsoVDpf8I1oHHKx2INnixi4HsmGC4iTvemA4lZhthqHkbVAURx9qXnAqlfFSz2OHH'
            'GM/mxUeoUSEtUgq2B/2DXriFnwj/463gELCToPObNV0zi+ZozP '
            'support@readthedocs.org'
        )
        profile = fixture.get(SSHKey, public_key=public_key)
        self.assertEqual(
            profile.fingerprint,
            'e6:98:8f:4a:8e:a1:df:0f:f9:bb:c4:53:93:b5:78:34',
        )

    def test_create_from_string(self):
        project = fixture.get(Project)
        self.assertEqual(project.sshkeys.count(), 0)
        key = SSHKey.objects.create_from_string(PRIVATE_KEY_STRING, project)
        self.assertEqual(key.project.slug, project.slug)
        self.assertEqual(key.private_key, PRIVATE_KEY_STRING)
        self.assertIsNotNone(key.public_key)
        self.assertEqual(project.sshkeys.count(), 1)
