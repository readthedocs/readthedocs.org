from __future__ import division, print_function, unicode_literals

import json

from django.http import QueryDict
from rest_framework.parsers import BaseParser


class RawBodyParser(BaseParser):

    """
    Parse a request and expose the original payload.

    DRF doesn't expose the request's body after using ``request.data``.
    We are implementing a custom parser to exposed it as `raw_body`.
    """

    media_type = None

    def parse(self, stream, media_type, parser_context):
        request = parser_context['request']
        raw_body = stream.read().decode()
        setattr(request, 'raw_body', raw_body)
        return raw_body


class RawBodyJSONParser(RawBodyParser):

    media_type = 'application/json'

    def parse(self, stream, media_type, parser_context):
        raw_body = super(RawBodyJSONParser, self).parse(
            stream, media_type, parser_context
        )
        return json.loads(raw_body)


class RawBodyFormParser(RawBodyParser):
    """
    Parser for form data.
    """

    media_type = 'application/x-www-form-urlencoded'

    def parse(self, stream, media_type, parser_context):
        raw_body = super(RawBodyFormParser, self).parse(
            stream, media_type, parser_context
        )
        data = QueryDict(raw_body)
        return dict(data.items())
