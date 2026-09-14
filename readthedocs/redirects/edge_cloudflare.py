"""
Cloudflare Workers KV backend for the edge redirect store.

This writes the routing data produced by :mod:`readthedocs.redirects.edge`
into a Cloudflare Workers KV namespace, which the edge Worker reads on each
request. See ``docs/dev/design/redirects-at-the-edge.rst``.

Configuration (settings):

- ``RTD_EDGE_REDIRECTS_CLOUDFLARE_ACCOUNT_ID``
- ``RTD_EDGE_REDIRECTS_CLOUDFLARE_NAMESPACE_ID``
- ``RTD_EDGE_REDIRECTS_CLOUDFLARE_TOKEN``
"""

import json

import requests
import structlog
from django.conf import settings

from readthedocs.redirects.edge import EdgeStore


log = structlog.get_logger(__name__)

API_BASE = "https://api.cloudflare.com/client/v4"
# KV is read-on-every-request; keep keys namespaced to avoid collisions.
DOMAIN_PREFIX = "domain:"
PROJECT_PREFIX = "project:"


class CloudflareKVStore(EdgeStore):
    """Read/write the edge routing data in a Cloudflare Workers KV namespace."""

    def __init__(self):
        self.account_id = settings.RTD_EDGE_REDIRECTS_CLOUDFLARE_ACCOUNT_ID
        self.namespace_id = settings.RTD_EDGE_REDIRECTS_CLOUDFLARE_NAMESPACE_ID
        self.token = settings.RTD_EDGE_REDIRECTS_CLOUDFLARE_TOKEN

    @property
    def _base_url(self):
        return (
            f"{API_BASE}/accounts/{self.account_id}"
            f"/storage/kv/namespaces/{self.namespace_id}"
        )

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _put(self, key, value):
        response = requests.put(
            f"{self._base_url}/values/{key}",
            headers=self._headers,
            data=json.dumps(value),
            timeout=10,
        )
        response.raise_for_status()

    def _get(self, key):
        response = requests.get(
            f"{self._base_url}/values/{key}",
            headers=self._headers,
            timeout=10,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def _delete(self, key):
        response = requests.delete(
            f"{self._base_url}/values/{key}",
            headers=self._headers,
            timeout=10,
        )
        if response.status_code != 404:
            response.raise_for_status()

    def set_project(self, slug, payload):
        self._put(f"{PROJECT_PREFIX}{slug}", payload)

    def get_project(self, slug):
        return self._get(f"{PROJECT_PREFIX}{slug}")

    def delete_project(self, slug):
        self._delete(f"{PROJECT_PREFIX}{slug}")

    def set_domain(self, host, slug):
        self._put(f"{DOMAIN_PREFIX}{host}", {"project": slug})

    def get_domain(self, host):
        return self._get(f"{DOMAIN_PREFIX}{host}")

    def delete_domain(self, host):
        self._delete(f"{DOMAIN_PREFIX}{host}")
