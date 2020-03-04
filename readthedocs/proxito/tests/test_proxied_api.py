from django.test import TestCase, override_settings

from readthedocs.rtd_tests.tests.test_footer import BaseTestFooterHTML


@override_settings(ROOT_URLCONF='readthedocs.proxito.urls')
class TestProxiedFooterHTML(BaseTestFooterHTML, TestCase):

    def setUp(self):
        super().setUp()
        self.host = 'pip.readthedocs.io'

    def render(self):
        r = self.client.get(self.url, HTTP_HOST=self.host)
        return r
