from django.test import TestCase
from django.urls import reverse


class TestProfileDetailURLs(TestCase):
    def test_profile_detail_url(self):
        url = reverse(
            "profiles_profile_detail",
            kwargs={"username": "foo+bar"},
        )
        self.assertEqual(url, "/profiles/foo+bar/")

        url = reverse(
            "profiles_profile_detail",
            kwargs={"username": "abc+def@ghi.jkl"},
        )
        self.assertEqual(url, "/profiles/abc+def@ghi.jkl/")

        url = reverse(
            "profiles_profile_detail",
            kwargs={"username": "abc-def+ghi"},
        )
        self.assertEqual(url, "/profiles/abc-def+ghi/")
