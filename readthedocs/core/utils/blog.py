from xml.etree import ElementTree

import requests
import structlog
from django.conf import settings
from django.core.cache import cache
from django.utils.dateparse import parse_datetime


log = structlog.get_logger(__name__)

ATOM = "{http://www.w3.org/2005/Atom}"


def get_blog_posts(limit=3):
    """Return the latest posts from the blog feed, cached for an hour."""
    if not settings.RTD_BLOG_FEED_URL:
        return []

    posts = cache.get("blog-posts")
    if posts is None:
        try:
            response = requests.get(settings.RTD_BLOG_FEED_URL, timeout=2)
            response.raise_for_status()
            feed = ElementTree.fromstring(response.content)
            posts = [
                {
                    "title": entry.findtext(f"{ATOM}title"),
                    "url": entry.find(f"{ATOM}link").get("href"),
                    "published": parse_datetime(entry.findtext(f"{ATOM}published")),
                }
                for entry in feed.iterfind(f"{ATOM}entry")
            ]
        except requests.RequestException, ElementTree.ParseError:
            log.warning("Unable to fetch blog posts.", exc_info=True)
            posts = []
        cache.set("blog-posts", posts, 60 * 60)
    return posts[:limit]
