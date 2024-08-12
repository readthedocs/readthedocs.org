import re

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get


class TestViews(TestCase):
    def setUp(self):
        self.user = get(User)

    def test_csp_headers(self):
        self.client.force_login(self.user)
        csp_header = "Content-Security-Policy"
        script_src_regex = re.compile(r".*\s+script-src [^;]*'unsafe-inline'")
        url = reverse("gold_detail")

        with override_settings(RTD_EXT_THEME_ENABLED=False):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertIsNone(script_src_regex.match(resp[csp_header]))

        with override_settings(RTD_EXT_THEME_ENABLED=True):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(script_src_regex.match(resp[csp_header]))
