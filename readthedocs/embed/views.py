"""Views for the embed app."""

import structlog
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.mixins import EmbedAPIMixin


log = structlog.get_logger(__name__)


class EmbedAPI(EmbedAPIMixin, APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        return Response(
            {
                "error": (
                    "Embed API v2 has been deprecated and is no longer available, please use embed API v3 instead. "
                    "Read our blog post for more information: https://about.readthedocs.com/blog/2024/11/embed-api-v2-deprecated/."
                )
            },
            status=status.HTTP_410_GONE,
        )
