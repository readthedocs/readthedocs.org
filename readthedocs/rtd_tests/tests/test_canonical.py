from django.test import TestCase
from projects.models import Project


class TestCanonical(TestCase):

    def setUp(self):
        self.p = Project(
            name='foo',
            repo='http://github.com/ericholscher/django-kong',
            )
        self.p.save()


    def test_canonical_clean(self):
        # Only a url
        self.p.canonical_url = "djangokong.com"
        self.assertEqual(self.p.clean_canonical_url, "http://djangokong.com/")
        # Extra bits in the URL
        self.p.canonical_url = "http://djangokong.com/en/latest/"
        self.assertEqual(self.p.clean_canonical_url, "http://djangokong.com/")
        self.p.canonical_url = "http://djangokong.com//"
        self.assertEqual(self.p.clean_canonical_url, "http://djangokong.com/")
        # Subdomain
        self.p.canonical_url = "foo.djangokong.com"
        self.assertEqual(self.p.clean_canonical_url, "http://foo.djangokong.com/")
        # Https
        self.p.canonical_url = "https://djangokong.com//"
        self.assertEqual(self.p.clean_canonical_url, "https://djangokong.com/")
        self.p.canonical_url = "https://foo.djangokong.com//"
        self.assertEqual(self.p.clean_canonical_url, "https://foo.djangokong.com/")

    """
    # Turn this feature off for now, until we fix the UI.
    def test_canonical_subdomain(self):
        self.p.canonical_url = "https://djangokong.com//"
        with self.settings(USE_SUBDOMAIN=True):
            self.assertEqual(self.p.get_docs_url(), "http://djangokong.com/en/latest/")
    """
