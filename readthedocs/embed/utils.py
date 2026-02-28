"""Embed utils."""


def recurse_while_none(element):
    """Recursively find the leaf node with the ``href`` attribute."""
    children = list(element.iter())
    if children:
        return recurse_while_none(children[0])

    href = element.attributes.get('href')
    if not href:
        href = element.attributes.get('id')
    return {element.text(): href}


def next_tag(element):
    """Return the next non-text sibling of element."""
    while element:
        element = element.next
        if element.tag != '-text':
            return element
    return None
