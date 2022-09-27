class TextToken:

    def __init__(self, text):
        self.text = text


class ArgumentToken:

    def __init__(self, *, name, value, type):
        self.name = name
        self.value = value
        self.type = type


class SearchQueryParser:

    allowed_arguments = {
        "project": list,
        "subprojects": list,
        "user": str,
    }

    def __init__(self, query):
        self._query = query
        self.query = ""
        self.arguments = {}

    def parse(self):
        tokens = (
            self._get_token(text)
            for text in self._query.split()
        )
        query = []
        arguments = {
            name: type()
            for name, type in self.allowed_arguments.items()
        }
        for token in tokens:
            if isinstance(token, TextToken):
                query.append(token.text)
            elif isinstance(token, ArgumentToken):
                if token.type == str:
                    arguments[token.name] = token.value
                elif token.type == list:
                    arguments[token.name].append(token.value)
                else:
                    raise ValueError(f"Invalid argument type {token.type}")
            else:
                raise ValueError("Invalid node")

        self.query = self._unescape(" ".join(query))
        self.arguments = arguments

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
