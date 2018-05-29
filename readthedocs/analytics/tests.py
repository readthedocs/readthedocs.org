from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from .utils import anonymize_ipaddress, anonymize_useragent


class UtilsTests(TestCase):
    def test_anonymize_ip(self):
        self.assertEqual(anonymize_ipaddress('127.0.0.1'), '127.0.0.0')
        self.assertEqual(anonymize_ipaddress('127.127.127.127'), '127.127.0.0')
        self.assertEqual(
            anonymize_ipaddress('3ffe:1900:4545:3:200:f8ff:fe21:67cf'),
            '3ffe:1900:4545:3:200:f8ff:fe21:0',
        )
        self.assertEqual(
            anonymize_ipaddress('fe80::200:f8ff:fe21:67cf'),
            'fe80::200:f8ff:fe21:0',
        )

    def test_anonymize_ua(self):
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        self.assertEqual(
            anonymize_useragent(ua),
            ua,
        )

        self.assertEqual(
            anonymize_useragent('Some rare user agent'),
            'Rare user agent',
        )

