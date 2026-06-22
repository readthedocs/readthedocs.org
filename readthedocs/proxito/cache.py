import structlog


log = structlog.get_logger(__name__)

CACHE_TAG_HEADER = "Cache-Tag"
CDN_CACHE_CONTROL_HEADER = "CDN-Cache-Control"

# Redirects without an explicit freshness lifetime are bypassed by the CDN
# (a bare ``CDN-Cache-Control: public`` isn't enough), so we cache them at the
# CDN level for a few hours. This doesn't affect browser caching.
REDIRECT_CDN_CACHE_CONTROL_MAX_AGE = 14400  # 4 hours


def add_cache_tags(response, cache_tags):
    """
    Add cache tags to the response.

    New cache tags will be appended to the existing ones.

    :param response: The response to add cache tags to.
    :param cache_tags: A list of cache tags to add to the response.
    """
    cache_tags = cache_tags.copy()
    current_cache_tag = response.headers.get(CACHE_TAG_HEADER)
    if current_cache_tag:
        cache_tags.append(current_cache_tag)

    response.headers[CACHE_TAG_HEADER] = ",".join(cache_tags)


def cache_response(response, cache_tags=None, force=True):
    """
    Cache the response at the CDN level.

    We add the ``Cache-Tag`` header to the response, to be able to purge
    the cache by a given tag. And we set the ``CDN-Cache-Control: public`` header
    to cache the response at the CDN level only. This doesn't
    affect caching at the browser level (``Cache-Control``).

    See:

    - https://developers.cloudflare.com/cache/how-to/purge-cache/#cache-tags-enterprise-only
    - https://developers.cloudflare.com/cache/about/cdn-cache-control.

    :param response: The response to cache.
    :param cache_tags: A list of cache tags to add to the response.
    :param force: If ``True``, the header will be set to public even if it
     was already set to private.
    """
    if cache_tags:
        add_cache_tags(response, cache_tags)
    if force or CDN_CACHE_CONTROL_HEADER not in response.headers:
        response.headers[CDN_CACHE_CONTROL_HEADER] = "public"


def cache_redirect_response(response):
    """
    Cache a redirect response at the CDN level with an explicit ``max-age``.

    The CDN bypasses redirects that only carry a bare ``CDN-Cache-Control:
    public`` (no freshness lifetime), so we add a ``max-age`` to make them
    cacheable at the CDN level only. We only do this for responses that are
    already public, to avoid caching private (e.g. private repos) redirects.
    This doesn't affect caching at the browser level (``Cache-Control``).

    :param response: The redirect response to cache.
    """
    if response.headers.get(CDN_CACHE_CONTROL_HEADER) == "public":
        response.headers[CDN_CACHE_CONTROL_HEADER] = (
            f"public, max-age={REDIRECT_CDN_CACHE_CONTROL_MAX_AGE}"
        )


def private_response(response, force=True):
    """
    Prevent the response from being cached at the CDN level.

    We do this by explicitly setting the ``CDN-Cache-Control`` header to private.

    :param response: The response to mark as private.
    :param force: If ``True``, the header will be set to private even if it
     was already set to public.
    """
    if force or CDN_CACHE_CONTROL_HEADER not in response.headers:
        response.headers[CDN_CACHE_CONTROL_HEADER] = "private"
