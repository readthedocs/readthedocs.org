"""Django storage mixin classes for different storage backends (Azure, S3)."""

from urllib.parse import urlsplit, urlunsplit


class OverrideHostnameMixin:

    """
    Override the hostname when outputting URLs.

    This is useful for use with a CDN or when proxying outside of Blob Storage

    See: https://github.com/jschneier/django-storages/pull/658
    """

    override_hostname = None    # Just the hostname without scheme (eg. 'assets.readthedocs.org')

    def url(self, *args, **kwargs):
        url = super().url(*args, **kwargs)

        if self.override_hostname:
            parts = list(urlsplit(url))
            parts[1] = self.override_hostname
            url = urlunsplit(parts)

        return url
