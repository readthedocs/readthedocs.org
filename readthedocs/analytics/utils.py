"""Utilities related to analytics."""

import hashlib
import ipaddress

import structlog
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from user_agents import parse


log = structlog.get_logger(__name__)  # noqa


def get_client_ip(request):
    """
    Gets the real client's IP address.

    It returns the real IP address of the client based on ``HTTP_X_FORWARDED_FOR``
    header. If ``HTTP_X_FORWARDED_FOR`` is not found, it returns the value of
    ``REMOTE_ADDR`` header and returns ``None`` if both the headers are not found.
    """
    x_forwarded_for = request.headers.get("X-Forwarded-For", None)
    if x_forwarded_for:
        # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
        # The client's IP will be the first one.
        # (eg. "X-Forwarded-For: client, proxy1, proxy2")
        client_ip = x_forwarded_for.split(",")[0].strip()

        # Removing the port number (if present)
        # But be careful about IPv6 addresses
        if client_ip.count(":") == 1:
            client_ip = client_ip.rsplit(":", maxsplit=1)[0]
    else:
        client_ip = request.META.get("REMOTE_ADDR", None)

    return client_ip


def anonymize_ip_address(ip_address):
    """Anonymizes an IP address by zeroing the last 2 bytes."""
    # Used to anonymize an IP by zero-ing out the last 2 bytes
    ip_mask = int("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000", 16)

    try:
        ip_obj = ipaddress.ip_address(force_str(ip_address))
    except ValueError:
        return None

    anonymized_ip = ipaddress.ip_address(int(ip_obj) & ip_mask)
    return anonymized_ip.compressed


def anonymize_user_agent(user_agent):
    """Anonymizes rare user agents."""
    # If the browser family is not recognized, this is a rare user agent
    parsed_ua = parse(user_agent)
    if parsed_ua.browser.family == "Other" or parsed_ua.os.family == "Other":
        return "Rare user agent"

    return user_agent


def generate_client_id(ip_address, user_agent):
    """
    Create an advertising ID.

    This simplifies things but essentially if a user has the same IP and same
    UA, this will treat them as the same user for analytics purposes
    """
    salt = b"advertising-client-id"

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
        hash_id.update(force_bytes(get_random_string(length=12)))

    return hash_id.hexdigest()
