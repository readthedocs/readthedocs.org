from readthedocs.rtd_tests.tests.test_footer import TestFooterHTML
from django.test import override_settings


@override_settings(ROOT_URLCONF='readthedocs.proxito.urls')
class TestProxiedFooterHTML(TestFooterHTML):

    def setUp(self):
        super().setUp()
        self.host = 'pip.readthedocs.io'

    def render(self):
        r = self.client.get(self.url, HTTP_HOST=self.host)
        return r
