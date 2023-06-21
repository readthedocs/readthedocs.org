import json

from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer


def pretty_json_field(instance, field):
    """
    Display a pretty version of a JSON field in the admin.

    Thanks to PyDanny: https://www.pydanny.com/pretty-formatting-json-django-admin.html
    """
    # Convert the data to sorted, indented JSON
    response = json.dumps(getattr(instance, field), sort_keys=True, indent=2)

    # Get the Pygments formatter
    formatter = HtmlFormatter()

    # Highlight the data
    response = highlight(response, JsonLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)
