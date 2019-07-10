# -*- coding: utf-8 -*-
import os

from django.test import TestCase

from readthedocs.search.parse_json import process_file


base_dir = os.path.dirname(os.path.dirname(__file__))

class TestHacks(TestCase):

    def test_h2_parsing(self):
        data = process_file(
            os.path.join(
                base_dir,
                'files/api.fjson',
            ),
        )
        self.assertEqual(data['sections'][1]['id'], 'a-basic-api-client-using-slumber')
        self.assertEqual(data['path'], 'api')
        self.assertEqual(data['title'], 'Read the Docs Public API')
