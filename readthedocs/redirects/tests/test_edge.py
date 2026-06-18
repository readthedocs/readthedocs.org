"""Tests for serving heavy redirects at the edge."""

import json

from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.projects.models import Project
from readthedocs.redirects import edge
from readthedocs.redirects.constants import EXACT_REDIRECT
from readthedocs.redirects.constants import PAGE_REDIRECT
from readthedocs.redirects.edge import LocalEdgeStore
from readthedocs.redirects.models import Redirect


@override_settings(PUBLIC_DOMAIN="readthedocs.io")
class EdgeSerializationTests(TestCase):
    def setUp(self):
        LocalEdgeStore.reset()
        self.project = Project.objects.create(
            name="Pip",
            slug="pip",
            repo="https://github.com/pip/pip",
            default_version="latest",
            language="en",
        )

    def test_only_forced_redirects_are_edge_eligible(self):
        forced = Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/old/*",
            to_url="/new/:splat",
            force=True,
        )
        # Not forced -> excluded.
        Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/other",
            to_url="/elsewhere",
            force=False,
        )
        # Disabled -> excluded.
        Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/disabled",
            to_url="/somewhere",
            force=True,
            enabled=False,
        )
        redirects = edge.get_edge_redirects(self.project)
        assert len(redirects) == 1
        assert redirects[0]["from"] == forced.from_url
        assert redirects[0]["to"] == "/new/:splat"
        assert redirects[0]["from_prefix"] == "/old/"

    def test_page_redirects_are_not_edge_eligible_yet(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type=PAGE_REDIRECT,
            from_url="/page.html",
            to_url="/new.html",
            force=True,
        )
        assert edge.get_edge_redirects(self.project) == []

    def test_serialize_project_includes_redirects(self):
        payload = edge.serialize_project(self.project)
        assert payload["project"] == "pip"
        assert payload["redirects"] == []

    def test_get_project_hosts_includes_subdomain(self):
        hosts = edge.get_project_hosts(self.project)
        assert "pip.readthedocs.io" in hosts

    def test_sync_writes_project_and_domains_to_store(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/old/*",
            to_url="/new/:splat",
            force=True,
        )
        store = LocalEdgeStore()
        edge.sync_project(self.project, store=store)

        assert store.get_project("pip")["redirects"][0]["to"] == "/new/:splat"
        assert store.get_domain("pip.readthedocs.io") == "pip"

    def test_remove_project_clears_store(self):
        store = LocalEdgeStore()
        edge.sync_project(self.project, store=store)
        hosts = edge.get_project_hosts(self.project)
        edge.remove_project("pip", hosts, store=store)
        assert store.get_project("pip") is None
        assert store.get_domain("pip.readthedocs.io") is None


@override_settings(PUBLIC_DOMAIN="readthedocs.io")
class EdgeHeaderDeliveryTests(TestCase):
    """The no-config delivery path: rules ride on a response header."""

    def setUp(self):
        cache.clear()
        self.project = Project.objects.create(
            name="Pip",
            slug="pip",
            repo="https://github.com/pip/pip",
            default_version="latest",
            language="en",
        )

    def test_header_is_none_without_forced_redirects(self):
        assert edge.edge_redirects_header(self.project) is None

    def test_header_serializes_forced_redirects_as_json(self):
        Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/old/*",
            to_url="/new/:splat",
            force=True,
        )
        header = edge.edge_redirects_header(self.project)
        rules = json.loads(header)
        assert rules[0]["from"] == "/old/*"
        assert rules[0]["to"] == "/new/:splat"

    def test_cached_header_is_reused(self):
        value = edge.cached_edge_redirects_header(self.project)
        assert value is None
        # A redirect added after caching is not seen until the cache expires.
        Redirect.objects.create(
            project=self.project,
            redirect_type=EXACT_REDIRECT,
            from_url="/old",
            to_url="/new",
            force=True,
        )
        assert edge.cached_edge_redirects_header(self.project) is None
        cache.clear()
        assert edge.cached_edge_redirects_header(self.project) is not None


class EdgeMatcherTests(TestCase):
    """The reference matcher must stay in parity with the Worker/origin."""

    def _payload(self, redirects):
        return {"project": "pip", "redirects": redirects}

    def test_exact_match_without_wildcard(self):
        payload = self._payload(
            [
                {
                    "type": EXACT_REDIRECT,
                    "from": "/old",
                    "from_prefix": None,
                    "to": "/new",
                    "status": 301,
                }
            ]
        )
        assert edge.match_redirect(payload, "/old") == ("/new", 301)
        # Trailing slash is normalized away.
        assert edge.match_redirect(payload, "/old/") == ("/new", 301)
        assert edge.match_redirect(payload, "/other") is None

    def test_wildcard_match_applies_splat(self):
        payload = self._payload(
            [
                {
                    "type": EXACT_REDIRECT,
                    "from": "/old/*",
                    "from_prefix": "/old/",
                    "to": "/new/:splat",
                    "status": 302,
                }
            ]
        )
        assert edge.match_redirect(payload, "/old/a/b.html") == ("/new/a/b.html", 302)

    def test_query_string_is_ignored_for_matching(self):
        payload = self._payload(
            [
                {
                    "type": EXACT_REDIRECT,
                    "from": "/old",
                    "from_prefix": None,
                    "to": "/new",
                    "status": 301,
                }
            ]
        )
        assert edge.match_redirect(payload, "/old?foo=bar") == ("/new", 301)

    def test_infinite_redirect_is_skipped(self):
        payload = self._payload(
            [
                {
                    "type": EXACT_REDIRECT,
                    "from": "/dir/*",
                    "from_prefix": "/dir/",
                    "to": "/dir/sub/:splat",
                    "status": 301,
                }
            ]
        )
        assert edge.match_redirect(payload, "/dir/sub/page.html") is None

    def test_first_match_wins(self):
        payload = self._payload(
            [
                {
                    "type": EXACT_REDIRECT,
                    "from": "/a/*",
                    "from_prefix": "/a/",
                    "to": "/first/:splat",
                    "status": 301,
                },
                {
                    "type": EXACT_REDIRECT,
                    "from": "/a/*",
                    "from_prefix": "/a/",
                    "to": "/second/:splat",
                    "status": 301,
                },
            ]
        )
        assert edge.match_redirect(payload, "/a/x") == ("/first/x", 301)
