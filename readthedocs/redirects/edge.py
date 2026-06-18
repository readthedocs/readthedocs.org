"""
Serialize redirect/routing data for the Cloudflare edge.

This is the origin side of the "heavy redirects at the edge" design
(see ``docs/dev/design/redirects-at-the-edge.rst``).

We replicate a compact, read-optimized view of the data the edge needs
into an :class:`EdgeStore` (Cloudflare Workers KV in production):

- ``domain:{host}`` -> the project a host belongs to.
- ``project:{slug}`` -> routing config + the edge-eligible redirect rules.

Only redirects that can be decided *without* origin state are replicated.
In practice that means **forced exact redirects**: they match on the whole
request path and don't depend on whether the target file exists, the version
list, or the privacy level. Everything else stays at the origin, which keeps
the full, authoritative redirect logic.
"""

import json
from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.core.cache import cache
from django.utils.module_loading import import_string

from readthedocs.redirects.constants import EXACT_REDIRECT
from readthedocs.redirects.constants import SPLAT_PLACEHOLDER


log = structlog.get_logger(__name__)


def serialize_redirect(redirect):
    """Serialize a single redirect into the compact edge representation."""
    return {
        "type": redirect.redirect_type,
        "from": redirect.from_url,
        # Precomputed prefix for wildcard (``*``) matching, so the edge
        # doesn't need to re-derive it. ``None`` means an exact match.
        "from_prefix": redirect.from_url_without_rest,
        "to": redirect.to_url,
        "status": redirect.http_status,
    }


def get_edge_redirects(project):
    """
    Return the ordered, edge-eligible redirects for a project.

    Only enabled, forced exact redirects can be served at the edge: they match
    on the whole request path and don't depend on origin state (file existence,
    version list, privacy). Everything else stays at the origin. Page and
    clean-URL redirects are a follow-up (see the design doc).
    """
    redirects = (
        project.redirects.filter(force=True, redirect_type=EXACT_REDIRECT)
        # ``enabled`` is nullable, so exclude only explicit ``False``.
        .exclude(enabled=False)
        .order_by("position", "-update_dt")
    )
    return [serialize_redirect(redirect) for redirect in redirects]


def get_project_hosts(project):
    """
    Return all hostnames that serve this project's docs.

    This is the project's subdomain on our public domain plus any custom
    domains. These are the keys the edge uses to map a request to a project.
    """
    hosts = []
    subdomain = project.subdomain(use_canonical_domain=False)
    if subdomain:
        hosts.append(subdomain)
    for domain in project.domains.all():
        hosts.append(domain.domain)
    return hosts


def serialize_project(project):
    """
    Build the routing payload the edge needs to serve a project.

    For now this is just the edge-eligible redirect rules. When structural
    redirects (canonical domain, default version) move to the edge, their
    config gets added here as the Worker grows to consume it.
    """
    return {
        "project": project.slug,
        "redirects": get_edge_redirects(project),
    }


def _normalize_path(path):
    """Drop the query string and ensure a single leading slash."""
    parsed = urlparse(path)
    path = parsed._replace(query="", fragment="").geturl()
    return "/" + path.lstrip("/")


def match_redirect(payload, path):
    """
    Reference implementation of the edge redirect matcher.

    This mirrors what the Cloudflare Worker does, and exists so we can test
    parity with the origin's matching in Python. Returns a
    ``(to_url, status)`` tuple or ``None`` when no rule matches.

    :param payload: A project payload from :func:`serialize_project`.
    :param path: The request path (may include a query string).
    """
    normalized = _normalize_path(path)
    without_slash = normalized.rstrip("/") or "/"

    for redirect in payload["redirects"]:
        if redirect["type"] != EXACT_REDIRECT:
            # Only exact redirects are supported at the edge for now.
            continue

        from_prefix = redirect["from_prefix"]
        to_url = redirect["to"]

        if from_prefix is None:
            # Exact match, with or without a trailing slash.
            if without_slash == redirect["from"].rstrip("/"):
                return to_url, redirect["status"]
            continue

        # Wildcard (``*``) match: everything after the prefix becomes the splat.
        if normalized.startswith(from_prefix):
            splat = normalized[len(from_prefix) :]
            resolved = to_url.replace(SPLAT_PLACEHOLDER, splat)
            if _will_cause_infinite_redirect(from_prefix, to_url, normalized):
                log.debug("Skipping edge redirect to avoid a loop", path=normalized)
                continue
            return resolved, redirect["status"]

    return None


def _will_cause_infinite_redirect(from_prefix, to_url, current_path):
    """Mirror ``Redirect._will_cause_infinite_redirect`` for the edge."""
    if SPLAT_PLACEHOLDER not in to_url:
        return False
    to_without_splat = to_url.split(SPLAT_PLACEHOLDER, maxsplit=1)[0]
    redirects_to_subpath = to_without_splat.startswith(from_prefix)
    return redirects_to_subpath and current_path.startswith(to_without_splat)


def edge_redirects_header(project):
    """
    Build the value for the ``X-RTD-Edge-Redirects`` response header.

    This is the "no-config" delivery path: instead of pushing data to the
    edge through the Cloudflare API, the origin emits the project's
    edge-eligible redirects on a response header, and the Worker caches them.
    The value is a compact JSON array of rules. Returns ``None`` when the
    project has no edge-eligible redirects (so we don't emit an empty header).
    """
    redirects = get_edge_redirects(project)
    if not redirects:
        return None
    return json.dumps(redirects, separators=(",", ":"))


def cached_edge_redirects_header(project):
    """
    Cached wrapper around :func:`edge_redirects_header`.

    The header is emitted on origin responses, so we cache the serialized
    value per project to avoid querying redirects on every response. A short
    TTL keeps the edge reasonably fresh while bounding origin cost to roughly
    one query per project per TTL.
    """
    cache_key = f"edge-redirects-header:{project.slug}"
    # We cache "no redirects" as ``""`` (not ``None``) so that the common case
    # of a project without forced redirects is a cache hit, not a miss that
    # re-queries on every response. ``cache.get`` returns ``None`` only on a
    # true miss.
    value = cache.get(cache_key)
    if value is None:
        value = edge_redirects_header(project) or ""
        cache.set(cache_key, value, settings.RTD_EDGE_REDIRECTS_HEADER_TTL)
    return value or None


def get_edge_store():
    """Return the configured edge store backend."""
    store_class = import_string(settings.RTD_EDGE_REDIRECTS_STORE_CLASS)
    return store_class()


def sync_project(project, store=None):
    """Replicate a project's routing config and redirects to the edge."""
    store = store or get_edge_store()
    payload = serialize_project(project)
    store.set_project(project.slug, payload)
    for host in get_project_hosts(project):
        store.set_domain(host, project.slug)
    log.info(
        "Synced project to the edge.",
        project_slug=project.slug,
        redirects=len(payload["redirects"]),
    )


def remove_project(slug, hosts, store=None):
    """Remove a project (and its hosts) from the edge."""
    store = store or get_edge_store()
    store.delete_project(slug)
    for host in hosts:
        store.delete_domain(host)
    log.info("Removed project from the edge.", project_slug=slug)


class EdgeStore:
    """Interface for a backend that holds the edge routing data."""

    def set_project(self, slug, payload):
        raise NotImplementedError

    def get_project(self, slug):
        raise NotImplementedError

    def delete_project(self, slug):
        raise NotImplementedError

    def set_domain(self, host, slug):
        raise NotImplementedError

    def get_domain(self, host):
        raise NotImplementedError

    def delete_domain(self, host):
        raise NotImplementedError


class LocalEdgeStore(EdgeStore):
    """
    In-memory edge store for development and tests.

    The data lives in class-level dicts so it behaves like a single shared
    store within a process, mirroring the global namespace of a real KV store.
    """

    projects = {}
    domains = {}

    def set_project(self, slug, payload):
        self.projects[slug] = payload

    def get_project(self, slug):
        return self.projects.get(slug)

    def delete_project(self, slug):
        self.projects.pop(slug, None)

    def set_domain(self, host, slug):
        self.domains[host] = slug

    def get_domain(self, host):
        return self.domains.get(host)

    def delete_domain(self, host):
        self.domains.pop(host, None)

    @classmethod
    def reset(cls):
        cls.projects = {}
        cls.domains = {}
