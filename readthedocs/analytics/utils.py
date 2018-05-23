"""Utilities related to analytics"""

from __future__ import absolute_import, unicode_literals
import logging

from django.utils.encoding import force_text
import requests

try:
    # Python 3.3+ only
    import ipaddress
except ImportError:
    from .vendor import ipaddress

log = logging.getLogger(__name__)

# Used to anonymize an IP by zero-ing out the last 2 bytes
MASK = int('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000', 16)


def get_client_ip(request):
    """Gets the real IP based on a request object"""
    ip_address = request.META.get('REMOTE_ADDR')

    # Get the original IP address (eg. "X-Forwarded-For: client, proxy1, proxy2")
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
    if x_forwarded_for:
        ip_address = x_forwarded_for

    return ip_address


def anonymize_ipaddress(ip_address):
    """Anonymizes an IP address by zeroing the last 2 bytes"""
    try:
        ip_obj = ipaddress.ip_address(force_text(ip_address))
    except ValueError:
        return None

    anonymized_ip = ipaddress.ip_address(int(ip_obj) & MASK)
    return anonymized_ip.compressed


def send_to_analytics(data):
    """Sends data to Google Analytics"""
    if data['uip']:
        # Anonymize IP address if applicable
        data['uip'] = anonymize_ipaddress(data['uip'])

    resp = None
    try:
        resp = requests.post(
            'https://www.google-analytics.com/collect',
            data=data,
        )
    except requests.Timeout:
        log.warning('Timeout sending to Google Analytics')

    if resp and not resp.ok:
        log.warning('Unknown error sending to Google Analytics')
