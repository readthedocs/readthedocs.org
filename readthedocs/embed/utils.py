"""Embed utils."""

from urllib.parse import urlparse

from pyquery import PyQuery as PQ  # noqa


def recurse_while_none(element):
    """Recursively find the leaf node with the ``href`` attribute."""
    if element.text is None and element.getchildren():
        return recurse_while_none(element.getchildren()[0])

    href = element.attrib.get("href")
    if not href:
        href = element.attrib.get("id")
    return {element.text: href}


def clean_references(obj, url, html_raw_response=False):
    """
    Rewrite (internal) links (href) and images (src) to make them absolute.

    1. external links/images are not changed
    2. prepend URL to links that are just fragments (e.g. #section)
    3. prepend URL (without filename) to internal relative links/images
    """

    # TODO: do not depend on PyQuery
    obj = PQ(obj)

    if url is None:
        return obj

    for tag in obj.find("a") + obj.find("img"):
        base_url = urlparse(url)
        attribute = "href" if tag.tag == "a" else "src"

        # Skip if the attribute doesn't exist
        if attribute not in tag.attrib:
            continue

        value = tag.attrib[attribute]

        # We need to make all internal links/images, to be absolute
        parsed_href = urlparse(value)
        if parsed_href.scheme or parsed_href.path.startswith("/"):
            # don't change external links/images
            continue

        if tag.tag == "a" and not parsed_href.path and parsed_href.fragment:
            # It's a link pointing to a specific section inside the target ``href="#section-link"``
            cleaned_value = base_url.geturl() + value
            tag.attrib[attribute] = cleaned_value
            continue

        if not base_url.path.endswith("/"):
            # internal relative link/image
            # href="../../another.html" and ``base_url`` is not HTMLDir
            # (e.g. /en/latest/deep/internal/section/page.html)
            # we want to remove the trailing filename (page.html) and use the rest as base URL
            # The resulting absolute link should be
            # https://slug.readthedocs.io/en/latest/deep/internal/section/../../another.html

            # remove the filename (page.html) from the original document URL (base_url) and,
            path, _ = base_url.path.rsplit("/", 1)
            # append the value of href/src (../../another.html) to the base URL.
            base_url = base_url._replace(path=path + "/")

        cleaned_value = base_url.geturl() + value
        tag.attrib[attribute] = cleaned_value

    if html_raw_response:
        return obj.outerHtml()

    return obj
