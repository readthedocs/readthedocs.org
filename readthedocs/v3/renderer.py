import json
from rest_framework.compat import (
    INDENT_SEPARATORS, LONG_SEPARATORS, SHORT_SEPARATORS,
)
from rest_framework.renderers import JSONRenderer


class AlphaneticalSortedJSONRenderer(JSONRenderer):

    """
    Renderer that sort they keys from the JSON alphabetically.

    See https://github.com/encode/django-rest-framework/pull/4202
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Copied from ``rest_framework.renders.JSONRenderer``.

        Changes:

          - sort_keys=True on json.dumps
          - use str instead of six.text_types

        https://github.com/encode/django-rest-framework/blob/master/rest_framework/renderers.py#L89
        """
        if data is None:
            return bytes()

        renderer_context = renderer_context or {}
        indent = self.get_indent(accepted_media_type, renderer_context)

        if indent is None:
            separators = SHORT_SEPARATORS if self.compact else LONG_SEPARATORS
        else:
            separators = INDENT_SEPARATORS

        ret = json.dumps(
            data,
            cls=self.encoder_class,
            indent=indent,
            ensure_ascii=self.ensure_ascii,
            allow_nan=not self.strict,
            separators=separators,
            sort_keys=True,
        )

        if isinstance(ret, str):
            # We always fully escape \u2028 and \u2029 to ensure we output JSON
            # that is a strict javascript subset. If bytes were returned
            # by json.dumps() then we don't have these characters in any case.
            # See: http://timelessrepo.com/json-isnt-a-javascript-subset
            ret = ret.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
            return bytes(ret.encode('utf-8'))
        return ret
