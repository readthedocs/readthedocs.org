import os
import shutil

from django.test import TestCase
from django.conf import settings

"""
from projects.utils import sanitize_conf

class SanitizeTest(TestCase):

    def setUp(self):
        self.directory = '/'.join(os.path.dirname(__file__).split('/'))
        temp = os.path.join(self.directory, 'data', 'template')
        no_temp = os.path.join(self.directory, 'data', 'no_template')

        #Set up mungable copies of these files
        self.new_temp = os.path.join(self.directory, 'data', 'new_template')
        self.new_no_temp = os.path.join(self.directory, 'data', 'new_no_template')
        shutil.copyfile(temp, self.new_temp)
        shutil.copyfile(no_temp, self.new_no_temp)

    def tearDown(self):
        os.remove(self.new_temp)
        os.remove(self.new_no_temp)

    def _match_file(self, to_match):
        pre_match = file(to_match, 'r').readlines()
        num_matched = sanitize_conf(to_match)
        post_match = file(to_match, 'r').readlines()
        return (pre_match, num_matched, post_match)

    def test_basic_template_directory(self):
        pre_match, num_matched, post_match = self._match_file(self.new_temp)
        self.assertEqual(num_matched, 1)
        self.assertTrue(settings.SITE_ROOT not in ''.join(pre_match))
        self.assertTrue(settings.SITE_ROOT in ''.join(post_match))

    def test_no_template_directory(self):
        pre_match, num_matched, post_match = self._match_file(self.new_no_temp)
        self.assertEqual(num_matched, 0)
        self.assertTrue(settings.SITE_ROOT not in pre_match)


"""
