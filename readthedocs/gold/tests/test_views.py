import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get


class TestViews(TestCase):
    def setUp(self):
        self.user = get(User)

    def test_csp_headers(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("gold_detail"))
        self.assertEqual(response.status_code, 200)
        csp = response["Content-Security-Policy"]
        self.assertTrue(re.match(r".*\s+script-src [^;]*'unsafe-inline'", csp))
