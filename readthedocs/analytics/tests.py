# -*- coding: utf-8 -*-
from django.test import TestCase, RequestFactory

from .utils import (
    anonymize_ip_address,
    anonymize_user_agent,
    get_client_ip,
)


class UtilsTests(TestCase):
    def test_anonymize_ip(self):
        self.assertEqual(anonymize_ip_address('127.0.0.1'), '127.0.0.0')
        self.assertEqual(anonymize_ip_address('127.127.127.127'), '127.127.0.0')
        self.assertEqual(
            anonymize_ip_address('3ffe:1900:4545:3:200:f8ff:fe21:67cf'),
            '3ffe:1900:4545:3:200:f8ff:fe21:0',
        )
        self.assertEqual(
            anonymize_ip_address('fe80::200:f8ff:fe21:67cf'),
            'fe80::200:f8ff:fe21:0',
        )

    def test_anonymize_ua(self):
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        self.assertEqual(
            anonymize_user_agent(ua),
            ua,
        )

        self.assertEqual(
            anonymize_user_agent('Some rare user agent'),
            'Rare user agent',
        )

    def test_get_client_ip_with_x_forwarded_for(self):
        # only client's ip is present
        request = RequestFactory().get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.195'
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, '203.0.113.195')

        # only client's ip is present
        request = RequestFactory().get('/')
        ip = '2001:abc:def:012:345:6789:abcd:ef12'
        request.META['HTTP_X_FORWARDED_FOR'] = ip
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, ip)

        # proxy1 and proxy2 are present along with client's ip
        request = RequestFactory().get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.195, 70.41.3.18, 150.172.238.178'
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, '203.0.113.195')

        # client ip with port
        request = RequestFactory().get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.195:8080, 70.41.3.18, 150.172.238.178'
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, '203.0.113.195')

        # client ip (ipv6), other clients with port
        request = RequestFactory().get('/')
        ip = '2001:abc:def:012:345:6789:abcd:ef12'
        x_forwarded_for = f'{ip}, 203.0.113.195:8080, 70.41.3.18'
        request.META['HTTP_X_FORWARDED_FOR'] = x_forwarded_for
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, ip)

        # client ip with port but not proxy1 and proxy2
        request = RequestFactory().get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.195:8080'
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, '203.0.113.195')

        # no header is present
        request = RequestFactory().get('/')
        if request.META['REMOTE_ADDR']:
            del request.META['REMOTE_ADDR']
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, None)

    def test_get_client_ip_with_remote_addr(self):

        request = RequestFactory().get('/')
        self.assertIsNone(request.META.get('HTTP_X_FORWARDED_FOR'))
        request.META['REMOTE_ADDR'] = '203.0.113.195'
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, '203.0.113.195')
