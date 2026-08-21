from collections import namedtuple

import pytest
from pyquery import PyQuery

from readthedocs.embed.utils import clean_references

URLData = namedtuple("URLData", ["docurl", "ref", "expected"])

html_base_url = "https://t.readthedocs.io/en/latest/page.html"
dirhtml_base_url = "https://t.readthedocs.io/en/latest/page/"
htmldata = [
    URLData(
        html_base_url,
        "#to-a-section",
        "https://t.readthedocs.io/en/latest/page.html#to-a-section",
    ),
    URLData(
        html_base_url,
        "/section.html",
        "/section.html",  # don't change it if starts with /
    ),
    URLData(
        html_base_url,
        "internal/deep/section.html",
        "https://t.readthedocs.io/en/latest/internal/deep/section.html",
    ),
    URLData(
        html_base_url,
        "section.html",
        "https://t.readthedocs.io/en/latest/section.html",
    ),
    URLData(
        html_base_url,
        "relative/page.html#to-a-section",
        "https://t.readthedocs.io/en/latest/relative/page.html#to-a-section",
    ),
    URLData(
        "https://t.readthedocs.io/en/latest/internal/deep/page/section.html",
        "../../page.html#to-a-section",
        "https://t.readthedocs.io/en/latest/internal/deep/page/../../page.html#to-a-section",
    ),
    URLData(
        "https://t.readthedocs.io/en/latest/internal/deep/page/section.html",
        "relative/page.html#to-a-section",
        "https://t.readthedocs.io/en/latest/internal/deep/page/relative/page.html#to-a-section",
    ),
    URLData(
        html_base_url,
        "https://readthedocs.org/",
        "https://readthedocs.org/",  # don't change external links
    ),
]

dirhtmldata = [
    URLData(
        dirhtml_base_url,
        "#to-a-section",
        "https://t.readthedocs.io/en/latest/page/#to-a-section",
    ),
    URLData(
        dirhtml_base_url,
        "/section/",
        "/section/",  # don't change it if starts with /
    ),
    URLData(
        dirhtml_base_url,
        "internal/deep/section/",
        "https://t.readthedocs.io/en/latest/page/internal/deep/section/",
    ),
    URLData(
        dirhtml_base_url,
        "section/",
        "https://t.readthedocs.io/en/latest/page/section/",
    ),
    URLData(
        dirhtml_base_url,
        "relative/page/#to-a-section",
        "https://t.readthedocs.io/en/latest/page/relative/page/#to-a-section",
    ),
    URLData(
        "https://t.readthedocs.io/en/latest/internal/deep/page/section/",
        "../../page/#to-a-section",
        "https://t.readthedocs.io/en/latest/internal/deep/page/section/../../page/#to-a-section",
    ),
    URLData(
        dirhtml_base_url,
        "https://readthedocs.org/",
        "https://readthedocs.org/",  # don't change external links
    ),
]

imagedata = [
    URLData(
        html_base_url,
        "/_images/image.png",
        "/_images/image.png",
    ),
    URLData(
        html_base_url,
        "relative/section/image.png",
        "https://t.readthedocs.io/en/latest/relative/section/image.png",
    ),
    URLData(
        "https://t.readthedocs.io/en/latest/internal/deep/page/topic.html",
        "../../../_images/image.png",
        "https://t.readthedocs.io/en/latest/internal/deep/page/../../../_images/image.png",
    ),
]


@pytest.mark.parametrize("url", htmldata + dirhtmldata)
def test_clean_links(url):
    pq = PyQuery(f'<body><a href="{url.ref}">Click here</a></body>')
    response = clean_references(pq, url.docurl)
    assert response.find("a").attr["href"] == url.expected


@pytest.mark.parametrize("url", imagedata)
def test_clean_images(url):
    pq = PyQuery(f'<body><img alt="image alt content" src="{url.ref}"></img></body>')
    response = clean_references(pq, url.docurl)
    assert response.find("img").attr["src"] == url.expected


def test_two_links():
    """
    First link does not affect the second one.

    We are using ``._replace`` for the firsturl case, and that should not affect
    the second link.
    """
    firsturl = URLData(
        "https://t.readthedocs.io/en/latest/internal/deep/page/section.html",
        "../../page.html#to-a-section",
        "https://t.readthedocs.io/en/latest/internal/deep/page/../../page.html#to-a-section",
    )
    secondurl = URLData(
        "",  # docurl comes from firsturl
        "#to-a-section",
        "https://t.readthedocs.io/en/latest/internal/deep/page/section.html#to-a-section",
    )
    pq = PyQuery(
        f'<body><a href="{firsturl.ref}">Click here</a><a href="{secondurl.ref}">Click here</a></body>'
    )
    response = clean_references(pq, firsturl.docurl)
    firstlink, secondlink = response.find("a")
    assert (firstlink.attrib["href"], secondlink.attrib["href"]) == (
        firsturl.expected,
        secondurl.expected,
    )


def test_missing_href_attribute():
    """Test that links without href attribute don't cause errors."""
    pq = PyQuery('<body><a>Link without href</a></body>')
    response = clean_references(pq, html_base_url)
    # Should not raise KeyError, just skip the link
    assert response.find("a") is not None


def test_missing_src_attribute():
    """Test that images without src attribute don't cause errors."""
    pq = PyQuery('<body><img alt="image without src"></img></body>')
    response = clean_references(pq, html_base_url)
    # Should not raise KeyError, just skip the image
    assert response.find("img") is not None
