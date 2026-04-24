class TextToken:
    def __init__(self, text):
        self.text = text


class ArgumentToken:
    def __init__(self, *, name, value, type):
        self.name = name
        self.value = value
        self.type = type


class SearchQueryParser:
    """Simplified and minimal parser for ``name:value`` expressions."""

    allowed_arguments = {
        "project": list,
        "subprojects": list,
        "user": str,
    }

    def __init__(self, query):
        self._query = query
        self.query = ""
        # Set all arguments to their default values.
        self.arguments = {name: type() for name, type in self.allowed_arguments.items()}

    def parse(self):
        r"""
        Parse the expression into a query and arguments.

        The parser steps are:

        - Split the string using white spaces.
        - Tokenize each string into a ``text`` or ``argument`` token.
          A valid argument has the ``name:value`` form,
          and it's declared in `allowed_arguments`,
          anything else is considered a text token.
        - All text tokens are concatenated to form the final query.

        To interpret an argument as text, it can be escaped as ``name\:value``.
        """
        tokens = (self._get_token(text) for text in self._query.split())
        query = []
        for token in tokens:
            if isinstance(token, TextToken):
                query.append(token.text)
            elif isinstance(token, ArgumentToken):
                if token.type is str:
                    self.arguments[token.name] = token.value
                elif token.type is list:
                    self.arguments[token.name].append(token.value)
                else:
                    raise ValueError(f"Invalid argument type {token.type}")
            else:
                raise ValueError("Invalid node")

        self.query = self._unescape(" ".join(query))

    def _get_token(self, text):
        result = text.split(":", maxsplit=1)
        if len(result) < 2:
            return TextToken(text)

        name, value = result
        if name in self.allowed_arguments:
            return ArgumentToken(
                name=name,
                value=value,
                type=self.allowed_arguments[name],
            )

        return TextToken(text)

    def _unescape(self, text):
        return text.replace("\\:", ":")
