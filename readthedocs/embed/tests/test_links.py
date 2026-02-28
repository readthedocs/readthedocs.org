from collections import namedtuple

import pytest
from selectolax.parser import HTMLParser

from readthedocs.embed.views import clean_links

URLData = namedtuple('URLData', ['docurl', 'href', 'expected'])

html_base_url = 'https://t.readthedocs.io/en/latest/page.html'
dirhtml_base_url = 'https://t.readthedocs.io/en/latest/page/'
htmldata = [
    URLData(
        html_base_url,
        '#to-a-section',
        'https://t.readthedocs.io/en/latest/page.html#to-a-section',
    ),
    URLData(
        html_base_url,
        '/section.html',
        '/section.html',  # don't change it if starts with /
    ),
    URLData(
        html_base_url,
        'internal/deep/section.html',
        'https://t.readthedocs.io/en/latest/internal/deep/section.html',
    ),
    URLData(
        html_base_url,
        'section.html',
        'https://t.readthedocs.io/en/latest/section.html',
    ),
    URLData(
        html_base_url,
        'relative/page.html#to-a-section',
        'https://t.readthedocs.io/en/latest/relative/page.html#to-a-section',
    ),
    URLData(
        'https://t.readthedocs.io/en/latest/internal/deep/page/section.html',
        '../../page.html#to-a-section',
        'https://t.readthedocs.io/en/latest/internal/deep/page/../../page.html#to-a-section',
    ),
    URLData(
        'https://t.readthedocs.io/en/latest/internal/deep/page/section.html',
        'relative/page.html#to-a-section',
        'https://t.readthedocs.io/en/latest/internal/deep/page/relative/page.html#to-a-section',
    ),
    URLData(
        html_base_url,
        'https://readthedocs.org/',
        'https://readthedocs.org/',  # don't change external links
    ),
]

dirhtmldata = [
    URLData(
        dirhtml_base_url,
        '#to-a-section',
        'https://t.readthedocs.io/en/latest/page/#to-a-section',
    ),
    URLData(
        dirhtml_base_url,
        '/section/',
        '/section/',  # don't change it if starts with /
    ),
    URLData(
        dirhtml_base_url,
        'internal/deep/section/',
        'https://t.readthedocs.io/en/latest/page/internal/deep/section/',
    ),
    URLData(
        dirhtml_base_url,
        'section/',
        'https://t.readthedocs.io/en/latest/page/section/',
    ),
    URLData(
        dirhtml_base_url,
        'relative/page/#to-a-section',
        'https://t.readthedocs.io/en/latest/page/relative/page/#to-a-section',
    ),
    URLData(
        'https://t.readthedocs.io/en/latest/internal/deep/page/section/',
        '../../page/#to-a-section',
        'https://t.readthedocs.io/en/latest/internal/deep/page/section/../../page/#to-a-section',
    ),
    URLData(
        dirhtml_base_url,
        'https://readthedocs.org/',
        'https://readthedocs.org/',  # don't change external links
    ),
]


@pytest.mark.parametrize('url', htmldata + dirhtmldata)
def test_clean_links(url):
    body = HTMLParser(f'<a href="{url.href}">Click here</a>')
    clean_links(body, url.docurl)
    assert body.css_first('a').attributes['href'] == url.expected


def test_two_links():
    """
    First link does not affect the second one.

    We are using ``._replace`` for the firsturl case, and that should not affect
    the second link.
    """
    firsturl = URLData(
        'https://t.readthedocs.io/en/latest/internal/deep/page/section.html',
        '../../page.html#to-a-section',
        'https://t.readthedocs.io/en/latest/internal/deep/page/../../page.html#to-a-section',
    )
    secondurl = URLData(
        '',  # docurl comes from firsturl
        '#to-a-section',
        'https://t.readthedocs.io/en/latest/internal/deep/page/section.html#to-a-section',
    )
    body = HTMLParser(f'<a href="{firsturl.href}">Click here</a><a href="{secondurl.href}">Click here</a>')
    clean_links(body, firsturl.docurl)
    firstlink, secondlink = body.css('a')
    assert firstlink.attributes['href'] == firsturl.expected
    assert secondlink.attributes['href'] == secondurl.expected
