from django.test import TestCase
from core import hacks

class TestHacks(TestCase):
    fixtures = ['eric.json', 'test_data.json']

    def setUp(self):
        hacks.patch_meta_path()

    def tearDown(self):
        hacks.unpatch_meta_path()

    def test_hack_failed_import(self):
        import boogy
        self.assertTrue(str(boogy), "<Silly Human, I'm not real>")

    #def test_hack_correct_import(self):
        #import itertools
        #self.assertFalse(str(itertools), "<Silly Human, I'm not real>")
