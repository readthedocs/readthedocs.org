import json
from pygments import highlight
from pygments.formatters import TerminalTrueColorFormatter
from pygments.lexers import JsonLexer


def p(data):
    j = json.dumps(data, sort_keys=True, indent=4)
    print(
        highlight(j, JsonLexer(), TerminalTrueColorFormatter())
    )
