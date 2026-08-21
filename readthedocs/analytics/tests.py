from unittest import mock

import pytest
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project

from .models import PageView
from .utils import anonymize_ip_address, anonymize_user_agent, get_client_ip


class UtilsTests(TestCase):
    def test_anonymize_ip(self):
        self.assertEqual(anonymize_ip_address("127.0.0.1"), "127.0.0.0")
        self.assertEqual(anonymize_ip_address("127.127.127.127"), "127.127.0.0")
        self.assertEqual(
            anonymize_ip_address("3ffe:1900:4545:3:200:f8ff:fe21:67cf"),
            "3ffe:1900:4545:3:200:f8ff:fe21:0",
        )
        self.assertEqual(
            anonymize_ip_address("fe80::200:f8ff:fe21:67cf"),
            "fe80::200:f8ff:fe21:0",
        )

    def test_anonymize_ua(self):
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        self.assertEqual(
            anonymize_user_agent(ua),
            ua,
        )

        self.assertEqual(
            anonymize_user_agent("Some rare user agent"),
            "Rare user agent",
        )

    def test_get_client_ip_with_x_forwarded_for(self):
        # only client's ip is present
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.195"
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "203.0.113.195")

        # only client's ip is present
        request = RequestFactory().get("/")
        ip = "2001:abc:def:012:345:6789:abcd:ef12"
        request.META["HTTP_X_FORWARDED_FOR"] = ip
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, ip)

        # proxy1 and proxy2 are present along with client's ip
        request = RequestFactory().get("/")
        request.META[
            "HTTP_X_FORWARDED_FOR"
        ] = "203.0.113.195, 70.41.3.18, 150.172.238.178"
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "203.0.113.195")

        # client ip with port
        request = RequestFactory().get("/")
        request.META[
            "HTTP_X_FORWARDED_FOR"
        ] = "203.0.113.195:8080, 70.41.3.18, 150.172.238.178"
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "203.0.113.195")

        # client ip (ipv6), other clients with port
        request = RequestFactory().get("/")
        ip = "2001:abc:def:012:345:6789:abcd:ef12"
        x_forwarded_for = f"{ip}, 203.0.113.195:8080, 70.41.3.18"
        request.META["HTTP_X_FORWARDED_FOR"] = x_forwarded_for
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, ip)

        # client ip with port but not proxy1 and proxy2
        request = RequestFactory().get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.195:8080"
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "203.0.113.195")

        # no header is present
        request = RequestFactory().get("/")
        if request.META["REMOTE_ADDR"]:
            del request.META["REMOTE_ADDR"]
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, None)

    def test_get_client_ip_with_remote_addr(self):
        request = RequestFactory().get("/")
        self.assertIsNone(request.headers.get("X-Forwarded-For"))
        request.META["REMOTE_ADDR"] = "203.0.113.195"
        client_ip = get_client_ip(request)
        self.assertEqual(client_ip, "203.0.113.195")


@pytest.mark.proxito
@override_settings(
    PUBLIC_DOMAIN="readthedocs.io", RTD_EXTERNAL_VERSION_DOMAIN="readthedocs.build"
)
class AnalyticsPageViewsTests(TestCase):
    def setUp(self):
        self.project = get(
            Project,
            slug="pip",
            privacy_level=PUBLIC,
        )
        self.version = get(Version, slug="1.8", project=self.project)
        self.project.versions.all().update(privacy_level=PUBLIC)
        self.absolute_uri = (
            f"https://{self.project.slug}.readthedocs.io/en/latest/index.html"
        )
        self.host = f"{self.project.slug}.readthedocs.io"
        self.url = (
            reverse("analytics_api")
            + f"?project={self.project.slug}&version={self.version.slug}"
            f"&absolute_uri={self.absolute_uri}"
        )

        self.today = timezone.now()
        self.tomorrow = timezone.now() + timezone.timedelta(days=1)
        self.yesterday = timezone.now() - timezone.timedelta(days=1)

    def test_invalid_uri(self):
        assert PageView.objects.all().count() == 0
        url = (
            reverse("analytics_api")
            + f"?project={self.project.slug}&version={self.version.slug}"
            f"&absolute_uri=https://docs.example.com"
        )
        self.client.get(url, headers={"host": self.host})
        assert PageView.objects.all().count() == 0

    def test_uri_for_another_project(self):
        other_project = get(
            Project,
            slug="other",
        )
        other_project.versions.all().update(privacy_level=PUBLIC)

        # Host and ``absolute_uri`` are from different projects
        assert PageView.objects.all().count() == 0
        url = (
            reverse("analytics_api")
            + f"?project={self.project.slug}&version=latest"
            f"&absolute_uri=https://other.readthedocs.io/en/latest/"
        )
        self.client.get(url, headers={"host": self.host})
        assert PageView.objects.all().count() == 0

        # Host and ``absolute_uri`` are from different projects with no ``?version`` attribute
        url = (
            reverse("analytics_api")
            + f"?project={self.project.slug}"
            f"&absolute_uri=https://other.readthedocs.io/en/latest/"
        )
        self.client.get(url, headers={"host": self.host})
        assert PageView.objects.all().count() == 0

        # Host and ``absolute_uri`` are from the same project
        url = (
            reverse("analytics_api")
            + f"?project=other&version=latest"
            f"&absolute_uri=https://other.readthedocs.io/en/latest/"
        )
        self.client.get(url, headers={"host": "other.readthedocs.io"})
        assert PageView.objects.all().count() == 1

    def test_cache_headers(self):
        resp = self.client.get(self.url, headers={"host": self.host})
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["CDN-Cache-Control"], "private")

    def test_increase_page_view_count(self):
        assert (
            PageView.objects.all().count() == 0
        ), "There's no PageView object created yet."

        # testing for yesterday
        with mock.patch("readthedocs.analytics.tasks.timezone.now") as mocked_timezone:
            mocked_timezone.return_value = self.yesterday

            self.client.get(self.url, headers={"host": self.host})

            assert (
                PageView.objects.all().count() == 1
            ), f"PageView object for path '{self.absolute_uri}' is created"
            assert PageView.objects.all().first().view_count == 1, "'index' has 1 view"

            self.client.get(self.url, headers={"host": self.host})

            assert (
                PageView.objects.all().count() == 1
            ), f"PageView object for path '{self.absolute_uri}' is already created"
            assert PageView.objects.filter(path="/index.html").count() == 1
            assert (
                PageView.objects.all().first().view_count == 2
            ), f"'{self.absolute_uri}' has 2 views now"

        # testing for today
        with mock.patch("readthedocs.analytics.tasks.timezone.now") as mocked_timezone:
            mocked_timezone.return_value = self.today

            self.client.get(self.url, headers={"host": self.host})

            assert (
                PageView.objects.all().count() == 2
            ), f"PageView object for path '{self.absolute_uri}' is created for two days (yesterday and today)"
            assert PageView.objects.filter(path="/index.html").count() == 2
            assert (
                PageView.objects.all().order_by("-date").first().view_count == 1
            ), f"'{self.absolute_uri}' has 1 view today"

        # testing for tomorrow
        with mock.patch("readthedocs.analytics.tasks.timezone.now") as mocked_timezone:
            mocked_timezone.return_value = self.tomorrow

            self.client.get(self.url, headers={"host": self.host})

            assert (
                PageView.objects.all().count() == 3
            ), f"PageView object for path '{self.absolute_uri}' is created for three days (yesterday, today & tomorrow)"
            assert PageView.objects.filter(path="/index.html").count() == 3
            assert (
                PageView.objects.all().order_by("-date").first().view_count == 1
            ), f"'{self.absolute_uri}' has 1 view tomorrow"

    def test_dont_track_external_domains(self):
        self.assertEqual(PageView.objects.all().count(), 0)
        get(
            Version,
            slug="123",
            type=EXTERNAL,
            built=True,
            active=True,
        )
        host = f"{self.project.slug}--123.readthedocs.build"
        r = self.client.get(self.url, headers={"host": host})
        self.assertEqual(r.status_code, 204)
        self.assertEqual(PageView.objects.all().count(), 0)

    def test_notfound_404_pages(self):
        self.assertEqual(PageView.objects.all().count(), 0)
        url = self.url + "&status=404"
        resp = self.client.get(url, headers={"host": self.host})
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(PageView.objects.all().count(), 1)
        self.assertEqual(PageView.objects.filter(status=404).count(), 1)

    def test_notfound_404_page_without_version(self):
        self.assertEqual(PageView.objects.all().count(), 0)
        absolute_uri = (
            f"https://{self.project.slug}.readthedocs.io/index.html"
        )
        url = (
            reverse("analytics_api")
            + f"?project={self.project.slug}&version=null"
            f"&absolute_uri={absolute_uri}"
            "&status=404"
        )

        resp = self.client.get(url, headers={"host": self.host})
        pageview = PageView.objects.all().first()

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(PageView.objects.all().count(), 1)
        self.assertIsNone(pageview.version)
        self.assertEqual(pageview.project.slug, self.project.slug)
        self.assertEqual(pageview.path, "/index.html")
        self.assertEqual(pageview.status, 404)
