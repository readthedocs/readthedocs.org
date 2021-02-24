"""Embed utils."""


def recurse_while_none(element):
    """Recursively find the leaf node with the ``href`` attribute."""
    if element.text is None and element.getchildren():
        return recurse_while_none(element.getchildren()[0])

    href = element.attrib.get('href')
    if not href:
        href = element.attrib.get('id')
    return {element.text: href}
