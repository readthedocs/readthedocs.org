"""Django storage mixin classes for different storage backends (Azure, S3)."""

from urllib.parse import urlsplit, urlunsplit


class OverrideHostnameMixin:

    """
    Override the hostname or protocol when outputting URLs.

    This is useful for use with a CDN or when proxying outside of Blob Storage

    See: https://github.com/jschneier/django-storages/pull/658
    """

    override_hostname = (
        None  # use the hostname without scheme (eg. 'assets.readthedocs.org')
    )
    override_protocol = (
        None  # set to "http" or "https". None = inherit automatic setting.
    )

    def url(self, *args, **kwargs):
        url = super().url(*args, **kwargs)

        if self.override_hostname or self.override_protocol:
            parts = list(urlsplit(url))
            if self.override_protocol:
                parts[0] = self.override_protocol
            if self.override_hostname:
                parts[1] = self.override_hostname
            url = urlunsplit(parts)

        return url


class S3PrivateBucketMixin:

    """Make the bucket private and use auth querystring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bucket_acl = 'private'
        self.default_acl = 'private'
        self.querystring_auth = True
