import os

import sphinx

srcdir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "examples",
    "default",
)


def get_anchor_link_title(thing):
    # https://github.com/sphinx-doc/sphinx/commit/bc635627d32b52e8e1381f23cddecf26429db1ae
    if sphinx.version_info < (5, 0, 0):
        if thing == "heading":
            thing = "headline"
        title = f"Permalink to this {thing}"
    # https://github.com/sphinx-doc/sphinx/commit/7e9a2066c2f31eda53d075f5a8b20a7430ca0c61
    elif sphinx.version_info >= (7, 2, 0):
        title = f"Link to this {thing}"
    else:
        title = f"Permalink to this {thing}"
    return title


def compare_content_without_blank_lines(text_a, text_b):
    lines_a = _split_lines_without_blank_lines(text_a)
    lines_b = _split_lines_without_blank_lines(text_b)
    assert lines_a == lines_b


def _split_lines_without_blank_lines(text):
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            lines.append(line)
    return lines
