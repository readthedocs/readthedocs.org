"""Simple client to access our API with Slumber credentials."""

import requests
import structlog
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from slumber import API
from slumber import serialize
from urllib3.util.retry import Retry

from .adapters import TimeoutHostHeaderSSLAdapter
from .adapters import TimeoutHTTPAdapter


log = structlog.get_logger(__name__)


class DrfJsonSerializer(serialize.JsonSerializer):
    """Additional serialization help from the DRF renderer."""

    key = "json-drf"

    def dumps(self, data):
        """Used to be able to render datetime objects."""
        return JSONRenderer().render(data)


def setup_api(build_api_key):
    session = requests.Session()
    if settings.SLUMBER_API_HOST.startswith("https"):
        # Only use the HostHeaderSSLAdapter for HTTPS connections
        adapter_class = TimeoutHostHeaderSSLAdapter
    else:
        adapter_class = TimeoutHTTPAdapter

    # Define a retry mechanism trying to attempt to not fail in the first error.
    # Builders hit this issue frequently because the webs are high loaded
    # (even on non-idempotent methods, sadly).
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        status=3,
        backoff_factor=0.5,  # 0.5, 1, 2 seconds
        allowed_methods=("GET", "PUT", "PATCH", "POST"),
        status_forcelist=(408, 413, 429, 500, 502, 503, 504),
    )

    session.mount(
        settings.SLUMBER_API_HOST,
        adapter_class(max_retries=retry),
    )
    session.headers.update({"Host": settings.PRODUCTION_DOMAIN})
    session.headers["Authorization"] = f"Token {build_api_key}"
    api_config = {
        "base_url": "%s/api/v2/" % settings.SLUMBER_API_HOST,
        "serializer": serialize.Serializer(
            default="json-drf",
            serializers=[
                serialize.JsonSerializer(),
                DrfJsonSerializer(),
            ],
        ),
        "session": session,
    }
    return API(**api_config)
