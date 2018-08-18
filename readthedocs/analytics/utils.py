"""Utilities related to analytics"""

from __future__ import absolute_import, unicode_literals
import hashlib
import logging

from django.conf import settings
from django.utils.encoding import force_text, force_bytes
from django.utils.crypto import get_random_string
import requests
from user_agents import parse

try:
    # Python 3.3+ only
    import ipaddress
except ImportError:
    from .vendor import ipaddress

log = logging.getLogger(__name__)   # noqa


def get_client_ip(request):
    """Gets the real IP based on a request object"""
    ip_address = request.META.get('REMOTE_ADDR')

    # Get the original IP address (eg. "X-Forwarded-For: client, proxy1, proxy2")
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
    if x_forwarded_for:
        ip_address = x_forwarded_for.rsplit(':')[0]

    return ip_address


def anonymize_ip_address(ip_address):
    """Anonymizes an IP address by zeroing the last 2 bytes"""
    # Used to anonymize an IP by zero-ing out the last 2 bytes
    ip_mask = int('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000', 16)

    try:
        ip_obj = ipaddress.ip_address(force_text(ip_address))
    except ValueError:
        return None

    anonymized_ip = ipaddress.ip_address(int(ip_obj) & ip_mask)
    return anonymized_ip.compressed


def anonymize_user_agent(user_agent):
    """Anonymizes rare user agents"""
    # If the browser family is not recognized, this is a rare user agent
    parsed_ua = parse(user_agent)
    if parsed_ua.browser.family == 'Other' or parsed_ua.os.family == 'Other':
        return 'Rare user agent'

    return user_agent


def send_to_analytics(data):
    """Sends data to Google Analytics"""
    if data.get('uip') and data.get('ua'):
        data['cid'] = generate_client_id(data['uip'], data['ua'])

    if 'uip' in data:
        # Anonymize IP address if applicable
        data['uip'] = anonymize_ip_address(data['uip'])

    if 'ua' in data:
        # Anonymize user agent if it is rare
        data['ua'] = anonymize_user_agent(data['ua'])

    resp = None
    log.debug('Sending data to analytics: %s', data)
    try:
        resp = requests.post(
            'https://www.google-analytics.com/collect',
            data=data,
            timeout=3,      # seconds
        )
    except requests.Timeout:
        log.warning('Timeout sending to Google Analytics')

    if resp and not resp.ok:
        log.warning('Unknown error sending to Google Analytics')


def generate_client_id(ip_address, user_agent):
    """
    Create an advertising ID

    This simplifies things but essentially if a user has the same IP and same UA,
    this will treat them as the same user for analytics purposes
    """
    salt = b'advertising-client-id'

    hash_id = hashlib.sha256()
    hash_id.update(force_bytes(settings.SECRET_KEY))
    hash_id.update(salt)
    if ip_address:
        hash_id.update(force_bytes(ip_address))
    if user_agent:
        hash_id.update(force_bytes(user_agent))

    if not ip_address and not user_agent:
        # Since no IP and no UA were specified,
        # there's no way to distinguish sessions.
        # Instead, just treat every user differently
        hash_id.update(force_bytes(get_random_string()))

    return hash_id.hexdigest()
