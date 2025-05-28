import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get
from readthedocs.payments.tests.utils import PaymentMixin


class TestViews(PaymentMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get(User)

    def test_csp_headers(self):
        """
        Test CSP headers aren't altered.

        This view originally altered the CSP directives based on whether we were
        using the new dashboard. We weren't using inline scripts in this view
        however, so this was reverted. The tests remain for now, but aren't
        super useful and will break when we change `script-src` in base settings.
        """
        self.client.force_login(self.user)
        csp_header = "Content-Security-Policy"
        script_src_regex = re.compile(r".*\s+script-src [^;]*'unsafe-inline'")
        url = reverse("gold_detail")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(script_src_regex.match(resp[csp_header]))
