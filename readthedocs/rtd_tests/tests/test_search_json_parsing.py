import os

from django.test import TestCase

from search.parse_json import process_file

base_dir = os.path.dirname(os.path.dirname(__file__))

class TestHacks(TestCase):

    def test_h2_parsing(self):
        data = process_file(
            os.path.join(
                base_dir,
                'files/api.fjson',
            )
        )
        self.assertEqual(data['sections'][1]['id'], 'a-basic-api-client-using-slumber')
        # Only capture h2's after the first section
        for obj in data['sections'][1:]:
            self.assertEqual(obj['content'][:5], '\n<h2>')
