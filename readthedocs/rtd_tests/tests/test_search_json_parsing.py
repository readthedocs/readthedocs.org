# -*- coding: utf-8 -*-
import os

from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.search.parse_json import process_file


base_dir = os.path.dirname(os.path.dirname(__file__))


class TestHacks(TestCase):

    @override_settings(MEDIA_ROOT=base_dir)
    def test_h2_parsing(self):
        data = process_file('files/api.fjson')

        self.assertEqual(data['sections'][1]['id'], 'a-basic-api-client-using-slumber')
        # Only capture h2's after the first section
        for obj in data['sections'][1:]:
            self.assertEqual(obj['content'][:5], '\n<h2>')
