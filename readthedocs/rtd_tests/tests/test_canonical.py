from django.test import TestCase
from projects.models import Project


class TestCanonical(TestCase):

    def test_canonical_clean(self):
        p = Project(
            name='foo',
            repo='http://github.com/ericholscher/django-kong',
            )

        # Only a url
        p.canonical_url = "djangokong.com"
        self.assertEqual(p.clean_canonical_url, "http://djangokong.com/")
        # Extra bits in the URL
        p.canonical_url = "http://djangokong.com/en/latest/"
        self.assertEqual(p.clean_canonical_url, "http://djangokong.com/")
        p.canonical_url = "http://djangokong.com//"
        self.assertEqual(p.clean_canonical_url, "http://djangokong.com/")
        # Subdomain
        p.canonical_url = "foo.djangokong.com"
        self.assertEqual(p.clean_canonical_url, "http://foo.djangokong.com/")
        # Https
        p.canonical_url = "https://djangokong.com//"
        self.assertEqual(p.clean_canonical_url, "https://djangokong.com/")
        p.canonical_url = "https://foo.djangokong.com//"
        self.assertEqual(p.clean_canonical_url, "https://foo.djangokong.com/")
